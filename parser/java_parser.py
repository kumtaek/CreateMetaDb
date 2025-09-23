"""
Java 파서 모듈
- 4단계 통합 처리: Java 파일에서 클래스/메서드 추출 및 상속 관계 분석
- 메모리 최적화 (스트리밍 처리)
- Classes 테이블 + Components 테이블 완전 지원

USER RULES:
- 하드코딩 금지: path_utils.get_parser_config_path("java") 사용 (크로스플랫폼 대응)
- Exception 처리: handle_error() 공통함수 사용
- 공통함수 사용: util 모듈 활용
- 메뉴얼 기반: parser/manual/01_java 참고
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple
from util import (
    ConfigUtils, FileUtils, HashUtils, PathUtils, ValidationUtils,
    app_logger, info, error, debug, warning, handle_error
)
from util.sql_join_analyzer import SqlJoinAnalyzer
from .sql_parser import SqlParser

class JavaParser:
    """Java 파서 - 4단계 통합 처리"""

    def __init__(self, config_path: str = None, project_name: str = None):
        from util.global_project import get_global_project_name, get_global_project_id, is_global_project_info_set
        if is_global_project_info_set():
            self.project_name = get_global_project_name()
            self.project_id = get_global_project_id()
        else:
            self.project_name = project_name
            self.project_id = None

        self.path_utils = PathUtils()
        
        if config_path is None:
            java_config_path = self.path_utils.get_parser_config_path("java")
            self.config = self._load_config(java_config_path)
        else:
            self.config_path = config_path
            self.config = self._load_config(config_path)

        self._compile_patterns_for_performance()

    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """설정 파일 로드"""
        try:
            from util import ConfigUtils, handle_error, warning
            config_utils = ConfigUtils()
            path = config_path or self.config_path if hasattr(self, 'config_path') else config_path
            config = config_utils.load_yaml_config(path)
            if not config:
                warning(f"설정 파일을 로드할 수 없습니다: {path}, 기본 설정 사용")
                return self._get_default_config()
            return config
        except Exception as e:
            warning(f"설정 파일 로드 실패: {config_path}, 기본 설정 사용: {str(e)}")
            return self._get_default_config()

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
            
            # 2. JPA 메서드 쿼리 변환
            # This part is complex and will be simplified for now as per user request.
            # jpa_method_queries = self._convert_jpa_method_queries(java_content, java_file)
            # sql_queries.extend(jpa_method_queries)

            # 3. StringBuilder 및 String 변수 추적을 통한 SQL 추출
            methods = self._get_methods_content(java_content)
            sql_parser = SqlParser()
            
            for method_name, method_content, method_start_line in methods:
                variable_tracker = {}

                # 1. StringBuilder 초기화 추적
                sb_init_pattern = re.compile(r'StringBuilder\s+(\w+)\s*=\s*new\s+StringBuilder\s*\(([^)]*)\);')
                for match in sb_init_pattern.finditer(method_content):
                    var_name, init_value = match.groups()
                    variable_tracker[var_name] = self._strip_quotes(init_value)

                # 2. String 변수 초기화 추적 (개선됨)
                # 2a. 단순 String 초기화: String sql = "MERGE INTO..."
                str_init_pattern = re.compile(r'String\s+(\w+)\s*=\s*"([^"]*)"(?:\s*\+\s*)?', re.MULTILINE)
                for match in str_init_pattern.finditer(method_content):
                    var_name, init_value = match.groups()
                    variable_tracker[var_name] = init_value

                # 2b. 여러 줄 문자열 리터럴 연결: String sql = "line1" + "line2" + ...
                multiline_str_pattern = re.compile(
                    r'String\s+(\w+)\s*=\s*("(?:[^"\\]|\\.)*"(?:\s*\+\s*"(?:[^"\\]|\\.)*")*)',
                    re.MULTILINE | re.DOTALL
                )
                for match in multiline_str_pattern.finditer(method_content):
                    var_name, concatenated_str = match.groups()
                    # 여러 문자열 리터럴을 하나로 합치기
                    strings = re.findall(r'"([^"]*)"', concatenated_str)
                    full_string = ''.join(strings)
                    variable_tracker[var_name] = full_string

                # 3. StringBuilder append 및 String 연결 추적 (개선됨)
                # 3a. StringBuilder.append(...)
                append_pattern = re.compile(r'(\w+)\.append\s*\(\s*"([^"]*)"\s*\);')
                for match in append_pattern.finditer(method_content):
                    var_name, appended_value = match.groups()
                    if var_name in variable_tracker:
                        variable_tracker[var_name] += appended_value

                # 3b. String += "..." 패턴
                string_concat_pattern = re.compile(r'(\w+)\s*\+=\s*"([^"]*)";')
                for match in string_concat_pattern.finditer(method_content):
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
        if (value.startswith('"') and value.endswith('"')) or (value.startswith('‘') and value.endswith('’')):
            return value[1:-1]
        return value

    def _extract_jpa_queries(self, java_content: str, java_file: str) -> List[Dict[str, Any]]:
        """JPA @Query 어노테이션에서 SQL 추출 (개선된 로직)"""
        jpa_queries = []
        try:
            # 1. @Query 어노테이션과 그 다음 메서드 시그니처를 함께 찾음
            #    - 그룹 1: @Query(...) 안의 내용
            #    - 그룹 2: 메서드 이름
            #    - re.DOTALL 플래그로 여러 줄에 걸친 어노테이션 처리
            annotation_method_pattern = re.compile(
                r'@Query\s*\((.*?)\)\s*(?:@\w+\s*)*'  # @Query(...)와 다른 어노테이션들
                r'(?:public|private|protected)?\s*(?:static\s+)?(?:<[^>]+>\s+)?' # 제어자, 제네릭
                r'[\w<>[\]]+\s+' # 반환 타입
                r'(\w+)\s*\(',    # 메서드 이름 (그룹 2)
                re.DOTALL
            )

            sql_parser = SqlParser()

            for match in annotation_method_pattern.finditer(java_content):
                annotation_content = match.group(1)
                method_name = match.group(2)

                # 2. 어노테이션 내용에서 모든 문자열 리터럴 추출
                string_literals = re.findall(r'\"((?:\\\"|[^"])*)\"', annotation_content)

                # 3. 문자열 리터럴들을 합쳐서 전체 SQL 쿼리 생성
                sql_content = "".join(string_literals)
                
                # 빈 쿼리는 건너뜀
                if not sql_content.strip():
                    continue

                # 4. 후속 처리 (기존 로직과 유사)
                clean_sql = sql_parser._preprocess_sql(sql_content)
                query_type = sql_parser.determine_query_type(clean_sql)
                alias_map = sql_parser.extract_tables_and_aliases(clean_sql)
                join_relationships = self.sql_join_analyzer.analyze_join_relationships(clean_sql, alias_map, java_file)

                query_info = {
                    'query_id': method_name,
                    'query_type': query_type,
                    'sql_content': sql_content, # 원본 SQL 저장
                    'used_tables': list(alias_map.values()),
                    'join_relationships': join_relationships,
                    'is_dynamic': True, # 문자열 연결이 있으므로 동적으로 간주
                    'method_name': method_name,
                    'line_start': java_content.count('\n', 0, match.start()) + 1,
                    'line_end': java_content.count('\n', 0, match.end()) + 1,
                    'has_error': 'N',
                    'error_message': None,
                    'source_type': 'JPA_QUERY'
                }
                jpa_queries.append(query_info)
                debug(f"JPA @Query 추출: {method_name} - {query_type}")

        except Exception as e:
            handle_error(e, f"JPA @Query 추출 실패: {java_file}")
        return jpa_queries


    def parse_java_file(self, java_file: str) -> Dict[str, Any]:
        """Java 파일을 파싱하여 클래스, 메서드, SQL 쿼리를 추출"""
        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                java_content = f.read()

            # SQL 쿼리 추출
            sql_queries = self._extract_sql_queries_from_java(java_content, java_file)

            return {
                'java_file': java_file,
                'sql_queries': sql_queries,
                'has_error': 'N',
                'error_message': None
            }

        except Exception as e:
            return {
                'java_file': java_file,
                'sql_queries': [],
                'has_error': 'Y',
                'error_message': str(e)
            }