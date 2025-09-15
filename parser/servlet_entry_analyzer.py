"""
SourceAnalyzer Servlet 프레임워크 진입점 분석기
- Servlet Framework (@WebServlet, HttpServlet 상속, web.xml 매핑) 기반 API 진입점 분석
- AST 파싱 및 정규식 Fallback 전략
- web.xml 파싱 및 상속 관계 분석 지원
- @WebServlet, HttpServlet, GenericServlet 등 분석
"""

import re
import time
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from .base_entry_analyzer import BaseEntryAnalyzer, BackendEntryInfo, FileInfo
from util.logger import app_logger, handle_error
from util.database_utils import DatabaseUtils


class ServletEntryAnalyzer(BaseEntryAnalyzer):
    """Servlet 프레임워크 진입점 분석기"""
    
    def __init__(self, servlet_url_map: Dict[str, str] = None):
        """
        Servlet 분석기 초기화
        
        Args:
            servlet_url_map: web.xml에서 파싱한 서블릿 클래스명과 URL 패턴 맵
        """
        # 설정 파일 경로 구성
        from util.path_utils import PathUtils
        path_utils = PathUtils()
        config_path = path_utils.get_parser_config_path("servlet_entry")
        
        super().__init__('servlet', config_path)
        
        # web.xml 파싱 결과 맵
        self.servlet_url_map = servlet_url_map or {}
        
        # 정규식 패턴 미리 컴파일
        self._compile_regex_patterns()
        
        # 데이터베이스 유틸리티 초기화
        self.db_utils = None
    
    def _compile_regex_patterns(self) -> None:
        """정규식 패턴 미리 컴파일"""
        try:
            # 설정에서 정규식 패턴 가져오기
            class_declaration_pattern = self.get_config_value("regex_patterns.class_declaration")
            web_servlet_pattern = self.get_config_value("regex_patterns.web_servlet_annotation")
            do_method_pattern = self.get_config_value("regex_patterns.do_method")
            service_method_pattern = self.get_config_value("regex_patterns.service_method")
            
            # 정규식 컴파일
            self.class_declaration_regex = re.compile(class_declaration_pattern) if class_declaration_pattern else None
            self.web_servlet_regex = re.compile(web_servlet_pattern) if web_servlet_pattern else None
            self.do_method_regex = re.compile(do_method_pattern) if do_method_pattern else None
            self.service_method_regex = re.compile(service_method_pattern) if service_method_pattern else None
            
            app_logger.debug("Servlet 분석기 정규식 패턴 컴파일 완료")
            
        except Exception as e:
            app_logger.warning(f"정규식 패턴 컴파일 실패, 기본 패턴 사용: {str(e)}")
            self._set_default_regex_patterns()
    
    def _set_default_regex_patterns(self) -> None:
        """기본 정규식 패턴 설정"""
        self.class_declaration_regex = re.compile(r'(?m)^[ \t]*((public|private|protected)\s+)?class\s+(\w+)\s+extends\s+(\w+)')
        # URL 패턴 추출 개선: 더 정확한 패턴 매칭
        self.web_servlet_regex = re.compile(r'@WebServlet\s*\(\s*(?:urlPatterns\s*=\s*)?(?:{\s*)?([^}]+)(?:\s*})?\s*\)')
        self.do_method_regex = re.compile(r'(?:public|protected)\s+void\s+(do\w+)\s*\([^)]*\)')
        self.service_method_regex = re.compile(r'(?:public|protected)\s+void\s+service\s*\([^)]*\)')
    
    def _init_database_utils(self, project_name: str) -> None:
        """데이터베이스 유틸리티 초기화"""
        if self.db_utils is None:
            # 공통함수 사용 - 하드코딩 금지
            db_path = self.path_utils.get_project_metadata_db_path(project_name)
            self.db_utils = DatabaseUtils(db_path)
    
    def analyze_backend_entry(self, java_file: FileInfo, stats: 'StatisticsCollector') -> List[BackendEntryInfo]:
        """
        Servlet 진입점 분석 (Fallback 전략 포함)
        AST -> 정규식 순서로 시도합니다.
        
        Args:
            java_file: 분석할 Java 파일 정보
            stats: 통계 수집기
            
        Returns:
            백엔드 진입점 정보 리스트
        """
        start_time = time.time()
        
        try:
            # 1. 정규식 기반 파싱을 우선 실행 (안정성 확보)
            regex_results = self._parse_with_regex(java_file.content, java_file.file_path, java_file.file_id)
            if regex_results:
                processing_time = time.time() - start_time
                if stats:
                    stats.log_file_result(
                        framework=self.framework_name,
                        file_path=java_file.file_path,
                        success=True,
                        stage='regex',
                        processing_time=processing_time,
                        entries_found=len(regex_results)
                    )
                return regex_results

            # 2. AST 기반 파싱으로 Fallback
            ast_results = self._parse_with_ast(java_file.content, java_file.file_path, java_file.file_id)
            if ast_results is not None:  # None이 아니면 성공 또는 복구 불가능한 오류
                processing_time = time.time() - start_time
                if stats:
                    stats.log_file_result(
                        framework=self.framework_name,
                        file_path=java_file.file_path,
                        success=True,
                        stage='ast_fallback',
                        processing_time=processing_time,
                        entries_found=len(ast_results)
                    )
                return ast_results

            # 모든 파싱 실패
            # USER 승인: 파싱 실패시 has_error 처리 (승인받은 예외 케이스)
            # 승인받지 않은 경우를 제외하고는 모든 에러는 handle_error() 처리 해야함
            processing_time = time.time() - start_time
            error_message = f"모든 파싱 방법으로 Servlet 진입점을 찾지 못했습니다: {java_file.file_path}"
            
            if stats:
                stats.log_file_result(
                    framework=self.framework_name,
                    file_path=java_file.file_path,
                    success=False,
                    stage='parsing_failed',
                    processing_time=processing_time,
                    entries_found=0,
                    error_message=error_message
                )
            return []

        except Exception as e:
            # USER RULE: 예측하지 못한 예외는 handle_error()로 즉시 종료
            processing_time = time.time() - start_time
            error_message = f"Servlet 분석 중 심각한 오류 발생: {str(e)}"
            handle_error(e, error_message)
            return []  # 이 라인은 실행되지 않음 (handle_error에서 exit)
    
    def _parse_with_ast(self, content: str, file_path: str = '', file_id: int = 0) -> Optional[List[BackendEntryInfo]]:
        """
        AST 기반 Servlet 파싱. 실패 시 None 반환.
        
        Args:
            content: Java 파일 내용
            file_path: 파일 경로
            file_id: 파일 ID
            
        Returns:
            분석 결과 리스트 또는 None (실패시)
        """
        try:
            # javalang 라이브러리 사용 시도
            try:
                import javalang
                from javalang.tokenizer import LexerError
                from javalang.parser import JavaSyntaxError
            except ImportError:
                # USER RULE: 필수 라이브러리 누락은 handle_error()로 즉시 종료
                handle_error(ImportError("javalang 라이브러리가 설치되지 않음"), 
                           "Servlet AST 파싱을 위한 필수 라이브러리 누락")
            
            try:
                tree = javalang.parse.parse(content)
                return self._extract_from_ast_tree(tree, content, file_path, file_id)
            except (LexerError, JavaSyntaxError, RecursionError) as e:
                # USER RULE: 파싱 문법 오류 및 재귀 오류는 Fallback을 위해 None 반환
                app_logger.debug(f"AST 파싱 오류, 정규식 파싱으로 Fallback: {str(e)}")
                return None
            except Exception as e:
                # USER RULE: 기타 예외는 handle_error()로 즉시 종료
                handle_error(e, f"AST 파싱 중 예외 발생")
                
        except Exception as e:
            # USER RULE: AST 파싱 초기화 실패는 handle_error()로 즉시 종료
            handle_error(e, f"AST 파싱 초기화 실패")
    
    def _extract_from_ast_tree(self, tree, content: str, file_path: str = '', file_id: int = 0) -> List[BackendEntryInfo]:
        """
        AST 트리에서 Servlet 진입점 추출
        
        Args:
            tree: javalang AST 트리
            content: 원본 파일 내용
            file_path: 파일 경로
            file_id: 파일 ID
            
        Returns:
            백엔드 진입점 정보 리스트
        """
        entries = []
        lines = content.split('\n')
        
        try:
            import javalang
            # 클래스 순회
            for path, node in tree:
                if isinstance(node, javalang.tree.ClassDeclaration):
                    class_info = self._extract_class_info_ast(node, lines, file_path, file_id)
                    if class_info:
                        # 클래스 내부의 메서드들을 직접 찾기
                        if hasattr(node, 'body') and node.body:
                            for body_item in node.body:
                                if isinstance(body_item, javalang.tree.MethodDeclaration):
                                    method_entries = self._extract_method_info_ast(body_item, class_info, lines)
                                    entries.extend(method_entries)
            
            return entries
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"AST 트리 추출 중 오류")
    
    def _extract_class_info_ast(self, class_node, lines: List[str], file_path: str = '', file_id: int = 0) -> Optional[Dict[str, Any]]:
        """AST로 클래스 정보 추출"""
        try:
            # 클래스 어노테이션 확인
            class_annotations = []
            url_patterns = []
            
            if hasattr(class_node, 'annotations') and class_node.annotations:
                for annotation in class_node.annotations:
                    annotation_name = annotation.name
                    class_annotations.append(f"@{annotation_name}")
                    
            # @WebServlet 어노테이션에서 URL 패턴 추출
            if annotation_name == 'WebServlet':
                extracted_patterns = self._extract_url_patterns_from_annotation(annotation)
                url_patterns.extend(extracted_patterns)
                app_logger.debug(f"@WebServlet 어노테이션에서 URL 패턴 추출: {extracted_patterns}")
            
            # @WebServlet 어노테이션이 없으면 web.xml 맵에서 확인
            if not url_patterns:
                class_full_name = self._get_full_class_name(class_node.name, content='\n'.join(lines))
                if class_full_name in self.servlet_url_map:
                    url_patterns.append(self.servlet_url_map[class_full_name])
            
            # Servlet 클래스인지 확인 (상속 관계 또는 어노테이션)
            is_servlet = (
                any('@WebServlet' in ann for ann in class_annotations) or
                self._is_servlet_class(class_node, lines)
            )
            
            if not is_servlet:
                return None
            
            return {
                'name': class_node.name,
                'annotations': class_annotations,
                'url_patterns': url_patterns,
                'line_start': class_node.position.line if hasattr(class_node, 'position') else 0,
                'file_path': file_path,
                'file_id': file_id
            }
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"클래스 정보 추출 실패")
    
    def _extract_method_info_ast(self, method_node, class_info: Dict[str, Any], lines: List[str]) -> List[BackendEntryInfo]:
        """AST로 메서드 정보 추출"""
        entries = []
        
        try:
            method_name = method_node.name
            
            # doXXX 메서드나 service 메서드인지 확인
            http_methods = self._get_http_methods_from_method_name(method_name)
            if not http_methods:
                return entries
            
            # 메서드 시그니처 검증
            if not self._is_valid_servlet_method_signature(method_node.parameters, method_name):
                return entries
            
            # 클래스의 URL 패턴들에 대해 엔트리 생성
            for url_pattern in class_info.get('url_patterns', ['/']):
                for http_method in http_methods:
                    entry = self.create_backend_entry_info(
                        class_name=class_info['name'],
                        method_name=method_name,
                        url_pattern=url_pattern,
                        http_method=http_method,
                        file_path=class_info.get('file_path', ''),
                        file_id=class_info.get('file_id', 0),
                        line_start=method_node.position.line if hasattr(method_node, 'position') else 0,
                        line_end=method_node.position.line if hasattr(method_node, 'position') else 0,
                        parameters=self._extract_method_parameters(method_node),
                        return_type=method_node.return_type.name if (hasattr(method_node, 'return_type') and method_node.return_type is not None) else 'void',
                        annotations=[f"@{method_name}"]
                    )
                    entries.append(entry)
            
            return entries
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"메서드 정보 추출 실패")
    
    def _parse_with_regex(self, content: str, file_path: str, file_id: int = 0) -> List[BackendEntryInfo]:
        """
        정규식 기반 Servlet 파싱
        
        Args:
            content: Java 파일 내용
            file_path: 파일 경로
            file_id: 파일 ID
            
        Returns:
            백엔드 진입점 정보 리스트
        """
        try:
            # 1. 주석 및 문자열 제거 전처리
            clean_content = self.preprocess_content(content)
            
            servlet_entries = []
            
            # 2. 클래스 선언과 상속 관계 분석
            if self.class_declaration_regex:
                class_matches = self.class_declaration_regex.findall(clean_content)
                for match in class_matches:
                    class_name = match[2]  # 클래스명
                    parent_class = match[3]  # 부모 클래스명
                    
                    # HttpServlet 상속 확인
                    if parent_class in ['HttpServlet', 'GenericServlet']:
                        # 3. @WebServlet 어노테이션 분석
                        url_patterns = self._extract_url_patterns_regex(clean_content)
                        
                        # @WebServlet 어노테이션이 없으면 web.xml 맵에서 확인
                        if not url_patterns:
                            class_full_name = self._get_full_class_name_from_content(class_name, content)
                            if class_full_name in self.servlet_url_map:
                                url_patterns.append(self.servlet_url_map[class_full_name])
                        
                        # URL 패턴이 없으면 기본값 사용
                        if not url_patterns:
                            url_patterns = ['/']
                        
                        app_logger.debug(f"정규식 파싱에서 URL 패턴 추출: {url_patterns}")
                        
                        # 4. doXXX 메서드 및 service 메서드 분석
                        do_methods = self._extract_do_methods_regex(clean_content)
                        service_methods = self._extract_service_methods_regex(clean_content)
                        
                        # 모든 메서드 정보 통합
                        all_methods = {}
                        all_methods.update(do_methods)
                        all_methods.update(service_methods)
                        
                        # 각 URL 패턴과 HTTP 메서드 조합으로 진입점 생성
                        for url_pattern in url_patterns:
                            for method_name, http_methods in all_methods.items():
                                for http_method in http_methods:
                                    entry = self.create_backend_entry_info(
                                        class_name=class_name,
                                        method_name=method_name,
                                        url_pattern=url_pattern,
                                        http_method=http_method,
                                        file_path=file_path,
                                        file_id=file_id,
                                        line_start=0,  # 정규식으로는 정확한 라인 번호 추출 어려움
                                        line_end=0,
                                        parameters=[],  # 정규식으로는 파라미터 추출 어려움
                                        return_type="void",
                                        annotations=[f"@{method_name}"]
                                    )
                                    servlet_entries.append(entry)
            
            return servlet_entries
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"정규식 파싱 실패: {file_path}")
    
    def _extract_url_patterns_from_annotation(self, annotation) -> List[str]:
        """@WebServlet 어노테이션에서 URL 패턴 추출"""
        try:
            url_patterns = []
            
            # element 속성에서 직접 추출
            if hasattr(annotation, 'element') and annotation.element:
                if hasattr(annotation.element, 'value'):
                    value = annotation.element.value
                    if isinstance(value, str):
                        url_patterns.append(value.strip('"'))
                    elif hasattr(value, 'values'):  # 배열 형태
                        for val in value.values:
                            if hasattr(val, 'value'):
                                url_patterns.append(val.value.strip('"'))
            
            # elements 방식으로 추출
            if not url_patterns and hasattr(annotation, 'elements') and annotation.elements:
                for element in annotation.elements:
                    if element.name in ['urlPatterns', 'value']:
                        if hasattr(element.value, 'value'):
                            url_patterns.append(element.value.value.strip('"'))
                        elif hasattr(element.value, 'values'):  # 배열 형태
                            for val in element.value.values:
                                if hasattr(val, 'value'):
                                    url_patterns.append(val.value.strip('"'))
            
            return url_patterns
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"URL 패턴 추출 실패")
    
    def _extract_url_patterns_regex(self, content: str) -> List[str]:
        """정규식으로 URL 패턴 추출"""
        try:
            url_patterns = []
            
            if self.web_servlet_regex:
                matches = self.web_servlet_regex.findall(content)
                for match in matches:
                    patterns_str = match.strip()
                    # 쉼표로 구분된 패턴들 파싱
                    patterns = [p.strip().strip('"') for p in patterns_str.split(',')]
                    url_patterns.extend(patterns)
                    
                    app_logger.debug(f"정규식 매칭 결과: {match} -> {patterns}")
            
            return url_patterns
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"정규식 URL 패턴 추출 실패")
    
    def _extract_do_methods_regex(self, content: str) -> Dict[str, List[str]]:
        """정규식으로 doXXX 메서드 추출"""
        try:
            methods = {}
            
            if self.do_method_regex:
                matches = self.do_method_regex.findall(content)
                for method_name in matches:
                    http_method = self._get_http_method_from_do_method(method_name)
                    if http_method:
                        methods[method_name] = [http_method]
            
            return methods
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"정규식 doXXX 메서드 추출 실패")
    
    def _extract_service_methods_regex(self, content: str) -> Dict[str, List[str]]:
        """정규식으로 service 메서드 추출"""
        try:
            methods = {}
            
            if self.service_method_regex:
                matches = self.service_method_regex.findall(content)
                if matches:
                    # service 메서드가 있으면 여러 HTTP 메서드에 매핑
                    service_methods = self.get_config_value("http_method_mapping.service_method_http_methods", ["GET", "POST"])
                    methods["service"] = service_methods
            
            return methods
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"정규식 service 메서드 추출 실패")
    
    def _get_http_methods_from_method_name(self, method_name: str) -> List[str]:
        """메서드명에서 HTTP 메서드 추출"""
        try:
            method_mapping = self.get_config_value("http_method_mapping.method_name_mapping", {})
            
            if method_name in method_mapping:
                http_method = method_mapping[method_name]
                if http_method == "MULTI":
                    # service 메서드의 경우 여러 HTTP 메서드 반환
                    return self.get_config_value("http_method_mapping.service_method_http_methods", ["GET", "POST"])
                else:
                    return [http_method]
            
            return []
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"HTTP 메서드 추출 실패: {method_name}")
    
    def _get_http_method_from_do_method(self, method_name: str) -> Optional[str]:
        """doXXX 메서드명에서 HTTP 메서드 추출"""
        try:
            method_mapping = self.get_config_value("http_method_mapping.method_name_mapping", {})
            return method_mapping.get(method_name)
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"doXXX 메서드 HTTP 메서드 추출 실패: {method_name}")
    
    def _is_valid_servlet_method_signature(self, parameters, method_name: str) -> bool:
        """메서드 파라미터가 Servlet 메서드 시그니처인지 검증"""
        try:
            if not parameters:
                return False
            
            # doXXX 메서드 시그니처 검증
            if method_name.startswith('do'):
                expected_signature = self.get_config_value("method_signature_validation.do_method_signature", 
                                                         ["HttpServletRequest", "HttpServletResponse"])
                if len(parameters) != len(expected_signature):
                    return False
                
                for i, param in enumerate(parameters):
                    param_type = param.type.name if hasattr(param.type, 'name') else str(param.type)
                    if param_type != expected_signature[i]:
                        return False
                
                return True
            
            # service 메서드 시그니처 검증
            elif method_name == 'service':
                expected_signature = self.get_config_value("method_signature_validation.service_method_signature",
                                                         ["ServletRequest", "ServletResponse"])
                if len(parameters) != len(expected_signature):
                    return False
                
                for i, param in enumerate(parameters):
                    param_type = param.type.name if hasattr(param.type, 'name') else str(param.type)
                    if param_type != expected_signature[i]:
                        return False
                
                return True
            
            return False
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"메서드 시그니처 검증 실패: {method_name}")
    
    def _is_servlet_class(self, class_node, lines: List[str]) -> bool:
        """클래스가 Servlet 클래스인지 확인 (상속 관계 기반)"""
        try:
            # 상속 관계 확인
            if hasattr(class_node, 'extends') and class_node.extends:
                parent_name = class_node.extends.name if hasattr(class_node.extends, 'name') else str(class_node.extends)
                inheritance_classes = self.get_config_value("servlet_annotations.inheritance_classes", 
                                                          ["HttpServlet", "GenericServlet"])
                return parent_name in inheritance_classes
            
            return False
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"Servlet 클래스 확인 실패")
    
    def _get_full_class_name(self, class_name: str, content: str) -> str:
        """클래스의 전체 이름(FQDN) 추출"""
        try:
            # 패키지 선언 찾기
            package_pattern = r'package\s+([\w\.]+);'
            match = re.search(package_pattern, content)
            if match:
                package_name = match.group(1)
                return f"{package_name}.{class_name}"
            else:
                return class_name
                
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"전체 클래스명 추출 실패: {class_name}")
    
    def _get_full_class_name_from_content(self, class_name: str, content: str) -> str:
        """컨텐츠에서 클래스의 전체 이름 추출"""
        return self._get_full_class_name(class_name, content)
    
    def _extract_method_parameters(self, method_node) -> List[str]:
        """메서드 파라미터 추출"""
        try:
            parameters = []
            if hasattr(method_node, 'parameters') and method_node.parameters:
                for param in method_node.parameters:
                    param_type = param.type.name if hasattr(param.type, 'name') else 'Object'
                    parameters.append(f"{param_type} {param.name}")
            return parameters
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"메서드 파라미터 추출 실패")


