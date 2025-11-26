"""
Backend Mapping Report 생성기 - 독립 클래스
SqlContent.db에서 직접 데이터를 조회하여 HTML 리포트 생성

주의: 리포트는 가능하면 이미 정제·저장된 메타DB(metadata.db/SqlContent.db)를 활용하며,
추가 재파싱 없이 메타에 기록된 정보를 사용해야 한다. (메타DB 정확성 검증 이후 기본 원칙)
"""

import os
import sqlite3
import gzip
from datetime import datetime
from typing import List, Dict, Any

from util.logger import app_logger, handle_error
from util.path_utils import PathUtils
from util.report_utils import ReportUtils


class BackendMappingReportGenerator:
    """Backend Mapping Report 생성기"""
    
    def __init__(self, project_name: str, output_dir: str):
        self.project_name = project_name
        self.output_dir = output_dir
        self.path_utils = PathUtils()
        self.report_utils = ReportUtils(project_name, output_dir)
        self.sql_content_db_path = self.path_utils.join_path('projects', project_name, 'SqlContent.db')
        self.metadata_db_path = self.path_utils.join_path('projects', project_name, 'metadata.db')
    
    def generate_report(self) -> bool:
        """리포트 생성 메인 메서드"""
        conn = None
        try:
            app_logger.info(f"Backend Mapping Report 생성 시작: {self.project_name}")

            # 1. 메타 데이터 로드 (USE_TABLE 기반)
            metadata_sql_map = self._load_metadata_use_tables()

            # 2. 조인 조건 로드 (metadata.db의 relationships 테이블에서)
            metadata_join_map = self._load_metadata_join_conditions()

            # 3. SqlContent 조회 (쿼리 원문 + 메타 테이블 매핑)
            conn = sqlite3.connect(self.sql_content_db_path)
            query_data = self._get_query_data(conn, metadata_sql_map)
            app_logger.info(f"조회된 쿼리 개수: {len(query_data)}")

            # 4. 데이터 분류 (조인 조건 맵 전달)
            categorized_data = self._categorize_queries(query_data, metadata_join_map)

            # 5. HTML 생성
            html_content = self._generate_html(categorized_data)

            # 6. 리소스 복사
            self.report_utils.copy_assets()

            # 7. 파일 저장
            output_file = self.report_utils.save_report(html_content, "BackendMappingReport")

            app_logger.info(f"Backend Mapping Report 생성 완료: {output_file}")
            return True

        except Exception as e:
            handle_error(e, "Backend Mapping Report 생성 실패")
            return False
        finally:
            if conn:
                conn.close()
    
    def _get_query_data(self, conn: sqlite3.Connection, metadata_sql_map: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, Any]]:
        """SqlContent.db에서 쿼리 데이터 조회 + 메타 테이블 매핑 병합"""
        cursor = conn.cursor()
        
        query = """
        SELECT 
            file_path,
            file_name,
            component_name,
            sql_content_compressed
        FROM sql_contents 
        WHERE del_yn = 'N'
        ORDER BY file_path, component_name
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        data = []
        for row in results:
            try:
                sql_content = gzip.decompress(row[3]).decode('utf-8')
            except:
                sql_content = row[3].decode('utf-8', errors='replace') if isinstance(row[3], bytes) else str(row[3])

            comp_name = (row[2] or '').upper()
            data.append({
                'file_path': row[0] or '',
                'file_name': row[1] or '',
                'component_name': row[2] or '',
                'sql_content': sql_content,
                'metadata_tables': metadata_sql_map.get(comp_name, [])
            })
        
        return data
    
    def _categorize_queries(self, query_data: List[Dict[str, Any]], metadata_join_map: Dict[str, Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        쿼리를 MyBatis, JPA, Java String으로 분류

        Args:
            query_data: SqlContent.db에서 조회한 쿼리 데이터
            metadata_join_map: metadata.db에서 조회한 조인 조건 맵 (component_name -> join_info)
        """
        if metadata_join_map is None:
            metadata_join_map = {}

        categorized = {
            'MyBatis': [],
            'JPA': [],
            'JavaString': []
        }

        for idx, item in enumerate(query_data, 1):
            file_path = item['file_path']
            file_name = item['file_name']
            component_name = item['component_name']
            sql_content = item['sql_content']

            # 경로 정규화 (디렉터리만 표시)
            normalized_path = self._normalize_dir(file_path, file_name)

            # SQL 타입 분석 (간단한 키워드 기반)
            sql_type = self._get_sql_type(sql_content)
            notes = self._get_sql_notes(sql_content)

            # 메타DB에서 테이블 목록 조회
            meta_tables = item.get('metadata_tables') or []
            if meta_tables:
                table_list = meta_tables
            else:
                table_list = []

            # 메타DB에서 조인 정보 조회 (SQL 재파싱 없이)
            comp_key = (component_name or '').upper()
            join_info = metadata_join_map.get(comp_key, {})
            join_type = join_info.get('join_type', '-')
            join_conditions = join_info.get('join_conditions', '-')

            entry = {
                'no': idx,
                'path': normalized_path,
                'path_href': self._build_folder_href(normalized_path),
                'file': file_name,
                'file_href': self._build_file_href(normalized_path, file_name),
                'method': component_name.split('.')[-1] if '.' in component_name else component_name,
                'query_id': component_name,
                'sql_type': sql_type,
                'tables': ', '.join(self._format_tables(table_list)) if table_list else '-',
                'join_conditions': join_conditions,
                'join_type': join_type,
                'notes': notes
            }

            # 파일 경로 기반 분류
            lower_path = normalized_path.lower()
            lower_file = (file_name or '').lower()
            is_repository_ctx = 'repository' in lower_path or 'repository' in lower_file or 'repository' in component_name.lower()
            is_java_file = lower_path.endswith('.java') or lower_file.endswith('.java')
            if lower_path.endswith('.xml') or 'mybatis' in lower_path:
                categorized['MyBatis'].append(entry)
            elif is_repository_ctx and (is_java_file or lower_file.endswith('.java')):
                categorized['JPA'].append(entry)
            else:
                categorized['JavaString'].append(entry)

        return categorized
    
    def _normalize_dir(self, file_path: str, file_name: str) -> str:
        """경로 정규화 (디렉터리만)"""
        if not file_path and not file_name:
            return ''
        
        clean_path = file_path or ''
        unix_path = self.path_utils.normalize_path_separator(clean_path, 'unix')
        if file_name and (unix_path.endswith('/' + file_name) or unix_path == file_name):
            unix_path = os.path.dirname(unix_path)
        
        if 'src/' in unix_path:
            return 'src/' + unix_path.split('src/', 1)[1]
        return unix_path
    
    def _get_sql_type(self, sql: str) -> str:
        """SQL 타입 추출 (간단한 키워드 기반)"""
        import re
        # 주석 제거
        without_block = re.sub(r'/\*.*?\*/', ' ', sql, flags=re.DOTALL)
        lines = [ln.strip() for ln in without_block.splitlines() if not ln.strip().startswith('--')]
        cleaned = ' '.join(lines).strip().upper()

        if not cleaned:
            return 'SQL_EMPTY'
        if cleaned.startswith('SELECT') or cleaned.startswith('WITH'):
            return 'SQL_SELECT'
        if cleaned.startswith('INSERT'):
            return 'SQL_INSERT'
        if cleaned.startswith('UPDATE'):
            return 'SQL_UPDATE'
        if cleaned.startswith('DELETE'):
            return 'SQL_DELETE'
        if cleaned.startswith('MERGE'):
            return 'SQL_MERGE'
        if sql.strip().startswith('--'):
            return 'SQL_REFERENCE'
        return 'SQL_UNKNOWN'

    def _get_sql_notes(self, sql: str) -> str:
        """SQL 진단 메시지 생성"""
        import re
        without_block = re.sub(r'/\*.*?\*/', ' ', sql, flags=re.DOTALL)
        lines = [ln.strip() for ln in without_block.splitlines() if not ln.strip().startswith('--')]
        cleaned = ' '.join(lines).strip()

        if not cleaned:
            return 'SQL 본문이 비어있거나 주석만 존재'
        if sql.strip().startswith('--'):
            return 'SQL 대신 MyBatis FQMN 주석만 수집됨'
        sql_upper = cleaned.upper()
        if not any(sql_upper.startswith(kw) for kw in ['SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE', 'MERGE']):
            return '선행 키워드를 인식하지 못함'
        return '-'

    def _format_tables(self, tables: List[Dict[str, str]]) -> List[str]:
        """테이블 표시 시 owner가 있으면 OWNER.TABLE 형태로 표현"""
        formatted = []
        for tbl in tables:
            owner = tbl.get('owner', 'UNKNOWN')
            name = tbl.get('table', '')
            if not name:
                continue
            if owner and owner != 'UNKNOWN':
                formatted.append(f"{owner}.{name}")
            else:
                formatted.append(name)
        return formatted

    def _load_metadata_use_tables(self) -> Dict[str, List[Dict[str, str]]]:
        """metadata.db의 USE_TABLE 관계를 component_name 기준으로 맵으로 적재"""
        meta_map: Dict[str, List[Dict[str, str]]] = {}
        if not os.path.exists(self.metadata_db_path):
            return meta_map
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT src.component_name AS sql_comp,
                       dst.component_name AS table_name,
                       COALESCE(t.table_owner, 'UNKNOWN') AS table_owner
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id AND src.del_yn = 'N'
                JOIN components dst ON r.dst_id = dst.component_id AND dst.del_yn = 'N'
                LEFT JOIN tables t ON t.component_id = dst.component_id AND t.del_yn = 'N'
                JOIN projects p ON src.project_id = p.project_id
                WHERE p.project_name = ?
                  AND r.rel_type = 'USE_TABLE'
                  AND r.del_yn = 'N'
                  AND dst.component_type = 'TABLE'
                """,
                (self.project_name,)
            )
            for comp_name, table_name, table_owner in cursor.fetchall():
                key = (comp_name or '').upper()
                meta_map.setdefault(key, []).append({
                    'owner': table_owner or 'UNKNOWN',
                    'table': table_name or ''
                })
            conn.close()
        except Exception as e:
            handle_error(e, "metadata USE_TABLE 로드 실패")
        return meta_map

    def _load_metadata_join_conditions(self) -> Dict[str, Dict[str, Any]]:
        """
        metadata.db에서 SQL 컴포넌트별 조인 조건 및 조인 타입을 조회

        Returns:
            Dict[str, Dict]: component_name(대문자) -> {
                'join_type': 'EXPLICIT'|'IMPLICIT'|'MERGE'|'-',
                'join_conditions': 'A.col=B.col; ...'
            }
        """
        join_map: Dict[str, Dict[str, Any]] = {}
        if not os.path.exists(self.metadata_db_path):
            return join_map
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            # SQL 컴포넌트가 사용하는 테이블 목록 조회
            cursor.execute(
                """
                SELECT src.component_name AS sql_comp,
                       GROUP_CONCAT(dst.component_name) AS table_list
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id AND src.del_yn = 'N'
                JOIN components dst ON r.dst_id = dst.component_id AND dst.del_yn = 'N'
                JOIN projects p ON src.project_id = p.project_id
                WHERE p.project_name = ?
                  AND r.rel_type = 'USE_TABLE'
                  AND r.del_yn = 'N'
                  AND dst.component_type = 'TABLE'
                GROUP BY src.component_name
                """,
                (self.project_name,)
            )
            sql_tables_map = {row[0].upper(): row[1].split(',') if row[1] else [] for row in cursor.fetchall()}

            # 테이블 간 JOIN 관계 전체 조회
            cursor.execute(
                """
                SELECT src.component_name AS src_table,
                       dst.component_name AS dst_table,
                       r.rel_type,
                       r.join_condition
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id AND src.del_yn = 'N'
                JOIN components dst ON r.dst_id = dst.component_id AND dst.del_yn = 'N'
                JOIN projects p ON src.project_id = p.project_id
                WHERE p.project_name = ?
                  AND r.rel_type LIKE 'JOIN_%'
                  AND r.del_yn = 'N'
                  AND src.component_type = 'TABLE'
                  AND dst.component_type = 'TABLE'
                """,
                (self.project_name,)
            )
            # 테이블 쌍별 조인 정보 저장: (norm_key) -> {'rel_types': set, 'conditions': set}
            table_joins = {}
            for src_tbl, dst_tbl, rel_type, condition in cursor.fetchall():
                # 정규화된 키 (알파벳순 정렬로 양방향 통일)
                norm_key = tuple(sorted([src_tbl.upper(), dst_tbl.upper()]))
                if norm_key not in table_joins:
                    table_joins[norm_key] = {'rel_types': set(), 'conditions': set()}
                table_joins[norm_key]['rel_types'].add(rel_type)
                if condition:
                    table_joins[norm_key]['conditions'].add(condition)

            # 각 SQL 컴포넌트가 사용하는 테이블들 간의 조인 조건 수집
            for sql_comp, tables in sql_tables_map.items():
                conditions = set()
                join_types = set()
                tables_upper = [t.upper() for t in tables]

                # 테이블 쌍별로 조인 조건 확인
                for i, tbl1 in enumerate(tables_upper):
                    for tbl2 in tables_upper[i+1:]:
                        norm_key = tuple(sorted([tbl1, tbl2]))
                        if norm_key in table_joins:
                            join_info = table_joins[norm_key]
                            conditions.update(join_info['conditions'])
                            join_types.update(join_info['rel_types'])

                # 조인 타입: 여러 개면 모두 표시 (JOIN_ 접두어 제거)
                type_display = []
                for jt in sorted(join_types):
                    type_display.append(jt.replace('JOIN_', ''))
                join_type_str = ', '.join(type_display) if type_display else '-'

                # 조인 조건 중복 제거 (A=B와 B=A는 동일), 컬럼 없는 조건 필터링
                normalized_conditions = set()
                for cond in conditions:
                    if '=' in cond:
                        parts = [p.strip() for p in cond.split('=', 1)]
                        if len(parts) == 2:
                            # 컬럼이 빈 조건 필터링 (예: "TABLE. = TABLE2.")
                            left_part, right_part = parts
                            if left_part.endswith('.') or right_part.endswith('.'):
                                continue
                            norm_cond = ' = '.join(sorted(parts))
                            normalized_conditions.add(norm_cond)
                        else:
                            normalized_conditions.add(cond)
                    else:
                        normalized_conditions.add(cond)

                join_map[sql_comp] = {
                    'join_type': join_type_str,
                    'join_conditions': '; '.join(sorted(normalized_conditions)) if normalized_conditions else '-'
                }

            conn.close()
        except Exception as e:
            handle_error(e, "metadata JOIN 조건 로드 실패")
        return join_map

    def _generate_html(self, data: Dict[str, List[Dict[str, Any]]]) -> str:
        """HTML 생성"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        sections_html = ""
        
        # 1. MyBatis
        if data['MyBatis']:
            sections_html += self._generate_section_html("MyBatis SQL 매핑", data['MyBatis'])
        
        # 2. JPA
        if data['JPA']:
            sections_html += self._generate_section_html("JPA Native / 커스텀 SQL 매핑", data['JPA'])
        
        # 3. Java String
        if data['JavaString']:
            sections_html += self._generate_section_html("Java 문자열 기반 SQL 매핑", data['JavaString'])
        
        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backend Mapping Report - {self.project_name}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1800px; margin: 0 auto; background: white; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #2980b9; margin-top: 30px; border-left: 5px solid #3498db; padding-left: 10px; background: #ecf0f1; padding: 10px; }}
        .info {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.85em; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }}
        th {{ background-color: #34495e; color: white; font-weight: bold; position: sticky; top: 0; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        tr:hover {{ background-color: #e8f4f8; }}
        .sql-type {{ font-weight: bold; color: #27ae60; }}
        .join-type {{ font-style: italic; color: #8e44ad; font-weight: bold; }}
        .tables {{ color: #c0392b; font-size: 0.9em; }}
        .conditions {{ font-family: 'Courier New', monospace; color: #d35400; font-size: 0.85em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Backend Mapping Report</h1>
        <div class="info">
            <strong>프로젝트:</strong> {self.project_name}<br>
            <strong>생성일시:</strong> {timestamp}
        </div>
        
        {sections_html}
    </div>
</body>
</html>"""
    
    def _generate_section_html(self, title: str, items: List[Dict[str, Any]]) -> str:
        """섹션 HTML 생성"""
        rows_html = ""
        for item in items:
            rows_html += f"""
            <tr>
                <td>{item['no']}</td>
                <td>{self._render_path(item)}</td>
                <td>{self._render_file(item)}</td>
                <td>{item['method']}</td>
                <td>{item['query_id']}</td>
                <td class="sql-type">{item['sql_type']}</td>
                <td class="tables">{item['tables']}</td>
                <td class="conditions">{item['join_conditions']}</td>
                <td class="join-type">{item['join_type']}</td>
                <td>{item['notes']}</td>
            </tr>
            """
        
        return f"""
        <h2>{title}</h2>
        <table>
            <thead>
                <tr>
                    <th style="width: 50px;">No</th>
                    <th style="width: 250px;">Path</th>
                    <th style="width: 180px;">File</th>
                    <th style="width: 150px;">Method</th>
                    <th style="width: 200px;">Query ID</th>
                    <th style="width: 100px;">SQL_Type</th>
                    <th style="width: 200px;">Tables</th>
                    <th>Join Conditions</th>
                    <th style="width: 120px;">JOIN_Type</th>
                    <th style="width: 200px;">Notes</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        """

    def _render_file(self, item: Dict[str, Any]) -> str:
        """파일명을 하이퍼링크로 출력"""
        file_name = item.get('file', '')
        href = item.get('file_href', '')
        if href and file_name:
            return f'<a href="{href}" target="_blank" rel="noopener noreferrer">{file_name}</a>'
        return file_name

    def _render_path(self, item: Dict[str, Any]) -> str:
        """경로를 하이퍼링크로 출력 (폴더 열기)"""
        path = item.get('path', '')
        href = item.get('path_href', '')
        if href and path:
            return f'<a href="{href}" target="_blank" rel="noopener noreferrer" title="폴더 열기">{path}</a>'
        return path

    def _build_file_href(self, normalized_path: str, file_name: str) -> str:
        """리포트 기준 상대 하이퍼링크 생성 (절대경로 fallback 없음)"""
        if not normalized_path:
            return ''
        try:
            # 프로젝트 내부 경로로 보정 (projects/{project_name}/ + 상대경로)
            joined = os.path.join(normalized_path, file_name) if file_name else normalized_path
            abs_path = self.path_utils.normalize_path(
                self.path_utils.join_path("projects", self.project_name, joined)
            )
            # 리포트 출력 디렉토리 기준 상대경로로 변환
            report_dir = self.path_utils.normalize_path(self.output_dir)
            rel_path = os.path.relpath(abs_path, report_dir)
            return self.path_utils.normalize_path_separator(rel_path, 'unix')
        except Exception as e:
            handle_error(e, f"파일 링크 생성 실패: {normalized_path}/{file_name}")
            return ''

    def _build_folder_href(self, normalized_path: str) -> str:
        """폴더를 여는 file:// 프로토콜 링크 생성"""
        if not normalized_path:
            return ''
        try:
            # 프로젝트 내부 경로로 절대 경로 생성
            abs_path = self.path_utils.normalize_path(
                self.path_utils.join_path("projects", self.project_name, normalized_path)
            )
            
            # 절대 경로가 실제로 존재하는지 확인
            if not os.path.exists(abs_path):
                # 경로가 존재하지 않으면 빈 문자열 반환
                return ''
            
            # Windows 경로를 file:// 프로토콜 형식으로 변환
            # file:///D:/path/to/folder 형식
            abs_path_normalized = os.path.abspath(abs_path).replace('\\', '/')
            return f"file:///{abs_path_normalized}"
        except Exception as e:
            app_logger.warning(f"폴더 링크 생성 실패: {normalized_path} - {e}")
            return ''
