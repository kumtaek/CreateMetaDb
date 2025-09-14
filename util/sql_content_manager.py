"""
SQL Content Manager - 정제된 SQL 내용 관리 모듈
- gzip 압축을 사용한 SQL 내용 저장
- 프로젝트별 별도 데이터베이스 파일 사용
- 3단계 XML 파싱에서 정제된 SQL 내용 저장
"""

import gzip
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from .logger import app_logger, handle_error
from .database_utils import DatabaseUtils
from .path_utils import PathUtils


class SqlContentManager:
    """정제된 SQL 내용 관리 클래스"""
    
    def __init__(self, project_name: str):
        """
        SqlContentManager 초기화
        
        Args:
            project_name: 프로젝트명
        """
        self.project_name = project_name
        self.db_utils = None
        self.initialized = False
        self.initialized = self._initialize_database()
    
    def _initialize_database(self) -> bool:
        """데이터베이스 초기화"""
        try:
            # 프로젝트별 데이터베이스 경로 생성 (공통함수 사용)
            path_utils = PathUtils()
            project_path = path_utils.get_project_path(self.project_name)
            db_path = os.path.join(project_path, "SqlContent.db")
            
            # 디렉토리 생성
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # DatabaseUtils 초기화
            self.db_utils = DatabaseUtils(db_path)
            
            # 데이터베이스 연결
            if not self.db_utils.connect():
                return False
            
            # 스키마 생성
            schema_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 'database', 'create_sql_content_db.sql'
            )
            schema_path = os.path.abspath(schema_path)
            
            if not self.db_utils.create_schema(schema_path):
                app_logger.error("SQL Content 데이터베이스 스키마 생성 실패")
                return False
            
            app_logger.info(f"SQL Content 데이터베이스 초기화 완료: {db_path}")
            return True
            
        except Exception as e:
            handle_error(e, "SQL Content 데이터베이스 초기화 실패")
            return False
    
    def save_sql_content(self, sql_content: str, project_id: int, **kwargs) -> bool:
        """
        정제된 SQL 내용 저장
        
        Args:
            sql_content: 정제된 SQL 내용
            project_id: 프로젝트 ID
            **kwargs: 추가 메타데이터
            
        Returns:
            저장 성공 여부
        """
        try:
            # 프로젝트 정보 먼저 저장 (외래키 제약조건 대비)
            self._ensure_project_exists(project_id, kwargs.get('file_path', ''))
            
            # gzip 압축
            compressed_content = self._compress_content(sql_content)
            
            # 데이터베이스에 저장
            sql_content_data = {
                'project_id': project_id,
                'file_id': kwargs.get('file_id'),
                'component_id': kwargs.get('component_id'),
                'sql_content_compressed': compressed_content,
                'query_type': kwargs.get('query_type', 'UNKNOWN'),
                'file_path': kwargs.get('file_path'),
                'component_name': kwargs.get('component_name'),
                'file_name': kwargs.get('file_name'),
                'line_start': kwargs.get('line_start'),
                'line_end': kwargs.get('line_end'),
                'hash_value': kwargs.get('hash_value'),
                'error_message': kwargs.get('error_message'),
                'del_yn': 'N'
            }
            
            # 데이터베이스에 저장
            success = self.db_utils.insert_or_replace('sql_contents', sql_content_data)
            
            if success:
                app_logger.debug(f"SQL 내용 저장 완료: {kwargs.get('component_name', 'unknown')} - {kwargs.get('file_path', 'unknown')}")
            
            return success
            
        except Exception as e:
            handle_error(e, "SQL 내용 저장 실패")
            return False
    
    def _ensure_project_exists(self, project_id: int, file_path: str) -> bool:
        """
        프로젝트 정보가 SqlContent.db에 존재하는지 확인하고 없으면 생성
        
        Args:
            project_id: 프로젝트 ID
            file_path: 파일 경로 (프로젝트 경로 추출용)
            
        Returns:
            성공 여부
        """
        try:
            # 프로젝트 정보 조회
            query = "SELECT project_id FROM projects WHERE project_id = ?"
            results = self.db_utils.execute_query(query, (project_id,))
            
            if not results:
                # 프로젝트 정보가 없으면 생성
                project_path = os.path.dirname(file_path) if file_path else f"projects/{self.project_name}"
                project_data = {
                    'project_id': project_id,
                    'project_name': self.project_name,
                    'project_path': project_path,
                    'del_yn': 'N'
                }
                self.db_utils.insert_or_replace('projects', project_data)
                app_logger.debug(f"SqlContent.db에 프로젝트 정보 생성: {self.project_name} (ID: {project_id})")
            
            return True
            
        except Exception as e:
            app_logger.warning(f"프로젝트 정보 확인/생성 실패: {str(e)}")
            return False
    
    def _compress_content(self, sql_content: str) -> bytes:
        """SQL 내용을 gzip으로 압축"""
        try:
            return gzip.compress(sql_content.encode('utf-8'))
        except Exception as e:
            handle_error(e, "SQL 내용 압축 실패")
            return sql_content.encode('utf-8')
    
    def _decompress_content(self, compressed_data: bytes) -> str:
        """압축된 SQL 내용을 gzip으로 압축 해제"""
        try:
            return gzip.decompress(compressed_data).decode('utf-8')
        except Exception as e:
            handle_error(e, "SQL 내용 압축 해제 실패")
            return compressed_data.decode('utf-8', errors='ignore')
    
    def get_sql_contents(self, project_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        SQL 내용 목록 조회
        
        Args:
            project_id: 프로젝트 ID
            limit: 조회 개수 제한
            
        Returns:
            SQL 내용 목록
        """
        try:
            query = """
            SELECT 
                content_id, file_path, component_name, query_type,
                hash_value, created_at, sql_content_compressed
            FROM sql_contents 
            WHERE project_id = ? AND del_yn = 'N'
            ORDER BY created_at DESC
            LIMIT ?
            """
            
            results = self.db_utils.execute_query(query, (project_id, limit))
            
            # 압축 해제
            sql_contents = []
            for row in results:
                content_data = {
                    'content_id': row[0],
                    'file_path': row[1],
                    'component_name': row[2],
                    'query_type': row[3],
                    'hash_value': row[4],
                    'created_at': row[5],
                    'sql_content': self._decompress_content(row[6])
                }
                sql_contents.append(content_data)
            
            return sql_contents
            
        except Exception as e:
            handle_error(e, "SQL 내용 조회 실패")
            return []
    
    def get_stats(self, project_id: int) -> Dict[str, Any]:
        """
        SQL 내용 통계 조회
        
        Args:
            project_id: 프로젝트 ID
            
        Returns:
            통계 정보
        """
        try:
            # 전체 통계
            total_query = """
            SELECT 
                COUNT(*) as total_sql_contents,
                SUM(LENGTH(sql_content_compressed)) as total_compressed_size,
                AVG(LENGTH(sql_content_compressed)) as avg_compressed_size,
                MAX(LENGTH(sql_content_compressed)) as max_compressed_size,
                MIN(LENGTH(sql_content_compressed)) as min_compressed_size
            FROM sql_contents 
            WHERE project_id = ? AND del_yn = 'N'
            """
            
            total_stats = self.db_utils.execute_query(total_query, (project_id,))
            
            # 파일별 통계
            file_query = """
            SELECT 
                file_path, file_name,
                COUNT(*) as total_sql_contents,
                SUM(LENGTH(sql_content_compressed)) as total_compressed_size,
                AVG(LENGTH(sql_content_compressed)) as avg_compressed_size
            FROM sql_contents 
            WHERE project_id = ? AND del_yn = 'N'
            GROUP BY file_path, file_name
            ORDER BY total_compressed_size DESC
            LIMIT 10
            """
            
            file_stats = self.db_utils.execute_query(file_query, (project_id,))
            
            # 쿼리 타입별 통계
            type_query = """
            SELECT 
                query_type,
                COUNT(*) as total_sql_contents,
                SUM(LENGTH(sql_content_compressed)) as total_compressed_size,
                AVG(LENGTH(sql_content_compressed)) as avg_compressed_size
            FROM sql_contents 
            WHERE project_id = ? AND del_yn = 'N'
            GROUP BY query_type
            ORDER BY total_compressed_size DESC
            """
            
            type_stats = self.db_utils.execute_query(type_query, (project_id,))
            
            return {
                'total_stats': total_stats[0] if total_stats else None,
                'file_stats': file_stats,
                'type_stats': type_stats
            }
            
        except Exception as e:
            handle_error(e, "SQL 내용 통계 조회 실패")
            return {}
    
    def close(self):
        """데이터베이스 연결 해제"""
        if self.db_utils:
            self.db_utils.disconnect()
            app_logger.info("SQL Content 데이터베이스 연결 해제")