# 사용 예시
if __name__ == "__main__":
    # Servlet 분석기 테스트
    analyzer = ServletEntryAnalyzer()
    
    # 테스트용 Java 파일 내용
    test_content = '''
package com.example;

import javax.servlet.*;
import javax.servlet.http.*;
import javax.servlet.annotation.*;

@WebServlet(urlPatterns = {"/user/*", "/admin/*"})
public class UserServlet extends HttpServlet {
    
    protected void doGet(HttpServletRequest request, HttpServletResponse response) {
        // GET 처리
    }
    
    protected void doPost(HttpServletRequest request, HttpServletResponse response) {
        // POST 처리
    }
}
'''
    
    # 테스트용 FileInfo 객체
    test_file = FileInfo(
        file_id=1,
        file_path="UserServlet.java",
        file_name="UserServlet.java",
        file_type="java",
        content=test_content,
        hash_value="test_hash"
    )
    
    # 통계 수집기 (Mock)
    class MockStats:
        def log_file_result(self, **kwargs):
            print(f"Stats: {kwargs}")
    
    # 분석 실행
    results = analyzer.analyze_backend_entry(test_file, MockStats())
    
    print(f"분석 결과: {len(results)}개 진입점 발견")
    for result in results:
        print(f"  {result.http_method} {result.url_pattern} - {result.class_name}.{result.method_name}")
