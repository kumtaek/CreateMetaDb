"""
SourceAnalyzer 백엔드 진입점 분석기 팩토리
- 프레임워크별 분석기 생성 및 관리
- 전략 패턴을 통한 분석기 선택
- 설정 기반 분석기 등록
"""

from typing import Dict, List, Type, Optional, Any
from .base_entry_analyzer import BaseEntryAnalyzer
from .spring_entry_analyzer import SpringEntryAnalyzer
from .servlet_entry_analyzer import ServletEntryAnalyzer
from util.logger import app_logger, handle_error
from util.path_utils import PathUtils


class EntryAnalyzerFactory:
    """백엔드 진입점 분석기 팩토리 클래스"""
    
    def __init__(self):
        """팩토리 초기화"""
        self._analyzers: Dict[str, Type[BaseEntryAnalyzer]] = {}
        self._analyzer_instances: Dict[str, BaseEntryAnalyzer] = {}
        self.path_utils = PathUtils()
        
        # 기본 분석기 등록
        self._register_default_analyzers()
    
    def _register_default_analyzers(self) -> None:
        """기본 분석기 등록"""
        try:
            # Spring 분석기 등록
            self.register_analyzer('spring', SpringEntryAnalyzer)
            
            # Servlet 분석기 등록
            self.register_analyzer('servlet', ServletEntryAnalyzer)
            
            app_logger.debug("기본 분석기 등록 완료")
            
        except Exception as e:
            handle_error(e, "기본 분석기 등록 실패")
    
    def register_analyzer(self, framework_name: str, analyzer_class: Type[BaseEntryAnalyzer]) -> None:
        """
        분석기 등록
        
        Args:
            framework_name: 프레임워크명 (예: 'spring', 'jax-rs', 'servlet')
            analyzer_class: 분석기 클래스
        """
        try:
            if not issubclass(analyzer_class, BaseEntryAnalyzer):
                raise ValueError(f"분석기는 BaseEntryAnalyzer를 상속받아야 합니다: {analyzer_class}")
            
            self._analyzers[framework_name] = analyzer_class
            app_logger.debug(f"분석기 등록 완료: {framework_name} -> {analyzer_class.__name__}")
            
        except Exception as e:
            handle_error(e, f"분석기 등록 실패: {framework_name}")
    
    def get_analyzer(self, framework_name: str, **kwargs) -> Optional[BaseEntryAnalyzer]:
        """
        분석기 인스턴스 조회 (싱글톤 패턴)
        
        Args:
            framework_name: 프레임워크명
            **kwargs: 분석기 생성 시 필요한 추가 파라미터 (예: servlet_url_map)
            
        Returns:
            분석기 인스턴스 또는 None (등록되지 않은 경우)
        """
        try:
            # Servlet 분석기는 매번 새로운 인스턴스 생성 (servlet_url_map이 다를 수 있음)
            if framework_name == 'servlet':
                # 등록된 분석기 클래스가 있는지 확인
                if framework_name not in self._analyzers:
                    # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                    handle_error(Exception(f"등록되지 않은 분석기: {framework_name}"), "분석기 조회 실패")
                
                # 분석기 인스턴스 생성 (servlet_url_map 전달)
                analyzer_class = self._analyzers[framework_name]
                analyzer_instance = analyzer_class(**kwargs)
                
                app_logger.debug(f"Servlet 분석기 인스턴스 생성: {framework_name}")
                return analyzer_instance
            
            # 다른 분석기들은 싱글톤 패턴 유지
            # 이미 생성된 인스턴스가 있으면 반환
            if framework_name in self._analyzer_instances:
                return self._analyzer_instances[framework_name]
            
            # 등록된 분석기 클래스가 있는지 확인
            if framework_name not in self._analyzers:
                # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                handle_error(Exception(f"등록되지 않은 분석기: {framework_name}"), "분석기 조회 실패")
            
            # 분석기 인스턴스 생성
            analyzer_class = self._analyzers[framework_name]
            analyzer_instance = analyzer_class()
            
            # 인스턴스 캐시에 저장
            self._analyzer_instances[framework_name] = analyzer_instance
            
            app_logger.debug(f"분석기 인스턴스 생성: {framework_name}")
            return analyzer_instance
            
        except Exception as e:
            handle_error(e, f"분석기 인스턴스 생성 실패: {framework_name}")
            return None
    
    def get_available_analyzers(self) -> List[str]:
        """
        사용 가능한 분석기 목록 조회
        
        Returns:
            프레임워크명 리스트
        """
        return list(self._analyzers.keys())
    
    def is_analyzer_available(self, framework_name: str) -> bool:
        """
        분석기 사용 가능 여부 확인
        
        Args:
            framework_name: 프레임워크명
            
        Returns:
            사용 가능 여부 (True/False)
        """
        return framework_name in self._analyzers
    
    def get_analyzer_info(self, framework_name: str) -> Optional[Dict[str, str]]:
        """
        분석기 정보 조회
        
        Args:
            framework_name: 프레임워크명
            
        Returns:
            분석기 정보 딕셔너리 또는 None
        """
        try:
            if framework_name not in self._analyzers:
                return None
            
            analyzer_class = self._analyzers[framework_name]
            
            return {
                'framework_name': framework_name,
                'class_name': analyzer_class.__name__,
                'module_name': analyzer_class.__module__,
                'description': getattr(analyzer_class, '__doc__', '').strip() if hasattr(analyzer_class, '__doc__') else ''
            }
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"분석기 정보 조회 실패: {framework_name}")
    
    def get_all_analyzer_info(self) -> Dict[str, Dict[str, str]]:
        """
        모든 분석기 정보 조회
        
        Returns:
            프레임워크별 분석기 정보 딕셔너리
        """
        info_dict = {}
        
        for framework_name in self._analyzers.keys():
            info = self.get_analyzer_info(framework_name)
            if info:
                info_dict[framework_name] = info
        
        return info_dict
    
    def load_analyzers_from_config(self, project_name: str, servlet_url_map: Dict[str, str] = None) -> List[BaseEntryAnalyzer]:
        """
        설정 파일에서 분석기 목록 로드
        
        Args:
            project_name: 프로젝트명
            servlet_url_map: web.xml에서 파싱한 서블릿 클래스명과 URL 패턴 맵
            
        Returns:
            활성화된 분석기 인스턴스 리스트
        """
        try:
            # 설정 파일에서 활성화된 분석기 목록 가져오기
            # Spring과 Servlet 분석기 모두 활성화
            active_analyzers = ['spring', 'servlet']
            
            analyzers = []
            for framework_name in active_analyzers:
                if framework_name == 'servlet':
                    # Servlet 분석기는 servlet_url_map 전달
                    analyzer = self.get_analyzer(framework_name, servlet_url_map=servlet_url_map)
                else:
                    # Spring 분석기는 기본 생성
                    analyzer = self.get_analyzer(framework_name)
                
                if analyzer:
                    analyzers.append(analyzer)
                    app_logger.debug(f"분석기 로드 완료: {framework_name}")
                else:
                    app_logger.warning(f"분석기 로드 실패: {framework_name}")
            
            app_logger.debug(f"총 {len(analyzers)}개 분석기 로드 완료")
            return analyzers
            
        except Exception as e:
            handle_error(e, f"설정에서 분석기 로드 실패: {project_name}")
            return []
    
    def create_analyzer_for_framework(self, framework_name: str) -> Optional[BaseEntryAnalyzer]:
        """
        특정 프레임워크용 분석기 생성 (팩토리 메서드)
        
        Args:
            framework_name: 프레임워크명
            
        Returns:
            분석기 인스턴스 또는 None
        """
        return self.get_analyzer(framework_name)
    
    def detect_framework_from_file(self, file_path: str, content: str) -> List[str]:
        """
        파일 내용에서 프레임워크 자동 감지
        
        Args:
            file_path: 파일 경로
            content: 파일 내용
            
        Returns:
            감지된 프레임워크명 리스트
        """
        detected_frameworks = []
        
        try:
            # Spring 프레임워크 감지
            spring_indicators = [
                '@RestController', '@Controller', '@RequestMapping',
                '@GetMapping', '@PostMapping', '@PutMapping', '@DeleteMapping',
                'org.springframework', 'SpringBootApplication'
            ]
            
            if any(indicator in content for indicator in spring_indicators):
                detected_frameworks.append('spring')
            
            # JAX-RS 프레임워크 감지
            jaxrs_indicators = [
                '@Path', '@GET', '@POST', '@PUT', '@DELETE',
                'javax.ws.rs', 'jakarta.ws.rs'
            ]
            
            if any(indicator in content for indicator in jaxrs_indicators):
                detected_frameworks.append('jax-rs')
            
            # Servlet 프레임워크 감지
            servlet_indicators = [
                '@WebServlet', 'HttpServlet', 'GenericServlet',
                'javax.servlet', 'jakarta.servlet'
            ]
            
            if any(indicator in content for indicator in servlet_indicators):
                detected_frameworks.append('servlet')
            
            app_logger.debug(f"프레임워크 감지 완료: {file_path} -> {detected_frameworks}")
            
        except Exception as e:
            # USER RULE: 프레임워크 감지 실패는 handle_error()로 즉시 종료
            handle_error(e, f"프레임워크 감지 실패: {file_path}")
        
        return detected_frameworks
    
    def get_analyzers_for_file(self, file_path: str, content: str) -> List[BaseEntryAnalyzer]:
        """
        파일에 적합한 분석기 목록 조회
        
        Args:
            file_path: 파일 경로
            content: 파일 내용
            
        Returns:
            적합한 분석기 인스턴스 리스트
        """
        analyzers = []
        
        try:
            # 프레임워크 자동 감지
            detected_frameworks = self.detect_framework_from_file(file_path, content)
            
            # 감지된 프레임워크에 해당하는 분석기 생성
            for framework_name in detected_frameworks:
                analyzer = self.get_analyzer(framework_name)
                if analyzer and analyzer.is_target_file(file_path):
                    analyzers.append(analyzer)
            
            # 감지되지 않은 경우 기본 분석기 사용
            if not analyzers:
                default_analyzer = self.get_analyzer('spring')
                if default_analyzer and default_analyzer.is_target_file(file_path):
                    analyzers.append(default_analyzer)
            
            app_logger.debug(f"파일용 분석기 선택: {file_path} -> {[a.get_framework_name() for a in analyzers]}")
            
        except Exception as e:
            # USER RULE: 파일용 분석기 선택 실패는 handle_error()로 즉시 종료
            handle_error(e, f"파일용 분석기 선택 실패: {file_path}")
        
        return analyzers
    
    def clear_instances(self) -> None:
        """분석기 인스턴스 캐시 초기화"""
        self._analyzer_instances.clear()
        app_logger.debug("분석기 인스턴스 캐시 초기화 완료")
    
    def get_factory_stats(self) -> Dict[str, Any]:
        """
        팩토리 통계 정보 조회
        
        Returns:
            팩토리 통계 딕셔너리
        """
        return {
            'registered_analyzers': len(self._analyzers),
            'active_instances': len(self._analyzer_instances),
            'available_frameworks': list(self._analyzers.keys()),
            'active_frameworks': list(self._analyzer_instances.keys())
        }


