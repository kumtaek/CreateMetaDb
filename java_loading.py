"""
심플 Java 로딩 모듈 - 4단계 처리
목표: files → classes → methods 순서로 components 테이블에 등록
관계 도출이 핵심 목표
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

class SimpleJavaLoader:
    """심플한 Java 파일 로더"""

    def __init__(self, project_name: str, conn: sqlite3.Connection):
        """초기화"""
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
        """Java 파일 로딩 실행 (외부 트랜잭션 내에서)"""
        try:
            info("Java 파일 로딩 시작 (심플 버전)")
            self.collected_sql_queries = []

            java_files = []
            for root, _, files in os.walk(self.project_source_path):
                for file in files:
                    if file.endswith('.java'):
                        java_files.append(os.path.join(root, file))

            if not java_files:
                warning("분석할 Java 파일이 없습니다.")
                return True

            info(f"처리할 Java 파일 수: {len(java_files)}개")

            for java_file in java_files:
                try:
                    self._process_java_file(java_file, project_id)
                    self.stats['java_files_processed'] += 1
                except Exception as e:
                    handle_error(e, f"Java 파일 처리 실패: {java_file}")
                    self.stats['errors'] += 1

            # SQL Content 저장 및 분석
            if self.collected_sql_queries:
                self._process_collected_queries(project_id)

            info("=== Java 로딩 완료 ===")
            return True

        except Exception as e:
            handle_error(e, "Java 로딩 실행 실패")
            return False

    def _process_java_file(self, java_file: str, project_id: int):
        """개별 Java 파일 처리"""
        file_id = self._get_file_id(java_file)
        if not file_id:
            debug(f"파일 ID를 찾을 수 없음: {java_file}")
            return

        try:
            debug(f"Java 파일 파싱: {java_file}")
            parse_result = self.java_parser.parse_java_file(java_file)
            if not parse_result.get('classes'):
                warning(f"클래스가 추출되지 않았습니다: {java_file}")
        except Exception as e:
            handle_error(e, f"Java 파일 파싱 실패: {java_file}")
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
                'component_name': f"{method['class']}.{method['name']}",
                'component_type': 'METHOD', 'parent_id': parent_class_id,
                'hash_value': HashUtils().generate_content_hash(f"{method['class']}.{method['name']}")
            }
            if self._upsert_component(method_comp):
                self.stats['methods_extracted'] += 1

        # 쿼리 분석 및 수집
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
            handle_error(e, f"Java 파일 쿼리 분석 실패: {java_file}")

    def _process_collected_queries(self, project_id: int):
        """수집된 모든 SQL 쿼리를 처리"""
        info(f"수집된 SQL 쿼리 {len(self.collected_sql_queries)}개를 SQL Content에 저장 및 분석")
        if not self.sql_content_manager or not self.sql_content_manager.initialized:
            warning("SQL Content Manager가 초기화되지 않아 쿼리 처리를 건너뜁니다.")
            return

        try:
            for query_data in self.collected_sql_queries:
                self.sql_content_manager.save_sql_content(conn=self.conn, **query_data)
        except Exception as e:
            handle_error(e, "SQL Content 저장 실패")

        try:
            from util.common_sql_processor import CommonSqlAnalyzer
            common_processor = CommonSqlAnalyzer(self.project_name)
            result = common_processor.analyze_all_queries()
            self.stats['relationships_created'] += result.get('statistics', {}).get('joins_found', 0)
            info(f"생성된 관계: {result.get('statistics', {}).get('joins_found', 0)}개")
        except Exception as e:
            handle_error(e, "Common SQL Processor 처리 실패")

    def _get_file_id(self, file_path: str) -> Optional[int]:
        """파일 경로로 file_id 조회"""
        try:
            relative_path = os.path.relpath(file_path, self.project_source_path).replace('\\', '/')
            query = "SELECT file_id FROM files WHERE file_path = ? AND project_id = (SELECT project_id FROM projects WHERE project_name = ?)"
            result = self.db_utils.execute_query(query, (relative_path, self.project_name), conn=self.conn)
            return result[0]['file_id'] if result else None
        except Exception as e:
            handle_error(e, f"파일 ID 조회 실패: {file_path}")
            return None

    def _upsert_component(self, comp_data: Dict) -> Optional[int]:
        """컴포넌트 UPSERT"""
        try:
            return self.db_utils.insert_or_replace_with_id('components', comp_data, conn=self.conn)
        except Exception as e:
            handle_error(e, f"컴포넌트 UPSERT 실패: {comp_data}")
            return None

    def _upsert_class(self, cls_data: dict, project_id: int, file_id: int) -> Optional[int]:
        """클래스를 classes 테이블에 UPSERT"""
        try:
            data = {
                'project_id': project_id, 'file_id': file_id,
                'class_name': cls_data['name'], 'line_start': cls_data['line'],
                'hash_value': HashUtils().generate_content_hash(f"{cls_data['name']}{cls_data['line']}")
            }
            return self.db_utils.insert_or_replace_with_id('classes', data, conn=self.conn)
        except Exception as e:
            handle_error(e, f"클래스 UPSERT 실패: {cls_data}")
            return None

def load_java_files_simple(project_name: str, project_id: int, conn: sqlite3.Connection) -> tuple[bool, dict]:
    """심플한 Java 파일 로딩 실행"""
    loader = SimpleJavaLoader(project_name, conn)
    success = loader.execute_java_loading(project_id)
    return success, loader.stats