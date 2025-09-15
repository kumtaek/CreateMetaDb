"""
SourceAnalyzer 백엔드 진입점 분석기 추상 기본 클래스
- 모든 분석기의 공통 인터페이스 정의
- 설정 파일 로드 및 검증
- 공통 유틸리티 메서드 제공
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from util.logger import app_logger, handle_error
from util.config_utils import ConfigUtils
from util.path_utils import PathUtils


@dataclass
class BackendEntryInfo:
    """백엔드 진입점 정보 데이터 클래스"""
    class_name: str           # 클래스명
    method_name: str          # 메서드명
    url_pattern: str          # URL 패턴
    http_method: str          # HTTP 메서드 (GET, POST, PUT, DELETE 등)
    parameters: List[str]     # 파라미터 목록
    return_type: str          # 반환 타입
    annotations: List[str]    # 관련 어노테이션
    file_path: str            # 파일 경로
    file_id: int              # 파일 ID
    line_start: int           # 시작 라인
    line_end: int             # 종료 라인
    framework: str = 'unknown'  # 프레임워크 ('spring', 'servlet', 'jax-rs' 등)
    class_url: str = ''       # 클래스 레벨 URL (Spring의 경우)
    has_error: str = 'N'      # 오류 여부 ('N'/'Y')
    error_message: Optional[str] = None  # 오류 메시지


@dataclass
class FileInfo:
    """파일 정보 데이터 클래스"""
    file_id: int
    file_path: str
    file_name: str
    file_type: str
    content: str
    hash_value: str
    line_count: int = 0


class BaseEntryAnalyzer(ABC):
    """백엔드 진입점 분석기 추상 기본 클래스"""
    
    def __init__(self, framework_name: str, config_path: str):
        """
        분석기 초기화
        
        Args:
            framework_name: 프레임워크명 (예: 'spring')
            config_path: 설정 파일 경로
        """
        self.framework_name = framework_name
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.path_utils = PathUtils()
        
        if not self.config:
            handle_error(Exception(f"설정 파일 로드 실패: {config_path}"), 
                        f"분석기 초기화 실패: {framework_name}")
    
    def _load_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """
        설정 파일 로드
        
        Args:
            config_path: 설정 파일 경로
            
        Returns:
            설정 딕셔너리 또는 None (실패시)
        """
        try:
            config_utils = ConfigUtils()
            config = config_utils.load_yaml_config(config_path)
            
            if config:
                app_logger.debug(f"설정 파일 로드 성공: {config_path}")
                return config
            else:
                app_logger.error(f"설정 파일 로드 실패: {config_path}")
                return None
                
        except Exception as e:
            handle_error(e, f"설정 파일 로드 중 오류 발생: {config_path}")
            return None
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """
        설정 값 조회 (점 표기법 지원)
        
        Args:
            key_path: 키 경로 (예: "file_filtering.include_patterns")
            default: 기본값
            
        Returns:
            설정 값 또는 기본값
        """
        try:
            keys = key_path.split('.')
            value = self.config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"설정 값 조회 실패: {key_path}")
    
    def is_target_file(self, file_path: str) -> bool:
        """
        파일이 분석 대상인지 확인 (2차 필터링)
        
        Args:
            file_path: 파일 경로
            
        Returns:
            분석 대상 여부 (True/False)
        """
        try:
            import fnmatch
            import os
            
            file_name = os.path.basename(file_path)
            
            # 포함 패턴 확인
            include_patterns = self.get_config_value("file_filtering.include_patterns", [])
            if include_patterns:
                include_match = any(fnmatch.fnmatch(file_name, pattern) for pattern in include_patterns)
                if not include_match:
                    return False
            
            # 제외 패턴 확인
            exclude_patterns = self.get_config_value("file_filtering.exclude_patterns", [])
            if exclude_patterns:
                exclude_match = any(fnmatch.fnmatch(file_name, pattern) for pattern in exclude_patterns)
                if exclude_match:
                    return False
            
            return True
            
        except Exception as e:
            # USER RULE: 파일 필터링 확인 실패는 handle_error()로 즉시 종료
            handle_error(e, f"파일 필터링 확인 실패: {file_path}")
    
    def preprocess_content(self, content: str) -> str:
        """
        분석 전 컨텐츠 전처리 (주석 및 문자열 제거)
        
        Args:
            content: 원본 컨텐츠
            
        Returns:
            전처리된 컨텐츠
        """
        try:
            import re
            
            # 멀티라인 주석 제거
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            
            # 한 줄 주석 제거
            content = re.sub(r'//.*', '', content)
            
            # 문자열 리터럴을 빈 문자열로 대체 (정규식 오탐지 방지)
            content = re.sub(r'"(.*?)"', '""', content)
            content = re.sub(r"'(.*?)'", "''", content)
            
            return content
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"컨텐츠 전처리 실패")
    
    def extract_url_from_annotation(self, annotation_text: str) -> Optional[str]:
        """
        어노테이션에서 URL 추출
        
        Args:
            annotation_text: 어노테이션 텍스트
            
        Returns:
            추출된 URL 또는 None
        """
        try:
            import re
            
            # URL 속성 목록 가져오기
            url_attributes = self.get_config_value("extraction_rules.url_attributes", ["path", "value"])
            
            # 각 URL 속성에 대해 패턴 매칭
            for attr in url_attributes:
                pattern = f'{attr}\\s*=\\s*"([^"]*)"'
                match = re.search(pattern, annotation_text)
                if match:
                    return match.group(1)
            
            # @RequestMapping("/path") 형태 직접 처리
            direct_pattern = r'@RequestMapping\s*\(\s*"([^"]*)"\s*\)'
            match = re.search(direct_pattern, annotation_text)
            if match:
                return match.group(1)
            
            return None
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"URL 추출 실패: {annotation_text}")
    
    def extract_http_method_from_annotation(self, annotation_text: str) -> List[str]:
        """
        어노테이션에서 HTTP 메서드 추출
        
        Args:
            annotation_text: 어노테이션 텍스트
            
        Returns:
            HTTP 메서드 리스트
        """
        try:
            import re
            
            # 기본 HTTP 메서드 가져오기
            default_methods = self.get_config_value("extraction_rules.default_http_methods", ["GET", "POST"])
            
            # method 속성에서 HTTP 메서드 추출
            method_pattern = r'method\s*=\s*\{([^}]*)\}'
            match = re.search(method_pattern, annotation_text)
            if match:
                methods_text = match.group(1)
                # RequestMethod.GET, RequestMethod.POST 형태에서 GET, POST 추출
                methods = re.findall(r'RequestMethod\.(\w+)', methods_text)
                if methods:
                    return [method.upper() for method in methods]
            
            # 어노테이션 타입에서 HTTP 메서드 추출
            if '@GetMapping' in annotation_text:
                return ['GET']
            elif '@PostMapping' in annotation_text:
                return ['POST']
            elif '@PutMapping' in annotation_text:
                return ['PUT']
            elif '@DeleteMapping' in annotation_text:
                return ['DELETE']
            elif '@PatchMapping' in annotation_text:
                return ['PATCH']
            
            # 기본값 반환
            return default_methods
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"HTTP 메서드 추출 실패: {annotation_text}")
    
    def normalize_url_path(self, *parts: str) -> str:
        """
        URL 경로 정규화
        
        Args:
            *parts: URL 경로 조각들
            
        Returns:
            정규화된 URL 경로
        """
        from util.path_utils import normalize_url_path
        return normalize_url_path(*parts)
    
    def create_backend_entry_info(self,
                                class_name: str,
                                method_name: str,
                                url_pattern: str,
                                http_method: str,
                                file_path: str,
                                file_id: int,
                                line_start: int,
                                line_end: int,
                                parameters: List[str] = None,
                                return_type: str = "void",
                                annotations: List[str] = None,
                                framework: str = None,
                                class_url: str = '',
                                has_error: str = 'N',
                                error_message: Optional[str] = None) -> BackendEntryInfo:
        """
        BackendEntryInfo 객체 생성

        Args:
            class_name: 클래스명
            method_name: 메서드명
            url_pattern: URL 패턴
            http_method: HTTP 메서드
            file_path: 파일 경로
            line_start: 시작 라인
            line_end: 종료 라인
            parameters: 파라미터 목록
            return_type: 반환 타입
            annotations: 어노테이션 목록
            framework: 프레임워크명 ('spring', 'servlet', 'jax-rs' 등)
            class_url: 클래스 레벨 URL (Spring의 경우)
            has_error: 오류 여부
            error_message: 오류 메시지

        Returns:
            BackendEntryInfo 객체
        """
        return BackendEntryInfo(
            class_name=class_name,
            method_name=method_name,
            url_pattern=url_pattern,
            http_method=http_method,
            parameters=parameters or [],
            return_type=return_type,
            annotations=annotations or [],
            file_path=file_path,
            file_id=file_id,
            line_start=line_start,
            line_end=line_end,
            framework=framework or self.framework_name,
            class_url=class_url,
            has_error=has_error,
            error_message=error_message
        )
    
    @abstractmethod
    def analyze_backend_entry(self, java_file: FileInfo, stats: 'StatisticsCollector') -> List[BackendEntryInfo]:
        """
        주어진 Java 파일에서 백엔드 진입점 정보를 분석하여 반환합니다.
        
        USER RULE: 파싱 에러 발생 시, 빈 리스트를 반환하고 stats에 실패를 기록합니다.
                   내부적으로 has_error='Y' 처리 후 DB에 저장될 수 있도록 합니다.
        
        Args:
            java_file: 분석할 Java 파일 정보
            stats: 통계 수집기
            
        Returns:
            백엔드 진입점 정보 리스트
        """
        pass
    
    def get_framework_name(self) -> str:
        """프레임워크명 반환"""
        return self.framework_name
    
    def get_config(self) -> Dict[str, Any]:
        """설정 딕셔너리 반환"""
        return self.config


# 사용 예시
if __name__ == "__main__":
    # 추상 클래스이므로 직접 인스턴스화할 수 없음
    # 구체적인 구현체에서 상속받아 사용
    pass
