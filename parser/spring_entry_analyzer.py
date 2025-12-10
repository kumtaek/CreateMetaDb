"""
SourceAnalyzer Spring 프레임워크 진입점 분석기
- Spring Boot, Spring MVC 어노테이션 기반 API 진입점 분석
- AST 파싱 및 정규식 Fallback 전략
- @RestController, @Controller, @RequestMapping 등 분석
"""

import re
import time
from typing import List, Dict, Any, Optional
from .base_entry_analyzer import BaseEntryAnalyzer, BackendEntryInfo, FileInfo
from util.logger import app_logger, handle_error


class SpringEntryAnalyzer(BaseEntryAnalyzer):
    """Spring 프레임워크 진입점 분석기"""
    
    def __init__(self):
        """Spring 분석기 초기화"""
        # 설정 파일 경로 구성
        from util.path_utils import PathUtils
        path_utils = PathUtils()
        config_path = path_utils.get_parser_config_path("spring_entry")
        
        super().__init__('spring', config_path)
        
        # 정규식 패턴 미리 컴파일
        self._compile_regex_patterns()
    
    def _compile_regex_patterns(self) -> None:
        """정규식 패턴 미리 컴파일"""
        try:
            # 설정에서 정규식 패턴 가져오기
            class_declaration_pattern = self.get_config_value("regex_patterns.class_declaration")
            class_annotation_pattern = self.get_config_value("regex_patterns.class_annotation")
            method_annotation_pattern = self.get_config_value("regex_patterns.method_annotation")
            url_from_attribute_pattern = self.get_config_value("regex_patterns.url_from_attribute")
            
            # 정규식 컴파일 (DOTALL 플래그 추가 - 줄바꿈 처리)
            self.class_declaration_regex = re.compile(class_declaration_pattern) if class_declaration_pattern else None
            self.class_annotation_regex = re.compile(class_annotation_pattern) if class_annotation_pattern else None
            self.method_annotation_regex = re.compile(method_annotation_pattern, re.DOTALL) if method_annotation_pattern else None
            self.url_from_attribute_regex = re.compile(url_from_attribute_pattern) if url_from_attribute_pattern else None
            
            app_logger.debug("Spring 분석기 정규식 패턴 컴파일 완료")
            
        except Exception as e:
            handle_error(e, "정규식 패턴 컴파일 실패")
    
    def _set_default_regex_patterns(self) -> None:
        """기본 정규식 패턴 설정"""
        self.class_declaration_regex = re.compile(r'(?m)^[ \t]*((public|private|protected)\s+)?class\s+(\w+)\s*.*{')
        self.class_annotation_regex = re.compile(r'(@(?:RestController|Controller|RequestMapping)\s*(?:\(.*?\))?)\s+(?=(?:public|class))')
        self.method_annotation_regex = re.compile(r'(@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*(?:\([^)]*\))?|@RequestMapping\s*\([^)]*(?:method\s*=|,\s*method\s*=)[^)]*\))\s*(?:\n\s*@\w+\s*)*\n\s*(?:public|private|protected)\s+(?:[\w\<\>\[\],\s\?]+\s+)(\w+)\s*\(', re.DOTALL)
        self.url_from_attribute_regex = re.compile(r'(?:path|value)\s*=\s*"(.*?)"')
    
    def extract_url_from_annotation(self, annotation_text: str) -> Optional[str]:
        """
        Spring 어노테이션에서 URL 추출 (모든 매핑 어노테이션 지원)
        
        Args:
            annotation_text: 어노테이션 텍스트
            
        Returns:
            추출된 URL 또는 None
        """
        try:
            import re
            
            # 모든 Spring 매핑 어노테이션에서 URL 추출
            mapping_patterns = [
                # 단순 형태: @GetMapping("/url")
                r'@GetMapping\s*\(\s*"([^"]*)"\s*\)',
                r'@PostMapping\s*\(\s*"([^"]*)"\s*\)',
                r'@PutMapping\s*\(\s*"([^"]*)"\s*\)',
                r'@DeleteMapping\s*\(\s*"([^"]*)"\s*\)',
                r'@PatchMapping\s*\(\s*"([^"]*)"\s*\)',
                r'@RequestMapping\s*\(\s*"([^"]*)"\s*\)',
                # 속성 형태: value = "/url" 또는 path = "/url"
                r'(?:path|value)\s*=\s*"([^"]*)"'
            ]
            
            for pattern in mapping_patterns:
                match = re.search(pattern, annotation_text)
                if match:
                    return match.group(1)
            
            # 어노테이션이 있지만 URL이 없는 경우 (예: @GetMapping())
            if any(anno in annotation_text for anno in ['@GetMapping', '@PostMapping', '@PutMapping', '@DeleteMapping', '@PatchMapping', '@RequestMapping']):
                # URL이 명시되지 않은 경우 빈 문자열 반환 (클래스 URL만 사용)
                return ""
            
            return None
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"Spring URL 추출 실패: {annotation_text}")
            return None
    
    def _combine_urls(self, class_url: str, method_url: str) -> str:
        """
        클래스 URL과 메서드 URL을 결합
        
        Args:
            class_url: 클래스 레벨 URL
            method_url: 메서드 레벨 URL
            
        Returns:
            결합된 URL
        """
        try:
            # 빈 URL 처리
            if not class_url and not method_url:
                return "/"
            
            if not class_url:
                return method_url or "/"
            
            if not method_url:
                return class_url
            
            # URL 정규화
            class_url = class_url.strip()
            method_url = method_url.strip()
            
            # 시작 슬래시 처리
            if not class_url.startswith('/'):
                class_url = '/' + class_url
            
            if method_url.startswith('/'):
                method_url = method_url[1:]  # 앞의 슬래시 제거
            
            # 끝 슬래시 처리
            if class_url.endswith('/'):
                class_url = class_url[:-1]
            
            # URL 결합
            if method_url:
                combined_url = f"{class_url}/{method_url}"
            else:
                combined_url = class_url
            
            # 중복 슬래시 제거
            combined_url = re.sub(r'/+', '/', combined_url)
            
            # 빈 경로는 루트로
            if not combined_url or combined_url == '':
                combined_url = '/'
            
            return combined_url
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"URL 결합 실패: class_url={class_url}, method_url={method_url}")
    
    def analyze_backend_entry(self, java_file: FileInfo, stats: 'StatisticsCollector') -> List[BackendEntryInfo]:
        """
        Spring 진입점 분석 (정규식 기반)
        
        Args:
            java_file: 분석할 Java 파일 정보
            stats: 통계 수집기
            
        Returns:
            백엔드 진입점 정보 리스트
        """
        start_time = time.time()
        
        try:
            # 정규식 기반 파싱 실행
            regex_results = self._parse_with_regex(java_file.content, java_file.file_path, java_file.file_id)
            
            processing_time = time.time() - start_time
            
            if regex_results:
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
            
            # 파싱 실패
            error_message = f"정규식 파싱으로 진입점을 찾지 못했습니다: {java_file.file_path}"
            
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
            error_message = f"Spring 분석 중 심각한 오류 발생: {str(e)}"
            handle_error(e, error_message)
            return []  # 이 라인은 실행되지 않음 (handle_error에서 exit)
    
    
    def _parse_with_regex(self, content: str, file_path: str, file_id: int = 0) -> List[BackendEntryInfo]:
        """
        정규식 기반 파싱
        
        Args:
            content: Java 파일 내용
            file_path: 파일 경로
            
        Returns:
            백엔드 진입점 정보 리스트
        """
        try:
            # 1. 주석 및 문자열 제거 전처리
            clean_content = self.preprocess_content(content)
            lines = content.split('\n')
            
            # 2. 클래스 정보 추출
            class_info = self._extract_class_info_regex(clean_content, lines)
            if not class_info:
                return []
            
            # 3. 메서드 정보 추출
            entries = self._extract_method_info_regex(clean_content, class_info, lines, file_path, file_id)
            
            return entries
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"정규식 파싱 실패: {file_path}")
    
    def _extract_class_info_regex(self, content: str, lines: List[str]) -> Optional[Dict[str, Any]]:
        """정규식으로 클래스 정보 추출"""
        try:
            # 클래스 선언 찾기
            if not self.class_declaration_regex:
                return None
            
            class_matches = self.class_declaration_regex.findall(content)
            if not class_matches:
                return None
            
            # 첫 번째 클래스 사용
            class_match = class_matches[0]
            class_name = class_match[2] if len(class_match) > 2 else "Unknown"
            
            # 클래스 어노테이션 찾기
            class_annotations = []
            class_url = ""
            
            if self.class_annotation_regex:
                annotation_matches = self.class_annotation_regex.findall(content)
                
                for match in annotation_matches:
                    annotation_text = match[0] if isinstance(match, tuple) else match
                    class_annotations.append(annotation_text)
                    
                    # URL 추출
                    url = self.extract_url_from_annotation(annotation_text)
                    if url:
                        class_url = url
            
            # Spring 컨트롤러인지 확인
            spring_annotations = self.get_config_value("spring_annotations.class_annotations", [])
            if not any(anno.replace('@', '') in [ann.replace('@', '') for ann in class_annotations] 
                      for anno in spring_annotations):
                return None
            
            return {
                'name': class_name,
                'annotations': class_annotations,
                'url': class_url,
                'line_start': 0,
                'file_id': 0  # 정규식 파싱에서는 file_id를 나중에 설정
            }
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"정규식 클래스 정보 추출 실패")
    
    def _extract_method_info_regex(self, content: str, class_info: Dict[str, Any], lines: List[str], file_path: str, file_id: int = 0) -> List[BackendEntryInfo]:
        """정규식으로 메서드 정보 추출"""
        entries = []
        
        try:
            # class_info에 file_id 설정
            class_info['file_id'] = file_id
            if not self.method_annotation_regex:
                return entries
            
            # 메서드 어노테이션 찾기 (클래스 레벨 제외)
            # 개선된 정규식: 메서드 레벨만 매치 (method 속성이 있거나 GetMapping 등의 전용 어노테이션)
            import re
            improved_pattern = r'(@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*(?:\([^)]*\))?|@RequestMapping\s*\([^)]*(?:method\s*=|,\s*method\s*=)[^)]*\))\s*(?:\n\s*@\w+\s*)*\n\s*(?:public|private|protected)\s+(?:[\w\<\>\[\],\s\?]+\s+)(\w+)\s*\('
            improved_regex = re.compile(improved_pattern, re.DOTALL)
            method_matches = improved_regex.findall(content)
            
            for match in method_matches:
                try:
                    if isinstance(match, tuple) and len(match) >= 2:
                        annotation_text = match[0]
                        method_name = match[1]
                    else:
                        continue

                    # 클래스 레벨 @RequestMapping 제외 로직 추가
                    # @RequestMapping에서 method 속성이 없으면 클래스 레벨일 가능성이 높음
                    if annotation_text.startswith('@RequestMapping') and 'method' not in annotation_text:
                        # 추가 검증: URL만 있고 method 속성이 없으면 클래스 레벨로 간주
                        if self.extract_url_from_annotation(annotation_text) and 'method' not in annotation_text:
                            continue  # 클래스 레벨로 간주하여 스킵

                    # HTTP 메서드 추출
                    http_methods = self.extract_http_method_from_annotation(annotation_text)

                    # URL 추출
                    method_url = self.extract_url_from_annotation(annotation_text)


                    # URL 조합
                    full_url = self._combine_urls(class_info['url'], method_url)

                    # 디버깅 로그
                    app_logger.debug(f"메서드: {method_name}, 어노테이션: {annotation_text[:50]}...")
                    app_logger.debug(f"  HTTP 메서드들: {http_methods}")
                    app_logger.debug(f"  메서드 URL: {method_url}")
                    app_logger.debug(f"  클래스 URL: {class_info['url']}")
                    app_logger.debug(f"  결합된 URL: {full_url}")
                    
                    # 각 HTTP 메서드에 대해 엔트리 생성
                    for http_method in http_methods:
                        entry = self.create_backend_entry_info(
                            class_name=class_info['name'],
                            method_name=method_name,
                            url_pattern=full_url,
                            http_method=http_method,
                            file_path=file_path,
                            file_id=class_info.get('file_id', 0),
                            line_start=0,  # 정규식으로는 정확한 라인 번호 추출 어려움
                            line_end=0,
                            parameters=[],  # 정규식으로는 파라미터 추출 어려움
                            return_type="void",
                            annotations=[annotation_text],
                            class_url=class_info.get('url', '')
                        )
                        entries.append(entry)
                        
                except Exception as e:
                    # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                    handle_error(e, f"메서드 정보 추출 실패")
            
            return entries
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"정규식 메서드 정보 추출 실패")


# 사용 예시
if __name__ == "__main__":
    # Spring 분석기 테스트
    analyzer = SpringEntryAnalyzer()
    
    # 테스트용 Java 파일 내용
    test_content = '''
@RestController
@RequestMapping("/api/users")
public class UserController {
    
    @GetMapping("/list")
    public List<User> getUserList() {
        return userService.getUsers();
    }
    
    @PostMapping("/create")
    public User createUser(@RequestBody User user) {
        return userService.createUser(user);
    }
}
'''
    
    # 테스트용 FileInfo 객체
    test_file = FileInfo(
        file_id=1,
        file_path="UserController.java",
        file_name="UserController.java",
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
