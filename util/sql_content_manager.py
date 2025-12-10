"""
SQL Content Manager - 정제된 SQL 내용 관리 모듈
- gzip 압축을 사용한 SQL 내용 저장
- 프로젝트별 별도 데이터베이스 파일 사용
- 3단계 XML 파싱에서 정제된 SQL 내용 저장
"""

import gzip
import sqlite3
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from .logger import app_logger, handle_error
from .database_utils import DatabaseUtils
from .path_utils import PathUtils
from .file_utils import FileUtils


class SqlContentManager:
    """정제된 SQL 내용 관리 클래스"""

    def __init__(self, project_name: str, enable_brute_force_search: bool = True):
        """
        SqlContentManager 초기화

        Args:
            project_name: 프로젝트명
            enable_brute_force_search: 단순 문자열 매칭을 통한 테이블 검색 활성화 여부 (기본값: True)
        """
        self.project_name = project_name
        self.db_utils = None
        self.initialized = False
        self.enable_brute_force_search = enable_brute_force_search
        self._cached_table_names = None  # 테이블 목록 캐싱 (Lazy Loading)
        self._compiled_regex_patterns = None  # 정규식 패턴 사전 컴파일 캐싱
        self._cleaned_sql_cache = {}  # SQL 전처리 결과 캐싱 (쿼리 해시 -> 정제된 SQL)
        self.initialized = self._initialize_database()
    
    def _initialize_database(self) -> bool:
        """데이터베이스 초기화"""
        try:
            # 프로젝트명 유효성 검증 (버그 방지)
            from .validation_utils import ValidationUtils
            if not ValidationUtils.is_valid_project_name(self.project_name):
                from .logger import handle_error
                handle_error(Exception(f"잘못된 프로젝트명: {self.project_name}"), "SQL Content Manager 초기화 실패")
                return False
            
            # 프로젝트별 데이터베이스 경로 생성 (공통함수 사용)
            path_utils = PathUtils()
            db_path = path_utils.join_path("projects", self.project_name, "SqlContent.db")
            
            # 디렉토리 생성
            project_dir = path_utils.join_path("projects", self.project_name)
            os.makedirs(project_dir, exist_ok=True)
            
            # DatabaseUtils 초기화
            self.db_utils = DatabaseUtils(db_path)
            
            # 데이터베이스 연결
            if not self.db_utils.connect():
                return False
            
            # 스키마 생성 (공통함수 사용)
            schema_path = path_utils.join_path("database", "create_sql_content_db.sql")
            
            if not self.db_utils.create_schema(schema_path):
                app_logger.error("SQL Content 데이터베이스 스키마 생성 실패")
                return False
            
            app_logger.info(f"SQL Content 데이터베이스 초기화 완료: {db_path}")
            return True
            
        except Exception as e:
            handle_error(e, "SQL Content 데이터베이스 초기화 실패")
            return False
    
    def save_sql_content(self, sql_content: str, project_id: int, conn=None, **kwargs) -> bool:
        """
        정제된 SQL 내용 저장 및 Component 등록 (공통부, 단일 연결 지원)
        
        Args:
            sql_content: 정제된 SQL 내용
            project_id: 프로젝트 ID
            conn: 사용할 연결 객체 (None이면 새 연결 생성)
            **kwargs: 추가 메타데이터 (query_id, file_id, file_path 등)
            
        Returns:
            저장 성공 여부
        """
        try:
            # 파일 경로/파일명 정리: 경로에 파일명이 섞여 온 경우 분리
            file_path = kwargs.get('file_path')
            file_name = kwargs.get('file_name')
            if file_path or file_name:
                clean_path, clean_name = self._sanitize_file_path(file_path, file_name)
                kwargs['file_path'] = clean_path
                kwargs['file_name'] = clean_name

            # 프로젝트 정보 먼저 저장 (외래키 제약조건 대비)
            self._ensure_project_exists(project_id, kwargs.get('file_path', ''))

            # 파일 컨텍스트 강제 확인: file_id 누락 시 즉시 중단
            try:
                from util.file_context import get_file_context_manager
                ctx_mgr = get_file_context_manager()
                # 외부에서 file_id를 안 넘겼으면 전역 컨텍스트를 반드시 요구
                if not kwargs.get('file_id'):
                    ctx = ctx_mgr.require_current_file()
                    kwargs['file_id'] = ctx.file_id
                    kwargs['file_path'] = kwargs.get('file_path') or ctx.file_path
                    kwargs['file_name'] = kwargs.get('file_name') or ctx.file_name
            except Exception:
                # require_current_file가 이미 handle_error를 호출하므로 여기서는 재처리 없음
                return False
            
            # 1. Component 등록 (metadata.db, 단일 연결 사용)
            component_id = self._register_sql_component(
                sql_content=sql_content,
                project_id=project_id,
                file_id=kwargs.get('file_id'),
                query_id=kwargs.get('query_id', kwargs.get('component_name', '')),
                file_path=kwargs.get('file_path', ''),
                query_type=kwargs.get('query_type', 'SQL_QUERY'),
                conn=conn,
                file_name=kwargs.get('file_name')
            )
            
            if not component_id:
                app_logger.error(f"SQL Component 등록 실패: {kwargs.get('query_id', 'unknown')}")
                return False
            
            # 2. gzip 압축
            compressed_content = self._compress_content(sql_content)
            # 공통부: SQL → TABLE 즉시 처리(USE_TABLE)
            meta_conn_created = False
            try:
                # 디버깅 대상 쿼리/파일 필터 (config + 특정 파일/쿼리)
                debug_target_query_id = None
                try:
                    from util.config_loader import ConfigLoader  # 기존 공통 설정 로더 사용
                    config = ConfigLoader().load_target_source_config(self.project_name)
                    # 예: target_source_config.yaml에 debug: { query_id: "MY_QUERY_ID" } 형태로 정의
                    debug_cfg = (config or {}).get('debug', {})
                    debug_target_query_id = (debug_cfg.get('query_id') or "").strip()
                except Exception:
                    # 설정 로딩 실패 시 디버그 필터 미적용 (전체 쿼리 동일 동작)
                    debug_target_query_id = None

                debug_source_file = kwargs.get('debug_source_file') or kwargs.get('file_name')
                debug_source_path = kwargs.get('debug_source_path') or kwargs.get('file_path')
                debug_hint = kwargs.get('debug_hint')

                current_query_id = kwargs.get('query_id', kwargs.get('component_name', ''))
                is_debug_target = bool(debug_target_query_id) and current_query_id == debug_target_query_id
                # 특정 파일/쿼리 조합(UbcRgstTgtPopDbio.dbio + selectListUbcRgstTgt)도 디버깅 강제
                if (debug_source_file == 'UbcRgstTgtPopDbio.dbio' and current_query_id == 'selectListUbcRgstTgt') or debug_hint:
                    is_debug_target = True

                from parser.sql_parser import SqlParser
                parser = SqlParser()
                table_names = parser.extract_table_names(sql_content) or set()

                if is_debug_target:
                    preview = (sql_content or '')[:500]
                    app_logger.info(
                        f"[USE_TABLE][TARGET][SQL_RAW] query_id={current_query_id} "
                        f"len={len(sql_content or '')} preview={preview}"
                    )

                # 디버깅용: 파서 단계에서 추출된 테이블 로그
                if is_debug_target:
                    app_logger.info(
                        f"[USE_TABLE][TARGET][PARSE] query_id={current_query_id} "
                        f"component_id={component_id} file={debug_source_file} "
                        f"path={debug_source_path} tables={sorted(list(table_names)) if table_names else []}"
                    )
                elif app_logger.logger.isEnabledFor(logging.DEBUG):
                    app_logger.debug(
                        f"[USE_TABLE][PARSE] query_id={current_query_id} "
                        f"component_id={component_id} tables={len(table_names)}"
                    )
                
                # [NEW] 단순 문자열 매칭을 통한 테이블 검색 (누락 방지)
                if self.enable_brute_force_search:
                    try:
                        # 1. 전체 테이블 목록 로드 (Lazy Loading)
                        if self._cached_table_names is None:
                            self._cached_table_names = self._load_all_tables(project_id, conn)

                        if self._cached_table_names:
                            # 2. SQL 전처리 (주석 제거 등) - 캐싱 적용
                            cleaned_sql = self._remove_comments_simple(sql_content).upper()

                            # 디버깅용: 전처리된 SQL 일부 로그 (길이 제한)
                            if is_debug_target:
                                preview = cleaned_sql[:300]
                                app_logger.info(
                                    f"[USE_TABLE][TARGET][CLEANED_SQL] query_id={current_query_id} "
                                    f"len={len(cleaned_sql)} preview={preview}"
                                )
                            elif app_logger.logger.isEnabledFor(logging.DEBUG):
                                app_logger.debug(
                                    f"[USE_TABLE][CLEANED_SQL] query_id={current_query_id} "
                                    f"len={len(cleaned_sql)}"
                                )

                            # 3. 단순 매칭 검색 (사전 컴파일된 정규식 패턴 사용)
                            if self._compiled_regex_patterns:
                                # 정규식 패턴이 컴파일되어 있으면 재사용
                                for known_table in self._cached_table_names:
                                    # 이미 찾은 테이블은 건너뜀
                                    if known_table in table_names:
                                        continue

                                    # 사전 컴파일된 패턴으로 검색 (성능 개선)
                                    pattern = self._compiled_regex_patterns.get(known_table)
                                    if pattern and pattern.search(cleaned_sql):
                                        table_names.add(known_table)
                                        if is_debug_target:
                                            app_logger.info(f"[USE_TABLE][TARGET][BRUTE_FORCE] 단순 매칭으로 테이블 발견: {known_table} (in {current_query_id})")
                                        elif app_logger.logger.isEnabledFor(logging.DEBUG):
                                            app_logger.debug(f"[USE_TABLE][BRUTE_FORCE] 단순 매칭 발견: {known_table}")
                            else:
                                # 정규식 패턴이 없으면 기존 방식 사용 (Fallback)
                                import re
                                for known_table in self._cached_table_names:
                                    # 이미 찾은 테이블은 건너뜀
                                    if known_table in table_names:
                                        continue

                                    # 단어 경계로 검색 (부분 일치 방지)
                                    if re.search(r'\b' + re.escape(known_table) + r'\b', cleaned_sql):
                                        table_names.add(known_table)
                                        if is_debug_target:
                                            app_logger.info(f"[USE_TABLE][TARGET][BRUTE_FORCE] 단순 매칭으로 테이블 발견: {known_table} (in {current_query_id})")
                                        elif app_logger.logger.isEnabledFor(logging.DEBUG):
                                            app_logger.debug(f"[USE_TABLE][BRUTE_FORCE] 단순 매칭 발견: {known_table}")
                    except Exception as e:
                        # 단순 매칭 실패해도 기존 로직은 계속 수행
                        app_logger.warning(f"단순 테이블 매칭 중 오류 (무시): {e}")

                # 디버깅용: 파서 + 단순검색 이후 최종 테이블 목록 로그
                if is_debug_target:
                    app_logger.info(
                        f"[USE_TABLE][TARGET][FINAL] query_id={current_query_id} "
                        f"component_id={component_id} tables={sorted(list(table_names)) if table_names else []}"
                    )
                elif app_logger.logger.isEnabledFor(logging.DEBUG):
                    app_logger.debug(
                        f"[USE_TABLE][FINAL] query_id={current_query_id} "
                        f"component_id={component_id} tables={len(table_names)}"
                    )

                if is_debug_target and not table_names:
                    app_logger.info(f"[USE_TABLE][TARGET][EMPTY] query_id={current_query_id} file={debug_source_file} path={debug_source_path}")

                if table_names:
                    metadata_db_path = f'projects/{self.project_name}/metadata.db'
                    metadata_db_utils = DatabaseUtils(metadata_db_path)
                    meta_conn = conn if conn is not None else metadata_db_utils.get_persistent_connection()
                    meta_conn_created = conn is None
                    linked_tables = set()
                    for table_name in table_names:
                        try:
                            normalized_table = (table_name or '').strip().upper()
                            if not normalized_table or normalized_table in linked_tables:
                                continue
                            rows = metadata_db_utils.execute_query(
                                "SELECT component_id FROM components WHERE component_type='TABLE' AND component_name=? AND del_yn='N' LIMIT 1",
                                (normalized_table,),
                                conn=meta_conn,
                            )
                            if not rows:
                                # 디버깅용: 테이블은 찾았지만 TABLE 컴포넌트가 없는 경우
                                if is_debug_target and app_logger.logger.isEnabledFor(logging.DEBUG):
                                    app_logger.debug(
                                        f"[USE_TABLE][NO_COMPONENT] query_id={current_query_id} "
                                        f"component_id={component_id} table_name={normalized_table}"
                                    )
                                continue
                            table_component_id = rows[0]['component_id']
                            if table_component_id in linked_tables:
                                continue
                            linked_tables.add(table_component_id)
                            rel_data = {
                                'src_id': component_id,
                                'dst_id': table_component_id,
                                'rel_type': 'USE_TABLE',
                                'confidence': 1.0,
                                'has_error': 'N',
                                'error_message': None,
                                'del_yn': 'N'
                            }
                            metadata_db_utils.insert_or_replace_with_id('relationships', rel_data, conn=meta_conn)
                        except Exception as e:
                            handle_error(e, f"USE_TABLE 관계 생성 실패: component_id={component_id}, table={table_name}")
                else:
                    # 디버깅용: 어떤 방식으로도 테이블을 찾지 못한 경우
                    if is_debug_target and app_logger.logger.isEnabledFor(logging.DEBUG):
                        app_logger.debug(
                            f"[USE_TABLE][EMPTY] query_id={current_query_id} "
                            f"component_id={component_id} - 테이블 미검출"
                        )
            except Exception as e:
                handle_error(e, "USE_TABLE 즉시 생성 처리 실패")
            finally:
                try:
                    if meta_conn_created and meta_conn:
                        meta_conn.close()
                except Exception:
                    pass
            
            # 3. SQL Content 저장 (SqlContent.db)
            sql_content_data = {
                'project_id': project_id,
                'file_id': kwargs.get('file_id'),
                'component_id': component_id,  # 등록된 component_id 사용
                'sql_content_compressed': compressed_content,
                'file_path': kwargs.get('file_path'),
                'component_name': kwargs.get('query_id', kwargs.get('component_name', '')),
                'file_name': kwargs.get('file_name'),
                'hash_value': kwargs.get('hash_value'),
                'del_yn': 'N'
            }
            
            # 데이터베이스에 저장 (UPSERT 사용)
            success = self._upsert_sql_content(sql_content_data)
            
            if success:
                app_logger.debug(f"SQL Content + Component 저장 완료: {kwargs.get('query_id', 'unknown')} (component_id: {component_id})")
            
            return success
            
        except Exception as e:
            handle_error(e, "SQL 내용 저장 실패")
    
    def _sanitize_file_path(self, file_path: str, file_name: Optional[str]) -> (str, Optional[str]):
        """
        file_path에 파일명이 섞여 있는 경우 디렉터리/파일명으로 분리
        """
        path_utils = PathUtils()
        normalized_path = path_utils.normalize_path_separator(file_path or '', 'unix')
        # 파일명이 path 끝에 포함된 경우
        if file_name and normalized_path.endswith('/' + file_name):
            directory = os.path.dirname(normalized_path)
            return directory, file_name
        # file_name이 없고 path만 있는 경우 path에서 파일명 추출
        if normalized_path and not file_name:
            basename = os.path.basename(normalized_path)
            dirname = os.path.dirname(normalized_path)
            return dirname, basename if basename else None
        return normalized_path, file_name

    def _register_sql_component(self, sql_content: str, project_id: int, file_id: int, 
                               query_id: str, file_path: str, query_type: str, conn=None, file_name: str = None) -> Optional[int]:
        """
        SQL Component를 metadata.db의 components 테이블에 등록 (공통부)
        
        Args:
            sql_content: SQL 내용
            project_id: 프로젝트 ID
            file_id: 파일 ID
            query_id: 쿼리 ID
            file_path: 파일 경로
            query_type: 쿼리 타입 (SQL_SELECT, SQL_INSERT 등)
            
        Returns:
            등록된 component_id 또는 None
        """
        try:
            if not query_id:
                app_logger.error("query_id가 비어있음")
                return None
            
            # SQL 내용 기반으로 쿼리 타입 결정 (SQL 내용이 없으면 query_id에서 추론)
            if query_type == 'SQL_QUERY':
                query_type = self._determine_sql_component_type(sql_content, query_id)
            
            # metadata.db에 연결하여 Component 등록
            metadata_db_path = f'projects/{self.project_name}/metadata.db'
            if not os.path.exists(metadata_db_path):
                app_logger.error(f"metadata.db 파일이 존재하지 않음: {metadata_db_path}")
                return None
            
            from .database_utils import DatabaseUtils
            from .hash_utils import HashUtils
            
            # 전달받은 연결 사용 (단일 연결 보장)
            metadata_db_utils = DatabaseUtils(metadata_db_path)
            if conn is None:
                conn = metadata_db_utils.get_persistent_connection()
            
            # 데이터베이스 연결 설정은 트랜잭션 외부에서 이미 완료됨
            # 트랜잭션 내부에서는 PRAGMA 설정 변경 불가
            
            # file_id 유효성 검증 및 보정
            try:
                resolved_file_id = self._resolve_or_create_file_id(
                    metadata_db_utils=metadata_db_utils,
                    project_id=project_id,
                    file_id=file_id,
                    file_path=file_path,
                    file_name=file_name or (Path(file_path).name if file_path else None),
                    conn=conn
                )
                if not resolved_file_id:
                    app_logger.error(f"유효한 file_id를 찾을 수 없음: {file_path or 'N/A'}")
                    return None
                file_id = resolved_file_id
            except Exception as e:
                handle_error(e, f"file_id 유효성 검증 실패: {query_id}")
                return None
            
            # Component 데이터 구성
            component_data = {
                'project_id': project_id,
                'file_id': file_id,
                'component_type': query_type,
                'component_name': query_id,
                'parent_id': None,
                'layer': 'QUERY',  # SQL 컴포넌트는 QUERY layer
                'line_start': 1,  # SQL에서는 정확한 라인 번호 추출이 어려움
                'line_end': 1,
                'has_error': 'N',
                'error_message': None,
                'hash_value': HashUtils.generate_md5(sql_content),
                'del_yn': 'N'
            }
            
            # components 테이블에 저장 (재시도 로직)
            max_retries = 3
            component_id = None
            
            for attempt in range(max_retries):
                try:
                    # 단일 연결을 사용하여 컴포넌트 등록
                    component_id = metadata_db_utils.insert_or_replace_with_id('components', component_data, conn)
                    break
                except Exception as e:
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        app_logger.warning(f"데이터베이스 락 발생, 재시도 {attempt + 1}/{max_retries}: {e}")
                        import time
                        time.sleep(2)  # 2초 대기
                        continue
                    else:
                        handle_error(e, f"SQL Component 등록 실패 (재시도 {attempt + 1}/{max_retries}): {query_id}")
                        return None
            
            if component_id:
                app_logger.debug(f"SQL Component 등록 성공: {query_id} (ID: {component_id}, type: {query_type})")
            else:
                app_logger.error(f"SQL Component 등록 실패: {query_id}")
            
            return component_id
            
        except Exception as e:
            handle_error(e, f"SQL Component 등록 실패: {query_id}")
            return None
    
    def _resolve_or_create_file_id(self, metadata_db_utils: DatabaseUtils, project_id: int, file_id: Optional[int],
                                   file_path: str, file_name: Optional[str], conn=None) -> Optional[int]:
        """
        file_id가 비거나 유효하지 않을 때 파일 경로/이름으로 보정하거나 신규 파일 메타를 생성한다.
        크로스플랫폼 경로 정규화와 확장자 기반 타입 추출을 수행한다.
        """
        try:
            # 전역 파일 컨텍스트 우선 사용 (현재 처리 중인 원본 파일 정보)
            try:
                from util.file_context import get_file_context_manager
                ctx = get_file_context_manager().get_current()
                if not file_id and ctx.file_id:
                    file_id = ctx.file_id
                    file_path = file_path or ctx.file_path or ''
                    file_name = file_name or ctx.file_name
            except Exception:
                pass

            path_utils = PathUtils()
            # 1) 전달된 file_id가 유효하면 그대로 사용
            if file_id:
                rows = metadata_db_utils.execute_query(
                    "SELECT file_id FROM files WHERE file_id = ? AND project_id = ? AND del_yn='N'",
                    (file_id, project_id),
                    conn=conn
                )
                if rows:
                    return file_id
                app_logger.warning(f"file_id {file_id}가 존재하지 않음. 경로 기반으로 재탐색 시도")
            
            # 2) 경로/파일명 기반 조회 (전역 컨텍스트 포함)
            normalized_path = path_utils.normalize_path_separator(file_path or '', 'unix')
            target_file_name = file_name or (Path(normalized_path).name if normalized_path else None)
            target_dir = Path(normalized_path).parent.as_posix() if normalized_path else ''
            if target_file_name:
                lookup = metadata_db_utils.execute_query(
                    """
                    SELECT file_id FROM files 
                    WHERE project_id = ? AND file_path = ? AND file_name = ? AND del_yn='N' 
                    LIMIT 1
                    """,
                    (project_id, target_dir, target_file_name),
                    conn=conn
                )
                if lookup:
                    return lookup[0]['file_id']
            
            # 3) 여전히 없으면 에러로 중단 (INFERRED 파일 생성 금지)
            handle_error(Exception("파일 메타를 찾지 못했습니다"), f"file_id 보정 실패: {target_dir}/{target_file_name or 'UNKNOWN'}")
            return None
        except Exception as e:
            handle_error(e, f"file_id 보정 실패: {file_path}")
            return None
    
    def _determine_sql_component_type(self, sql_content: str, query_id: str = None) -> str:
        """
        SQL 내용을 기반으로 컴포넌트 타입 결정.
        SQL 내용이 없거나 타입을 결정할 수 없는 경우 query_id(메서드명)에서 추론.

        Args:
            sql_content: SQL 내용
            query_id: 쿼리 ID (메서드명 포함, 예: UserMapper.selectById)

        Returns:
            SQL 컴포넌트 타입 (SQL_SELECT, SQL_INSERT, SQL_UPDATE, SQL_DELETE, SQL_MERGE, SQL_QUERY)
        """
        sql_upper = (sql_content or '').upper().strip()

        # SQL 내용 기반 타입 결정
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

        # SQL 내용으로 타입을 결정할 수 없는 경우, query_id(메서드명)에서 추론
        if query_id:
            method_name = query_id.split('.')[-1] if '.' in query_id else query_id
            method_lower = method_name.lower()

            if method_lower.startswith(('select', 'find', 'get', 'count', 'exists', 'search', 'query', 'fetch', 'load', 'retrieve')):
                return 'SQL_SELECT'
            elif method_lower.startswith(('insert', 'create', 'add', 'save', 'register')):
                return 'SQL_INSERT'
            elif method_lower.startswith(('update', 'modify', 'change', 'edit', 'set')):
                return 'SQL_UPDATE'
            elif method_lower.startswith(('delete', 'remove', 'drop', 'truncate', 'erase')):
                return 'SQL_DELETE'
            elif method_lower.startswith('merge'):
                return 'SQL_MERGE'

        return 'SQL_QUERY'
    
    def _upsert_sql_content(self, sql_content_data: Dict[str, Any]) -> bool:
        """
        SQL Content를 DatabaseUtils의 upsert 메서드로 저장 (hash_value 기반 변동분 감지)
        
        Args:
            sql_content_data: SQL Content 데이터
            
        Returns:
            저장 성공 여부
        """
        try:
            project_id = sql_content_data.get('project_id')
            component_id = sql_content_data.get('component_id')
            hash_value = sql_content_data.get('hash_value', '-')
            # 파일 컨텍스트 강제 확인 (component_id 없이 저장하는 경우도 file_id 필요)
            try:
                from util.file_context import get_file_context_manager
                ctx = get_file_context_manager().require_current_file()
                if not sql_content_data.get('file_id'):
                    handle_error(Exception("file_id 누락"), "SQL Content 저장 실패: file_id 누락")
                    return False
            except Exception:
                return False
            
            # 기존 데이터 조회 (hash_value로 중복 체크)
            check_query = """
                SELECT project_id, file_id, component_id, hash_value, del_yn 
                FROM sql_contents 
                WHERE hash_value = ?
            """
            existing_results = self.db_utils.execute_query(check_query, (hash_value,))
            
            if existing_results:
                # hash_value가 이미 존재하면 스킵
                app_logger.debug(f"SQL Content 중복 (스킵): {sql_content_data.get('component_name', 'unknown')} (hash_value: {hash_value})")
                return True
            else:
                # 기존 데이터가 없으면 UPSERT 사용 (UNIQUE 제약조건 처리)
                unique_columns = ['component_name', 'file_id', 'project_id']
                success = self.db_utils.upsert('sql_contents', sql_content_data, unique_columns)
                
                if success:
                    app_logger.debug(f"SQL Content UPSERT 성공 (신규): {sql_content_data.get('component_name', 'unknown')}")
                else:
                    app_logger.error(f"SQL Content UPSERT 실패: {sql_content_data.get('component_name', 'unknown')}")
                
                return success is not None
                
        except Exception as e:
            handle_error(e, "SQL Content UPSERT 실패")
    
    def cleanup_deleted_sql_contents(self, project_id: int, current_component_ids: List[int]) -> int:
        """
        삭제된 SQL Content 정리 (현재 존재하지 않는 component_id의 SQL Content를 삭제)
        
        Args:
            project_id: 프로젝트 ID
            current_component_ids: 현재 존재하는 component_id 리스트
            
        Returns:
            삭제된 SQL Content 개수
        """
        try:
            if not current_component_ids:
                return 0
            
            # 삭제할 SQL Content 조회 (현재 component_id에 없는 것들)
            placeholders = ', '.join(['?' for _ in current_component_ids])
            select_query = f"""
                SELECT project_id, file_id, component_id, component_name 
                FROM sql_contents 
                WHERE project_id = ? AND component_id NOT IN ({placeholders}) AND del_yn = 'N'
            """
            
            with self.db_utils.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(select_query, [project_id] + current_component_ids)
                deleted_contents = cursor.fetchall()
                
                if deleted_contents:
                    # 삭제된 SQL Content를 del_yn = 'Y'로 업데이트
                    delete_query = f"""
                        UPDATE sql_contents 
                        SET del_yn = 'Y', updated_at = CURRENT_TIMESTAMP
                        WHERE project_id = ? AND component_id NOT IN ({placeholders}) AND del_yn = 'N'
                    """
                    cursor.execute(delete_query, [project_id] + current_component_ids)
                    conn.commit()
                    
                    deleted_count = len(deleted_contents)
                    app_logger.info(f"삭제된 SQL Content 정리 완료: {deleted_count}개")
                    
                    # 삭제된 SQL Content 목록 로그
                    for project_id, file_id, component_id, component_name in deleted_contents:
                        app_logger.debug(f"삭제된 SQL Content: {component_name} (project_id: {project_id}, file_id: {file_id}, component_id: {component_id})")
                    
                    return deleted_count
                else:
                    app_logger.debug("삭제할 SQL Content가 없습니다")
                    return 0
                    
        except Exception as e:
            app_logger.error(f"삭제된 SQL Content 정리 실패 (무시하고 계속 진행): {str(e)}")
            return 0
    
    def _ensure_project_exists(self, project_id: int, file_path: str) -> bool:
        """
        프로젝트 정보가 SqlContent.db에 존재하는지 확인하고 없으면 생성
        
        Args:
            project_id: 프로젝트 ID
            file_path: 파일 경로 (프로젝트 경로 추출용)
            
        Returns:
            성공 여부
        """
        try:
            # 프로젝트 정보 조회
            query = "SELECT project_id FROM projects WHERE project_id = ?"
            results = self.db_utils.execute_query(query, (project_id,))
            
            if not results:
                # 프로젝트 정보가 없으면 생성
                project_path = os.path.dirname(file_path) if file_path else f"projects/{self.project_name}"
                project_data = {
                    'project_id': project_id,
                    'project_name': self.project_name,
                    'project_path': project_path,
                    'del_yn': 'N'
                }
                self.db_utils.insert_or_replace('projects', project_data)
                app_logger.debug(f"SqlContent.db에 프로젝트 정보 생성: {self.project_name} (ID: {project_id})")
            
            return True
            
        except Exception as e:
            app_logger.warning(f"프로젝트 정보 확인/생성 실패: {str(e)}")
            return False
    
    def _compress_content(self, sql_content: str) -> bytes:
        """SQL 내용을 gzip으로 압축"""
        try:
            return gzip.compress(sql_content.encode('utf-8'))
        except Exception as e:
            app_logger.error(f"SQL 내용 압축 실패 (무시하고 계속 진행): {str(e)}")
            return sql_content.encode('utf-8')
    
    def _decompress_content(self, compressed_data: bytes) -> str:
        """압축된 SQL 내용을 gzip으로 압축 해제"""
        try:
            return gzip.decompress(compressed_data).decode('utf-8')
        except Exception as e:
            app_logger.error(f"SQL 내용 압축 해제 실패 (무시하고 계속 진행): {str(e)}")
            return compressed_data.decode('utf-8', errors='replace')
    
    def get_sql_contents(self, project_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        SQL 내용 목록 조회
        
        Args:
            project_id: 프로젝트 ID
            limit: 조회 개수 제한
            
        Returns:
            SQL 내용 목록
        """
        try:
            query = """
            SELECT 
                project_id, file_id, component_id, file_path, component_name,
                hash_value, created_at, sql_content_compressed
            FROM sql_contents 
            WHERE project_id = ? AND del_yn = 'N'
            ORDER BY created_at DESC
            LIMIT ?
            """
            
            results = self.db_utils.execute_query(query, (project_id, limit))
            
            # 압축 해제
            sql_contents = []
            for row in results:
                content_data = {
                    'project_id': row[0],
                    'file_id': row[1],
                    'component_id': row[2],
                    'file_path': row[3],
                    'component_name': row[4],
                    'hash_value': row[5],
                    'created_at': row[6],
                    'sql_content': self._decompress_content(row[7])
                }
                sql_contents.append(content_data)
            
            return sql_contents
            
        except Exception as e:
            app_logger.error(f"SQL 내용 조회 실패 (무시하고 계속 진행): {str(e)}")
            return []
    
    def get_stats(self, project_id: int) -> Dict[str, Any]:
        """
        SQL 내용 통계 조회
        
        Args:
            project_id: 프로젝트 ID
            
        Returns:
            통계 정보
        """
        try:
            # 전체 통계
            total_query = """
            SELECT 
                COUNT(*) as total_sql_contents,
                SUM(LENGTH(sql_content_compressed)) as total_compressed_size,
                AVG(LENGTH(sql_content_compressed)) as avg_compressed_size,
                MAX(LENGTH(sql_content_compressed)) as max_compressed_size,
                MIN(LENGTH(sql_content_compressed)) as min_compressed_size
            FROM sql_contents 
            WHERE project_id = ? AND del_yn = 'N'
            """
            
            total_stats = self.db_utils.execute_query(total_query, (project_id,))
            
            # 파일별 통계
            file_query = """
            SELECT 
                file_path, file_name,
                COUNT(*) as total_sql_contents,
                SUM(LENGTH(sql_content_compressed)) as total_compressed_size,
                AVG(LENGTH(sql_content_compressed)) as avg_compressed_size
            FROM sql_contents 
            WHERE project_id = ? AND del_yn = 'N'
            GROUP BY file_path, file_name
            ORDER BY total_compressed_size DESC
            LIMIT 10
            """
            
            file_stats = self.db_utils.execute_query(file_query, (project_id,))
            
            # 쿼리 타입별 통계
            type_query = """
            SELECT 
                COUNT(*) as total_sql_contents,
                SUM(LENGTH(sql_content_compressed)) as total_compressed_size,
                AVG(LENGTH(sql_content_compressed)) as avg_compressed_size
            FROM sql_contents 
            WHERE project_id = ? AND del_yn = 'N'
            ORDER BY total_compressed_size DESC
            """
            
            type_stats = self.db_utils.execute_query(type_query, (project_id,))
            
            return {
                'total_stats': total_stats[0] if total_stats else None,
                'file_stats': file_stats,
                'type_stats': type_stats
            }
            
        except Exception as e:
            app_logger.error(f"SQL 내용 통계 조회 실패 (무시하고 계속 진행): {str(e)}")
            return {}
    
    def close(self):
        """데이터베이스 연결 해제"""
        if self.db_utils:
            self.db_utils.disconnect()
            app_logger.info("SQL Content 데이터베이스 연결 해제")

    def _load_all_tables(self, project_id: int, conn=None) -> set:
        """
        프로젝트의 모든 테이블 목록을 로드 (캐싱용)

        Args:
            project_id: 프로젝트 ID
            conn: DB 연결 객체

        Returns:
            테이블명 집합 (대문자)
        """
        try:
            metadata_db_path = f'projects/{self.project_name}/metadata.db'
            metadata_db_utils = DatabaseUtils(metadata_db_path)

            # 연결 관리: 전달받은 conn이 있으면 사용, 없으면 임시 연결 생성
            temp_conn = None
            use_conn = conn

            if use_conn is None:
                temp_conn = metadata_db_utils.get_connection()
                use_conn = temp_conn

            try:
                # 테이블 목록 조회 (Owner 무시, 테이블명만)
                query = "SELECT table_name FROM tables WHERE project_id = ? AND del_yn = 'N'"
                rows = metadata_db_utils.execute_query(query, (project_id,), conn=use_conn)

                table_names = set()
                if rows:
                    for row in rows:
                        t_name = row.get('table_name')
                        if t_name:
                            table_names.add(t_name.upper())

                app_logger.info(f"전체 테이블 목록 로드 완료: {len(table_names)}개")

                # 정규식 패턴 사전 컴파일 (성능 최적화)
                self._compile_regex_patterns(table_names)

                return table_names

            finally:
                if temp_conn:
                    temp_conn.close()

        except Exception as e:
            app_logger.error(f"전체 테이블 목록 로드 실패: {e}")
            return set()

    def _compile_regex_patterns(self, table_names: set):
        """
        테이블명에 대한 정규식 패턴을 사전 컴파일 (성능 최적화)

        Args:
            table_names: 테이블명 집합
        """
        try:
            import re
            self._compiled_regex_patterns = {}

            for table_name in table_names:
                # 단어 경계로 검색하는 패턴 사전 컴파일
                pattern = re.compile(r'\b' + re.escape(table_name) + r'\b')
                self._compiled_regex_patterns[table_name] = pattern

            app_logger.info(f"정규식 패턴 사전 컴파일 완료: {len(self._compiled_regex_patterns)}개")
        except Exception as e:
            app_logger.warning(f"정규식 패턴 컴파일 실패 (무시): {e}")
            self._compiled_regex_patterns = None

    def _remove_comments_simple(self, sql: str) -> str:
        """
        SQL에서 주석 및 태그를 제거하는 간단한 전처리 (캐싱 적용)

        Args:
            sql: 원본 SQL

        Returns:
            정제된 SQL
        """
        try:
            import hashlib

            # SQL 해시 생성 (캐시 키)
            sql_hash = hashlib.md5(sql.encode('utf-8')).hexdigest()

            # 캐시 확인
            if sql_hash in self._cleaned_sql_cache:
                return self._cleaned_sql_cache[sql_hash]

            import re
            # 1. MyBatis 태그 제거 (간단히 태그만 제거하고 내용은 남김, 혹은 공백 처리)
            # 여기서는 태그 자체를 공백으로 치환하여 단어 경계 유지
            cleaned = re.sub(r'<[^>]+>', ' ', sql)

            # 2. 라인 주석 제거 (-- ... 한 줄)
            cleaned = re.sub(r'--[^\r\n]*', '', cleaned)
            cleaned = re.sub(r'//[^\r\n]*', '', cleaned)

            # 3. 블록 주석 제거 (/* ... */)
            cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)

            # 4. 공백 정규화
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()

            # 캐시 저장 (메모리 제한: 최대 1만 개)
            if len(self._cleaned_sql_cache) < 10000:
                self._cleaned_sql_cache[sql_hash] = cleaned

            return cleaned
        except Exception:
            return sql
