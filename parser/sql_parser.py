"""
SQL 파서 모듈
- 서브쿼리, UNION, MyBatis 동적 SQL 지원
- 시스템 테이블 및 별칭 필터링
- 설정 기반 패턴 매칭
"""

import re
import yaml
from typing import List, Dict, Set, Any, Optional, Tuple
from util import debug, error, handle_error, PathUtils, ValidationUtils


class SqlParser:
    """SQL 파서 클래스"""

    def __init__(self):
        """SQL 파서 초기화"""
        self.path_utils = PathUtils()
        self.sql_keywords = None
        self.exclude_patterns = None
        self.system_functions = None
        self._load_sql_configuration()

    def _load_sql_configuration(self) -> None:
        """SQL 설정 파일 로드"""
        try:
            # 공통함수 사용 (하드코딩 금지)
            config_path = self.path_utils.join_path('config', 'parser', 'sql_keyword.yaml')

            from util.file_utils import FileUtils
            file_info = FileUtils.get_file_info(config_path)

            if file_info['exists']:
                content = FileUtils.read_file_content(config_path)
                self.sql_keywords = yaml.safe_load(content)

                # 설정에서 패턴들 로드
                self.exclude_patterns = self.sql_keywords.get('exclude_table_patterns', [])
                self.system_functions = self._extract_system_functions()

                debug(f"SQL 설정 파일 로드 완료: {config_path}")
            else:
                self._load_default_configuration()
                debug("기본 SQL 설정 사용")

        except Exception as e:
            debug(f"SQL 설정 로드 실패: {str(e)}")
            self._load_default_configuration()

    def _load_default_configuration(self) -> None:
        """기본 SQL 설정 로드"""
        try:
            # 기본 제외 패턴 설정
            self.exclude_patterns = [
                r'^DUAL$',
                r'^SYS\.',
                r'^USER_',
                r'^ALL_',
                r'^DBA_',
                r'^V\$',
                r'^GV\$',
                r'^X\$',
                r'^TEMP_',
                r'^TMP_'
            ]

            # 기본 시스템 함수 설정
            self.system_functions = {
                'NOW', 'SYSDATE', 'SYSTIMESTAMP', 'CURRENT_DATE', 'CURRENT_TIMESTAMP',
                'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ROUND', 'TRUNC',
                'SUBSTR', 'LENGTH', 'UPPER', 'LOWER', 'TO_CHAR', 'TO_DATE'
            }

        except Exception as e:
            handle_error(e, "기본 SQL 설정 로드 실패")

    def _extract_system_functions(self) -> Set[str]:
        """설정에서 시스템 함수 목록 추출"""
        try:
            functions = set()

            if self.sql_keywords:
                # 집계 함수
                if 'sql_function_patterns' in self.sql_keywords:
                    for category, patterns in self.sql_keywords['sql_function_patterns'].items():
                        for pattern in patterns:
                            # 패턴에서 함수명 추출 (예: "COUNT\\(.*\\)" -> "COUNT")
                            func_name = re.sub(r'\\.*', '', pattern).strip()
                            if func_name:
                                functions.add(func_name)

                # 예약어 중 함수들
                reserved_keywords = self.sql_keywords.get('sql_reserved_keywords', [])
                function_keywords = {
                    'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ROUND', 'TRUNC',
                    'SUBSTR', 'LENGTH', 'UPPER', 'LOWER', 'TO_CHAR', 'TO_DATE',
                    'NVL', 'DECODE', 'COALESCE', 'SYSDATE', 'SYSTIMESTAMP'
                }

                for keyword in reserved_keywords:
                    if keyword in function_keywords:
                        functions.add(keyword)

            return functions

        except Exception as e:
            debug(f"시스템 함수 추출 중 오류: {str(e)}")
            return {'NOW', 'SYSDATE', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX'}

    def extract_table_names(self, sql_content: str) -> Set[str]:
        """
        테이블명 추출

        Args:
            sql_content: SQL 컨텐츠

        Returns:
            추출된 테이블명 집합
        """
        try:
            if not sql_content or not sql_content.strip():
                return set()

            # 1. SQL 전처리
            processed_sql = self._preprocess_sql(sql_content)

            table_names = set()

            # 2. UNION 쿼리 분할 처리
            union_queries = self._split_union_queries(processed_sql)

            for query in union_queries:
                # 3. 서브쿼리에서 테이블 추출
                subquery_tables = self._extract_from_subqueries(query)
                table_names.update(subquery_tables)

                # 4. 메인 쿼리에서 테이블 추출
                main_tables = self._extract_from_main_query(query)
                table_names.update(main_tables)

            # 5. 테이블명 필터링 및 검증
            validated_tables = self._validate_and_filter_tables(table_names)

            debug(f"테이블명 추출 결과: {validated_tables}")
            return validated_tables

        except Exception as e:
            debug(f"테이블명 추출 중 오류: {str(e)}")
            return set()

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

    def _split_union_queries(self, sql_content: str) -> List[str]:
        """UNION으로 구분된 쿼리 분할"""
        try:
            # UNION ALL 또는 UNION으로 분할
            queries = re.split(r'\bUNION\s+(?:ALL\s+)?', sql_content, flags=re.IGNORECASE)

            # 빈 쿼리 제거 및 공백 정리
            valid_queries = []
            for query in queries:
                query = query.strip()
                if query:
                    valid_queries.append(query)

            return valid_queries if valid_queries else [sql_content]

        except Exception as e:
            debug(f"UNION 쿼리 분할 중 오류: {str(e)}")
            return [sql_content]

    def _extract_from_subqueries(self, sql_content: str) -> Set[str]:
        """서브쿼리에서 테이블명 추출"""
        try:
            table_names = set()

            # 서브쿼리 패턴들
            subquery_patterns = [
                # EXISTS 서브쿼리: EXISTS (SELECT ... FROM table ...)
                r'EXISTS\s*\(\s*SELECT\s+.*?\s+FROM\s+([A-Z_][A-Z0-9_]*)',

                # IN 서브쿼리: IN (SELECT ... FROM table ...)
                r'IN\s*\(\s*SELECT\s+.*?\s+FROM\s+([A-Z_][A-Z0-9_]*)',

                # 일반 서브쿼리: (SELECT ... FROM table ...)
                r'\(\s*SELECT\s+.*?\s+FROM\s+([A-Z_][A-Z0-9_]*)',

                # 상관 서브쿼리: SELECT ... FROM table WHERE col = (SELECT ... FROM table2 ...)
                r'=\s*\(\s*SELECT\s+.*?\s+FROM\s+([A-Z_][A-Z0-9_]*)',

                # 집계 함수 서브쿼리: (SELECT COUNT(*) FROM table WHERE ...)
                r'\(\s*SELECT\s+(?:COUNT|SUM|AVG|MIN|MAX)\s*\([^)]*\)\s+FROM\s+([A-Z_][A-Z0-9_]*)'
            ]

            for pattern in subquery_patterns:
                matches = re.finditer(pattern, sql_content, re.DOTALL)
                for match in matches:
                    table_name = match.group(1).strip()

                    # 별칭이 있을 수 있으므로 첫 번째 토큰만 사용
                    table_name = table_name.split()[0] if ' ' in table_name else table_name

                    if self._is_valid_table_name_candidate(table_name):
                        table_names.add(table_name)
                        debug(f"서브쿼리에서 테이블 추출: {table_name}")

            return table_names

        except Exception as e:
            debug(f"서브쿼리 테이블 추출 중 오류: {str(e)}")
            return set()

    def _extract_from_main_query(self, sql_content: str) -> Set[str]:
        """메인 쿼리에서 테이블명 추출"""
        try:
            table_names = set()

            # FROM 절에서 테이블 추출
            from_tables = self._extract_from_clause(sql_content)
            table_names.update(from_tables)

            # JOIN 절에서 테이블 추출
            join_tables = self._extract_join_clause(sql_content)
            table_names.update(join_tables)

            # DML 문에서 테이블 추출
            dml_tables = self._extract_dml_tables(sql_content)
            table_names.update(dml_tables)

            return table_names

        except Exception as e:
            debug(f"메인 쿼리 테이블 추출 중 오류: {str(e)}")
            return set()

    def _extract_from_clause(self, sql_content: str) -> Set[str]:
        """FROM 절에서 테이블명 추출"""
        try:
            table_names = set()

            # FROM 절 패턴들 (개선된 버전)
            from_patterns = [
                # 단일 테이블: FROM table_name alias
                r'\bFROM\s+([A-Z_][A-Z0-9_]*)\s+(?:[A-Z_][A-Z0-9_]*\s+)?(?=WHERE|GROUP|ORDER|HAVING|UNION|JOIN|$|;)',

                # 단일 테이블 (별칭 없음): FROM table_name WHERE/GROUP/ORDER/등
                r'\bFROM\s+([A-Z_][A-Z0-9_]*)\s+(?=WHERE|GROUP|ORDER|HAVING|UNION|$|;)',

                # 콤마로 구분된 다중 테이블: FROM table1, table2, table3
                r'\bFROM\s+([A-Z_][A-Z0-9_]*(?:\s+[A-Z_][A-Z0-9_]*)?(?:\s*,\s*[A-Z_][A-Z0-9_]*(?:\s+[A-Z_][A-Z0-9_]*)?)*)',
            ]

            for pattern in from_patterns:
                matches = re.finditer(pattern, sql_content)
                for match in matches:
                    from_clause = match.group(1).strip()

                    # 콤마로 구분된 테이블들 처리
                    if ',' in from_clause:
                        table_parts = from_clause.split(',')
                        for part in table_parts:
                            table_name = self._extract_table_from_part(part.strip())
                            if table_name and self._is_valid_table_name_candidate(table_name):
                                table_names.add(table_name)
                                debug(f"FROM 절(다중)에서 테이블 추출: {table_name}")
                    else:
                        # 단일 테이블 처리
                        table_name = self._extract_table_from_part(from_clause)
                        if table_name and self._is_valid_table_name_candidate(table_name):
                            table_names.add(table_name)
                            debug(f"FROM 절(단일)에서 테이블 추출: {table_name}")

            return table_names

        except Exception as e:
            debug(f"FROM 절 테이블 추출 중 오류: {str(e)}")
            return set()

    def _extract_join_clause(self, sql_content: str) -> Set[str]:
        """JOIN 절에서 테이블명 추출"""
        try:
            table_names = set()

            # JOIN 패턴들 (모든 JOIN 타입 지원)
            join_patterns = [
                r'\bINNER\s+JOIN\s+([A-Z_][A-Z0-9_]*)',
                r'\bLEFT\s+(?:OUTER\s+)?JOIN\s+([A-Z_][A-Z0-9_]*)',
                r'\bRIGHT\s+(?:OUTER\s+)?JOIN\s+([A-Z_][A-Z0-9_]*)',
                r'\bFULL\s+(?:OUTER\s+)?JOIN\s+([A-Z_][A-Z0-9_]*)',
                r'\bCROSS\s+JOIN\s+([A-Z_][A-Z0-9_]*)',
                r'\bNATURAL\s+JOIN\s+([A-Z_][A-Z0-9_]*)',
                r'\bJOIN\s+([A-Z_][A-Z0-9_]*)'  # 기본 JOIN
            ]

            for pattern in join_patterns:
                matches = re.finditer(pattern, sql_content)
                for match in matches:
                    table_name = match.group(1).strip()

                    if self._is_valid_table_name_candidate(table_name):
                        table_names.add(table_name)
                        debug(f"JOIN 절에서 테이블 추출: {table_name}")

            return table_names

        except Exception as e:
            debug(f"JOIN 절 테이블 추출 중 오류: {str(e)}")
            return set()

    def _extract_dml_tables(self, sql_content: str) -> Set[str]:
        """DML 문에서 테이블명 추출"""
        try:
            table_names = set()

            # DML 패턴들
            dml_patterns = [
                r'\bINSERT\s+INTO\s+([A-Z_][A-Z0-9_]*)',
                r'\bUPDATE\s+([A-Z_][A-Z0-9_]*)',
                r'\bDELETE\s+FROM\s+([A-Z_][A-Z0-9_]*)',
                r'\bMERGE\s+INTO\s+([A-Z_][A-Z0-9_]*)',
                r'\bTRUNCATE\s+TABLE\s+([A-Z_][A-Z0-9_]*)'
            ]

            for pattern in dml_patterns:
                matches = re.finditer(pattern, sql_content)
                for match in matches:
                    table_name = match.group(1).strip()

                    if self._is_valid_table_name_candidate(table_name):
                        table_names.add(table_name)
                        debug(f"DML 문에서 테이블 추출: {table_name}")

            return table_names

        except Exception as e:
            debug(f"DML 테이블 추출 중 오류: {str(e)}")
            return set()

    def _extract_table_from_part(self, table_part: str) -> Optional[str]:
        """테이블 부분에서 테이블명 추출 (별칭 처리)"""
        try:
            if not table_part:
                return None

            # 공백으로 분할하여 첫 번째가 테이블명, 나머지는 별칭
            tokens = table_part.split()
            if tokens:
                return tokens[0].strip()

            return None

        except Exception as e:
            debug(f"테이블 부분 파싱 중 오류: {str(e)}")
            return None

    def _is_valid_table_name_candidate(self, table_name: str) -> bool:
        """테이블명 후보 기본 검증 (필터링 전 단계)"""
        try:
            if not table_name or len(table_name) < 2:
                return False

            # 기본 패턴 검사 (영문자로 시작, 영문자/숫자/언더스코어 조합)
            if not re.match(r'^[A-Z][A-Z0-9_]*$', table_name):
                return False

            return True

        except Exception as e:
            debug(f"테이블명 후보 검증 중 오류: {str(e)}")
            return False

    def _validate_and_filter_tables(self, table_names: Set[str]) -> Set[str]:
        """테이블명 집합 검증 및 필터링"""
        try:
            validated_tables = set()

            for table_name in table_names:
                if ValidationUtils.is_valid_table_name(table_name):
                    validated_tables.add(table_name)
                else:
                    debug(f"테이블명 필터링됨: {table_name}")

            return validated_tables

        except Exception as e:
            debug(f"테이블명 검증 및 필터링 중 오류: {str(e)}")
            return table_names

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

                    if self._is_valid_table_name_candidate(table_name):
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
                    r'([A-Z_][A-Z0-9_]*)\\.([A-Z_][A-Z0-9_]*)\s*\\(\\+\\)\s*=\s*([A-Z_][A-Z0-9_]*)\\.([A-Z_][A-Z0-9_]*)',
                    # 단순 조인: col = col
                    r'\\b([A-Z_][A-Z0-9_]*)\\s*=\\s*([A-Z_][A-Z0-9_]*)\\b'
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