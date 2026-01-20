"""
Query List Report 생성기
- Java, XML에서 도출된 쿼리 리스트 조회
- file(xml, java), query_id, query, 관련 테이블 컬럼으로 구성
- 콜체인 리포트와 유사한 구조로 구현
"""

import os
import sys
import gzip
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from util.logger import app_logger, handle_error
from util.path_utils import PathUtils
from util.database_utils import DatabaseUtils
from util.report_utils import ReportUtils
from util.sql_content_manager import SqlContentManager
from util import get_sql_compress
from util.runtime_options import get_report_folders
from util.report_filter_utils import ReportFilterUtils
from reports.report_templates import ReportTemplates


class QueryListReportGenerator:
    """Query List Report 생성기 클래스"""
    
    def __init__(self, project_name: str, output_dir: str):
        """
        초기화
        
        Args:
            project_name: 프로젝트명
            output_dir: 출력 디렉토리
        """
        self.project_name = project_name
        self.output_dir = output_dir
        self.path_utils = PathUtils()
        self.templates = ReportTemplates()
        self.report_utils = ReportUtils(project_name, output_dir)
        
        # 메타데이터베이스 연결
        self.metadata_db_path = self.path_utils.get_project_metadata_db_path(project_name)
        self.db_utils = DatabaseUtils(self.metadata_db_path)
        
        # SqlContent 데이터베이스 연결
        self.sql_content_manager = SqlContentManager(project_name)
        
        if not self.db_utils.connect():
            handle_error(Exception("데이터베이스 연결 실패"), f"메타데이터베이스 연결 실패: {self.metadata_db_path}")
    
    def generate_report(self) -> bool:
        """
        Query List Report 생성
        
        Returns:
            생성 성공 여부 (True/False)
        """
        try:
            app_logger.info(f"Query List Report 생성 시작: {self.project_name}")
            
            # 1. 프로젝트 ID 조회
            project_id = self._get_project_id()
            if not project_id:
                handle_error(Exception("프로젝트를 찾을 수 없음"), f"프로젝트 ID 조회 실패: {self.project_name}")
            
            # 2. 통계 정보 조회
            stats = self._get_statistics(project_id)
            
            # 3. 쿼리 리스트 데이터 조회
            query_data = self._get_query_list_data(project_id)
            
            # 4. HTML 생성
            html_content = self._generate_html(stats, query_data)
            
            # 5. CSS 및 JS 파일 복사
            self.report_utils.copy_assets()
            
            # 6. 파일 저장
            output_file = self.report_utils.save_report(html_content, "QueryListReport")
            
            app_logger.info(f"Query List Report 생성 완료: {output_file}")
            return True
            
        except Exception as e:
            handle_error(e, "Query List Report 생성 실패")
            return False
        finally:
            self.db_utils.disconnect()
            if self.sql_content_manager:
                self.sql_content_manager.close()
    
    def _get_project_id(self) -> Optional[int]:
        """프로젝트 ID 조회"""
        try:
            query = "SELECT project_id FROM projects WHERE project_name = ? AND del_yn = 'N'"
            results = self.db_utils.execute_query(query, (self.project_name,))
            
            if results:
                # DatabaseUtils는 딕셔너리 형태로 결과를 반환
                return results[0]['project_id']
            return None
            
        except Exception as e:
            handle_error(e, "프로젝트 ID 조회 실패")
            return None
    
    def _get_statistics(self, project_id: int) -> Dict[str, int]:
        """통계 정보 조회"""
        try:
            # 전체 쿼리 개수
            total_query = """
            SELECT COUNT(*) 
            FROM components c
            WHERE c.project_id = ? 
            AND c.component_type LIKE 'SQL_%' 
            AND c.del_yn = 'N'
            """
            total_results = self.db_utils.execute_query(total_query, (project_id,))
            total_queries = total_results[0]['COUNT(*)'] if total_results else 0
            
            # Java 파일에서 도출된 쿼리 개수
            java_query = """
            SELECT COUNT(*) 
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            WHERE c.project_id = ? 
            AND c.component_type LIKE 'SQL_%' 
            AND f.file_type = 'JAVA'
            AND c.del_yn = 'N'
            """
            java_results = self.db_utils.execute_query(java_query, (project_id,))
            java_queries = java_results[0]['COUNT(*)'] if java_results else 0
            
            # XML 파일에서 도출된 쿼리 개수
            xml_query = """
            SELECT COUNT(*) 
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            WHERE c.project_id = ? 
            AND c.component_type LIKE 'SQL_%' 
            AND f.file_type = 'XML'
            AND c.del_yn = 'N'
            """
            xml_results = self.db_utils.execute_query(xml_query, (project_id,))
            xml_queries = xml_results[0]['COUNT(*)'] if xml_results else 0
            
            # 관련 테이블 개수
            table_query = """
            SELECT COUNT(DISTINCT t.table_name)
            FROM components c
            JOIN relationships r ON c.component_id = r.src_id
            JOIN tables t ON r.dst_id = t.component_id
            WHERE c.project_id = ? 
            AND c.component_type LIKE 'SQL_%' 
            AND r.rel_type = 'USE_TABLE'
            AND c.del_yn = 'N'
            AND r.del_yn = 'N'
            """
            table_results = self.db_utils.execute_query(table_query, (project_id,))
            related_tables = table_results[0]['COUNT(DISTINCT t.table_name)'] if table_results else 0
            
            return {
                'total_queries': total_queries,
                'java_queries': java_queries,
                'xml_queries': xml_queries,
                'related_tables': related_tables
            }
            
        except Exception as e:
            handle_error(e, "통계 정보 조회 실패")
            return {
                'total_queries': 0,
                'java_queries': 0,
                'xml_queries': 0,
                'related_tables': 0
            }
    
    def _get_query_list_data(self, project_id: int) -> List[Dict[str, Any]]:
        """쿼리 리스트 데이터 조회 - SqlContent.db에서 직접 조회"""
        try:
            import sqlite3
            
            sql_db_name = "SqlContent_compressed.db" if get_sql_compress() else "SqlContent.db"
            sqlcontent_conn = sqlite3.connect(f'projects/{self.project_name}/{sql_db_name}')
            sqlcontent_cursor = sqlcontent_conn.cursor()
            
            query = """
            SELECT 
                component_name,
                file_path,
                sql_content_compressed,
                hash_value,
                created_at
            FROM sql_contents 
            WHERE del_yn = 'N'
            ORDER BY file_path, component_name
            """
            
            sqlcontent_cursor.execute(query)
            results = sqlcontent_cursor.fetchall()
            
            query_data = []
            for row in results:
                component_name = row[0]
                file_path = row[1] or ''  # Ensure file_path is a string
                sql_content_compressed = row[2]
                hash_value = row[3]
                created_at = row[4]
                
                # SQL 내용 압축 해제
                sql_content = self._decompress_sql_content(sql_content_compressed)
                
                # 파일 타입 결정 (fallback to UNKNOWN if path is empty)
                if file_path:
                    file_type = 'XML' if file_path.lower().endswith('.xml') else 'JAVA'
                else:
                    file_type = 'UNKNOWN'
                
                # SQL 내용에서 테이블명 추출
                extracted_tables = self._extract_tables_from_sql(sql_content)
                related_tables = ', '.join(extracted_tables) if extracted_tables else 'N/A'
                
                # 쿼리 타입 결정
                query_type = self._determine_query_type(sql_content)
                
                query_info = {
                    'component_id': 0,  # SqlContent에는 component_id가 없음
                    'query_id': component_name,
                    'component_type': query_type,
                    'file_path': file_path,
                    'file_name': os.path.basename(file_path) if file_path else 'Unknown',
                    'file_type': file_type,
                    'line_start': 0,  # SqlContent에는 라인 정보가 없음
                    'line_end': 0,
                    'sql_content': sql_content,
                    'related_tables': related_tables
                }
                query_data.append(query_info)
            
            sqlcontent_conn.close()

            folder_filters = get_report_folders()
            if folder_filters:
                filter_utils = ReportFilterUtils()
                query_data = filter_utils.filter_rows_by_paths(query_data, ['file_path'], folder_filters)
            
            app_logger.info(f"쿼리 리스트 데이터 조회 완료: {len(query_data)}개")
            return query_data
            
        except Exception as e:
            handle_error(e, "쿼리 리스트 데이터 조회 실패")
            return []
    
    def _get_sql_content(self, component_id: int) -> str:
        """SqlContent에서 실제 SQL 내용 조회"""
        try:
            # SqlContent 데이터베이스에서 쿼리 내용 조회
            query = """
            SELECT sql_content_compressed
            FROM sql_contents 
            WHERE component_id = ? AND del_yn = 'N'
            """
            
            results = self.sql_content_manager.db_utils.execute_query(query, (component_id,))
            
            if results:
                compressed_data = results[0]['sql_content_compressed']
                # gzip 압축 해제
                sql_content = self.sql_content_manager._decompress_content(compressed_data)
                return sql_content
            else:
                return "SQL 내용을 찾을 수 없음"
                
        except Exception as e:
            app_logger.warning(f"SQL 내용 조회 실패 (component_id: {component_id}): {str(e)}")
            return "SQL 내용 조회 실패"
    
    def _extract_tables_from_sql(self, sql_content: str) -> List[str]:
        """SQL 내용에서 테이블명 추출 (키워드 필터링 적용)"""
        try:
            import re
            from util.oracle_keyword_manager import is_literal_value, is_oracle_keyword
            tables = set()
            
            # SQL을 대문자로 변환하여 처리
            sql_upper = sql_content.upper()
            
            # FROM 절에서 테이블명 추출
            from_pattern = r'\bFROM\s+([A-Z_][A-Z0-9_]*)'
            from_matches = re.findall(from_pattern, sql_upper)
            tables.update(from_matches)
            
            # JOIN 절에서 테이블명 추출
            join_pattern = r'\bJOIN\s+([A-Z_][A-Z0-9_]*)'
            join_matches = re.findall(join_pattern, sql_upper)
            tables.update(join_matches)
            
            # UPDATE 절에서 테이블명 추출
            update_pattern = r'\bUPDATE\s+([A-Z_][A-Z0-9_]*)'
            update_matches = re.findall(update_pattern, sql_upper)
            tables.update(update_matches)
            
            # INSERT INTO 절에서 테이블명 추출
            insert_pattern = r'\bINSERT\s+INTO\s+([A-Z_][A-Z0-9_]*)'
            insert_matches = re.findall(insert_pattern, sql_upper)
            tables.update(insert_matches)
            
            # DELETE FROM 절에서 테이블명 추출
            delete_pattern = r'\bDELETE\s+FROM\s+([A-Z_][A-Z0-9_]*)'
            delete_matches = re.findall(delete_pattern, sql_upper)
            tables.update(delete_matches)
            
            # SQL 키워드/리터럴 필터링 (YAML 설정 기반)
            filtered_tables = set()
            for table in tables:
                # 리터럴 값이나 Oracle 키워드는 제외
                if not is_literal_value(table) and not is_oracle_keyword(table):
                    filtered_tables.add(table)
            
            # 실제 테이블 오너 정보를 조회하여 접두사 추가
            prefixed_tables = set()
            for table in filtered_tables:
                # 데이터베이스에서 실제 테이블 오너 조회
                owner = self._get_table_owner(table)
                if owner:
                    prefixed_tables.add(f'{owner}.{table}')
                else:
                    prefixed_tables.add(table)
            
            return list(prefixed_tables)
            
        except Exception as e:
            app_logger.debug(f"SQL 테이블명 추출 실패: {str(e)}")
            return []
    
    def _get_table_owner(self, table_name: str) -> Optional[str]:
        """테이블 오너 정보 조회"""
        try:
            # 실제 데이터베이스에서 테이블 오너 조회
            query = """
                SELECT table_owner
                FROM tables t
                JOIN projects p ON t.project_id = p.project_id
                WHERE p.project_name = ? 
                AND t.table_name = ?
                AND t.del_yn = 'N'
                LIMIT 1
            """
            
            result = self.db_utils.execute_query(query, (self.project_name, table_name.upper()))
            if result:
                return result[0]['table_owner']
            
            # 기본값 반환 (SAMPLE이 대부분)
            return 'SAMPLE'
            
        except Exception as e:
            app_logger.debug(f"테이블 오너 조회 실패: {table_name} - {str(e)}")
            return 'SAMPLE'
    
    def _decompress_sql_content(self, compressed_data: bytes) -> str:
        """압축된 SQL 내용을 gzip으로 압축 해제"""
        try:
            return gzip.decompress(compressed_data).decode('utf-8')
        except Exception as e:
            app_logger.warning(f"SQL 내용 압축 해제 실패: {str(e)}")
            try:
                # Fallback: 압축되지 않은 데이터로 시도
                return compressed_data.decode('utf-8', errors='replace')
            except:
                return "SQL 내용 압축 해제 실패"
    
    def _determine_query_type(self, sql_content: str) -> str:
        """SQL 내용을 기반으로 쿼리 타입 결정"""
        try:
            sql_upper = sql_content.upper().strip()
            
            if sql_upper.startswith('SELECT'):
                return 'SQL_SELECT'
            elif sql_upper.startswith('INSERT'):
                return 'SQL_INSERT'
            elif sql_upper.startswith('UPDATE'):
                return 'SQL_UPDATE'
            elif sql_upper.startswith('DELETE'):
                return 'SQL_DELETE'
            elif sql_upper.startswith('MERGE'):
                return 'SQL_MERGE'
            else:
                return 'SQL_QUERY'
                
        except Exception as e:
            app_logger.debug(f"쿼리 타입 결정 실패: {str(e)}")
            return 'SQL_QUERY'
    
    def _generate_html(self, stats: Dict[str, int], query_data: List[Dict[str, Any]]) -> str:
        """HTML 생성"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 통계 카드 HTML 생성
            stats_html = self._generate_stats_html(stats)
            
            # 쿼리 리스트 테이블 HTML 생성
            table_html = self._generate_query_table_html(query_data)
            
            return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Query List Report - {self.project_name}</title>
    <link rel="stylesheet" href="css/woori.css">
    <style>
        .query-list-body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 2px;
            background: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%);
            min-height: 100vh;
        }}
        .query-list-container {{
            width: 100%;
            max-width: none;
            margin: 0;
            background: white;
            border-radius: 4px;
            box-shadow: 0 4px 8px rgba(25, 118, 210, 0.16);
            overflow: hidden;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        .query-list-header {{
            background: linear-gradient(90deg, #0d47a1 0%, #1976d2 100%);
            color: white;
            padding: 4px 8px;
            margin-bottom: 3px;
            position: sticky;
            top: 0;
            z-index: 100;
            flex-shrink: 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            min-height: 40px;
        }}
        .header-left {{
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }}
        .header-left h1 {{
            margin: 0;
            font-size: 1.2em;
            font-weight: 300;
            color: white;
            line-height: 1.2;
        }}
        .subtitle {{
            margin: 2px 0 0 0;
            opacity: 0.8;
            font-size: 0.7em;
            color: white;
            line-height: 1.2;
        }}
        .header-right {{
            display: flex;
            align-items: center;
        }}
        .csv-export-btn {{
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.7em;
            transition: all 0.3s ease;
            margin: 0;
        }}
        .csv-export-btn:hover {{
            background: rgba(255,255,255,0.3);
        }}
        .query-list-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 6px;
            padding: 6px;
            background: #f8f9fa;
            margin-bottom: 3px;
            position: sticky;
            top: 43px;
            z-index: 99;
            flex-shrink: 0;
        }}
        .query-list-stat-card {{
            background: white;
            padding: 6px;
            border-radius: 4px;
            text-align: center;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        .query-list-stat-card:hover {{
            transform: translateY(-1px);
        }}
        .query-list-stat-number {{
            font-size: 1.0em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 2px;
        }}
        .query-list-stat-label {{
            color: #7f8c8d;
            font-size: 0.7em;
            font-weight: 500;
        }}
        .query-list-content {{
            padding: 2px;
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
            min-height: 0;
        }}
        .query-list-table-container {{
            background: white;
            border-radius: 4px;
            overflow: auto;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            flex: 1;
            min-height: 0;
        }}
        .query-list-table {{
            width: 100%;
            border-collapse: collapse;
            table-layout: auto;
            min-width: 1000px;
        }}
        .query-list-table th {{
            background: #3498db;
            color: white;
            padding: 8px 6px;
            text-align: left;
            font-weight: 600;
            font-size: 0.8em;
            position: sticky;
            top: 0;
            z-index: 98;
            white-space: nowrap;
        }}
        .query-list-table td {{
            padding: 6px;
            border-bottom: 1px solid #eee;
            font-size: 0.8em;
            vertical-align: top;
            white-space: nowrap;
            cursor: pointer;
            transition: background-color 0.2s ease;
        }}
        .query-list-table td:hover {{
            background-color: #f0f8ff;
        }}
        .query-list-table td.copied {{
            background-color: #e8f5e8 !important;
            color: #2e7d32;
        }}
        .query-list-table td.copied::after {{
            content: " ✓ 복사됨";
            font-size: 0.7em;
            color: #2e7d32;
            margin-left: 5px;
        }}
        .query-list-table tr:hover {{
            background-color: #bbdefb;
            box-shadow: 0 4px 8px rgba(25, 118, 210, 0.4);
            transform: translateY(-2px);
            transition: all 0.2s ease;
            border-left: 4px solid #1976d2;
        }}
        /* 컬럼 너비 설정 - 내용에 맞춰 자동 조정, SQL만 넓게 설정 */
        .query-list-table th:nth-child(1), .query-list-table td:nth-child(1) {{ width: auto; min-width: 120px; max-width: 200px; }} /* 파일명 - 내용에 맞춰 줄임 */
        .query-list-table th:nth-child(2), .query-list-table td:nth-child(2) {{ width: auto; min-width: 100px; max-width: 150px; }} /* 쿼리 ID - 내용에 맞춰 줄임 */
        .query-list-table th:nth-child(3), .query-list-table td:nth-child(3) {{ width: 800px; min-width: 800px; }} /* SQL 내용 - 더 넓게 설정 */
        .query-list-table th:nth-child(4), .query-list-table td:nth-child(4) {{ width: auto; min-width: 120px; max-width: 200px; }} /* 관련 테이블 - 내용에 맞춰 줄임 */
        .file-type-java {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: 500;
            font-size: 0.7em;
        }}
        .file-type-xml {{
            background: #fff3e0;
            color: #f57c00;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: 500;
            font-size: 0.7em;
        }}
        .query-list-table td:nth-child(3) {{
            font-family: 'Courier New', monospace;
            font-size: 0.7em;
            background: #f5f5f5;
            padding: 4px;
            border-left: 2px solid #3498db;
            white-space: pre-wrap;
            word-break: break-all;
            vertical-align: top;
        }}
        .sql-content:hover {{
            background: #e3f2fd;
            border-left-color: #1976d2;
        }}
        .sql-content.copied {{
            background: #e8f5e8 !important;
            border-left-color: #2e7d32 !important;
            color: #2e7d32;
        }}
        .sql-content.copied::after {{
            content: " ✓ SQL 복사됨";
            font-size: 0.6em;
            color: #2e7d32;
            display: block;
            margin-top: 2px;
            font-weight: bold;
        }}
        .related-tables {{
            color: #666;
            font-size: 0.7em;
            word-break: break-all;
        }}
        .query-type {{
            background: #e8f5e8;
            color: #2e7d32;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: 500;
            font-size: 0.7em;
        }}
        /* 반응형 디자인 */
        @media (max-width: 768px) {{
            .query-list-table {{
                font-size: 0.7em;
                min-width: 800px;
            }}
            .query-list-table th, .query-list-table td {{
                padding: 4px 2px;
            }}
            .query-list-table th:nth-child(3), .query-list-table td:nth-child(3) {{ width: 500px; min-width: 500px; }} /* SQL 내용 조정 */
        }}
        @media (max-width: 480px) {{
            .query-list-stats {{
                grid-template-columns: repeat(2, 1fr);
            }}
            .query-list-table {{
                min-width: 600px;
            }}
            .query-list-table th:nth-child(3), .query-list-table td:nth-child(3) {{ width: 400px; min-width: 400px; }} /* SQL 내용 더 조정 */
        }}
    </style>
</head>
<body class="query-list-body">
    <div class="query-list-container">
        <div class="query-list-header">
            <div class="header-left">
                <h1>Query List Report</h1>
                <div class="subtitle">프로젝트: {self.project_name} | 생성일시: {timestamp}</div>
            </div>
            <div class="header-right">
                <button onclick="exportToCSV()" class="csv-export-btn">📊 CSV 다운로드</button>
            </div>
        </div>
        {stats_html}
        <div class="query-list-content">
            <div class="query-list-table-container">
                <table id="queryTable" class="query-list-table">
                    <thead>
                        <tr>
                            <th>파일명</th>
                            <th>쿼리 ID</th>
                            <th>SQL 내용</th>
                            <th>관련 테이블</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_html}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        function exportToCSV() {{
            const table = document.getElementById('queryTable');
            const rows = table.querySelectorAll('tr');
            let csv = [];
            
            for (let i = 0; i < rows.length; i++) {{
                const row = rows[i];
                const cols = row.querySelectorAll('td, th');
                let csvRow = [];
                
                for (let j = 0; j < cols.length; j++) {{
                    let cellText = cols[j].textContent || cols[j].innerText;
                    // CSV에서 쉼표와 따옴표 처리
                    if (cellText.includes(',') || cellText.includes('"') || cellText.includes('\\n')) {{
                        cellText = '"' + cellText.replace(/"/g, '""') + '"';
                    }}
                    csvRow.push(cellText);
                }}
                csv.push(csvRow.join(','));
            }}
            
            const csvContent = csv.join('\\n');
            // CP949 인코딩을 위한 BOM 추가
            const BOM = '\\uFEFF';
            const csvWithBOM = BOM + csvContent;
            const blob = new Blob([csvWithBOM], {{ type: 'text/csv;charset=cp949;' }});
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', 'query_list_{timestamp.replace(" ", "_").replace(":", "")}.csv');
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }}

        // 클립보드 복사 함수
        async function copyToClipboard(text) {{
            try {{
                await navigator.clipboard.writeText(text);
                return true;
            }} catch (err) {{
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                try {{
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    return true;
                }} catch (fallbackErr) {{
                    document.body.removeChild(textArea);
                    return false;
                }}
            }}
        }}

        // 복사 완료 시각적 피드백
        function showCopyFeedback(element, text) {{
            // 기존 복사 표시 제거
            document.querySelectorAll('.copied').forEach(el => {{
                el.classList.remove('copied');
            }});
            
            // 새로운 복사 표시 추가
            element.classList.add('copied');
            
            // 2초 후 복사 표시 제거
            setTimeout(() => {{
                element.classList.remove('copied');
            }}, 2000);
            
            // 브라우저 알림 (선택사항)
            if (navigator.clipboard) {{
                console.log(`복사됨: ${{text.substring(0, 50)}}${{text.length > 50 ? '...' : ''}}`);
            }}
        }}

        // 페이지 로드 시 더블클릭 이벤트 리스너 추가
        document.addEventListener('DOMContentLoaded', function() {{
            const table = document.getElementById('queryTable');
            const cells = table.querySelectorAll('td');
            
            cells.forEach(cell => {{
                cell.addEventListener('dblclick', async function(e) {{
                    e.preventDefault();
                    
                    let textToCopy = '';
                    let elementToHighlight = this;
                    
                    // SQL 내용 셀인지 확인 (3번째 컬럼)
                    if (this.cellIndex === 2) {{
                        // SQL 내용 복사
                        const sqlContent = this.querySelector('.sql-content');
                        if (sqlContent) {{
                            textToCopy = sqlContent.textContent || sqlContent.innerText;
                            elementToHighlight = sqlContent;
                        }} else {{
                            textToCopy = this.textContent || this.innerText;
                        }}
                    }} else {{
                        // 일반 셀 내용 복사
                        textToCopy = this.textContent || this.innerText;
                    }}
                    
                    // 텍스트가 있는 경우에만 복사
                    if (textToCopy && textToCopy.trim()) {{
                        const success = await copyToClipboard(textToCopy.trim());
                        if (success) {{
                            showCopyFeedback(elementToHighlight, textToCopy);
                        }} else {{
                            alert('클립보드 복사에 실패했습니다.');
                        }}
                    }}
                }});
                
                // 셀에 툴팁 추가
                cell.title = '더블클릭하여 복사';
            }});
        }});
    </script>
</body>
</html>"""
            
        except Exception as e:
            handle_error(e, "HTML 생성 실패")
            return ""
    
    def _generate_stats_html(self, stats: Dict[str, int]) -> str:
        """통계 카드 HTML 생성"""
        try:
            return f"""
            <div class="query-list-stats">
                <div class="query-list-stat-card">
                    <div class="query-list-stat-number">{stats['total_queries']}</div>
                    <div class="query-list-stat-label">전체 쿼리</div>
                </div>
                <div class="query-list-stat-card">
                    <div class="query-list-stat-number">{stats['java_queries']}</div>
                    <div class="query-list-stat-label">Java 쿼리</div>
                </div>
                <div class="query-list-stat-card">
                    <div class="query-list-stat-number">{stats['xml_queries']}</div>
                    <div class="query-list-stat-label">XML 쿼리</div>
                </div>
                <div class="query-list-stat-card">
                    <div class="query-list-stat-number">{stats['related_tables']}</div>
                    <div class="query-list-stat-label">관련 테이블</div>
                </div>
            </div>
            """
            
        except Exception as e:
            handle_error(e, "통계 HTML 생성 실패")
            return ""
    
    def _generate_query_table_html(self, query_data: List[Dict[str, Any]]) -> str:
        """쿼리 테이블 HTML 생성"""
        try:
            if not query_data:
                return "<tr><td colspan='7' style='text-align: center; padding: 50px; color: #999;'>조회된 쿼리가 없습니다.</td></tr>"
            
            rows = []
            for query in query_data:
                file_type_class = f"file-type-{query['file_type'].lower()}"
                query_type_class = "query-type"
                
                # SQL 내용 전체 표시 (HTML 태그 escape)
                import html
                sql_content = html.escape(query['sql_content'])
                
                row = f"""
                <tr>
                    <td>{query['file_name']}</td>
                    <td><strong>{query['query_id']}</strong></td>
                    <td>{sql_content}</td>
                    <td>{query['related_tables']}</td>
                </tr>
                """
                rows.append(row)
            
            return "".join(rows)
            
        except Exception as e:
            handle_error(e, "쿼리 테이블 HTML 생성 실패")
            return "<tr><td colspan='7' style='text-align: center; padding: 50px; color: #999;'>테이블 생성 중 오류가 발생했습니다.</td></tr>"


if __name__ == '__main__':
    import sys
    from util.arg_utils import ArgUtils
    
    # 명령행 인자 파싱
    arg_utils = ArgUtils()
    parser = arg_utils.create_parser("Query List Report 생성기")
    args = parser.parse_args()
    
    project_name = args.project_name
    print(f"Query List Report 생성 시작: {project_name}")
    
    generator = QueryListReportGenerator(project_name, './temp')
    result = generator.generate_report()
    
    if result:
        print(f"Query List Report 생성 완료: {project_name}")
    else:
        print(f"Query List Report 생성 실패: {project_name}")
