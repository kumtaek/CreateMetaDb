"""
SourceAnalyzer 해시값 생성 및 변경감지 공통 유틸리티 모듈
- 해시값 생성
- 변경감지
- 파일 해시 비교
"""

import hashlib
import os
from typing import Optional, Dict, Any, List
from .logger import app_logger, handle_error


class HashUtils:
    """해시값 생성 및 변경감지 관련 공통 유틸리티 클래스"""
    
    @staticmethod
    def generate_md5(content: str) -> str:
        """
        MD5 해시값 생성
        
        Args:
            content: 해시를 생성할 문자열
            
        Returns:
            MD5 해시값 (32자리 16진수 문자열)
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_sha1(content: str) -> str:
        """
        SHA1 해시값 생성
        
        Args:
            content: 해시를 생성할 문자열
            
        Returns:
            SHA1 해시값 (40자리 16진수 문자열)
        """
        return hashlib.sha1(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_sha256(content: str) -> str:
        """
        SHA256 해시값 생성
        
        Args:
            content: 해시를 생성할 문자열
            
        Returns:
            SHA256 해시값 (64자리 16진수 문자열)
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_file_hash(file_path: str, algorithm: str = 'md5') -> Optional[str]:
        """
        파일의 해시값 생성
        
        Args:
            file_path: 파일 경로
            algorithm: 해시 알고리즘 (md5, sha1, sha256)
            
        Returns:
            파일 해시값 또는 None (실패시)
        """
        try:
            if algorithm.lower() == 'md5':
                hash_obj = hashlib.md5()
            elif algorithm.lower() == 'sha1':
                hash_obj = hashlib.sha1()
            elif algorithm.lower() == 'sha256':
                hash_obj = hashlib.sha256()
            else:
                app_logger.error(f"지원하지 않는 해시 알고리즘: {algorithm}")
                return None
            
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            
            hash_value = hash_obj.hexdigest()
            app_logger.debug(f"파일 해시 생성 성공: {file_path} ({algorithm})")
            return hash_value
            
        except FileNotFoundError:
            app_logger.error(f"파일을 찾을 수 없습니다: {file_path}")
            return None
        except Exception as e:
            handle_error(e, f"파일 해시 생성 실패: {file_path}")
            return None
    
    @staticmethod
    def generate_content_hash(content: str, algorithm: str = 'md5') -> str:
        """
        문자열 내용의 해시값 생성
        
        Args:
            content: 해시를 생성할 문자열
            algorithm: 해시 알고리즘 (md5, sha1, sha256)
            
        Returns:
            해시값
        """
        if algorithm.lower() == 'md5':
            return hashlib.md5(content.encode('utf-8')).hexdigest()
        elif algorithm.lower() == 'sha1':
            return hashlib.sha1(content.encode('utf-8')).hexdigest()
        elif algorithm.lower() == 'sha256':
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        else:
            app_logger.warning(f"지원하지 않는 해시 알고리즘: {algorithm}, MD5 사용")
            return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def compare_file_hashes(file_path: str, stored_hash: str, algorithm: str = 'md5') -> bool:
        """
        파일의 현재 해시값과 저장된 해시값 비교
        
        Args:
            file_path: 파일 경로
            stored_hash: 저장된 해시값
            algorithm: 해시 알고리즘 (md5, sha1, sha256)
            
        Returns:
            해시값 일치 여부 (True/False)
        """
        current_hash = HashUtils.generate_file_hash(file_path, algorithm)
        if current_hash is None:
            return False
        
        return current_hash == stored_hash
    
    @staticmethod
    def is_file_changed(file_path: str, stored_hash: str, algorithm: str = 'md5') -> bool:
        """
        파일이 변경되었는지 확인
        
        Args:
            file_path: 파일 경로
            stored_hash: 저장된 해시값
            algorithm: 해시 알고리즘 (md5, sha1, sha256)
            
        Returns:
            파일 변경 여부 (True: 변경됨, False: 변경되지 않음)
        """
        return not HashUtils.compare_file_hashes(file_path, stored_hash, algorithm)
    
    @staticmethod
    def generate_metadata_hash(metadata: Dict[str, Any]) -> str:
        """
        메타데이터 딕셔너리의 해시값 생성
        
        Args:
            metadata: 메타데이터 딕셔너리
            
        Returns:
            메타데이터 해시값
        """
        # 딕셔너리를 정렬된 문자열로 변환
        sorted_items = sorted(metadata.items())
        content = str(sorted_items)
        return HashUtils.generate_content_hash(content)
    
    @staticmethod
    def _matches_patterns(file_path: str, patterns: List[str]) -> bool:
        """
        파일 경로가 패턴과 매칭되는지 확인
        
        Args:
            file_path: 파일 경로
            patterns: 패턴 리스트
            
        Returns:
            매칭 여부 (True/False)
        """
        import fnmatch
        
        for pattern in patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False
    
    @staticmethod
    def generate_component_hash(component_data: Dict[str, Any]) -> str:
        """
        컴포넌트 데이터의 해시값 생성
        
        Args:
            component_data: 컴포넌트 데이터 딕셔너리
            
        Returns:
            컴포넌트 해시값
        """
        # 해시 계산에 포함할 주요 필드들
        hash_fields = [
            'component_name',
            'component_type',
            'file_path',
            'line_start',
            'line_end',
            'content'  # 실제 내용이 있다면
        ]
        
        hash_data = {}
        for field in hash_fields:
            if field in component_data:
                hash_data[field] = component_data[field]
        
        return HashUtils.generate_metadata_hash(hash_data)
    
    @staticmethod
    def generate_relationship_hash(relationship_data: Dict[str, Any]) -> str:
        """
        관계 데이터의 해시값 생성
        
        Args:
            relationship_data: 관계 데이터 딕셔너리
            
        Returns:
            관계 해시값
        """
        # 해시 계산에 포함할 주요 필드들
        hash_fields = [
            'src_id',
            'dst_id',
            'rel_type',
            'confidence'
        ]
        
        hash_data = {}
        for field in hash_fields:
            if field in relationship_data:
                hash_data[field] = relationship_data[field]
        
        return HashUtils.generate_metadata_hash(hash_data)
    
    @staticmethod
    def generate_table_hash(table_data: Dict[str, Any]) -> str:
        """
        테이블 데이터의 해시값 생성
        
        Args:
            table_data: 테이블 데이터 딕셔너리
            
        Returns:
            테이블 해시값
        """
        # 해시 계산에 포함할 주요 필드들
        hash_fields = [
            'table_name',
            'table_owner',
            'table_comments'
        ]
        
        hash_data = {}
        for field in hash_fields:
            if field in table_data:
                hash_data[field] = table_data[field]
        
        return HashUtils.generate_metadata_hash(hash_data)
    
    @staticmethod
    def generate_column_hash(column_data: Dict[str, Any]) -> str:
        """
        컬럼 데이터의 해시값 생성
        
        Args:
            column_data: 컬럼 데이터 딕셔너리
            
        Returns:
            컬럼 해시값
        """
        # 해시 계산에 포함할 주요 필드들
        hash_fields = [
            'column_name',
            'data_type',
            'data_length',
            'nullable',
            'column_comments',
            'position_pk',
            'data_default'
        ]
        
        hash_data = {}
        for field in hash_fields:
            if field in column_data:
                hash_data[field] = column_data[field]
        
        return HashUtils.generate_metadata_hash(hash_data)
    
    @staticmethod
    def get_hash_algorithm_info(algorithm: str) -> Dict[str, Any]:
        """
        해시 알고리즘 정보 반환
        
        Args:
            algorithm: 해시 알고리즘명
            
        Returns:
            알고리즘 정보 딕셔너리
        """
        algorithms = {
            'md5': {
                'name': 'MD5',
                'length': 32,
                'description': 'Message Digest Algorithm 5',
                'security': 'low',
                'speed': 'fast'
            },
            'sha1': {
                'name': 'SHA-1',
                'length': 40,
                'description': 'Secure Hash Algorithm 1',
                'security': 'medium',
                'speed': 'medium'
            },
            'sha256': {
                'name': 'SHA-256',
                'length': 64,
                'description': 'Secure Hash Algorithm 256',
                'security': 'high',
                'speed': 'slow'
            }
        }
        
        return algorithms.get(algorithm.lower(), {
            'name': 'Unknown',
            'length': 0,
            'description': 'Unknown algorithm',
            'security': 'unknown',
            'speed': 'unknown'
        })


# 편의 함수들
def generate_md5(content: str) -> str:
    """MD5 해시값 생성 편의 함수"""
    return HashUtils.generate_md5(content)


def generate_sha256(content: str) -> str:
    """SHA256 해시값 생성 편의 함수"""
    return HashUtils.generate_sha256(content)


def generate_file_hash(file_path: str, algorithm: str = 'md5') -> Optional[str]:
    """파일 해시값 생성 편의 함수"""
    return HashUtils.generate_file_hash(file_path, algorithm)


def is_file_changed(file_path: str, stored_hash: str, algorithm: str = 'md5') -> bool:
    """파일 변경 여부 확인 편의 함수"""
    return HashUtils.is_file_changed(file_path, stored_hash, algorithm)
