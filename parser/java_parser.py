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
from typing import List, Dict, Any, Optional
from util import (
    ConfigUtils, FileUtils, HashUtils, PathUtils, ValidationUtils,
    app_logger, info, error, debug, warning, handle_error
)
from util.sql_join_analyzer import SqlJoinAnalyzer


class JavaParser:
    """Java 파서 - 4단계 통합 처리"""

    def __init__(self, config_path: str = None, project_name: str = None):
        """
        Java 파서 초기화 (성능 최적화 포함)

        Args:
            config_path: 설정 파일 경로
            project_name: 프로젝트명 (선택적, 전역에서 가져옴)
        """
        # USER RULES: 하드코딩 지양 - 프로젝트 정보 전역 관리
        from util.global_project import get_global_project_name, get_global_project_id, is_global_project_info_set

        # 전역 프로젝트 정보 활용 (실행 중 변경되지 않는 값)
        if is_global_project_info_set():
            self.project_name = get_global_project_name()
            self.project_id = get_global_project_id()
        else:
            # 개별 설정이 있는 경우 (테스트 등)
            self.project_name = project_name
            self.project_id = None

        # PathUtils 인스턴스 생성 (공통함수 사용)
        self.path_utils = PathUtils()
        
        if config_path is None:
            # USER RULES: 하드코딩 지양 - 공통함수 사용 (크로스플랫폼 대응)
            java_config_path = self.path_utils.get_parser_config_path("java")
            self.config = self._load_config(java_config_path)
        else:
            self.config_path = config_path
            self.config = self._load_config(config_path)

        # 성능 최적화: 정규식 패턴 미리 컴파일
        self._compile_patterns_for_performance()

        # 성능 설정 로드
        self.performance_config = self.config.get('performance', {})
        self.large_file_threshold_mb = self.performance_config.get('large_file_threshold_mb', 1.0)
        self.batch_size = self.performance_config.get('batch_size', 100)
        self.use_compiled_patterns = self.performance_config.get('use_compiled_patterns', True)

        # 5단계 관계 분석 설정 로드
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
        
        # 공통 SQL 조인 분석기 초기화
        self.sql_join_analyzer = SqlJoinAnalyzer(self.config)

    def _compile_patterns_for_performance(self):
        """성능 최적화를 위한 정규식 패턴 미리 컴파일"""
        try:
            # 클래스 추출 패턴 컴파일
            class_patterns = self.config.get('java_class_extraction_patterns', [])
            self.compiled_class_patterns = []

            for pattern in class_patterns:
                try:
                    compiled_pattern = re.compile(pattern, re.MULTILINE)
                    self.compiled_class_patterns.append(compiled_pattern)
                except re.error as e:
                    # exception은 handle_error()로 exit해야 에러 인지가 가능하다
                    handle_error(f"클래스 패턴 컴파일 실패: {pattern} - {str(e)}")

            # 메서드 추출 패턴 컴파일
            method_patterns = self.config.get('method_extraction_patterns', [])
            self.compiled_method_patterns = []

            for pattern in method_patterns:
                try:
                    compiled_pattern = re.compile(pattern, re.MULTILINE)
                    self.compiled_method_patterns.append(compiled_pattern)
                except re.error as e:
                    # exception은 handle_error()로 exit해야 에러 인지가 가능하다
                    handle_error(f"메서드 패턴 컴파일 실패: {pattern} - {str(e)}")

            # 복잡한 메서드 필터링 패턴 컴파일
            complex_filtering = self.config.get('complex_method_filtering', {})
            self.compiled_business_patterns = {}

            for pattern_type, patterns in complex_filtering.items():
                self.compiled_business_patterns[pattern_type] = []
                if isinstance(patterns, list):
                    for pattern in patterns:
                        try:
                            compiled_pattern = re.compile(pattern, re.IGNORECASE)
                            self.compiled_business_patterns[pattern_type].append(compiled_pattern)
                        except re.error as e:
                            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
                            handle_error(f"비즈니스 패턴 컴파일 실패: {pattern} - {str(e)}")

            # 패키지 추출 패턴 컴파일
            package_patterns = self.config.get('package_extraction_patterns', [])
            self.compiled_package_patterns = []

            for pattern in package_patterns:
                try:
                    compiled_pattern = re.compile(pattern)
                    self.compiled_package_patterns.append(compiled_pattern)
                except re.error as e:
                    # exception은 handle_error()로 exit해야 에러 인지가 가능하다
                    handle_error(f"패키지 패턴 컴파일 실패: {pattern} - {str(e)}")

            # 상속 관계 패턴 컴파일
            inheritance_config = self.config.get('inheritance_analysis', {})
            extends_patterns = inheritance_config.get('extends_patterns', [])
            self.compiled_extends_patterns = []

            for pattern in extends_patterns:
                try:
                    compiled_pattern = re.compile(pattern, re.MULTILINE)
                    self.compiled_extends_patterns.append(compiled_pattern)
                except re.error as e:
                    # exception은 handle_error()로 exit해야 에러 인지가 가능하다
                    handle_error(f"상속 패턴 컴파일 실패: {pattern} - {str(e)}")

            # 5단계 관계 분석 패턴 컴파일
            relationship_config = self.config.get('relationship_analysis', {})
            
            # CALL_QUERY 패턴 컴파일
            call_query_patterns = relationship_config.get('call_query_patterns', [])
            self.compiled_call_query_patterns = []
            for pattern in call_query_patterns:
                try:
                    compiled_pattern = re.compile(pattern, re.MULTILINE | re.IGNORECASE)
                    self.compiled_call_query_patterns.append(compiled_pattern)
                except re.error as e:
                    handle_error(f"CALL_QUERY 패턴 컴파일 실패: {pattern} - {str(e)}")

            # CALL_METHOD 패턴 컴파일
            call_method_patterns = relationship_config.get('call_method_patterns', [])
            self.compiled_call_method_patterns = []
            for pattern in call_method_patterns:
                try:
                    compiled_pattern = re.compile(pattern, re.MULTILINE)
                    self.compiled_call_method_patterns.append(compiled_pattern)
                except re.error as e:
                    handle_error(f"CALL_METHOD 패턴 컴파일 실패: {pattern} - {str(e)}")

            # USE_TABLE 패턴 컴파일
            use_table_patterns = relationship_config.get('use_table_patterns', [])
            self.compiled_use_table_patterns = []
            for pattern in use_table_patterns:
                try:
                    compiled_pattern = re.compile(pattern, re.MULTILINE | re.IGNORECASE)
                    self.compiled_use_table_patterns.append(compiled_pattern)
                except re.error as e:
                    handle_error(f"USE_TABLE 패턴 컴파일 실패: {pattern} - {str(e)}")

            # 제외할 메서드 패턴 컴파일
            exclude_methods = relationship_config.get('exclude_methods', [])
            self.compiled_exclude_methods = []
            for pattern in exclude_methods:
                try:
                    compiled_pattern = re.compile(pattern, re.IGNORECASE)
                    self.compiled_exclude_methods.append(compiled_pattern)
                except re.error as e:
                    handle_error(f"제외 메서드 패턴 컴파일 실패: {pattern} - {str(e)}")

            info(f"정규식 패턴 컴파일 완료: 클래스 {len(self.compiled_class_patterns)}개, "
                 f"메서드 {len(self.compiled_method_patterns)}개, "
                 f"패키지 {len(self.compiled_package_patterns)}개, "
                 f"상속 {len(self.compiled_extends_patterns)}개, "
                 f"CALL_QUERY {len(self.compiled_call_query_patterns)}개, "
                 f"CALL_METHOD {len(self.compiled_call_method_patterns)}개, "
                 f"USE_TABLE {len(self.compiled_use_table_patterns)}개")

        except Exception as e:
            handle_error(e, "정규식 패턴 컴파일 실패")
            self.compiled_business_patterns = {}
            self.compiled_package_patterns = []
            self.compiled_extends_patterns = []
            self.compiled_call_query_patterns = []
            self.compiled_call_method_patterns = []
            self.compiled_use_table_patterns = []
            self.compiled_exclude_methods = []

    def get_filtered_java_files(self, project_path: str = None) -> List[str]:
        """
        Java 파일 수집 및 필터링

        Args:
            project_path: 프로젝트 경로

        Returns:
            Java 파일 경로 리스트
        """
        try:
            # USER RULES: 공통함수 사용 지향
            file_utils = FileUtils()

            # USER RULES: 하드코딩 지양 - PathUtils 공통함수 사용
            if project_path is None and self.project_name:
                path_utils = PathUtils()
                project_path = path_utils.get_project_source_path(self.project_name)

            if not project_path:
                # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                # USER RULES: Exception 발생시 handle_error()로 exit()
                handle_error(Exception("프로젝트 경로가 지정되지 않았습니다"), "Java 파일 수집 실패")

            java_files = []
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith('.java'):
                        file_path = self.path_utils.join_path(root, file)
                        if self._is_valid_java_file(file_path):
                            java_files.append(file_path)

            info(f"Java 파일 수집 완료: {len(java_files)}개")
            return java_files

        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            # USER RULES: Exception 발생시 handle_error()로 exit()
            handle_error(e, "Java 파일 수집 실패")
            return []

    def _is_valid_java_file(self, file_path: str) -> bool:
        """
        유효한 Java 파일인지 확인

        Args:
            file_path: 파일 경로

        Returns:
            유효성 여부
        """
        try:
            file_utils = FileUtils()
            content = file_utils.read_file(file_path)
            if not content:
                return False

            # 기본적인 Java 파일 검증
            java_indicators = ['class', 'interface', 'enum', 'package', 'import']
            content_lower = content.lower()
            return any(indicator in content_lower for indicator in java_indicators)

        except Exception as e:
            handle_error(f"Java 파일 확인 실패: {file_path}, 오류: {str(e)}")
            return False

    def parse_java_file(self, java_file: str) -> Dict[str, Any]:
        """
        Java 파일에서 클래스/메서드 정보 추출 및 상속 관계 분석

        Args:
            java_file: Java 파일 경로

        Returns:
            분석 결과 딕셔너리
        """
        try:
            # 1. 파일 크기별 처리 전략 결정
            processing_strategy = self._determine_processing_strategy(java_file)

            # 2. Java 파일 읽기
            file_utils = FileUtils()
            java_content = file_utils.read_file(java_file)
            if not java_content:
                return {
                    'classes': [],
                    'methods': [],
                    'inheritance_relationships': [],
                    'file_path': java_file,
                    'has_error': 'Y',
                    'error_message': 'Java 파일 읽기 실패'
                }

            # 3. 전처리 (주석 및 문자열 리터럴 안전 처리)
            processed_content, string_map = self._preprocess_java_content_safe(java_content)

            # 4. 클래스 정보 추출
            debug(f"클래스 정보 추출 시작: {java_file}")
            classes = self._extract_class_info_safe(processed_content, java_file, java_content)
            debug(f"클래스 정보 추출 완료: {len(classes)}개")

            # 5. 메서드 정보 추출
            debug(f"메서드 정보 추출 시작: {java_file}")
            methods = self._extract_method_info_safe(processed_content, java_file, java_content)
            debug(f"메서드 정보 추출 완료: {len(methods)}개")
            
            # 6. 메서드 정보를 해당 클래스에 포함
            classes = self._associate_methods_with_classes(classes, methods)

            # 7. SQL 쿼리 추출 (새로운 기능 추가)
            debug(f"SQL 쿼리 추출 시작: {java_file}")
            sql_queries = self._extract_sql_queries_from_java(java_content, java_file)
            debug(f"SQL 쿼리 추출 완료: {len(sql_queries)}개")

            # 8. 파싱 결과 검증
            validated_classes = self._validate_parsing_results(classes, java_content)
            validated_methods = self._validate_parsing_results(methods, java_content)

            # 7. 상속 관계 분석
            inheritance_relationships = self._analyze_inheritance_relationships_safe(processed_content)

            # 8. 5단계 관계 분석 (통합 처리)
            call_query_relationships = self._analyze_call_query_relationships_safe(processed_content, validated_methods)
            call_method_relationships = self._analyze_call_method_relationships_safe(processed_content, validated_methods)
            use_table_relationships = self._analyze_use_table_relationships_safe(processed_content, validated_methods)

            # 9. 통계 업데이트
            self.stats['files_processed'] += 1
            self.stats['classes_extracted'] += len(validated_classes)
            self.stats['methods_extracted'] += len(validated_methods)
            self.stats['inheritance_relationships_created'] += len(inheritance_relationships)
            self.stats['call_query_relationships_created'] += len(call_query_relationships)
            self.stats['call_method_relationships_created'] += len(call_method_relationships)
            self.stats['use_table_relationships_created'] += len(use_table_relationships)

            return {
                'classes': validated_classes,
                'methods': validated_methods,
                'sql_queries': sql_queries,  # SQL 쿼리 정보 추가
                'inheritance_relationships': inheritance_relationships,
                'call_query_relationships': call_query_relationships,
                'call_method_relationships': call_method_relationships,
                'use_table_relationships': use_table_relationships,
                'file_path': java_file,
                'processing_strategy': processing_strategy,
                'has_error': 'N',
                'error_message': None
            }

        except Exception as e:
            # USER RULES: 파싱 에러는 has_error='Y', error_message 남기고 계속 진행
            error_message = f"Java 파싱 중 예외 발생: {str(e)}"
            handle_error(e, f"parse_java_file에서 예외 발생: {java_file}")
            # handle_error(Exception(f"{error_message} - {java_file}"), "Java 파싱 실패")
            self.stats['errors'] += 1
            return {
                'classes': [],
                'methods': [],
                'inheritance_relationships': [],
                'call_query_relationships': [],
                'call_method_relationships': [],
                'use_table_relationships': [],
                'file_path': java_file,
                'has_error': 'Y',
                'error_message': error_message
            }

    def _determine_processing_strategy(self, file_path: str) -> Dict[str, Any]:
        """파일 크기별 최적 처리 전략 결정"""
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

            if file_size_mb < self.performance_config.get('streaming_threshold_mb', 0.5):
                return {'strategy': 'memory', 'chunk_size': None}
            elif file_size_mb < self.large_file_threshold_mb:
                return {'strategy': 'streaming', 'chunk_size': 1024}
            else:
                return {'strategy': 'chunk', 'chunk_size': 512}

        except Exception as e:
            handle_error(e, "처리 전략 결정 실패")
            return {'strategy': 'memory', 'chunk_size': None}

    def _preprocess_java_content_safe(self, java_content: str) -> tuple:
        """
        안전한 Java 파일 전처리
        - 주석 제거 (블록 주석, 라인 주석)
        - 문자열 리터럴 보호
        - 정규식 파싱 최적화
        """
        try:
            # 1. 블록 주석 제거 (/* ... */)
            processed_content = self._remove_block_comments_safe(java_content)

            # 2. 라인 주석 제거 (// ...)
            processed_content = self._remove_line_comments_safe(processed_content)

            # 3. 문자열 리터럴 임시 치환
            processed_content, string_map = self._protect_string_literals(processed_content)

            return processed_content, string_map

        except Exception as e:
            handle_error(f"Java 파일 전처리 실패: {str(e)}")
            return java_content, {}

    def _remove_block_comments_safe(self, content: str) -> str:
        """블록 주석 안전 제거"""
        try:
            # 중첩된 주석을 고려한 제거 로직
            result = []
            i = 0
            while i < len(content):
                if i < len(content) - 1 and content[i:i+2] == '/*':
                    # 블록 주석 시작
                    j = i + 2
                    while j < len(content) - 1:
                        if content[j:j+2] == '*/':
                            # 블록 주석 종료
                            i = j + 2
                            break
                        j += 1
                    else:
                        # 블록 주석이 닫히지 않음 - 파일 끝까지 주석으로 처리
                        break
                else:
                    result.append(content[i])
                    i += 1

            return ''.join(result)

        except Exception as e:
            handle_error(f"블록 주석 제거 실패: {str(e)}")
            return content

    def _remove_line_comments_safe(self, content: str) -> str:
        """라인 주석 제거"""
        try:
            lines = content.split('\n')
            processed_lines = []

            for line in lines:
                # 문자열 리터럴 내의 // 는 제거하지 않음
                if '"' in line or "'" in line:
                    # 문자열 리터럴이 있는 라인은 복잡한 처리 필요
                    processed_line = self._remove_line_comments_with_string_protection(line)
                else:
                    # 단순한 라인 주석 제거
                    comment_pos = line.find('//')
                    if comment_pos != -1:
                        processed_line = line[:comment_pos].rstrip()
                    else:
                        processed_line = line

                processed_lines.append(processed_line)

            return '\n'.join(processed_lines)

        except Exception as e:
            handle_error(f"라인 주석 제거 실패: {str(e)}")
            return content

    def _remove_line_comments_with_string_protection(self, line: str) -> str:
        """문자열 리터럴을 보호하면서 라인 주석 제거"""
        try:
            in_string = False
            quote_char = None
            i = 0

            while i < len(line) - 1:
                char = line[i]

                if not in_string:
                    if char in ['"', "'"]:
                        in_string = True
                        quote_char = char
                    elif char == '/' and line[i + 1] == '/':
                        return line[:i].rstrip()
                else:
                    if char == quote_char and line[i - 1] != '\\':
                        in_string = False
                        quote_char = None

                i += 1

            return line

        except Exception as e:
            handle_error(f"문자열 보호 라인 주석 제거 실패: {str(e)}")
            return line

    def _protect_string_literals(self, content: str) -> tuple:
        """문자열 리터럴 보호 (정규식 파싱 시 고려)"""
        try:
            string_placeholders = {}
            placeholder_counter = 0

            # 이스케이프된 따옴표를 고려한 문자열 리터럴 찾기
            i = 0
            while i < len(content):
                if content[i] in ['"', "'"]:
                    quote_char = content[i]
                    # 문자열 리터럴 시작
                    j = i + 1
                    while j < len(content):
                        if content[j] == quote_char and content[j-1] != '\\':
                            # 문자열 리터럴 종료
                            placeholder = f"__STRING_PLACEHOLDER_{placeholder_counter}__"
                            string_placeholders[placeholder] = content[i:j+1]
                            content = content[:i] + placeholder + content[j+1:]
                            placeholder_counter += 1
                            i += len(placeholder) - 1
                            break
                        j += 1
                    else:
                        # 문자열이 닫히지 않음
                        break
                i += 1

            return content, string_placeholders

        except Exception as e:
            handle_error(f"문자열 리터럴 보호 실패: {str(e)}")
            return content, {}

    def _extract_class_info_safe(self, java_content: str, file_path: str, original_content: str) -> List[Dict[str, Any]]:
        """
        Java 파일에서 클래스 정보 추출 (안전성 강화)
        """
        try:
            classes = []

            # USER RULES: 하드코딩 지양 - 컴파일된 패턴 사용
            for compiled_pattern in self.compiled_class_patterns:
                matches = compiled_pattern.finditer(java_content)
                for match in matches:
                    class_info = self._parse_class_match_safe(match, java_content, file_path, original_content)
                    if class_info:
                        classes.append(class_info)

            return classes

        except Exception as e:
            # USER RULES: 파싱 에러는 has_error='Y', error_message 남기고 계속 진행
            handle_error(f"클래스 정보 추출 실패: {str(e)}")
            return []

    def _parse_class_match_safe(self, match: re.Match, java_content: str, file_path: str, original_content: str) -> Optional[Dict[str, Any]]:
        """
        클래스 매치 결과를 안전하게 파싱하여 클래스 정보 생성
        """
        try:
            # 클래스명 추출
            class_name = match.group(1)

            # 클래스 타입 결정
            class_type = self._determine_class_type(match.group(0))

            # 패키지명 추출 (파일 경로에서 + Java 내용에서)
            package_name = self._extract_package_name_flexible(file_path, original_content)

            # 라인 번호 추출 (original_content 기준으로 정확히 계산)
            line_start = self._find_line_number_in_original(original_content, class_name, match.group(0))
            line_end = self._find_class_end_line_safe(original_content, line_start)

            # 상속 정보 추출
            parent_class_name = None
            interfaces = []

            if len(match.groups()) > 1 and match.group(2):
                if class_type in ['class', 'enum']:
                    parent_class_name = match.group(2)
                elif class_type == 'interface':
                    # 인터페이스 상속은 메타DB에 표현하지 않음
                    pass

            if len(match.groups()) > 2 and match.group(3):
                # implements 절 파싱
                implements_clause = match.group(3)
                interfaces = [iface.strip() for iface in implements_clause.split(',') if iface.strip()]

            # 클래스 내용 추출 및 해시 생성
            class_content = self._extract_class_content_safe(original_content, match.start(), line_end)
            hash_value = HashUtils().generate_md5(class_content)

            # 메서드 정보는 나중에 _associate_methods_with_classes에서 처리
            # 여기서는 빈 리스트로 초기화

            return {
                'class_name': class_name,
                'class_type': class_type,
                'package_name': package_name,
                'line_start': line_start,
                'line_end': line_end,
                'parent_class_name': parent_class_name,
                'interfaces': interfaces,
                'hash_value': hash_value,
                'file_path': file_path,
                'methods': []  # 메서드 정보는 나중에 추가
            }

        except Exception as e:
            # 파싱 에러로 has_error='Y' 처리하고 계속 진행
            return None

    def _extract_methods_for_class(self, java_content: str, class_name: str, class_start: int, class_end_line: int) -> List[Dict[str, Any]]:
        """
        특정 클래스 내의 메서드만 추출
        
        Args:
            java_content: Java 파일 내용
            class_name: 클래스명
            class_start: 클래스 시작 위치
            class_end_line: 클래스 끝 라인 번호
            
        Returns:
            해당 클래스의 메서드 정보 리스트
        """
        try:
            methods = []
            
            # 클래스 범위 내에서만 메서드 검색
            class_content = self._extract_content_by_line_range(java_content, 1, class_end_line)
            
            # 메서드 패턴으로 검색
            for i, compiled_pattern in enumerate(self.compiled_method_patterns):
                matches = compiled_pattern.finditer(class_content)
                for match in matches:
                    method_name = match.group(1)
                    
                    # USER RULES: 제어문 키워드 필터링 적용 (METHOD 컴포넌트로 잘못 파싱 방지)
                    if self._is_control_keyword(method_name):
                        debug(f"제어문 키워드 필터링: {method_name} - 건너뜀")
                        continue
                    
                    # 메서드가 해당 클래스에 속하는지 확인
                    if self._is_method_in_class(class_content, method_name, class_name):
                        # 메서드 본문 추출
                        method_body = self._extract_method_body(class_content, match.start())
                        complexity_classification = self._classify_method_complexity(method_name, method_body)
                        
                        # 메서드 정보 생성
                        method_info = self._create_method_info_safe(match, class_content, '', class_name, complexity_classification)
                        if method_info:
                            methods.append(method_info)
                            debug(f"클래스 {class_name}에서 메서드 발견: {method_name}")
            
            return methods
            
        except Exception as e:
            handle_error(f"클래스 메서드 추출 실패: {class_name} - {str(e)}")
            return []

    def _extract_content_by_line_range(self, content: str, start_line: int, end_line: int) -> str:
        """특정 라인 범위의 내용을 추출"""
        try:
            lines = content.split('\n')
            if start_line <= 0 or end_line > len(lines):
                return content
            
            return '\n'.join(lines[start_line-1:end_line])
        except Exception as e:
            handle_error(f"라인 범위 추출 실패: {str(e)}")
            return content

    def _is_method_in_class(self, class_content: str, method_name: str, class_name: str) -> bool:
        """메서드가 해당 클래스에 속하는지 확인"""
        try:
            # 간단한 휴리스틱: 메서드명이 클래스 내용에 있고, 
            # 중괄호 블록 구조로 클래스 내부에 있는지 확인
            method_pattern = rf'\b{re.escape(method_name)}\s*\('
            matches = list(re.finditer(method_pattern, class_content))
            
            if not matches:
                return False
            
            # 첫 번째 매치가 클래스 내부에 있는지 확인
            method_pos = matches[0].start()
            
            # 클래스 시작부터 메서드 위치까지의 중괄호 균형 확인
            before_method = class_content[:method_pos]
            open_braces = before_method.count('{')
            close_braces = before_method.count('}')
            
            # 클래스 시작 중괄호 이후에 메서드가 있는지 확인
            return open_braces > close_braces
            
        except Exception as e:
            handle_error(f"메서드 소속 확인 실패: {method_name} - {str(e)}")
            return False

    def _associate_methods_with_classes(self, classes: List[Dict[str, Any]], methods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        메서드 정보를 해당 클래스에 포함시킴
        
        Args:
            classes: 클래스 정보 리스트
            methods: 메서드 정보 리스트
            
        Returns:
            메서드가 포함된 클래스 정보 리스트
        """
        try:
            # 각 클래스에 methods 필드 초기화
            for class_info in classes:
                class_info['methods'] = []
            
            # 각 메서드를 해당하는 클래스에 할당
            for method in methods:
                method_class_name = method.get('class_name')
                if method_class_name:
                    # 해당 클래스 찾기
                    for class_info in classes:
                        if class_info.get('class_name') == method_class_name:
                            class_info['methods'].append(method)
                            debug(f"메서드 {method.get('method_name')}를 클래스 {method_class_name}에 할당")
                            break
            
            return classes
            
        except Exception as e:
            handle_error(f"메서드-클래스 연결 실패: {str(e)}")
            return classes

    def _determine_class_type(self, class_declaration: str) -> str:
        """
        클래스 선언문에서 클래스 타입 결정
        """
        if '@interface' in class_declaration:
            return 'annotation'
        elif 'enum' in class_declaration:
            return 'enum'
        elif 'interface' in class_declaration:
            return 'interface'
        else:
            return 'class'

    def _extract_package_name_flexible(self, file_path: str, java_content: str = None) -> str:
        """
        유연한 패키지명 추출 (다양한 프로젝트 구조 대응)
        """
        try:
            # USER RULES: 하드코딩 지양 - 설정 파일에서 패턴 로드
            package_patterns = self.config.get('package_extraction_patterns', [
                r'src/main/java/(.+?)/',
                r'src/(.+?)/',
                r'main/java/(.+?)/',
                r'java/(.+?)/',
                r'app/(.+?)/',
                r'com/(.+?)/',
                r'org/(.+?)/'
            ])

            # USER RULES: 공통함수 사용 지향
            path_utils = PathUtils()
            normalized_path = path_utils.normalize_path(file_path)

            # 1. 설정 파일 패턴으로 패키지명 추출 시도
            for compiled_pattern in self.compiled_package_patterns:
                match = compiled_pattern.search(normalized_path)
                if match:
                    package_path = match.group(1)
                    # 파일명 제거하고 디렉토리 경로만 추출
                    package_path = self.path_utils.get_parent_directory(package_path)
                    # 경로 구분자를 점으로 변환
                    package_name = package_path.replace(self.path_utils.get_path_separator(), '.').replace('/', '.')

                    if package_name and package_name != '.':
                        return package_name

            # 2. Java 파일 내용에서 package 선언문 찾기 (fallback)
            if java_content:
                package_from_content = self._extract_package_from_content(java_content)
                if package_from_content:
                    return package_from_content

            # 3. 기본값 반환 (USER RULES: 하드코딩 지양 - 설정 파일에서 가져오기)
            return self.config.get('method_complexity', {}).get('default_package', 'default')

        except Exception as e:
            handle_error(f"패키지명 추출 실패: {str(e)}")
            return self.config.get('method_complexity', {}).get('default_package', 'default')

    def _extract_package_from_content(self, java_content: str) -> Optional[str]:
        """
        Java 파일 내용에서 package 선언문 추출
        """
        try:
            # package 선언문 패턴
            package_pattern = r'^\s*package\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*;'

            lines = java_content.split('\n')
            for line in lines:
                # 주석 제거
                if '//' in line:
                    line = line[:line.find('//')]

                match = re.match(package_pattern, line.strip())
                if match:
                    return match.group(1)

            return None

        except Exception as e:
            handle_error(f"Java 파일에서 패키지명 추출 실패: {str(e)}")
            return None

    def _find_class_end_line_safe(self, java_content: str, class_start_pos: int) -> int:
        """
        클래스의 종료 라인 번호 안전하게 찾기
        """
        try:
            # 중괄호 매칭을 통한 클래스 종료 위치 찾기
            brace_count = 0
            in_string = False
            string_char = None
            escape_next = False

            for i in range(class_start_pos, len(java_content)):
                char = java_content[i]

                if escape_next:
                    escape_next = False
                    continue

                if char == '\\':
                    escape_next = True
                    continue

                if not in_string:
                    if char in ['"', "'"]:
                        in_string = True
                        string_char = char
                    elif char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # 클래스 종료 위치 찾음
                            return java_content[:i+1].count('\n') + 1
                else:
                    if char == string_char:
                        in_string = False
                        string_char = None

            # 클래스 종료를 찾지 못한 경우 파일 끝
            return java_content.count('\n') + 1

        except Exception as e:
            handle_error(f"클래스 종료 라인 찾기 실패: {str(e)}")
            return java_content.count('\n') + 1

    def _extract_class_content_safe(self, java_content: str, start_pos: int, end_line: int) -> str:
        """
        클래스 내용 추출 (해시 생성용)
        """
        try:
            lines = java_content.split('\n')
            start_line = java_content[:start_pos].count('\n') + 1

            if start_line <= len(lines) and end_line <= len(lines):
                class_lines = lines[start_line - 1:end_line]
                return '\n'.join(class_lines)

            return java_content[start_pos:]

        except Exception as e:
            handle_error(f"클래스 내용 추출 실패: {str(e)}")
            return ""

    def _extract_method_info_safe(self, java_content: str, file_path: str, original_content: str) -> List[Dict[str, Any]]:
        """
        Java 파일에서 메서드 정보 추출 (안전성 강화 + 복잡도 기반 필터링)
        """
        try:
            methods = []

            # USER RULES: 하드코딩 지양 - 컴파일된 패턴 사용
            debug(f"메서드 추출 시작: {file_path}")
            debug(f"컴파일된 메서드 패턴 수: {len(self.compiled_method_patterns)}")
            debug(f"_extract_method_info_safe 호출됨: {file_path}")
            
            for i, compiled_pattern in enumerate(self.compiled_method_patterns):
                matches = compiled_pattern.finditer(java_content)
                match_count = 0
                
                for match in matches:
                    method_name = match.group(1)
                    match_count += 1
                    debug(f"패턴 {i+1}에서 메서드 발견: {method_name}")

                    # USER RULES: 제어문 키워드 필터링 적용 (METHOD 컴포넌트로 잘못 파싱 방지)
                    if self._is_control_keyword(method_name):
                        debug(f"제어문 키워드 필터링: {method_name} - 건너뜀")
                        continue

                    # 메서드 복잡도 분류로 정교한 필터링
                    method_body = self._extract_method_body(original_content, match.start())
                    complexity_classification = self._classify_method_complexity(method_name, method_body)

                    # 복잡도 분류는 통계용이므로 필터링하지 않음
                    # 모든 메서드를 포함하여 처리

                    # 클래스명 추출 (메서드가 속한 클래스)
                    class_name = self._find_class_for_method(java_content, match.start())
                    if not class_name:
                        debug(f"메서드 {method_name}의 클래스를 찾을 수 없음 - 건너뜀")
                        continue
                    debug(f"메서드 {method_name}이 클래스 {class_name}에 속함")

                    # 메서드 정보 생성
                    method_info = self._create_method_info_safe(match, original_content, file_path, class_name, complexity_classification)
                    if method_info:
                        methods.append(method_info)

            return methods

        except Exception as e:
            # USER RULES: 파싱 에러는 has_error='Y', error_message 남기고 계속 진행
            handle_error(f"_extract_method_info_safe에서 예외 발생: {str(e)}")
            handle_error(f"메서드 정보 추출 실패: {str(e)}")
            return []

    def _extract_method_body(self, java_content: str, method_start_pos: int) -> str:
        """메서드 본문 추출 (복잡도 분석용)"""
        try:
            # 메서드 시작에서 중괄호 찾기
            brace_start = java_content.find('{', method_start_pos)
            if brace_start == -1:
                return ""

            # 중괄호 매칭으로 메서드 본문 추출
            brace_count = 0
            in_string = False
            string_char = None
            escape_next = False

            for i in range(brace_start, len(java_content)):
                char = java_content[i]

                if escape_next:
                    escape_next = False
                    continue

                if char == '\\':
                    escape_next = True
                    continue

                if not in_string:
                    if char in ['"', "'"]:
                        in_string = True
                        string_char = char
                    elif char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # 메서드 종료
                            return java_content[brace_start:i+1]
                else:
                    if char == string_char:
                        in_string = False
                        string_char = None

            return ""

        except Exception as e:
            handle_error(f"메서드 본문 추출 실패: {str(e)}")
            return ""

    def _classify_method_complexity(self, method_name: str, method_body: str) -> str:
        """
        메서드 복잡도 분류로 정교한 필터링

        Returns:
            'exclude', 'include', 'complex_business'
        """
        try:
            # USER RULES: 하드코딩 지양 - 설정 파일에서 복잡도 값 가져오기
            complexity_config = self.config.get('method_complexity', {})
            exclude_complexity = complexity_config.get('exclude_complexity', 'exclude')
            include_complexity = complexity_config.get('include_complexity', 'include')
            complex_business_complexity = complexity_config.get('complex_business_complexity', 'complex_business')
            
            # 1. 단순 getter/setter 확인
            if self._is_simple_getter_setter(method_name, method_body):
                return exclude_complexity

            # 2. 기본 Object 메서드 확인
            if self._is_basic_object_method(method_name):
                return exclude_complexity

            # 3. 복잡한 비즈니스 로직 getter/setter 확인
            if self._is_complex_business_method(method_name, method_body):
                return complex_business_complexity

            # 4. 생성자 및 main 메서드 확인
            if self._is_constructor_or_main(method_name):
                return exclude_complexity

            return include_complexity  # 기본적으로 포함

        except Exception as e:
            handle_error(f"메서드 복잡도 분류 실패: {str(e)}")
            return complexity_config.get('include_complexity', 'include')

    def _is_simple_getter_setter(self, method_name: str, method_body: str) -> bool:
        """단순 getter/setter 확인"""
        try:
            # 단순 getter 패턴
            if re.match(r'^get[A-Z]\w*$', method_name):
                # 본문이 단순한 return 문만 있는지 확인
                body_lines = [line.strip() for line in method_body.split('\n') if line.strip() and not line.strip().startswith(('{}', '}'))]
                if len(body_lines) <= 3:  # return 문과 중괄호만
                    return True

            # 단순 setter 패턴
            if re.match(r'^set[A-Z]\w*$', method_name):
                # 본문이 단순한 할당문만 있는지 확인
                body_lines = [line.strip() for line in method_body.split('\n') if line.strip() and not line.strip().startswith(('{}', '}'))]
                if len(body_lines) <= 3:  # 할당문과 중괄호만
                    return True

            # 단순 boolean getter 패턴
            if re.match(r'^is[A-Z]\w*$', method_name):
                body_lines = [line.strip() for line in method_body.split('\n') if line.strip() and not line.strip().startswith(('{}', '}'))]
                if len(body_lines) <= 3:
                    return True

            return False

        except Exception as e:
            handle_error(f"단순 getter/setter 확인 실패: {str(e)}")
            return False

    def _is_basic_object_method(self, method_name: str) -> bool:
        """기본 Object 메서드 확인"""
        basic_methods = [
            'toString', 'equals', 'hashCode', 'getClass', 'clone',
            'finalize', 'notify', 'notifyAll', 'wait', 'main'
        ]
        return method_name in basic_methods

    def _is_complex_business_method(self, method_name: str, method_body: str) -> bool:
        """복잡한 비즈니스 로직 메서드 확인"""
        try:
            # USER RULES: 하드코딩 지양 - 컴파일된 패턴 사용
            # 복잡한 getter 패턴
            business_getter_patterns = self.compiled_business_patterns.get('business_getter_patterns', [])
            for pattern in business_getter_patterns:
                if pattern.match(method_name):
                    return True

            # 복잡한 setter 패턴
            business_setter_patterns = self.compiled_business_patterns.get('business_setter_patterns', [])
            for pattern in business_setter_patterns:
                if pattern.match(method_name):
                    return True

            # 복잡한 boolean 메서드 패턴
            business_boolean_patterns = self.compiled_business_patterns.get('business_boolean_patterns', [])
            for pattern in business_boolean_patterns:
                if pattern.match(method_name):
                    return True

            # 메서드 본문 복잡도 확인
            if self._is_method_body_complex(method_body):
                return True

            return False

        except Exception as e:
            handle_error(f"복잡한 비즈니스 메서드 확인 실패: {str(e)}")
            return False

    def _is_method_body_complex(self, method_body: str) -> bool:
        """메서드 본문 복잡도 확인"""
        try:
            if not method_body:
                return False

            # 복잡도 지표들
            lines = method_body.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]

            # 라인 수가 많으면 복잡
            if len(non_empty_lines) > 10:
                return True

            # 특정 키워드가 있으면 복잡한 로직으로 판단
            complex_keywords = ['if', 'for', 'while', 'switch', 'try', 'catch', 'synchronized']
            content = method_body.lower()
            complex_keyword_count = sum(1 for keyword in complex_keywords if keyword in content)

            if complex_keyword_count > 1:
                return True

            return False

        except Exception as e:
            handle_error(f"메서드 본문 복잡도 확인 실패: {str(e)}")
            return False

    def _is_constructor_or_main(self, method_name: str) -> bool:
        """생성자 및 main 메서드 확인"""
        return method_name in ['<init>', '<clinit>', 'main']

    def _is_control_keyword(self, method_name: str) -> bool:
        """
        제어문 키워드인지 확인 (METHOD 컴포넌트로 잘못 파싱 방지)
        
        Args:
            method_name: 확인할 메서드명
            
        Returns:
            제어문 키워드이면 True, 아니면 False
        """
        try:
            # USER RULES: 하드코딩 지양 - 설정 파일에서 제어문 키워드 가져오기
            exclude_patterns = self.config.get('method_filter_patterns', {}).get('exclude_patterns', [])
            
            # 제어문 키워드 패턴 확인
            for pattern in exclude_patterns:
                if pattern.startswith('^') and pattern.endswith('$'):
                    # 정확한 매치 패턴 (^keyword$)
                    keyword = pattern[1:-1]  # ^와 $ 제거
                    if method_name == keyword:
                        return True
            
            return False
            
        except Exception as e:
            # USER RULES: 파싱 에러는 has_error='Y', error_message 남기고 계속 진행
            handle_error(f"제어문 키워드 확인 실패: {method_name} - {str(e)}")
            return False

    def _find_class_for_method(self, java_content: str, method_pos: int) -> Optional[str]:
        """
        메서드가 속한 클래스명 찾기
        """
        try:
            # 메서드 위치 이전의 내용에서 가장 가까운 클래스 찾기
            content_before_method = java_content[:method_pos]
            debug(f"메서드 위치 이전 내용 길이: {len(content_before_method)}")

            # 컴파일된 클래스 패턴 사용
            last_class = None
            for i, compiled_pattern in enumerate(self.compiled_class_patterns):
                matches = list(compiled_pattern.finditer(content_before_method))
                debug(f"클래스 패턴 {i+1}에서 {len(matches)}개 클래스 발견")
                for match in matches:
                    last_class = match.group(1)
                    debug(f"발견된 클래스: {last_class}")

            debug(f"최종 선택된 클래스: {last_class}")
            return last_class

        except Exception as e:
            handle_error(f"메서드의 클래스 찾기 실패: {str(e)}")
            return None

    def _create_method_info_safe(self, match: re.Match, java_content: str, file_path: str, class_name: str, complexity: str) -> Optional[Dict[str, Any]]:
        """
        메서드 정보 안전하게 생성
        """
        try:
            method_name = match.group(1)

            # 라인 번호 추출
            line_start = java_content[:match.start()].count('\n') + 1
            line_end = self._find_method_end_line_safe(java_content, match.start())

            # 메서드 내용 추출 및 해시 생성
            method_content = self._extract_method_content_safe(java_content, match.start(), line_end)
            hash_value = HashUtils().generate_md5(method_content)

            return {
                'method_name': method_name,
                'class_name': class_name,
                'line_start': line_start,
                'line_end': line_end,
                'hash_value': hash_value,
                'file_path': file_path,
                'complexity': complexity
            }

        except Exception as e:
            handle_error(f"메서드 정보 생성 실패: {str(e)}")
            return None

    def _find_method_end_line_safe(self, java_content: str, method_start_pos: int) -> int:
        """
        메서드의 종료 라인 번호 안전하게 찾기
        """
        try:
            # 중괄호 매칭을 통한 메서드 종료 위치 찾기
            brace_count = 0
            in_string = False
            string_char = None
            escape_next = False

            for i in range(method_start_pos, len(java_content)):
                char = java_content[i]

                if escape_next:
                    escape_next = False
                    continue

                if char == '\\':
                    escape_next = True
                    continue

                if not in_string:
                    if char in ['"', "'"]:
                        in_string = True
                        string_char = char
                    elif char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # 메서드 종료 위치 찾음
                            return java_content[:i+1].count('\n') + 1
                else:
                    if char == string_char:
                        in_string = False
                        string_char = None

            # 메서드 종료를 찾지 못한 경우 파일 끝
            return java_content.count('\n') + 1

        except Exception as e:
            handle_error(f"메서드 종료 라인 찾기 실패: {str(e)}")
            return java_content.count('\n') + 1

    def _extract_method_content_safe(self, java_content: str, start_pos: int, end_line: int) -> str:
        """
        메서드 내용 추출 (해시 생성용)
        """
        try:
            lines = java_content.split('\n')
            start_line = java_content[:start_pos].count('\n') + 1

            if start_line <= len(lines) and end_line <= len(lines):
                method_lines = lines[start_line - 1:end_line]
                return '\n'.join(method_lines)

            return java_content[start_pos:]

        except Exception as e:
            handle_error(f"메서드 내용 추출 실패: {str(e)}")
            return ""

    def _analyze_inheritance_relationships_safe(self, java_content: str) -> List[Dict[str, Any]]:
        """
        Java 파일에서 상속 관계 분석 (클래스 상속만, implements 제외)
        """
        try:
            inheritance_relationships = []

            # USER RULES: 하드코딩 지양 - 컴파일된 상속 패턴 사용
            for compiled_pattern in self.compiled_extends_patterns:
                matches = compiled_pattern.finditer(java_content)
                for match in matches:
                    child_class = match.group(1)
                    parent_class = match.group(2)

                    # 상속 관계 정보 생성
                    relationship = {
                        'child_class': child_class,
                        'parent_class': parent_class,
                        'rel_type': 'EXTENDS'
                    }
                    inheritance_relationships.append(relationship)

            return inheritance_relationships

        except Exception as e:
            # USER RULES: 파싱 에러는 has_error='Y', error_message 남기고 계속 진행
            handle_error(f"상속 관계 분석 실패: {str(e)}")
            return []

    def _validate_parsing_results(self, parsed_data: List[Dict], original_content: str) -> List[Dict]:
        """파싱 결과 검증"""
        try:
            validated_results = []

            for item in parsed_data:
                # 1. 주석 내부 파싱 결과 제외
                if self._is_inside_comment_check(original_content, item.get('line_start', 1)):
                    continue

                # 2. 문자열 리터럴 내부 파싱 결과 제외
                if self._is_inside_string_literal_check(original_content, item.get('line_start', 1)):
                    continue

                # 3. 유효한 Java 구문인지 확인
                if self._is_valid_java_syntax(item):
                    validated_results.append(item)

            return validated_results

        except Exception as e:
            # 파싱 에러로 has_error='Y' 처리하고 계속 진행
            return parsed_data

    def _is_inside_comment_check(self, content: str, line_number: int) -> bool:
        """특정 라인이 주석 내부인지 확인 (개선된 버전)"""
        try:
            lines = content.split('\n')
            if line_number > len(lines) or line_number <= 0:
                return False

            target_line = lines[line_number - 1].strip()

            # 라인 주석 확인 - 라인이 //로 시작하는 경우만
            if target_line.startswith('//'):
                return True

            # 블록 주석 확인 (정확한 버전)
            # 해당 라인까지의 내용에서 블록 주석 상태 확인
            content_until_line = '\n'.join(lines[:line_number - 1])

            # /* 와 */ 의 쌍을 정확히 매칭
            block_start_count = content_until_line.count('/*')
            block_end_count = content_until_line.count('*/')

            # 시작된 블록 주석이 모두 닫혔으면 주석 내부가 아님
            if block_start_count <= block_end_count:
                return False

            # 마지막으로 열린 블록 주석의 위치 확인
            last_start = content_until_line.rfind('/*')
            last_end = content_until_line.rfind('*/')

            # 마지막 시작이 마지막 끝보다 뒤에 있으면 블록 주석 내부
            if last_start > last_end:
                # 하지만 해당 라인 자체가 블록 주석의 끝이면 제외
                if target_line.endswith('*/'):
                    return False
                return True

            return False

        except Exception as e:
            handle_error(f"주석 확인 실패: {str(e)}")
            return False

    def _is_inside_string_literal_check(self, content: str, line_number: int) -> bool:
        """특정 라인이 문자열 리터럴 내부인지 확인"""
        try:
            lines = content.split('\n')
            if line_number > len(lines):
                return False

            target_line = lines[line_number - 1]

            # 간단한 문자열 리터럴 확인
            quote_count = target_line.count('"')
            single_quote_count = target_line.count("'")

            # 홀수 개의 따옴표가 있으면 문자열 내부일 가능성
            return (quote_count % 2 == 1) or (single_quote_count % 2 == 1)

        except Exception as e:
            handle_error(f"문자열 리터럴 확인 실패: {str(e)}")
            return False

    def _is_valid_java_syntax(self, item: Dict) -> bool:
        """유효한 Java 구문인지 확인"""
        try:
            # 기본적인 검증
            if not item.get('class_name') and not item.get('method_name'):
                return False

            # 클래스명이나 메서드명이 Java 식별자 규칙에 맞는지 확인
            name = item.get('class_name') or item.get('method_name')
            if name and re.match(r'^[a-zA-Z_$][a-zA-Z0-9_$]*$', name):
                return True

            return False

        except Exception as e:
            handle_error(f"Java 구문 유효성 확인 실패: {str(e)}")
            return True  # 확실하지 않으면 포함

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        설정 파일 로드
        """
        try:
            # USER RULES: 공통함수 사용 지향
            config_utils = ConfigUtils()
            config = config_utils.load_yaml_config(config_path)
            if not config:
                handle_error(f"설정 파일을 로드할 수 없습니다: {config_path}")
                return self._get_default_config()
            return config
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            # USER RULES: Exception 발생시 handle_error()로 exit()
            handle_error(e, f"설정 파일 로드 실패: {config_path}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """기본 설정 반환"""
        return {
            'java_class_extraction_patterns': [
                r'public\s+class\s+(\w+)',
                r'class\s+(\w+)',
                r'public\s+interface\s+(\w+)',
                r'interface\s+(\w+)',
                r'public\s+enum\s+(\w+)',
                r'enum\s+(\w+)'
            ],
            'method_extraction_patterns': [
                # 기존 패턴 (어노테이션 없는 경우)
                r'(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*\{',
                # @Override 등 어노테이션이 있는 메소드 - 정확한 들여쓰기 패턴
                r'@\w+\s*\n\s*(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:\w+)\s+(\w+)\s*\([^)]*\)\s*\n\s+throws\s+[^{]+\{',
                # @Override 메소드 - throws 없는 경우
                r'@\w+\s*\n\s*(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:\w+)\s+(\w+)\s*\([^)]*\)\s*\{',
                # @Override 메소드 - 매개변수가 여러 줄인 경우
                r'@\w+\s*\n\s*(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:\w+)\s+(\w+)\s*\([^)]*\)\s*(?:\n\s+throws\s+[^{]+)?\s*\{',
                # 여러 어노테이션이 연속으로 있는 경우
                r'(?:@\w+\s*\n\s*)+(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:\w+)\s+(\w+)\s*\([^)]*\)\s*(?:\n\s+throws\s+[^{]+)?\s*\{'
            ],
            'complex_method_filtering': {
                'business_getter_patterns': [r'^get.+With.+', r'^get.+By.+'],
                'business_setter_patterns': [r'^set.+For.+', r'^set.+With.+'],
                'business_boolean_patterns': [r'^is.+Valid.+', r'^can.+']
            },
            'package_extraction_patterns': [
                r'src/main/java/(.+?)/',
                r'src/(.+?)/'
            ],
            'inheritance_analysis': {
                'extends_patterns': [
                    r'public\s+class\s+(\w+)\s+extends\s+(\w+)',
                    r'class\s+(\w+)\s+extends\s+(\w+)'
                ]
            },
            'performance': {
                'large_file_threshold_mb': 1.0,
                'batch_size': 100,
                'use_compiled_patterns': True
            }
        }

    def _find_line_number_in_original(self, original_content: str, class_name: str, class_declaration: str) -> int:
        """
        original_content에서 클래스 선언문의 실제 라인 번호 찾기

        Args:
            original_content: 원본 Java 파일 내용
            class_name: 클래스명
            class_declaration: 클래스 선언문

        Returns:
            라인 번호 (1부터 시작)
        """
        try:
            lines = original_content.split('\n')

            # 클래스명을 포함하고 class 키워드가 있는 라인 찾기
            for i, line in enumerate(lines):
                stripped_line = line.strip()
                if (class_name in stripped_line and
                    ('class ' in stripped_line or 'interface ' in stripped_line or 'enum ' in stripped_line)):
                    # 주석이 아닌 실제 선언문인지 확인
                    if not (stripped_line.startswith('//') or stripped_line.startswith('*') or stripped_line.startswith('/*')):
                        return i + 1

            # 찾지 못한 경우 1 반환 (기본값)
            handle_error(f"클래스 선언문 라인을 찾을 수 없음: {class_name}")
            return 1

        except Exception as e:
            handle_error(f"라인 번호 계산 실패: {str(e)}")
            return 1

    def _analyze_call_query_relationships_safe(self, java_content: str, methods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        CALL_QUERY 관계 분석 (메서드 → SQL 쿼리)
        """
        try:
            call_query_relationships = []

            for method in methods:
                try:
                    method_name = method.get('method_name', '')
                    class_name = method.get('class_name', '')
                    line_start = method.get('line_start', 1)
                    line_end = method.get('line_end', 1)

                    # 메서드 본문 추출
                    method_body = self._extract_method_body_from_lines(java_content, line_start, line_end)
                    if not method_body:
                        continue

                    # CALL_QUERY 패턴 매칭
                    for compiled_pattern in self.compiled_call_query_patterns:
                        matches = compiled_pattern.finditer(method_body)
                        for match in matches:
                            query_id = self._extract_query_id_from_match(match, method_body)
                            if query_id:
                                relationship = {
                                    'src_name': f"{class_name}.{method_name}",
                                    'dst_name': query_id,
                                    'rel_type': 'CALL_QUERY',
                                    'line_number': line_start + self._find_line_in_method_body(method_body, match.start()),
                                    'relationship_detail': match.group(0)
                                }
                                call_query_relationships.append(relationship)

                except Exception as e:
                    handle_error(f"CALL_QUERY 관계 분석 실패: {method.get('method_name', 'UNKNOWN')} - {str(e)}")

            return call_query_relationships

        except Exception as e:
            handle_error(f"CALL_QUERY 관계 분석 실패: {str(e)}")
            return []

    def _analyze_call_method_relationships_safe(self, java_content: str, methods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        CALL_METHOD 관계 분석 (메서드 → 메서드)
        """
        try:
            call_method_relationships = []

            for method in methods:
                try:
                    method_name = method.get('method_name', '')
                    class_name = method.get('class_name', '')
                    line_start = method.get('line_start', 1)
                    line_end = method.get('line_end', 1)

                    # 메서드 본문 추출
                    method_body = self._extract_method_body_from_lines(java_content, line_start, line_end)
                    if not method_body:
                        continue

                    # CALL_METHOD 패턴 매칭
                    for compiled_pattern in self.compiled_call_method_patterns:
                        matches = compiled_pattern.finditer(method_body)
                        for match in matches:
                            called_method = self._extract_called_method_from_match(match)
                            if called_method and not self._should_exclude_method(called_method):
                                relationship = {
                                    'src_name': f"{class_name}.{method_name}",
                                    'dst_name': called_method,
                                    'rel_type': 'CALL_METHOD',
                                    'line_number': line_start + self._find_line_in_method_body(method_body, match.start()),
                                    'relationship_detail': match.group(0)
                                }
                                call_method_relationships.append(relationship)

                except Exception as e:
                    handle_error(f"CALL_METHOD 관계 분석 실패: {method.get('method_name', 'UNKNOWN')} - {str(e)}")

            return call_method_relationships

        except Exception as e:
            handle_error(f"CALL_METHOD 관계 분석 실패: {str(e)}")
            return []

    def _analyze_use_table_relationships_safe(self, java_content: str, methods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        USE_TABLE 관계 분석 (메서드 → 테이블)
        """
        try:
            use_table_relationships = []

            for method in methods:
                try:
                    method_name = method.get('method_name', '')
                    class_name = method.get('class_name', '')
                    line_start = method.get('line_start', 1)
                    line_end = method.get('line_end', 1)

                    # 메서드 본문 추출
                    method_body = self._extract_method_body_from_lines(java_content, line_start, line_end)
                    if not method_body:
                        continue

                    # USE_TABLE 패턴 매칭
                    for compiled_pattern in self.compiled_use_table_patterns:
                        matches = compiled_pattern.finditer(method_body)
                        for match in matches:
                            table_name = self._extract_table_name_from_match(match)
                            if table_name and ValidationUtils.is_valid_table_name(table_name):
                                relationship = {
                                    'src_name': f"{class_name}.{method_name}",
                                    'dst_name': table_name,
                                    'rel_type': 'USE_TABLE',
                                    'line_number': line_start + self._find_line_in_method_body(method_body, match.start()),
                                    'relationship_detail': match.group(0)
                                }
                                use_table_relationships.append(relationship)

                except Exception as e:
                    handle_error(f"USE_TABLE 관계 분석 실패: {method.get('method_name', 'UNKNOWN')} - {str(e)}")

            return use_table_relationships

        except Exception as e:
            handle_error(f"USE_TABLE 관계 분석 실패: {str(e)}")
            return []

    def _extract_method_body_from_lines(self, java_content: str, line_start: int, line_end: int) -> str:
        """라인 범위로부터 메서드 본문 추출"""
        try:
            lines = java_content.split('\n')
            if line_start > len(lines) or line_end > len(lines):
                return ""
            
            method_lines = lines[line_start - 1:line_end]
            return '\n'.join(method_lines)

        except Exception as e:
            handle_error(f"메서드 본문 추출 실패: {str(e)}")
            return ""

    def _extract_query_id_from_match(self, match: re.Match, method_body: str) -> Optional[str]:
        """매치 결과에서 쿼리 ID 추출"""
        try:
            matched_text = match.group(0)
            
            # mapper.methodName() 패턴
            if 'mapper.' in matched_text.lower():
                # mapper. 뒤의 메서드명 추출
                mapper_match = re.search(r'mapper\.(\w+)', matched_text, re.IGNORECASE)
                if mapper_match:
                    return mapper_match.group(1)
            
            # sqlSession.methodName() 패턴
            if 'sqlsession.' in matched_text.lower():
                # sqlSession. 뒤의 메서드명 추출
                sqlsession_match = re.search(r'sqlsession\.(\w+)', matched_text, re.IGNORECASE)
                if sqlsession_match:
                    return sqlsession_match.group(1)
            
            # 기타 패턴들
            if match.groups():
                return match.group(1)
            
            return None

        except Exception as e:
            handle_error(f"쿼리 ID 추출 실패: {str(e)}")
            return None

    def _extract_called_method_from_match(self, match: re.Match) -> Optional[str]:
        """매치 결과에서 호출된 메서드명 추출"""
        try:
            matched_text = match.group(0)
            
            # this.methodName() 패턴
            if 'this.' in matched_text:
                this_match = re.search(r'this\.(\w+)', matched_text)
                if this_match:
                    return this_match.group(1)
            
            # object.methodName() 패턴
            if '.' in matched_text and 'this.' not in matched_text:
                dot_match = re.search(r'(\w+)\.(\w+)', matched_text)
                if dot_match:
                    return dot_match.group(2)
            
            # methodName() 패턴 (같은 클래스 내)
            if match.groups():
                return match.group(1)
            
            return None

        except Exception as e:
            handle_error(f"호출된 메서드 추출 실패: {str(e)}")
            return None

    def _extract_table_name_from_match(self, match: re.Match) -> Optional[str]:
        """매치 결과에서 테이블명 추출"""
        try:
            if match.groups():
                return match.group(1)
            return None

        except Exception as e:
            handle_error(f"테이블명 추출 실패: {str(e)}")
            return None

    def _should_exclude_method(self, method_name: str) -> bool:
        """메서드가 제외 대상인지 확인"""
        try:
            for compiled_pattern in self.compiled_exclude_methods:
                if compiled_pattern.match(method_name):
                    return True
            return False

        except Exception as e:
            handle_error(f"메서드 제외 확인 실패: {str(e)}")
            return False



    def _find_line_in_method_body(self, method_body: str, position: int) -> int:
        """메서드 본문 내에서 위치의 라인 번호 찾기"""
        try:
            return method_body[:position].count('\n') + 1

        except Exception as e:
            handle_error(f"라인 번호 찾기 실패: {str(e)}")
            return 1

    def _extract_sql_queries_from_java(self, java_content: str, java_file: str) -> List[Dict[str, Any]]:
        """
        Java 파일에서 SQL 쿼리 추출
        StringBuilder로 동적 생성되는 쿼리를 분석하여 SQL 컴포넌트로 추출
        
        Args:
            java_content: Java 파일 내용
            java_file: Java 파일 경로
            
        Returns:
            추출된 SQL 쿼리 정보 리스트
        """
        try:
            sql_queries = []
            
            # 설정에서 SQL 패턴 로드
            sql_patterns = self.config.get('relationship_analysis', {}).get('use_table_patterns', [])
            if not sql_patterns:
                debug(f"SQL 패턴이 설정되지 않음: {java_file}")
                return []
            
            # StringBuilder 패턴으로 동적 쿼리 추출 (개선된 패턴)
            stringbuilder_pattern = r'StringBuilder\s+(\w+)\s*=\s*new\s+StringBuilder\(\);(.*?)(?=System\.out\.println|return)'
            
            matches = re.finditer(stringbuilder_pattern, java_content, re.DOTALL | re.MULTILINE)
            
            for match_idx, match in enumerate(matches):
                var_name = match.group(1)
                query_construction = match.group(2)
                
                # append 호출들에서 SQL 문장 조합
                append_pattern = rf'{re.escape(var_name)}\.append\s*\(\s*"([^"]+)"\s*\)'
                append_matches = re.findall(append_pattern, query_construction)
                
                if append_matches:
                    # SQL 문장 조합
                    full_query = ' '.join(append_matches)
                    
                    # SQL 쿼리인지 확인 (SELECT, INSERT, UPDATE, DELETE 포함)
                    sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'WHERE', 'JOIN']
                    if any(keyword in full_query.upper() for keyword in sql_keywords):
                        
                        # 쿼리 타입 결정
                        query_type = self._determine_java_sql_type(full_query)
                        
                        # 사용된 테이블 추출
                        used_tables = self._extract_tables_from_java_sql(full_query)
                        
                        # 조인 관계 분석
                        join_relationships = self._analyze_java_sql_joins(full_query)
                        
                        # 메서드명 추출 (StringBuilder가 포함된 메서드)
                        method_name = self._find_containing_method_name(java_content, match.start())
                        
                        sql_info = {
                            'query_id': method_name or f'dynamicQuery_{match_idx + 1}',
                            'query_type': query_type,
                            'sql_content': full_query,
                            'used_tables': used_tables,
                            'join_relationships': join_relationships,
                            'is_dynamic': True,
                            'method_name': method_name,
                            'line_start': java_content[:match.start()].count('\n') + 1,
                            'line_end': java_content[:match.end()].count('\n') + 1,
                            'has_error': 'N',
                            'error_message': None
                        }
                        
                        sql_queries.append(sql_info)
                        debug(f"Java SQL 쿼리 추출: {method_name} - {query_type}")
            
            return sql_queries
            
        except Exception as e:
            handle_error(e, f"Java SQL 쿼리 추출 실패: {java_file}")
            return []

    def _determine_java_sql_type(self, sql_content: str) -> str:
        """Java에서 추출한 SQL의 타입 결정"""
        try:
            sql_upper = sql_content.upper().strip()
            
            if sql_upper.startswith('SELECT'):
                return 'SQL_SELECT'
            elif sql_upper.startswith('INSERT'):
                return 'SQL_INSERT'
            elif sql_upper.startswith('UPDATE'):
                return 'SQL_UPDATE'
            elif sql_upper.startswith('DELETE'):
                return 'SQL_DELETE'
            else:
                return 'SQL_UNKNOWN'
                
        except Exception as e:
            handle_error(e, "Java SQL 타입 결정 실패")
            return 'SQL_UNKNOWN'

    def _extract_tables_from_java_sql(self, sql_content: str) -> List[str]:
        """Java SQL에서 사용된 테이블 추출"""
        try:
            tables = []
            sql_upper = sql_content.upper()
            
            # FROM 절 테이블 추출
            from_pattern = r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            from_matches = re.findall(from_pattern, sql_upper)
            tables.extend(from_matches)
            
            # JOIN 절 테이블 추출
            join_pattern = r'\b(?:LEFT\s+|RIGHT\s+|INNER\s+|OUTER\s+)?JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            join_matches = re.findall(join_pattern, sql_upper)
            tables.extend(join_matches)
            
            # INSERT INTO 테이블 추출
            insert_pattern = r'\bINSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            insert_matches = re.findall(insert_pattern, sql_upper)
            tables.extend(insert_matches)
            
            # UPDATE 테이블 추출
            update_pattern = r'\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            update_matches = re.findall(update_pattern, sql_upper)
            tables.extend(update_matches)
            
            # DELETE FROM 테이블 추출
            delete_pattern = r'\bDELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            delete_matches = re.findall(delete_pattern, sql_upper)
            tables.extend(delete_matches)
            
            # 중복 제거 및 정리
            return list(set([table.strip() for table in tables if table.strip()]))
            
        except Exception as e:
            handle_error(e, "Java SQL 테이블 추출 실패")
            return []

    def _analyze_java_sql_joins(self, sql_content: str) -> List[Dict[str, Any]]:
        """Java SQL에서 조인 관계 분석 (공통 모듈 사용)"""
        try:
            # 공통 SQL 조인 분석 모듈 사용
            join_relationships = self.sql_join_analyzer.analyze_join_relationships(
                sql_content, "java_source", 0
            )
            
            # Java 파서용 형식으로 변환
            java_join_relationships = []
            for rel in join_relationships:
                java_join_info = {
                    'source_table': rel.get('source_table', ''),
                    'target_table': rel.get('target_table', ''),
                    'rel_type': rel.get('rel_type', 'JOIN_EXPLICIT'),
                    'join_type': rel.get('join_type', 'UNKNOWN_JOIN'),
                    'join_condition': rel.get('description', ''),
                    'confidence': rel.get('confidence', 0.8)
                }
                java_join_relationships.append(java_join_info)
            
            debug(f"Java SQL 조인 분석 완료: {len(java_join_relationships)}개 관계 발견")
            return java_join_relationships
            
        except Exception as e:
            handle_error(e, "Java SQL 조인 분석 실패")
            return []

    def _find_containing_method_name(self, java_content: str, position: int) -> Optional[str]:
        """주어진 위치를 포함하는 메서드명 찾기"""
        try:
            # 위치 이전의 내용에서 가장 가까운 메서드 선언 찾기
            content_before = java_content[:position]
            
            # 메서드 패턴 (설정에서 로드)
            method_patterns = self.config.get('method_extraction_patterns', [])
            
            # 역순으로 메서드 패턴 매칭
            for pattern in method_patterns:
                matches = list(re.finditer(pattern, content_before, re.MULTILINE))
                if matches:
                    # 가장 마지막 매치 (가장 가까운 메서드)
                    last_match = matches[-1]
                    return last_match.group(1)
            
            return None
            
        except Exception as e:
            handle_error(e, "메서드명 찾기 실패")
            return None