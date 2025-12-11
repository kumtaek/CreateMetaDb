"""
Java 파일에서 sqltext SQL ID 문자열을 검색해 CALL_QUERY 관계를 생성하는 모듈.
- component_type='SQL_QUERY', layer='SQL_TEXT'인 컴포넌트만 대상.
- 단순 문자열 매칭(대소문자 무시)으로 누락을 최소화한다.
"""

import os
from typing import List, Dict

from util import (
    DatabaseUtils, FileUtils, PathUtils,
    app_logger, info, debug, warning, handle_error,
    get_project_source_path
)


class SqlTextJavaMatcher:
    """sqltext SQL ID를 Java 파일에서 검색해 CALL_QUERY 관계를 생성한다."""

    def __init__(self, project_name: str, conn):
        self.project_name = project_name
        self.conn = conn
        self.path_utils = PathUtils()
        self.db_utils = DatabaseUtils(self.path_utils.get_project_metadata_db_path(project_name))
        self.project_src_root = get_project_source_path(project_name)

    def execute(self) -> bool:
        """매칭 실행"""
        try:
            project_id = self.db_utils.get_project_id(self.project_name, self.conn)
            if not project_id:
                handle_error(Exception("프로젝트 ID 조회 실패"), f"프로젝트 ID를 찾을 수 없습니다: {self.project_name}")
                return False

            sql_components = self._load_sqltext_components(project_id)
            if not sql_components:
                info("SQLTEXT 컴포넌트가 없어 추가 매칭 대상이 없습니다")
                return True

            java_files = self._load_java_files(project_id)
            if not java_files:
                info("Java 파일이 없어 sqltext 매칭 대상이 없습니다")
                return True

            total_matches = 0
            total_relationships = 0

            for file_info in java_files:
                matched = self._process_java_file(file_info, sql_components, project_id)
                total_matches += matched['matched_sql']
                total_relationships += matched['relationships_created']

            info(f"sqltext-Java 매칭 완료: 파일 {len(java_files)}개, 매칭된 SQL ID {total_matches}개, 생성/유지된 관계 {total_relationships}개")
            return True
        except Exception as e:
            handle_error(e, "sqltext-Java 매칭 실행 실패")
            return False

    def _load_sqltext_components(self, project_id: int) -> List[Dict]:
        """sqltext에서 생성된 SQL_QUERY 컴포넌트 목록 로드"""
        try:
            query = """
                SELECT component_id, component_name
                FROM components
                WHERE project_id = ?
                  AND component_type = 'SQL_QUERY'
                  AND layer = 'SQLTEXT'
                  AND del_yn = 'N'
            """
            rows = self.db_utils.execute_query(query, (project_id,), conn=self.conn)
            return rows or []
        except Exception as e:
            handle_error(e, "SQLTEXT 컴포넌트 로드 실패")
            return []

    def _load_java_files(self, project_id: int) -> List[Dict]:
        """files 테이블에서 Java 파일 목록 로드"""
        try:
            query = """
                SELECT file_id, file_name, file_path
                FROM files
                WHERE project_id = ?
                  AND file_type = 'JAVA'
                  AND del_yn = 'N'
            """
            return self.db_utils.execute_query(query, (project_id,), conn=self.conn)
        except Exception as e:
            handle_error(e, "Java 파일 목록 로드 실패")
            return []

    def _process_java_file(self, file_info: Dict, sql_components: List[Dict], project_id: int) -> Dict[str, int]:
        """단일 Java 파일을 처리하여 CALL_QUERY 관계를 생성"""
        matched_sql = 0
        relationships_created = 0
        file_path_parts = [self.project_src_root]
        if file_info.get('file_path'):
            file_path_parts.append(file_info['file_path'])
        file_path_parts.append(file_info['file_name'])
        full_path = os.path.join(*file_path_parts)

        if not os.path.exists(full_path):
            handle_error(Exception("Java 파일 미존재"), f"Java 파일이 존재하지 않습니다: {full_path}")
            return {'matched_sql': 0, 'relationships_created': 0}

        content = FileUtils.read_file(full_path)
        if content is None:
            handle_error(Exception("Java 파일 읽기 실패"), f"Java 파일을 읽을 수 없습니다: {full_path}")
            return {'matched_sql': 0, 'relationships_created': 0}
        # 대소문자 구분 매칭을 위해 원문 그대로 사용

        # 파일 내 모든 METHOD 컴포넌트 조회 (없으면 에러 처리)
        method_ids = self._get_method_components(project_id, file_info['file_id'])
        if not method_ids:
            warning(f"METHOD 컴포넌트 없음: {full_path} (sqltext 매칭 스킵)")
            return {'matched_sql': 0, 'relationships_created': 0}

        for sql_comp in sql_components:
            sql_id = sql_comp['component_name']
            # 대소문자 구분하여 SQL ID 리터럴이 그대로 존재하는지 확인
            if sql_id and sql_id in content:
                matched_sql += 1
                for method_id in method_ids:
                    rel_data = {
                        'src_id': method_id,
                        'dst_id': sql_comp['component_id'],
                        'rel_type': 'CALL_QUERY',
                        'del_yn': 'N'
                    }
                    self.db_utils.insert_or_replace('relationships', rel_data)
                    relationships_created += 1
                debug(f"sqltext 매칭: {file_info['file_name']} 포함 SQL_ID={sql_id} -> METHOD {len(method_ids)}개 연결")

        return {'matched_sql': matched_sql, 'relationships_created': relationships_created}

    def _get_method_components(self, project_id: int, file_id: int) -> List[int]:
        """해당 Java 파일의 METHOD 컴포넌트 ID 리스트 반환"""
        try:
            query = """
                SELECT component_id
                FROM components
                WHERE project_id = ?
                  AND file_id = ?
                  AND component_type = 'METHOD'
                  AND del_yn = 'N'
            """
            rows = self.db_utils.execute_query(query, (project_id, file_id), conn=self.conn)
            return [row['component_id'] for row in rows] if rows else []
        except Exception as e:
            handle_error(e, "Java 컴포넌트 조회 실패")
            return []


def execute_sqltext_java_matching(project_name: str, conn) -> bool:
    """편의 함수"""
    matcher = SqlTextJavaMatcher(project_name, conn)
    return matcher.execute()
