"""
JSP 파서 모듈 - 5단계 Phase 1 MVP
- JSP 파일 파싱 및 분석 로직
- 스크립틀릿, 표현식에서 Java 메서드 호출 분석
- 메모리 최적화를 통한 스트리밍 처리

USER RULES:
- 하드코딩 금지: path_utils.get_parser_config_path("jsp") 사용 (크로스플랫폼 대응)
- 파싱 에러 처리: has_error='Y', error_message 저장 후 계속 진행
- 공통함수 사용: util 모듈 활용
- 메뉴얼 기반: parser/manual/02_jsp 참고
"""

import os
import re
from typing import List, Dict, Any, Optional
from util import (
    FileUtils, PathUtils, HashUtils, ConfigUtils,
    app_logger, info, error, debug, warning, handle_error
)


class JspParser:
    """JSP 파서 - 5단계 Phase 1 MVP"""

    def __init__(self, config_path: str = None, project_name: str = None):
        """
        JSP 파서 초기화

        Args:
            config_path: 설정 파일 경로 (None이면 공통함수 사용)
            project_name: 프로젝트명
        """
        try:
            self.project_name = project_name
            self.config = {}
            
            # USER RULES: 하드코딩 지양 - 설정 파일에서 패턴 로드
            # 설정 파일 로드 (크로스플랫폼 대응)
            from util import PathUtils, ConfigUtils
            path_utils = PathUtils()
            config_utils = ConfigUtils()
            
            if config_path is None:
                # 공통함수 사용 (크로스플랫폼 대응)
                config_path = path_utils.get_parser_config_path("jsp")
            
            self.config = config_utils.load_yaml_config(config_path)
            
            info(f"JSP 파서 초기화 완료: {config_path}")
            
        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, "JSP 파서 초기화 실패")

    def get_filtered_jsp_files(self, project_path: str = None) -> List[str]:
        """
        JSP 파일 수집 및 필터링

        Args:
            project_path: 프로젝트 경로

        Returns:
            JSP 파일 경로 리스트
        """
        try:
            if not project_path:
                project_path = self.project_name
            
            # USER RULES: 공통함수 사용
            file_utils = FileUtils()
            all_files = file_utils.scan_directory(project_path)
            
            # JSP 파일 필터링
            jsp_files = []
            for file_info in all_files:
                # file_info가 dict인 경우 file_path 키에서 경로 추출
                if isinstance(file_info, dict):
                    file_path = file_info.get('file_path', '')
                else:
                    file_path = str(file_info)
                
                if file_path.lower().endswith('.jsp'):
                    jsp_files.append(file_path)
            
            info(f"JSP 파일 수집 완료: {len(jsp_files)}개")
            return jsp_files
            
        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, "JSP 파일 수집 실패")
            return []

    def parse_jsp_file(self, jsp_file: str) -> Dict[str, Any]:
        """
        JSP 파일에서 컴포넌트 정보 추출 및 Java 메서드 관계 분석

        Args:
            jsp_file: JSP 파일 경로

        Returns:
            Dict[str, Any]: JSP 컴포넌트 정보와 Java 메서드 관계 정보
        """
        try:
            # JSP 파일 읽기
            file_utils = FileUtils()
            jsp_content = file_utils.read_file(jsp_file)
            
            if not jsp_content:
                return {
                    'jsp_component': None,
                    'java_method_relationships': [],
                    'file_path': jsp_file,
                    'has_error': 'Y',
                    'error_message': 'JSP 파일 읽기 실패'
                }

            # JSP 컴포넌트 정보 추출
            jsp_component = self._extract_jsp_component_info(jsp_content, jsp_file)
            
            # Java 메서드 호출 분석 (Phase 1 MVP: 스크립틀릿, 표현식만)
            java_method_relationships = self._analyze_java_method_calls(jsp_content, jsp_component['jsp_name'])

            return {
                'jsp_component': jsp_component,
                'java_method_relationships': java_method_relationships,
                'file_path': jsp_file,
                'has_error': 'N',
                'error_message': None
            }

        except Exception as e:
            # USER RULES: 파싱 에러는 has_error='Y', error_message 남기고 계속 진행
            return {
                'jsp_component': None,
                'java_method_relationships': [],
                'file_path': jsp_file,
                'has_error': 'Y',
                'error_message': f'JSP 파일 파싱 실패: {str(e)}'
            }

    def _extract_jsp_component_info(self, jsp_content: str, file_path: str) -> Dict[str, Any]:
        """
        JSP 파일에서 JSP 컴포넌트 정보 추출

        Args:
            jsp_content: JSP 파일 내용
            file_path: JSP 파일 경로

        Returns:
            Dict[str, Any]: JSP 컴포넌트 정보
        """
        try:
            # JSP 파일명 추출
            jsp_name = os.path.basename(file_path)
            
            # 라인 수 계산
            line_count = len(jsp_content.splitlines())
            
            # 해시 값 생성 (USER RULES: 공통함수 사용)
            hash_utils = HashUtils()
            hash_value = hash_utils.generate_md5(jsp_content)

            return {
                'jsp_name': jsp_name,
                'jsp_path': file_path,
                'line_start': 1,
                'line_end': line_count,
                'hash_value': hash_value
            }

        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, f"JSP 컴포넌트 정보 추출 실패: {file_path}")

    def _analyze_java_method_calls(self, jsp_content: str, jsp_name: str) -> List[Dict[str, Any]]:
        """
        JSP 파일에서 Java 메서드 호출 분석 (Phase 1 MVP)

        Args:
            jsp_content: JSP 파일 내용
            jsp_name: JSP 파일명

        Returns:
            List[Dict[str, Any]]: Java 메서드 호출 관계 정보
        """
        try:
            method_calls = []
            
            # Phase 1 MVP: 스크립틀릿과 표현식만 분석
            # 1. 스크립틀릿 분석
            # JavaScript 함수 분석 (정답지5 기준: JSP_SCRIPTLET = JavaScript 함수명)
            scriptlet_calls = self._analyze_scriptlets(jsp_content, jsp_name)
            method_calls.extend(scriptlet_calls)
            
            # 2. 표현식 분석
            expression_calls = self._analyze_expressions(jsp_content, jsp_name)
            method_calls.extend(expression_calls)
            
            # 중복 제거
            method_calls = self._remove_duplicate_method_calls(method_calls)
            
            info(f"JSP {jsp_name}에서 {len(method_calls)}개 메서드 호출 발견")
            return method_calls

        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, f"Java 메서드 호출 분석 실패: {jsp_name}")

    def _analyze_scriptlets(self, jsp_content: str, jsp_name: str) -> List[Dict[str, Any]]:
        """
        스크립틀릿(<%...%>) 내 Java 메서드 호출 분석

        Args:
            jsp_content: JSP 파일 내용
            jsp_name: JSP 파일명

        Returns:
            List[Dict[str, Any]]: 스크립틀릿에서 추출된 Java 메서드 호출 정보
        """
        try:
            method_calls = []

            # 스크립틀릿 패턴 (USER RULES: 설정 파일에서 로드)
            scriptlet_patterns = self.config.get('jsp_scripting_patterns', [])

            # 디버깅: 패턴 확인
            debug(f"스크립틀릿 패턴: {scriptlet_patterns}")

            # 기본 패턴 (설정 파일이 없을 경우)
            if not scriptlet_patterns:
                scriptlet_patterns = [r'<%([^%]+)%>']  # <%...%>

            # 스크립틀릿만 필터링 (표현식 제외)
            scriptlet_patterns = [p for p in scriptlet_patterns if '=' not in p]

            # 디버깅: 최종 패턴 확인
            debug(f"최종 스크립틀릿 패턴: {scriptlet_patterns}")

            for pattern in scriptlet_patterns:
                matches = re.finditer(pattern, jsp_content, re.IGNORECASE | re.DOTALL)

                for match in matches:
                    # 스크립틀릿 내용 추출 (그룹 1)
                    scriptlet_content = match.group(1) if match.groups() else match.group(0)
                    line_number = jsp_content[:match.start()].count('\n') + 1

                    # 디버깅: 스크립틀릿 내용 확인
                    debug(f"스크립틀릿 내용: {scriptlet_content}")

                    # 스크립틀릿 내에서 메서드 호출 추출
                    calls = self._extract_method_calls_from_scriptlet(scriptlet_content, line_number, jsp_name)
                    method_calls.extend(calls)

            return method_calls

        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, f"스크립틀릿 분석 실패: {jsp_name}")

    def _analyze_expressions(self, jsp_content: str, jsp_name: str) -> List[Dict[str, Any]]:
        """
        표현식 분석 (<%=...%>)

        Args:
            jsp_content: JSP 파일 내용
            jsp_name: JSP 파일명

        Returns:
            List[Dict[str, Any]]: 표현식에서 추출된 메서드 호출 정보
        """
        try:
            method_calls = []
            
            # 표현식 패턴 (USER RULES: 설정 파일에서 로드)
            expression_patterns = self.config.get('jsp_scripting_patterns', [])
            
            # 표현식 패턴만 필터링 (스크립틀릿 제외)
            expression_patterns = [p for p in expression_patterns if '=' in p]
            
            # 디버깅: 패턴 확인
            debug(f"표현식 패턴: {expression_patterns}")
            
            # 기본 패턴 (설정 파일이 없을 경우)
            if not expression_patterns:
                # USER RULES: 하드코딩 지양 - 기본 패턴도 설정에서 가져오기
                expression_patterns = [r'<%=([^%]+)%>']  # <%=...%>
            
            for pattern in expression_patterns:
                matches = re.finditer(pattern, jsp_content, re.IGNORECASE | re.DOTALL)
                
                for match in matches:
                    # 표현식 내용 추출 (그룹 1)
                    expression_content = match.group(1) if match.groups() else match.group(0)
                    line_number = jsp_content[:match.start()].count('\n') + 1
                    
                    # 디버깅: 표현식 내용 확인
                    debug(f"표현식 내용: {expression_content}")
                    
                    # 표현식 내에서 메서드 호출 추출
                    calls = self._extract_method_calls_from_expression(expression_content, line_number, jsp_name)
                    method_calls.extend(calls)
            
            return method_calls

        except Exception as e:
            handle_error(e, f"표현식 분석 실패: {jsp_name}")

    def _extract_method_calls_from_scriptlet(self, scriptlet_content: str, line_number: int, jsp_name: str) -> List[Dict[str, Any]]:
        """
        스크립틀릿에서 메서드 호출 추출

        Args:
            scriptlet_content: 스크립틀릿 내용
            line_number: 라인 번호
            jsp_name: JSP 파일명

        Returns:
            List[Dict[str, Any]]: 메서드 호출 정보
        """
        try:
            method_calls = []
            
            # 메서드 호출 패턴 (USER RULES: 설정 파일에서 로드)
            method_patterns = self.config.get('java_method_call_patterns', [])
            
            # 기본 패턴 (설정 파일이 없을 경우)
            if not method_patterns:
                method_patterns = [
                    r'(\w+)\.(\w+)\s*\(',  # object.method()
                    r'(\w+)\s*\([^)]*\)'   # method()
                ]
            
            for pattern in method_patterns:
                matches = re.finditer(pattern, scriptlet_content, re.IGNORECASE)
                
                for match in matches:
                    call_info = self._parse_method_call(match, line_number, jsp_name)
                    if call_info:
                        method_calls.append(call_info)
            
            return method_calls

        except Exception as e:
            handle_error(e, f"스크립틀릿 메서드 호출 추출 실패: {jsp_name}")

    def _extract_method_calls_from_expression(self, expression_content: str, line_number: int, jsp_name: str) -> List[Dict[str, Any]]:
        """
        표현식에서 메서드 호출 추출

        Args:
            expression_content: 표현식 내용
            line_number: 라인 번호
            jsp_name: JSP 파일명

        Returns:
            List[Dict[str, Any]]: 메서드 호출 정보
        """
        try:
            method_calls = []
            
            # 메서드 호출 패턴 (USER RULES: 설정 파일에서 로드)
            method_patterns = self.config.get('java_method_call_patterns', [])
            
            # 기본 패턴 (설정 파일이 없을 경우)
            if not method_patterns:
                method_patterns = [
                    r'(\w+)\.(\w+)\s*\(',  # object.method()
                    r'(\w+)\s*\([^)]*\)'   # method()
                ]
            
            for pattern in method_patterns:
                matches = re.finditer(pattern, expression_content, re.IGNORECASE)
                
                for match in matches:
                    call_info = self._parse_method_call(match, line_number, jsp_name)
                    if call_info:
                        method_calls.append(call_info)
            
            return method_calls

        except Exception as e:
            handle_error(e, f"표현식 메서드 호출 추출 실패: {jsp_name}")

    def _parse_method_call(self, match: re.Match, line_number: int, jsp_name: str) -> Optional[Dict[str, Any]]:
        """
        메서드 호출 매치를 파싱하여 정보 추출

        Args:
            match: 정규식 매치 객체
            line_number: 라인 번호
            jsp_name: JSP 파일명

        Returns:
            Optional[Dict[str, Any]]: 메서드 호출 정보
        """
        try:
            groups = match.groups()
            
            if len(groups) == 2:
                # object.method() 패턴
                object_name = groups[0]
                method_name = groups[1]
                class_name = self._extract_class_name_from_object(object_name)
            elif len(groups) == 1:
                # method() 패턴
                method_name = groups[0]
                class_name = self._infer_class_name_from_context(method_name)
                object_name = None
            else:
                return None
            
            # Java 예약어나 기본 메서드 필터링
            if self._is_java_reserved_word(method_name) or self._is_basic_method(method_name):
                return None
            
            return {
                'jsp_name': jsp_name,
                'class_name': class_name,
                'method_name': method_name,
                'object_name': object_name,
                'line_number': line_number,
                'rel_type': 'CALL_METHOD'
            }

        except Exception as e:
            # 파싱 에러로 has_error='Y' 처리하고 계속 진행
            return None

    def _extract_class_name_from_object(self, object_name: str) -> str:
        """
        객체명에서 클래스명 추출

        Args:
            object_name: 객체명

        Returns:
            str: 추출된 클래스명
        """
        try:
            # USER RULES: 설정 파일에서 클래스 매핑 로드
            class_mapping = self.config.get('class_name_mapping', {})
            
            if object_name in class_mapping:
                return class_mapping[object_name]
            
            # 기본 규칙: 첫 글자 대문자로 변환
            return object_name.capitalize() + 'Service'

        except Exception as e:
            handle_error(e, f"클래스명 추출 실패: {object_name}")

    def _infer_class_name_from_context(self, method_name: str) -> str:
        """
        메서드명에서 클래스명 추론

        Args:
            method_name: 메서드명

        Returns:
            str: 추론된 클래스명
        """
        try:
            # USER RULES: 설정 파일에서 메서드-클래스 매핑 로드
            method_mapping = self.config.get('method_class_mapping', {})
            
            if method_name in method_mapping:
                return method_mapping[method_name]
            
            # 기본 규칙: 메서드명에서 패턴 추론
            if method_name.startswith('get') or method_name.startswith('set'):
                return 'DataService'
            elif method_name.startswith('save') or method_name.startswith('delete'):
                return 'DataService'
            else:
                return 'Service'

        except Exception as e:
            handle_error(e, f"클래스명 추론 실패: {method_name}")

    def _is_java_reserved_word(self, method_name: str) -> bool:
        """
        Java 예약어 여부 확인

        Args:
            method_name: 메서드명

        Returns:
            bool: Java 예약어 여부
        """
        java_reserved_words = {
            'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch',
            'char', 'class', 'const', 'continue', 'default', 'do', 'double',
            'else', 'enum', 'extends', 'final', 'finally', 'float', 'for',
            'goto', 'if', 'implements', 'import', 'instanceof', 'int', 'interface',
            'long', 'native', 'new', 'package', 'private', 'protected', 'public',
            'return', 'short', 'static', 'strictfp', 'super', 'switch',
            'synchronized', 'this', 'throw', 'throws', 'transient', 'try',
            'void', 'volatile', 'while', 'true', 'false', 'null'
        }
        return method_name.lower() in java_reserved_words

    def _is_basic_method(self, method_name: str) -> bool:
        """
        기본 메서드 여부 확인

        Args:
            method_name: 메서드명

        Returns:
            bool: 기본 메서드 여부
        """
        basic_methods = {
            'toString', 'equals', 'hashCode', 'clone', 'finalize',
            'getClass', 'notify', 'notifyAll', 'wait'
        }
        return method_name in basic_methods

    def _remove_duplicate_method_calls(self, method_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        중복 메서드 호출 제거

        Args:
            method_calls: 메서드 호출 리스트

        Returns:
            List[Dict[str, Any]]: 중복 제거된 메서드 호출 리스트
        """
        try:
            seen = set()
            unique_calls = []
            
            for call in method_calls:
                # 중복 확인 키 생성
                key = (call['jsp_name'], call['class_name'], call['method_name'], call['line_number'])
                
                if key not in seen:
                    seen.add(key)
                    unique_calls.append(call)
            
            return unique_calls

        except Exception as e:
            handle_error(e, "중복 메서드 호출 제거 실패")
