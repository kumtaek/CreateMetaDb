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
from util.runtime_options import get_report_folders
from util.report_filter_utils import ReportFilterUtils


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
        """metadata.db에서 METHOD 중심으로 Frontend/API/Query 연계를 조회"""
        try:
            cursor = conn.cursor()

            project_id = self.project_name_to_id(conn)
            if not project_id:
                return []

            query = """
            SELECT DISTINCT
                m.component_name AS method_name,
                mf.file_name     AS method_file,
                mf.file_path     AS method_path,
                COALESCE(api.component_name, '-') AS api_url,
                COALESCE(ff.file_path, '-')       AS frontend_path,
                COALESCE(ff.file_name, '-')       AS frontend_file,
                q.component_name                  AS query_id,
                qf.file_name                      AS query_file,
                qf.file_path                      AS query_path
            FROM components m
            JOIN files mf ON m.file_id = mf.file_id
            LEFT JOIN relationships r_am
                ON r_am.dst_id = m.component_id
               AND r_am.rel_type = 'CALL_METHOD'
               AND r_am.del_yn = 'N'
            LEFT JOIN components api
                ON r_am.src_id = api.component_id
               AND api.component_type = 'API_URL'
               AND api.del_yn = 'N'
            LEFT JOIN relationships r_f
                ON r_f.dst_id = api.component_id
               AND r_f.rel_type = 'CALL_API'
               AND r_f.del_yn = 'N'
            LEFT JOIN components f
                ON r_f.src_id = f.component_id
               AND f.del_yn = 'N'
            LEFT JOIN files ff ON f.file_id = ff.file_id AND ff.del_yn = 'N'
            LEFT JOIN relationships r_q
                ON r_q.src_id = m.component_id
               AND r_q.rel_type = 'CALL_QUERY'
               AND r_q.del_yn = 'N'
            LEFT JOIN components q ON r_q.dst_id = q.component_id AND q.del_yn = 'N'
            LEFT JOIN files qf ON q.file_id = qf.file_id AND qf.del_yn = 'N'
            WHERE m.project_id = ?
              AND m.component_type = 'METHOD'
              AND m.del_yn = 'N'
              AND mf.del_yn = 'N'
            ORDER BY frontend_path, frontend_file, api_url, method_path, method_file, method_name, query_file, query_id
            """

            cursor.execute(query, (project_id,))
            rows = cursor.fetchall()

            folder_filters = get_report_folders()
            filter_utils = ReportFilterUtils()

            result = []
            for row in rows:
                if folder_filters:
                    frontend_path = row['frontend_path'] or ''
                    method_path = row['method_path'] or ''
                    query_path = row['query_path'] or ''
                    if not (
                        filter_utils.is_path_in_folders(frontend_path, folder_filters)
                        or filter_utils.is_path_in_folders(method_path, folder_filters)
                        or filter_utils.is_path_in_folders(query_path, folder_filters)
                    ):
                        continue
                result.append({
                    'frontend_path': row['frontend_path'] or '-',
                    'frontend_file': row['frontend_file'] or '-',
                    'api_url': row['api_url'] or '-',
                    'method_file': self._combine_path(row['method_path'], row['method_file']),
                    'method_name': row['method_name'] or '-',
                    'query_file': self._combine_path(row['query_path'], row['query_file']) if row['query_file'] else '-',
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
        """HTML 생성 (Backend Mapping Report와 동일 톤/스타일)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        def sort_key(val: str) -> str:
            norm = (val or "").lower()
            # '-' 표시는 뒤로 보내기 위한 보조 키
            return f"1|{norm}" if norm == "-" else f"0|{norm}"

        sorted_data = sorted(
            data,
            key=lambda row: (
                sort_key(row.get('frontend_path')),
                sort_key(row.get('frontend_file')),
                sort_key(row.get('api_url')),
                sort_key(row.get('method_file')),
                sort_key(row.get('method_name')),
                sort_key(row.get('query_file')),
                sort_key(row.get('query_id')),
            ),
        )

        rows_html = ""
        for idx, row in enumerate(sorted_data, 1):
            rows_html += f"""
            <tr>
                <td>{idx}</td>
                <td>{row['frontend_path']}</td>
                <td>{row['frontend_file']}</td>
                <td>{row['api_url']}</td>
                <td>{row['method_file']}</td>
                <td>{row['method_name']}</td>
                <td>{row['query_file']}</td>
                <td>{row['query_id']}</td>
            </tr>
            """

        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Frontend Mapping Report - {self.project_name}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; font-size: 9pt; font-weight: normal; }}
        strong {{ font-weight: normal; }}
        .container {{ max-width: 1800px; margin: 0 auto; background: white; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; font-size: 1.2em; font-weight: normal; }}
        .info {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; font-weight: normal; font-size: 9pt; }}
        th {{ background-color: #3498db; color: white; font-weight: normal; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        tr:hover {{ background-color: #e8f4f8; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Frontend Mapping Report</h1>
        <div class="info">
            <strong>프로젝트:</strong> {self.project_name}<br>
            <strong>생성일시:</strong> {timestamp}
        </div>
        <table>
            <thead>
                <tr>
                    <th style="width:50px;">No</th>
                    <th style="width:220px;">Frontend Path</th>
                    <th style="width:180px;">Frontend File</th>
                    <th style="width:240px;">API URL</th>
                    <th style="width:220px;">Method File</th>
                    <th style="width:200px;">Method</th>
                    <th style="width:200px;">XML File</th>
                    <th style="width:180px;">Query ID</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
</body>
</html>"""
