"""
컴포넌트 필터링 유틸리티
- 잘못된 파싱 결과 필터링
- 메타데이터 생성 품질 향상
- 기존 파서 로직에 영향 없음

USER RULES:
- 공통함수 사용 지향 (ConfigUtils, PathUtils 등)
- Exception 발생시 handle_error()로 Exit
- 크로스플랫폼 대응
- 하드코딩 금지
- 설정 파일 활용 (config/parser/java_keyword.yaml)
"""

import os
import re
from typing import List, Dict, Any, Optional, Set

from util.logger import app_logger, handle_error
from util.path_utils import PathUtils


class ComponentFilterUtils:
    """컴포넌트 필터링 유틸리티 클래스"""
    
    def __init__(self):
        """초기화 - USER RULES: 공통함수 사용"""
        try:
            self.path_utils = PathUtils()
            
            # 설정 파일 로드 (USER RULES: 하드코딩 금지)
            self._load_filter_configs()
            
        except Exception as e:
            # USER RULES: Exception 발생시 handle_error()로 Exit
            handle_error(e, "ComponentFilterUtils 초기화 실패")
    
    def _load_filter_configs(self):
        """필터링 설정 로드"""
        try:
            import yaml
            
            # USER RULES: 공통함수 사용 - PathUtils로 설정 파일 경로 생성
            java_config_file = self.path_utils.get_parser_config_path("java")
            
            # 설정 파일 로드 (USER RULES: 직접 yaml 로드)
            if not self.path_utils.exists(java_config_file):
                handle_error(Exception("Java 키워드 설정 파일이 존재하지 않음"), 
                           f"설정 파일을 찾을 수 없음: {java_config_file}")
            
            with open(java_config_file, 'r', encoding='utf-8') as f:
                self.java_config = yaml.safe_load(f)
            
            if not self.java_config:
                handle_error(Exception("Java 키워드 설정 파일 로드 실패"), 
                           f"설정 파일이 비어있거나 읽을 수 없음: {java_config_file}")
            
            # 필터링 패턴 컴파일 (성능 최적화)
            self._compile_filter_patterns()
            
            app_logger.debug("컴포넌트 필터링 설정 로드 완료")
            
        except Exception as e:
            handle_error(e, "필터링 설정 로드 실패")
    
    def _compile_filter_patterns(self):
        """필터링 패턴 컴파일 (성능 최적화)"""
        try:
            self.compiled_patterns = {}
            
            # 잘못된 메서드명 패턴 컴파일
            invalid_patterns = self.java_config.get('invalid_method_names', {})
            for pattern_name, pattern in invalid_patterns.items():
                if pattern and isinstance(pattern, str):
                    self.compiled_patterns[pattern_name] = re.compile(pattern)
            
            # HTTP 메서드 상수 집합 생성 (빠른 검색)
            self.http_methods = set(self.java_config.get('http_method_constants', []))
            
            # Java 기본 클래스 집합 생성
            self.java_core_classes = set(self.java_config.get('java_core_classes', []))
            
            # Java 예약어 집합 생성
            self.java_reserved_keywords = set(self.java_config.get('java_reserved_keywords', []))
            
            app_logger.debug(f"필터링 패턴 컴파일 완료: {len(self.compiled_patterns)}개 패턴")
            
        except Exception as e:
            handle_error(e, "필터링 패턴 컴파일 실패")
    
    def is_invalid_component_name(self, component_name: str, component_type: str = "METHOD") -> bool:
        """
        컴포넌트 이름이 유효하지 않은지 검사
        
        Args:
            component_name: 컴포넌트 이름
            component_type: 컴포넌트 타입 (METHOD, CLASS 등)
            
        Returns:
            True: 유효하지 않음 (필터링 대상)
            False: 유효함
        """
        try:
            if not component_name or not isinstance(component_name, str):
                return True
            
            # 1. HTTP 메서드 상수 필터링
            if component_name.upper() in self.http_methods:
                app_logger.debug(f"HTTP 메서드 상수 필터링: {component_name}")
                return True
            
            # 2. Java 기본 클래스 필터링 (METHOD 타입인 경우)
            if component_type == "METHOD" and component_name in self.java_core_classes:
                app_logger.debug(f"Java 기본 클래스 필터링: {component_name}")
                return True
            
            # 3. Java 예약어 필터링
            if component_name.lower() in self.java_reserved_keywords:
                app_logger.debug(f"Java 예약어 필터링: {component_name}")
                return True
            
            # 4. 패턴 기반 필터링
            for pattern_name, compiled_pattern in self.compiled_patterns.items():
                if compiled_pattern.match(component_name):
                    app_logger.debug(f"{pattern_name} 패턴 필터링: {component_name}")
                    return True
            
            # 모든 검사 통과
            return False
            
        except Exception as e:
            # USER RULES: Exception 발생시 handle_error()로 Exit
            handle_error(e, f"컴포넌트 이름 검증 실패: {component_name}")
    
    def filter_components(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        컴포넌트 리스트 필터링
        
        Args:
            components: 원본 컴포넌트 리스트
            
        Returns:
            필터링된 컴포넌트 리스트
        """
        try:
            if not components or not isinstance(components, list):
                return []
            
            filtered_components = []
            filtered_count = 0
            
            for component in components:
                if not isinstance(component, dict):
                    continue
                
                component_name = component.get('component_name', '')
                component_type = component.get('component_type', 'METHOD')
                
                # 유효하지 않은 컴포넌트 제외
                if self.is_invalid_component_name(component_name, component_type):
                    filtered_count += 1
                    app_logger.debug(f"컴포넌트 필터링: {component_name} ({component_type})")
                    continue
                
                # 유효한 컴포넌트만 포함
                filtered_components.append(component)
            
            app_logger.info(f"컴포넌트 필터링 완료: {filtered_count}개 제외, {len(filtered_components)}개 유지")
            return filtered_components
            
        except Exception as e:
            # USER RULES: Exception 발생시 handle_error()로 Exit
            handle_error(e, "컴포넌트 리스트 필터링 실패")
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """
        필터링 통계 정보 반환
        
        Returns:
            필터링 설정 통계
        """
        try:
            return {
                'http_methods_count': len(self.http_methods),
                'java_core_classes_count': len(self.java_core_classes),
                'java_reserved_keywords_count': len(self.java_reserved_keywords),
                'compiled_patterns_count': len(self.compiled_patterns),
                'config_loaded': bool(self.java_config)
            }
            
        except Exception as e:
            handle_error(e, "필터링 통계 정보 생성 실패")


# 전역 인스턴스 (싱글톤 패턴) - USER RULES: 공통함수 패턴 준수
_component_filter = None

def get_component_filter() -> ComponentFilterUtils:
    """컴포넌트 필터 유틸리티 인스턴스 반환 (싱글톤)"""
    global _component_filter
    try:
        if _component_filter is None:
            _component_filter = ComponentFilterUtils()
        return _component_filter
    except Exception as e:
        handle_error(e, "컴포넌트 필터 유틸리티 인스턴스 생성 실패")


# 편의 함수들 - USER RULES: 공통함수 패턴 준수
def is_invalid_component_name(component_name: str, component_type: str = "METHOD") -> bool:
    """컴포넌트 이름 유효성 검사 편의 함수"""
    try:
        filter_utils = get_component_filter()
        return filter_utils.is_invalid_component_name(component_name, component_type)
    except Exception as e:
        handle_error(e, f"컴포넌트 이름 검증 편의 함수 실패: {component_name}")


def filter_components(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """컴포넌트 리스트 필터링 편의 함수"""
    try:
        filter_utils = get_component_filter()
        return filter_utils.filter_components(components)
    except Exception as e:
        handle_error(e, "컴포넌트 리스트 필터링 편의 함수 실패")


def get_filter_statistics() -> Dict[str, Any]:
    """필터링 통계 정보 반환 편의 함수"""
    try:
        filter_utils = get_component_filter()
        return filter_utils.get_filter_statistics()
    except Exception as e:
        handle_error(e, "필터링 통계 정보 편의 함수 실패")
