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
from parser.simple_java_parser import SimpleJavaParser
from parser.simple_query_analyzer import SimpleQueryAnalyzer
from util.sql_content_manager import SqlContentManager
from util.path_utils import PathUtils

class SimpleJavaLoader:
    """Simple Java file loader"""

    def __init__(self, project_name: str, conn: sqlite3.Connection):
        """Initialize loader"""
        self.project_name = project_name
        self.conn = conn
        self.project_source_path = get_project_source_path(project_name)

        self.db_utils = DatabaseUtils(get_project_metadata_db_path(project_name))
        self.java_parser = SimpleJavaParser()
        self.simple_query_analyzer = SimpleQueryAnalyzer(project_name, self.conn)
        self.sql_content_manager = SqlContentManager(project_name)

        self.stats = {
            'java_files_processed': 0,
            'classes_extracted': 0,
            'methods_extracted': 0,
            'sql_queries_extracted': 0,
            'relationships_created': 0,
            'errors': 0
        }

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
                warning("No Java files found to analyze.")
                return True

            info(f"Java files to process: {len(java_files)}")

            for java_file in java_files:
                try:
                    self._process_java_file(java_file, project_id)
                    self.stats['java_files_processed'] += 1
                except Exception as e:
                    handle_error(e, f"Java file processing failed: {java_file}")
                    self.stats['errors'] += 1

            if self.collected_sql_queries:
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
            debug(f"File ID not found: {java_file}")
            return

        try:
            debug(f"Parsing Java file: {java_file}")
            parse_result = self.java_parser.parse_java_file(java_file)
            if not parse_result.get('classes'):
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
                class_name = os.path.splitext(os.path.basename(java_file))[0]
                query_counter = {}
                for query in all_queries:
                    method_name = query.get('method_name', 'unknown')
                    query_counter[method_name] = query_counter.get(method_name, 0) + 1
                    formatted_query_id = f"{class_name}.{method_name}_Qry_{query_counter[method_name]}"
                    self.collected_sql_queries.append({
                        'sql_content': query.get('sql_content', ''), 'query_id': formatted_query_id,
                        'file_id': file_id, 'project_id': project_id
                    })
        except Exception as e:
            handle_error(e, f"Java query analysis failed: {java_file}")

    def _process_collected_queries(self, project_id: int):
        """Process all collected SQL queries"""
        info(f"Collected SQL queries: {len(self.collected_sql_queries)} → save & post-process")
        if not self.sql_content_manager or not self.sql_content_manager.initialized:
            warning("SQL Content Manager媛 珥덇린?붾릺吏 ?딆븘 荑쇰━ 泥섎━瑜?嫄대꼫?곷땲??")
            return

        try:
            from util.common_sql_processor import CommonSqlAnalyzer
            analyzer = CommonSqlAnalyzer(self.project_name)
            for query_data in self.collected_sql_queries:
                ok = self.sql_content_manager.save_sql_content(conn=self.conn, **query_data)
                # 利됱떆 USE_TABLE/JOIN/而щ읆 愿怨??앹꽦 蹂댁셿 泥섎━
                try:
                    if ok and query_data.get('sql_content'):
                        clean_sql = analyzer._remove_comments(query_data['sql_content'])
                        table_info = analyzer._extract_tables(clean_sql)
                        alias_map = table_info.get('alias_map', {})
                        joins = []
                        joins.extend(analyzer._extract_explicit_joins(clean_sql, alias_map))
                        joins.extend(analyzer._extract_implicit_joins(clean_sql, alias_map))
                        joins.extend(analyzer._extract_merge_joins(clean_sql, alias_map))
                        if joins:
                            analyzer._save_table_joins_components(joins)
                        # 而щ읆 ?ъ슜 愿怨꾨뒗 SQL component_id媛 ?꾩슂?섏뿬 ??λ맂 component?????common_sql_processor媛 泥섎━
                        # ?ш린?쒕뒗 而щ읆紐낅쭔 異붿텧?섏뿬 愿怨?????쒕룄
                        columns = analyzer._extract_columns(clean_sql, alias_map)
                        if columns:
                            # component_id??諛⑷툑 ??λ맂 component_name???ㅻ줈 議고쉶
                            comp_name = query_data.get('query_id') or query_data.get('component_name')
                            comp_row = self.db_utils.execute_query(
                                "SELECT component_id FROM components WHERE project_id=(SELECT project_id FROM projects WHERE project_name=?) AND component_name=? AND component_type LIKE 'SQL_%' AND del_yn='N' ORDER BY component_id DESC LIMIT 1",
                                (self.project_name, comp_name),
                                conn=self.conn,
                            )
                            if comp_row:
                                analyzer._save_use_column_relationships(comp_row[0]['component_id'], columns)
                except Exception as e:
                    handle_error(e, "利됱떆 SQL 蹂댁셿 遺꾩꽍 ?ㅽ뙣(Java)")
        except Exception as e:
            handle_error(e, "SQL content save failed")

        try:
            from util.common_sql_processor import CommonSqlAnalyzer
            common_processor = CommonSqlAnalyzer(self.project_name)
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
            return None

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

def load_java_files_simple(project_name: str, project_id: int, conn: sqlite3.Connection) -> tuple[bool, dict]:
    """Run simple Java loading"""
    loader = SimpleJavaLoader(project_name, conn)
    success = loader.execute_java_loading(project_id)
    return success, loader.stats




