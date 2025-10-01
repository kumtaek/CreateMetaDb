"""Backend entry loading engine (UTF-8)"""

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


class BackendEntryLoadingEngine:
    """獄쏄퉮肉??筌욊쑴????브쑴苑?筌롫뗄???遺우춭"""
    
    def __init__(self, project_name: str, conn: sqlite3.Connection):
        """
        ?遺우춭 ?λ뜃由??
        
        Args:
            project_name: ?袁⑥쨮??븍뱜筌?
            conn: ?紐??癒?퐣 雅뚯눘????怨쀬뵠?怨뺤퓢??곷뮞 ?怨뚭퍙 揶쏆빘猿?
        """
        self.project_name = project_name
        self.conn = conn
        self.path_utils = PathUtils()
        self.hash_utils = HashUtils()
        self.cache = get_global_cache()
        self.stats = get_global_collector()
        self.factory = get_global_factory()
        
        self.db = DatabaseUtils(self.path_utils.get_project_metadata_db_path(project_name))
        self.project_source_path = self.path_utils.get_project_source_path(project_name)
        
        self.servlet_url_map = self._parse_web_xml()
        self.analyzers = self._load_analyzers()
        try:
            app_logger.debug("Analyzers: {}".format([analyzer.get_framework_name() for analyzer in self.analyzers]))
        except Exception:
            app_logger.debug("Analyzers loaded")
        app_logger.info(f"獄쏄퉮肉??筌욊쑴????브쑴苑??遺우춭 ?λ뜃由???袁⑥┷: {project_name}")
    
    def _load_analyzers(self) -> List:
        """??쇱젟?癒?퐣 ?브쑴苑띷묾?嚥≪뮆諭?""
        try:
            analyzers = self.factory.load_analyzers_from_config(self.project_name, self.servlet_url_map)
            app_logger.debug("Analyzers loaded: {}".format(len(analyzers)))
            return analyzers
        except Exception as e:
            handle_error(e, f"?브쑴苑띷묾?嚥≪뮆諭???쎈솭: {self.project_name}")
            return []
    
    def _build_project_file_path(self, dir_path: Optional[str], file_name: str) -> str:
        parts = ['projects', self.project_name]
        if dir_path:
            parts.append(dir_path)
        parts.append(file_name)
        return self.path_utils.join_path(*parts)

    def _compose_relative_file_path(self, dir_path: Optional[str], file_name: str) -> str:
        if dir_path:
            combined = os.path.join(dir_path, file_name)
        else:
            combined = file_name
        return self.path_utils.normalize_path_separator(combined, 'unix')

    def _parse_web_xml(self) -> Dict[str, str]:
        """Parse web.xml files and build servlet URL mappings"""
        try:
            query = "SELECT f.file_path, f.file_name FROM files f JOIN projects p ON f.project_id = p.project_id WHERE p.project_name = ? AND f.file_name = 'web.xml' AND f.del_yn = 'N'"
            results = self.db.execute_query(query, (self.project_name,), conn=self.conn)
            if not results:
                app_logger.debug("web.xml file not found")
                return {}

            url_map = {}
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
        """5??ｍ?獄쏄퉮肉??筌욊쑴????브쑴苑???쎈뻬 (?紐? ?紐껋삏??????곷퓠??"""
        try:
            app_logger.info("=== 獄쏄퉮肉??筌욊쑴????브쑴苑???뽰삂 ===")
            self.stats.start_analysis()

            java_files = self._get_java_files()
            if not java_files:
                handle_error(Exception("?브쑴苑??Java ???뵬????곷뮸??덈뼄."), "獄쏄퉮肉??筌욊쑴????브쑴苑???쎈솭")
                return True

            all_backend_entries = self._analyze_backend_entries(java_files)
            try:
                app_logger.info("Backend entry analysis done: {} entries".format(len(all_backend_entries)))
            except Exception:
                app_logger.info("Backend entry analysis done")

            self._save_results_to_db(all_backend_entries)
            app_logger.info("?브쑴苑?野껉퀗??DB ?????袁⑥┷")

            # 蹂댁셿 ??? MyBatis mapper namespace+id ?몃뜳????mapper_map upsert
            try:
                from util.mapper_indexer import index_mappers
                indexed = index_mappers(self.project_name, self.conn)
                app_logger.info("mapper_map ??? {}嫄?.format(indexed))
            except Exception as e:
                handle_error(e, "mapper_map ?몃뜳???섑뻾 ?ㅽ뙣")
            self._print_backend_entry_statistics()
            app_logger.info("=== 獄쏄퉮肉??筌욊쑴????브쑴苑??袁⑥┷ ===")
            return True
        except Exception as e:
            handle_error(e, f"獄쏄퉮肉??筌욊쑴????브쑴苑??袁⑥쨮?紐꾨뮞 ??쎈솭: {self.project_name}")
            return False
        finally:
            self.stats.end_analysis()

    def _get_java_files(self) -> List[FileInfo]:
        """Collect Java files to analyze."""
        query = "SELECT f.file_id, f.file_path, f.file_name, f.file_type, f.hash_value FROM files f JOIN projects p ON f.project_id = p.project_id WHERE p.project_name = ? AND UPPER(f.file_type) = 'JAVA' AND f.del_yn = 'N'"
        results = self.db.execute_query(query, (self.project_name,), conn=self.conn)

        java_files = []
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
        return java_files

    def _read_file_content(self, file_path: str) -> Optional[str]:
        """???뵬 ??곸뒠 ??꾨┛"""
        try:
            normalized_path = self.path_utils.normalize_path(file_path)
            with open(normalized_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            # ???뵬????용뮉 野껋럩??野껋럡?э쭕??곗뮆???랁?None 獄쏆꼹??(?袁⑥쨮域밸챶???ル굝利??? ??놁벉)
            handle_error(Exception(f"???뵬??筌≪뼚??????곸벉: {file_path}"), "???뵬 ??꾨┛ ??쎈솭")
            return None
        except Exception as e:
            # 疫꿸퀬? ??됱뇚??handle_error嚥?筌ｌ꼶??
            handle_error(e, f"???뵬 ??꾨┛ ??쎈솭: {file_path}")
            return None

    def _analyze_backend_entries(self, java_files: List[FileInfo]) -> List[BackendEntryInfo]:
        """獄쏄퉮肉??筌욊쑴????브쑴苑?""
        all_entries = []
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
        """2筌??袁り숲筌?獄??브쑴苑???쎈뻬"""
        file_entries = []
        for analyzer in self.analyzers:
            full_path = self.path_utils.join_path("projects", self.project_name, java_file.file_path)
            if analyzer.is_target_file(full_path):
                entries = analyzer.analyze_backend_entry(java_file, self.stats)
                file_entries.extend(entries)
                if analyzer.get_framework_name() == 'spring' and entries:
                    break
        return file_entries

    def _save_results_to_db(self, entries: List[BackendEntryInfo]) -> None:
        """?브쑴苑?野껉퀗?든몴?DB??????""
        project_id = self.db.get_project_id(self.project_name, conn=self.conn)
        if not project_id:
            raise Exception("?袁⑥쨮??븍뱜 ID 鈺곌퀬????쎈솭")

        components_to_insert = []
        if entries:
            self._create_api_components(entries, project_id, components_to_insert)
            if components_to_insert:
                self.db.batch_insert_or_replace('components', components_to_insert, conn=self.conn)

        relationships_to_insert = []
        if entries:
            self._create_api_relationships(entries, project_id, relationships_to_insert)
            if relationships_to_insert:
                self.db.batch_insert_or_replace('relationships', relationships_to_insert, conn=self.conn)

    def _create_api_url_component(self, entry: BackendEntryInfo, project_id: int) -> Optional[Dict[str, Any]]:
        # API_URL component creation
        url_pattern = entry.url_pattern.strip()
        if not url_pattern or url_pattern == '/' or url_pattern.startswith(':') or not url_pattern.startswith('/') or url_pattern.upper() in ['GET', 'POST', 'PUT', 'DELETE'] or ':' in url_pattern:
            return None
        
        component_name = format_api_component_name(entry.http_method, entry.method_name, url_pattern) or url_pattern
        identity_key = build_api_identity_key(url_pattern, entry.http_method)
        hash_value = self.hash_utils.generate_content_hash(identity_key)

        existing = self.db.get_component_by_hash(project_id, 'API_URL', hash_value)
        if existing:
            existing_id = existing['component_id']
            if existing.get('component_name') != component_name:
                self.db.update_component_name(existing_id, component_name, conn=self.conn)
            if entry.file_id is not None and existing.get('file_id') != entry.file_id:
                self.db.update_component_file_id(existing_id, entry.file_id, conn=self.conn)
            return None
        return {
            'project_id': project_id, 'file_id': entry.file_id, 'component_name': component_name,
            'component_type': 'API_URL', 'layer': 'API_ENTRY', 'line_start': entry.line_start,
            'line_end': entry.line_end, 'hash_value': hash_value, 'del_yn': 'N',
            'has_error': entry.has_error, 'error_message': entry.error_message, 'parent_id': None
        }

    def _create_api_components(self, entries: List[BackendEntryInfo], project_id: int, components_to_insert: List[Dict[str, Any]]):
        # Create API_URL components from analyzed entries
        for entry in entries:
            component = self._create_api_url_component(entry, project_id)
            if component:
                components_to_insert.append(component)

    def _find_existing_method(self, entry: BackendEntryInfo, project_id: int) -> Optional[int]:
        full_method_name = f"{entry.class_name}.{entry.method_name}"
        query = "SELECT c.component_id FROM components c WHERE c.project_id = ? AND c.component_type = 'METHOD' AND c.component_name = ? AND c.del_yn = 'N'"
        results = self.db.execute_query(query, (project_id, full_method_name), conn=self.conn)
        return results[0]['component_id'] if results else None

    def _create_api_relationships(self, entries: List[BackendEntryInfo], project_id: int, relationships_to_insert: List[Dict[str, Any]]):
        for entry in entries:
            api_url_name = format_api_component_name(entry.http_method, entry.method_name, entry.url_pattern) or entry.url_pattern
            api_url_id = self._get_component_id_by_type(project_id, api_url_name, 'API_URL')
            method_id = self._find_existing_method(entry, project_id)
            if api_url_id and method_id:
                relationships_to_insert.append({'src_id': api_url_id, 'dst_id': method_id, 'rel_type': 'CALL_METHOD', 'del_yn': 'N', 'has_error': 'N', 'error_message': None})

            # Controller ??????뵠??筌띲끋釉?????(?類? 筌띲끉臾??
            try:
                identity_key = build_api_identity_key(entry.url_pattern, entry.http_method)
                identity_hash = self.hash_utils.generate_content_hash(identity_key)
                map_data = {
                    'project_id': project_id,
                    'file_id': entry.file_id,
                    'class_name': entry.class_name,
                    'method_name': entry.method_name,
                    'http_method': (entry.http_method or ''),
                    'url': entry.url_pattern,
                    'identity_hash': identity_hash,
                    'del_yn': 'N'
                }
                # controller_api_map upsert
                self.db.insert_or_replace_with_id('controller_api_map', map_data, conn=self.conn)
            except Exception as e:
                handle_error(e, f"controller_api_map ??????쎈솭: {entry.class_name}.{entry.method_name} {entry.http_method} {entry.url_pattern}")

    def _get_component_id_by_type(self, project_id: int, component_name: str, component_type: str) -> Optional[int]:
        query = "SELECT component_id FROM components WHERE project_id = ? AND component_name = ? AND component_type = ? AND del_yn = 'N'"
        results = self.db.execute_query(query, (project_id, component_name, component_type), conn=self.conn)
        return results[0]['component_id'] if results else None

    def _print_backend_entry_statistics(self) -> None:
        self.stats.print_summary()

def execute_backend_entry_loading(project_name: str, conn: sqlite3.Connection) -> bool:
    try:
        engine = BackendEntryLoadingEngine(project_name, conn)
        return engine.execute_backend_entry_loading()
    except Exception as e:
        handle_error(e, f"獄쏄퉮肉??筌욊쑴????브쑴苑???쎈뻬 ??쎈솭: {project_name}")
        return False


