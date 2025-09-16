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
        JSP 파일에서 컴포넌트 정보 추출 및 관계 분석

        Args:
            jsp_file: JSP 파일 경로

        Returns:
            Dict[str, Any]: JSP 컴포넌트 정보와 모든 관계 정보
        """
        try:
            # JSP 파일 읽기
            file_utils = FileUtils()
            jsp_content = file_utils.read_file(jsp_file)

            if not jsp_content:
                return {
                    'jsp_component': None,
                    'java_method_relationships': [],
                    'jsp_relationships': [],
                    'advanced_relationships': {},
                    'file_path': jsp_file,
                    'has_error': 'Y',
                    'error_message': 'JSP 파일 읽기 실패'
                }

            # JSP 컴포넌트 정보 추출
            jsp_component = self._extract_jsp_component_info(jsp_content, jsp_file)

            # Phase 1: Java 메서드 호출 분석 (스크립틀릿, 표현식)
            java_method_relationships = self._analyze_java_method_calls(jsp_content, jsp_component['jsp_name'])

            # Phase 2: JSP 간 관계 분석
            jsp_relationships = self._analyze_jsp_relationships(jsp_content, jsp_component['jsp_name'])

            # Phase 3: 고도화 관계 분석 (EL, JSTL, Java Bean, 태그 라이브러리)
            advanced_relationships = self._analyze_advanced_relationships(jsp_content, jsp_component['jsp_name'])

            return {
                'jsp_component': jsp_component,
                'java_method_relationships': java_method_relationships,
                'jsp_relationships': jsp_relationships,
                'advanced_relationships': advanced_relationships,
                'file_path': jsp_file,
                'has_error': 'N',
                'error_message': None
            }

        except Exception as e:
            # USER RULES: 파싱 에러는 has_error='Y', error_message 남기고 계속 진행
            return {
                'jsp_component': None,
                'java_method_relationships': [],
                'jsp_relationships': [],
                'advanced_relationships': {},
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
            handle_error(e, f"메서드 호출 파싱 실패: {jsp_name}")

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

    # Phase 2: JSP 간 관계 분석 메서드들
    def _analyze_jsp_relationships(self, jsp_content: str, jsp_name: str) -> List[Dict[str, Any]]:
        """
        JSP 파일에서 다른 JSP와의 관계 분석 (Phase 2)

        Args:
            jsp_content: JSP 파일 내용
            jsp_name: JSP 파일명

        Returns:
            List[Dict[str, Any]]: JSP 관계 정보
        """
        try:
            jsp_relationships = []

            # 1. <%@ include %> 디렉티브 분석
            include_relationships = self._analyze_include_directives(jsp_content, jsp_name)
            jsp_relationships.extend(include_relationships)

            # 2. <jsp:include>, <jsp:forward> 액션 분석
            action_relationships = self._analyze_jsp_actions(jsp_content, jsp_name)
            jsp_relationships.extend(action_relationships)

            # 중복 제거
            jsp_relationships = self._remove_duplicate_jsp_relationships(jsp_relationships)

            info(f"JSP {jsp_name}에서 {len(jsp_relationships)}개 JSP 관계 발견")
            return jsp_relationships

        except Exception as e:
            handle_error(e, f"JSP 관계 분석 실패: {jsp_name}")

    def _analyze_include_directives(self, jsp_content: str, jsp_name: str) -> List[Dict[str, Any]]:
        """
        <%@ include %> 디렉티브 분석

        Args:
            jsp_content: JSP 파일 내용
            jsp_name: JSP 파일명

        Returns:
            List[Dict[str, Any]]: include 디렉티브 관계 정보
        """
        try:
            relationships = []

            # include 디렉티브 패턴 (설정 파일에서 로드)
            include_patterns = self.config.get('jsp_include_patterns', [])

            # 기본 패턴
            if not include_patterns:
                include_patterns = [
                    r'<%@\s*include\s+file\s*=\s*["\']([^"\']+)["\']',
                    r'<%@include\s+file\s*=\s*["\']([^"\']+)["\']'
                ]

            for pattern in include_patterns:
                matches = re.finditer(pattern, jsp_content, re.IGNORECASE | re.DOTALL)

                for match in matches:
                    included_file = match.group(1)
                    line_number = jsp_content[:match.start()].count('\n') + 1

                    # 경로 정규화
                    included_file = self._normalize_jsp_path(included_file)

                    relationship = {
                        'src_jsp': jsp_name,
                        'dst_jsp': included_file,
                        'relationship_type': 'INCLUDE_DIRECTIVE',
                        'line_number': line_number
                    }
                    relationships.append(relationship)

            return relationships

        except Exception as e:
            handle_error(e, f"include 디렉티브 분석 실패: {jsp_name}")

    def _analyze_jsp_actions(self, jsp_content: str, jsp_name: str) -> List[Dict[str, Any]]:
        """
        <jsp:include>, <jsp:forward> 액션 분석

        Args:
            jsp_content: JSP 파일 내용
            jsp_name: JSP 파일명

        Returns:
            List[Dict[str, Any]]: JSP 액션 관계 정보
        """
        try:
            relationships = []

            # JSP 액션 패턴 (설정 파일에서 로드)
            action_patterns = self.config.get('jsp_action_patterns', {})

            # 기본 패턴
            if not action_patterns:
                action_patterns = {
                    'include': r'<jsp:include\s+page\s*=\s*["\']([^"\']+)["\']',
                    'forward': r'<jsp:forward\s+page\s*=\s*["\']([^"\']+)["\']'
                }

            for action_type, pattern in action_patterns.items():
                matches = re.finditer(pattern, jsp_content, re.IGNORECASE | re.DOTALL)

                for match in matches:
                    target_page = match.group(1)
                    line_number = jsp_content[:match.start()].count('\n') + 1

                    # 경로 정규화
                    target_page = self._normalize_jsp_path(target_page)

                    relationship = {
                        'src_jsp': jsp_name,
                        'dst_jsp': target_page,
                        'relationship_type': f'JSP_{action_type.upper()}',
                        'line_number': line_number
                    }
                    relationships.append(relationship)

            return relationships

        except Exception as e:
            handle_error(e, f"JSP 액션 분석 실패: {jsp_name}")

    def _normalize_jsp_path(self, jsp_path: str) -> str:
        """
        JSP 파일 경로 정규화

        Args:
            jsp_path: JSP 파일 경로

        Returns:
            str: 정규화된 JSP 파일 경로
        """
        try:
            # 절대 경로를 상대 경로로 변환
            if jsp_path.startswith('/'):
                jsp_path = jsp_path[1:]

            # 역슬래시를 슬래시로 변환
            jsp_path = jsp_path.replace('\\', '/')

            # JSP 확장자가 없으면 추가
            if not jsp_path.lower().endswith('.jsp'):
                jsp_path = jsp_path + '.jsp'

            return jsp_path

        except Exception as e:
            handle_error(e, f"JSP 경로 정규화 실패: {jsp_path}")

    def _remove_duplicate_jsp_relationships(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        중복 JSP 관계 제거

        Args:
            relationships: JSP 관계 리스트

        Returns:
            List[Dict[str, Any]]: 중복 제거된 JSP 관계 리스트
        """
        try:
            seen = set()
            unique_relationships = []

            for rel in relationships:
                # 중복 확인 키 생성
                key = (rel['src_jsp'], rel['dst_jsp'], rel['relationship_type'])

                if key not in seen:
                    seen.add(key)
                    unique_relationships.append(rel)

            return unique_relationships

        except Exception as e:
            handle_error(e, "중복 JSP 관계 제거 실패")

    def generate_jsp_dependency_graph(self, jsp_files: List[str]) -> Dict[str, Any]:
        """
        JSP 의존성 그래프 생성

        Args:
            jsp_files: JSP 파일 경로 리스트

        Returns:
            Dict[str, Any]: JSP 의존성 그래프 정보
        """
        try:
            # JSP 의존성 그래프 구조
            dependency_graph = {
                'nodes': {},  # JSP 파일 노드
                'edges': [],  # JSP 간 의존성 관계
                'circular_dependencies': [],  # 순환 의존성
                'isolated_nodes': [],  # 독립 노드 (의존성 없음)
                'entry_points': [],  # 진입점 (다른 JSP에서 참조되지 않음)
                'leaf_nodes': []  # 리프 노드 (다른 JSP를 참조하지 않음)
            }

            # 1. 모든 JSP 파일 분석하여 노드와 엣지 구성
            all_relationships = []
            for jsp_file in jsp_files:
                result = self.parse_jsp_file(jsp_file)

                if result['has_error'] == 'N' and result['jsp_relationships']:
                    jsp_name = result['jsp_component']['jsp_name']

                    # 노드 추가
                    dependency_graph['nodes'][jsp_name] = {
                        'file_path': jsp_file,
                        'outgoing_dependencies': [],
                        'incoming_dependencies': []
                    }

                    # 관계 수집
                    all_relationships.extend(result['jsp_relationships'])

            # 2. 엣지 구성 및 의존성 연결
            for rel in all_relationships:
                src_jsp = rel['src_jsp']
                dst_jsp = rel['dst_jsp']
                rel_type = rel['relationship_type']

                edge = {
                    'source': src_jsp,
                    'target': dst_jsp,
                    'type': rel_type,
                    'line_number': rel.get('line_number', 0)
                }
                dependency_graph['edges'].append(edge)

                # 노드별 의존성 관계 업데이트
                if src_jsp in dependency_graph['nodes']:
                    if dst_jsp not in dependency_graph['nodes'][src_jsp]['outgoing_dependencies']:
                        dependency_graph['nodes'][src_jsp]['outgoing_dependencies'].append(dst_jsp)

                if dst_jsp not in dependency_graph['nodes']:
                    # 참조되는 JSP가 분석 대상에 없는 경우 노드 생성
                    dependency_graph['nodes'][dst_jsp] = {
                        'file_path': None,  # 외부 파일
                        'outgoing_dependencies': [],
                        'incoming_dependencies': []
                    }

                if src_jsp not in dependency_graph['nodes'][dst_jsp]['incoming_dependencies']:
                    dependency_graph['nodes'][dst_jsp]['incoming_dependencies'].append(src_jsp)

            # 3. 순환 의존성 탐지
            dependency_graph['circular_dependencies'] = self._detect_circular_dependencies(dependency_graph['nodes'])

            # 4. 특별한 노드들 식별
            dependency_graph['isolated_nodes'] = self._find_isolated_nodes(dependency_graph['nodes'])
            dependency_graph['entry_points'] = self._find_entry_points(dependency_graph['nodes'])
            dependency_graph['leaf_nodes'] = self._find_leaf_nodes(dependency_graph['nodes'])

            info(f"JSP 의존성 그래프 생성 완료: 노드 {len(dependency_graph['nodes'])}개, 엣지 {len(dependency_graph['edges'])}개")

            if dependency_graph['circular_dependencies']:
                warning(f"순환 의존성 발견: {len(dependency_graph['circular_dependencies'])}개")

            return dependency_graph

        except Exception as e:
            handle_error(e, "JSP 의존성 그래프 생성 실패")

    def _detect_circular_dependencies(self, nodes: Dict[str, Dict]) -> List[List[str]]:
        """
        순환 의존성 탐지

        Args:
            nodes: JSP 노드 딕셔너리

        Returns:
            List[List[str]]: 순환 의존성 경로 리스트
        """
        try:
            circular_deps = []
            visited = set()
            rec_stack = set()

            def dfs_detect_cycle(node: str, path: List[str]) -> bool:
                if node in rec_stack:
                    # 순환 의존성 발견
                    cycle_start = path.index(node)
                    cycle = path[cycle_start:] + [node]
                    circular_deps.append(cycle)
                    return True

                if node in visited:
                    return False

                visited.add(node)
                rec_stack.add(node)

                if node in nodes:
                    for dependency in nodes[node]['outgoing_dependencies']:
                        if dfs_detect_cycle(dependency, path + [node]):
                            return True

                rec_stack.remove(node)
                return False

            for node in nodes:
                if node not in visited:
                    dfs_detect_cycle(node, [])

            return circular_deps

        except Exception as e:
            handle_error(e, "순환 의존성 탐지 실패")

    def _find_isolated_nodes(self, nodes: Dict[str, Dict]) -> List[str]:
        """
        독립 노드 찾기 (의존성이 없는 JSP)

        Args:
            nodes: JSP 노드 딕셔너리

        Returns:
            List[str]: 독립 노드 리스트
        """
        try:
            isolated = []
            for node_name, node_data in nodes.items():
                if (not node_data['outgoing_dependencies'] and
                    not node_data['incoming_dependencies']):
                    isolated.append(node_name)
            return isolated

        except Exception as e:
            handle_error(e, "독립 노드 탐지 실패")

    def _find_entry_points(self, nodes: Dict[str, Dict]) -> List[str]:
        """
        진입점 찾기 (다른 JSP에서 참조되지 않는 JSP)

        Args:
            nodes: JSP 노드 딕셔너리

        Returns:
            List[str]: 진입점 리스트
        """
        try:
            entry_points = []
            for node_name, node_data in nodes.items():
                if (not node_data['incoming_dependencies'] and
                    node_data['outgoing_dependencies']):
                    entry_points.append(node_name)
            return entry_points

        except Exception as e:
            handle_error(e, "진입점 탐지 실패")

    def _find_leaf_nodes(self, nodes: Dict[str, Dict]) -> List[str]:
        """
        리프 노드 찾기 (다른 JSP를 참조하지 않는 JSP)

        Args:
            nodes: JSP 노드 딕셔너리

        Returns:
            List[str]: 리프 노드 리스트
        """
        try:
            leaf_nodes = []
            for node_name, node_data in nodes.items():
                if (not node_data['outgoing_dependencies'] and
                    node_data['incoming_dependencies']):
                    leaf_nodes.append(node_name)
            return leaf_nodes

        except Exception as e:
            handle_error(e, "리프 노드 탐지 실패")

    # Phase 3: 고도화 관계 분석 메서드들
    def _analyze_advanced_relationships(self, jsp_content: str, jsp_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        고도화 관계 분석 (EL, JSTL, Java Bean, 태그 라이브러리)

        Args:
            jsp_content: JSP 파일 내용
            jsp_name: JSP 파일명

        Returns:
            Dict[str, List[Dict[str, Any]]]: 고도화 관계 정보
        """
        try:
            advanced_relationships = {
                'el_expressions': [],  # EL 표현식 관계
                'jstl_tags': [],  # JSTL 태그 관계
                'java_beans': [],  # Java Bean 관계
                'tag_libraries': []  # 태그 라이브러리 관계
            }

            # 1. EL 표현식 분석
            el_relationships = self._analyze_el_expressions(jsp_content, jsp_name)
            advanced_relationships['el_expressions'] = el_relationships

            # 2. JSTL 태그 분석
            jstl_relationships = self._analyze_jstl_tags(jsp_content, jsp_name)
            advanced_relationships['jstl_tags'] = jstl_relationships

            # 3. Java Bean 관계 분석
            bean_relationships = self._analyze_java_beans(jsp_content, jsp_name)
            advanced_relationships['java_beans'] = bean_relationships

            # 4. 태그 라이브러리 관계 분석
            taglib_relationships = self._analyze_tag_libraries(jsp_content, jsp_name)
            advanced_relationships['tag_libraries'] = taglib_relationships

            total_relations = sum(len(v) for v in advanced_relationships.values())
            info(f"JSP {jsp_name}에서 {total_relations}개 고도화 관계 발견")

            return advanced_relationships

        except Exception as e:
            handle_error(e, f"고도화 관계 분석 실패: {jsp_name}")

    def _analyze_el_expressions(self, jsp_content: str, jsp_name: str) -> List[Dict[str, Any]]:
        """
        EL 표현식 (${...}) 분석

        Args:
            jsp_content: JSP 파일 내용
            jsp_name: JSP 파일명

        Returns:
            List[Dict[str, Any]]: EL 표현식 관계 정보
        """
        try:
            el_relationships = []

            # EL 표현식 패턴 (설정 파일에서 로드)
            el_patterns = self.config.get('jsp_el_patterns', [])

            # 기본 패턴
            if not el_patterns:
                el_patterns = [
                    r'\$\{([^}]+)\}',  # ${...}
                    r'#\{([^}]+)\}'    # #{...}
                ]

            for pattern in el_patterns:
                matches = re.finditer(pattern, jsp_content, re.IGNORECASE | re.DOTALL)

                for match in matches:
                    el_expression = match.group(1).strip()
                    line_number = jsp_content[:match.start()].count('\n') + 1

                    # EL 표현식에서 Bean 속성 및 메서드 추출
                    bean_relations = self._parse_el_expression(el_expression, jsp_name, line_number)
                    el_relationships.extend(bean_relations)

            return el_relationships

        except Exception as e:
            handle_error(e, f"EL 표현식 분석 실패: {jsp_name}")

    def _parse_el_expression(self, el_expression: str, jsp_name: str, line_number: int) -> List[Dict[str, Any]]:
        """
        EL 표현식 파싱하여 Bean 관계 추출

        Args:
            el_expression: EL 표현식 내용
            jsp_name: JSP 파일명
            line_number: 라인 번호

        Returns:
            List[Dict[str, Any]]: EL 관계 정보
        """
        try:
            relationships = []

            # Bean 속성 접근 패턴
            bean_property_patterns = [
                r'(\w+)\.(\w+)',  # bean.property
                r'(\w+)\[\'([^\']+)\'\]',  # bean['property']
                r'(\w+)\["([^"]+)"\]'  # bean["property"]
            ]

            # 메서드 호출 패턴
            method_call_patterns = [
                r'(\w+)\.(\w+)\s*\(',  # bean.method()
            ]

            for pattern in bean_property_patterns:
                matches = re.finditer(pattern, el_expression, re.IGNORECASE)

                for match in matches:
                    bean_name = match.group(1)
                    property_name = match.group(2)

                    relationship = {
                        'jsp_name': jsp_name,
                        'bean_name': bean_name,
                        'property_or_method': property_name,
                        'access_type': 'PROPERTY',
                        'el_expression': el_expression,
                        'line_number': line_number
                    }
                    relationships.append(relationship)

            for pattern in method_call_patterns:
                matches = re.finditer(pattern, el_expression, re.IGNORECASE)

                for match in matches:
                    bean_name = match.group(1)
                    method_name = match.group(2)

                    relationship = {
                        'jsp_name': jsp_name,
                        'bean_name': bean_name,
                        'property_or_method': method_name,
                        'access_type': 'METHOD',
                        'el_expression': el_expression,
                        'line_number': line_number
                    }
                    relationships.append(relationship)

            return relationships

        except Exception as e:
            handle_error(e, f"EL 표현식 파싱 실패: {el_expression}")

    def _analyze_jstl_tags(self, jsp_content: str, jsp_name: str) -> List[Dict[str, Any]]:
        """
        JSTL 태그 분석

        Args:
            jsp_content: JSP 파일 내용
            jsp_name: JSP 파일명

        Returns:
            List[Dict[str, Any]]: JSTL 태그 관계 정보
        """
        try:
            jstl_relationships = []

            # JSTL 태그 패턴 (설정 파일에서 로드)
            jstl_patterns = self.config.get('jsp_jstl_patterns', {})

            # 기본 패턴
            if not jstl_patterns:
                jstl_patterns = {
                    'forEach': r'<c:forEach\s+([^>]+)>',
                    'if': r'<c:if\s+([^>]+)>',
                    'choose': r'<c:choose\s*>',
                    'when': r'<c:when\s+([^>]+)>',
                    'otherwise': r'<c:otherwise\s*>',
                    'set': r'<c:set\s+([^>]+)>',
                    'out': r'<c:out\s+([^>]+)>'
                }

            for tag_type, pattern in jstl_patterns.items():
                matches = re.finditer(pattern, jsp_content, re.IGNORECASE | re.DOTALL)

                for match in matches:
                    line_number = jsp_content[:match.start()].count('\n') + 1

                    if match.groups():
                        attributes = match.group(1)
                    else:
                        attributes = ''

                    # 태그 속성에서 Bean 관계 추출
                    bean_relations = self._parse_jstl_attributes(attributes, tag_type, jsp_name, line_number)
                    jstl_relationships.extend(bean_relations)

            return jstl_relationships

        except Exception as e:
            handle_error(e, f"JSTL 태그 분석 실패: {jsp_name}")

    def _parse_jstl_attributes(self, attributes: str, tag_type: str, jsp_name: str, line_number: int) -> List[Dict[str, Any]]:
        """
        JSTL 태그 속성에서 Bean 관계 추출

        Args:
            attributes: 태그 속성
            tag_type: 태그 타입
            jsp_name: JSP 파일명
            line_number: 라인 번호

        Returns:
            List[Dict[str, Any]]: JSTL 관계 정보
        """
        try:
            relationships = []

            # 속성에서 Bean 참조 패턴
            bean_ref_patterns = [
                r'var\s*=\s*["\']([^"\']+)["\']',  # var="beanName"
                r'items\s*=\s*["\']?\$\{([^}"\']+)\}["\']?',  # items="${beanList}"
                r'test\s*=\s*["\']?\$\{([^}"\']+)\}["\']?',  # test="${condition}"
                r'value\s*=\s*["\']?\$\{([^}"\']+)\}["\']?'  # value="${bean.property}"
            ]

            for pattern in bean_ref_patterns:
                matches = re.finditer(pattern, attributes, re.IGNORECASE)

                for match in matches:
                    bean_reference = match.group(1)

                    relationship = {
                        'jsp_name': jsp_name,
                        'jstl_tag': tag_type,
                        'bean_reference': bean_reference,
                        'attributes': attributes,
                        'line_number': line_number
                    }
                    relationships.append(relationship)

            return relationships

        except Exception as e:
            handle_error(e, f"JSTL 속성 파싱 실패: {attributes}")

    def _analyze_java_beans(self, jsp_content: str, jsp_name: str) -> List[Dict[str, Any]]:
        """
        Java Bean 관계 분석 (<jsp:useBean>)

        Args:
            jsp_content: JSP 파일 내용
            jsp_name: JSP 파일명

        Returns:
            List[Dict[str, Any]]: Java Bean 관계 정보
        """
        try:
            bean_relationships = []

            # Java Bean 패턴 (설정 파일에서 로드)
            bean_patterns = self.config.get('jsp_bean_patterns', [])

            # 기본 패턴
            if not bean_patterns:
                bean_patterns = [
                    r'<jsp:useBean\s+([^>]+)>',
                    r'<jsp:getProperty\s+([^>]+)>',
                    r'<jsp:setProperty\s+([^>]+)>'
                ]

            for pattern in bean_patterns:
                matches = re.finditer(pattern, jsp_content, re.IGNORECASE | re.DOTALL)

                for match in matches:
                    attributes = match.group(1)
                    line_number = jsp_content[:match.start()].count('\n') + 1
                    tag_name = match.group(0).split()[0][1:]  # 태그명 추출

                    # Bean 정보 추출
                    bean_info = self._parse_bean_attributes(attributes, tag_name, jsp_name, line_number)
                    if bean_info:
                        bean_relationships.append(bean_info)

            return bean_relationships

        except Exception as e:
            handle_error(e, f"Java Bean 분석 실패: {jsp_name}")

    def _parse_bean_attributes(self, attributes: str, tag_name: str, jsp_name: str, line_number: int) -> Optional[Dict[str, Any]]:
        """
        Bean 태그 속성 파싱

        Args:
            attributes: 태그 속성
            tag_name: 태그명
            jsp_name: JSP 파일명
            line_number: 라인 번호

        Returns:
            Optional[Dict[str, Any]]: Bean 관계 정보
        """
        try:
            # Bean 속성 추출
            id_match = re.search(r'id\s*=\s*["\']([^"\']+)["\']', attributes, re.IGNORECASE)
            class_match = re.search(r'class\s*=\s*["\']([^"\']+)["\']', attributes, re.IGNORECASE)
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', attributes, re.IGNORECASE)
            property_match = re.search(r'property\s*=\s*["\']([^"\']+)["\']', attributes, re.IGNORECASE)

            bean_id = id_match.group(1) if id_match else None
            bean_class = class_match.group(1) if class_match else None
            bean_name = name_match.group(1) if name_match else bean_id
            bean_property = property_match.group(1) if property_match else None

            if bean_name or bean_class:
                return {
                    'jsp_name': jsp_name,
                    'tag_type': tag_name,
                    'bean_id': bean_id,
                    'bean_name': bean_name,
                    'bean_class': bean_class,
                    'bean_property': bean_property,
                    'line_number': line_number
                }

            return None

        except Exception as e:
            handle_error(e, f"Bean 속성 파싱 실패: {attributes}")

    def _analyze_tag_libraries(self, jsp_content: str, jsp_name: str) -> List[Dict[str, Any]]:
        """
        태그 라이브러리 관계 분석 (<%@ taglib %>)

        Args:
            jsp_content: JSP 파일 내용
            jsp_name: JSP 파일명

        Returns:
            List[Dict[str, Any]]: 태그 라이브러리 관계 정보
        """
        try:
            taglib_relationships = []

            # 태그 라이브러리 패턴 (설정 파일에서 로드)
            taglib_patterns = self.config.get('jsp_taglib_patterns', [])

            # 기본 패턴
            if not taglib_patterns:
                taglib_patterns = [
                    r'<%@\s*taglib\s+([^>]+)>',
                    r'<%@taglib\s+([^>]+)>'
                ]

            for pattern in taglib_patterns:
                matches = re.finditer(pattern, jsp_content, re.IGNORECASE | re.DOTALL)

                for match in matches:
                    attributes = match.group(1)
                    line_number = jsp_content[:match.start()].count('\n') + 1

                    # 태그 라이브러리 정보 추출
                    taglib_info = self._parse_taglib_attributes(attributes, jsp_name, line_number)
                    if taglib_info:
                        taglib_relationships.append(taglib_info)

            return taglib_relationships

        except Exception as e:
            handle_error(e, f"태그 라이브러리 분석 실패: {jsp_name}")

    def _parse_taglib_attributes(self, attributes: str, jsp_name: str, line_number: int) -> Optional[Dict[str, Any]]:
        """
        태그 라이브러리 속성 파싱

        Args:
            attributes: 태그 라이브러리 속성
            jsp_name: JSP 파일명
            line_number: 라인 번호

        Returns:
            Optional[Dict[str, Any]]: 태그 라이브러리 관계 정보
        """
        try:
            # 태그 라이브러리 속성 추출
            uri_match = re.search(r'uri\s*=\s*["\']([^"\']+)["\']', attributes, re.IGNORECASE)
            prefix_match = re.search(r'prefix\s*=\s*["\']([^"\']+)["\']', attributes, re.IGNORECASE)
            tagdir_match = re.search(r'tagdir\s*=\s*["\']([^"\']+)["\']', attributes, re.IGNORECASE)

            uri = uri_match.group(1) if uri_match else None
            prefix = prefix_match.group(1) if prefix_match else None
            tagdir = tagdir_match.group(1) if tagdir_match else None

            if uri or tagdir:
                return {
                    'jsp_name': jsp_name,
                    'taglib_uri': uri,
                    'taglib_prefix': prefix,
                    'taglib_dir': tagdir,
                    'line_number': line_number
                }

            return None

        except Exception as e:
            handle_error(e, f"태그 라이브러리 속성 파싱 실패: {attributes}")

    def analyze_api_calls(self, jsp_content: str, jsp_name: str) -> List[Dict[str, Any]]:
        """
        JSP 파일에서 API 호출 패턴 분석

        Args:
            jsp_content: JSP 파일 내용
            jsp_name: JSP 파일명

        Returns:
            List[Dict[str, Any]]: API 호출 정보 리스트
        """
        try:
            api_calls = []
            
            # 설정에서 API 호출 패턴 가져오기
            api_patterns_text = self.config.get('api_call_patterns', '')
            default_methods = self.config.get('default_http_methods', {})
            
            if not api_patterns_text:
                debug("API 호출 패턴이 설정되지 않음")
                return api_calls
            
            # 리터럴 블록을 리스트로 변환
            api_patterns = [line.strip() for line in api_patterns_text.strip().split('\n') if line.strip()]
            
            # 각 라인별로 API 호출 패턴 분석
            lines = jsp_content.split('\n')
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                # 각 패턴에 대해 매칭 시도
                for pattern in api_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        try:
                            api_call = self._extract_api_call_info(match, line, line_num, jsp_name, default_methods)
                            if api_call:
                                api_calls.append(api_call)
                        except Exception as e:
                            handle_error(e, f"API 호출 정보 추출 실패 (라인 {line_num})")
            
            debug(f"JSP API 호출 분석 완료: {jsp_name}, {len(api_calls)}개 발견")
            return api_calls
            
        except Exception as e:
            handle_error(e, f"JSP API 호출 분석 실패: {jsp_name}")

    def _extract_api_call_info(self, match, line: str, line_num: int, jsp_name: str, default_methods: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        매칭된 API 호출에서 정보 추출

        Args:
            match: 정규식 매칭 결과
            line: 분석 중인 라인
            line_num: 라인 번호
            jsp_name: JSP 파일명
            default_methods: 기본 HTTP 메서드 매핑

        Returns:
            Optional[Dict[str, Any]]: API 호출 정보
        """
        try:
            groups = match.groups()
            if not groups:
                return None
            
            # URL 추출 (첫 번째 그룹)
            api_url = groups[0].strip()
            if not api_url:
                return None
            
            # HTTP 메서드 추출
            http_method = self._extract_http_method(match, line, groups, default_methods)
            
            # API 호출 정보 생성
            api_call = {
                'jsp_name': jsp_name,
                'api_url': api_url,
                'http_method': http_method,
                'line_number': line_num,
                'source_line': line.strip(),
                'component_name': f"{api_url}:{http_method}"
            }
            
            return api_call
            
        except Exception as e:
            handle_error(e, "API 호출 정보 추출 실패")

    def _extract_http_method(self, match, line: str, groups: tuple, default_methods: Dict[str, str]) -> str:
        """
        HTTP 메서드 추출

        Args:
            match: 정규식 매칭 결과
            line: 분석 중인 라인
            groups: 매칭 그룹
            default_methods: 기본 HTTP 메서드 매핑

        Returns:
            str: HTTP 메서드
        """
        try:
            # 두 번째 그룹이 있으면 HTTP 메서드로 사용
            if len(groups) > 1 and groups[1]:
                return groups[1].strip().upper()
            
            # 라인에서 HTTP 메서드 패턴 찾기
            method_patterns = [
                r'type\s*:\s*["\']([^"\']+)["\']',
                r'method\s*:\s*["\']([^"\']+)["\']',
                r'\.(get|post|put|delete)\s*\('
            ]
            
            for pattern in method_patterns:
                method_match = re.search(pattern, line, re.IGNORECASE)
                if method_match:
                    method = method_match.group(1) if method_match.groups() else method_match.group(0)
                    if method.startswith('.'):
                        method = method[1:].split('(')[0]
                    return method.strip().upper()
            
            # 기본값: 라인에서 메서드 타입 추론
            line_lower = line.lower()
            if '.get(' in line_lower:
                return 'GET'
            elif '.post(' in line_lower:
                return 'POST'
            elif '.put(' in line_lower:
                return 'PUT'
            elif '.delete(' in line_lower:
                return 'DELETE'
            elif 'ajax' in line_lower:
                return default_methods.get('ajax', 'GET')
            elif 'fetch' in line_lower:
                return default_methods.get('fetch', 'GET')
            
            # 기본값
            return 'GET'
            
        except Exception as e:
            handle_error(e, "HTTP 메서드 추출 실패")