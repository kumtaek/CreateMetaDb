"""
공통 쿼리 처리 함수
목표: 쿼리 추출 → 쿼리 저장 → 테이블 추출 → 조인 관계 추출
"""

import re
import gzip
from typing import Dict, List, Any, Optional
from util import handle_error, debug, info
from util.database_utils import DatabaseUtils
from util.sql_content_manager import SqlContentManager
from util.oracle_keyword_manager import get_oracle_keyword_manager


class CommonQueryProcessor:
    """공통 쿼리 처리기"""
    
    def __init__(self, project_name: str, conn):
        self.project_name = project_name
        self.conn = conn
        self.sql_content_manager = SqlContentManager(project_name)
        self.oracle_keyword_manager = get_oracle_keyword_manager()
        
        self.stats = {
            'queries_processed': 0,
            'tables_extracted': 0,
            'joins_extracted': 0,
            'errors': 0
        }

    def process_query(self, file_id: int, method_component_id: int, query_data: Dict[str, Any]) -> bool:
        """
        공통 쿼리 처리 - 3단계
        
        Args:
            file_id: 파일 ID
            method_component_id: 메서드 컴포넌트 ID
            query_data: {'query_id': str, 'sql_content': str, 'query_type': str}
        """
        try:
            # 필수 키 검증
            if not query_data.get('query_id'):
                handle_error(Exception('query_id is missing'), 'query_id 누락')
                return False
            # 1단계: 쿼리 저장 및 components 등록
            query_component_id = self._save_query_component(file_id, query_data)
            if not query_component_id:
                return False
            
            # METHOD → QUERY 관계 생성
            self._create_method_query_relationship(method_component_id, query_component_id)
            
            # 2단계: 테이블 추출
            tables = self._extract_tables_from_sql(query_data['sql_content'])
            self._save_tables(tables)
            
            # 3단계: 조인 관계 추출
            joins = self._extract_joins_from_sql(query_data['sql_content'], tables)
            self._save_joins(joins)
            
            self.stats['queries_processed'] += 1
            return True
            
        except Exception as e:
            handle_error(e, f"쿼리 처리 실패: {query_data.get('query_id', 'Unknown')}")
            self.stats['errors'] += 1
            return False

    def _save_query_component(self, file_id: int, query_data: Dict[str, Any]) -> Optional[int]:
        """쿼리 컴포넌트 저장"""
        try:
            # components 테이블에 저장
            component_data = {
                'project_id': 1,  # SampleSrc 프로젝트 ID
                'file_id': file_id,
                'component_name': query_data['query_id'],
                'component_type': query_data['query_type'],
                'parent_id': None,
                'hash_value': 'QUERY'
            }
            
            component_id = self._insert_or_replace_component(component_data)
            
            # SqlContent에 저장
            self.sql_content_manager.save_sql_content(
                conn=self.conn,
                component_id=component_id,
                sql_content=query_data['sql_content'],
                file_id=file_id,
                project_id=1
            )
            
            return component_id
            
        except Exception as e:
            handle_error(e, f"쿼리 컴포넌트 저장 실패: {query_data['query_id']}")
            return None

    def _create_method_query_relationship(self, method_id: int, query_id: int) -> None:
        """METHOD → QUERY 관계 생성"""
        try:
            sql = """
                INSERT OR IGNORE INTO relationships (src_id, dst_id, rel_type, confidence, has_error, del_yn)
                VALUES (?, ?, 'EXECUTES_QUERY', 1.0, 'N', 'N')
            """
            self._execute_update(sql, (method_id, query_id))
            
        except Exception as e:
            handle_error(e, f"METHOD → QUERY 관계 생성 실패: {method_id} → {query_id}")

    def _extract_tables_from_sql(self, sql_content: str) -> List[Dict[str, Any]]:
        """SQL에서 테이블 추출 - 심플 버전"""
        try:
            tables = []
            
            # 주석 제거
            sql_clean = re.sub(r'--.*?$', '', sql_content, flags=re.MULTILINE)
            sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
            
            # 테이블 추출 패턴들
            patterns = [
                r'FROM\s+(\w+)',
                r'INSERT\s+INTO\s+(\w+)',
                r'UPDATE\s+(\w+)\s+SET',
                r'DELETE\s+FROM\s+(\w+)',
                r'MERGE\s+INTO\s+(\w+)',
                r'JOIN\s+(\w+)\s+ON',
                r'USING\s+(\w+)\s+ON'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, sql_clean, re.IGNORECASE)
                for match in matches:
                    table_name = match.upper()
                    if not self.oracle_keyword_manager.is_oracle_keyword(table_name):
                        tables.append({
                            'table_name': table_name,
                            'alias': None
                        })
            
            # 중복 제거
            unique_tables = []
            seen = set()
            for table in tables:
                if table['table_name'] not in seen:
                    unique_tables.append(table)
                    seen.add(table['table_name'])
            
            return unique_tables
            
        except Exception as e:
            handle_error(e, "테이블 추출 실패")
            return []

    def _save_tables(self, tables: List[Dict[str, Any]]) -> None:
        """테이블 저장"""
        try:
            for table in tables:
                table_name = table['table_name']
                
                # 기존 테이블 확인
                query = "SELECT component_id FROM components WHERE component_name = ? AND component_type = 'TABLE' AND del_yn = 'N' LIMIT 1"
                result = self._execute_query(query, (table_name,))
                
                if not result:
                    # INFERRED 테이블 생성
                    self._create_inferred_table(table_name)
                    self.stats['tables_extracted'] += 1
                    
        except Exception as e:
            handle_error(e, "테이블 저장 실패")

    def _create_inferred_table(self, table_name: str) -> None:
        """INFERRED 테이블 생성"""
        try:
            # components 테이블에 저장
            component_data = {
                'project_id': 1,
                'file_id': 1,  # inferred 컴포넌트용 file_id
                'component_name': table_name,
                'component_type': 'TABLE',
                'parent_id': None,
                'hash_value': 'INFERRED'
            }
            
            component_id = self.db_utils.insert_or_replace('components', component_data)
            
            # tables 테이블에 저장
            table_data = {
                'project_id': 1,
                'table_name': table_name,
                'table_owner': 'UNKNOWN',
                'table_comments': 'Inferred from SQL analysis',
                'component_id': component_id,
                'hash_value': 'INFERRED'
            }
            
            self.db_utils.insert_or_replace('tables', table_data)
            
        except Exception as e:
            handle_error(e, f"INFERRED 테이블 생성 실패: {table_name}")

    def _extract_joins_from_sql(self, sql_content: str, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """SQL에서 조인 관계 추출 - 심플 버전"""
        try:
            joins = []
            
            # 주석 제거
            sql_clean = re.sub(r'--.*?$', '', sql_content, flags=re.MULTILINE)
            sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
            
            # 조인 패턴들
            join_patterns = [
                r'JOIN\s+(\w+)\s+ON\s+(\w+\.\w+)\s*=\s*(\w+\.\w+)',
                r'WHERE\s+(\w+\.\w+)\s*=\s*(\w+\.\w+)'
            ]
            
            for pattern in join_patterns:
                matches = re.finditer(pattern, sql_clean, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) >= 3:
                        table1 = match.group(1).upper()
                        column1 = match.group(2).upper()
                        column2 = match.group(3).upper()
                        
                        # 테이블명 추출
                        if '.' in column1:
                            table1_from_col = column1.split('.')[0]
                        if '.' in column2:
                            table2_from_col = column2.split('.')[0]
                        
                        joins.append({
                            'table1': table1,
                            'table2': table2_from_col if '.' in column2 else table1,
                            'column1': column1,
                            'column2': column2,
                            'join_type': 'JOIN_EXPLICIT' if 'JOIN' in pattern else 'JOIN_IMPLICIT'
                        })
            
            return joins
            
        except Exception as e:
            handle_error(e, "조인 관계 추출 실패")
            return []

    def _save_joins(self, joins: List[Dict[str, Any]]) -> None:
        """조인 관계 저장"""
        try:
            for join in joins:
                # 테이블 컴포넌트 ID 찾기
                table1_id = self._find_table_component_id(join['table1'])
                table2_id = self._find_table_component_id(join['table2'])
                
                if table1_id and table2_id and table1_id != table2_id:
                    # 조인 관계 저장
                    sql = """
                        INSERT OR IGNORE INTO relationships (src_id, dst_id, rel_type, confidence, has_error, del_yn)
                        VALUES (?, ?, ?, 1.0, 'N', 'N')
                    """
                    self.db_utils.execute_update(sql, (table1_id, table2_id, join['join_type']), conn=self.conn)
                    self.stats['joins_extracted'] += 1
                    
        except Exception as e:
            handle_error(e, "조인 관계 저장 실패")

    def _find_table_component_id(self, table_name: str) -> Optional[int]:
        """테이블 컴포넌트 ID 찾기"""
        try:
            query = "SELECT component_id FROM components WHERE component_name = ? AND component_type = 'TABLE' AND del_yn = 'N' LIMIT 1"
            result = self._execute_query(query, (table_name,))
            return result[0]['component_id'] if result else None
            
        except Exception as e:
            handle_error(e, f"테이블 컴포넌트 ID 찾기 실패: {table_name}")
            return None

    def _insert_or_replace_component(self, component_data: Dict[str, Any]) -> int:
        """컴포넌트 삽입 또는 교체"""
        try:
            cursor = self.conn.cursor()
            
            # 기존 컴포넌트 확인
            check_sql = """
                SELECT component_id FROM components 
                WHERE component_name = ? AND file_id = ? AND project_id = ? AND del_yn = 'N'
            """
            cursor.execute(check_sql, (
                component_data['component_name'],
                component_data['file_id'],
                component_data['project_id']
            ))
            result = cursor.fetchone()
            
            if result:
                # 기존 컴포넌트 업데이트
                update_sql = """
                    UPDATE components SET 
                        component_type = ?, parent_id = ?, hash_value = ?, 
                        updated_at = datetime('now', '+9 hours')
                    WHERE component_id = ?
                """
                cursor.execute(update_sql, (
                    component_data['component_type'],
                    component_data['parent_id'],
                    component_data['hash_value'],
                    result[0]
                ))
                return result[0]
            else:
                # 새 컴포넌트 삽입
                insert_sql = """
                    INSERT INTO components 
                    (project_id, file_id, component_name, component_type, parent_id, hash_value, created_at, updated_at, del_yn)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now', '+9 hours'), datetime('now', '+9 hours'), 'N')
                """
                cursor.execute(insert_sql, (
                    component_data['project_id'],
                    component_data['file_id'],
                    component_data['component_name'],
                    component_data['component_type'],
                    component_data['parent_id'],
                    component_data['hash_value']
                ))
                return cursor.lastrowid
                
        except Exception as e:
            handle_error(e, f"컴포넌트 저장 실패: {component_data.get('component_name', 'Unknown')}")

    def _execute_update(self, sql: str, params: tuple) -> None:
        """SQL 업데이트 실행"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            self.conn.commit()
        except Exception as e:
            handle_error(e, f"SQL 업데이트 실패: {sql}")

    def _execute_query(self, sql: str, params: tuple) -> List[Dict[str, Any]]:
        """SQL 쿼리 실행"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            handle_error(e, f"SQL 쿼리 실행 실패: {sql}")
            return []

    def get_statistics(self) -> Dict[str, int]:
        """통계 반환"""
        return self.stats.copy()
