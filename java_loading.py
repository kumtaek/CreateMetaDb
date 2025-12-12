"""Simple Java loader (UTF-8, no BOM) — stage 4 components
- Extract classes/methods and persist to components
- Analyze SQL strings in Java and save SqlContent + relationships
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional
from util import (
    DatabaseUtils, info, warning, debug, handle_error,
    get_project_source_path, get_project_metadata_db_path, HashUtils
)
from util.file_context import get_file_context_manager
from parser.simple_java_parser import SimpleJavaParser
from parser.simple_query_analyzer import SimpleQueryAnalyzer
from util.sql_content_manager import SqlContentManager
from util.path_utils import PathUtils
from util.base_loading_engine import BaseLoadingEngine

class SimpleJavaLoader(BaseLoadingEngine):
    """Simple Java file loader"""

    def __init__(self, project_name: str, conn: sqlite3.Connection, use_compression: Optional[bool] = None):
        """Initialize loader"""
        super().__init__(project_name, conn)

        self.java_parser = SimpleJavaParser()
        self.simple_query_analyzer = SimpleQueryAnalyzer(project_name, self.conn)

        # 설정 파일에서 enable_brute_force_table_search 옵션 읽기
        from util.config_utils import ConfigUtils
        from util.logger import app_logger
        config_utils = ConfigUtils()
        config = config_utils.load_target_source_config(project_name)
        enable_brute_force = True  # 기본값
        if config:
            enable_brute_force = config.get('sql_analysis', {}).get('enable_brute_force_table_search', True)
            app_logger.info(f"단순 테이블 매칭 설정: {enable_brute_force}")

        from util import get_sql_compress
        resolved_compress = use_compression if use_compression is not None else get_sql_compress()
        self.sql_content_manager = SqlContentManager(project_name, enable_brute_force_search=enable_brute_force, use_compression=resolved_compress)
        # 파일 컨텍스트 (현재 처리 중인 파일/컴포넌트 정보 전역 보관)
        self.file_context = get_file_context_manager()

        self.stats = {
            'java_files_processed': 0,
            'classes_extracted': 0,
            'methods_extracted': 0,
            'sql_queries_extracted': 0,
            'relationships_created': 0,
            'errors': 0
        }
        # JPA Entity-Table 매핑 딕셔너리 (전역 수집)
        self.entity_table_mapping = {}

    def execute_java_loading(self, project_id: int) -> bool:
        """Execute Java loading (pipeline-integrated)"""
        try:
            info("Java loading start (simple)")
            self.collected_sql_queries = []

            java_files = []
            for root, _, files in os.walk(self.project_source_path):
                for file in files:
                    if file.endswith('.java'):
                        java_files.append(os.path.join(root, file))

            if not java_files:
                handle_error(Exception("No Java files found"), "No Java files found to analyze.")

            info(f"Java files to process: {len(java_files)}")

            for java_file in java_files:
                try:
                    self._process_java_file(java_file, project_id)
                    self.stats['java_files_processed'] += 1
                except Exception as e:
                    handle_error(e, f"Java file processing failed: {java_file}")
                    raise

                    self.stats['errors'] += 1

            if self.collected_sql_queries:
                # Entity-Table 매핑을 쿼리 분석기에 설정 (JPQL 변환용)
                if self.entity_table_mapping:
                    info(f"Entity-Table 매핑 적용: {len(self.entity_table_mapping)}개")
                    self.simple_query_analyzer.set_entity_table_mapping(self.entity_table_mapping)
                self._process_collected_queries(project_id)

            info("=== Java loading done ===")
            return True
        except Exception as e:
            handle_error(e, "Java loading run failed")
            return False

    def _process_java_file(self, java_file: str, project_id: int):
        """Process a single Java file"""
        file_id = self._get_file_id(java_file)
        if not file_id:
            handle_error(Exception("File ID not found"), f"File ID not found: {java_file}")
            return

        # 파일 컨텍스트 스택에 현재 파일 정보 저장 (전역 추적)
        path_utils = PathUtils()
        rel = path_utils.get_relative_path(java_file, self.project_source_path)
        rel_unix = path_utils.normalize_path_separator(rel, 'unix')
        file_dir = os.path.dirname(rel_unix) if rel_unix else ''
        if file_dir in ('', '.'):
            file_dir = ''
        else:
            file_dir = path_utils.normalize_path_separator(file_dir, 'unix')
        file_name = os.path.basename(rel_unix)

        self.file_context.push(
            project_name=self.project_name,
            project_id=project_id,
            file_id=file_id,
            file_path=file_dir,
            file_name=file_name,
            file_type='JAVA',
            source_type='JAVA',
            stage='Java'
        )

        try:
            try:
                debug(f"Parsing Java file: {java_file}")
                parse_result = self.java_parser.parse_java_file(java_file)
                debug(f"parse_result keys: {list(parse_result.keys())}")
                debug(f"classes in parse_result: {parse_result.get('classes')}")
                if not parse_result.get('classes'):
                    # Enum 파일인지 확인
                    with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if 'enum ' in content:
                            # Enum은 연관관계가 없어서 처리하지 않음
                            debug(f"Enum file ignored (no relationships): {java_file}")
                        else:
                            warning(f"No classes extracted: {java_file}")
            except Exception as e:
                handle_error(e, f"Java file parse failed: {java_file}")
                return

            class_id_map = {}
            for cls in parse_result.get('classes', []):
                class_id = self._upsert_class(cls, project_id, file_id)
                if class_id:
                    class_id_map[cls['name']] = class_id
                    self.stats['classes_extracted'] += 1

            # Entity-Table 매핑 수집 (JPQL 변환용)
            file_entity_mapping = parse_result.get('entity_table_mapping', {})
            if file_entity_mapping:
                self.entity_table_mapping.update(file_entity_mapping)
                debug(f"Entity-Table 매핑 수집: {file_entity_mapping}")

            for method in parse_result.get('methods', []):
                parent_class_id = class_id_map.get(method['class'])
                method_comp = {
                    'project_id': project_id, 'file_id': file_id,
                    'component_name': method['name'],
                    'component_type': 'METHOD', 'parent_id': parent_class_id,
                    'hash_value': HashUtils().generate_content_hash(method['name'])
                }
                if self._upsert_component(method_comp):
                    self.stats['methods_extracted'] += 1

            # Query extraction & collection
            try:
                query_analysis = self.simple_query_analyzer.analyze_java_file(java_file, file_id)
                if query_analysis and (query_analysis.get('java_queries') or query_analysis.get('jpa_queries')):
                    all_queries = query_analysis['java_queries'] + query_analysis['jpa_queries']
                    self.stats['sql_queries_extracted'] += len(all_queries)
                    for query in all_queries:
                        method_name = query.get('method_name', 'unknown')
                        base_query_id = query.get('query_id') or query.get('variable_name') or method_name
                        # 동일 파일 내 중복 query_id 방지를 위해 메서드명으로 네임스페이스 부여
                        if not hasattr(self, "_query_ids_seen"):
                            self._query_ids_seen = {}
                        file_key = file_id
                        seen_set = self._query_ids_seen.setdefault(file_key, set())
                        query_id = base_query_id
                        if query_id in seen_set:
                            query_id = f"{method_name}.{base_query_id}"
                        # 그래도 충돌 시 숫자 접미사 부여
                        suffix = 2
                        while query_id in seen_set:
                            query_id = f"{method_name}.{base_query_id}_{suffix}"
                            suffix += 1
                        seen_set.add(query_id)
                        # ✅ file_path, file_name을 수집 시점에 포함 (이미 계산된 값 사용)
                        self.collected_sql_queries.append({
                            'sql_content': query.get('sql_content', ''), 
                            'query_id': query_id,
                            'query_type': query.get('query_type', 'SQL_QUERY'),
                            'file_id': file_id, 
                            'project_id': project_id,
                            'file_path': file_dir,    # ✅ 추가: 이미 계산된 file_path
                            'file_name': file_name    # ✅ 추가: 이미 계산된 file_name
                        })
            except Exception as e:
                handle_error(e, f"Java query analysis failed: {java_file}")

            # MyBatis FQMN 쿼리 추출 및 upsert 처리
            try:
                from parser.java_parser import JavaParser
                java_parser = JavaParser()
                
                with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                    java_content = f.read()
                
                # MyBatis FQMN 쿼리 추출
                mybatis_fqmn_queries = java_parser._extract_mybatis_fqmn_queries(java_content, java_file)
                
                if mybatis_fqmn_queries:
                    debug(f"MyBatis FQMN 쿼리 {len(mybatis_fqmn_queries)}개 추출: {java_file}")
                    
                    for query in mybatis_fqmn_queries:
                        fqmn = query['query_id']  # com.example.mapper.UserMapper.selectUserById
                        
                        # 기존 SQL 컴포넌트 확인 (XML에서 이미 등록되었을 수 있음)
                        existing_component = self.db_utils.execute_query(
                            "SELECT component_id FROM components WHERE component_name = ? AND project_id = ? AND del_yn = 'N'",
                            (fqmn, project_id)
                        )
                        
                        if existing_component:
                            # XML에서 이미 등록됨 → 관계만 생성
                            debug(f"기존 SQL 컴포넌트 발견: {fqmn}")
                        else:
                            # XML에서 등록되지 않음 → INFERRED 쿼리로 등록
                            # 메서드명에서 SQL 타입 추론
                            inferred_type = self._infer_sql_type_from_method_name(fqmn)
                            sql_component = {
                                'project_id': project_id,
                                'file_id': file_id,
                                'component_name': fqmn,
                                'component_type': inferred_type,
                                'parent_id': None,
                                'hash_value': HashUtils().generate_content_hash(fqmn)
                            }
                            
                            if self._upsert_component(sql_component):
                                self.stats['sql_queries_extracted'] += 1
                                debug(f"INFERRED 쿼리 컴포넌트 등록: {fqmn}")
                                
                                # SqlContent.db에도 저장
                                self.collected_sql_queries.append({
                                    'sql_content': query['sql_content'],
                                    'query_id': fqmn,
                                    'file_id': file_id,
                                    'project_id': project_id,
                                    'file_path': file_dir,    # ✅ 추가
                                    'file_name': file_name    # ✅ 추가
                                })
                            
            except Exception as e:
                handle_error(e, f"MyBatis FQMN 처리 실패: {java_file}")
        finally:
            # 항상 컨텍스트 복원
            self.file_context.pop()

    def _process_collected_queries(self, project_id: int):
        """Process all collected SQL queries by saving them to SqlContent.db"""
        info(f"Collected SQL queries: {len(self.collected_sql_queries)} → saving to SqlContent.db")
        if not self.sql_content_manager or not self.sql_content_manager.initialized:
            handle_error(Exception("SQL Content Manager not initialized"), "SQL Content Manager가 초기화되지 않아 쿼리 처리를 건너뜁니다.")

        # Entity-Table 매핑이 있으면 저장 전에 JPQL 정규화 적용
        if self.entity_table_mapping:
            jpql_normalized_count = 0
            for query_data in self.collected_sql_queries:
                sql_content = query_data.get('sql_content', '')
                if sql_content:
                    normalized = self.simple_query_analyzer._normalize_jpql(sql_content)
                    if normalized != sql_content:
                        query_data['sql_content'] = normalized
                        jpql_normalized_count += 1
            if jpql_normalized_count > 0:
                info(f"JPQL 정규화 적용: {jpql_normalized_count}개 쿼리")

        try:
            for query_data in self.collected_sql_queries:
                # 파일 컨텍스트 세팅: 저장 대상 쿼리가 속한 파일 기준
                file_id = query_data.get('file_id')
                file_path = ''
                file_name = ''
                if file_id:
                    rows = self.db_utils.execute_query(
                        "SELECT file_path, file_name FROM files WHERE file_id = ? AND del_yn='N'",
                        (file_id,),
                        conn=self.conn
                    )
                    if rows:
                        file_path = rows[0].get('file_path', '') or ''
                        file_name = rows[0].get('file_name', '') or ''
                # file_id가 없으면 전역 컨텍스트가 누락된 것이므로 즉시 중단
                else:
                    handle_error(Exception("file_id missing in collected query"), "SQL content save failed: file_id 누락")
                    return
                # 컨텍스트 push (없으면 저장 시 require_current_file에서 중단)
                self.file_context.push(
                    project_name=self.project_name,
                    project_id=project_id,
                    file_id=file_id,
                    file_path=file_path,
                    file_name=file_name,
                    file_type='JAVA',
                    source_type='JAVA',
                    stage='Java-SQLSave'
                )
                try:
                    self.sql_content_manager.save_sql_content(conn=self.conn, **query_data)
                finally:
                    self.file_context.pop()
        except Exception as e:
            handle_error(e, "SQL content save failed")

        try:
            from util.common_sql_processor import CommonSqlAnalyzer
            common_processor = CommonSqlAnalyzer(self.project_name, self.sql_content_manager.use_compression)
            result = common_processor.analyze_all_queries()
            self.stats['relationships_created'] += result.get('statistics', {}).get('joins_found', 0)
            info(f"Created JOIN relationships: {result.get('statistics', {}).get('joins_found', 0)}")
        except Exception as e:
            handle_error(e, "Common SQL Processor analyze failed")

    def _get_file_id(self, file_path: str) -> Optional[int]:
        """Lookup file_id by (file_path + file_name)"""
        try:
            rel = os.path.relpath(file_path, self.project_source_path)
            rel_unix = PathUtils().normalize_path_separator(rel, 'unix')
            file_dir = os.path.dirname(rel_unix) if rel_unix else ''
            if file_dir in ('', '.'):
                file_dir = ''
            file_name = os.path.basename(rel_unix)
            query = "SELECT file_id FROM files WHERE file_path = ? AND file_name = ? AND project_id = (SELECT project_id FROM projects WHERE project_name = ?)"
            result = self.db_utils.execute_query(query, (file_dir, file_name, self.project_name), conn=self.conn)
            return result[0]['file_id'] if result else None
        except Exception as e:
            handle_error(e, f"File ID lookup failed: {file_path}")

    def _upsert_component(self, comp_data: Dict) -> Optional[int]:
        """UPSERT component"""
        try:
            return self.db_utils.insert_or_replace_with_id('components', comp_data, conn=self.conn)
        except Exception as e:
            handle_error(e, f"Component UPSERT failed: {comp_data}")
            return None

    def _upsert_class(self, cls_data: dict, project_id: int, file_id: int) -> Optional[int]:
        """UPSERT into classes table"""
        try:
            data = {
                'project_id': project_id,
                'file_id': file_id,
                'class_name': cls_data['name'],
                'hash_value': HashUtils().generate_content_hash(f"{cls_data['name']}{cls_data['line']}")
            }
            return self.db_utils.insert_or_replace_with_id('classes', data, conn=self.conn)
        except Exception as e:
            handle_error(e, f"Class UPSERT failed: {cls_data}")
            return None

    def _infer_sql_type_from_method_name(self, fqmn: str) -> str:
        """
        MyBatis Mapper 메서드명(FQMN)에서 SQL 타입을 추론.

        Args:
            fqmn: Fully Qualified Method Name (예: UserMapper.selectById)

        Returns:
            추론된 SQL 타입 (SQL_SELECT, SQL_INSERT, SQL_UPDATE, SQL_DELETE)
            추론 불가 시 SQL_QUERY 반환
        """
        # FQMN에서 메서드명 추출 (예: UserMapper.selectById -> selectById)
        method_name = fqmn.split('.')[-1] if '.' in fqmn else fqmn
        method_lower = method_name.lower()

        # 메서드명 접두어 기반 SQL 타입 추론
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
        else:
            # 추론 불가 시 기본값
            return 'SQL_QUERY'

def load_java_files_simple(project_name: str, project_id: int, conn: sqlite3.Connection, use_compression: Optional[bool] = None) -> tuple[bool, dict]:
    """Run simple Java loading"""
    loader = SimpleJavaLoader(project_name, conn, use_compression)
    success = loader.execute_java_loading(project_id)
    return success, loader.stats
