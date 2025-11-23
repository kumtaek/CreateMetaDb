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
            
            # 2. SqlContent 조회 (쿼리 원문 + 메타 테이블 매핑)
            conn = sqlite3.connect(self.sql_content_db_path)
            query_data = self._get_query_data(conn, metadata_sql_map)
            app_logger.info(f"조회된 쿼리 개수: {len(query_data)}")
            
            # 3. 데이터 분류
            categorized_data = self._categorize_queries(query_data)
            
            # 4. HTML 생성
            html_content = self._generate_html(categorized_data)
            
            # 5. 리소스 복사
            self.report_utils.copy_assets()
            
            # 6. 파일 저장
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
    
    def _categorize_queries(self, query_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """쿼리를 MyBatis, JPA, Java String으로 분류"""
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
            
            # SQL 분석
            sql_analysis = self._analyze_sql(sql_content)
            meta_tables = item.get('metadata_tables') or []
            if meta_tables:
                table_list = meta_tables
            else:
                table_list = [{'owner': 'UNKNOWN', 'table': t} for t in sql_analysis['tables']]
            
            entry = {
                'no': idx,
                'path': normalized_path,
                'path_href': '',  # 경로는 텍스트로만 표시
                'file': file_name,
                'file_href': self._build_file_href(normalized_path, file_name),
                'method': component_name.split('.')[-1] if '.' in component_name else component_name,
                'query_id': component_name,
                'sql_type': sql_analysis['sql_type'],
                'tables': ', '.join(self._format_tables(table_list)) if table_list else '-',
                'join_conditions': sql_analysis['join_conditions'],
                'join_type': sql_analysis['join_type'],
                'notes': sql_analysis['notes']
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
    
    def _analyze_sql(self, sql: str) -> Dict[str, Any]:
        """SQL 내용 분석 후 유형/테이블/조인 정보와 진단 메시지 반환"""
        import re
        
        def _strip_comments(source: str) -> str:
            """SQL 주석 제거"""
            without_block = re.sub(r'/\*.*?\*/', ' ', source, flags=re.DOTALL)
            lines = []
            for line in without_block.splitlines():
                stripped = line.strip()
                if stripped.startswith('--'):
                    continue
                lines.append(stripped)
            return ' '.join(lines).strip()
        
        cleaned_sql = _strip_comments(sql)
        sql_upper = cleaned_sql.strip().upper()
        notes = []
        
        if not cleaned_sql:
            sql_type = 'SQL_EMPTY'
            notes.append('SQL 본문이 비어있거나 주석만 존재')
        elif sql_upper.startswith('SELECT') or sql_upper.startswith('WITH'):
            sql_type = 'SQL_SELECT'
        elif sql_upper.startswith('INSERT'):
            sql_type = 'SQL_INSERT'
        elif sql_upper.startswith('UPDATE'):
            sql_type = 'SQL_UPDATE'
        elif sql_upper.startswith('DELETE'):
            sql_type = 'SQL_DELETE'
        elif sql_upper.startswith('MERGE'):
            sql_type = 'SQL_MERGE'
        elif sql.strip().startswith('--'):
            sql_type = 'SQL_REFERENCE'
            notes.append('SQL 대신 MyBatis FQMN 주석만 수집됨')
        else:
            sql_type = 'SQL_UNKNOWN'
            notes.append('선행 키워드를 인식하지 못함')
        
        join_type = self._get_join_type(cleaned_sql)
        tables = self._extract_tables(cleaned_sql)
        join_conditions = self._extract_join_conditions(sql)
        
        return {
            'sql_type': sql_type,
            'tables': tables,
            'join_conditions': join_conditions,
            'join_type': join_type,
            'notes': '; '.join(notes) if notes else '-'
        }
    
    def _get_join_type(self, sql: str) -> str:
        """조인 타입 추출"""
        sql_upper = sql.upper()
        if 'MERGE INTO' in sql_upper:
            return 'JOIN_MERGE'
        elif 'JOIN' in sql_upper:
            return 'JOIN_EXPLICIT'
        elif ',' in sql_upper and 'FROM' in sql_upper:
            return 'JOIN_IMPLICIT'
        return '-'
    
    def _extract_tables(self, sql: str) -> List[str]:
        """테이블 추출 (간단한 버전, OWNER/별칭이 있으면 테이블명만 사용)"""
        import re
        sql_upper = sql.upper()
        tables = []
        
        # FROM 절에서 테이블 추출
        if 'FROM' in sql_upper:
            from_match = re.search(r'FROM\s+([A-Z0-9_,\s]+?)(?:\s+WHERE|\s+GROUP|\s+ORDER|\s+JOIN|$)', sql_upper)
            if from_match:
                table_part = from_match.group(1)
                for table in table_part.split(','):
                    table_stripped = table.strip()
                    if table_stripped:
                        parts = table_stripped.split()
                        if parts:
                            table_name = self._normalize_table_token(parts[0])
                            if table_name and table_name not in ['SELECT', 'WHERE']:
                                tables.append(table_name)
        
        # JOIN 절에서 테이블 추출
        join_matches = re.findall(r'JOIN\s+([A-Z0-9_\.]+)', sql_upper)
        tables.extend([self._normalize_table_token(t) for t in join_matches])

        return list(set(tables))[:10]

    def _normalize_table_token(self, token: str) -> str:
        """OWNER.테이블 또는 alias.테이블 형태에서 테이블명만 추출"""
        if not token:
            return token
        if '.' in token:
            return token.split('.')[-1]
        return token

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
    
    def _extract_join_conditions(self, sql: str) -> str:
        """JOIN 조건식 추출 (ON 절 + WHERE의 테이블 조인식)"""
        import re
        
        normalized = ' '.join(sql.replace('\n', ' ').split())
        if not normalized:
            return '-'
        
        normalized_upper = normalized.upper()
        conditions = []
        boundary_keywords = [' JOIN ', ' WHERE ', ' GROUP ', ' ORDER ', ' HAVING ', ' UNION ', ' INTERSECT ', ' EXCEPT ']
        
        # ON 절 추출
        search_pos = 0
        while True:
            on_pos = normalized_upper.find(' ON ', search_pos)
            if on_pos == -1:
                break
            start = on_pos + 4
            end_candidates = [normalized_upper.find(keyword, start) for keyword in boundary_keywords if normalized_upper.find(keyword, start) != -1]
            end = min(end_candidates) if end_candidates else len(normalized_upper)
            condition = normalized[start:end].strip()
            if condition:
                conditions.append(condition)
            search_pos = end
        
        # WHERE 절에서 암묵적 조인 조건 추출
        where_pos = normalized_upper.find(' WHERE ')
        if where_pos != -1:
            where_start = where_pos + len(' WHERE ')
            where_end_candidates = [normalized_upper.find(keyword, where_start) for keyword in boundary_keywords[2:] if normalized_upper.find(keyword, where_start) != -1]
            where_end = min(where_end_candidates) if where_end_candidates else len(normalized_upper)
            where_clause = normalized[where_start:where_end]
            for cond in re.split(r'\bAND\b|\bOR\b', where_clause, flags=re.IGNORECASE):
                cond_stripped = cond.strip()
                if cond_stripped and '.' in cond_stripped and '=' in cond_stripped and not re.search(r"['\"]", cond_stripped):
                    conditions.append(cond_stripped)
        
        filtered = [c for c in conditions if self._looks_like_join_equality(c)]
        return '; '.join(dict.fromkeys(filtered)) if filtered else '-'

    def _looks_like_join_equality(self, condition: str) -> bool:
        """조인 조건으로 볼 수 있는지 단순 검사 (컬럼=컬럼 형태만 인정)"""
        import re
        if '=' not in condition:
            return False
        
        left, right = [part.strip().strip('()') for part in condition.split('=', 1)]
        
        # 숫자/상수 비교는 제외
        numeric = re.compile(r'^[-+]?\d+(\.\d+)?$')
        if numeric.match(left) or numeric.match(right):
            return False
        
        # 파라미터/바인딩 제외 (:param, #{}, ${})
        param_pattern = re.compile(r'[:#${]')
        if param_pattern.search(left) or param_pattern.search(right):
            return False
        
        col_pattern = re.compile(r'^[A-Z_][A-Z0-9_]*\.[A-Z_][A-Z0-9_]*$', re.IGNORECASE)
        return bool(col_pattern.match(left) and col_pattern.match(right))
    
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
                <td>{item['path']}</td>
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
