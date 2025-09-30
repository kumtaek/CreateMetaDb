"""
공통 SQL 분석기
SqlContent.db에서 순수 SQL을 읽어서 테이블/조인 분석을 수행하는 공통화된 분석기
"""
import sqlite3
import re
import gzip
import hashlib
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

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
        self.project_name = project_name
        self.sql_content_db_path = f"projects/{project_name}/SqlContent.db"
        
        # Oracle 키워드 로드
        self.oracle_keywords = self._load_oracle_keywords()
        
    def _load_oracle_keywords(self) -> set:
        """Oracle 키워드 로드"""
        try:
            with open('config/parser/oracle_keywords.txt', 'r', encoding='utf-8') as f:
                return set(line.strip().upper() for line in f if line.strip())
        except:
            return set()
    
    def analyze_all_queries(self) -> Dict[str, Any]:
        """SqlContent.db의 모든 쿼리 분석"""
        results = {
            'tables': [],
            'join_relationships': [],
            'statistics': {
                'total_queries': 0,
                'tables_found': 0,
                'joins_found': 0
            }
        }
        
        try:
            conn = sqlite3.connect(self.sql_content_db_path)
            cursor = conn.cursor()
            
            # SqlContent.db에서 모든 쿼리 가져오기
            cursor.execute("""
                SELECT component_name, sql_content_compressed, file_path
                FROM sql_contents 
                WHERE del_yn = 'N'
            """)
            
            queries = cursor.fetchall()
            results['statistics']['total_queries'] = len(queries)
            
            all_tables = set()
            all_joins = []
            
            for component_name, compressed_sql, file_path in queries:
                try:
                    # 압축된 SQL 해제
                    if compressed_sql:
                        sql_content = gzip.decompress(compressed_sql).decode('utf-8')
                    else:
                        continue
                    
                    # 주석 제거
                    clean_sql = self._remove_comments(sql_content)
                    
                    # 테이블 추출 (2단계)
                    table_result = self._extract_tables(clean_sql)
                    all_tables.update(table_result['tables'])
                    
                    # 조인 관계 추출 (3단계) - alias_map 전달
                    joins = self._extract_join_relationships(clean_sql, table_result['alias_map'])
                    all_joins.extend(joins)
                    
                except Exception as e:
                    from util.logger import handle_error
                    handle_error(e, f"쿼리 분석 실패: {component_name}")
                    continue
            
            # 결과 정리
            results['tables'] = list(all_tables)
            results['join_relationships'] = all_joins
            results['statistics']['tables_found'] = len(all_tables)
            results['statistics']['joins_found'] = len(all_joins)
            
            # 데이터베이스에 저장
            if all_tables:
                self._save_tables_batch_to_metadata(list(all_tables))
                    
            if all_joins:
                self._save_joins_batch_to_metadata(all_joins)
            
            conn.close()
            
        except Exception as e:
            from util.logger import handle_error
            handle_error(e, "analyze_all_queries 실행 실패")
            
        return results
    
    def _remove_comments(self, sql: str) -> str:
        """SQL 주석 제거"""
        # -- 주석 제거
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        # /* */ 주석 제거
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        return sql.strip()
    
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
        
        # ③ MERGE ... USING ... ON (<조인조건>) --> JOIN_MERGEON
        merge_joins = self._extract_merge_joins(sql, alias_map)
        joins.extend(merge_joins)
        
        return joins
    
    def _extract_implicit_joins(self, sql: str, alias_map: Dict[str, str]) -> List[JoinCondition]:
        """WHERE 절에서 암시적 조인 관계 추출"""
        joins = []
        
        # WHERE 절에서 = 조건 직접 찾기 (알리아스 있음/없음 모두)
        where_join_pattern = r'WHERE\s+.*?(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)'
        matches = re.findall(where_join_pattern, sql, re.IGNORECASE | re.DOTALL)
        
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
                    join_type='MERGEON'
                ))
        
        return joins
    
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
                # 중복 체크
                cursor.execute("""
                    SELECT COUNT(*) FROM relationships 
                    WHERE src_id = ? AND dst_id = ? AND rel_type = ?
                """, (left_table_id[0], right_table_id[0], f"JOIN_{join.join_type}"))
                
                if cursor.fetchone()[0] == 0:
                    # 조인 관계 저장
                    cursor.execute("""
                        INSERT INTO relationships (src_id, dst_id, rel_type, confidence, del_yn)
                        VALUES (?, ?, ?, ?, 'N')
                    """, (left_table_id[0], right_table_id[0], f"JOIN_{join.join_type}", 0.8))
                
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
                    relationship_data = {
                        'src_id': left_result[0]['table_id'],
                        'dst_id': right_result[0]['table_id'],
                        'rel_type': f"JOIN_{join.join_type}",
                        'confidence': 0.8,
                        'del_yn': 'N'
                    }
                    db_utils.insert_record('relationships', relationship_data)
                
        except Exception as e:
            from util.logger import handle_error
            handle_error(e, f"조인 관계 저장 실패: {join.left_table} -> {join.right_table}")
