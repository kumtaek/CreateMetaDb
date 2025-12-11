"""
Frontend Mapping Report 생성기
- 메타DB(metadata.db)에 저장된 관계만 활용하여 프론트엔드 → API_URL → METHOD → SQL_QUERY 체인을 시각화
- 추가 재파싱 없이 metadata.db 조회 결과만 사용
"""

import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any

from util.logger import app_logger, handle_error
from util.path_utils import PathUtils
from util.report_utils import ReportUtils


class FrontendMappingReportGenerator:
    """프론트엔드 매핑 리포트 생성기"""

    def __init__(self, project_name: str, output_dir: str):
        self.project_name = project_name
        self.output_dir = output_dir
        self.path_utils = PathUtils()
        self.report_utils = ReportUtils(project_name, output_dir)
        self.metadata_db_path = self.path_utils.join_path('projects', project_name, 'metadata.db')

    def generate_report(self) -> bool:
        """리포트 생성 메인 메서드"""
        conn = None
        try:
            app_logger.info(f"Frontend Mapping Report 생성 시작: {self.project_name}")

            conn = sqlite3.connect(self.metadata_db_path)
            conn.row_factory = sqlite3.Row

            mapping_rows = self._fetch_mapping_data(conn)
            app_logger.info(f"프론트엔드 매핑 데이터 로드: {len(mapping_rows)}건")

            html_content = self._generate_html(mapping_rows)

            # 리소스 복사
            self.report_utils.copy_assets()

            # 파일 저장
            output_file = self.report_utils.save_report(html_content, "FrontendMappingReport")
            app_logger.info(f"Frontend Mapping Report 생성 완료: {output_file}")
            return True

        except Exception as e:
            handle_error(e, "Frontend Mapping Report 생성 실패")
            return False
        finally:
            if conn:
                conn.close()

    def _fetch_mapping_data(self, conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        """metadata.db에서 프론트→API→METHOD→SQL QUERY 체인 조회"""
        try:
            cursor = conn.cursor()

            project_id = self.project_name_to_id(conn)
            if not project_id:
                return []

            query = """
            WITH base AS (
                SELECT
                    f.component_name   AS frontend_name,
                    ff.file_name       AS frontend_file,
                    ff.file_path       AS frontend_path,
                    api.component_name AS api_url,
                    COALESCE(m_rel.component_id, m_file.component_id)       AS method_id,
                    COALESCE(m_rel.component_name, m_file.component_name)   AS method_name,
                    COALESCE(m_rel.file_id, m_file.file_id)                 AS method_file_id
                FROM relationships r_api
                JOIN components f   ON r_api.src_id = f.component_id    AND r_api.rel_type = 'CALL_API' AND r_api.del_yn = 'N' AND f.del_yn = 'N'
                JOIN components api ON r_api.dst_id = api.component_id  AND api.del_yn = 'N'
                LEFT JOIN files ff   ON f.file_id   = ff.file_id
                LEFT JOIN relationships r_m ON r_m.src_id = api.component_id AND r_m.rel_type = 'CALL_METHOD' AND r_m.del_yn = 'N'
                LEFT JOIN components m_rel ON r_m.dst_id = m_rel.component_id AND m_rel.del_yn = 'N'
                LEFT JOIN components m_file ON m_file.file_id = api.file_id AND m_file.component_type = 'METHOD' AND m_file.del_yn = 'N'
                WHERE f.project_id = ?
            )
            SELECT DISTINCT
                b.frontend_name,
                b.frontend_file,
                b.frontend_path,
                b.api_url,
                b.method_name,
                mf.file_name   AS method_file,
                mf.file_path   AS method_path,
                q.component_name AS query_id
            FROM base b
            LEFT JOIN relationships r_q ON r_q.src_id = b.method_id AND r_q.rel_type = 'CALL_QUERY' AND r_q.del_yn = 'N'
            LEFT JOIN components q ON r_q.dst_id = q.component_id AND q.del_yn = 'N'
            LEFT JOIN files mf ON b.method_file_id = mf.file_id
            ORDER BY b.frontend_path, b.frontend_file, b.api_url, b.method_name, q.component_name
            """

            cursor.execute(query, (project_id,))
            rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append({
                    'frontend_name': row['frontend_name'] or '-',
                    'frontend_file': self._combine_path(row['frontend_path'], row['frontend_file']),
                    'api_url': row['api_url'] or '-',
                    'method_name': row['method_name'] or '-',
                    'method_file': self._combine_path(row['method_path'], row['method_file']) if row['method_file'] else '-',
                    'query_id': row['query_id'] or '-'
                })
            return result
        except Exception as e:
            handle_error(e, "프론트엔드 매핑 데이터 조회 실패")
            return []

    def project_name_to_id(self, conn: sqlite3.Connection) -> int:
        """프로젝트 ID 조회"""
        cursor = conn.cursor()
        cursor.execute("SELECT project_id FROM projects WHERE project_name = ? AND del_yn = 'N'", (self.project_name,))
        row = cursor.fetchone()
        if not row:
            handle_error(Exception("프로젝트 ID 없음"), f"프로젝트 ID를 찾을 수 없습니다: {self.project_name}")
            return 0
        return row[0]

    def _combine_path(self, dir_path: str, file_name: str) -> str:
        """경로와 파일명을 합쳐 표현 (슬래시 정규화)"""
        dir_path = dir_path or ''
        if dir_path.endswith('/'):
            return f"{dir_path}{file_name}"
        if dir_path:
            return f"{dir_path}/{file_name}"
        return file_name or '-'

    def _generate_html(self, data: List[Dict[str, Any]]) -> str:
        """HTML 생성 (단순 테이블)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rows_html = []
        for idx, row in enumerate(data, 1):
            rows_html.append(f"""
                <tr>
                    <td>{idx}</td>
                    <td>{row['frontend_name']}</td>
                    <td>{row['frontend_file']}</td>
                    <td>{row['api_url']}</td>
                    <td>{row['method_name']}</td>
                    <td>{row['method_file']}</td>
                    <td>{row['query_id']}</td>
                </tr>
            """)

        html = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <title>Frontend Mapping Report - {self.project_name}</title>
            <link rel="stylesheet" type="text/css" href="css/woori.css">
        </head>
        <body>
            <h2>Frontend Mapping Report</h2>
            <p>Project: {self.project_name} / Generated at: {timestamp}</p>
            <table class="table table-bordered table-striped">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Frontend Component</th>
                        <th>Frontend File</th>
                        <th>API URL</th>
                        <th>Method</th>
                        <th>Method File</th>
                        <th>Query ID</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows_html)}
                </tbody>
            </table>
        </body>
        </html>
        """
        return html
