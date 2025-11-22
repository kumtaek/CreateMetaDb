import sqlite3
from typing import Optional, Dict, Any
from util import (
    PathUtils, DatabaseUtils,
    app_logger, info, error, debug, warning, handle_error,
    get_project_source_path, get_project_metadata_db_path
)

class BaseLoadingEngine:
    """
    모든 로딩 엔진의 기본 클래스
    공통 초기화, DB 연결, 프로젝트 ID 조회, 통계 관리 기능을 제공합니다.
    """
    
    def __init__(self, project_name: str, conn: Optional[sqlite3.Connection] = None):
        """
        초기화
        
        Args:
            project_name: 프로젝트명
            conn: 데이터베이스 연결 객체 (Optional)
        """
        self.project_name = project_name
        self.conn = conn
        self.path_utils = PathUtils()
        
        # 프로젝트 경로 설정
        self.project_source_path = get_project_source_path(project_name)
        self.metadata_db_path = get_project_metadata_db_path(project_name)
        
        # DB 유틸리티 초기화
        self.db_utils = DatabaseUtils(self.metadata_db_path)
        
        # 통계 정보 (하위 클래스에서 구체화)
        self.stats: Dict[str, int] = {}
        
        # info(f"{self.__class__.__name__} 초기화: {project_name}") # 로그 과다 방지

    def get_project_id(self) -> Optional[int]:
        """프로젝트 ID 조회"""
        try:
            return self.db_utils.get_project_id(self.project_name, self.conn)
        except Exception as e:
            handle_error(e, "프로젝트 ID 조회 실패")
            return None

    def _print_statistics(self):
        """통계 정보 출력 (기본 구현)"""
        info(f"=== {self.__class__.__name__} 통계 ===")
        for key, value in self.stats.items():
            info(f"  - {key}: {value}")
