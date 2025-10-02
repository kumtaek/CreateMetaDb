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
                    
                    # 테이블 추출
                    tables = self._extract_tables(clean_sql)
                    all_tables.update(tables)
                    
                    # 조인 관계 추출
                    joins = self._extract_join_relationships(clean_sql, tables)
                    all_joins.extend(joins)
                    
                except Exception as e:
                    print(f"Error analyzing query {component_name}: {e}")
                    continue
            
            # 결과 정리
            results['tables'] = list(all_tables)
            results['join_relationships'] = all_joins
            results['statistics']['tables_found'] = len(all_tables)
            results['statistics']['joins_found'] = len(all_joins)
            
            conn.close()
            
        except Exception as e:
            print(f"Error in analyze_all_queries: {e}")
            
        return results
    
    def _remove_comments(self, sql: str) -> str:
        """SQL 주석 제거"""
        # -- 주석 제거
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
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
                # 조인 관계 저장
                cursor.execute("""
                    INSERT INTO relationships (src_id, dst_id, rel_type, confidence, del_yn)
                    VALUES (?, ?, ?, ?, 'N')
                """, (left_table_id[0], right_table_id[0], f"JOIN_{join.join_type}", 0.8))
                
        except Exception as e:
            print(f"Error saving join relationship: {e}")
