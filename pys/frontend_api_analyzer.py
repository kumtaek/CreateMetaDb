"""
프론트엔드 API 호출 분석기
- React/Vue/TypeScript에서 API 호출 패턴 추출
- 다양한 HTTP 클라이언트 지원 (axios, fetch, vue-resource 등)
- API URL과 HTTP 메서드 추출
"""

import re
from typing import List, Dict, Any, Set, Tuple, Optional
from util import app_logger, info, error, debug, warning, handle_error


class FrontendApiAnalyzer:
    """프론트엔드 API 호출 분석기"""

    def __init__(self):
        # 지원하는 파일 확장자
        self.supported_extensions = {'.js', '.jsx', '.ts', '.tsx', '.vue'}

        # API 호출 패턴들 (프레임워크별)
        self.api_patterns = {
            # Axios 패턴
            'axios': [
                r'axios\.get\s*\(\s*["\']([^"\']+)["\']',
                r'axios\.post\s*\(\s*["\']([^"\']+)["\']',
                r'axios\.put\s*\(\s*["\']([^"\']+)["\']',
                r'axios\.delete\s*\(\s*["\']([^"\']+)["\']',
                r'axios\.patch\s*\(\s*["\']([^"\']+)["\']',
                r'axios\s*\(\s*{\s*method:\s*["\']([^"\']+)["\'].*?url:\s*["\']([^"\']+)["\']',
                r'axios\s*\(\s*{\s*url:\s*["\']([^"\']+)["\'].*?method:\s*["\']([^"\']+)["\']'
            ],

            # Fetch API 패턴
            'fetch': [
                r'fetch\s*\(\s*["\']([^"\']+)["\']',
                r'fetch\s*\(\s*["\']([^"\']+)["\'].*?method:\s*["\']([^"\']+)["\']'
            ],

            # jQuery AJAX 패턴
            'jquery': [
                r'\$\.ajax\s*\(\s*{\s*url:\s*["\']([^"\']+)["\']',
                r'\$\.get\s*\(\s*["\']([^"\']+)["\']',
                r'\$\.post\s*\(\s*["\']([^"\']+)["\']',
                r'jQuery\.ajax\s*\(\s*{\s*url:\s*["\']([^"\']+)["\']'
            ],

            # Vue Resource 패턴
            'vue_resource': [
                r'this\.\$http\.get\s*\(\s*["\']([^"\']+)["\']',
                r'this\.\$http\.post\s*\(\s*["\']([^"\']+)["\']',
                r'this\.\$http\.put\s*\(\s*["\']([^"\']+)["\']',
                r'this\.\$http\.delete\s*\(\s*["\']([^"\']+)["\']'
            ],

            # Vue Composition API 패턴
            'vue_composition': [
                r'await\s+fetch\s*\(\s*["\']([^"\']+)["\']',
                r'await\s+axios\.get\s*\(\s*["\']([^"\']+)["\']',
                r'await\s+axios\.post\s*\(\s*["\']([^"\']+)["\']'
            ],

            # React Hook 패턴
            'react_hooks': [
                r'useEffect\s*\([^}]*axios\.get\s*\(\s*["\']([^"\']+)["\']',
                r'useCallback\s*\([^}]*axios\.post\s*\(\s*["\']([^"\']+)["\']',
                r'useState\s*\([^}]*fetch\s*\(\s*["\']([^"\']+)["\']'
            ],

            # TypeScript 특화 패턴
            'typescript': [
                r'async\s+\w+\s*\([^)]*\)\s*:\s*Promise<[^>]+>\s*{[^}]*axios\.get\s*\(\s*["\']([^"\']+)["\']',
                r'const\s+\w+\s*:\s*AxiosResponse<[^>]+>\s*=\s*await\s+axios\.get\s*\(\s*["\']([^"\']+)["\']'
            ]
        }

        # HTTP 메서드 추출 패턴
        self.method_patterns = [
            r'method:\s*["\']([^"\']+)["\']',
            r'axios\.(\w+)\s*\(',
            r'\$\.(\w+)\s*\(',
            r'this\.\$http\.(\w+)\s*\('
        ]

        # URL 변수 치환 패턴
        self.url_variable_patterns = [
            r'\$\{([^}]+)\}',  # ${variable}
            r'\`([^`]*\$\{[^}]+\}[^`]*)\`',  # template literal
            r'["\']([^"\']*\+[^"\']*)["\']'  # string concatenation
        ]

    def analyze_frontend_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        프론트엔드 파일 분석

        Args:
            file_path: 파일 경로
            content: 파일 내용

        Returns:
            분석 결과 (API 호출 정보 포함)
        """
        try:
            file_extension = self._get_file_extension(file_path)

            if file_extension not in self.supported_extensions:
                return {
                    'file_path': file_path,
                    'file_type': 'UNSUPPORTED',
                    'api_calls': []
                }

            # 파일 타입 결정
            file_type = self._detect_frontend_file_type(file_path, content)

            # API 호출 추출
            api_calls = self._extract_api_calls(content, file_type)

            # 컴포넌트명 추출
            component_name = self._extract_component_name(file_path, content, file_type)

            result = {
                'file_path': file_path,
                'file_type': file_type,
                'component_name': component_name,
                'api_calls': api_calls,
                'api_call_count': len(api_calls)
            }

            info(f"프론트엔드 파일 분석 완료 - 타입: {file_type}, API 호출: {len(api_calls)}개")
            return result

        except Exception as e:
            handle_error(e, f"프론트엔드 파일 분석 실패: {file_path}")
            return {
                'file_path': file_path,
                'file_type': 'ERROR',
                'error': str(e)
            }

    def _get_file_extension(self, file_path: str) -> str:
        """파일 확장자 추출"""
        import os
        return os.path.splitext(file_path)[1].lower()

    def _detect_frontend_file_type(self, file_path: str, content: str) -> str:
        """프론트엔드 파일 타입 감지"""
        try:
            file_extension = self._get_file_extension(file_path)
            content_lower = content.lower()

            # Vue 파일
            if file_extension == '.vue':
                return 'VUE_COMPONENT'

            # TypeScript 파일
            elif file_extension in ['.ts', '.tsx']:
                if 'react' in content_lower or 'jsx' in content_lower or '.tsx' in file_path:
                    return 'REACT_TYPESCRIPT'
                else:
                    return 'TYPESCRIPT'

            # JavaScript/JSX 파일
            elif file_extension in ['.js', '.jsx']:
                if 'react' in content_lower or 'jsx' in content_lower or '.jsx' in file_path:
                    return 'REACT_COMPONENT'
                elif 'vue' in content_lower:
                    return 'VUE_SCRIPT'
                else:
                    return 'JAVASCRIPT'

            return 'UNKNOWN_FRONTEND'

        except Exception as e:
            handle_error(e, f"프론트엔드 파일 타입 감지 실패: {file_path}")
            return 'UNKNOWN'

    def _extract_api_calls(self, content: str, file_type: str) -> List[Dict[str, Any]]:
        """API 호출 추출"""
        try:
            api_calls = []

            # 모든 패턴에 대해 검색
            for framework, patterns in self.api_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL)

                    for match in matches:
                        # URL 추출
                        api_url = self._extract_url_from_match(match)

                        if api_url and self._is_valid_api_url(api_url):
                            # HTTP 메서드 추정
                            http_method = self._infer_http_method(pattern, match, content)

                            # 라인 번호 계산
                            line_number = content[:match.start()].count('\n') + 1

                            # URL 정규화
                            normalized_url = self._normalize_api_url(api_url)

                            api_call = {
                                'api_url': normalized_url,
                                'original_url': api_url,
                                'http_method': http_method,
                                'framework': framework,
                                'pattern': pattern,
                                'line_number': line_number,
                                'confidence': self._calculate_confidence(framework, pattern, api_url)
                            }

                            # 중복 제거
                            if not self._is_duplicate_api_call(api_calls, api_call):
                                api_calls.append(api_call)

            return api_calls

        except Exception as e:
            handle_error(e, "API 호출 추출 실패")
            return []

    def _extract_url_from_match(self, match: re.Match) -> Optional[str]:
        """정규식 매치에서 URL 추출"""
        try:
            groups = match.groups()

            if not groups:
                return None

            # 패턴에 따라 URL 위치가 다름
            for group in groups:
                if group and ('/' in group or group.startswith('api')):
                    return group.strip()

            # 첫 번째 그룹을 기본으로 사용
            return groups[0].strip() if groups[0] else None

        except Exception as e:
            handle_error(e, "URL 추출 실패")
            return None

    def _infer_http_method(self, pattern: str, match: re.Match, content: str) -> str:
        """HTTP 메서드 추정"""
        try:
            # 패턴에서 메서드 추출
            if '.get' in pattern:
                return 'GET'
            elif '.post' in pattern:
                return 'POST'
            elif '.put' in pattern:
                return 'PUT'
            elif '.delete' in pattern:
                return 'DELETE'
            elif '.patch' in pattern:
                return 'PATCH'

            # 매치된 텍스트에서 메서드 추출
            matched_text = match.group(0)
            for method_pattern in self.method_patterns:
                method_match = re.search(method_pattern, matched_text, re.IGNORECASE)
                if method_match:
                    return method_match.group(1).upper()

            # 기본값
            return 'GET'

        except Exception as e:
            handle_error(e, "HTTP 메서드 추정 실패")
            return 'UNKNOWN'

    def _is_valid_api_url(self, url: str) -> bool:
        """유효한 API URL인지 검증"""
        if not url:
            return False

        # 너무 짧거나 긴 URL 제외
        if len(url) < 2 or len(url) > 200:
            return False

        # API URL 패턴 확인
        api_indicators = [
            '/api/', '/rest/', '/service/', '/v1/', '/v2/', '/graphql',
            url.startswith('/'), url.startswith('api/'), url.startswith('rest/')
        ]

        # 제외할 패턴
        exclude_patterns = [
            'http://', 'https://', 'ftp://', 'mailto:',
            '.css', '.js', '.png', '.jpg', '.gif',
            'javascript:', 'data:', '#'
        ]

        # 제외 패턴 체크
        for exclude in exclude_patterns:
            if exclude in url.lower():
                return False

        # API 패턴 체크
        return any(api_indicators)

    def _normalize_api_url(self, url: str) -> str:
        """API URL 정규화"""
        try:
            # 변수 부분 정규화
            normalized = url

            # ${variable} → {variable}
            normalized = re.sub(r'\$\{([^}]+)\}', r'{\1}', normalized)

            # 템플릿 리터럴 처리
            if '${' in normalized:
                normalized = re.sub(r'[`"]([^`"]*\$\{[^}]+\}[^`"]*)[`"]', r'\1', normalized)

            # 문자열 연결 처리 (간단한 케이스만)
            normalized = re.sub(r'["\']([^"\']*)\+[^"\']*\+[^"\']*["\']', r'\1{dynamic}', normalized)

            # 시작/끝 따옴표 제거
            normalized = normalized.strip('\'"` ')

            # 중복 슬래시 제거
            normalized = re.sub(r'/+', '/', normalized)

            return normalized

        except Exception as e:
            handle_error(e, f"API URL 정규화 실패: {url}")
            return url

    def _calculate_confidence(self, framework: str, pattern: str, url: str) -> float:
        """신뢰도 계산"""
        try:
            confidence = 0.5  # 기본값

            # 프레임워크별 신뢰도
            framework_scores = {
                'axios': 0.9,
                'fetch': 0.8,
                'jquery': 0.7,
                'vue_resource': 0.8,
                'vue_composition': 0.8,
                'react_hooks': 0.8,
                'typescript': 0.9
            }

            confidence += framework_scores.get(framework, 0.3)

            # URL 패턴에 따른 신뢰도 조정
            if url.startswith('/api/'):
                confidence += 0.2
            elif url.startswith('/rest/'):
                confidence += 0.15
            elif url.startswith('/'):
                confidence += 0.1

            # 변수가 포함된 경우 신뢰도 조정
            if '{' in url or '$' in url:
                confidence -= 0.1

            return min(1.0, confidence)

        except Exception as e:
            handle_error(e, "신뢰도 계산 실패")
            return 0.5

    def _is_duplicate_api_call(self, existing_calls: List[Dict[str, Any]], new_call: Dict[str, Any]) -> bool:
        """중복 API 호출 체크"""
        for call in existing_calls:
            if (call['api_url'] == new_call['api_url'] and
                call['http_method'] == new_call['http_method']):
                return True
        return False

    def _extract_component_name(self, file_path: str, content: str, file_type: str) -> str:
        """컴포넌트명 추출"""
        try:
            import os

            # 파일명에서 기본 컴포넌트명 추출
            file_name = os.path.basename(file_path)
            base_name = os.path.splitext(file_name)[0]

            # Vue 컴포넌트
            if file_type == 'VUE_COMPONENT':
                # Vue 컴포넌트명 패턴
                name_match = re.search(r'name:\s*["\']([^"\']+)["\']', content)
                if name_match:
                    return name_match.group(1)

            # React 컴포넌트
            elif 'REACT' in file_type:
                # React 컴포넌트 패턴
                patterns = [
                    r'export\s+default\s+function\s+([A-Za-z_][A-Za-z0-9_]*)',
                    r'const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\([^)]*\)\s*=>\s*{',
                    r'function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*{'
                ]

                for pattern in patterns:
                    match = re.search(pattern, content)
                    if match:
                        return match.group(1)

            # 기본값: 파일명 사용
            return base_name

        except Exception as e:
            handle_error(e, f"컴포넌트명 추출 실패: {file_path}")
            return os.path.basename(file_path)

    def get_unique_api_urls(self, api_calls: List[Dict[str, Any]]) -> Set[str]:
        """API 호출에서 고유한 URL 집합 추출"""
        return {call['api_url'] for call in api_calls if call.get('api_url')}

    def group_by_framework(self, api_calls: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """프레임워크별로 API 호출 그룹화"""
        grouped = {}
        for call in api_calls:
            framework = call.get('framework', 'unknown')
            if framework not in grouped:
                grouped[framework] = []
            grouped[framework].append(call)
        return grouped