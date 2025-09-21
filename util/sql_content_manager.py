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
            # 프로젝트명 유효성 검증 (버그 방지)
            from .validation_utils import ValidationUtils
            if not ValidationUtils.is_valid_project_name(self.project_name):
                from .logger import handle_error
                handle_error(Exception(f"잘못된 프로젝트명: {self.project_name}"), "SQL Content Manager 초기화 실패")
                return False
            
            # 프로젝트별 데이터베이스 경로 생성 (공통함수 사용)
            path_utils = PathUtils()
            db_path = path_utils.join_path("projects", self.project_name, "SqlContent.db")
            
            # 디렉토리 생성
            project_dir = path_utils.join_path("projects", self.project_name)
            os.makedirs(project_dir, exist_ok=True)
            
            # DatabaseUtils 초기화
            self.db_utils = DatabaseUtils(db_path)
            
            # 데이터베이스 연결
            if not self.db_utils.connect():
                return False
            
            # 스키마 생성 (공통함수 사용)
            schema_path = path_utils.join_path("database", "create_sql_content_db.sql")
            
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
            
            # 데이터베이스에 저장 (UPSERT 사용)
            success = self._upsert_sql_content(sql_content_data)
            
            if success:
                app_logger.debug(f"SQL 내용 저장 완료: {kwargs.get('component_name', 'unknown')} - {kwargs.get('file_path', 'unknown')}")
            
            return success
            
        except Exception as e:
            handle_error(e, "SQL 내용 저장 실패")
    
    def _upsert_sql_content(self, sql_content_data: Dict[str, Any]) -> bool:
        """
        SQL Content를 DatabaseUtils의 upsert 메서드로 저장 (hash_value 기반 변동분 감지)
        
        Args:
            sql_content_data: SQL Content 데이터
            
        Returns:
            저장 성공 여부
        """
        try:
            project_id = sql_content_data.get('project_id')
            component_id = sql_content_data.get('component_id')
            hash_value = sql_content_data.get('hash_value', '-')
            
            # 기존 데이터 조회 (hash_value 비교용)
            check_query = """
                SELECT content_id, hash_value, del_yn 
                FROM sql_contents 
                WHERE project_id = ? AND component_id = ?
            """
            existing_results = self.db_utils.execute_query(check_query, (project_id, component_id))
            
            if existing_results:
                existing_content_id, existing_hash, existing_del_yn = existing_results[0]
                
                # hash_value가 같으면 업데이트 불필요
                if existing_hash == hash_value and existing_del_yn == 'N':
                    app_logger.debug(f"SQL Content 변경 없음 (스킵): {sql_content_data.get('component_name', 'unknown')}")
                    return True
                
                # hash_value가 다르면 UPSERT (기존 데이터 업데이트)
                # project_id와 component_id로 업데이트
                update_query = """
                    UPDATE sql_contents 
                    SET file_id = ?, sql_content_compressed = ?, query_type = ?, 
                        file_path = ?, component_name = ?, file_name = ?, 
                        line_start = ?, line_end = ?, hash_value = ?, 
                        error_message = ?, del_yn = 'N'
                    WHERE project_id = ? AND component_id = ?
                """
                update_values = (
                    sql_content_data.get('file_id'),
                    sql_content_data.get('sql_content_compressed'),
                    sql_content_data.get('query_type'),
                    sql_content_data.get('file_path'),
                    sql_content_data.get('component_name'),
                    sql_content_data.get('file_name'),
                    sql_content_data.get('line_start'),
                    sql_content_data.get('line_end'),
                    hash_value,
                    sql_content_data.get('error_message'),
                    project_id,
                    component_id
                )
                
                with self.db_utils.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(update_query, update_values)
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        app_logger.debug(f"SQL Content UPSERT 성공 (업데이트): {sql_content_data.get('component_name', 'unknown')}")
                        return True
                    else:
                        app_logger.error(f"SQL Content 업데이트 실패 (영향받은 행 없음): {sql_content_data.get('component_name', 'unknown')}")
                        return False
                
            else:
                # 기존 데이터가 없으면 INSERT
                success = self.db_utils.insert_record('sql_contents', sql_content_data)
                
                if success:
                    app_logger.debug(f"SQL Content UPSERT 성공 (신규): {sql_content_data.get('component_name', 'unknown')}")
                else:
                    app_logger.error(f"SQL Content 삽입 실패: {sql_content_data.get('component_name', 'unknown')}")
                
                return success
                
        except Exception as e:
            handle_error(e, "SQL Content UPSERT 실패")
    
    def cleanup_deleted_sql_contents(self, project_id: int, current_component_ids: List[int]) -> int:
        """
        삭제된 SQL Content 정리 (현재 존재하지 않는 component_id의 SQL Content를 삭제)
        
        Args:
            project_id: 프로젝트 ID
            current_component_ids: 현재 존재하는 component_id 리스트
            
        Returns:
            삭제된 SQL Content 개수
        """
        try:
            if not current_component_ids:
                return 0
            
            # 삭제할 SQL Content 조회 (현재 component_id에 없는 것들)
            placeholders = ', '.join(['?' for _ in current_component_ids])
            select_query = f"""
                SELECT content_id, component_name 
                FROM sql_contents 
                WHERE project_id = ? AND component_id NOT IN ({placeholders}) AND del_yn = 'N'
            """
            
            with self.db_utils.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(select_query, [project_id] + current_component_ids)
                deleted_contents = cursor.fetchall()
                
                if deleted_contents:
                    # 삭제된 SQL Content를 del_yn = 'Y'로 업데이트
                    delete_query = f"""
                        UPDATE sql_contents 
                        SET del_yn = 'Y', updated_at = CURRENT_TIMESTAMP
                        WHERE project_id = ? AND component_id NOT IN ({placeholders}) AND del_yn = 'N'
                    """
                    cursor.execute(delete_query, [project_id] + current_component_ids)
                    conn.commit()
                    
                    deleted_count = len(deleted_contents)
                    app_logger.info(f"삭제된 SQL Content 정리 완료: {deleted_count}개")
                    
                    # 삭제된 SQL Content 목록 로그
                    for content_id, component_name in deleted_contents:
                        app_logger.debug(f"삭제된 SQL Content: {component_name} (ID: {content_id})")
                    
                    return deleted_count
                else:
                    app_logger.debug("삭제할 SQL Content가 없습니다")
                    return 0
                    
        except Exception as e:
            app_logger.error(f"삭제된 SQL Content 정리 실패 (무시하고 계속 진행): {str(e)}")
            return 0
    
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
            app_logger.error(f"SQL 내용 압축 실패 (무시하고 계속 진행): {str(e)}")
            return sql_content.encode('utf-8')
    
    def _decompress_content(self, compressed_data: bytes) -> str:
        """압축된 SQL 내용을 gzip으로 압축 해제"""
        try:
            return gzip.decompress(compressed_data).decode('utf-8')
        except Exception as e:
            app_logger.error(f"SQL 내용 압축 해제 실패 (무시하고 계속 진행): {str(e)}")
            return compressed_data.decode('utf-8', errors='replace')
    
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
            app_logger.error(f"SQL 내용 조회 실패 (무시하고 계속 진행): {str(e)}")
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
            app_logger.error(f"SQL 내용 통계 조회 실패 (무시하고 계속 진행): {str(e)}")
            return {}
    
    def close(self):
        """데이터베이스 연결 해제"""
        if self.db_utils:
            self.db_utils.disconnect()
            app_logger.info("SQL Content 데이터베이스 연결 해제")
