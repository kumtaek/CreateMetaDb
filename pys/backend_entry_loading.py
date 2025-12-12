"""
Backend entry loading engine (clean UTF-8, no BOM)
"""

import os
import sqlite3
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

from util.logger import app_logger, handle_error
from util.database_utils import DatabaseUtils
from util.path_utils import PathUtils
from util.hash_utils import HashUtils
from util.api_naming import format_api_component_name, build_api_identity_key
from util.cache_utils import get_global_cache
from util.statistics_utils import get_global_collector
from parser.entry_analyzer_factory import get_global_factory
from parser.base_entry_analyzer import BackendEntryInfo, FileInfo
from util.base_loading_engine import BaseLoadingEngine


class BackendEntryLoadingEngine(BaseLoadingEngine):
    # Engine to analyze backend entries and persist components/relationships

    def __init__(self, project_name: str, conn: sqlite3.Connection):
        # Initialize engine with project and DB connection
        super().__init__(project_name, conn)
        self.db = self.db_utils  # Alias for compatibility
        # 프로젝트 ID 캐시 (파일 재스캔 시 upsert에 사용)
        self.project_id = self.db_utils.get_project_id(project_name)
        
        self.hash_utils = HashUtils()
        self.cache = get_global_cache()
        self.stats = get_global_collector()
        self.factory = get_global_factory()

        # self.project_source_path is already set by super()

        self.servlet_url_map = self._parse_web_xml()
        self.analyzers = self._load_analyzers()
        try:
            app_logger.debug("Analyzers: {}".format([a.get_framework_name() for a in self.analyzers]))
        except Exception:
            app_logger.debug("Analyzers loaded")
        app_logger.info(f"Backend entry loading initialized: {project_name}")

    def _load_analyzers(self) -> List:
        # Load analyzers from config
        try:
            analyzers = self.factory.load_analyzers_from_config(self.project_name, self.servlet_url_map)
            app_logger.debug("Analyzers loaded: {}".format(len(analyzers)))
            return analyzers
        except Exception as e:
            handle_error(e, f"Failed to load analyzers: {self.project_name}")
            return []

    def _build_project_file_path(self, dir_path: Optional[str], file_name: str) -> str:
        parts = ['projects', self.project_name]
        if dir_path:
            parts.append(dir_path)
        parts.append(file_name)
        return self.path_utils.join_path(*parts)

    def _compose_relative_file_path(self, dir_path: Optional[str], file_name: str) -> str:
        combined = os.path.join(dir_path, file_name) if dir_path else file_name
        return self.path_utils.normalize_path_separator(combined, 'unix')

    def _parse_web_xml(self) -> Dict[str, str]:
        # Parse web.xml files and build servlet URL mappings
        try:
            query = (
                "SELECT f.file_path, f.file_name FROM files f JOIN projects p ON f.project_id = p.project_id "
                "WHERE p.project_name = ? AND f.file_name = 'web.xml' AND f.del_yn = 'N'"
            )
            results = self.db.execute_query(query, (self.project_name,), conn=self.conn)
            if not results:
                app_logger.debug("web.xml file not found")
                return {}

            url_map: Dict[str, str] = {}
            for row in results:
                try:
                    relative_label = self._compose_relative_file_path(row['file_path'], row['file_name'])
                    web_xml_path = self._build_project_file_path(row['file_path'], row['file_name'])
                    web_xml_content = self._read_file_content(web_xml_path)
                    if not web_xml_content:
                        continue

                    root = ET.fromstring(web_xml_content)
                    servlet_mappings = {
                        elem.find('servlet-name').text: elem.find('url-pattern').text
                        for elem in root.findall('servlet-mapping')
                        if elem.find('servlet-name') is not None and elem.find('url-pattern') is not None
                    }
                    servlet_classes = {
                        elem.find('servlet-name').text: elem.find('servlet-class').text
                        for elem in root.findall('servlet')
                        if elem.find('servlet-name') is not None and elem.find('servlet-class') is not None
                    }

                    for name, url in servlet_mappings.items():
                        if name in servlet_classes:
                            url_map[servlet_classes[name]] = url
                except Exception as e:
                    handle_error(e, f"web.xml parsing failed: {relative_label}")
            return url_map
        except Exception as e:
            handle_error(e, "web.xml parsing encountered an error")
            return {}

    def execute_backend_entry_loading(self) -> bool:
        # Run full backend entry analysis and persist results
        try:
            app_logger.info("=== Backend entry analysis start ===")
            self.stats.start_analysis()

            java_files = self._get_java_files()
            if not java_files:
                # 여전히 자바 파일이 없으면 근본 원인을 알리며 중단 (스킵 대신 실패로 처리)
                handle_error(Exception("No Java files found to analyze."), "Backend entry loading")
                return False

            all_backend_entries = self._analyze_backend_entries(java_files)
            try:
                app_logger.info(
                    "Backend entry analysis done: {} entries".format(len(all_backend_entries))
                )
            except Exception:
                app_logger.info("Backend entry analysis done")

            self._save_results_to_db(all_backend_entries)
            app_logger.info("Backend entry components/relationships persisted to DB")

            # MyBatis mapper namespace+id indexing removed (mapper_map table not used)
            self._print_backend_entry_statistics()
            app_logger.info("=== Backend entry analysis done ===")
            return True
        except Exception as e:
            handle_error(e, f"Backend entry loading failed: {self.project_name}")
            return False
        finally:
            self.stats.end_analysis()

    def _get_java_files(self) -> List[FileInfo]:
        """
        Java 파일을 수집합니다.
        - 1차: files 테이블에서 JAVA 타입 조회
        - 2차: 조회 실패 시 실제 파일 시스템을 스캔하여 보완하고, 누락된 파일을 files 테이블에 upsert
        """
        query = (
            "SELECT f.file_id, f.file_path, f.file_name, f.file_type, f.hash_value "
            "FROM files f JOIN projects p ON f.project_id = p.project_id "
            "WHERE p.project_name = ? AND UPPER(f.file_type) = 'JAVA' AND f.del_yn = 'N'"
        )
        results = self.db.execute_query(query, (self.project_name,), conn=self.conn)

        java_files: List[FileInfo] = []
        for row in results or []:
            relative_path = self._compose_relative_file_path(row['file_path'], row['file_name'])
            full_path = self._build_project_file_path(row['file_path'], row['file_name'])
            content = self._read_file_content(full_path)
            if content:
                java_files.append(
                    FileInfo(
                        file_id=row['file_id'],
                        file_path=relative_path,
                        file_name=row['file_name'],
                        file_type=row['file_type'],
                        content=content,
                        hash_value=row['hash_value'],
                        line_count=len(content.splitlines()),
                    )
                )

        if java_files:
            return java_files

        # files 테이블에 JAVA가 없으면 직접 스캔 (INFERRED만 있는 경우 대비)
        app_logger.warning("files 테이블에 JAVA 타입이 없어 파일 시스템을 직접 스캔합니다.")
        scanned: List[FileInfo] = []
        for root, _, files in os.walk(self.project_source_path):
            for fname in files:
                if fname.lower().endswith('.java'):
                    full_path = os.path.join(root, fname)
                    content = self._read_file_content(full_path)
                    if not content:
                        continue
                    rel_path = os.path.relpath(full_path, self.project_source_path)
                    rel_unix = self.path_utils.normalize_path_separator(rel_path, 'unix')
                    file_hash = self.hash_utils.generate_md5(content)
                    file_info = FileInfo(
                        file_id=None,
                        file_path=os.path.dirname(rel_unix),
                        file_name=fname,
                        file_type='JAVA',
                        content=content,
                        hash_value=file_hash,
                        line_count=len(content.splitlines()),
                    )
                    scanned.append(file_info)

                    # files 테이블에 누락된 경우 upsert (프로젝트 ID 사용)
                    try:
                        proj_id = self.project_id or self.db.get_project_id(self.project_name)
                        file_data = {
                            'project_id': proj_id,
                            'file_path': os.path.dirname(rel_unix),
                            'file_name': fname,
                            'file_type': 'JAVA',
                            'hash_value': file_hash,
                            'line_count': file_info.line_count,
                            'frameworks': None,
                            'del_yn': 'N'
                        }
                        self.db.upsert('files', file_data, ['file_name', 'file_path', 'project_id'], self.conn)
                    except Exception as e:
                        handle_error(e, f"파일 스캔 후 files upsert 실패: {rel_unix}")

        return scanned

    def _read_file_content(self, file_path: str) -> Optional[str]:
        # Read file content as UTF-8
        try:
            normalized_path = self.path_utils.normalize_path(file_path)
            with open(normalized_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            handle_error(Exception(f"File not found: {file_path}"), "Read file failed")
            return None
        except Exception as e:
            handle_error(e, f"Read file failed: {file_path}")
            return None

    def _analyze_backend_entries(self, java_files: List[FileInfo]) -> List[BackendEntryInfo]:
        # Analyze each Java file using registered analyzers
        all_entries: List[BackendEntryInfo] = []
        for java_file in java_files:
            cached_entries = self.cache.get(java_file.hash_value)
            if cached_entries:
                all_entries.extend(cached_entries)
                continue

            file_entries = self._filter_and_analyze_file(java_file)
            if file_entries:
                self.cache.set(java_file.hash_value, file_entries)
                all_entries.extend(file_entries)
        return all_entries

    def _filter_and_analyze_file(self, java_file: FileInfo) -> List[BackendEntryInfo]:
        # Run analyzers on a single file; prefer Spring analyzer when matched
        file_entries: List[BackendEntryInfo] = []
        for analyzer in self.analyzers:
            full_path = self.path_utils.join_path("projects", self.project_name, java_file.file_path)
            if analyzer.is_target_file(full_path):
                entries = analyzer.analyze_backend_entry(java_file, self.stats)
                file_entries.extend(entries)
                if analyzer.get_framework_name() == 'spring' and entries:
                    break
        return file_entries

    def _save_results_to_db(self, entries: List[BackendEntryInfo]) -> None:
        # Persist API_URL components and relationships
        project_id = self.db.get_project_id(self.project_name, conn=self.conn)
        if not project_id:
            raise Exception("Project ID not found")

        components_to_insert: List[Dict[str, Any]] = []
        if entries:
            self._create_api_components(entries, project_id, components_to_insert)
            if components_to_insert:
                self.db.batch_insert_or_replace('components', components_to_insert, conn=self.conn)

        relationships_to_insert: List[Dict[str, Any]] = []
        if entries:
            self._create_api_relationships(entries, project_id, relationships_to_insert)
            if relationships_to_insert:
                self.db.batch_insert_or_replace('relationships', relationships_to_insert, conn=self.conn)

    def _create_api_url_component(self, entry: BackendEntryInfo, project_id: int) -> Optional[Dict[str, Any]]:
        # API_URL component creation
        url_pattern = (entry.url_pattern or '').strip()
        if (
            not url_pattern
            or url_pattern == '/'
            or url_pattern.startswith(':')
            or not url_pattern.startswith('/')
            or url_pattern.upper() in ['GET', 'POST', 'PUT', 'DELETE']
            or ':' in url_pattern
        ):
            return None

        component_name = format_api_component_name(entry.http_method, url_pattern, url_pattern)
        identity_key = build_api_identity_key(url_pattern, entry.http_method)
        if not component_name or not identity_key:
            return None

        hash_value = self.hash_utils.generate_content_hash(identity_key)

        existing = self.db.get_component_by_hash(project_id, 'API_URL', hash_value)
        if existing:
            existing_id = existing['component_id']
            if existing.get('component_name') != component_name:
                self.db.update_component_name(existing_id, component_name, conn=self.conn)
            # 프론트엔드에서 이미 file_id를 설정했을 수 있으므로 비어 있을 때만 백엔드 file_id 적용
            if existing.get('file_id') is None and entry.file_id is not None:
                self.db.update_component_file_id(existing_id, entry.file_id, conn=self.conn)
            return None
        return {
            'project_id': project_id,
            'file_id': entry.file_id,
            'component_name': component_name,
            'component_type': 'API_URL',
            'layer': 'API_ENTRY',
            'line_start': entry.line_start,
            'line_end': entry.line_end,
            'hash_value': hash_value,
            'del_yn': 'N',
            'has_error': entry.has_error,
            'error_message': entry.error_message,
            'parent_id': None,
        }

    def _create_api_components(self, entries: List[BackendEntryInfo], project_id: int, components_to_insert: List[Dict[str, Any]]):
        # Create API_URL components from analyzed entries
        for entry in entries:
            component = self._create_api_url_component(entry, project_id)
            if component:
                components_to_insert.append(component)

    def _find_existing_method(self, entry: BackendEntryInfo, project_id: int) -> Optional[int]:
        # 자바 파서는 component_name을 메서드명 단독으로 저장하므로 파일 기준으로 매칭
        candidates = []
        if entry.file_id is not None:
            query = (
                "SELECT c.component_id FROM components c WHERE c.project_id = ? "
                "AND c.component_type = 'METHOD' AND c.component_name = ? AND c.file_id = ? AND c.del_yn = 'N'"
            )
            candidates = self.db.execute_query(query, (project_id, entry.method_name, entry.file_id), conn=self.conn)
        if not candidates:
            query = (
                "SELECT c.component_id FROM components c WHERE c.project_id = ? "
                "AND c.component_type = 'METHOD' AND c.component_name = ? AND c.del_yn = 'N'"
            )
            candidates = self.db.execute_query(query, (project_id, entry.method_name), conn=self.conn)
        return candidates[0]['component_id'] if candidates else None

    def _get_methods_by_file(self, project_id: int, file_id: int) -> List[int]:
        """동일 파일 내 METHOD 컴포넌트 ID 리스트 반환"""
        try:
            query = (
                "SELECT component_id FROM components "
                "WHERE project_id = ? AND file_id = ? AND component_type = 'METHOD' AND del_yn = 'N'"
            )
            rows = self.db.execute_query(query, (project_id, file_id), conn=self.conn)
            return [row['component_id'] for row in rows] if rows else []
        except Exception as e:
            handle_error(e, "METHOD 컴포넌트 조회 실패")
            return []

    def _create_api_relationships(self, entries: List[BackendEntryInfo], project_id: int, relationships_to_insert: List[Dict[str, Any]]):
        for entry in entries:
            normalized_url = (entry.url_pattern or '').strip()
            identity_key = build_api_identity_key(normalized_url, entry.http_method)
            identity_hash = self.hash_utils.generate_content_hash(identity_key) if identity_key else None
            api_url_name = format_api_component_name(entry.http_method, normalized_url, normalized_url)

            api_url_id = None
            if identity_hash:
                api_url_id = self._get_component_id_by_hash(project_id, identity_hash, 'API_URL')
            if api_url_id is None and api_url_name:
                api_url_id = self._get_component_id_by_type(project_id, api_url_name, 'API_URL')

            method_id = self._find_existing_method(entry, project_id)
            if api_url_id and method_id:
                relationships_to_insert.append({
                    'src_id': api_url_id,
                    'dst_id': method_id,
                    'rel_type': 'CALL_METHOD',
                    'del_yn': 'N',
                })
            # 추가 방어: 메서드명을 못 찾으면 동일 파일의 METHOD 전부 연결 (메타DB 기반, 재파싱 없음)
            elif api_url_id and entry.file_id is not None:
                fallback_methods = self._get_methods_by_file(project_id, entry.file_id)
                for mid in fallback_methods:
                    relationships_to_insert.append({
                        'src_id': api_url_id,
                        'dst_id': mid,
                        'rel_type': 'CALL_METHOD',
                        'del_yn': 'N',
                    })


    def _get_component_id_by_type(self, project_id: int, component_name: str, component_type: str) -> Optional[int]:
        query = "SELECT component_id FROM components WHERE project_id = ? AND component_name = ? AND component_type = ? AND del_yn = 'N'"
        results = self.db.execute_query(query, (project_id, component_name, component_type), conn=self.conn)
        return results[0]['component_id'] if results else None

    def _get_component_id_by_hash(self, project_id: int, hash_value: str, component_type: str) -> Optional[int]:
        query = "SELECT component_id FROM components WHERE project_id = ? AND component_type = ? AND hash_value = ? AND del_yn = 'N'"
        results = self.db.execute_query(query, (project_id, component_type, hash_value), conn=self.conn)
        return results[0]['component_id'] if results else None

    def _print_backend_entry_statistics(self) -> None:
        self.stats.print_summary()


def execute_backend_entry_loading(project_name: str, conn: sqlite3.Connection) -> bool:
    try:
        engine = BackendEntryLoadingEngine(project_name, conn)
        return engine.execute_backend_entry_loading()
    except Exception as e:
        handle_error(e, f"Backend entry loading failed: {project_name}")
        return False
