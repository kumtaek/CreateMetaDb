"""
Simple Query Analyzer (UTF-8, ASCII comments)

Responsibilities
- Extract SQL from Java source (string literals, concatenation, StringBuilder, String.format)
- Extract JPA @Query strings
- Provide method list for downstream mapping

Notes
- This is a clean, minimal, cross-platform-safe implementation.
- Heuristics are conservative to avoid false positives.
"""

from __future__ import annotations

import re
import os
import sqlite3
from typing import Dict, List, Any

from util import info, handle_error, DatabaseUtils, ConfigUtils, PathUtils, HashUtils
from util.oracle_keyword_manager import get_oracle_keyword_manager
from parser.string_format_extractor import extract_string_format_queries


class SimpleQueryAnalyzer:
    """Analyze Java files to extract SQL queries and helper data."""

    def __init__(self, project_name: str, conn: sqlite3.Connection):
        try:
            self.project_name = project_name
            self.conn = conn
            self.db_utils = DatabaseUtils(None)
            self.config_utils = ConfigUtils()
            self.path_utils = PathUtils()
            self.hash_utils = HashUtils()

            self.oracle_keyword_manager = get_oracle_keyword_manager()
            self.oracle_keywords = self.oracle_keyword_manager.get_keywords()
            self.sql_start_patterns = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'MERGE']
            info("SimpleQueryAnalyzer initialized")
        except Exception as e:
            handle_error(e, "SimpleQueryAnalyzer initialization failed")

    # ===== Java file analysis =====

    def analyze_java_file(self, file_path: str, file_id: int) -> Dict[str, List[Dict]]:
        """Parse a Java file and extract queries per method."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            results = {'java_queries': [], 'jpa_queries': [], 'methods': []}
            methods = self._extract_java_methods(content)
            results['methods'] = methods

            for method in methods:
                method_name = method['name']
                method_content = method['content']

                java_queries = self._extract_java_queries(method_content, method_name)
                results['java_queries'].extend(java_queries)

                jpa_queries = self._extract_jpa_queries(method_content, method_name)
                results['jpa_queries'].extend(jpa_queries)

                fmt_queries = extract_string_format_queries(method_content, method_name)
                if fmt_queries:
                    results['java_queries'].extend(fmt_queries)

            # JPA @Query 어노테이션 추출 (메서드 선언부 위의 어노테이션 인식)
            # Repository 인터페이스의 @Query(nativeQuery=true) 등을 인식
            jpa_annotation_queries = self._extract_jpa_annotation_queries(content)
            if jpa_annotation_queries:
                # 중복 제거 (메서드 본문에서 이미 추출된 것 제외)
                existing_ids = {q['query_id'] for q in results['jpa_queries']}
                for q in jpa_annotation_queries:
                    if q['query_id'] not in existing_ids:
                        results['jpa_queries'].append(q)
                        existing_ids.add(q['query_id'])

            info(f"Java analyzed: {file_path}, methods={len(methods)}, java={len(results['java_queries'])}, jpa={len(results['jpa_queries'])}")
            return results
        except Exception as e:
            handle_error(e, f"Java analysis failed: {file_path}")
            return {'java_queries': [], 'jpa_queries': [], 'methods': []}

    def _extract_java_methods(self, content: str) -> List[Dict]:
        """Very simple method body extractor."""
        try:
            methods: List[Dict] = []
            pattern = r'(public|private|protected)\s+[^{;]+?(\w+)\s*\([^)]*\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
            for m in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
                methods.append({'name': m.group(2), 'content': m.group(3)})
            return methods
        except Exception as e:
            handle_error(e, "Java method extraction failed")
            return []

    def _extract_java_queries(self, method_content: str, method_name: str) -> List[Dict]:
        """Find SQL assembled via string literals/concat/StringBuilder."""
        try:
            queries: List[Dict] = []
            string_vars: Dict[str, str] = {}

            # String constants
            for i, const in enumerate(re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', method_content, re.DOTALL)):
                string_vars[f'STRING_CONST_{i}'] = const.strip()

            # var = "..."
            for m in re.finditer(r'String\s+(\w+)\s*=\s*"([^"]*)"', method_content, re.IGNORECASE):
                string_vars[m.group(1)] = m.group(2).strip()

            # var += "..."  /  var = var + "..."
            concat_patterns = [
                r'(\w+)\s*\+=\s*"([^"\\]*(?:\\.[^"\\]*)*)"',
                r'(\w+)\s*=\s*\w+\s*\+\s*"([^"\\]*(?:\\.[^"\\]*)*)"',
            ]
            for p in concat_patterns:
                for m in re.finditer(p, method_content, re.IGNORECASE):
                    var, append = m.group(1), m.group(2).strip()
                    string_vars[var] = (string_vars.get(var, '') + ' ' + append).strip()

            # StringBuilder.append("...")
            for m in re.finditer(r'StringBuilder\s+(\w+).*?\.append\("([^"\\]*(?:\\.[^"\\]*)*)"\)', method_content, re.DOTALL | re.IGNORECASE):
                var, append = m.group(1), m.group(2).strip()
                string_vars[var] = (string_vars.get(var, '') + ' ' + append).strip()

            # Keep only SQL-looking strings
            for var_name, var_content in string_vars.items():
                cleaned = re.sub(r'\s+', ' ', var_content.strip())
                if self._is_sql_query(cleaned):
                    queries.append({
                        'query_id': f"{method_name}_{var_name}",
                        'method_name': method_name,
                        'variable_name': var_name,
                        'sql_content': cleaned,
                        'query_type': self._detect_query_type(cleaned),
                    })

            return queries
        except Exception as e:
            handle_error(e, f"Java query extraction failed: {method_name}")
            return []

    def _extract_jpa_queries(self, method_content: str, method_name: str) -> List[Dict]:
        """Extract @Query("...") fragments and join them (from method body)."""
        try:
            queries: List[Dict] = []
            for m in re.finditer(r'@Query\s*\(\s*([\s\S]+?)\s*\)', method_content, re.DOTALL | re.IGNORECASE):
                annotation = m.group(1)
                parts = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', annotation, re.DOTALL)
                if not parts:
                    continue
                full = re.sub(r'\s+', ' ', ' '.join(p.strip() for p in parts).strip())
                if self._is_sql_query(full):
                    queries.append({
                        'query_id': method_name,
                        'method_name': method_name,
                        'variable_name': method_name,
                        'sql_content': full,
                        'query_type': self._detect_query_type(full),
                    })
            return queries
        except Exception as e:
            handle_error(e, f"JPA query extraction failed: {method_name}")
            return []

    # JPA 어노테이션 파싱 설정 상수
    JPA_METHOD_SEARCH_RANGE = 500  # @Query 어노테이션 이후 메서드 선언 검색 범위 (문자 수)

    def _extract_jpa_annotation_queries(self, content: str) -> List[Dict]:
        """
        JPA @Query 어노테이션에서 SQL 추출 (메서드 선언부 위의 어노테이션 인식).

        Args:
            content: Java 소스 파일 전체 내용

        Returns:
            추출된 JPA 쿼리 목록 (query_id, method_name, sql_content, query_type, is_native)

        지원 패턴:
        - @Query("SELECT ...")
        - @Query(value = "SELECT ...", nativeQuery = true)
        - @Query(nativeQuery = true, value = "SELECT ...")
        - 멀티라인 @Query(value = \"\"\"...\"\"\", nativeQuery = true)
        """
        try:
            queries: List[Dict] = []

            # 2단계 접근: 먼저 @Query 위치를 찾고, 그 다음 메서드명을 찾음
            # 1단계: @Query(...) 블록 찾기
            query_blocks = self._find_query_annotation_blocks(content)

            # 2단계: 각 @Query 블록 뒤의 메서드명 찾기
            for start_idx, end_idx, annotation_content in query_blocks:
                # @Query 종료 후 설정된 범위 내에서 메서드 선언 검색
                search_area = content[end_idx:end_idx + self.JPA_METHOD_SEARCH_RANGE]

                # 메서드 선언 패턴: 반환타입 메서드명(
                # Java의 모든 반환 타입을 범용적으로 매칭 (식별자 + 제네릭/배열 조합)
                method_match = re.search(
                    r'[\w<>\[\],\s]+\s+(\w+)\s*\(',
                    search_area
                )

                if method_match:
                    method_name = method_match.group(1)

                    # SQL 내용 추출
                    sql_content = self._extract_sql_from_annotation(annotation_content)

                    if sql_content and self._is_sql_query(sql_content):
                        # nativeQuery 여부 확인
                        is_native = 'nativeQuery' in annotation_content and 'true' in annotation_content.lower()

                        queries.append({
                            'query_id': method_name,
                            'method_name': method_name,
                            'variable_name': method_name,
                            'sql_content': sql_content,
                            'query_type': self._detect_query_type(sql_content),
                            'is_native': is_native,
                        })

            return queries
        except Exception as e:
            handle_error(e, "JPA annotation query extraction failed")
            return []

    def _find_query_annotation_blocks(self, content: str) -> List[tuple]:
        """
        소스 코드에서 @Query 어노테이션 블록들을 찾아 반환.

        Args:
            content: Java 소스 파일 전체 내용

        Returns:
            [(시작위치, 끝위치, 어노테이션내용), ...] 형태의 리스트
        """
        query_blocks = []
        i = 0
        while True:
            idx = content.find('@Query', i)
            if idx == -1:
                break

            # 괄호 시작 찾기
            paren_start = content.find('(', idx)
            if paren_start == -1:
                i = idx + 1
                continue

            # 괄호 매칭으로 끝 찾기
            paren_count = 1
            j = paren_start + 1
            while j < len(content) and paren_count > 0:
                if content[j] == '(':
                    paren_count += 1
                elif content[j] == ')':
                    paren_count -= 1
                j += 1

            if paren_count == 0:
                annotation_content = content[paren_start + 1:j - 1]
                query_blocks.append((idx, j, annotation_content))

            i = j

        return query_blocks

    def _extract_sql_from_annotation(self, annotation_content: str) -> str:
        """
        @Query 어노테이션 내용에서 SQL 문자열 추출.

        Args:
            annotation_content: @Query(...) 괄호 안의 내용

        Returns:
            추출된 SQL 문자열 (공백 정규화됨), 실패 시 빈 문자열

        지원 패턴:
        - value = \"\"\"...\"\"\": Java 15+ text block
        - value = "..." + "...": 문자열 연결
        - "...": 단순 문자열
        """
        try:
            # 1. value = "..." 패턴 (멀티라인 포함)
            # value = """...""" (Java 15+ text block)
            text_block_match = re.search(
                r'value\s*=\s*"""([\s\S]*?)"""',
                annotation_content,
                re.DOTALL
            )
            if text_block_match:
                return re.sub(r'\s+', ' ', text_block_match.group(1).strip())

            # value = "..." + "..." (문자열 연결)
            value_match = re.search(
                r'value\s*=\s*("(?:[^"\\]|\\.)*"(?:\s*\+\s*"(?:[^"\\]|\\.)*")*)',
                annotation_content,
                re.DOTALL
            )
            if value_match:
                parts = re.findall(r'"((?:[^"\\]|\\.)*)"', value_match.group(1), re.DOTALL)
                if parts:
                    return re.sub(r'\s+', ' ', ' '.join(p.strip() for p in parts).strip())

            # 2. 단순 @Query("...") 패턴 (value= 없이)
            # 첫 번째 문자열이 SQL인 경우
            direct_match = re.search(
                r'^[^"]*"((?:[^"\\]|\\.)*)"',
                annotation_content,
                re.DOTALL
            )
            if direct_match:
                sql = direct_match.group(1).strip()
                # nativeQuery, value 등의 키워드가 아닌 실제 SQL인지 확인
                if sql and not re.match(r'^(nativeQuery|value|countQuery|name)\s*$', sql, re.IGNORECASE):
                    return re.sub(r'\s+', ' ', sql)

            # 3. 모든 문자열 조각을 연결
            all_strings = re.findall(r'"((?:[^"\\]|\\.)*)"', annotation_content, re.DOTALL)
            if all_strings:
                combined = ' '.join(s.strip() for s in all_strings if s.strip())
                return re.sub(r'\s+', ' ', combined.strip())

            return ''
        except Exception as e:
            handle_error(e, "SQL extraction from annotation failed")
            return ''

    # ===== Helpers =====

    def _is_sql_query(self, s: str) -> bool:
        head = (s or '').lstrip().upper()
        return any(head.startswith(k) for k in self.sql_start_patterns)

    def _detect_query_type(self, s: str) -> str:
        u = (s or '').lstrip().upper()
        if u.startswith('SELECT'):
            return 'SQL_SELECT'
        if u.startswith('INSERT'):
            return 'SQL_INSERT'
        if u.startswith('UPDATE'):
            return 'SQL_UPDATE'
        if u.startswith('DELETE'):
            return 'SQL_DELETE'
        return 'SQL_MERGE'

