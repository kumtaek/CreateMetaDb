"""
SourceAnalyzer 설정 파일 처리 공통 유틸리티 모듈
- YAML 파일 읽기
- 설정 값 검증
- 프로젝트별 설정 우선순위 처리
"""

import yaml
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from .logger import app_logger, handle_error
from .file_utils import FileUtils


class ConfigUtils:
    """설정 파일 처리 관련 공통 유틸리티 클래스"""
    
    def __init__(self, base_config_path: str = "config"):
        """
        설정 유틸리티 초기화
        
        Args:
            base_config_path: 기본 설정 파일 경로
        """
        self.base_config_path = base_config_path
    
    def load_yaml_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """
        YAML 설정 파일 로드
        
        Args:
            config_path: 설정 파일 경로
            
        Returns:
            설정 딕셔너리 또는 None (실패시)
        """
        try:
            content = FileUtils.read_file(config_path)
            if content is None:
                return None
            
            config = yaml.safe_load(content)
            app_logger.debug(f"YAML 설정 파일 로드 성공: {config_path}")
            return config
            
        except yaml.YAMLError as e:
            handle_error(e, f"YAML 파싱 오류: {config_path}")
            return None
        except Exception as e:
            handle_error(e, f"설정 파일 로드 실패: {config_path}")
            return None
    
    def save_yaml_config(self, config_path: str, config: Dict[str, Any]) -> bool:
        """
        YAML 설정 파일 저장
        
        Args:
            config_path: 설정 파일 경로
            config: 저장할 설정 딕셔너리
            
        Returns:
            저장 성공 여부 (True/False)
        """
        try:
            yaml_content = yaml.dump(config, default_flow_style=False, allow_unicode=True, indent=2)
            success = FileUtils.write_file(config_path, yaml_content)
            
            if success:
                app_logger.debug(f"YAML 설정 파일 저장 성공: {config_path}")
            return success
            
        except Exception as e:
            handle_error(e, f"설정 파일 저장 실패: {config_path}")
            return False
    
    def load_project_config(self, project_name: str, config_filename: str) -> Optional[Dict[str, Any]]:
        """
        프로젝트별 설정 파일 로드 (우선순위 적용)
        
        우선순위:
        1. ./projects/{project_name}/config/{config_filename}
        2. ./config/{config_filename}
        
        Args:
            project_name: 프로젝트명
            config_filename: 설정 파일명
            
        Returns:
            설정 딕셔너리 또는 None (실패시)
        """
        # 프로젝트별 설정 파일 경로 (크로스플랫폼 대응)
        from util import PathUtils
        path_utils = PathUtils()
        project_config_path = path_utils.join_path("projects", project_name, "config", config_filename)
        base_config_path = path_utils.join_path(self.base_config_path, config_filename)
        
        # 프로젝트별 설정이 있으면 우선 사용
        if os.path.exists(project_config_path):
            config = self.load_yaml_config(project_config_path)
            if config:
                app_logger.debug(f"프로젝트별 설정 사용: {project_config_path}")
                return config
        
        # 기본 설정 사용
        if os.path.exists(base_config_path):
            config = self.load_yaml_config(base_config_path)
            if config:
                app_logger.debug(f"기본 설정 사용: {base_config_path}")
                return config
        
        app_logger.warning(f"설정 파일을 찾을 수 없습니다: {config_filename}")
        return None
    
    def merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        설정 딕셔너리 병합 (override_config가 우선)
        
        Args:
            base_config: 기본 설정
            override_config: 우선 적용할 설정
            
        Returns:
            병합된 설정 딕셔너리
        """
        merged = base_config.copy()
        
        for key, value in override_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self.merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def get_config_value(self, config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """
        중첩된 설정에서 값을 가져오기 (점 표기법 지원)
        
        Args:
            config: 설정 딕셔너리
            key_path: 키 경로 (예: "database.host", "parser.java_keywords")
            default: 기본값
            
        Returns:
            설정 값 또는 기본값
        """
        try:
            keys = key_path.split('.')
            value = config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            handle_error(e, f"설정 값 조회 실패: {key_path}")
            return default
    
    def set_config_value(self, config: Dict[str, Any], key_path: str, value: Any) -> bool:
        """
        중첩된 설정에 값을 설정하기 (점 표기법 지원)
        
        Args:
            config: 설정 딕셔너리
            key_path: 키 경로 (예: "database.host", "parser.java_keywords")
            value: 설정할 값
            
        Returns:
            설정 성공 여부 (True/False)
        """
        try:
            keys = key_path.split('.')
            current = config
            
            # 마지막 키를 제외한 모든 키에 대해 딕셔너리 생성
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # 마지막 키에 값 설정
            current[keys[-1]] = value
            return True
            
        except Exception as e:
            handle_error(e, f"설정 값 설정 실패: {key_path}")
            return False
    
    def validate_config(self, config: Dict[str, Any], required_keys: List[str]) -> bool:
        """
        설정 검증 (필수 키 존재 여부 확인)
        
        Args:
            config: 검증할 설정 딕셔너리
            required_keys: 필수 키 리스트 (점 표기법 지원)
            
        Returns:
            검증 성공 여부 (True/False)
        """
        try:
            for key_path in required_keys:
                value = self.get_config_value(config, key_path)
                if value is None:
                    app_logger.error(f"필수 설정 키가 누락되었습니다: {key_path}")
                    return False
            
            app_logger.debug("설정 검증 성공")
            return True
            
        except Exception as e:
            handle_error(e, "설정 검증 실패")
            return False
    
    def load_parser_config(self, project_name: str, parser_type: str) -> Optional[Dict[str, Any]]:
        """
        파서별 설정 파일 로드
        
        Args:
            project_name: 프로젝트명
            parser_type: 파서 타입 (java, xml, jsp, sql, csv, yaml 등)
            
        Returns:
            파서 설정 딕셔너리 또는 None (실패시)
        """
        config_filename = f"{parser_type}_keyword.yaml"
        return self.load_project_config(project_name, config_filename)
    
    def load_system_config(self, config_filename: str = "config.yaml") -> Optional[Dict[str, Any]]:
        """
        시스템 설정 파일 로드
        
        Args:
            config_filename: 설정 파일명
            
        Returns:
            시스템 설정 딕셔너리 또는 None (실패시)
        """
        config_path = f"{self.base_config_path}/{config_filename}"
        return self.load_yaml_config(config_path)
    
    def load_logging_config(self) -> Optional[Dict[str, Any]]:
        """
        로깅 설정 파일 로드
        
        Returns:
            로깅 설정 딕셔너리 또는 None (실패시)
        """
        return self.load_system_config("logging.yaml")
    
    def load_target_source_config(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        분석 대상 소스 설정 파일 로드
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            분석 대상 소스 설정 딕셔너리 또는 None (실패시)
        """
        return self.load_project_config(project_name, "target_source_config.yaml")
    
    def get_file_filters(self, project_name: str) -> Dict[str, List[str]]:
        """
        파일 필터 설정 가져오기
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            파일 필터 딕셔너리
        """
        config = self.load_target_source_config(project_name)
        if not config:
            return {}
        
        return config.get('file_filters', {})
    
    def get_include_patterns(self, project_name: str, file_type: str) -> List[str]:
        """
        특정 파일 타입의 포함 패턴 가져오기
        
        Args:
            project_name: 프로젝트명
            file_type: 파일 타입
            
        Returns:
            포함 패턴 리스트
        """
        file_filters = self.get_file_filters(project_name)
        return file_filters.get(file_type, {}).get('include', [])
    
    def get_exclude_patterns(self, project_name: str, file_type: str) -> List[str]:
        """
        특정 파일 타입의 제외 패턴 가져오기
        
        Args:
            project_name: 프로젝트명
            file_type: 파일 타입
            
        Returns:
            제외 패턴 리스트
        """
        file_filters = self.get_file_filters(project_name)
        return file_filters.get(file_type, {}).get('exclude', [])
    
    def create_default_config(self, config_path: str, config_type: str) -> bool:
        """
        기본 설정 파일 생성
        
        Args:
            config_path: 설정 파일 경로
            config_type: 설정 타입 (system, parser, target_source 등)
            
        Returns:
            생성 성공 여부 (True/False)
        """
        default_configs = {
            'system': {
                'database': {
                    'path': 'metadata.db',
                    'timeout': 30
                },
                'logging': {
                    'level': 'INFO',
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
                },
                'analysis': {
                    'max_file_size': 10485760,  # 10MB
                    'supported_extensions': ['.java', '.xml', '.jsp', '.sql', '.csv']
                }
            },
            'target_source': {
                'file_filters': {
                    'java': {
                        'include': ['**/*.java'],
                        'exclude': ['**/test/**', '**/Test.java']
                    },
                    'xml': {
                        'include': ['**/*.xml'],
                        'exclude': ['**/test/**']
                    },
                    'jsp': {
                        'include': ['**/*.jsp'],
                        'exclude': ['**/test/**']
                    }
                }
            }
        }
        
        if config_type in default_configs:
            return self.save_yaml_config(config_path, default_configs[config_type])
        
        app_logger.error(f"지원하지 않는 설정 타입: {config_type}")
        return False


# 편의 함수들
def load_yaml_config(config_path: str) -> Optional[Dict[str, Any]]:
    """YAML 설정 파일 로드 편의 함수"""
    config_utils = ConfigUtils()
    return config_utils.load_yaml_config(config_path)


def load_project_config(project_name: str, config_filename: str) -> Optional[Dict[str, Any]]:
    """프로젝트별 설정 파일 로드 편의 함수"""
    config_utils = ConfigUtils()
    return config_utils.load_project_config(project_name, config_filename)


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """설정 값 조회 편의 함수"""
    config_utils = ConfigUtils()
    return config_utils.get_config_value(config, key_path, default)
