"""
sqltext 폴더의 *.sql 파일을 메타DB와 SqlContent.db에 저장하는 로더
- sqltext/ 하위 모든 서브폴더 재귀 탐색
- 파일명(확장자 제외)을 query_id로 사용
- files, components(metadata.db) + sql_contents(SqlContent.db) 기록
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from util import (
    PathUtils, FileUtils, HashUtils,
    app_logger, info, warning, handle_error,
    DatabaseUtils
)
from util.file_context import get_file_context_manager
from util.sql_content_manager import SqlContentManager


class SqlTextLoadingEngine:
    """sqltext 폴더의 SQL 파일을 로드하여 메타DB와 SqlContent.db에 저장"""

    def __init__(self, project_name: str, conn, use_compression: Optional[bool] = None):
        from util import get_sql_compress
        self.project_name = project_name
        self.conn = conn
        self.path_utils = PathUtils()
        self.hash_utils = HashUtils()
        resolved_compress = use_compression if use_compression is not None else get_sql_compress()
        self.db_utils = DatabaseUtils(self.path_utils.get_project_metadata_db_path(project_name))
        self.sql_content_mgr = SqlContentManager(project_name, enable_brute_force_search=True, use_compression=resolved_compress)
        self.project_root = self.path_utils.join_path(self.path_utils.project_root, "projects", project_name)
        self.sqltext_root = os.path.join(self.project_root, "sqltext")

    def execute(self) -> bool:
        """sqltext 폴더 로딩 실행"""
        try:
            if not os.path.exists(self.sqltext_root):
                info(f"sqltext 폴더가 없어 스킵: {self.sqltext_root}")
                return True

            project_id = self._get_project_id()
            if not project_id:
                handle_error(Exception("프로젝트 ID 조회 실패"), f"프로젝트 ID를 찾을 수 없습니다: {self.project_name}")
                return False

            sql_files = self._collect_sql_files()
            if not sql_files:
                info("sqltext 폴더에 처리할 SQL 파일이 없습니다")
                return True

            total_files = len(sql_files)
            processed_count = 0
            log_interval = 500
            for sql_path in sql_files:
                self._process_sql_file(sql_path, project_id)
                processed_count += 1
                # 500개 단위 진행 상황 로그
                if processed_count % log_interval == 0:
                    info(f"sqltext 로딩 진행: {processed_count}/{total_files}개 처리")

            # 잔여분 진행 로그 (500개 단위가 아닌 경우)
            if processed_count % log_interval != 0:
                info(f"sqltext 로딩 진행: {processed_count}/{total_files}개 처리")
            info(f"sqltext 로딩 완료: {processed_count}개 SQL 파일 처리")
            return True
        except Exception as e:
            handle_error(e, "sqltext 로딩 실행 실패")
            return False

    def _collect_sql_files(self) -> List[Path]:
        """sqltext 하위 모든 *.sql 파일 수집"""
        paths: List[Path] = []
        for path in Path(self.sqltext_root).rglob("*.sql"):
            if path.is_file():
                paths.append(path)
        return paths

    def _get_project_id(self) -> Optional[int]:
        """프로젝트 ID 조회"""
        try:
            return self.db_utils.get_project_id(self.project_name, self.conn)
        except Exception as e:
            handle_error(e, f"프로젝트 ID 조회 실패: {self.project_name}")
            return None

    def _process_sql_file(self, sql_path: Path, project_id: int) -> None:
        """단일 SQL 파일 처리"""
        try:
            query_id = sql_path.stem
            relative_path = os.path.relpath(sql_path, self.project_root)
            file_path_unix = self.path_utils.normalize_path_separator(relative_path, 'unix')

            content = FileUtils.read_file(str(sql_path))
            if content is None:
                handle_error(Exception("SQL 파일 읽기 실패"), f"SQL 파일을 읽을 수 없습니다: {sql_path}")
                return

            file_id = self._upsert_file_record(project_id, sql_path, file_path_unix)
            if not file_id:
                handle_error(Exception("파일 ID 생성 실패"), f"files 테이블 저장 실패: {sql_path}")
                return

            component_id = self._upsert_component(project_id, file_id, query_id, content)
            if not component_id:
                handle_error(Exception("컴포넌트 생성 실패"), f"components 저장 실패: query_id={query_id}, file={sql_path}")
                return

            # SqlContent.db 저장 (file_context 설정 후 처리)
            ctx_mgr = get_file_context_manager()
            ctx_mgr.push(
                project_name=self.project_name,
                project_id=project_id,
                file_id=file_id,
                file_path=file_path_unix,
                file_name=sql_path.name,
                file_type='SQL',
                source_type='SQLTEXT',
                stage='SQLTEXT'
            )
            try:
                self.sql_content_mgr.save_sql_content(
                    sql_content=content,
                    project_id=project_id,
                    file_id=file_id,
                    file_path=file_path_unix,
                    file_name=sql_path.name,
                    query_id=query_id,
                    query_type=self._infer_query_type(content, query_id),
                    component_layer='QUERY_FROM_SQLTEXT'
                )
            finally:
                ctx_mgr.pop()
        except Exception as e:
            handle_error(e, f"SQL 파일 처리 실패: {sql_path}")

    def _upsert_file_record(self, project_id: int, sql_path: Path, file_path_unix: str) -> Optional[int]:
        """files 테이블 upsert 후 file_id 반환"""
        file_info = FileUtils.get_file_info(str(sql_path))
        # files 테이블은 스키마에 맞게 명시적 INSERT 사용 (file_context 의존 회피)
        insert_sql = """
            INSERT OR IGNORE INTO files
                (project_id, file_name, file_path, file_type, line_count, hash_value, del_yn)
            VALUES (?, ?, ?, ?, ?, ?, 'N')
        """
        self.db_utils.execute_update(
            insert_sql,
            (
                project_id,
                sql_path.name,
                file_path_unix,
                'SQL',
                file_info.get('line_count'),
                file_info.get('hash_value'),
            ),
            conn=self.conn
        )

        result = self.db_utils.execute_query(
            """
            SELECT file_id FROM files
            WHERE project_id = ? AND file_name = ? AND file_path = ? AND del_yn = 'N'
            LIMIT 1
            """,
            (project_id, sql_path.name, file_path_unix),
            conn=self.conn
        )
        return result[0]['file_id'] if result else None

    def _infer_query_type(self, sql_content: str, query_id: str) -> str:
        """SQLTEXT 쿼리 유형 추론 (공통 SQL Content Manager 로직 재사용)"""
        try:
            return self.sql_content_mgr._determine_sql_component_type(sql_content, query_id)
        except Exception:
            return 'SQL_QUERY'

    def _upsert_component(self, project_id: int, file_id: int, query_id: str, sql_content: str) -> Optional[int]:
        """components 테이블 upsert 후 component_id 반환"""
        component_type = self._infer_query_type(sql_content, query_id)
        component_data = {
            'project_id': project_id,
            'file_id': file_id,
            'component_name': query_id,
            'component_type': component_type,
            'layer': 'QUERY_FROM_SQLTEXT',
            'hash_value': self.hash_utils.generate_md5(query_id),
            'del_yn': 'N'
        }
        self.db_utils.insert_or_replace('components', component_data)

        result = self.db_utils.execute_query(
            """
            SELECT component_id FROM components
            WHERE project_id = ? AND file_id = ? AND component_name = ? AND component_type = ? AND del_yn = 'N'
            LIMIT 1
            """,
            (project_id, file_id, query_id, component_type),
            conn=self.conn
        )
        return result[0]['component_id'] if result else None


def execute_sqltext_loading(project_name: str, conn, use_compression: Optional[bool] = None) -> bool:
    """편의 함수"""
    engine = SqlTextLoadingEngine(project_name, conn, use_compression)
    return engine.execute()
