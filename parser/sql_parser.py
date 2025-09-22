
"""
SQL 파서 모듈
- 서브쿼리, UNION, MyBatis 동적 SQL 지원
- 시스템 테이블 및 별칭 필터링
- 설정 기반 패턴 매칭
"""

import re
import yaml
import os
from typing import List, Dict, Set, Any, Optional, Tuple
from util import debug, error, handle_error, PathUtils, ValidationUtils, info, warning


class SqlParser:
    """SQL 파서 클래스"""

    def __init__(self):
        """SQL 파서 초기화"""
        self.path_utils = PathUtils()
        self.oracle_keywords = set()
        self._load_sql_configuration()

    def _load_sql_configuration(self) -> None:
        """oracle_sql_keyword.yaml 파일에서 키워드를 로드하여 self.oracle_keywords 세트에 저장합니다."""
        try:
            config_path = self.path_utils.get_parser_config_path("oracle_sql")
            if not os.path.exists(config_path):
                warning(f"Oracle 키워드 설정 파일을 찾을 수 없습니다: {config_path}")
                return

            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            keywords = set()
            if isinstance(config, dict):
                for key, value in config.items():
                    if key.endswith('_keywords') or key.endswith('_functions'):
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                if isinstance(sub_value, list):
                                    keywords.update([kw.upper() for kw in sub_value])
                        elif isinstance(value, list):
                             keywords.update([kw.upper() for kw in value])

            self.oracle_keywords = keywords
            info(f"Oracle SQL 키워드 {len(self.oracle_keywords)}개 로드 완료.")

        except Exception as e:
            handle_error(e, "Oracle SQL 키워드 설정 로드 실패")

    def extract_tables_and_aliases(self, sql_content: str) -> Dict[str, str]:
        """SQL에서 테이블명과 별칭을 추출하여 맵으로 반환합니다."""
        alias_map = {}
        try:
            # FROM 및 JOIN 절에서 "테이블명 별칭" 패턴 추출
            pattern = r'\b(?:FROM|JOIN)\s+([\w\.]+)(?:\s+AS)?\s+([a-zA-Z_][\w]*)(?=[\s,]|\bON|\bWHERE|\bGROUP|\bORDER|;|$)'
            matches = re.findall(pattern, sql_content, re.IGNORECASE)
            for match in matches:
                table_name = match[0].split('.')[-1].upper()
                alias = match[1].upper()
                if table_name not in self.oracle_keywords and alias not in self.oracle_keywords:
                    alias_map[alias] = table_name

            # 별칭이 없는 테이블도 추가 (FROM table1, table2 ...)
            from_clause_match = re.search(r'\bFROM\s+(.*?)(?=\bWHERE|\bGROUP|\bORDER|\bJOIN|;|$)', sql_content, re.IGNORECASE | re.DOTALL)
            if from_clause_match:
                from_content = from_clause_match.group(1)
                tables_part = from_content.split('ON')[0]
                for table_part in tables_part.split(','):
                    parts = table_part.strip().split()
                    if not parts:  # 빈 parts 방어 처리
                        continue
                    table_name = parts[0].split('.')[-1].upper()
                    if table_name not in self.oracle_keywords and ValidationUtils.is_valid_table_name(table_name):
                        if len(parts) == 1: # 별칭이 없는 경우
                            if table_name not in alias_map.values():
                                alias_map[table_name] = table_name
                        elif len(parts) > 1: # 별칭이 있는 경우 (이미 위에서 처리되었을 수 있음)
                            alias = parts[1].upper()
                            if alias not in alias_map:
                                alias_map[alias] = table_name

        except Exception as e:
            handle_error(e, "테이블 및 별칭 추출 실패")
        
        debug(f"추출된 테이블/별칭 맵: {alias_map}")
        return alias_map

    def extract_table_names(self, sql_content: str) -> Set[str]:
        """
        SQL 내용에서 테이블명을 추출합니다. (단순 패턴 및 키워드 필터링 적용)

        Args:
            sql_content: SQL 컨텐츠

        Returns:
            추출 및 필터링된 테이블명 집합
        """
        try:
            if not sql_content or not sql_content.strip():
                return set()

            # 1. SQL 전처리 (주석 제거, 대문자 변환 등)
            processed_sql = self._preprocess_sql(sql_content)

            # 2. 단순 패턴으로 테이블 후보 추출
            # FROM, JOIN, UPDATE, INTO(INSERT, MERGE), USING 다음에 오는 단어 추출
            patterns = [
                r'\bFROM\s+([\w\.]+)',
                r'\bJOIN\s+([\w\.]+)',
                r'\bUPDATE\s+([\w\.]+)',
                r'\bINTO\s+([\w\.]+)', 
                r'\bUSING\s+([\w\.]+)' 
            ]
            
            candidates = set()
            for pattern in patterns:
                matches = re.findall(pattern, processed_sql, re.IGNORECASE)
                for match in matches:
                    # 소유자.테이블명 형태일 수 있으므로 .으로 분리하여 마지막 부분을 테이블명으로 간주
                    table_name = match.split('.')[-1]
                    candidates.add(table_name.upper())

            # 3. Oracle 키워드 필터링
            validated_tables = {tbl for tbl in candidates if tbl not in self.oracle_keywords and ValidationUtils.is_valid_table_name(tbl)}
            
            debug(f"테이블명 추출 결과: {validated_tables}")
            return validated_tables

        except Exception as e:
            debug(f"테이블명 추출 중 오류: {str(e)}")
            return set()

    def determine_query_type(self, sql_content: str) -> str:
        """
        SQL 쿼리 종류 인식
        
        Args:
            sql_content: SQL 컨텐츠
            
        Returns:
            쿼리 종류 (SQL_SELECT, SQL_INSERT, SQL_UPDATE, SQL_DELETE, SQL_MERGE)
        """
        try:
            if not sql_content or not sql_content.strip():
                return 'SQL_UNKNOWN'

            # 1. SQL 전처리 (주석 제거, 대문자 변환)
            processed_sql = self._preprocess_sql(sql_content)
            
            # 2. 첫 번째 키워드 추출
            # 공백과 특수문자 제거 후 첫 번째 단어 추출
            first_word = processed_sql.strip().split()[0] if processed_sql.strip() else ""
            
            # 3. 쿼리 종류 결정
            if first_word == 'INSERT':
                return 'SQL_INSERT'
            elif first_word == 'UPDATE':
                return 'SQL_UPDATE'
            elif first_word == 'DELETE':
                return 'SQL_DELETE'
            elif first_word == 'MERGE':
                return 'SQL_MERGE'
            else:
                # 그 외 모든 것 (SELECT, WITH, 등)은 SELECT로 처리
                return 'SQL_SELECT'
                
        except Exception as e:
            debug(f"쿼리 종류 인식 중 오류: {str(e)}")
            return 'SQL_UNKNOWN'

    def _preprocess_sql(self, sql_content: str) -> str:
        """SQL 전처리"""
        try:
            # 1. MyBatis 동적 태그 제거
            processed = self._remove_mybatis_tags(sql_content)

            # 2. 주석 제거
            processed = self._remove_comments(processed)

            # 3. 줄바꿈 및 공백 정규화
            processed = self._normalize_whitespace(processed)

            # 4. 바인딩 변수 정규화
            processed = self._normalize_binding_variables(processed)

            # 5. 대문자 변환
            processed = processed.upper()

            return processed

        except Exception as e:
            debug(f"SQL 전처리 중 오류: {str(e)}")
            return sql_content.upper()

    def _remove_mybatis_tags(self, sql_content: str) -> str:
        """MyBatis 동적 태그 제거"""
        try:
            # MyBatis 동적 태그 패턴들 (내용은 유지, 태그만 제거)
            tag_patterns = [
                (r'<if\s+test=["\'][^"\']*["\'][^>]*>(.*?)</if>', r'\1'),
                (r'<choose\s*>(.*?)</choose>', r'\1'),
                (r'<when\s+test=["\'][^"\']*["\'][^>]*>(.*?)</when>', r'\1'),
                (r'<otherwise\s*>(.*?)</otherwise>', r'\1'),
                (r'<where\s*>(.*?)</where>', r' WHERE \1'),
                (r'<set\s*>(.*?)</set>', r' SET \1'),
                (r'<trim[^>]*>(.*?)</trim>', r'\1'),
                (r'<foreach[^>]*>(.*?)</foreach>', r'\1')
            ]

            processed = sql_content
            for pattern, replacement in tag_patterns:
                processed = re.sub(pattern, replacement, processed, flags=re.DOTALL | re.IGNORECASE)

            return processed

        except Exception as e:
            debug(f"MyBatis 태그 제거 중 오류: {str(e)}")
            return sql_content

    def _remove_comments(self, sql_content: str) -> str:
        """SQL 주석 제거"""
        try:
            # 단일 라인 주석 제거 (-- 주석)
            processed = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)

            # 다중 라인 주석 제거 (/* */ 주석)
            processed = re.sub(r'/\*.*?\*/', '', processed, flags=re.DOTALL)

            return processed

        except Exception as e:
            debug(f"SQL 주석 제거 중 오류: {str(e)}")
            return sql_content

    def _normalize_whitespace(self, sql_content: str) -> str:
        """줄바꿈 및 공백 정규화"""
        try:
            # 연속된 공백을 단일 공백으로 변환
            processed = re.sub(r'\s+', ' ', sql_content)

            # 앞뒤 공백 제거
            processed = processed.strip()

            return processed

        except Exception as e:
            debug(f"공백 정규화 중 오류: {str(e)}")
            return sql_content

    def _normalize_binding_variables(self, sql_content: str) -> str:
        """바인딩 변수 정규화"""
        try:
            # MyBatis 바인딩 변수 #{param} -> ?
            processed = re.sub(r'#\{[^}]*\}', '?', sql_content)

            # MyBatis 바인딩 변수 ${param} -> ?
            processed = re.sub(r'\$\{[^}]*\}', '?', processed)

            return processed

        except Exception as e:
            debug(f"바인딩 변수 정규화 중 오류: {str(e)}")
            return sql_content

    def analyze_join_relationships(self, sql_content: str) -> List[Dict[str, Any]]:
        """
        JOIN 관계 분석

        Args:
            sql_content: SQL 컨텐츠

        Returns:
            JOIN 관계 정보 리스트
        """
        try:
            # SQL 전처리
            processed_sql = self._preprocess_sql(sql_content)

            join_relationships = []

            # 명시적 JOIN 분석
            explicit_joins = self._analyze_explicit_joins(processed_sql)
            join_relationships.extend(explicit_joins)

            # 암시적 JOIN 분석 (WHERE 절)
            implicit_joins = self._analyze_implicit_joins(processed_sql)
            join_relationships.extend(implicit_joins)

            return join_relationships

        except Exception as e:
            debug(f"JOIN 관계 분석 중 오류: {str(e)}")
            return []

    def _analyze_explicit_joins(self, sql_content: str) -> List[Dict[str, Any]]:
        """명시적 JOIN 분석"""
        try:
            join_relationships = []

            # 명시적 JOIN 패턴들
            explicit_join_patterns = [
                (r'INNER\s+JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)\s+ON\s+([^,\s]+)\s*=\s*([^,\s]+)', 'INNER_JOIN'),
                (r'LEFT\s+(?:OUTER\s+)?JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)\s+ON\s+([^,\s]+)\s*=\s*([^,\s]+)', 'LEFT_JOIN'),
                (r'RIGHT\s+(?:OUTER\s+)?JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)\s+ON\s+([^,\s]+)\s*=\s*([^,\s]+)', 'RIGHT_JOIN'),
                (r'FULL\s+(?:OUTER\s+)?JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)\s+ON\s+([^,\s]+)\s*=\s*([^,\s]+)', 'FULL_JOIN'),
                (r'CROSS\s+JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)', 'CROSS_JOIN'),
                (r'NATURAL\s+JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)', 'NATURAL_JOIN')
            ]

            for pattern, join_type in explicit_join_patterns:
                matches = re.finditer(pattern, sql_content)
                for match in matches:
                    if join_type in ['CROSS_JOIN', 'NATURAL_JOIN']:
                        # ON 절이 없는 JOIN
                        table_name = match.group(1)
                        table_alias = match.group(2)

                        join_info = {
                            'join_type': join_type,
                            'table_name': table_name,
                            'table_alias': table_alias,
                            'relationship_type': 'JOIN_EXPLICIT'
                        }
                    else:
                        # ON 절이 있는 JOIN
                        table_name = match.group(1)
                        table_alias = match.group(2)
                        left_col = match.group(3)
                        right_col = match.group(4)

                        join_info = {
                            'join_type': join_type,
                            'table_name': table_name,
                            'table_alias': table_alias,
                            'left_column': left_col,
                            'right_column': right_col,
                            'relationship_type': 'JOIN_EXPLICIT'
                        }

                    if ValidationUtils.is_valid_table_name(table_name):
                        join_relationships.append(join_info)
                        debug(f"명시적 JOIN 분석: {join_info}")

            return join_relationships

        except Exception as e:
            debug(f"명시적 JOIN 분석 중 오류: {str(e)}")
            return []

    def _analyze_implicit_joins(self, sql_content: str) -> List[Dict[str, Any]]:
        """암시적 JOIN 분석 (WHERE 절)"""
        try:
            join_relationships = []

            # WHERE 절 추출
            where_pattern = r'WHERE\s+(.+?)(?=\s+(?:GROUP|ORDER|HAVING|UNION|$))'
            where_match = re.search(where_pattern, sql_content, re.DOTALL)

            if where_match:
                where_clause = where_match.group(1)

                # 암시적 조인 조건 패턴들
                implicit_join_patterns = [
                    # alias.col = alias.col
                    r'([A-Z_][A-Z0-9_]*)\\.([A-Z_][A-Z0-9_]*)\s*=\s*([A-Z_][A-Z0-9_]*)\\.([A-Z_][A-Z0-9_]*)',
                    # Oracle (+) 외부 조인
                    r'([A-Z_][A-Z0-9_]*)\\.([A-Z_][A-Z0-9_]*)\s*\(\+\)\s*=\s*([A-Z_][A-Z0-9_]*)\\.([A-Z_][A-Z0-9_]*)',
                    # 단순 조인: col = col
                    r'\b([A-Z_][A-Z0-9_]*)\s*=\s*([A-Z_][A-Z0-9_]*)\b'
                ]

                for pattern in implicit_join_patterns:
                    matches = re.finditer(pattern, where_clause)
                    for match in matches:
                        if len(match.groups()) == 4:  # alias.col = alias.col 형태
                            left_alias = match.group(1)
                            left_col = match.group(2)
                            right_alias = match.group(3)
                            right_col = match.group(4)

                            join_info = {
                                'join_type': 'IMPLICIT',
                                'left_table_alias': left_alias,
                                'left_column': left_col,
                                'right_table_alias': right_alias,
                                'right_column': right_col,
                                'relationship_type': 'JOIN_IMPLICIT'
                            }
                        elif len(match.groups()) == 2:  # col = col 형태
                            left_col = match.group(1)
                            right_col = match.group(2)

                            join_info = {
                                'join_type': 'IMPLICIT',
                                'left_column': left_col,
                                'right_column': right_col,
                                'relationship_type': 'WHERE_JOIN'
                            }
                        else:
                            continue

                        join_relationships.append(join_info)
                        debug(f"암시적 JOIN 분석: {join_info}")

            return join_relationships

        except Exception as e:
            debug(f"암시적 JOIN 분석 중 오류: {str(e)}")
            return []
