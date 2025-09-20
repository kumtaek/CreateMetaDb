"""
SourceAnalyzer 데이터베이스 처리 공통 유틸리티 모듈
- SQLite 연결 관리
- 쿼리 실행
- 트랜잭션 처리
- 스키마 생성
"""

import sqlite3
import os
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager
from .logger import app_logger, handle_error, error
import threading


class DatabaseCache:
    """데이터베이스 조회 결과 캐싱을 위한 싱글톤 클래스"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseCache, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._project_id_cache = {}  # {project_name: project_id}
            self._table_id_cache = {}    # {(project_name, table_name): table_id}
            self._table_component_id_cache = {}  # {(project_name, table_name): component_id}
            self._initialized = True
    
    def get_project_id(self, project_name: str) -> Optional[int]:
        """프로젝트 ID 캐시에서 조회"""
        return self._project_id_cache.get(project_name)
    
    def set_project_id(self, project_name: str, project_id: int):
        """프로젝트 ID 캐시에 저장"""
        self._project_id_cache[project_name] = project_id
    
    def get_table_id(self, project_name: str, table_name: str) -> Optional[int]:
        """테이블 ID 캐시에서 조회"""
        return self._table_id_cache.get((project_name, table_name))
    
    def set_table_id(self, project_name: str, table_name: str, table_id: int):
        """테이블 ID 캐시에 저장"""
        self._table_id_cache[(project_name, table_name)] = table_id
    
    def get_table_component_id(self, project_name: str, table_name: str) -> Optional[int]:
        """테이블 컴포넌트 ID 캐시에서 조회"""
        return self._table_component_id_cache.get((project_name, table_name))
    
    def set_table_component_id(self, project_name: str, table_name: str, component_id: int):
        """테이블 컴포넌트 ID 캐시에 저장"""
        self._table_component_id_cache[(project_name, table_name)] = component_id
    
    def clear_cache(self):
        """캐시 초기화"""
        self._project_id_cache.clear()
        self._table_id_cache.clear()
        self._table_component_id_cache.clear()


class DatabaseUtils:
    """데이터베이스 처리 관련 공통 유틸리티 클래스"""
    
    def __init__(self, db_path: str):
        """
        데이터베이스 유틸리티 초기화
        
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self.connection = None
    
    def connect(self) -> bool:
        """
        데이터베이스에 연결
        
        Returns:
            연결 성공 여부 (True/False)
        """
        try:
            # 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            
            # 외래키 제약조건 활성화
            self.connection.execute("PRAGMA foreign_keys = ON")
            
            # 성능 최적화 설정
            self.connection.execute("PRAGMA journal_mode = WAL")
            self.connection.execute("PRAGMA synchronous = NORMAL")
            self.connection.execute("PRAGMA cache_size = 10000")
            self.connection.execute("PRAGMA temp_store = MEMORY")
            
            app_logger.debug(f"데이터베이스 연결 성공: {self.db_path}")
            return True
            
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, f"데이터베이스 연결 실패: {self.db_path}")
            return False
    
    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.connection:
            try:
                self.connection.close()
                app_logger.debug(f"데이터베이스 연결 해제: {self.db_path}")
            except Exception as e:
                # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                handle_error(e, f"데이터베이스 연결 해제 실패")
            finally:
                self.connection = None
    
    @contextmanager
    def get_connection(self):
        """
        데이터베이스 연결 컨텍스트 매니저
        
        Yields:
            sqlite3.Connection: 데이터베이스 연결 객체
        """
        conn = None
        try:
            if not self.connection:
                if not self.connect():
                    raise Exception("데이터베이스 연결 실패")
            conn = self.connection
            yield conn
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"데이터베이스 연결 오류")
        finally:
            # 연결은 클래스 레벨에서 관리하므로 여기서는 닫지 않음
            pass
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        SELECT 쿼리 실행
        
        Args:
            query: 실행할 SQL 쿼리
            params: 쿼리 파라미터
            
        Returns:
            쿼리 결과 리스트
        """
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                results = []
                for row in cursor.fetchall():
                    results.append(dict(row))
                
                app_logger.debug(f"쿼리 실행 성공: {query[:50]}...")
                return results
                
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"쿼리 실행 실패: {query[:50]}...")
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        INSERT, UPDATE, DELETE 쿼리 실행
        
        Args:
            query: 실행할 SQL 쿼리
            params: 쿼리 파라미터
            
        Returns:
            영향받은 행 수
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                conn.commit()
                affected_rows = cursor.rowcount
                
                app_logger.debug(f"업데이트 쿼리 실행 성공: {query[:50]}..., 영향받은 행: {affected_rows}")
                return affected_rows
                
        except Exception as e:
            handle_error(e, f"업데이트 쿼리 실행 실패: {query[:50]}...")
            return 0
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        여러 개의 파라미터로 쿼리 실행 (배치 처리)
        
        Args:
            query: 실행할 SQL 쿼리
            params_list: 파라미터 리스트
            
        Returns:
            처리된 행 수
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                
                processed_rows = len(params_list)
                app_logger.debug(f"배치 쿼리 실행 성공: {query[:50]}..., 처리된 행: {processed_rows}")
                return processed_rows
                
        except Exception as e:
            handle_error(e, f"배치 쿼리 실행 실패: {query[:50]}...")
            return 0
    
    def execute_script(self, script_path: str) -> bool:
        """
        SQL 스크립트 파일 실행
        
        Args:
            script_path: SQL 스크립트 파일 경로
            
        Returns:
            실행 성공 여부 (True/False)
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as file:
                script_content = file.read()
            
            with self.get_connection() as conn:
                # 스크립트를 개별 문장으로 분할하여 실행
                statements = [stmt.strip() for stmt in script_content.split(';') if stmt.strip()]
                
                for statement in statements:
                    try:
                        conn.execute(statement)
                    except Exception as stmt_error:
                        # 인덱스가 이미 존재하는 경우는 무시
                        if 'already exists' in str(stmt_error):
                            app_logger.debug(f"인덱스가 이미 존재함 (무시): {statement[:50]}...")
                            continue
                        else:
                            # 다른 에러는 그대로 발생시킴
                            raise stmt_error
                
                conn.commit()
                app_logger.debug(f"SQL 스크립트 실행 성공: {script_path}")
                return True
                
        except Exception as e:
            handle_error(e, f"SQL 스크립트 실행 실패: {script_path}")
            return False
    
    def create_schema(self, schema_script_path: str) -> bool:
        """
        데이터베이스 스키마 생성
        
        Args:
            schema_script_path: 스키마 생성 스크립트 경로
            
        Returns:
            생성 성공 여부 (True/False)
        """
        return self.execute_script(schema_script_path)
    
    def table_exists(self, table_name: str) -> bool:
        """
        테이블 존재 여부 확인
        
        Args:
            table_name: 확인할 테이블명
            
        Returns:
            테이블 존재 여부 (True/False)
        """
        query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
        """
        results = self.execute_query(query, (table_name,))
        return len(results) > 0
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        테이블 구조 정보 조회
        
        Args:
            table_name: 테이블명
            
        Returns:
            테이블 구조 정보 리스트
        """
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)
    
    def get_table_count(self, table_name: str) -> int:
        """
        테이블의 레코드 수 조회
        
        Args:
            table_name: 테이블명
            
        Returns:
            레코드 수
        """
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        results = self.execute_query(query)
        return results[0]['count'] if results else 0
    
    def upsert(self, table_name: str, data: Dict[str, Any], unique_columns: List[str]) -> bool:
        """
        UPSERT 실행 (기존 레코드가 있으면 UPDATE, 없으면 INSERT)
        
        Args:
            table_name: 테이블명
            data: 삽입/업데이트할 데이터 딕셔너리
            unique_columns: 유니크 키 컬럼 리스트 (중복 확인용)
            
        Returns:
            성공 여부 (True/False)
        """
        try:
            # 기존 레코드 확인을 위한 WHERE 조건 생성
            where_conditions = {col: data[col] for col in unique_columns if col in data}
            
            if where_conditions:
                # 기존 레코드가 있는지 확인
                where_clauses = [f"{col} = ?" for col in where_conditions.keys()]
                where_values = tuple(where_conditions.values())
                
                check_query = f"""
                SELECT COUNT(*) as count FROM {table_name}
                WHERE {' AND '.join(where_clauses)}
                """
                
                results = self.execute_query(check_query, where_values)
                existing_count = results[0]['count'] if results else 0
                
                if existing_count > 0:
                    # 기존 레코드가 있으면 UPDATE
                    update_data = {k: v for k, v in data.items() if k not in unique_columns}
                    if update_data:
                        return self.update_record(table_name, update_data, where_conditions)
                    else:
                        return True  # 업데이트할 데이터가 없으면 성공으로 처리
                else:
                    # 기존 레코드가 없으면 INSERT
                    return self.insert_record(table_name, data)
            else:
                # 유니크 키가 없으면 그냥 INSERT
                return self.insert_record(table_name, data)
                
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"UPSERT 실패: {table_name}")
    
    def insert_record(self, table_name: str, data: Dict[str, Any]) -> bool:
        """
        단순 INSERT 실행
        
        Args:
            table_name: 테이블명
            data: 삽입할 데이터 딕셔너리
            
        Returns:
            성공 여부 (True/False)
        """
        try:
            columns = list(data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            values = tuple(data.values())
            
            query = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({placeholders})
            """
            
            affected_rows = self.execute_update(query, values)
            return affected_rows > 0
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"INSERT 실패: {table_name}")
    
    def insert_or_replace(self, table_name: str, data: Dict[str, Any]) -> bool:
        """
        UPSERT 실행 (기존 레코드 교체) - 데이터베이스 호환성을 위해 upsert 로직 사용
        
        Args:
            table_name: 테이블명
            data: 삽입할 데이터 딕셔너리
            
        Returns:
            성공 여부 (True/False)
        """
        try:
            # upsert 로직 사용 (데이터베이스 호환성)
            # 테이블별 unique_columns 설정
            if table_name == 'components':
                unique_columns = ['project_id', 'component_type', 'component_name', 'file_id']
            elif table_name == 'tables':
                unique_columns = ['project_id', 'table_name', 'table_owner']
            elif table_name == 'columns':
                unique_columns = ['table_id', 'column_name']
            elif table_name == 'relationships':
                unique_columns = ['src_id', 'dst_id', 'rel_type']
            else:
                unique_columns = ['project_id']  # 기본값
            
            result = self.upsert(table_name, data, unique_columns)
            return result is not None
            
        except Exception as e:
            handle_error(e, f"UPSERT 실패: {table_name}")
    
    def batch_insert_or_replace(self, table_name: str, data_list: List[Dict[str, Any]]) -> int:
        """
        배치 UPSERT 실행 (데이터베이스 호환성)
        
        Args:
            table_name: 테이블명
            data_list: 삽입할 데이터 리스트
            
        Returns:
            처리된 행 수
        """
        if not data_list:
            return 0
        
        try:
            # 테이블별 unique_columns 설정
            if table_name == 'components':
                unique_columns = ['project_id', 'component_type', 'component_name', 'file_id']
            elif table_name == 'tables':
                unique_columns = ['project_id', 'table_name', 'table_owner']
            elif table_name == 'columns':
                unique_columns = ['table_id', 'column_name']
            elif table_name == 'relationships':
                unique_columns = ['src_id', 'dst_id', 'rel_type']
            else:
                unique_columns = ['project_id']  # 기본값
            
            processed_count = 0
            for data in data_list:
                result = self.upsert(table_name, data, unique_columns)
                if result:
                    processed_count += 1
            
            return processed_count
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"배치 UPSERT 실패: {table_name}")
    
    def update_record(self, table_name: str, update_data: Dict[str, Any], where_conditions: Dict[str, Any]) -> bool:
        """
        레코드 업데이트
        
        Args:
            table_name: 테이블명
            update_data: 업데이트할 데이터 딕셔너리
            where_conditions: WHERE 조건 딕셔너리
            
        Returns:
            성공 여부 (True/False)
        """
        try:
            # SET 절 생성
            set_clauses = []
            values = []
            
            for column, value in update_data.items():
                if isinstance(value, str) and value.startswith('datetime('):
                    # SQL 함수는 그대로 사용
                    set_clauses.append(f"{column} = {value}")
                else:
                    set_clauses.append(f"{column} = ?")
                    values.append(value)
            
            # WHERE 절 생성
            where_clauses = []
            for column, value in where_conditions.items():
                where_clauses.append(f"{column} = ?")
                values.append(value)
            
            query = f"""
            UPDATE {table_name}
            SET {', '.join(set_clauses)}
            WHERE {' AND '.join(where_clauses)}
            """
            
            affected_rows = self.execute_update(query, tuple(values))
            return affected_rows > 0
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"레코드 업데이트 실패: {table_name}")
    
    def get_last_insert_id(self) -> int:
        """
        마지막 삽입된 ID 조회
        
        Returns:
            마지막 삽입된 ID
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT last_insert_rowid()")
                return cursor.fetchone()[0]
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"마지막 삽입 ID 조회 실패")
    
    def insert_or_replace_with_id(self, table_name: str, data: Dict[str, Any]) -> int:
        """
        Upsert 실행 후 삽입된 ID 반환 (직접 구현)
        
        Args:
            table_name: 테이블명
            data: 삽입할 데이터 딕셔너리
            
        Returns:
            삽입된 레코드의 ID (실패시 0)
        """
        try:
            # 디버그 로그 추가
            app_logger.debug(f"Upsert 실행: {table_name}")
            app_logger.debug(f"데이터: {data}")
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if table_name == 'components':
                    # components 테이블용 upsert 구현
                    # UNIQUE INDEX: (component_name, file_id, project_id)
                    
                    app_logger.debug(f"Components upsert 시작: {data.get('component_name')} ({data.get('component_type')})")
                    
                    # 1. 기존 레코드 존재 여부 확인
                    select_query = """
                    SELECT component_id FROM components 
                    WHERE project_id = ? AND component_name = ? AND file_id = ?
                    """
                    select_params = (data.get('project_id'), data.get('component_name'), data.get('file_id'))
                    
                    app_logger.debug(f"기존 레코드 확인 쿼리: {select_query}")
                    app_logger.debug(f"쿼리 파라미터: {select_params}")
                    
                    cursor.execute(select_query, select_params)
                    existing = cursor.fetchone()
                    
                    app_logger.debug(f"기존 레코드 조회 결과: {existing}")
                    
                    if existing:
                        # 2. 기존 레코드가 있으면 UPDATE
                        component_id = existing[0]
                        update_columns = [col for col in data.keys() if col not in ['project_id', 'component_name', 'file_id']]
                        update_set = ', '.join([f"{col} = ?" for col in update_columns])
                        update_values = [data[col] for col in update_columns] + [component_id]
                        
                        update_query = f"""
                        UPDATE components SET {update_set}
                        WHERE component_id = ?
                        """
                        
                        app_logger.debug(f"UPDATE 쿼리: {update_query}")
                        app_logger.debug(f"UPDATE 파라미터: {update_values}")
                        
                        cursor.execute(update_query, update_values)
                        
                        app_logger.debug(f"UPDATE 실행 완료: component_id = {component_id}")
                        return component_id
                    else:
                        # 3. 기존 레코드가 없으면 INSERT
                        columns = list(data.keys())
                        placeholders = ', '.join(['?' for _ in columns])
                        values = tuple(data.values())
                        
                        insert_query = f"""
                        INSERT INTO {table_name} ({', '.join(columns)})
                        VALUES ({placeholders})
                        """
                        
                        app_logger.debug(f"INSERT 쿼리: {insert_query}")
                        app_logger.debug(f"INSERT 파라미터: {values}")
                        
                        cursor.execute(insert_query, values)
                        component_id = cursor.lastrowid
                        
                        app_logger.debug(f"INSERT 실행 완료: component_id = {component_id}")
                        return component_id
                        
                elif table_name == 'classes':
                    # classes 테이블용 upsert 구현
                    # UNIQUE INDEX: (class_name, file_id, project_id)
                    
                    app_logger.debug(f"Classes upsert 시작: {data.get('class_name')}")
                    
                    # 1. 기존 레코드 존재 여부 확인
                    select_query = """
                    SELECT class_id FROM classes 
                    WHERE project_id = ? AND class_name = ? AND file_id = ?
                    """
                    select_params = (data.get('project_id'), data.get('class_name'), data.get('file_id'))
                    
                    app_logger.debug(f"기존 레코드 확인 쿼리: {select_query}")
                    app_logger.debug(f"쿼리 파라미터: {select_params}")
                    
                    cursor.execute(select_query, select_params)
                    existing = cursor.fetchone()
                    
                    app_logger.debug(f"기존 레코드 조회 결과: {existing}")
                    
                    if existing:
                        # 2. 기존 레코드가 있으면 UPDATE
                        class_id = existing[0]
                        update_columns = [col for col in data.keys() if col not in ['project_id', 'class_name', 'file_id']]
                        update_set = ', '.join([f"{col} = ?" for col in update_columns])
                        update_values = [data[col] for col in update_columns] + [class_id]
                        
                        update_query = f"""
                        UPDATE classes SET {update_set}
                        WHERE class_id = ?
                        """
                        
                        app_logger.debug(f"UPDATE 쿼리: {update_query}")
                        app_logger.debug(f"UPDATE 파라미터: {update_values}")
                        
                        cursor.execute(update_query, update_values)
                        
                        app_logger.debug(f"UPDATE 실행 완료: class_id = {class_id}")
                        return class_id
                    else:
                        # 3. 기존 레코드가 없으면 INSERT
                        columns = list(data.keys())
                        placeholders = ', '.join(['?' for _ in columns])
                        values = tuple(data.values())
                        
                        insert_query = f"""
                        INSERT INTO {table_name} ({', '.join(columns)})
                        VALUES ({placeholders})
                        """
                        
                        app_logger.debug(f"INSERT 쿼리: {insert_query}")
                        app_logger.debug(f"INSERT 파라미터: {values}")
                        
                        cursor.execute(insert_query, values)
                        class_id = cursor.lastrowid
                        
                        app_logger.debug(f"INSERT 실행 완료: class_id = {class_id}")
                        return class_id
                else:
                    # 다른 테이블용 기본 구현
                    columns = list(data.keys())
                    placeholders = ', '.join(['?' for _ in columns])
                    values = tuple(data.values())
                    
                    # upsert 로직 사용 (데이터베이스 호환성)
                    # 테이블별 unique_columns 설정
                    if table_name == 'components':
                        unique_columns = ['project_id', 'component_type', 'component_name', 'file_id']
                    elif table_name == 'tables':
                        unique_columns = ['project_id', 'table_name', 'table_owner']
                    elif table_name == 'columns':
                        unique_columns = ['table_id', 'column_name']
                    elif table_name == 'relationships':
                        unique_columns = ['src_id', 'dst_id', 'rel_type']
                    else:
                        unique_columns = ['project_id']  # 기본값
                    
                    result = self.upsert(table_name, data, unique_columns)
                    return result if result else 0
                
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"Upsert 실패: {table_name}")
    
    def begin_transaction(self):
        """트랜잭션 시작"""
        try:
            with self.get_connection() as conn:
                conn.execute("BEGIN TRANSACTION")
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"트랜잭션 시작 실패")
    
    def commit_transaction(self):
        """트랜잭션 커밋"""
        try:
            with self.get_connection() as conn:
                conn.commit()
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"트랜잭션 커밋 실패")
    
    def rollback_transaction(self):
        """트랜잭션 롤백"""
        try:
            with self.get_connection() as conn:
                conn.rollback()
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"트랜잭션 롤백 실패")
    
    @contextmanager
    def transaction(self):
        """
        트랜잭션 컨텍스트 매니저
        
        Yields:
            DatabaseUtils: 자기 자신
        """
        try:
            self.begin_transaction()
            yield self
            self.commit_transaction()
        except Exception as e:
            self.rollback_transaction()
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"트랜잭션 오류")
    
    def vacuum(self):
        """데이터베이스 최적화 (VACUUM)"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                app_logger.debug("데이터베이스 최적화 완료")
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"데이터베이스 최적화 실패")
    
    def analyze(self):
        """통계 정보 업데이트 (ANALYZE)"""
        try:
            with self.get_connection() as conn:
                conn.execute("ANALYZE")
                app_logger.debug("통계 정보 업데이트 완료")
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"통계 정보 업데이트 실패")
    
    def get_project_id(self, project_name: str) -> Optional[int]:
        """
        프로젝트 ID 조회 (캐싱 적용)
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            프로젝트 ID 또는 None
        """
        cache = DatabaseCache()
        
        # 캐시에서 먼저 조회
        cached_id = cache.get_project_id(project_name)
        if cached_id is not None:
            return cached_id
        
        # 캐시에 없으면 DB에서 조회
        try:
            query = "SELECT project_id FROM projects WHERE project_name = ?"
            results = self.execute_query(query, (project_name,))
            
            if results:
                project_id = results[0]['project_id']
                # 캐시에 저장
                cache.set_project_id(project_name, project_id)
                return project_id
            return None
            
        except Exception as e:
            handle_error(e, f"프로젝트 ID 조회 실패: {project_name}")
            return None
    
    def get_table_id(self, project_name: str, table_name: str) -> Optional[int]:
        """
        테이블 ID 조회 (table_owner 우선순위 적용)
        
        Args:
            project_name: 프로젝트명
            table_name: 테이블명
            
        Returns:
            테이블 ID 또는 None
        """
        try:
            # table_owner 우선순위: 'UNKNOWN'이 아닌 것을 우선, LIMIT 1로 한 건만 선택
            query = """
                SELECT t.table_id 
                FROM tables t
                JOIN projects p ON t.project_id = p.project_id
                WHERE p.project_name = ? AND t.table_name = ? AND t.del_yn = 'N'
                ORDER BY CASE WHEN t.table_owner = 'UNKNOWN' THEN 1 ELSE 0 END, t.table_id
                LIMIT 1
            """
            results = self.execute_query(query, (project_name, table_name.upper()))
            
            if results and len(results) > 0:
                return results[0]['table_id']
            return None
            
        except Exception as e:
            handle_error(e, f"테이블 ID 조회 실패: {table_name}")
            return None
    
    def get_table_component_id(self, project_name: str, table_name: str) -> Optional[int]:
        """
        테이블 컴포넌트 ID 조회 (table_owner 우선순위 적용)
        
        Args:
            project_name: 프로젝트명
            table_name: 테이블명
            
        Returns:
            컴포넌트 ID 또는 None
        """
        try:
            query = """
                SELECT c.component_id 
                FROM components c
                JOIN projects p ON c.project_id = p.project_id
                JOIN tables t ON c.component_id = t.component_id
                WHERE p.project_name = ? AND t.table_name = ? AND c.del_yn = 'N'
                ORDER BY CASE WHEN t.table_owner = 'UNKNOWN' THEN 1 ELSE 0 END, c.component_id
                LIMIT 1
            """
            results = self.execute_query(query, (project_name, table_name.upper()))
            
            if results and len(results) > 0:
                return results[0]['component_id']
            return None
            
        except Exception as e:
            handle_error(e, f"테이블 컴포넌트 ID 조회 실패: {table_name}")
            return None
    
    def get_components_by_parent_id(self, project_name: str, parent_id: int, component_type: str = None) -> List[Dict[str, Any]]:
        """
        parent_id로 하위 컴포넌트들 조회
        
        Args:
            project_name: 프로젝트명
            parent_id: 부모 컴포넌트 ID
            component_type: 컴포넌트 타입 필터 (선택사항)
            
        Returns:
            하위 컴포넌트 리스트
        """
        try:
            if component_type:
                query = """
                    SELECT c.* FROM components c
                    JOIN projects p ON c.project_id = p.project_id
                    WHERE p.project_name = ? AND c.parent_id = ? AND c.component_type = ? AND c.del_yn = 'N'
                """
                results = self.execute_query(query, (project_name, parent_id, component_type))
            else:
                query = """
                    SELECT c.* FROM components c
                    JOIN projects p ON c.project_id = p.project_id
                    WHERE p.project_name = ? AND c.parent_id = ? AND c.del_yn = 'N'
                """
                results = self.execute_query(query, (project_name, parent_id))
            
            return results if results else []
            
        except Exception as e:
            handle_error(e, f"하위 컴포넌트 조회 실패: {project_name}, parent_id={parent_id}")
            return []
    
    def get_component_id(self, project_id: int, component_name: str, component_type: str) -> Optional[int]:
        """
        컴포넌트 ID 조회
        
        Args:
            project_id: 프로젝트 ID
            component_name: 컴포넌트명
            component_type: 컴포넌트 타입
            
        Returns:
            컴포넌트 ID (없으면 None)
        """
        try:
            query = """
                SELECT component_id 
                FROM components 
                WHERE project_id = ? AND component_name = ? AND component_type = ? AND del_yn = 'N'
                LIMIT 1
            """
            param_component_name = component_name.upper() if component_type in ['TABLE', 'COLUMN'] else component_name
            results = self.execute_query(query, (project_id, param_component_name, component_type))
            
            if results and len(results) > 0:
                return results[0]['component_id']
            return None
            
        except Exception as e:
            handle_error(e, f"컴포넌트 ID 조회 실패: {component_name}")
            return None
    
    def find_method_by_api_pattern(self, project_id: int, api_url: str, http_method: str) -> Optional[int]:
        """
        API URL 패턴으로 매칭되는 METHOD 컴포넌트 찾기
        
        Args:
            project_id: 프로젝트 ID
            api_url: API URL 패턴
            http_method: HTTP 메서드
            
        Returns:
            METHOD 컴포넌트 ID (없으면 None)
        """
        try:
            # USER RULES: 하드코딩 지양 - 실제 클래스명과 메서드명으로 매칭
            # Spring Controller의 @RequestMapping, @GetMapping 등으로 매핑된 메서드 찾기
            # URL 패턴에서 클래스명과 메서드명을 추출하여 정확한 매칭 수행
            
            # 임시로 모든 METHOD 컴포넌트 중에서 첫 번째를 반환 (단순 구현)
            # TODO: 실제 URL 패턴 매칭 로직 구현 필요
            query = """
                SELECT c.component_id 
                FROM components c
                WHERE c.project_id = ? 
                  AND c.component_type = 'METHOD'
                  AND c.layer IN ('CONTROLLER', 'REST_CONTROLLER', 'SERVLET')
                  AND c.del_yn = 'N'
                LIMIT 1
            """
            results = self.execute_query(query, (project_id,))
            
            if results and len(results) > 0:
                return results[0]['component_id']
            return None
            
        except Exception as e:
            handle_error(e, f"METHOD 컴포넌트 매칭 실패: {api_url}:{http_method}")
            return None
    
    def get_columns_by_table_component_id(self, project_name: str, table_component_id: int) -> List[Dict[str, Any]]:
        """
        테이블의 component_id로 해당 테이블의 모든 컬럼 조회
        
        Args:
            project_name: 프로젝트명
            table_component_id: 테이블의 component_id
            
        Returns:
            컬럼 정보 리스트
        """
        try:
            query = """
                SELECT c.*, comp.component_name, comp.component_type
                FROM columns c
                JOIN components comp ON c.table_id = (
                    SELECT t.table_id 
                    FROM tables t 
                    WHERE t.component_id = ?
                )
                WHERE comp.parent_id = ? AND comp.component_type = 'COLUMN' AND comp.del_yn = 'N'
            """
            results = self.execute_query(query, (table_component_id, table_component_id))
            return results if results else []
            
        except Exception as e:
            handle_error(e, f"테이블 컬럼 조회 실패: {project_name}, component_id={table_component_id}")
            return []
    
    def get_column_component_by_name_and_parent(self, project_name: str, column_name: str, parent_id: int) -> Optional[Dict[str, Any]]:
        """
        컬럼명과 parent_id로 컬럼 컴포넌트 조회
        
        Args:
            project_name: 프로젝트명
            column_name: 컬럼명
            parent_id: 부모 테이블의 component_id
            
        Returns:
            컬럼 컴포넌트 정보 또는 None
        """
        try:
            query = """
                SELECT comp.*, c.*
                FROM components comp
                LEFT JOIN columns c ON comp.component_id = c.component_id
                WHERE comp.project_id = (
                    SELECT project_id FROM projects WHERE project_name = ?
                )
                AND comp.component_name = ? 
                AND comp.parent_id = ? 
                AND comp.component_type = 'COLUMN' 
                AND comp.del_yn = 'N'
            """
            results = self.execute_query(query, (project_name, column_name.upper(), parent_id))
            return results[0] if results else None
            
        except Exception as e:
            handle_error(e, f"컬럼 컴포넌트 조회 실패: {project_name}, {column_name}, parent_id={parent_id}")
            return None
    
    def get_table_columns_by_parent_id(self, project_name: str, table_component_id: int) -> List[Dict[str, Any]]:
        """
        테이블의 component_id로 해당 테이블의 모든 컬럼 조회 (간소화된 버전)

        Args:
            project_name: 프로젝트명
            table_component_id: 테이블의 component_id

        Returns:
            컬럼 정보 리스트
        """
        try:
            query = """
                SELECT comp.component_id, comp.component_name, comp.component_type, comp.parent_id
                FROM components comp
                WHERE comp.project_id = (
                    SELECT project_id FROM projects WHERE project_name = ?
                )
                AND comp.parent_id = ?
                AND comp.component_type = 'COLUMN'
                AND comp.del_yn = 'N'
            """
            results = self.execute_query(query, (project_name, table_component_id))
            return results if results else []

        except Exception as e:
            handle_error(e, f"테이블 컬럼 조회 실패: {project_name}, component_id={table_component_id}")
            return []

    def insert_relationship(self, src_id: int, dst_id: int, rel_type: str, confidence: float = 1.0) -> bool:
        """
        relationships 테이블에 연관관계 저장 (중복 방지)

        Args:
            src_id: 소스 컴포넌트 ID
            dst_id: 대상 컴포넌트 ID
            rel_type: 관계 타입
            confidence: 신뢰도 (기본값: 1.0)

        Returns:
            저장 성공 여부
        """
        try:
            if not src_id or not dst_id:
                app_logger.warning(f"소스(src) 또는 대상(dst) ID가 없어 관계 저장을 건너뜁니다: {rel_type}")
                return False

            sql = """
                INSERT OR IGNORE INTO relationships (src_id, dst_id, rel_type, confidence, has_error, del_yn)
                VALUES (?, ?, ?, ?, 'N', 'N')
            """
            result = self.execute_update(sql, (src_id, dst_id, rel_type, confidence))
            return result > 0

        except Exception as e:
            handle_error(e, f"관계 저장 실패: {src_id} → {dst_id} ({rel_type})")
            return False

    def find_component_id(self, project_id: int, component_name: str, component_type: str = None, file_id: int = None) -> Optional[int]:
        """
        이름, 타입, 파일 ID로 컴포넌트 ID 조회

        Args:
            project_id: 프로젝트 ID
            component_name: 컴포넌트명
            component_type: 컴포넌트 타입 (선택적)
            file_id: 파일 ID (선택적)

        Returns:
            컴포넌트 ID 또는 None
        """
        try:
            query = "SELECT component_id FROM components WHERE project_id = ? AND component_name = ? AND del_yn = 'N'"
            params = [project_id, component_name]

            if component_type:
                query += " AND component_type = ?"
                params.append(component_type)
            if file_id:
                query += " AND file_id = ?"
                params.append(file_id)
            query += " LIMIT 1"

            result = self.execute_query(query, tuple(params))
            return result[0]['component_id'] if result else None

        except Exception as e:
            handle_error(e, f"컴포넌트 ID 조회 실패: {component_name}")
            return None

    def find_or_create_component(self, project_id: int, component_name: str, component_type: str,
                                 file_id: int = None, parent_id: int = None, layer: str = None) -> Optional[int]:
        """
        컴포넌트 조회 또는 생성

        Args:
            project_id: 프로젝트 ID
            component_name: 컴포넌트명
            component_type: 컴포넌트 타입
            file_id: 파일 ID (선택적)
            parent_id: 부모 컴포넌트 ID (선택적)
            layer: 레이어 (선택적)

        Returns:
            컴포넌트 ID 또는 None
        """
        try:
            # 기존 컴포넌트 찾기
            component_id = self.find_component_id(project_id, component_name, component_type, file_id)

            if component_id:
                return component_id

            # 새 컴포넌트 생성
            component_data = {
                'project_id': project_id,
                'file_id': file_id,
                'component_type': component_type,
                'component_name': component_name,
                'parent_id': parent_id,
                'layer': layer or component_type,
                'hash_value': 'INFERRED',
                'del_yn': 'N'
            }

            return self.insert_or_replace('components', component_data)

        except Exception as e:
            handle_error(e, f"컴포넌트 조회/생성 실패: {component_name}")
            return None

    def create_inferred_table_component(self, project_id: int, table_name: str) -> Optional[int]:
        """
        추론된 테이블 컴포넌트 생성

        Args:
            project_id: 프로젝트 ID
            table_name: 테이블명

        Returns:
            생성된 컴포넌트 ID 또는 None
        """
        try:
            # 기존 테이블 컴포넌트 확인
            existing_id = self.find_component_id(project_id, table_name, 'TABLE')
            if existing_id:
                return existing_id

            # 새 테이블 컴포넌트 생성
            component_data = {
                'project_id': project_id,
                'file_id': None,  # 추론된 컴포넌트는 특정 파일에 속하지 않음
                'component_type': 'TABLE',
                'component_name': table_name,
                'parent_id': None,
                'layer': 'TABLE',
                'hash_value': 'INFERRED',
                'del_yn': 'N'
            }

            component_id = self.insert_or_replace('components', component_data)

            # tables 테이블에도 추가
            if component_id:
                table_data = {
                    'project_id': project_id,
                    'table_name': table_name,
                    'table_owner': 'INFERRED',
                    'table_comments': 'Inferred from SQL analysis',
                    'component_id': component_id,
                    'hash_value': 'INFERRED',
                    'del_yn': 'N'
                }

                self.insert_or_replace('tables', table_data)

            return component_id

        except Exception as e:
            handle_error(e, f"추론된 테이블 컴포넌트 생성 실패: {table_name}")
            return None

    def get_relationship_count(self, project_id: int = None) -> int:
        """
        저장된 관계 수 조회

        Args:
            project_id: 프로젝트 ID (선택적)

        Returns:
            관계 수
        """
        try:
            if project_id:
                query = """
                    SELECT COUNT(*) as count FROM relationships r
                    JOIN components c ON r.src_id = c.component_id
                    WHERE c.project_id = ? AND r.del_yn = 'N'
                """
                result = self.execute_query(query, (project_id,))
            else:
                query = "SELECT COUNT(*) as count FROM relationships WHERE del_yn = 'N'"
                result = self.execute_query(query)

            return result[0]['count'] if result else 0

        except Exception as e:
            handle_error(e, "관계 수 조회 실패")
            return 0


# 편의 함수들
def create_database_connection(db_path: str) -> Optional[DatabaseUtils]:
    """
    데이터베이스 연결 생성 편의 함수
    
    Args:
        db_path: 데이터베이스 파일 경로
        
    Returns:
        DatabaseUtils 인스턴스 또는 None
    """
    db_utils = DatabaseUtils(db_path)
    if db_utils.connect():
        return db_utils
    return None


def execute_sql_script(db_path: str, script_path: str) -> bool:
    """
    SQL 스크립트 실행 편의 함수
    
    Args:
        db_path: 데이터베이스 파일 경로
        script_path: SQL 스크립트 파일 경로
        
    Returns:
        실행 성공 여부 (True/False)
    """
    db_utils = DatabaseUtils(db_path)
    try:
        if db_utils.connect():
            return db_utils.execute_script(script_path)
        return False
    finally:
        db_utils.disconnect()
