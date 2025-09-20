"""
단순화된 연관관계 분석기
- 목적: 쿼리→테이블→조인관계 도출에 집중
- 접근: 복잡한 파싱 대신 단순한 패턴 매칭
- 동적 테이블명 정규화 (table_{동적} → table)
"""

import re
from typing import List, Dict, Any, Set, Tuple
from util import app_logger, info, error, debug, warning, handle_error


class SimpleRelationshipAnalyzer:
    """단순화된 연관관계 분석기"""

    def __init__(self):
        self.table_patterns = [
            # FROM 절
            r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:_{[^}]+})?)\s*([a-zA-Z_][a-zA-Z0-9_]*)?',
            # JOIN 절
            r'\b(?:LEFT|RIGHT|INNER|OUTER|CROSS|FULL)?\s*JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:_{[^}]+})?)\s*([a-zA-Z_][a-zA-Z0-9_]*)?',
            # UPDATE 문
            r'\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*(?:_{[^}]+})?)',
            # INSERT INTO
            r'\bINSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*(?:_{[^}]+})?)',
            # DELETE FROM
            r'\bDELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:_{[^}]+})?)'
        ]

        self.join_patterns = [
            # explicit join: table1 JOIN table2 ON condition
            r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:LEFT|RIGHT|INNER|OUTER|CROSS|FULL)?\s*JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+ON\s+([^WHERE^GROUP^ORDER^HAVING]+)',
            # implicit join: WHERE a.id = b.id
            r'WHERE.*?([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)'
        ]

    def extract_tables_from_sql(self, sql_content: str) -> Set[str]:
        """
        SQL에서 테이블명 추출 (동적 부분 제거)

        Args:
            sql_content: SQL 내용

        Returns:
            정규화된 테이블명 집합
        """
        try:
            if not sql_content:
                return set()

            # SQL 정규화 (주석, 개행 제거)
            normalized_sql = self._normalize_sql(sql_content)

            tables = set()

            # 테이블 패턴으로 추출
            for pattern in self.table_patterns:
                matches = re.findall(pattern, normalized_sql, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        table_name = match[0]  # 첫 번째가 테이블명
                    else:
                        table_name = match

                    # 동적 부분 제거 및 정규화
                    normalized_table = self._normalize_table_name(table_name)
                    if self._is_valid_table_name(normalized_table):
                        tables.add(normalized_table.upper())

            debug(f"추출된 테이블: {tables}")
            return tables

        except Exception as e:
            handle_error(e, f"테이블 추출 실패: SQL 길이={len(sql_content)}")
            return set()

    def extract_join_relationships(self, sql_content: str, tables: Set[str]) -> List[Dict[str, Any]]:
        """
        SQL에서 조인 관계 추출

        Args:
            sql_content: SQL 내용
            tables: 추출된 테이블 집합

        Returns:
            조인 관계 리스트
        """
        try:
            if not sql_content or not tables:
                return []

            normalized_sql = self._normalize_sql(sql_content)
            relationships = []

            # Explicit JOIN 관계 추출
            explicit_joins = self._extract_explicit_joins(normalized_sql, tables)
            relationships.extend(explicit_joins)

            # Implicit JOIN 관계 추출 (WHERE 절)
            implicit_joins = self._extract_implicit_joins(normalized_sql, tables)
            relationships.extend(implicit_joins)

            # 중복 제거
            unique_relationships = self._remove_duplicate_relationships(relationships)

            debug(f"추출된 조인 관계 수: {len(unique_relationships)}")
            return unique_relationships

        except Exception as e:
            handle_error(e, f"조인 관계 추출 실패: SQL 길이={len(sql_content)}")
            return []

    def analyze_sql_components(self, sql_content: str, sql_id: str = None) -> Dict[str, Any]:
        """
        SQL에서 모든 컴포넌트 분석 (통합 함수)

        Args:
            sql_content: SQL 내용
            sql_id: SQL ID (선택적)

        Returns:
            분석 결과 (테이블, 조인관계 포함)
        """
        try:
            # 1. 테이블 추출
            tables = self.extract_tables_from_sql(sql_content)

            # 2. 조인 관계 추출
            join_relationships = self.extract_join_relationships(sql_content, tables)

            # 3. 결과 정리
            result = {
                'sql_id': sql_id,
                'tables': list(tables),
                'join_relationships': join_relationships,
                'table_count': len(tables),
                'join_count': len(join_relationships)
            }

            info(f"SQL 분석 완료 - ID: {sql_id}, 테이블: {len(tables)}개, 조인: {len(join_relationships)}개")
            return result

        except Exception as e:
            handle_error(e, f"SQL 컴포넌트 분석 실패: sql_id={sql_id}")
            return {
                'sql_id': sql_id,
                'tables': [],
                'join_relationships': [],
                'table_count': 0,
                'join_count': 0,
                'error': str(e)
            }

    def _normalize_sql(self, sql_content: str) -> str:
        """SQL 정규화"""
        try:
            # XML 태그 제거
            sql = re.sub(r'<[^>]+>', ' ', sql_content)

            # 주석 제거
            sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
            sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)

            # 개행, 탭을 공백으로 변환
            sql = re.sub(r'\s+', ' ', sql)

            return sql.strip().upper()

        except Exception as e:
            handle_error(e, "SQL 정규화 실패")
            return sql_content.upper()

    def _normalize_table_name(self, table_name: str) -> str:
        """테이블명 정규화 (동적 부분 제거)"""
        try:
            if not table_name:
                return ""

            # table_{동적} → table 변환
            normalized = re.sub(r'_{[^}]+}', '', table_name)

            # 특수문자 제거
            normalized = re.sub(r'[^a-zA-Z0-9_]', '', normalized)

            return normalized.strip()

        except Exception as e:
            handle_error(e, f"테이블명 정규화 실패: {table_name}")
            return table_name

    def _is_valid_table_name(self, table_name: str) -> bool:
        """유효한 테이블명인지 검증"""
        if not table_name or len(table_name) < 2:
            return False

        # 예약어 제외
        reserved_words = {
            'SELECT', 'FROM', 'WHERE', 'JOIN', 'ON', 'AND', 'OR', 'NOT',
            'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER',
            'INDEX', 'TABLE', 'DATABASE', 'SCHEMA', 'VIEW', 'TRIGGER',
            'NULL', 'TRUE', 'FALSE', 'IF', 'THEN', 'ELSE', 'CASE', 'WHEN'
        }

        return table_name.upper() not in reserved_words

    def _extract_explicit_joins(self, normalized_sql: str, tables: Set[str]) -> List[Dict[str, Any]]:
        """Explicit JOIN 관계 추출"""
        try:
            relationships = []

            # JOIN 패턴 검색
            join_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s+([a-zA-Z_][a-zA-Z0-9_]*\s+)?(?:LEFT|RIGHT|INNER|OUTER|CROSS|FULL)?\s*JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+([a-zA-Z_][a-zA-Z0-9_]*\s+)?ON\s+([^WHERE^GROUP^ORDER^HAVING^JOIN]+)'

            matches = re.findall(join_pattern, normalized_sql, re.IGNORECASE)

            for match in matches:
                table1 = self._normalize_table_name(match[0])
                table2 = self._normalize_table_name(match[2])
                condition = match[4].strip()

                if (self._is_valid_table_name(table1) and
                    self._is_valid_table_name(table2) and
                    table1 != table2):

                    relationships.append({
                        'source_table': table1.upper(),
                        'target_table': table2.upper(),
                        'rel_type': 'JOIN_EXPLICIT',
                        'join_type': 'EXPLICIT_JOIN',
                        'condition': condition,
                        'description': f"EXPLICIT JOIN: {table1} ↔ {table2}"
                    })

            return relationships

        except Exception as e:
            handle_error(e, "Explicit JOIN 추출 실패")
            return []

    def _extract_implicit_joins(self, normalized_sql: str, tables: Set[str]) -> List[Dict[str, Any]]:
        """Implicit JOIN 관계 추출 (WHERE 절)"""
        try:
            relationships = []

            # WHERE 절에서 조인 조건 찾기
            where_match = re.search(r'\bWHERE\b(.+?)(?:\bGROUP\b|\bORDER\b|\bHAVING\b|$)', normalized_sql, re.IGNORECASE | re.DOTALL)

            if not where_match:
                return relationships

            where_clause = where_match.group(1)

            # 별칭.컬럼 = 별칭.컬럼 패턴
            implicit_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)'

            matches = re.findall(implicit_pattern, where_clause, re.IGNORECASE)

            for match in matches:
                alias1, col1, alias2, col2 = match

                # 별칭에서 테이블명 추정 (단순화)
                table1 = self._resolve_alias_to_table(alias1, tables)
                table2 = self._resolve_alias_to_table(alias2, tables)

                if (table1 and table2 and table1 != table2 and
                    self._is_valid_table_name(table1) and
                    self._is_valid_table_name(table2)):

                    relationships.append({
                        'source_table': table1.upper(),
                        'target_table': table2.upper(),
                        'rel_type': 'JOIN_IMPLICIT',
                        'join_type': 'IMPLICIT_JOIN',
                        'condition': f"{alias1}.{col1} = {alias2}.{col2}",
                        'description': f"IMPLICIT JOIN: {table1} ↔ {table2}"
                    })

            return relationships

        except Exception as e:
            handle_error(e, "Implicit JOIN 추출 실패")
            return []

    def _resolve_alias_to_table(self, alias: str, tables: Set[str]) -> str:
        """별칭을 테이블명으로 해석 (단순화된 로직)"""
        try:
            alias_upper = alias.upper()

            # 1. 별칭이 테이블명과 정확히 일치
            if alias_upper in tables:
                return alias_upper

            # 2. 별칭이 테이블명의 접두사
            for table in tables:
                if table.startswith(alias_upper):
                    return table

            # 3. 테이블명이 별칭을 포함
            for table in tables:
                if alias_upper in table:
                    return table

            # 4. 해석 불가시 별칭 자체를 반환
            return alias_upper

        except Exception as e:
            handle_error(e, f"별칭 해석 실패: {alias}")
            return alias.upper()

    def _remove_duplicate_relationships(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 관계 제거"""
        try:
            unique_relationships = []
            seen = set()

            for rel in relationships:
                # 양방향 중복 제거 (A→B, B→A를 같은 관계로 처리)
                key = tuple(sorted([rel['source_table'], rel['target_table']]))

                if key not in seen:
                    seen.add(key)
                    unique_relationships.append(rel)

            return unique_relationships

        except Exception as e:
            handle_error(e, "중복 관계 제거 실패")
            return relationships