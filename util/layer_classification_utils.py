"""
Layer 분류 유틸리티
- Java 클래스들을 아키텍처 레이어로 분류하는 공통 함수
- 콜체인리포트와 아키텍처리포트에서 공통 사용
"""

import os
import re
from typing import List, Dict, Any, Optional, Set
from util.logger import app_logger, handle_error
from util.path_utils import PathUtils


class LayerClassificationUtils:
    """Layer 분류 유틸리티 클래스"""
    
    def __init__(self):
        """초기화"""
        self.path_utils = PathUtils()
        self._layer_patterns_cache = None
    
    def get_layer_classification_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """
        설정 파일에서 레이어 분류 패턴 로드 (캐시 사용)
        
        Returns:
            레이어별 분류 패턴 딕셔너리
        """
        try:
            # 캐시된 패턴이 있으면 반환
            if self._layer_patterns_cache is not None:
                return self._layer_patterns_cache
            
            import yaml
            
            # 설정 파일 경로 (공통함수 사용)
            config_path = self.path_utils.get_parser_config_path("java")
            
            if not self.path_utils.exists(config_path):
                app_logger.warning(f"설정 파일이 존재하지 않습니다: {config_path}, 기본 패턴 사용")
                self._layer_patterns_cache = self._get_default_layer_patterns()
                return self._layer_patterns_cache
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            layer_classification = config.get('layer_classification', {})
            
            # 기본 레이어 패턴이 없으면 기본값 사용
            if not layer_classification:
                app_logger.warning("설정 파일에 layer_classification이 없습니다, 기본 패턴 사용")
                self._layer_patterns_cache = self._get_default_layer_patterns()
            else:
                self._layer_patterns_cache = layer_classification
            
            app_logger.debug(f"레이어 분류 패턴 로드 완료: {list(self._layer_patterns_cache.keys())}")
            return self._layer_patterns_cache
            
        except Exception as e:
            app_logger.warning(f"설정 파일 로드 실패: {e}, 기본 패턴 사용")
            self._layer_patterns_cache = self._get_default_layer_patterns()
            return self._layer_patterns_cache
    
    def _get_default_layer_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """기본 레이어 분류 패턴 (설정 파일 로드 실패 시 사용)"""
        return {
            'controller': {
                'suffixes': ['controller', 'ctrl', 'servlet'],
                'keywords': ['controller', 'servlet', 'Servlet', '@Controller'],
                'folder_patterns': ['*controller*', '*ctrl*', '*web*', '*api*', '*servlet*']
            },
            'service': {
                'suffixes': ['service', 'svc', 'manager', 'facade'],
                'keywords': ['service', 'business', 'logic', 'manager', 'facade'],
                'folder_patterns': ['*service*', '*business*', '*logic*', '*manager*', '*facade*']
            },
            'repository': {
                'suffixes': ['dao', 'repository', 'repo', 'mapper'],
                'keywords': ['dao', 'repository', 'mapper', 'data'],
                'folder_patterns': ['*dao*', '*repository*', '*mapper*', '*data*']
            },
            'model': {
                'suffixes': ['entity', 'model', 'vo', 'dto', 'domain'],
                'keywords': ['entity', 'model', 'vo', 'dto', 'domain', 'bean'],
                'folder_patterns': ['*model*', '*entity*', '*vo*', '*dto*', '*domain*', '*bean*', '*enums*']
            },
            'util': {
                'suffixes': ['util', 'utils', 'helper', 'common'],
                'keywords': ['util', 'helper', 'common', 'tool'],
                'folder_patterns': ['*util*', '*helper*', '*common*', '*tool*']
            }
        }
    
    def classify_component_by_patterns(self, component_name: str, file_path: str = "", file_name: str = "", 
                                     layer_patterns: Optional[Dict[str, Dict[str, List[str]]]] = None) -> Optional[str]:
        """
        컴포넌트를 패턴에 따라 레이어로 분류
        
        Args:
            component_name: 컴포넌트명 (클래스명, 메서드명 등)
            file_path: 파일 경로
            file_name: 파일명
            layer_patterns: 레이어 분류 패턴 (None이면 설정 파일에서 로드)
            
        Returns:
            분류된 레이어명 (CONTROLLER, SERVICE, REPOSITORY, MODEL, UTIL) 또는 None
        """
        try:
            if layer_patterns is None:
                layer_patterns = self.get_layer_classification_patterns()
            
            # 레이어 우선순위 순서 (repository가 가장 우선)
            layer_order = ['repository', 'controller', 'service', 'model', 'util']
            
            for layer_name in layer_order:
                if layer_name not in layer_patterns:
                    continue
                
                patterns = layer_patterns[layer_name]
                if self._matches_layer_patterns(component_name, file_path, file_name, patterns):
                    # 레이어 매핑 변경
                    if layer_name == 'repository':
                        app_logger.debug(f"컴포넌트 분류: {component_name} -> MODEL (기존 REPOSITORY)")
                        return 'MODEL'
                    elif layer_name == 'model':
                        app_logger.debug(f"컴포넌트 분류: {component_name} -> ETC (기존 MODEL)")
                        return 'ETC'
                    else:
                        app_logger.debug(f"컴포넌트 분류: {component_name} -> {layer_name.upper()}")
                        return layer_name.upper()
            
            # 분류되지 않은 경우 None 반환
            app_logger.debug(f"컴포넌트 분류 실패: {component_name}")
            return None
            
        except Exception as e:
            # USER RULES: exception발생시 handle_error()로 exit()
            handle_error(e, f"컴포넌트 레이어 분류 실패: {component_name}")
            return None
    
    def _matches_layer_patterns(self, component_name: str, file_path: str, file_name: str, 
                              patterns: Dict[str, List[str]]) -> bool:
        """
        컴포넌트가 특정 레이어 패턴과 매칭되는지 확인
        
        Args:
            component_name: 컴포넌트명
            file_path: 파일 경로
            file_name: 파일명
            patterns: 레이어 패턴
            
        Returns:
            매칭 여부
        """
        try:
            suffixes = patterns.get('suffixes', [])
            keywords = patterns.get('keywords', [])
            folder_patterns = patterns.get('folder_patterns', [])
            
            # 1순위: folder_patterns 매칭 (폴더 구조가 가장 정확한 분류)
            if folder_patterns:
                for pattern in folder_patterns:
                    # 와일드카드 패턴을 정규식으로 변환
                    normalized_path = self.path_utils.normalize_path_separator(file_path, 'unix')
                    regex_pattern = pattern.replace('*', '.*')
                    if re.search(regex_pattern, normalized_path, re.IGNORECASE):
                        return True
            
            # 2순위: 클래스명 keyword 매칭
            if keywords:
                for keyword in keywords:
                    if keyword.lower() in component_name.lower():
                        return True
            
            # 3순위: 파일명 패턴 매칭
            if suffixes:
                for suffix in suffixes:
                    if file_name.lower().endswith(suffix.lower() + '.java'):
                        return True
            
            # 4순위: 클래스명 suffix 패턴 매칭
            if suffixes:
                for suffix in suffixes:
                    if component_name.lower().endswith(suffix.lower()):
                        return True
            
            return False
            
        except Exception as e:
            # USER RULES: exception발생시 handle_error()로 exit()
            handle_error(e, f"레이어 패턴 매칭 실패: {component_name}")
            return False
    
    def classify_multiple_components(self, components: List[Dict[str, Any]], 
                                   layer_patterns: Optional[Dict[str, Dict[str, List[str]]]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        여러 컴포넌트들을 레이어별로 분류
        
        Args:
            components: 컴포넌트 리스트 (각 요소는 component_name, file_path, file_name 포함)
            layer_patterns: 레이어 분류 패턴
            
        Returns:
            레이어별로 분류된 컴포넌트 딕셔너리
        """
        try:
            if layer_patterns is None:
                layer_patterns = self.get_layer_classification_patterns()
            
            # 레이어별 결과 딕셔너리 초기화
            layer_results = {}
            layer_order = ['model', 'controller', 'service', 'repository', 'util']
            for layer_name in layer_order:
                layer_results[layer_name] = []
            
            # 분류되지 않은 컴포넌트들
            unclassified = []
            processed_components = set()
            
            # 우선순위 순서로 분류 (model 우선)
            for layer_name in layer_order:
                if layer_name not in layer_patterns:
                    continue
                
                patterns = layer_patterns[layer_name]
                
                for component in components:
                    component_name = component.get('component_name', '')
                    
                    # 이미 분류된 컴포넌트는 건너뛰기
                    if component_name in processed_components:
                        continue
                    
                    file_path = component.get('file_path', '')
                    file_name = component.get('file_name', '')
                    
                    if self._matches_layer_patterns(component_name, file_path, file_name, patterns):
                        layer_results[layer_name].append(component)
                        processed_components.add(component_name)
            
            # 분류되지 않은 컴포넌트들 수집
            for component in components:
                component_name = component.get('component_name', '')
                if component_name not in processed_components:
                    unclassified.append(component)
            
            # 분류되지 않은 컴포넌트들을 기타로 추가
            if unclassified:
                layer_results['etc'] = unclassified
            
            app_logger.info(f"컴포넌트 레이어 분류 완료: {dict((k, len(v)) for k, v in layer_results.items())}")
            return layer_results
            
        except Exception as e:
            handle_error(e, "다중 컴포넌트 레이어 분류 실패")
            return {'model': [], 'controller': [], 'service': [], 'repository': [], 'util': [], 'etc': []}
    
    def get_component_layer(self, component_type: str, component_name: str = "", 
                          file_path: str = "", file_name: str = "") -> str:
        """
        컴포넌트 타입과 패턴을 기반으로 레이어 결정
        
        Layer 분류 기준:
        - FRONTEND: JSP/JSX/Vue 파일
        - API_ENTRY: API_URL 컴포넌트 (프론트엔드에서 호출하는 API 엔드포인트)
        - CONTROLLER: HTTP 요청 처리, API 엔드포인트 (*Controller, *Servlet, @Controller)
        - SERVICE: 비즈니스 로직 처리 (*Service, *Manager, *Facade)
        - REPOSITORY: 데이터 접근 로직 (*Mapper, *Repository, *DAO)
        - MODEL: 데이터 모델 (*Entity, *Model, *VO, *DTO, *Domain)
        - QUERY: SQL 쿼리 (SQL_SELECT, SQL_INSERT, SQL_UPDATE, SQL_DELETE, QUERY)
        - TABLE: 데이터베이스 테이블
        - UTIL: 유틸리티 클래스 (*Util, *Helper, *Common)
        
        Args:
            component_type: 컴포넌트 타입 (CLASS, METHOD, SQL_*, QUERY, TABLE, API_URL 등)
            component_name: 컴포넌트명
            file_path: 파일 경로
            file_name: 파일명
            
        Returns:
            레이어명 (FRONTEND, API_ENTRY, CONTROLLER, SERVICE, REPOSITORY, MODEL, QUERY, TABLE, UTIL)
        """
        try:
            # 컴포넌트 타입별 기본 레이어 매핑
            type_layer_mapping = {
                'SQL_SELECT': 'QUERY',
                'SQL_INSERT': 'QUERY', 
                'SQL_UPDATE': 'QUERY',
                'SQL_DELETE': 'QUERY',
                'QUERY': 'QUERY',
                'TABLE': 'TABLE',
                'COLUMN': 'TABLE',
                'API_URL': 'API_ENTRY',
                'JSP': 'FRONTEND'
            }
            
            # 명시적 타입 매핑이 있으면 우선 사용
            if component_type in type_layer_mapping:
                return type_layer_mapping[component_type]
            
            # CLASS, METHOD 타입은 패턴 매칭으로 분류
            if component_type in ['CLASS', 'METHOD']:
                # 1. setter/getter 메서드는 ETC로 분류
                if component_type == 'METHOD' and self._is_setter_getter_method(component_name):
                    return 'ETC'
                
                classified_layer = self.classify_component_by_patterns(component_name, file_path, file_name)
                if classified_layer:
                    # REPOSITORY 레이어를 MODEL로 변경
                    if classified_layer == 'REPOSITORY':
                        return 'MODEL'
                    return classified_layer
                else:
                    # 분류되지 않은 경우 기본값
                    return 'APPLICATION'
            
            # 기타 타입들의 기본값
            return 'APPLICATION'
            
        except Exception as e:
            # USER RULES: exception발생시 handle_error()로 exit()
            handle_error(e, f"컴포넌트 레이어 결정 실패: {component_type}, {component_name}")
            return 'APPLICATION'
    
    def _is_setter_getter_method(self, method_name: str) -> bool:
        """
        setter/getter 메서드인지 확인
        
        Args:
            method_name: 메서드명
            
        Returns:
            setter/getter 메서드이면 True
        """
        try:
            # getter 패턴: get*, is*
            if (method_name.startswith('get') and len(method_name) > 3 and method_name[3].isupper()) or \
               (method_name.startswith('is') and len(method_name) > 2 and method_name[2].isupper()):
                return True
            
            # setter 패턴: set*
            if method_name.startswith('set') and len(method_name) > 3 and method_name[3].isupper():
                return True
                
            return False
            
        except Exception as e:
            # USER RULES: exception발생시 handle_error()로 exit()
            handle_error(e, f"setter/getter 메서드 확인 실패: {method_name}")
            return False


# 전역 인스턴스 (싱글톤 패턴)
_layer_classifier = None

def get_layer_classifier() -> LayerClassificationUtils:
    """Layer 분류 유틸리티 인스턴스 반환 (싱글톤)"""
    global _layer_classifier
    if _layer_classifier is None:
        _layer_classifier = LayerClassificationUtils()
    return _layer_classifier
