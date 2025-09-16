"""
SourceAnalyzer 데이터 검증 공통 유틸리티 모듈
- 입력 파라미터 검증
- 파일 존재 여부 확인
- 데이터 타입 검증
- 비즈니스 규칙 검증
"""

import os
import re
from typing import Optional, List, Dict, Any, Union, Callable
from .logger import app_logger, handle_error


class ValidationUtils:
    """데이터 검증 관련 공통 유틸리티 클래스"""
    
    @staticmethod
    def is_valid_project_name(project_name: str) -> bool:
        """
        프로젝트명 유효성 검증
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            유효성 여부 (True/False)
        """
        if not project_name or not isinstance(project_name, str):
            return False
        
        # 프로젝트명 규칙: 영문자, 숫자, 하이픈, 언더스코어만 허용
        try:
            pattern = r'^[a-zA-Z0-9_-]+$'
            return bool(re.match(pattern, project_name))
        except RecursionError:
            # Recursion limit 초과시 간단한 fallback 검증
            from util.logger import info
            info(f"RecursionError in regex validation, using fallback for: {project_name}")
            # 간단한 문자 검사로 fallback
            allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')
            return all(c in allowed_chars for c in project_name)
    
    @staticmethod
    def is_valid_file_path(file_path: str) -> bool:
        """
        파일 경로 유효성 검증
        
        Args:
            file_path: 파일 경로
            
        Returns:
            유효성 여부 (True/False)
        """
        if not file_path or not isinstance(file_path, str):
            return False
        
        try:
            # 경로가 유효한지 확인 (공통함수 사용)
            from .file_utils import FileUtils
            file_info = FileUtils.get_file_info(file_path)
            return file_info['exists'] or file_info['is_valid_path']
        except Exception:
            return False
    
    @staticmethod
    def is_valid_file_type(file_type: str) -> bool:
        """
        파일 타입 유효성 검증
        
        Args:
            file_type: 파일 타입
            
        Returns:
            유효성 여부 (True/False)
        """
        valid_types = ['java', 'xml', 'jsp', 'sql', 'csv', 'yaml', 'properties', 'txt', 'json', 'unknown']
        return file_type in valid_types
    
    @staticmethod
    def is_valid_component_type(component_type: str) -> bool:
        """
        컴포넌트 타입 유효성 검증
        
        Args:
            component_type: 컴포넌트 타입
            
        Returns:
            유효성 여부 (True/False)
        """
        valid_types = [
            'JSP', 'METHOD', 'SQL_SELECT', 'SQL_INSERT', 'SQL_UPDATE', 
            'SQL_DELETE', 'SQL_MERGE', 'TABLE', 'COLUMN', 'CLASS'
        ]
        return component_type in valid_types
    
    @staticmethod
    def is_valid_relationship_type(rel_type: str) -> bool:
        """
        관계 타입 유효성 검증
        
        Args:
            rel_type: 관계 타입
            
        Returns:
            유효성 여부 (True/False)
        """
        valid_types = [
            'CALL_QUERY', 'CALL_METHOD', 'USE_TABLE', 'FK', 'PK',
            'JOIN_EXPLICIT', 'JOIN_IMPLICIT', 'QUERY_TABLE'
        ]
        return rel_type in valid_types
    
    @staticmethod
    def is_valid_hash_value(hash_value: str, algorithm: str = 'md5') -> bool:
        """
        해시값 유효성 검증
        
        Args:
            hash_value: 해시값
            algorithm: 해시 알고리즘
            
        Returns:
            유효성 여부 (True/False)
        """
        if not hash_value or not isinstance(hash_value, str):
            return False
        
        # 16진수 문자열인지 확인
        if not re.match(r'^[a-fA-F0-9]+$', hash_value):
            return False
        
        # 알고리즘별 길이 확인
        expected_lengths = {
            'md5': 32,
            'sha1': 40,
            'sha256': 64
        }
        
        expected_length = expected_lengths.get(algorithm.lower(), 32)
        return len(hash_value) == expected_length
    
    @staticmethod
    def is_valid_line_number(line_number: Union[int, str]) -> bool:
        """
        라인 번호 유효성 검증
        
        Args:
            line_number: 라인 번호
            
        Returns:
            유효성 여부 (True/False)
        """
        try:
            line_num = int(line_number)
            return line_num > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_confidence(confidence: Union[float, int]) -> bool:
        """
        신뢰도 값 유효성 검증
        
        Args:
            confidence: 신뢰도 값 (0.0 ~ 1.0)
            
        Returns:
            유효성 여부 (True/False)
        """
        try:
            conf = float(confidence)
            return 0.0 <= conf <= 1.0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_boolean(value: Union[str, bool, int]) -> bool:
        """
        불린 값 유효성 검증
        
        Args:
            value: 검증할 값
            
        Returns:
            유효성 여부 (True/False)
        """
        if isinstance(value, bool):
            return True
        
        if isinstance(value, str):
            return value.upper() in ['Y', 'N', 'TRUE', 'FALSE', 'YES', 'NO', '1', '0']
        
        if isinstance(value, int):
            return value in [0, 1]
        
        return False
    
    @staticmethod
    def normalize_boolean(value: Union[str, bool, int]) -> str:
        """
        불린 값을 Y/N으로 정규화
        
        Args:
            value: 정규화할 값
            
        Returns:
            정규화된 값 (Y/N)
        """
        if isinstance(value, bool):
            return 'Y' if value else 'N'
        
        if isinstance(value, str):
            upper_value = value.upper()
            if upper_value in ['Y', 'TRUE', 'YES', '1']:
                return 'Y'
            elif upper_value in ['N', 'FALSE', 'NO', '0']:
                return 'N'
        
        if isinstance(value, int):
            return 'Y' if value == 1 else 'N'
        
        return 'N'  # 기본값
    
    @staticmethod
    def validate_file_exists(file_path: str) -> bool:
        """
        파일 존재 여부 확인
        
        Args:
            file_path: 파일 경로
            
        Returns:
            파일 존재 여부 (True/False)
        """
        return os.path.exists(file_path) and os.path.isfile(file_path)
    
    @staticmethod
    def validate_directory_exists(directory_path: str) -> bool:
        """
        디렉토리 존재 여부 확인
        
        Args:
            directory_path: 디렉토리 경로
            
        Returns:
            디렉토리 존재 여부 (True/False)
        """
        return os.path.exists(directory_path) and os.path.isdir(directory_path)
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """
        필수 필드 존재 여부 검증
        
        Args:
            data: 검증할 데이터 딕셔너리
            required_fields: 필수 필드 리스트
            
        Returns:
            누락된 필드 리스트
        """
        missing_fields = []
        
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                missing_fields.append(field)
        
        return missing_fields
    
    @staticmethod
    def validate_data_types(data: Dict[str, Any], type_schema: Dict[str, type]) -> List[str]:
        """
        데이터 타입 검증
        
        Args:
            data: 검증할 데이터 딕셔너리
            type_schema: 필드별 타입 스키마
            
        Returns:
            타입 오류가 있는 필드 리스트
        """
        type_errors = []
        
        for field, expected_type in type_schema.items():
            if field in data:
                value = data[field]
                if not isinstance(value, expected_type):
                    type_errors.append(f"{field}: expected {expected_type.__name__}, got {type(value).__name__}")
        
        return type_errors
    
    @staticmethod
    def validate_string_length(value: str, min_length: int = 0, max_length: int = None) -> bool:
        """
        문자열 길이 검증
        
        Args:
            value: 검증할 문자열
            min_length: 최소 길이
            max_length: 최대 길이
            
        Returns:
            유효성 여부 (True/False)
        """
        if not isinstance(value, str):
            return False
        
        length = len(value)
        
        if length < min_length:
            return False
        
        if max_length is not None and length > max_length:
            return False
        
        return True
    
    @staticmethod
    def validate_numeric_range(value: Union[int, float], min_value: float = None, max_value: float = None) -> bool:
        """
        숫자 범위 검증
        
        Args:
            value: 검증할 숫자
            min_value: 최소값
            max_value: 최대값
            
        Returns:
            유효성 여부 (True/False)
        """
        try:
            num_value = float(value)
            
            if min_value is not None and num_value < min_value:
                return False
            
            if max_value is not None and num_value > max_value:
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_regex_pattern(value: str, pattern: str) -> bool:
        """
        정규식 패턴 검증
        
        Args:
            value: 검증할 문자열
            pattern: 정규식 패턴
            
        Returns:
            유효성 여부 (True/False)
        """
        if not isinstance(value, str):
            return False
        
        try:
            return bool(re.match(pattern, value))
        except re.error as e:
            handle_error(e, f"잘못된 정규식 패턴: {pattern}")
            return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        이메일 주소 유효성 검증
        
        Args:
            email: 이메일 주소
            
        Returns:
            유효성 여부 (True/False)
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return ValidationUtils.validate_regex_pattern(email, pattern)
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        URL 유효성 검증
        
        Args:
            url: URL
            
        Returns:
            유효성 여부 (True/False)
        """
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return ValidationUtils.validate_regex_pattern(url, pattern)
    
    @staticmethod
    def validate_java_class_name(class_name: str) -> bool:
        """
        Java 클래스명 유효성 검증
        
        Args:
            class_name: Java 클래스명
            
        Returns:
            유효성 여부 (True/False)
        """
        # Java 클래스명 규칙: 영문자로 시작, 영문자/숫자/언더스코어/달러사인 허용
        pattern = r'^[a-zA-Z][a-zA-Z0-9_$]*$'
        return ValidationUtils.validate_regex_pattern(class_name, pattern)
    
    @staticmethod
    def validate_sql_identifier(identifier: str) -> bool:
        """
        SQL 식별자 유효성 검증
        
        Args:
            identifier: SQL 식별자
            
        Returns:
            유효성 여부 (True/False)
        """
        # SQL 식별자 규칙: 영문자로 시작, 영문자/숫자/언더스코어 허용
        pattern = r'^[a-zA-Z][a-zA-Z0-9_]*$'
        return ValidationUtils.validate_regex_pattern(identifier, pattern)
    
    @staticmethod
    def validate_comprehensive(data: Dict[str, Any], validation_rules: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        종합적인 데이터 검증
        
        Args:
            data: 검증할 데이터 딕셔너리
            validation_rules: 검증 규칙 딕셔너리
            
        Returns:
            검증 결과 딕셔너리 (필드별 오류 리스트)
        """
        errors = {}
        
        for field, rules in validation_rules.items():
            field_errors = []
            value = data.get(field)
            
            # 필수 필드 검증
            if rules.get('required', False) and (value is None or value == ''):
                field_errors.append(f"{field} is required")
                continue
            
            # 값이 없으면 다른 검증 스킵
            if value is None or value == '':
                continue
            
            # 타입 검증
            expected_type = rules.get('type')
            if expected_type and not isinstance(value, expected_type):
                field_errors.append(f"{field} must be {expected_type.__name__}")
                continue
            
            # 문자열 길이 검증
            if isinstance(value, str):
                min_length = rules.get('min_length')
                max_length = rules.get('max_length')
                if not ValidationUtils.validate_string_length(value, min_length, max_length):
                    field_errors.append(f"{field} length must be between {min_length or 0} and {max_length or 'unlimited'}")
            
            # 숫자 범위 검증
            if isinstance(value, (int, float)):
                min_value = rules.get('min_value')
                max_value = rules.get('max_value')
                if not ValidationUtils.validate_numeric_range(value, min_value, max_value):
                    field_errors.append(f"{field} must be between {min_value or 'unlimited'} and {max_value or 'unlimited'}")
            
            # 정규식 패턴 검증
            pattern = rules.get('pattern')
            if pattern and not ValidationUtils.validate_regex_pattern(str(value), pattern):
                field_errors.append(f"{field} format is invalid")
            
            # 커스텀 검증 함수
            custom_validator = rules.get('validator')
            if custom_validator and not custom_validator(value):
                field_errors.append(f"{field} validation failed")
            
            if field_errors:
                errors[field] = field_errors
        
        return errors


# 편의 함수들
def is_valid_project_name(project_name: str) -> bool:
    """프로젝트명 유효성 검증 편의 함수"""
    return ValidationUtils.is_valid_project_name(project_name)


def is_valid_file_path(file_path: str) -> bool:
    """파일 경로 유효성 검증 편의 함수"""
    return ValidationUtils.is_valid_file_path(file_path)


def validate_file_exists(file_path: str) -> bool:
    """파일 존재 여부 확인 편의 함수"""
    return ValidationUtils.validate_file_exists(file_path)


def validate_directory_exists(directory_path: str) -> bool:
    """디렉토리 존재 여부 확인 편의 함수"""
    return ValidationUtils.validate_directory_exists(directory_path)


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """필수 필드 존재 여부 검증 편의 함수"""
    return ValidationUtils.validate_required_fields(data, required_fields)
