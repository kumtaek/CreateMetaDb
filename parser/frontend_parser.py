"""
범용 프론트엔드 파서 모듈
- JSP, JSX, Vue, TS, JS, HTML 파일의 API 호출 패턴 분석
- 기존 JSP 파서 로직을 범용화하여 모든 프론트엔드 파일 타입 지원
- 메모리 최적화를 통한 스트리밍 처리

USER RULES:
- 하드코딩 금지: path_utils.get_parser_config_path("frontend") 사용 (크로스플랫폼 대응)
- 파싱 에러 처리: has_error='Y', error_message 저장 후 계속 진행
- 공통함수 사용: util 모듈 활용
"""

import os
import re
from typing import List, Dict, Any, Optional
from util import (
    FileUtils, PathUtils, HashUtils, ConfigUtils,
    app_logger, info, error, debug, warning, handle_error
)


class FrontendParser:
    """범용 프론트엔드 파서 - JSP, JSX, Vue, TS, JS, HTML 지원"""

    def __init__(self, config_path: str = None, project_name: str = None):
        """
        프론트엔드 파서 초기화

        Args:
            config_path: 설정 파일 경로 (None이면 공통함수 사용)
            project_name: 프로젝트명
        """
        try:
            self.project_name = project_name
            self.config = {}
            
            # USER RULES: 하드코딩 지양 - 설정 파일에서 패턴 로드
            from util import PathUtils, ConfigUtils
            self.path_utils = PathUtils()
            config_utils = ConfigUtils()
            
            if config_path is None:
                # 공통함수 사용 (크로스플랫폼 대응)
                config_path = self.path_utils.get_parser_config_path("frontend")
            
            self.config = config_utils.load_yaml_config(config_path)
            
            info(f"프론트엔드 파서 초기화 완료: {config_path}")
            
        except Exception as e:
            handle_error(e, f"프론트엔드 파서 초기화 실패: {config_path}")

    def parse_frontend_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        프론트엔드 파일 파싱 (JSP, JSX, Vue, TS, JS, HTML)

        Args:
            file_path: 파일 경로
            file_type: 파일 타입 ('JSP', 'JSX', 'VUE', 'TS', 'JS', 'HTML')

        Returns:
            Dict[str, Any]: 파싱 결과
        """
        try:
            debug(f"프론트엔드 파일 파싱 시작: {file_path} (타입: {file_type})")
            
            # 파일 내용 읽기
            file_content = FileUtils.read_file(file_path)
            if not file_content:
                warning(f"파일 내용을 읽을 수 없음: {file_path}")
                return {
                    'file_name': os.path.basename(file_path),
                    'file_type': file_type,
                    'api_calls': [],
                    'components': [],
                    'relationships': [],
                    'has_error': 'Y',
                    'error_message': '파일 내용을 읽을 수 없음'
                }
            
            # 파일 타입별 파싱 로직 적용
            if file_type.upper() == 'JSP':
                return self._parse_jsp_file(file_path, file_content)
            elif file_type.upper() in ['JSX', 'VUE', 'TS', 'JS']:
                return self._parse_javascript_file(file_path, file_content, file_type)
            elif file_type.upper() == 'HTML':
                return self._parse_html_file(file_path, file_content)
            else:
                warning(f"지원하지 않는 파일 타입: {file_type}")
                return {
                    'file_name': os.path.basename(file_path),
                    'file_type': file_type,
                    'api_calls': [],
                    'components': [],
                    'relationships': [],
                    'has_error': 'Y',
                    'error_message': f'지원하지 않는 파일 타입: {file_type}'
                }
                
        except Exception as e:
            error(f"프론트엔드 파일 파싱 실패: {file_path} - {str(e)}")
            return {
                'file_name': os.path.basename(file_path),
                'file_type': file_type,
                'api_calls': [],
                'components': [],
                'relationships': [],
                'has_error': 'Y',
                'error_message': str(e)
            }

    def _parse_jsp_file(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """JSP 파일 파싱 (기존 JSP 파서 로직 재사용)"""
        try:
            # 기존 JSP 파서 인스턴스 생성
            from parser.jsp_parser import JspParser
            jsp_parser = JspParser(project_name=self.project_name)
            
            # JSP 파서로 분석 (parse_jsp_file 메서드 사용)
            parse_result = jsp_parser.parse_jsp_file(file_path)
            
            # 결과에서 필요한 정보 추출
            jsp_component = parse_result.get('jsp_component', {})
            # JSP 컴포넌트 구조를 FrontendParser 형식으로 변환
            if jsp_component:
                # jsp_name을 component_name으로 매핑
                jsp_component['component_name'] = jsp_component.get('jsp_name', os.path.basename(file_path))
                jsp_component['component_type'] = 'JSP'
            jsp_components = [jsp_component] if jsp_component else []
            api_calls = parse_result.get('api_calls', [])
            
            # API 호출에서 jsp_name을 file_name으로 매핑
            for api_call in api_calls:
                if 'jsp_name' in api_call:
                    api_call['file_name'] = api_call['jsp_name']
            
            return {
                'file_name': os.path.basename(file_path),
                'file_type': 'JSP',
                'components': jsp_components,
                'api_calls': api_calls,
                'relationships': [],
                'has_error': 'N',
                'error_message': None
            }
            
        except Exception as e:
            handle_error(e, f"JSP 파일 파싱 실패: {file_path}")

    def _parse_javascript_file(self, file_path: str, file_content: str, file_type: str) -> Dict[str, Any]:
        """JavaScript 계열 파일 파싱 (JSX, Vue, TS, JS)"""
        try:
            debug(f"JavaScript 파일 파싱: {file_path} (타입: {file_type})")
            
            # API 호출 추출
            api_calls = self._extract_api_calls_from_javascript(file_content, os.path.basename(file_path), file_type)
            
            # 컴포넌트 추출 (파일 타입별)
            components = self._extract_components_from_javascript(file_content, os.path.basename(file_path), file_type)
            
            return {
                'file_name': os.path.basename(file_path),
                'file_type': file_type.upper(),
                'components': components,
                'api_calls': api_calls,
                'relationships': [],
                'has_error': 'N',
                'error_message': None
            }
            
        except Exception as e:
            handle_error(e, f"JavaScript 파일 파싱 실패: {file_path}")

    def _parse_html_file(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """HTML 파일 파싱"""
        try:
            debug(f"HTML 파일 파싱: {file_path}")
            
            # API 호출 추출 (HTML 내 JavaScript)
            api_calls = self._extract_api_calls_from_html(file_content, os.path.basename(file_path))
            
            # HTML 컴포넌트 추출
            components = self._extract_components_from_html(file_content, os.path.basename(file_path))
            
            return {
                'file_name': os.path.basename(file_path),
                'file_type': 'HTML',
                'components': components,
                'api_calls': api_calls,
                'relationships': [],
                'has_error': 'N',
                'error_message': None
            }
            
        except Exception as e:
            handle_error(e, f"HTML 파일 파싱 실패: {file_path}")

    def _extract_api_calls_from_javascript(self, content: str, file_name: str, file_type: str) -> List[Dict[str, Any]]:
        """JavaScript 계열 파일에서 API 호출 추출"""
        try:
            api_calls = []
            
            # 설정에서 API 호출 패턴 가져오기 (JSP 설정 재사용 + JavaScript 전용 패턴 추가)
            api_patterns_text = self.config.get('api_call_patterns', '')
            js_api_patterns_text = self.config.get('javascript_api_patterns', '')
            default_methods = self.config.get('default_http_methods', {})
            
            # JSP 패턴 + JavaScript 전용 패턴 결합
            all_patterns = []
            if api_patterns_text:
                all_patterns.extend([line.strip() for line in api_patterns_text.strip().split('\n') if line.strip()])
            if js_api_patterns_text:
                all_patterns.extend([line.strip() for line in js_api_patterns_text.strip().split('\n') if line.strip()])
            
            if not all_patterns:
                debug("API 호출 패턴이 설정되지 않음")
                return api_calls
            
            # 전체 내용에 대해 API 호출 패턴 분석
            for pattern in all_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    try:
                        # 매칭된 위치의 라인 번호 계산
                        line_num = content[:match.start()].count('\n') + 1
                        line_start = content.rfind('\n', 0, match.start()) + 1
                        line_end = content.find('\n', match.end())
                        if line_end == -1:
                            line_end = len(content)
                        line = content[line_start:line_end]
                        
                        # API 호출 정보 추출
                        api_call = self._extract_api_call_info(match, line, line_num, file_name, default_methods)
                        if api_call:
                            api_calls.append(api_call)
                            
                    except Exception as e:
                        debug(f"API 호출 정보 추출 실패: {str(e)}")
                        continue
            
            debug(f"JavaScript 파일에서 {len(api_calls)}개 API 호출 발견: {file_name}")
            return api_calls
            
        except Exception as e:
            handle_error(e, "JavaScript API 호출 추출 실패")

    def _extract_api_calls_from_html(self, content: str, file_name: str) -> List[Dict[str, Any]]:
        """HTML 파일에서 API 호출 추출 (script 태그 내 JavaScript)"""
        try:
            api_calls = []
            
            # script 태그 내 JavaScript 코드 추출
            script_pattern = r'<script[^>]*>(.*?)</script>'
            script_matches = re.finditer(script_pattern, content, re.IGNORECASE | re.DOTALL)
            
            for script_match in script_matches:
                script_content = script_match.group(1)
                if script_content.strip():
                    # JavaScript 코드에서 API 호출 추출
                    js_api_calls = self._extract_api_calls_from_javascript(script_content, file_name, 'JS')
                    api_calls.extend(js_api_calls)
            
            debug(f"HTML 파일에서 {len(api_calls)}개 API 호출 발견: {file_name}")
            return api_calls
            
        except Exception as e:
            handle_error(e, "HTML API 호출 추출 실패")

    def _extract_api_call_info(self, match, line: str, line_num: int, file_name: str, default_methods: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """API 호출 정보 추출 (JSP 파서 로직 재사용)"""
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
                'file_name': file_name,
                'api_url': api_url,
                'http_method': http_method,
                'line_number': line_num,
                'source_line': line.strip(),
                'component_name': f"{api_url}:{http_method}"
            }
            
            return api_call
            
        except Exception as e:
            debug(f"API 호출 정보 추출 실패: {str(e)}")
            return None

    def _extract_http_method(self, match, line: str, groups: tuple, default_methods: Dict[str, str]) -> str:
        """HTTP 메서드 추출 (JSP 파서 로직 재사용)"""
        try:
            # 두 번째 그룹이 있으면 HTTP 메서드로 사용
            if len(groups) > 1 and groups[1]:
                return groups[1].strip().upper()
            
            # 라인에서 HTTP 메서드 패턴 찾기
            method_patterns = [
                r'type\s*:\s*["\']([^"\']+)["\']',
                r'method\s*:\s*["\']([^"\']+)["\']',
                r'\.(get|post|put|delete)\s*\(',
                r'method\s*:\s*["\']([^"\']+)["\']'  # fetch 옵션
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
            debug(f"HTTP 메서드 추출 실패: {str(e)}")
            return 'GET'

    def _extract_components_from_javascript(self, content: str, file_name: str, file_type: str) -> List[Dict[str, Any]]:
        """JavaScript 계열 파일에서 컴포넌트 추출"""
        try:
            components = []
            
            # 파일 타입별 컴포넌트 추출 로직
            if file_type.upper() == 'JSX':
                components = self._extract_jsx_components(content, file_name)
            elif file_type.upper() == 'VUE':
                components = self._extract_vue_components(content, file_name)
            elif file_type.upper() in ['TS', 'JS']:
                components = self._extract_js_components(content, file_name)
            
            return components
            
        except Exception as e:
            handle_error(e, f"{file_type} 컴포넌트 추출 실패")

    def _extract_components_from_html(self, content: str, file_name: str) -> List[Dict[str, Any]]:
        """HTML 파일에서 컴포넌트 추출"""
        try:
            components = []
            
            # HTML 파일 자체를 하나의 컴포넌트로 처리
            component = {
                'component_name': file_name,
                'component_type': 'HTML',
                'line_start': 1,
                'line_end': content.count('\n') + 1,
                'hash_value': HashUtils.generate_content_hash(content)
            }
            components.append(component)
            
            return components
            
        except Exception as e:
            handle_error(e, "HTML 컴포넌트 추출 실패")

    def _extract_jsx_components(self, content: str, file_name: str) -> List[Dict[str, Any]]:
        """JSX 파일에서 컴포넌트 추출"""
        try:
            components = []
            
            # React 컴포넌트 패턴 찾기
            component_patterns = [
                r'function\s+(\w+)\s*\(',  # function ComponentName(
                r'const\s+(\w+)\s*=\s*\(',  # const ComponentName = (
                r'class\s+(\w+)\s+extends',  # class ComponentName extends
                r'export\s+default\s+function\s+(\w+)',  # export default function ComponentName
                r'export\s+default\s+(\w+)'  # export default ComponentName
            ]
            
            for pattern in component_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    component_name = match.group(1)
                    line_num = content[:match.start()].count('\n') + 1
                    
                    component = {
                        'component_name': component_name,
                        'component_type': 'JSX',
                        'line_start': line_num,
                        'line_end': line_num,
                        'hash_value': HashUtils.generate_content_hash(component_name)
                    }
                    components.append(component)
            
            return components
            
        except Exception as e:
            handle_error(e, "JSX 컴포넌트 추출 실패")

    def _extract_vue_components(self, content: str, file_name: str) -> List[Dict[str, Any]]:
        """Vue 파일에서 컴포넌트 추출"""
        try:
            components = []
            
            # Vue 컴포넌트 패턴 찾기
            component_patterns = [
                r'<template[^>]*>',  # <template> 태그
                r'<script[^>]*>',   # <script> 태그
                r'<style[^>]*>'     # <style> 태그
            ]
            
            for pattern in component_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    tag_name = match.group(0).split()[0][1:-1]  # 태그명 추출
                    line_num = content[:match.start()].count('\n') + 1
                    
                    component = {
                        'component_name': f"{file_name}_{tag_name}",
                        'component_type': 'VUE',
                        'line_start': line_num,
                        'line_end': line_num,
                        'hash_value': HashUtils.generate_content_hash(tag_name)
                    }
                    components.append(component)
            
            return components
            
        except Exception as e:
            handle_error(e, "Vue 컴포넌트 추출 실패")

    def _extract_js_components(self, content: str, file_name: str) -> List[Dict[str, Any]]:
        """JavaScript 파일에서 컴포넌트 추출"""
        try:
            components = []
            
            # JavaScript 함수/클래스 패턴 찾기
            component_patterns = [
                r'function\s+(\w+)\s*\(',  # function functionName(
                r'class\s+(\w+)',          # class ClassName
                r'const\s+(\w+)\s*=\s*function',  # const functionName = function
                r'export\s+default\s+function\s+(\w+)'  # export default function
            ]
            
            for pattern in component_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    component_name = match.group(1)
                    line_num = content[:match.start()].count('\n') + 1
                    
                    component = {
                        'component_name': component_name,
                        'component_type': 'JS',
                        'line_start': line_num,
                        'line_end': line_num,
                        'hash_value': HashUtils.generate_content_hash(component_name)
                    }
                    components.append(component)
            
            return components
            
        except Exception as e:
            handle_error(e, "JavaScript 컴포넌트 추출 실패")
