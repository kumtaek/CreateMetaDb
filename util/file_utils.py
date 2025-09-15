"""
SourceAnalyzer 파일 처리 공통 유틸리티 모듈
- 파일 읽기/쓰기
- 파일 경로 처리
- 파일 타입 감지
- 파일 해시값 생성
"""

import os
import hashlib
import mimetypes
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from .logger import app_logger, handle_error, info


class FileUtils:
    """파일 처리 관련 공통 유틸리티 클래스"""
    
    # 지원하는 파일 타입 정의
    SUPPORTED_EXTENSIONS = {
        'java': ['.java'],
        'xml': ['.xml'],
        'jsp': ['.jsp'],
        'sql': ['.sql'],
        'csv': ['.csv'],
        'yaml': ['.yaml', '.yml'],
        'properties': ['.properties'],
        'txt': ['.txt'],
        'json': ['.json']
    }
    
    @staticmethod
    def read_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """
        파일을 읽어서 내용을 반환
        
        Args:
            file_path: 읽을 파일 경로
            encoding: 파일 인코딩 (기본값: utf-8)
            
        Returns:
            파일 내용 (문자열) 또는 None (읽기 실패시)
        """
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
                app_logger.debug(f"파일 읽기 성공: {file_path}")
                return content
        except FileNotFoundError:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(Exception(f"파일을 찾을 수 없습니다: {file_path}"), f"파일 읽기 실패: {file_path}")
        except UnicodeDecodeError:
            info(f"인코딩 문제 감지, 다른 인코딩으로 재시도: {os.path.basename(file_path)}")
            try:
                with open(file_path, 'r', encoding='cp949') as file:
                    content = file.read()
                    app_logger.debug(f"파일 읽기 성공 (cp949): {file_path}")
                    return content
            except UnicodeDecodeError:
                # CP949도 실패하면 다른 인코딩 시도
                try:
                    with open(file_path, 'r', encoding='euc-kr') as file:
                        content = file.read()
                        app_logger.debug(f"파일 읽기 성공 (euc-kr): {file_path}")
                        return content
                except UnicodeDecodeError:
                    # 모든 인코딩 실패 시 에러 처리
                    handle_error(Exception(f"모든 인코딩 시도 실패 (utf-8, cp949, euc-kr): {file_path}"), f"파일 인코딩 문제: {file_path}")
                    return None
            except Exception as e:
                handle_error(e, f"파일 읽기 실패: {file_path}")
                return None
        except Exception as e:
            handle_error(e, f"파일 읽기 실패: {file_path}")
            return None
    
    @staticmethod
    def write_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """
        파일에 내용을 쓴다
        
        Args:
            file_path: 쓸 파일 경로
            content: 쓸 내용
            encoding: 파일 인코딩 (기본값: utf-8)
            
        Returns:
            성공 여부 (True/False)
        """
        try:
            # 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as file:
                file.write(content)
                app_logger.debug(f"파일 쓰기 성공: {file_path}")
                return True
        except Exception as e:
            handle_error(e, f"파일 쓰기 실패: {file_path}")
            return False
    
    @staticmethod
    def get_file_type(file_path: str) -> str:
        """
        파일 확장자로부터 파일 타입을 결정
        
        Args:
            file_path: 파일 경로
            
        Returns:
            파일 타입 (java, xml, jsp, sql, csv, yaml, properties, txt, json, unknown)
        """
        if not file_path:
            return 'unknown'
        
        file_ext = Path(file_path).suffix.lower()
        
        for file_type, extensions in FileUtils.SUPPORTED_EXTENSIONS.items():
            if file_ext in extensions:
                return file_type
        
        return 'unknown'
    
    @staticmethod
    def get_file_hash(file_path: str) -> Optional[str]:
        """
        파일의 MD5 해시값을 계산
        
        Args:
            file_path: 파일 경로
            
        Returns:
            MD5 해시값 (문자열) 또는 None (실패시)
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            handle_error(e, f"파일 해시 계산 실패: {file_path}")
            return None
    
    @staticmethod
    def get_content_hash(content: str) -> str:
        """
        문자열 내용의 MD5 해시값을 계산
        
        Args:
            content: 해시를 계산할 문자열
            
        Returns:
            MD5 해시값 (문자열)
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """
        파일의 상세 정보를 반환
        
        Args:
            file_path: 파일 경로
            
        Returns:
            파일 정보 딕셔너리
        """
        try:
            if not os.path.exists(file_path):
                return {
                    'exists': False,
                    'error': 'File not found'
                }
            
            stat = os.stat(file_path)
            path_obj = Path(file_path)
            
            return {
                'exists': True,
                'file_name': path_obj.name,
                'file_path': str(path_obj.absolute()),
                'relative_path': file_path,
                'file_type': FileUtils.get_file_type(file_path),
                'file_size': stat.st_size,
                'line_count': FileUtils.count_lines(file_path),
                'hash_value': FileUtils.get_file_hash(file_path),
                'created_at': stat.st_ctime,
                'modified_at': stat.st_mtime,
                'is_file': path_obj.is_file(),
                'is_dir': path_obj.is_dir()
            }
        except Exception as e:
            handle_error(e, f"파일 정보 조회 실패: {file_path}")
            return {
                'exists': False,
                'error': str(e)
            }
    
    @staticmethod
    def count_lines(file_path: str) -> int:
        """
        파일의 라인 수를 계산
        
        Args:
            file_path: 파일 경로
            
        Returns:
            라인 수
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return sum(1 for _ in file)
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp949') as file:
                    return sum(1 for _ in file)
            except Exception:
                return 0
        except Exception:
            return 0
    
    @staticmethod
    def scan_directory(directory_path: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        디렉토리를 스캔하여 파일 목록을 반환
        
        Args:
            directory_path: 스캔할 디렉토리 경로
            recursive: 재귀적 스캔 여부
            
        Returns:
            파일 정보 리스트
        """
        files = []
        
        try:
            if recursive:
                for root, dirs, filenames in os.walk(directory_path):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        file_info = FileUtils.get_file_info(file_path)
                        if file_info['exists']:
                            files.append(file_info)
            else:
                for item in os.listdir(directory_path):
                    item_path = os.path.join(directory_path, item)
                    if os.path.isfile(item_path):
                        file_info = FileUtils.get_file_info(item_path)
                        if file_info['exists']:
                            files.append(file_info)
            
            app_logger.debug(f"디렉토리 스캔 완료: {directory_path}, 파일 수: {len(files)}")
            return files
            
        except Exception as e:
            handle_error(e, f"디렉토리 스캔 실패: {directory_path}")
            return []
    
    @staticmethod
    def filter_files_by_type(files: List[Dict[str, Any]], file_types: List[str]) -> List[Dict[str, Any]]:
        """
        파일 타입으로 필터링
        
        Args:
            files: 파일 정보 리스트
            file_types: 필터링할 파일 타입 리스트
            
        Returns:
            필터링된 파일 정보 리스트
        """
        return [file_info for file_info in files if file_info.get('file_type') in file_types]
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> bool:
        """
        디렉토리가 존재하지 않으면 생성
        
        Args:
            directory_path: 디렉토리 경로
            
        Returns:
            성공 여부 (True/False)
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            handle_error(e, f"디렉토리 생성 실패: {directory_path}")
            return False
    
    @staticmethod
    def get_relative_path(file_path: str, base_path: str) -> str:
        """
        기본 경로를 기준으로 한 상대 경로를 반환
        
        Args:
            file_path: 파일 경로
            base_path: 기준 경로
            
        Returns:
            상대 경로
        """
        try:
            return os.path.relpath(file_path, base_path)
        except ValueError:
            # 다른 드라이브에 있는 경우 절대 경로 반환
            return file_path
    
    @staticmethod
    def cleanup_old_log_files(log_directory: str, hours_threshold: int = 24) -> int:
        """
        24시간(또는 지정된 시간) 지난 로그 파일들을 삭제
        
        Args:
            log_directory: 로그 디렉토리 경로
            hours_threshold: 삭제 기준 시간 (시간 단위, 기본값: 24)
            
        Returns:
            삭제된 파일 수
        """
        deleted_count = 0
        current_time = time.time()
        threshold_seconds = hours_threshold * 3600  # 시간을 초로 변환
        
        try:
            if not os.path.exists(log_directory):
                info(f"로그 디렉토리가 존재하지 않습니다: {log_directory}")
                return 0
            
            for filename in os.listdir(log_directory):
                file_path = os.path.join(log_directory, filename)
                
                # 파일인지 확인
                if not os.path.isfile(file_path):
                    continue
                
                # .log 확장자 파일만 처리
                if not filename.endswith('.log'):
                    continue
                
                try:
                    # 파일의 수정 시간 확인
                    file_mtime = os.path.getmtime(file_path)
                    file_age = current_time - file_mtime
                    
                    # 지정된 시간보다 오래된 파일 삭제
                    if file_age > threshold_seconds:
                        os.remove(file_path)
                        deleted_count += 1
                        info(f"오래된 로그 파일 삭제: {filename} (생성일: {time.ctime(file_mtime)})")
                        
                except Exception as e:
                    # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                    handle_error(e, f"로그 파일 삭제 실패: {filename}")
            
            if deleted_count > 0:
                info(f"총 {deleted_count}개의 오래된 로그 파일을 삭제했습니다")
            else:
                info("삭제할 오래된 로그 파일이 없습니다")
                
            return deleted_count
            
        except Exception as e:
            handle_error(e, f"로그 파일 정리 실패: {log_directory}")
            return 0


# 편의 함수들
def read_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """파일 읽기 편의 함수"""
    return FileUtils.read_file(file_path, encoding)


def write_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """파일 쓰기 편의 함수"""
    return FileUtils.write_file(file_path, content, encoding)


def get_file_type(file_path: str) -> str:
    """파일 타입 감지 편의 함수"""
    return FileUtils.get_file_type(file_path)


def get_file_hash(file_path: str) -> Optional[str]:
    """파일 해시 계산 편의 함수"""
    return FileUtils.get_file_hash(file_path)


def get_content_hash(content: str) -> str:
    """내용 해시 계산 편의 함수"""
    return FileUtils.get_content_hash(content)


def cleanup_old_log_files(log_directory: str, hours_threshold: int = 24) -> int:
    """오래된 로그 파일 삭제 편의 함수"""
    return FileUtils.cleanup_old_log_files(log_directory, hours_threshold)
