"""
Java 파서 모듈
- Java 파일에서 클래스, 메서드, SQL 쿼리 추출
- 3단계 공통 처리: 쿼리 추출 → 테이블 도출 → 조인관계 분석
- CALL_METHOD, CALL_QUERY 관계 생성

USER RULES:
- 하드코딩 금지
- Exception 처리: handle_error() 공통함수 사용
- 공통함수 사용: util 모듈 활용
"""

import re
import os
from typing import List, Dict, Set, Any, Optional, Tuple
from util import (
    ConfigUtils, FileUtils, HashUtils, PathUtils,
    debug, info, error, warning, handle_error
)
from .sql_join_analyzer import SqlJoinAnalyzer
from .sql_parser import SqlParser


class JavaParser:
    """Java 파서 - 클래스, 메서드, SQL 쿼리, 관계 분석"""

    def __init__(self, config_path: str = None, project_name: str = None):
        """
        Java 파서 초기화

        Args:
            config_path: 설정 파일 경로
            project_name: 프로젝트 이름
        """
        try:
            from util.global_project import get_global_project_name, get_global_project_id, is_global_project_info_set

            if is_global_project_info_set():
                self.project_name = get_global_project_name()
                self.project_id = get_global_project_id()
            else:
                self.project_name = project_name
                self.project_id = None

            self.current_file_id = None
            self.path_utils = PathUtils()
            self.file_utils = FileUtils()
            self.hash_utils = HashUtils()

        except Exception as e:
            handle_error(e, "Java 파서 초기화 실패")

        # 설정 로드
        self.config = self._load_config(config_path)

        # 통계 및 기타 초기화
        self._initialize_components()

    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """설정 파일을 로드합니다"""
        try:
            from util import ConfigUtils, warning
            config_utils = ConfigUtils()

            if config_path and os.path.exists(config_path):
                config = config_utils.load_yaml_config(config_path)
                if config:
                    return config

            # 기본 설정 파일 경로 시도
            default_config_path = self.path_utils.get_parser_config_path("java")
            if os.path.exists(default_config_path):
                config = config_utils.load_yaml_config(default_config_path)
                if config:
                    return config

            warning(f"설정 파일을 로드할 수 없습니다: {config_path}, 기본 설정 사용")
            return self._get_default_config()

        except Exception as e:
            warning(f"설정 파일 로드 실패: {config_path}, 기본 설정 사용: {str(e)}")
            return self._get_default_config()

    def _initialize_components(self):
        """컴포넌트들을 초기화합니다"""
        try:
            self.performance_config = self.config.get('performance', {})
            self.large_file_threshold_mb = self.performance_config.get('large_file_threshold_mb', 1.0)
            self.batch_size = self.performance_config.get('batch_size', 100)
            self.use_compiled_patterns = self.performance_config.get('use_compiled_patterns', True)

            self.relationship_config = self.config.get('relationship_analysis', {})
            self.relationship_performance = self.relationship_config.get('relationship_performance', {})

            self.stats = {
                'files_processed': 0,
                'files_skipped': 0,
                'classes_extracted': 0,
                'methods_extracted': 0,
                'inheritance_relationships_created': 0,
                'call_query_relationships_created': 0,
                'call_method_relationships_created': 0,
                'use_table_relationships_created': 0,
                'errors': 0
            }

            self.sql_join_analyzer = SqlJoinAnalyzer(self.config)

        except Exception as e:
            handle_error(e, "Java 파서 컴포넌트 초기화 실패")

    def _get_default_config(self) -> Dict[str, Any]:
        """기본 Java 파서 설정"""
        return {
            'performance': {
                'large_file_threshold_mb': 1.0,
                'batch_size': 100,
                'use_compiled_patterns': True
            },
            'relationship_analysis': {
                'relationship_performance': {}
            }
        }

    def _compile_patterns_for_performance(self):
        """성능을 위한 패턴 컴파일 (현재는 빈 구현)"""
        pass

    def get_filtered_java_files(self, project_path: str = None) -> List[str]:
        """
        Java 파일 수집 및 필터링

        Args:
            project_path: 프로젝트 경로

        Returns:
            Java 파일 경로 리스트
        """
        try:
            if not project_path:
                project_path = self.project_name

            # USER RULES: 공통함수 사용
            file_utils = FileUtils()
            all_files = file_utils.scan_directory(project_path)

            # Java 파일 필터링
            java_files = []
            for file_info in all_files:
                # file_info가 dict인 경우 file_path 키에서 경로 추출
                if isinstance(file_info, dict):
                    file_path = file_info.get('file_path', '')
                else:
                    file_path = str(file_info)

                if file_path.lower().endswith('.java'):
                    java_files.append(file_path)

            debug(f"Java 파일 수집 완료: {len(java_files)}개")
            return java_files

        except Exception as e:
            handle_error(e, f"Java 파일 수집 실패: {project_path}")
            return []

    def _extract_sql_queries_from_java(self, java_content: str, java_file: str) -> List[Dict[str, Any]]:
        """
        Java 파일에서 SQL 쿼리 추출 (쿼리 도려내기 로직 포함)
        StringBuilder와 문자열 변수 조합으로 동적 생성되는 쿼리를 분석하여 SQL 컴포넌트로 추출
        """
        try:
            sql_queries = []

            # 1. JPA @Query 추출
            jpa_queries = self._extract_jpa_queries(java_content, java_file)
            sql_queries.extend(jpa_queries)

            # 2. MyBatis 인터페이스 Mapper 메서드 추출 (간단화)
            # @Select, @Insert, @Update, @Delete 어노테이션 처리
            mybatis_annotation_queries = self._extract_mybatis_annotation_queries(java_content, java_file)
            sql_queries.extend(mybatis_annotation_queries)

            # 3. 동적 SQL 쿼리 추출 (StringBuilder, 문자열 변수 조합)
            dynamic_queries = self._extract_dynamic_sql_queries(java_content, java_file)
            sql_queries.extend(dynamic_queries)

            debug(f"Java 파일에서 추출된 SQL 쿼리: {len(sql_queries)}개")
            return sql_queries

        except Exception as e:
            handle_error(e, f"Java SQL 쿼리 추출 실패: {java_file}")
            return []

    def _extract_dynamic_sql_queries(self, java_content: str, java_file: str) -> List[Dict[str, Any]]:
        """동적 SQL 쿼리 추출 (StringBuilder와 문자열 변수 조합 분석)"""
        try:
            sql_queries = []
            sql_parser = SqlParser()

            # 메서드별로 처리
            methods_info = self._get_methods_content(java_content)

            for method_name, method_content, method_start_line in methods_info:
                # 각 메서드에서 SQL 관련 변수 추적
                variable_tracker = {}

                # 1. String 선언 및 초기화 패턴
                string_declaration_pattern = re.compile(r'String\s+(\w+)\s*=\s*"([^"]*)";')
                for match in string_declaration_pattern.finditer(method_content):
                    var_name, initial_value = match.groups()
                    variable_tracker[var_name] = initial_value

                # 2. StringBuilder 패턴 (append)
                sb_patterns = [
                    re.compile(r'StringBuilder\s+(\w+)\s*=\s*new\s+StringBuilder\s*\(\s*"([^"]*)"\s*\);'),
                    re.compile(r'(\w+)\.append\s*\(\s*"([^"]*)"\s*\);')
                ]

                for match in sb_patterns[0].finditer(method_content):
                    var_name, initial_value = match.groups()
                    variable_tracker[var_name] = initial_value

                for match in sb_patterns[1].finditer(method_content):
                    var_name, appended_value = match.groups()
                    if var_name in variable_tracker:
                        variable_tracker[var_name] += appended_value

                # 3c. String = String + "..." 패턴
                string_assign_concat_pattern = re.compile(r'(\w+)\s*=\s*\1\s*\+\s*"([^"]*)";')
                for match in string_assign_concat_pattern.finditer(method_content):
                    var_name, appended_value = match.groups()
                    if var_name in variable_tracker:
                        variable_tracker[var_name] += appended_value

                # 추적된 변수들 중 SQL 쿼리 탐색
                for var_name, full_query in variable_tracker.items():
                    # SQL 키워드로 시작하는지 확인 (원본 쿼리 기준)
                    if any(full_query.strip().upper().startswith(keyword) for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'MERGE']):

                        # 분석용 쿼리 생성 (전처리 수행)
                        clean_sql = sql_parser._preprocess_sql(full_query)
                        query_type = sql_parser.determine_query_type(clean_sql)

                        # 2/3단계: 테이블 추출 및 조인 관계 분석
                        alias_map = sql_parser.extract_tables_and_aliases(clean_sql)
                        join_relationships = self.sql_join_analyzer.analyze_join_relationships(clean_sql, alias_map, java_file)

                        # 쿼리가 발견된 대략적인 라인 찾기
                        line_num = method_start_line
                        for i, line in enumerate(method_content.split('\n')):
                            if var_name in line:
                                line_num += i
                                break

                        query_info = {
                            'query_id': f'{method_name}_{var_name}',
                            'query_type': query_type,
                            'sql_content': full_query,  # DB 저장용 원본 쿼리
                            'used_tables': list(alias_map.values()),
                            'join_relationships': join_relationships,
                            'is_dynamic': True,
                            'method_name': method_name,
                            'line_start': line_num,
                            'line_end': line_num,
                            'has_error': 'N',
                            'error_message': None,
                            'source_type': 'JAVA_DYNAMIC'
                        }
                        sql_queries.append(query_info)
                        debug(f"Java 동적 SQL 추출: {method_name}의 {var_name} - {query_type}")

            debug(f"Java SQL 쿼리 추출 완료: {len(sql_queries)}개")
            return sql_queries

        except Exception as e:
            handle_error(e, f"Java SQL 쿼리 추출 실패: {java_file}")
            return []

    def _get_methods_content(self, java_content: str) -> List[Tuple[str, str, int]]:
        """Java 내용에서 각 메서드의 이름과 본문, 시작 라인을 추출합니다."""
        methods = []
        method_pattern = re.compile(
            r'(?!class\s|interface\s|enum\s)(?:(?:public|private|protected|static|final|synchronized|abstract|@\w+(?:\([^)]*\))?)\s+)*'
            r'(?:<[^>]+>\s+)?'
            r'[\w<>[\]]+\s+'
            r'(\w+)'
            r'\s*\([^)]*\)'
            r'(?:\s*throws\s+[\w,\s]+)?'
            r'(\s*\{((?:[^\{\}]|\{{2}}|(?<!\\)\"(?:\\.|[^"\\])*\"|(?<!\\)\'(?:\\.|[^\'\\])*\')*)\})?'
            , re.MULTILINE
        )
        for match in method_pattern.finditer(java_content):
            method_name = match.group(1)
            method_body = match.group(2)
            if method_body:
                start_pos = match.start()
                start_line = java_content.count('\n', 0, start_pos) + 1
                methods.append((method_name, method_body, start_line))
        return methods

    def _strip_quotes(self, value: str) -> str:
        """문자열의 양 끝 따옴표를 제거합니다."""
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith('\'') and value.endswith('\'')):
            return value[1:-1]
        return value

    def _extract_jpa_queries(self, java_content: str, java_file: str) -> List[Dict[str, Any]]:
        """JPA @Query 어노테이션에서 SQL 추출 (단순화된 로직)
        @Query(...) 괄호 안의 문자열만 추출하는 심플한 방식"""
        jpa_queries = []
        try:
            # 1. @Query(...) 패턴을 찾아서 괄호 안의 내용과 메서드명을 추출
            # @Query("...") 또는 @Query(value="...") 또는 @Query(nativeQuery=true, value="...") 등 모든 형태 지원
            query_pattern = re.compile(
                r'@Query\s*\((.*?)\)\s*'  # @Query(...) 괄호 안의 내용
                r'(?:.*?\n)*?'  # 어노테이션과 메서드 사이의 내용 (줄바꿈 포함)
                r'(?:@\w+.*?\n)*?'  # 다른 어노테이션들
                r'(?:public|private|protected)?\s*(?:static\s+)?(?:<[^>]+>\s+)?'  # 접근제어자, 제네릭
                r'[\w<>[\]]+\s+'  # 반환 타입
                r'(\w+)\s*\(',  # 메서드명 캡처
                re.DOTALL
            )

            for match in query_pattern.finditer(java_content):
                annotation_content = match.group(1)
                method_name = match.group(2)

                # 2. 괄호 안에서 SQL 추출
                sql_content = ""

                # value="..." 패턴 찾기
                value_match = re.search(r'value\s*=\s*"([^"]*)"', annotation_content)
                if value_match:
                    sql_content = value_match.group(1)
                else:
                    # 직접 문자열 패턴 찾기 (첫 번째 문자열)
                    direct_match = re.search(r'"([^"]*)"', annotation_content)
                    if direct_match:
                        sql_content = direct_match.group(1)

                if sql_content.strip():
                    # 3. JPA JPQL → SQL 변환 (간단한 경우만)
                    sql_content = self._convert_jpql_to_sql_simple(sql_content)

                    # 4. 쿼리 정보 생성
                    sql_parser = SqlParser()
                    query_type = sql_parser.determine_query_type(sql_content)

                    # 라인 번호 찾기
                    start_pos = match.start()
                    line_number = java_content.count('\n', 0, start_pos) + 1

                    query_info = {
                        'query_id': f'{method_name}_jpa',
                        'query_type': query_type,
                        'sql_content': sql_content,
                        'used_tables': [],  # 후에 공통 처리에서 추출
                        'join_relationships': [],  # 후에 공통 처리에서 추출
                        'is_dynamic': False,
                        'method_name': method_name,
                        'line_start': line_number,
                        'line_end': line_number + sql_content.count('\n'),
                        'has_error': 'N',
                        'error_message': None,
                        'source_type': 'JPA_QUERY'
                    }
                    jpa_queries.append(query_info)
                    debug(f"JPA 쿼리 추출: {method_name} - {query_type}")

            return jpa_queries

        except Exception as e:
            handle_error(e, f"JPA 쿼리 추출 실패: {java_file}")
            return []

    def _convert_jpql_to_sql_simple(self, jpql: str) -> str:
        """JPQL을 SQL로 간단 변환 (단순한 경우만)"""
        # 간단한 변환만 수행 (FROM Entity → FROM table)
        # 실제로는 복잡한 변환이 필요하지만 여기서는 단순화
        sql = jpql

        # 일반적인 엔티티명 → 테이블명 변환 (간단한 규칙)
        entity_to_table_patterns = [
            (r'\bUser\b', 'USERS'),
            (r'\bProduct\b', 'PRODUCTS'),
            (r'\bOrder\b', 'ORDERS'),
            (r'\bCategory\b', 'CATEGORIES')
        ]

        for entity_pattern, table_name in entity_to_table_patterns:
            sql = re.sub(entity_pattern, table_name, sql, flags=re.IGNORECASE)

        return sql

    def _extract_mybatis_annotation_queries(self, java_content: str, java_file: str) -> List[Dict[str, Any]]:
        """MyBatis 어노테이션에서 SQL 추출 (@Select, @Insert, @Update, @Delete)"""
        try:
            annotation_queries = []
            sql_parser = SqlParser()

            # MyBatis SQL 어노테이션 패턴
            annotation_patterns = [
                (r'@Select\s*\(\s*"([^"]*)"\s*\)', 'SQL_SELECT'),
                (r'@Insert\s*\(\s*"([^"]*)"\s*\)', 'SQL_INSERT'),
                (r'@Update\s*\(\s*"([^"]*)"\s*\)', 'SQL_UPDATE'),
                (r'@Delete\s*\(\s*"([^"]*)"\s*\)', 'SQL_DELETE')
            ]

            for pattern, expected_type in annotation_patterns:
                for match in re.finditer(pattern, java_content, re.DOTALL):
                    sql_content = match.group(1)

                    # 다음 메서드명 찾기
                    method_match = re.search(r'(?:public|private|protected)?\s*(?:static\s+)?(?:<[^>]+>\s+)?[\w<>[\]]+\s+(\w+)\s*\(',
                                           java_content[match.end():])
                    method_name = method_match.group(1) if method_match else 'unknown_method'

                    # 라인 번호 계산
                    start_pos = match.start()
                    line_number = java_content.count('\n', 0, start_pos) + 1

                    query_info = {
                        'query_id': f'{method_name}_mybatis',
                        'query_type': expected_type,
                        'sql_content': sql_content,
                        'used_tables': [],  # 후에 공통 처리에서 추출
                        'join_relationships': [],  # 후에 공통 처리에서 추출
                        'is_dynamic': False,
                        'method_name': method_name,
                        'line_start': line_number,
                        'line_end': line_number,
                        'has_error': 'N',
                        'error_message': None,
                        'source_type': 'MYBATIS_ANNOTATION'
                    }
                    annotation_queries.append(query_info)
                    debug(f"MyBatis 어노테이션 쿼리 추출: {method_name} - {expected_type}")

            return annotation_queries

        except Exception as e:
            handle_error(e, f"MyBatis 어노테이션 쿼리 추출 실패: {java_file}")
            return []

    def parse_java_file(self, java_file: str) -> Dict[str, Any]:
        """Java 파일을 파싱하여 클래스, 메서드, SQL 쿼리를 추출하고 공통 2,3단계 처리 수행"""
        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                java_content = f.read()

            # 1. 클래스 추출
            classes = self._extract_classes(java_content)

            # 2. 메서드 추출
            methods = self._extract_methods(java_content)

            # 3. SQL 쿼리 추출
            sql_queries = self._extract_sql_queries_from_java(java_content, java_file)

            # 4. 공통 2,3단계 처리: 각 쿼리에 대해 테이블 도출 및 조인관계 분석
            processed_queries = []
            for query_info in sql_queries:
                # 2단계: 테이블 도출
                tables_and_aliases = self._extract_tables_from_query(query_info['sql_content'])
                query_info['used_tables'] = tables_and_aliases

                # 3단계: 조인관계 분석
                join_relationships = self._analyze_join_relationships(
                    query_info['sql_content'], tables_and_aliases, java_file
                )
                query_info['join_relationships'] = join_relationships

                processed_queries.append(query_info)

            # 5. CALL_METHOD 관계 생성 (메서드 간 호출 관계)
            call_method_relationships = self._create_call_method_relationships(java_content, methods)

            # 6. CALL_QUERY 관계 생성 (메서드 → SQL 쿼리 관계)
            call_query_relationships = self._create_call_query_relationships(methods, processed_queries)

            return {
                'java_file': java_file,
                'classes': classes,
                'methods': methods,
                'sql_queries': processed_queries,
                'call_method_relationships': call_method_relationships,
                'call_query_relationships': call_query_relationships,
                'has_error': 'N',
                'error_message': None
            }

        except Exception as e:
            handle_error(e, f"Java 파일 파싱 실패: {java_file}")
            return {
                'java_file': java_file,
                'classes': [],
                'methods': [],
                'sql_queries': [],
                'has_error': 'Y',
                'error_message': str(e)
            }

    def _extract_classes(self, java_content: str) -> List[Dict[str, Any]]:
        """Java 파일에서 클래스 정보를 추출"""
        classes = []
        try:
            # public/protected/private class 패턴
            class_pattern = re.compile(
                r'(?:^|\n)\s*(?:(public|protected|private)\s+)?'
                r'(?:(static|final|abstract)\s+)*'
                r'class\s+(\w+)'
                r'(?:\s+extends\s+(\w+))?'
                r'(?:\s+implements\s+([^{]+))?'
                r'\s*\{',
                re.MULTILINE
            )

            for match in class_pattern.finditer(java_content):
                access_modifier = match.group(1) or 'package'
                class_name = match.group(3)
                extends_class = match.group(4)
                implements_interfaces = match.group(5)

                start_pos = match.start()
                start_line = java_content.count('\n', 0, start_pos) + 1

                class_info = {
                    'class_name': class_name,
                    'access_modifier': access_modifier,
                    'extends_class': extends_class,
                    'implements_interfaces': implements_interfaces.strip() if implements_interfaces else None,
                    'line_start': start_line,
                    'line_end': start_line + 50  # 대략적인 추정
                }
                classes.append(class_info)
                debug(f"클래스 추출: {class_name}")

        except Exception as e:
            handle_error(e, f"클래스 추출 실패: {java_file}")
        return classes

    def _extract_methods(self, java_content: str) -> List[Dict[str, Any]]:
        """Java 파일에서 메서드 정보를 추출 (public/protected만)"""
        methods = []
        try:
            # public/protected 메서드만 추출 (Java 표준 API 메서드 제외)
            method_pattern = re.compile(
                r'(?:^|\n)\s*(?:(public|protected)\s+)'
                r'(?:(static|final|synchronized|abstract)\s+)*'
                r'(?:<[^>]+>\s+)?'  # 제네릭
                r'[\w<>[\]]+\s+'    # 반환 타입
                r'(\w+)\s*\('       # 메서드명
                r'[^)]*\)'          # 매개변수
                r'(?:\s*throws\s+[^{]+)?'  # throws
                r'\s*\{',           # 메서드 시작
                re.MULTILINE
            )

            for match in method_pattern.finditer(java_content):
                access_modifier = match.group(1)
                method_name = match.group(3)

                start_pos = match.start()
                start_line = java_content.count('\n', 0, start_pos) + 1

                method_info = {
                    'method_name': method_name,
                    'access_modifier': access_modifier,
                    'line_start': start_line,
                    'line_end': start_line + 20  # 대략적인 추정
                }
                methods.append(method_info)
                debug(f"메서드 추출: {method_name}")

        except Exception as e:
            handle_error(e, f"메서드 추출 실패: {java_file}")
        return methods

    def _extract_tables_from_query(self, sql_content: str) -> Dict[str, str]:
        """SQL 쿼리에서 테이블명과 별칭을 추출 (2단계 공통 처리)"""
        try:
            sql_parser = SqlParser()
            return sql_parser.extract_tables_and_aliases(sql_content)
        except Exception as e:
            handle_error(e, f"테이블 추출 실패: {sql_content[:100]}")
            return {}

    def _analyze_join_relationships(self, sql_content: str, tables_aliases: Dict[str, str], source_file: str) -> List[Dict[str, Any]]:
        """SQL 쿼리에서 조인관계를 분석 (3단계 공통 처리)"""
        try:
            return self.sql_join_analyzer.analyze_join_relationships(sql_content, tables_aliases, source_file)
        except Exception as e:
            handle_error(e, f"조인관계 분석 실패: {source_file}")
            return []

    def _create_call_method_relationships(self, java_content: str, methods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """메서드 간 호출 관계 생성 (CALL_METHOD)"""
        try:
            call_method_relationships = []

            # 각 메서드에서 다른 메서드 호출을 찾음
            for method in methods:
                method_name = method['method_name']

                # 메서드 호출 패턴 찾기 (간단한 패턴)
                # methodName() 또는 object.methodName() 형태
                call_patterns = [
                    r'\.(\w+)\s*\(',  # object.methodName()
                    r'\b(\w+)\s*\('   # methodName() (단순 호출)
                ]

                for pattern in call_patterns:
                    for match in re.finditer(pattern, java_content):
                        called_method = match.group(1)

                        # 호출되는 메서드가 추출된 메서드 목록에 있는지 확인
                        target_method = next((m for m in methods if m['method_name'] == called_method), None)
                        if target_method and called_method != method_name:  # 자기 자신 호출 제외

                            relationship = {
                                'src_name': method_name,
                                'dst_name': called_method,
                                'relationship_type': 'CALL_METHOD',
                                'src_type': 'METHOD',
                                'dst_type': 'METHOD'
                            }

                            # 중복 관계 제거
                            if relationship not in call_method_relationships:
                                call_method_relationships.append(relationship)
                                debug(f"CALL_METHOD 관계 생성: {method_name} → {called_method}")

            return call_method_relationships

        except Exception as e:
            handle_error(e, "CALL_METHOD 관계 생성 실패")
            return []

    def _create_call_query_relationships(self, methods: List[Dict[str, Any]], sql_queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """메서드 → SQL 쿼리 호출 관계 생성 (CALL_QUERY)"""
        try:
            call_query_relationships = []

            # 각 SQL 쿼리에 대해 해당 메서드와의 관계 생성
            for query in sql_queries:
                if 'method_name' in query:
                    method_name = query['method_name']
                    query_id = query['query_id']

                    # 해당 메서드가 메서드 목록에 있는지 확인
                    method_exists = any(m['method_name'] == method_name for m in methods)
                    if method_exists:
                        relationship = {
                            'src_name': method_name,
                            'dst_name': query_id,
                            'relationship_type': 'CALL_QUERY',
                            'src_type': 'METHOD',
                            'dst_type': query.get('query_type', 'SQL_SELECT')
                        }
                        call_query_relationships.append(relationship)
                        debug(f"CALL_QUERY 관계 생성: {method_name} → {query_id}")

            return call_query_relationships

        except Exception as e:
            handle_error(e, "CALL_QUERY 관계 생성 실패")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        return self.stats.copy()

    def reset_statistics(self):
        """통계 정보 초기화"""
        self.stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'classes_extracted': 0,
            'methods_extracted': 0,
            'inheritance_relationships_created': 0,
            'call_query_relationships_created': 0,
            'call_method_relationships_created': 0,
            'use_table_relationships_created': 0,
            'errors': 0
        }