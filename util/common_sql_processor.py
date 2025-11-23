"""
공통 SQL 분석기
SqlContent.db에서 순수 SQL을 읽어서 테이블/조인 분석을 수행하는 공통화된 분석기
"""
import sqlite3
import re
import gzip
import hashlib
from typing import Dict, List, Any, Tuple, Optional, Set
from dataclasses import dataclass
from util.sql_normalization_utils import normalize_sql_loose_with_config, DEFAULT_SQL_NORMALIZATION_CONFIG
from util.logger import error, handle_error

@dataclass
class TableInfo:
    """테이블 정보"""
    table_name: str
    alias: str
    owner: str = 'UNKNOWN'
    is_inferred: bool = True

@dataclass
class JoinCondition:
    """조인 조건 정보"""
    left_table: str
    right_table: str
    left_column: str
    right_column: str
    join_type: str = 'INNER'

class CommonSqlAnalyzer:
    """공통 SQL 분석기 - SqlContent.db 기반"""
    
    def __init__(self, project_name: str):
        from util.database_utils import DatabaseUtils
        self.project_name = project_name
        self.sql_content_db_path = f"projects/{project_name}/SqlContent.db"
        self.db_utils = DatabaseUtils(f"projects/{project_name}/metadata.db")
        self.project_id = self.db_utils.get_project_id(project_name)
        
        # Oracle 키워드 로드
        self.oracle_keywords = self._load_oracle_keywords()
        # SQL 정규화 설정 (향후 필요 시 환경설정으로 확장 가능)
        self.sql_normalize_config = DEFAULT_SQL_NORMALIZATION_CONFIG.copy()
        
    def _load_oracle_keywords(self) -> Set[str]:
        """Oracle 키워드를 공통 매니저에서 로드"""
        try:
            from util.oracle_keyword_manager import get_oracle_keywords
            return get_oracle_keywords()
        except Exception as e:
            from util.logger import handle_error
            handle_error(e, "Oracle 키워드 로드 실패, 빈 집합으로 대체")
            return set()

    def _find_table_for_column(self, column_name: str, candidate_tables: List[str]) -> Optional[str]:
        """
        별칭 없는 컬럼에 대해 해당 컬럼을 가진 테이블을 DB에서 찾음
        Oracle 방식: 정확히 1개의 테이블만 해당 컬럼을 가지면 반환, 그 외(0개 또는 2개 이상) None

        Args:
            column_name: 컬럼명 (별칭 없음)
            candidate_tables: 후보 테이블 목록 (같은 쿼리에서 사용된 다른 테이블들)

        Returns:
            해당 컬럼을 가진 테이블명 (정확히 1개인 경우) 또는 None
        """
        if not column_name or not candidate_tables:
            return None

        try:
            # DB에서 해당 컬럼을 가진 테이블 목록 조회
            col_upper = column_name.upper()
            matching_tables = []

            for table_name in candidate_tables:
                query = """
                    SELECT COUNT(*) as cnt FROM columns c
                    JOIN tables t ON c.table_id = t.table_id
                    WHERE t.table_name = ? AND c.column_name = ? AND c.del_yn = 'N' AND t.del_yn = 'N'
                """
                result = self.db_utils.execute_query(query, (table_name.upper(), col_upper))
                if result and result[0].get('cnt', 0) > 0:
                    matching_tables.append(table_name)

            # 정확히 1개의 테이블만 해당 컬럼을 가지는 경우에만 반환
            if len(matching_tables) == 1:
                return matching_tables[0]

            # 0개 또는 2개 이상이면 모호하므로 None 반환
            return None

        except Exception as e:
            from util.logger import handle_error
            handle_error(e, f"컬럼 소속 테이블 조회 실패: {column_name}")
            return None

    def analyze_all_queries(self) -> Dict[str, Any]:
        """[수정] 모든 SQL을 분석하고, 컬럼의 parent_id를 정확히 설정합니다."""
        # ... (함수 시작 및 쿼리 조회 부분은 동일) ...
        
        try:
            conn = sqlite3.connect(self.sql_content_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT component_id, file_id, sql_content_compressed FROM sql_contents WHERE del_yn = 'N'")
            queries = cursor.fetchall()

            joins_saved = 0

            from util.file_context import get_file_context_manager
            ctx_mgr = get_file_context_manager()

            for component_id, file_id, compressed_sql in queries:
                try:
                    if not compressed_sql:
                        continue
                    sql_content = gzip.decompress(compressed_sql).decode('utf-8')
                    clean_sql = normalize_sql_loose_with_config(sql_content, self.sql_normalize_config)

                    # 파일 컨텍스트 설정 (분석 대상 SQL이 속한 파일 기준)
                    file_path = ''
                    file_name = ''
                    if file_id:
                        file_rows = self.db_utils.execute_query(
                            "SELECT file_path, file_name FROM files WHERE file_id = ? AND del_yn='N'",
                            (file_id,),
                            conn=self.db_utils.get_persistent_connection()
                        )
                        if file_rows:
                            file_path = file_rows[0].get('file_path', '') or ''
                            file_name = file_rows[0].get('file_name', '') or ''
                    ctx_mgr.push(
                        project_name=self.project_name,
                        project_id=self.project_id,
                        file_id=file_id,
                        file_path=file_path,
                        file_name=file_name,
                        file_type=None,
                        source_type='SQL',
                        stage='CommonSql'
                    )
                    
                    table_result = self._extract_tables(clean_sql)
                    alias_map = table_result.get('alias_map', {})

                    # USE_TABLE 관계 저장
                    if table_result.get('tables'):
                        self._save_use_table_relationships(component_id, table_result['tables'])

                    # JOIN 관계 저장
                    joins = self._extract_join_relationships(clean_sql, alias_map)
                    if joins:
                        self._save_table_joins_components(joins)
                        joins_saved += len(joins)

                    # COLUMN 컴포넌트의 PARENT_ID 설정
                    columns_to_process = self._extract_columns(clean_sql, alias_map)
                    if columns_to_process:
                        self._update_column_parent_ids(columns_to_process, alias_map)

                except Exception as e:
                    handle_error(e, f"쿼리 분석 실패: component_id={component_id}")
                    continue
                finally:
                    ctx_mgr.pop()
            conn.close()
        except Exception as e:
            handle_error(e, "analyze_all_queries 실행 실패")
            
        return {"statistics": {"joins_found": joins_saved}}

    def _save_use_table_relationships(self, sql_component_id: int, tables: List[str]) -> None:
        """metadata.db의 components(표 TABLE)와 relationships를 이용해 USE_TABLE 생성"""
        try:
            from util.database_utils import DatabaseUtils
            metadata_db_path = f"projects/{self.project_name}/metadata.db"
            db = DatabaseUtils(metadata_db_path)
            conn = db.get_persistent_connection()
            for table_name in tables:
                rows = db.execute_query(
                    "SELECT component_id FROM components WHERE component_type='TABLE' AND component_name=? AND del_yn='N' LIMIT 1",
                    (table_name,), conn=conn)
                if not rows:
                    continue
                table_component_id = rows[0]['component_id']
                rel_data = {
                    'src_id': sql_component_id,
                    'dst_id': table_component_id,
                    'rel_type': 'USE_TABLE',
                    'confidence': 1.0,
                    'has_error': 'N',
                    'error_message': None,
                    'del_yn': 'N'
                }
                db.insert_or_replace_with_id('relationships', rel_data, conn=conn)
        except Exception as e:
            from util.logger import handle_error
            handle_error(e, f"USE_TABLE 관계 저장 실패: sql_component_id={sql_component_id}")

    def _save_table_joins_components(self, joins: List[JoinCondition]) -> None:
        """[수정] TABLE(component) 간 JOIN_* 관계와 USE_COLUMN 관계를 함께 생성합니다."""
        try:
            from util.database_utils import DatabaseUtils
            metadata_db_path = f"projects/{self.project_name}/metadata.db"
            db = DatabaseUtils(metadata_db_path)
            conn = db.get_persistent_connection()
            # 프로젝트 ID 조회 (INFERRED 파일/컴포넌트 생성 시 활용)
            proj_id_rows = db.execute_query("SELECT project_id FROM projects WHERE project_name=?", (self.project_name,), conn=conn)
            project_id = proj_id_rows[0]['project_id'] if proj_id_rows else None

            def ensure_table_component(table_name: str) -> int:
                """테이블 컴포넌트를 조회하거나, 현재 파일 컨텍스트의 file_id로 생성 (inferred 파일 생성 금지)."""
                if project_id is None:
                    msg = f"[CommonSqlAnalyzer] 프로젝트 ID를 찾을 수 없습니다: {self.project_name}"
                    error(msg)
                    raise RuntimeError(msg)
                rows = db.execute_query(
                    """
                    SELECT component_id FROM components 
                    WHERE component_type='TABLE' 
                      AND component_name = ? 
                      AND project_id = ? 
                      AND del_yn='N'
                    LIMIT 1
                    """,
                    (table_name, project_id), conn=conn)
                if rows:
                    return rows[0]['component_id']

                # 기존 테이블 컴포넌트가 없으면 현재 파일 컨텍스트를 활용해 생성
                try:
                    from util.file_context import get_file_context_manager
                    ctx = get_file_context_manager().require_current_file()
                    file_id = ctx.file_id
                    if not file_id:
                        msg = f"[CommonSqlAnalyzer] 테이블 컴포넌트 누락 및 file_id 없음: {table_name}"
                        error(msg)
                        raise RuntimeError(msg)
                    comp_data = {
                        'project_id': project_id,
                        'file_id': file_id,
                        'component_name': table_name,
                        'component_type': 'TABLE',
                        'parent_id': None,
                        'layer': None,
                        'line_start': None,
                        'line_end': None,
                        'has_error': 'N',
                        'error_message': None,
                        'hash_value': hashlib.md5(f"{table_name}".encode()).hexdigest(),
                        'del_yn': 'N'
                    }
                    comp_id = db.insert_or_replace_with_id('components', comp_data, conn=conn)
                    return comp_id
                except Exception as e:
                    msg = f"[CommonSqlAnalyzer] 테이블 컴포넌트 생성 실패: {table_name} (project_id={project_id})"
                    error(msg)
                    raise RuntimeError(msg) from e

            for join in joins:
                src_comp_id = ensure_table_component(join.left_table)
                dst_comp_id = ensure_table_component(join.right_table)
                if not src_comp_id or not dst_comp_id:
                    continue

                # 조인 조건 그대로 보존 (스키마에 없어도 INFERRED로 유지 - 쿼리에 나온 대로 메타 생성)
                stored_src_col = join.left_column.upper()
                stored_dst_col = join.right_column.upper()
                join_cond = f"{join.left_table}.{stored_src_col} = {join.right_table}.{stored_dst_col}"

                # JOIN 관계 저장
                rel = {
                    'src_id': src_comp_id,
                    'dst_id': dst_comp_id,
                    'rel_type': f"JOIN_{join.join_type}",
                    'confidence': 0.8,
                    'del_yn': 'N',
                    'src_column': stored_src_col,
                    'dst_column': stored_dst_col,
                    'join_condition': join_cond
                }
                db.insert_or_replace_with_id('relationships', rel, conn=conn)

                src_col_row = db.execute_query("SELECT component_id FROM components WHERE component_type='COLUMN' AND parent_id=? AND component_name=?", (src_comp_id, join.left_column), conn=conn)
                dst_col_row = db.execute_query("SELECT component_id FROM components WHERE component_type='COLUMN' AND parent_id=? AND component_name=?", (dst_comp_id, join.right_column), conn=conn)
                src_col_comp_id = src_col_row[0]['component_id'] if src_col_row else None
                dst_col_comp_id = dst_col_row[0]['component_id'] if dst_col_row else None

                if src_comp_id and src_col_comp_id:
                    db.insert_relationship(src_comp_id, src_col_comp_id, 'USE_COLUMN')
                if dst_comp_id and dst_col_comp_id:
                    db.insert_relationship(dst_comp_id, dst_col_comp_id, 'USE_COLUMN')

        except Exception as e:
            from util.logger import handle_error
            handle_error(e, "JOIN 및 USE_COLUMN 관계 저장 실패 (inferred 파일 생성 금지 모드)")
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

    def _extract_columns(self, sql: str, alias_map: Dict[str, str]) -> List[Tuple[str, str]]:
        """[임시 수정] WHERE/ON 절의 '조인 조건'에 사용된 컬럼만 추출합니다."""
        try:
            cols = set()
            where_on_segment = ""
            
            where_on_match = re.search(r"\b(WHERE|ON)\b(.*)", sql, flags=re.IGNORECASE | re.DOTALL)
            if where_on_match:
                where_on_segment = where_on_match.group(2)
            else: # WHERE나 ON이 없으면 조인 컬럼도 없음
                return []

            # 조인 조건 패턴: a.col = b.col 또는 a.col = col
            condition_pattern = r'\b([\w\.]+)\b\s*=\s*\b([\w\.]+)\b'
            conditions = re.findall(condition_pattern, where_on_segment)
            for part1, part2 in conditions:
                # 양쪽 중 하나라도 '.'을 포함해야 조인 조건으로 간주
                if '.' in part1 or '.' in part2:
                    cols.add(part1)
                    cols.add(part2)

            resolved = []
            for col_part in cols:
                if '.' in col_part:
                    alias, col_name = col_part.split('.', 1)
                    table_name = alias_map.get(alias.upper(), alias.upper())
                    resolved.append((table_name, col_name.upper()))
                else:
                    resolved.append(('UNKNOWN', col_part.upper()))
            
            return resolved
        except Exception as e:
            from util.logger import handle_error
            handle_error(e, "Column extraction failed")
            return []



    def _find_owner_table_of_column(self, column_name: str, candidate_tables: list[str]) -> Optional[str]:
        """[신규] 후보 테이블 목록 중에서, 특정 컬럼을 실제로 소유한 테이블을 DB에서 찾습니다."""
        if not column_name or not candidate_tables:
            return None
        try:
            conn = self.db_utils.get_persistent_connection()
            cur = conn.cursor()
            for table_name in candidate_tables:
                table_comp_id = self.db_utils.get_component_id(self.project_id, table_name, 'TABLE')
                if not table_comp_id:
                    continue

                cur.execute("SELECT 1 FROM components WHERE project_id=? AND component_type='COLUMN' AND parent_id=? AND component_name=?",
                            (self.project_id, table_comp_id, column_name))
                if cur.fetchone():
                    return table_name
            return None
        except Exception as e:
            from util.logger import handle_error
            handle_error(e, f"컬럼 소유자 테이블 검색 실패 '{column_name}': {e}")
            return None

    def _update_column_parent_ids(self, columns: List[Tuple[str, str]], alias_map: Dict[str, str]) -> None:
        """별칭 없는 컬럼의 부모 테이블 ID를 찾아 업데이트합니다."""
        try:
            if not columns:
                return
            conn = self.db_utils.get_persistent_connection()
            for table_name, col_name in columns:
                # 키워드/리터럴 컬럼은 무시하여 잘못된 inferred 컬럼 생성을 방지
                if not self._should_register_column(col_name):
                    continue

                if table_name == 'UNKNOWN':
                    candidate_tables = list(alias_map.values())
                    owner_table = self._find_owner_table_of_column(col_name, candidate_tables)
                    if owner_table:
                        table_name = owner_table
                    elif candidate_tables:
                        table_name = candidate_tables[0]
                        self.db_utils.register_inferred_column(self.project_id, table_name, col_name)
                    else:
                        continue

                table_comp_id = self.db_utils.get_component_id(self.project_id, table_name, 'TABLE')
                if not table_comp_id:
                    continue

                col_comp = self.db_utils.execute_query("SELECT component_id FROM components WHERE component_type='COLUMN' AND component_name=? AND parent_id=?", (col_name, table_comp_id), conn=conn)
                if col_comp:
                    # 이미 올바른 parent_id를 가지고 있으므로 업데이트 불필요
                    continue
                else:
                    # parent_id가 잘못되었거나 없는 경우, 올바른 parent_id로 업데이트
                    self.db_utils.update_record('components', {'parent_id': table_comp_id}, {'component_name': col_name, 'component_type': 'COLUMN', 'project_id': self.project_id}, conn=conn)

        except Exception as e:
            from util.logger import handle_error
            handle_error(e, "컬럼 parent_id 업데이트 실패")
    
    def _remove_comments(self, sql: str) -> str:
        """SQL 주석 제거"""
        return normalize_sql_loose_with_config(sql, self.sql_normalize_config)
    
    def _extract_tables(self, sql: str) -> Dict[str, Any]:
        """SQL에서 테이블 추출 (2단계) - 테이블명과 알리아스 매핑"""
        tables = set()
        alias_map = {}
        
        # 2단계: 테이블 추출 정규식 패턴들
        patterns = [
            r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\s+[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\s+[a-zA-Z_][a-zA-Z0-9_]*)?)\s+SET',
            r'DELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\s+[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'INSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\s+[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'MERGE\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\s+[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\s+[a-zA-Z_][a-zA-Z0-9_]*)?)\s+ON',
            r'USING\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\s+[a-zA-Z_][a-zA-Z0-9_]*)?)\s+ON'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            for match in matches:
                # 테이블명과 별칭 분리
                parts = match.strip().split()
                table_name = parts[0].upper()
                
                # Oracle 키워드 체크
                if table_name not in self.oracle_keywords:
                    tables.add(table_name)
                    
                    # 알리아스가 있으면 매핑 생성
                    if len(parts) > 1:
                        alias = parts[1].upper()
                        alias_map[alias] = table_name
        
        return {
            'tables': list(tables),
            'alias_map': alias_map
        }
    
    def _extract_join_relationships(self, sql: str, alias_map: Dict[str, str]) -> List[JoinCondition]:
        """SQL에서 조인 관계 추출 (3단계) - 3가지 패턴 분석"""
        joins = []
        
        # ① WHERE ... <조인조건> --> JOIN_IMPLICIT
        implicit_joins = self._extract_implicit_joins(sql, alias_map)
        joins.extend(implicit_joins)
        
        # ② JOIN ... ON <조인조건> --> JOIN_EXPLICIT  
        explicit_joins = self._extract_explicit_joins(sql, alias_map)
        joins.extend(explicit_joins)
        
        # ③ MERGE ... USING ... ON (<조인조건>) --> JOIN_MERGE
        merge_joins = self._extract_merge_joins(sql, alias_map)
        joins.extend(merge_joins)
        
        return joins
    
    def _extract_implicit_joins(self, sql: str, alias_map: Dict[str, str]) -> List[JoinCondition]:
        """[수정] WHERE 절에서 별칭이 없거나 (+)가 포함된 조인 조건을 분석합니다."""
        joins = []
        where_match = re.search(r'\bWHERE\s+(.*?)(?=\bGROUP|\bORDER|\bHAVING|;|$)', sql, re.IGNORECASE | re.DOTALL)
        if not where_match:
            return joins

        where_clause = where_match.group(1)
        where_clause = re.sub(r'\(\+\)', '', where_clause)

        condition_pattern = r'([\w\.]+)\s*=\s*([\w\.]+)'
        conditions = re.findall(condition_pattern, where_clause)

        for part1, part2 in conditions:
            part1_has_dot = '.' in part1
            part2_has_dot = '.' in part2

            table1, col1, table2, col2 = None, None, None, None

            if part1_has_dot:
                alias1, col1 = part1.split('.', 1)
                table1 = alias_map.get(alias1.upper())
            else:
                col1 = part1

            if part2_has_dot:
                alias2, col2 = part2.split('.', 1)
                table2 = alias_map.get(alias2.upper())
            else:
                col2 = part2

            if not col1 or not col2:
                continue

            # 리터럴 값 체크 (숫자, 문자열, SYSDATE 등은 조인 조건에서 제외)
            from util.oracle_keyword_manager import is_literal_value
            if is_literal_value(col1) or is_literal_value(col2):
                continue

            # 테이블 추론 (별칭 없는 컬럼 처리)
            # Oracle 방식: 해당 컬럼을 가진 테이블이 정확히 1개일 때만 매핑
            if table1 and not table2:
                candidate_tables = [tbl for tbl in alias_map.values() if tbl != table1]
                # DB에서 col2를 가진 테이블 찾기
                table2 = self._find_table_for_column(col2, candidate_tables)
            elif not table1 and table2:
                candidate_tables = [tbl for tbl in alias_map.values() if tbl != table2]
                # DB에서 col1을 가진 테이블 찾기
                table1 = self._find_table_for_column(col1, candidate_tables)

            if table1 and table2 and table1 != table2:
                if (table1.upper() not in self.oracle_keywords and
                    table2.upper() not in self.oracle_keywords and
                    col1.upper() not in self.oracle_keywords and
                    col2.upper() not in self.oracle_keywords):
                    joins.append(JoinCondition(
                        left_table=table1,
                        right_table=table2,
                        left_column=col1.upper(),
                        right_column=col2.upper(),
                        join_type='IMPLICIT'
                    ))
        return joins
    
    def _extract_explicit_joins(self, sql: str, alias_map: Dict[str, str]) -> List[JoinCondition]:
        """JOIN ... ON 절에서 명시적 조인 관계 추출"""
        joins = []
        
        # JOIN 절에서 = 조건 직접 찾기 (알리아스 있음/없음 모두)
        join_join_pattern = r'JOIN\s+\w+(?:\s+\w+)?\s+ON\s+.*?(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)'
        matches = re.findall(join_join_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            left_alias, left_col, right_alias, right_col = match
            
            # 알리아스 매핑 (있으면 매핑, 없으면 그대로)
            left_table = alias_map.get(left_alias.upper(), left_alias.upper())
            right_table = alias_map.get(right_alias.upper(), right_alias.upper())
            
            # Oracle 키워드만 제외 (INFERRED 테이블/컬럼 도출 목표)
            if (left_table.upper() not in self.oracle_keywords and 
                right_table.upper() not in self.oracle_keywords and
                left_col.upper() not in self.oracle_keywords and 
                right_col.upper() not in self.oracle_keywords):
                
                joins.append(JoinCondition(
                    left_table=left_table,
                    right_table=right_table,
                    left_column=left_col.upper(),
                    right_column=right_col.upper(),
                    join_type='EXPLICIT'
                ))
        
        return joins
    
    def _extract_merge_joins(self, sql: str, alias_map: Dict[str, str]) -> List[JoinCondition]:
        """MERGE ... USING ... ON 절에서 조인 관계 추출"""
        joins = []
        
        # MERGE 절에서 = 조건 직접 찾기 (알리아스 있음/없음 모두)
        merge_join_pattern = r'MERGE\s+INTO\s+\w+(?:\s+\w+)?\s+USING\s+\w+(?:\s+\w+)?\s+ON\s+.*?(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)'
        matches = re.findall(merge_join_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            left_alias, left_col, right_alias, right_col = match
            
            # 알리아스 매핑 (있으면 매핑, 없으면 그대로)
            left_table = alias_map.get(left_alias.upper(), left_alias.upper())
            right_table = alias_map.get(right_alias.upper(), right_alias.upper())
            
            # Oracle 키워드만 제외 (INFERRED 테이블/컬럼 도출 목표)
            if (left_table.upper() not in self.oracle_keywords and 
                right_table.upper() not in self.oracle_keywords and
                left_col.upper() not in self.oracle_keywords and 
                right_col.upper() not in self.oracle_keywords):
                
                joins.append(JoinCondition(
                    left_table=left_table,
                    right_table=right_table,
                    left_column=left_col.upper(),
                    right_column=right_col.upper(),
                    join_type='MERGE'
                ))
        
        return joins

    # Override with enhanced MERGE USING subselect handling (placed later in class to take precedence)
    def _extract_merge_joins(self, sql: str, alias_map: Dict[str, str]) -> List[JoinCondition]:
        """
        Extract JOINs from MERGE statements.
        Heuristics:
        - USING (subselect ...): create JOIN_MERGE between MERGE target and all tables in subselect FROM/JOIN.
        - Keep ON equality alias-based joins as well.
        """
        joins: List[JoinCondition] = []

        def _upper(s: str) -> str:
            return s.upper() if isinstance(s, str) else s

        try:
            # MERGE target table
            m_target = re.search(r"MERGE\s+INTO\s+([A-Za-z_][A-Za-z0-9_$.]*)", sql, flags=re.IGNORECASE)
            target_table = _upper(m_target.group(1)) if m_target else None

            # Find USING ... ON with simple parentheses-aware scan
            using_match = re.search(r"\bUSING\b", sql, flags=re.IGNORECASE)
            on_pos = None
            if using_match:
                i = using_match.end()
                level = 0
                while i < len(sql):
                    ch = sql[i]
                    if ch == '(':
                        level += 1
                    elif ch == ')':
                        level = max(0, level - 1)
                    if level == 0 and re.match(r"\s*ON\b", sql[i:], flags=re.IGNORECASE):
                        on_pos = i + re.match(r"\s*ON\b", sql[i:], flags=re.IGNORECASE).start()
                        break
                    i += 1

            using_segment = None
            if using_match and on_pos:
                using_segment = sql[using_match.end():on_pos].strip()

            if target_table and using_segment:
                tables_in_using: List[str] = []
                seg = using_segment.strip()
                if seg.startswith('('):
                    # inner subselect
                    level = 0
                    start = 0
                    end = len(seg)
                    for idx, ch in enumerate(seg):
                        if ch == '(':
                            if level == 0:
                                start = idx + 1
                            level += 1
                        elif ch == ')':
                            level -= 1
                            if level == 0:
                                end = idx
                                break
                    inner = seg[start:end]
                    for pat in (
                        r"\bFROM\s+([A-Za-z_][A-Za-z0-9_$.]*)",
                        r"\bJOIN\s+([A-Za-z_][A-Za-z0-9_$.]*)",
                    ):
                        for t in re.findall(pat, inner, flags=re.IGNORECASE):
                            t_up = _upper(t)
                            if t_up and t_up not in self.oracle_keywords:
                                tables_in_using.append(t_up)
                else:
                    m_tbl = re.match(r"([A-Za-z_][A-Za-z0-9_$.]*)", seg, flags=re.IGNORECASE)
                    if m_tbl:
                        t_up = _upper(m_tbl.group(1))
                        if t_up and t_up not in self.oracle_keywords:
                            tables_in_using.append(t_up)

                for t in dict.fromkeys(tables_in_using):
                    if t != target_table and target_table not in self.oracle_keywords:
                        joins.append(JoinCondition(
                            left_table=target_table,
                            right_table=t,
                            left_column='',
                            right_column='',
                            join_type='MERGE'
                        ))

            # Alias-based equality in ON clause
            merge_join_pattern = (
                r'MERGE\s+INTO\s+\w+(?:\s+\w+)?\s+USING\s+\w+(?:\s+\w+)?\s+ON\s+.*?'
                r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)'
            )
            for left_alias, left_col, right_alias, right_col in re.findall(merge_join_pattern, sql, re.IGNORECASE | re.DOTALL):
                lt = alias_map.get(_upper(left_alias), _upper(left_alias))
                rt = alias_map.get(_upper(right_alias), _upper(right_alias))
                if (lt not in self.oracle_keywords and rt not in self.oracle_keywords
                        and _upper(left_col) not in self.oracle_keywords and _upper(right_col) not in self.oracle_keywords):
                    joins.append(JoinCondition(
                        left_table=lt,
                        right_table=rt,
                        left_column=_upper(left_col),
                        right_column=_upper(right_col),
                        join_type='MERGE'
                    ))

            return joins
        except Exception:
            return []

    def save_analysis_results(self, results: Dict[str, Any]) -> bool:
        """분석 결과를 데이터베이스에 저장"""
        try:
            # metadata.db 연결
            metadata_db_path = f"projects/{self.project_name}/metadata.db"
            conn = sqlite3.connect(metadata_db_path)
            cursor = conn.cursor()
            
            # 테이블 저장
            for table_name in results['tables']:
                self._save_table(cursor, table_name)
            
            # 조인 관계 저장
            for join in results['join_relationships']:
                self._save_join_relationship(cursor, join)
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            from util.logger import handle_error
            handle_error(e, "분석 결과 저장 실패")
            return False

    def _should_register_column(self, column_name: str) -> bool:
        """
        컬럼 등록 여부 판단
        - Oracle 키워드는 제외
        - 리터럴 값(숫자, 문자열, SYSDATE, NULL, TRUE/FALSE 등)은 제외
        - sql_keyword.yaml의 literal_keywords, literal_value_patterns 참조
        """
        try:
            if not column_name:
                return False

            # 리터럴 값 체크 (YAML 설정 기반)
            from util.oracle_keyword_manager import is_literal_value
            if is_literal_value(column_name):
                return False

            name_upper = column_name.upper()

            # Oracle 키워드 체크
            if name_upper in self.oracle_keywords:
                return False

            return True
        except Exception:
            return False
    
    def _save_table(self, cursor, table_name: str):
        """테이블 정보 저장"""
        try:
            # 테이블 존재 여부 확인
            cursor.execute("""
                SELECT table_id FROM tables 
                WHERE table_name = ? AND project_id = (SELECT project_id FROM projects WHERE project_name = ?)
            """, (table_name, self.project_name))
            
            if not cursor.fetchone():
                # INFERRED 테이블 생성
                hash_value = hashlib.md5(f"{self.project_name}_{table_name}".encode()).hexdigest()
                cursor.execute("""
                    INSERT INTO tables (project_id, table_name, table_owner, hash_value, del_yn)
                    VALUES ((SELECT project_id FROM projects WHERE project_name = ?), ?, 'UNKNOWN', ?, 'N')
                """, (self.project_name, table_name, hash_value))
                
        except Exception as e:
            from util.logger import handle_error
            handle_error(e, f"테이블 저장 실패: {table_name}")
    
    def _save_table_with_db_utils(self, db_utils, table_name: str):
        """DatabaseUtils를 사용한 테이블 정보 저장"""
        try:
            # 테이블 존재 여부 확인
            check_query = """
                SELECT table_id FROM tables 
                WHERE table_name = ? AND project_id = (SELECT project_id FROM projects WHERE project_name = ?)
            """
            existing = db_utils.execute_query(check_query, (table_name, self.project_name))
            
            if not existing:
                # INFERRED 테이블 생성
                hash_value = hashlib.md5(f"{self.project_name}_{table_name}".encode()).hexdigest()
                insert_data = {
                    'project_id': f"(SELECT project_id FROM projects WHERE project_name = '{self.project_name}')",
                    'table_name': table_name,
                    'table_owner': 'UNKNOWN',
                    'hash_value': hash_value,
                    'del_yn': 'N'
                }
                db_utils.insert_record('tables', insert_data)
                
        except Exception as e:
            from util.logger import handle_error
            handle_error(e, f"테이블 저장 실패: {table_name}")
    
    def _save_tables_batch_to_metadata(self, tables: List[str]) -> None:
        """테이블들을 metadata.db에 배치 저장"""
        try:
            # 기존 연결을 사용하여 처리 (별도 연결 생성하지 않음)
            from util.database_utils import DatabaseUtils
            metadata_db_path = f"projects/{self.project_name}/metadata.db"
            
            # 기존 연결이 있는지 확인하고 사용
            with DatabaseUtils(metadata_db_path).get_connection() as conn:
                cursor = conn.cursor()
                for table_name in tables:
                    self._save_table(cursor, table_name)
                conn.commit()
            
        except Exception as e:
            from util.logger import handle_error
            handle_error(e, f"테이블 배치 저장 실패: {len(tables)}개 테이블")
    
    def _save_joins_batch_to_metadata(self, joins: List[JoinCondition]) -> None:
        """조인 관계들을 metadata.db에 배치 저장"""
        try:
            # 기존 연결을 사용하여 처리 (별도 연결 생성하지 않음)
            from util.database_utils import DatabaseUtils
            metadata_db_path = f"projects/{self.project_name}/metadata.db"
            
            # 기존 연결이 있는지 확인하고 사용
            with DatabaseUtils(metadata_db_path).get_connection() as conn:
                cursor = conn.cursor()
                for join in joins:
                    self._save_join_relationship(cursor, join)
                conn.commit()
            
        except Exception as e:
            from util.logger import handle_error
            handle_error(e, f"조인 관계 배치 저장 실패: {len(joins)}개 관계")
    
    def _save_join_relationship(self, cursor, join: JoinCondition):
        """조인 관계 저장"""
        try:
            # 소스와 대상 테이블 ID 찾기
            cursor.execute("""
                SELECT t.table_id FROM tables t
                JOIN projects p ON t.project_id = p.project_id
                WHERE t.table_name = ? AND p.project_name = ?
            """, (join.left_table, self.project_name))
            left_table_id = cursor.fetchone()
            
            cursor.execute("""
                SELECT t.table_id FROM tables t
                JOIN projects p ON t.project_id = p.project_id
                WHERE t.table_name = ? AND p.project_name = ?
            """, (join.right_table, self.project_name))
            right_table_id = cursor.fetchone()
            
            if left_table_id and right_table_id:
                # 스키마에 없어도 조인 조건을 그대로 보존(INFERRED)
                stored_src_col = join.left_column.upper()
                stored_dst_col = join.right_column.upper()
                join_cond = f"{join.left_table}.{stored_src_col} = {join.right_table}.{stored_dst_col}"
                # 중복 체크
                cursor.execute("""
                    SELECT COUNT(*) FROM relationships 
                    WHERE src_id = ? AND dst_id = ? AND rel_type = ?
                """, (left_table_id[0], right_table_id[0], f"JOIN_{join.join_type}"))
                
                if cursor.fetchone()[0] == 0:
                    # 조인 관계 저장
                    cursor.execute("""
                        INSERT INTO relationships (src_id, dst_id, rel_type, confidence, del_yn, src_column, dst_column, join_condition)
                        VALUES (?, ?, ?, ?, 'N', ?, ?, ?)
                    """, (left_table_id[0], right_table_id[0], f"JOIN_{join.join_type}", 0.8, stored_src_col, stored_dst_col, join_cond))
                
        except Exception as e:
            from util.logger import handle_error
            handle_error(e, f"조인 관계 저장 실패: {join.left_table} -> {join.right_table}")
    
    def _save_join_relationship_with_db_utils(self, db_utils, join: JoinCondition):
        """DatabaseUtils를 사용한 조인 관계 저장"""
        try:
            # 소스와 대상 테이블 ID 찾기
            left_query = """
                SELECT t.table_id FROM tables t
                JOIN projects p ON t.project_id = p.project_id
                WHERE t.table_name = ? AND p.project_name = ?
            """
            left_result = db_utils.execute_query(left_query, (join.left_table, self.project_name))
            
            right_query = """
                SELECT t.table_id FROM tables t
                JOIN projects p ON t.project_id = p.project_id
                WHERE t.table_name = ? AND p.project_name = ?
            """
            right_result = db_utils.execute_query(right_query, (join.right_table, self.project_name))
            
            if left_result and right_result:
                # 중복 체크
                check_query = """
                    SELECT COUNT(*) FROM relationships 
                    WHERE src_id = ? AND dst_id = ? AND rel_type = ?
                """
                count_result = db_utils.execute_query(check_query, (left_result[0]['table_id'], right_result[0]['table_id'], f"JOIN_{join.join_type}"))
                
                if count_result[0]['COUNT(*)'] == 0:
                    # 조인 관계 저장
                    # 스키마에 없어도 조인 조건을 그대로 보존(INFERRED)
                    stored_src_col = join.left_column.upper()
                    stored_dst_col = join.right_column.upper()
                    join_cond = f"{join.left_table}.{stored_src_col} = {join.right_table}.{stored_dst_col}"

                    relationship_data = {
                        'src_id': left_result[0]['table_id'],
                        'dst_id': right_result[0]['table_id'],
                        'rel_type': f"JOIN_{join.join_type}",
                        'confidence': 0.8,
                        'del_yn': 'N',
                        'src_column': stored_src_col,
                        'dst_column': stored_dst_col,
                        'join_condition': join_cond
                    }
                    db_utils.insert_record('relationships', relationship_data)
                
        except Exception as e:
            from util.logger import handle_error
            handle_error(e, f"조인 관계 저장 실패: {join.left_table} -> {join.right_table}")
