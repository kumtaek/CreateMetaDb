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

from .sql_join_analyzer import SqlJoinAnalyzer
from .sql_parser import SqlParser

class CommonSqlAnalyzer:
    """공통 SQL 분석기 - SqlContent.db 기반"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.sql_content_db_path = f"projects/{project_name}/SqlContent.db"
        self.sql_parser = SqlParser()
        self.sql_join_analyzer = SqlJoinAnalyzer()
    
    def analyze_all_queries(self) -> List[Dict[str, Any]]:
        """SqlContent.db의 모든 쿼리를 분석하여 '조인 후보' 딕셔너리 리스트를 반환합니다."""
        all_join_candidates = []
        try:
            conn = sqlite3.connect(self.sql_content_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT sql_content_compressed FROM sql_contents WHERE del_yn = 'N'")
            queries = cursor.fetchall()
            
            for compressed_sql_row in queries:
                try:
                    if not compressed_sql_row[0]:
                        continue
                    sql_content = gzip.decompress(compressed_sql_row[0]).decode('utf-8')
                    clean_sql = self.sql_parser._preprocess_sql(sql_content)
                    
                    alias_map = self.sql_parser.extract_tables_and_aliases(clean_sql)
                    if not alias_map:
                        continue

                    join_candidates = self.sql_join_analyzer.analyze_join_relationships(clean_sql, alias_map)
                    if join_candidates:
                        all_join_candidates.extend(join_candidates)
                        
                except Exception as e:
                    print(f"Error analyzing a single query: {e}")
                    continue
            
            conn.close()
            
        except Exception as e:
            print(f"Error in analyze_all_queries: {e}")
            
        return all_join_candidates
    
    def _remove_comments(self, sql: str) -> str:
        """SQL 주석 제거"""
        # -- 주석 제거
        sql = re.sub(r'--[^\r\n]*', '', sql)
        sql = re.sub(r'//[^\r\n]*', '', sql)
        # /* */ 주석 제거
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        return sql.strip()
    
    def _extract_tables(self, sql: str) -> List[str]:
        """SQL에서 테이블 추출 (2단계)"""
        tables = set()
        
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
        
        return list(tables)
    
    def _extract_join_relationships(self, sql: str, tables: List[str]) -> List[JoinCondition]:
        """SQL에서 조인 관계 추출 (3단계)"""
        joins = []
        
        # JOIN 패턴들
        join_patterns = [
            r'(\w+)\s+JOIN\s+(\w+)\s+ON\s+([^=]+)=([^=\s]+)',
            r'(\w+)\s+LEFT\s+JOIN\s+(\w+)\s+ON\s+([^=]+)=([^=\s]+)',
            r'(\w+)\s+RIGHT\s+JOIN\s+(\w+)\s+ON\s+([^=]+)=([^=\s]+)',
            r'(\w+)\s+INNER\s+JOIN\s+(\w+)\s+ON\s+([^=]+)=([^=\s]+)',
            r'(\w+)\s+OUTER\s+JOIN\s+(\w+)\s+ON\s+([^=]+)=([^=\s]+)'
        ]
        
        for pattern in join_patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            for match in matches:
                left_table = match[0].upper()
                right_table = match[1].upper()
                left_column = match[2].strip()
                right_column = match[3].strip()
                
                # 테이블이 추출된 테이블 목록에 있는지 확인
                if left_table in [t.upper() for t in tables] and right_table in [t.upper() for t in tables]:
                    join_type = 'INNER'
                    if 'LEFT' in pattern.upper():
                        join_type = 'LEFT'
                    elif 'RIGHT' in pattern.upper():
                        join_type = 'RIGHT'
                    elif 'OUTER' in pattern.upper():
                        join_type = 'OUTER'
                    
                    joins.append(JoinCondition(
                        left_table=left_table,
                        right_table=right_table,
                        left_column=left_column,
                        right_column=right_column,
                        join_type=join_type
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
            print(f"Error saving analysis results: {e}")
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
            print(f"Error saving table {table_name}: {e}")
    
    def _save_join_relationship(self, cursor, join: JoinCondition):
        """조인 관계 저장"""
        try:
            # 테이블 컴포넌트 확보 (없으면 INFERRED로 생성)
            cursor.execute("SELECT project_id FROM projects WHERE project_name = ?", (self.project_name,))
            project_row = cursor.fetchone()
            project_id = project_row[0] if project_row else None

            def ensure_table_component(table_name: str):
                """테이블 컴포넌트를 조회하거나 현재 파일 컨텍스트로 생성 (inferred 파일 생성 금지)."""
                cursor.execute(
                    """
                    SELECT component_id FROM components 
                    WHERE component_type='TABLE' 
                      AND component_name=? 
                      AND project_id=? 
                      AND del_yn='N' 
                    LIMIT 1
                    """,
                    (table_name, project_id)
                )
                row = cursor.fetchone()
                if row:
                    return row[0]

                # 현재 파일 컨텍스트 기반으로 컴포넌트 생성
                try:
                    from util.file_context import get_file_context_manager
                    ctx = get_file_context_manager().require_current_file()
                    file_id = ctx.file_id
                    if not file_id:
                        msg = f"[CommonSqlAnalyzer] 테이블 컴포넌트 누락 및 file_id 없음: {table_name}"
                        error(msg)
                        raise RuntimeError(msg)
                    comp_hash = hashlib.md5(table_name.encode()).hexdigest()
                    cursor.execute(
                        """
                        INSERT INTO components (project_id, file_id, component_name, component_type, hash_value, del_yn)
                        VALUES (?, ?, ?, 'TABLE', ?, 'N')
                        """,
                        (project_id, file_id, table_name, comp_hash)
                    )
                    return cursor.lastrowid
                except Exception as e:
                    msg = f"[CommonSqlAnalyzer] 테이블 컴포넌트 생성 실패: {table_name} (project_id={project_id})"
                    error(msg)
                    raise RuntimeError(msg) from e

            src_comp_id = ensure_table_component(join.left_table)
            dst_comp_id = ensure_table_component(join.right_table)
            
            if src_comp_id and dst_comp_id:
                # 조인 관계 저장
                cursor.execute("""
                    INSERT INTO relationships (src_id, dst_id, rel_type, confidence, del_yn, src_column, dst_column, join_condition)
                    VALUES (?, ?, ?, ?, 'N', ?, ?, ?)
                """, (src_comp_id, dst_comp_id, f"JOIN_{join.join_type}", 0.8, join.left_column.upper(), join.right_column.upper(), f"{join.left_table}.{join.left_column} = {join.right_table}.{join.right_column}"))
                
        except Exception as e:
            handle_error(e, "조인 관계 저장 실패 (inferred 파일 생성 금지 모드)")