# 전역 팩토리 인스턴스
_global_factory: Optional[EntryAnalyzerFactory] = None


def get_global_factory() -> EntryAnalyzerFactory:
    """
    전역 팩토리 인스턴스 조회 (싱글톤)
    
    Returns:
        전역 EntryAnalyzerFactory 인스턴스
    """
    global _global_factory
    
    if _global_factory is None:
        _global_factory = EntryAnalyzerFactory()
    
    return _global_factory


def reset_global_factory() -> None:
    """전역 팩토리 초기화"""
    global _global_factory
    
    if _global_factory:
        _global_factory.clear_instances()
        _global_factory = None


# 편의 함수들
def get_analyzer(framework_name: str) -> Optional[BaseEntryAnalyzer]:
    """분석기 조회 편의 함수"""
    return get_global_factory().get_analyzer(framework_name)


def get_available_analyzers() -> List[str]:
    """사용 가능한 분석기 목록 조회 편의 함수"""
    return get_global_factory().get_available_analyzers()


def load_analyzers_from_config(project_name: str) -> List[BaseEntryAnalyzer]:
    """설정에서 분석기 로드 편의 함수"""
    return get_global_factory().load_analyzers_from_config(project_name)


def get_analyzers_for_file(file_path: str, content: str) -> List[BaseEntryAnalyzer]:
    """파일용 분석기 조회 편의 함수"""
    return get_global_factory().get_analyzers_for_file(file_path, content)


# 사용 예시
if __name__ == "__main__":
    # 팩토리 테스트
    factory = EntryAnalyzerFactory()
    
    # 사용 가능한 분석기 목록
    print("사용 가능한 분석기:", factory.get_available_analyzers())
    
    # Spring 분석기 조회
    spring_analyzer = factory.get_analyzer('spring')
    if spring_analyzer:
        print(f"Spring 분석기 로드 성공: {spring_analyzer.get_framework_name()}")
    
    # 분석기 정보 조회
    analyzer_info = factory.get_all_analyzer_info()
    for framework, info in analyzer_info.items():
        print(f"{framework}: {info['class_name']}")
    
    # 팩토리 통계
    stats = factory.get_factory_stats()
    print(f"팩토리 통계: {stats}")
