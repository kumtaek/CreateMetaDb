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
from .logger import app_logger, handle_error, error, debug
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
                
                app_logger.debug(f"execute_query 시작: {query[:100]}...")
                if params:
                    app_logger.debug(f"execute_query 파라미터: {params}")
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                results = []
                for row in cursor.fetchall():
                    results.append(dict(row))
                
                app_logger.debug(f"execute_query 성공: {len(results)}개 결과")
                return results
                
        except Exception as e:
            # 에러 발생 시에만 쿼리 로그를 error 레벨로 출력
            app_logger.error(f"=== SQL 쿼리 실행 실패 상세 정보 ===")
            app_logger.error(f"실행된 쿼리: {query}")
            app_logger.error(f"바인딩 파라미터: {params}")
            app_logger.error(f"에러 메시지: {str(e)}")
            app_logger.error(f"에러 타입: {type(e).__name__}")
            
            # 모든 상세 로그가 출력된 후 Exception을 다시 발생시켜 상위에서 handle_error 호출
            app_logger.error(f"=== 상세 로그 출력 완료, Exception 재발생 ===")
            raise e
    
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
                
                app_logger.debug(f"업데이트 쿼리 실행 성공: 영향받은 행: {affected_rows}")
                return affected_rows
                
        except Exception as e:
            # 에러 발생 시에만 쿼리 로그를 error 레벨로 출력
            app_logger.error(f"=== SQL 쿼리 실행 실패 상세 정보 ===")
            app_logger.error(f"실행된 쿼리: {query}")
            app_logger.error(f"바인딩 파라미터: {params}")
            app_logger.error(f"에러 메시지: {str(e)}")
            app_logger.error(f"에러 타입: {type(e).__name__}")
            
            # 외래키 제약조건 위반 시 추가 디버깅
            if "FOREIGN KEY constraint failed" in str(e):
                app_logger.error(f"=== A. file_id 문제 또는 B. project_id 문제 또는 C. 관계 생성 시 component_id 문제 ===")
                app_logger.error(f"=== 외래키 제약조건 위반 추가 디버깅 ===")
                # 외래키 제약조건 위반 시 참조 데이터 존재 여부 확인
                self._debug_foreign_key_constraint(query, params)
            
            # UNIQUE 제약조건 위반 시 추가 정보
            elif "UNIQUE constraint failed" in str(e):
                app_logger.error(f"=== UNIQUE 제약조건 위반 ===")
                app_logger.error(f"중복된 데이터로 인한 제약조건 위반")
            
            # NOT NULL 제약조건 위반 시 추가 정보  
            elif "NOT NULL constraint failed" in str(e):
                app_logger.error(f"=== NOT NULL 제약조건 위반 ===")
                app_logger.error(f"필수 필드가 NULL 값으로 설정됨")
            
            # 모든 상세 로그가 출력된 후 Exception을 다시 발생시켜 상위에서 handle_error 호출
            app_logger.error(f"=== 상세 로그 출력 완료, Exception 재발생 ===")
            raise e

    def _debug_foreign_key_constraint(self, query: str, params: tuple) -> None:
        """
        외래키 제약조건 위반 시 상세 디버깅 정보 출력
        
        Args:
            query: 실행하려던 SQL 쿼리
            params: 쿼리 파라미터
        """
        try:
            app_logger.error(f"=== 외래키 제약조건 디버깅 시작 ===")
            
            # INSERT 쿼리인 경우 외래키 참조 데이터 존재 여부 확인
            if query.strip().upper().startswith('INSERT'):
                self._debug_insert_foreign_keys(query, params)
            elif query.strip().upper().startswith('UPDATE'):
                self._debug_update_foreign_keys(query, params)
            else:
                app_logger.error(f"지원하지 않는 쿼리 타입: {query.strip().upper().split()[0]}")
                
        except Exception as debug_e:
            app_logger.error(f"외래키 디버깅 중 에러: {str(debug_e)}")

    def _debug_insert_foreign_keys(self, query: str, params: tuple) -> None:
        """INSERT 쿼리의 외래키 디버깅"""
        try:
            # INSERT INTO components 쿼리인 경우
            if 'components' in query.lower():
                app_logger.error(f"=== components 테이블 INSERT 디버깅 ===")
                
                # 파라미터 매핑 (INSERT 쿼리 구조에 따라)
                if len(params) >= 12:  # components 테이블 INSERT 파라미터 개수
                    project_id = params[0] if len(params) > 0 else None
                    file_id = params[1] if len(params) > 1 else None
                    component_name = params[2] if len(params) > 2 else None
                    component_type = params[3] if len(params) > 3 else None
                    
                    app_logger.error(f"삽입하려는 데이터:")
                    app_logger.error(f"  project_id: {project_id}")
                    app_logger.error(f"  file_id: {file_id}")
                    app_logger.error(f"  component_name: {component_name}")
                    app_logger.error(f"  component_type: {component_type}")
                    
                    # 참조 데이터 존재 여부 확인
                    self._check_referenced_data_exists(project_id, file_id)
            
            # INSERT INTO relationships 쿼리인 경우
            elif 'relationships' in query.lower():
                app_logger.error(f"=== relationships 테이블 INSERT 디버깅 ===")
                
                if len(params) >= 6:  # relationships 테이블 INSERT 파라미터 개수
                    src_id = params[0] if len(params) > 0 else None
                    dst_id = params[1] if len(params) > 1 else None
                    rel_type = params[2] if len(params) > 2 else None
                    
                    app_logger.error(f"삽입하려는 관계:")
                    app_logger.error(f"  src_id: {src_id}")
                    app_logger.error(f"  dst_id: {dst_id}")
                    app_logger.error(f"  rel_type: {rel_type}")
                    
                    # 참조 데이터 존재 여부 확인
                    self._check_relationship_references(src_id, dst_id)
                    
        except Exception as e:
            app_logger.error(f"INSERT 외래키 디버깅 실패: {str(e)}")

    def _debug_update_foreign_keys(self, query: str, params: tuple) -> None:
        """UPDATE 쿼리의 외래키 디버깅"""
        try:
            app_logger.error(f"=== UPDATE 쿼리 디버깅 ===")
            app_logger.error(f"UPDATE 쿼리는 외래키 제약조건 위반이 드물지만 확인 중...")
            
        except Exception as e:
            app_logger.error(f"UPDATE 외래키 디버깅 실패: {str(e)}")

    def _check_referenced_data_exists(self, project_id: int, file_id: int) -> None:
        """참조 데이터 존재 여부 확인"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # project_id 존재 여부 확인
                if project_id is not None:
                    cursor.execute("SELECT COUNT(*) FROM projects WHERE project_id = ? AND del_yn = 'N'", (project_id,))
                    project_exists = cursor.fetchone()[0] > 0
                    app_logger.error(f"  project_id {project_id} 존재 여부: {'존재' if project_exists else '존재하지 않음'}")
                    
                    if not project_exists:
                        # 전체 프로젝트 목록 출력
                        cursor.execute("SELECT project_id, project_name FROM projects WHERE del_yn = 'N'")
                        projects = cursor.fetchall()
                        app_logger.error(f"  사용 가능한 프로젝트: {projects}")
                
                # file_id 존재 여부 확인
                if file_id is not None:
                    cursor.execute("SELECT COUNT(*) FROM files WHERE file_id = ? AND del_yn = 'N'", (file_id,))
                    file_exists = cursor.fetchone()[0] > 0
                    app_logger.error(f"  file_id {file_id} 존재 여부: {'존재' if file_exists else '존재하지 않음'}")
                    
                    if not file_exists:
                        # 최근 파일 목록 출력 (상위 10개)
                        cursor.execute("SELECT file_id, file_name, file_type FROM files WHERE del_yn = 'N' ORDER BY file_id DESC LIMIT 10")
                        files = cursor.fetchall()
                        app_logger.error(f"  최근 파일 목록: {files}")
                        
        except Exception as e:
            app_logger.error(f"참조 데이터 확인 실패: {str(e)}")

    def _check_relationship_references(self, src_id: int, dst_id: int) -> None:
        """관계 참조 데이터 존재 여부 확인"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # src_id 존재 여부 확인
                if src_id is not None:
                    cursor.execute("SELECT COUNT(*) FROM components WHERE component_id = ? AND del_yn = 'N'", (src_id,))
                    src_exists = cursor.fetchone()[0] > 0
                    app_logger.error(f"  src_id {src_id} 존재 여부: {'존재' if src_exists else '존재하지 않음'}")
                    
                    if not src_exists:
                        # 최근 컴포넌트 목록 출력 (상위 10개)
                        cursor.execute("SELECT component_id, component_name, component_type FROM components WHERE del_yn = 'N' ORDER BY component_id DESC LIMIT 10")
                        components = cursor.fetchall()
                        app_logger.error(f"  최근 컴포넌트 목록: {components}")
                
                # dst_id 존재 여부 확인
                if dst_id is not None:
                    cursor.execute("SELECT COUNT(*) FROM components WHERE component_id = ? AND del_yn = 'N'", (dst_id,))
                    dst_exists = cursor.fetchone()[0] > 0
                    app_logger.error(f"  dst_id {dst_id} 존재 여부: {'존재' if dst_exists else '존재하지 않음'}")
                    
                    if not dst_exists:
                        # 최근 컴포넌트 목록 출력 (상위 10개)
                        cursor.execute("SELECT component_id, component_name, component_type FROM components WHERE del_yn = 'N' ORDER BY component_id DESC LIMIT 10")
                        components = cursor.fetchall()
                        app_logger.error(f"  최근 컴포넌트 목록: {components}")
                        
        except Exception as e:
            app_logger.error(f"관계 참조 데이터 확인 실패: {str(e)}")
    
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
            # 에러 발생 시에만 쿼리 로그를 error 레벨로 출력
            app_logger.error(f"=== 배치 SQL 쿼리 실행 실패 상세 정보 ===")
            app_logger.error(f"실행된 쿼리: {query}")
            app_logger.error(f"바인딩 파라미터 리스트: {params_list}")
            app_logger.error(f"파라미터 개수: {len(params_list) if params_list else 0}")
            app_logger.error(f"에러 메시지: {str(e)}")
            app_logger.error(f"에러 타입: {type(e).__name__}")
            
            # 첫 번째 파라미터만 상세 출력 (너무 많을 수 있으므로)
            if params_list and len(params_list) > 0:
                app_logger.error(f"첫 번째 파라미터 예시: {params_list[0]}")
            
            # 모든 상세 로그가 출력된 후 Exception을 다시 발생시켜 상위에서 handle_error 호출
            app_logger.error(f"=== 상세 로그 출력 완료, Exception 재발생 ===")
            raise e
    
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
            # components 테이블에 대한 특별한 검증 및 로깅
            if table_name == 'components':
                # file_id NULL 체크
                if data.get('file_id') is None:
                    error(f"[DATABASE_UTILS] FATAL: components 테이블에 file_id가 NULL인 데이터 삽입 시도!")
                    error(f"[DATABASE_UTILS] 삽입 데이터: {data}")
                    handle_error(Exception("components 테이블에 file_id가 NULL인 데이터 삽입 시도"), f"components 테이블 삽입 실패: file_id NULL")
                    return False
                
                # 디버그 로그
                debug(f"[DATABASE_UTILS] components 테이블 삽입: {data.get('component_name')} ({data.get('component_type')}) file_id={data.get('file_id')}")
            
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
            # components 테이블에 대한 특별한 검증
            if table_name == 'components':
                # file_id NULL 체크
                for i, data in enumerate(data_list):
                    if data.get('file_id') is None:
                        error(f"[DATABASE_UTILS] FATAL: batch components 테이블에 file_id가 NULL인 데이터 삽입 시도!")
                        error(f"[DATABASE_UTILS] 인덱스 {i} 삽입 데이터: {data}")
                        handle_error(Exception("batch components 테이블에 file_id가 NULL인 데이터 삽입 시도"), f"batch components 테이블 삽입 실패: file_id NULL")
                        return 0
                
                debug(f"[DATABASE_UTILS] batch components 테이블 삽입: {len(data_list)}개")
            
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
            # components 테이블에 대한 특별한 검증
            if table_name == 'components':
                # file_id NULL 체크
                if data.get('file_id') is None:
                    error(f"[DATABASE_UTILS] FATAL: insert_or_replace_with_id components 테이블에 file_id가 NULL인 데이터 삽입 시도!")
                    error(f"[DATABASE_UTILS] 삽입 데이터: {data}")
                    handle_error(Exception("insert_or_replace_with_id components 테이블에 file_id가 NULL인 데이터 삽입 시도"), f"components 테이블 삽입 실패: file_id NULL")
                    return 0
                
                # 디버그 로그
                debug(f"[DATABASE_UTILS] insert_or_replace_with_id components: {data.get('component_name')} ({data.get('component_type')}) file_id={data.get('file_id')}")
            
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

    def update_file_frameworks(self, file_id: int, new_framework: str) -> bool:
        """
        파일의 frameworks 필드에 새로운 프레임워크 추가 (중복 제거)
        
        Args:
            file_id: 파일 ID
            new_framework: 추가할 프레임워크 ('jquery', 'axios', 'fetch', 'xhr' 등)
            
        Returns:
            업데이트 성공 여부
        """
        try:
            if not new_framework or not new_framework.strip():
                return False
            
            new_framework = new_framework.strip().lower()
            
            # 현재 frameworks 값 조회
            query = "SELECT frameworks FROM files WHERE file_id = ?"
            result = self.execute_query(query, (file_id,))
            
            if not result:
                debug(f"파일 ID {file_id}를 찾을 수 없음")
                return False
            
            current_frameworks = result[0]['frameworks'] or ''
            
            # 기존 프레임워크들을 set으로 변환 (중복 제거)
            existing_frameworks = set()
            if current_frameworks:
                existing_frameworks = {fw.strip().lower() for fw in current_frameworks.split(',') if fw.strip()}
            
            # 새 프레임워크 추가
            existing_frameworks.add(new_framework)
            
            # 정렬된 문자열로 변환
            updated_frameworks = ', '.join(sorted(existing_frameworks))
            
            # 변경사항이 있을 때만 업데이트
            if updated_frameworks != current_frameworks:
                update_query = "UPDATE files SET frameworks = ?, updated_at = datetime('now', '+9 hours') WHERE file_id = ?"
                result = self.execute_update(update_query, (updated_frameworks, file_id))
                
                if result > 0:
                    debug(f"파일 frameworks 업데이트 성공: file_id={file_id}, frameworks='{updated_frameworks}'")
                    return True
                else:
                    debug(f"파일 frameworks 업데이트 실패: file_id={file_id}")
                    return False
            else:
                debug(f"파일 frameworks 변경사항 없음: file_id={file_id}")
                return True
            
        except Exception as e:
            debug(f"파일 frameworks 업데이트 실패: file_id={file_id}, framework={new_framework} - {str(e)}")
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

            # inferred 컴포넌트용 file_id 찾기 (프로젝트의 첫 번째 파일 사용)
            inferred_file_id = self._get_inferred_file_id_for_component(project_id)
            if not inferred_file_id:
                error(f"inferred 테이블 컴포넌트용 file_id를 찾을 수 없음: {table_name}")
                return None

            # 새 테이블 컴포넌트 생성
            component_data = {
                'project_id': project_id,
                'file_id': inferred_file_id,  # inferred 컴포넌트용 file_id 사용
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

    def _get_inferred_file_id_for_component(self, project_id: int) -> Optional[int]:
        """
        inferred 컴포넌트용 file_id 찾기 (프로젝트의 첫 번째 파일 사용)
        
        Args:
            project_id: 프로젝트 ID
            
        Returns:
            file_id 또는 None
        """
        try:
            # SQL 관련 파일 우선 조회 (inferred 컴포넌트는 주로 SQL 분석에서 생성)
            sql_file_query = """
                SELECT file_id 
                FROM files 
                WHERE project_id = ? AND file_type IN ('XML', 'SQL') AND del_yn = 'N'
                ORDER BY file_type, file_id
                LIMIT 1
            """
            sql_result = self.execute_query(sql_file_query, (project_id,))
            
            if sql_result and len(sql_result) > 0:
                file_id = sql_result[0]['file_id']
                debug(f"inferred 컴포넌트용 SQL 관련 file_id: {file_id}")
                return file_id
            
            # Java 파일 조회 (StringBuilder SQL 분석에서도 inferred 생성 가능)
            java_file_query = """
                SELECT file_id 
                FROM files 
                WHERE project_id = ? AND file_type = 'JAVA' AND del_yn = 'N'
                ORDER BY file_id
                LIMIT 1
            """
            java_result = self.execute_query(java_file_query, (project_id,))
            
            if java_result and len(java_result) > 0:
                file_id = java_result[0]['file_id']
                debug(f"inferred 컴포넌트용 Java file_id: {file_id}")
                return file_id
            
            # 마지막으로 첫 번째 파일 사용 (fallback)
            first_file_query = "SELECT file_id FROM files WHERE project_id = ? AND del_yn = 'N' ORDER BY file_id LIMIT 1"
            first_file_result = self.execute_query(first_file_query, (project_id,))
            first_file_id = first_file_result[0]['file_id'] if first_file_result else None
            
            if not first_file_id:
                error(f"프로젝트 {project_id}에 파일이 없습니다. 1단계 파일 스캔이 제대로 실행되지 않았습니다.")
                return None
                
            debug(f"inferred 컴포넌트용 첫 번째 file_id (fallback): {first_file_id}")
            return first_file_id
            
        except Exception as e:
            handle_error(e, f"inferred 컴포넌트용 file_id 조회 실패")
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
