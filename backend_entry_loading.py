"""
SourceAnalyzer 5단계 - 백엔드 진입점 분석 메인 엔진
- Spring Framework 기반 API 진입점 분석
- API_URL 컴포넌트 생성
- CALL_API_F2B 관계 생성
- 캐싱 및 통계 수집
"""

import sqlite3
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from util.logger import app_logger, handle_error
from util.database_utils import DatabaseUtils
from util.path_utils import PathUtils
from util.hash_utils import HashUtils
from util.cache_utils import get_global_cache
from util.statistics_utils import get_global_collector
from parser.entry_analyzer_factory import get_global_factory
from parser.base_entry_analyzer import BackendEntryInfo, FileInfo


class BackendEntryLoadingEngine:
    """백엔드 진입점 분석 메인 엔진"""
    
    def __init__(self, project_name: str, conn: sqlite3.Connection):
        """
        엔진 초기화
        
        Args:
            project_name: 프로젝트명
            conn: 외부에서 주입된 데이터베이스 연결 객체
        """
        self.project_name = project_name
        self.conn = conn
        self.path_utils = PathUtils()
        self.hash_utils = HashUtils()
        self.cache = get_global_cache()
        self.stats = get_global_collector()
        self.factory = get_global_factory()
        
        self.db = DatabaseUtils(self.path_utils.get_project_metadata_db_path(project_name))
        
        self.servlet_url_map = self._parse_web_xml()
        self.analyzers = self._load_analyzers()
        app_logger.debug(f"로드된 분석기: {[analyzer.get_framework_name() for analyzer in self.analyzers]}")
        app_logger.info(f"백엔드 진입점 분석 엔진 초기화 완료: {project_name}")
    
    def _load_analyzers(self) -> List:
        """설정에서 분석기 로드"""
        try:
            analyzers = self.factory.load_analyzers_from_config(self.project_name, self.servlet_url_map)
            app_logger.debug(f"분석기 로드 완료: {len(analyzers)}개")
            return analyzers
        except Exception as e:
            handle_error(e, f"분석기 로드 실패: {self.project_name}")
            return []
    
    def _parse_web_xml(self) -> Dict[str, str]:
        """프로젝트의 web.xml 파일들을 파싱하여 서블릿 클래스와 URL 패턴 맵을 생성"""
        try:
            query = "SELECT f.file_path FROM files f JOIN projects p ON f.project_id = p.project_id WHERE p.project_name = ? AND f.file_name = 'web.xml' AND f.del_yn = 'N'"
            results = self.db.execute_query(query, (self.project_name,), conn=self.conn)
            if not results:
                app_logger.debug("web.xml 파일을 찾을 수 없습니다")
                return {}
            
            url_map = {}
            for row in results:
                try:
                    web_xml_path = self.path_utils.join_path("projects", self.project_name, row['file_path'])
                    web_xml_content = self._read_file_content(web_xml_path)
                    if not web_xml_content: continue

                    root = ET.fromstring(web_xml_content)
                    servlet_mappings = {elem.find('servlet-name').text: elem.find('url-pattern').text for elem in root.findall('servlet-mapping') if elem.find('servlet-name') is not None and elem.find('url-pattern') is not None}
                    servlet_classes = {elem.find('servlet-name').text: elem.find('servlet-class').text for elem in root.findall('servlet') if elem.find('servlet-name') is not None and elem.find('servlet-class') is not None}
                    
                    for name, url in servlet_mappings.items():
                        if name in servlet_classes:
                            url_map[servlet_classes[name]] = url
                except Exception as e:
                    handle_error(e, f"web.xml 파싱 실패: {row['file_path']}")
            return url_map
        except Exception as e:
            handle_error(e, "web.xml 파싱 중 오류 발생")
            return {}

    def execute_backend_entry_loading(self) -> bool:
        """5단계 백엔드 진입점 분석 실행 (외부 트랜잭션 내에서)"""
        try:
            app_logger.info("=== 백엔드 진입점 분석 시작 ===")
            self.stats.start_analysis()

            java_files = self._get_java_files()
            if not java_files:
                warning("분석할 Java 파일이 없습니다.")
                return True

            all_backend_entries = self._analyze_backend_entries(java_files)
            app_logger.info(f"백엔드 진입점 분석 완료: {len(all_backend_entries)}개 진입점")

            self._save_results_to_db(all_backend_entries)
            app_logger.info("분석 결과 DB 저장 완료")

            self._print_backend_entry_statistics()
            app_logger.info("=== 백엔드 진입점 분석 완료 ===")
            return True
        except Exception as e:
            handle_error(e, f"백엔드 진입점 분석 프로세스 실패: {self.project_name}")
            return False
        finally:
            self.stats.end_analysis()

    def _get_java_files(self) -> List[FileInfo]:
        """분석 대상 Java 파일 수집"""
        query = "SELECT f.file_id, f.file_path, f.file_name, f.file_type, f.hash_value FROM files f JOIN projects p ON f.project_id = p.project_id WHERE p.project_name = ? AND UPPER(f.file_type) = 'JAVA' AND f.del_yn = 'N'"
        results = self.db.execute_query(query, (self.project_name,), conn=self.conn)
        
        java_files = []
        for row in results or []:
            full_path = self.path_utils.join_path("projects", self.project_name, row['file_path'])
            content = self._read_file_content(full_path)
            if content:
                java_files.append(FileInfo(file_id=row['file_id'], file_path=row['file_path'], file_name=row['file_name'], file_type=row['file_type'], content=content, hash_value=row['hash_value'], line_count=len(content.split('\n'))))
        return java_files

    def _read_file_content(self, file_path: str) -> Optional[str]:
        """파일 내용 읽기"""
        try:
            normalized_path = self.path_utils.normalize_path(file_path)
            with open(normalized_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            handle_error(e, f"파일 읽기 실패: {file_path}")
            return None

    def _analyze_backend_entries(self, java_files: List[FileInfo]) -> List[BackendEntryInfo]:
        """백엔드 진입점 분석"""
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
        """2차 필터링 및 분석 실행"""
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
        """분석 결과를 DB에 저장"""
        project_id = self.db.get_project_id(self.project_name, conn=self.conn)
        if not project_id:
            raise Exception("프로젝트 ID 조회 실패")

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
        """API_URL 컴포넌트 데이터 생성"""
        url_pattern = entry.url_pattern.strip()
        if not url_pattern or url_pattern == '/' or url_pattern.startswith(':') or not url_pattern.startswith('/') or url_pattern.upper() in ['GET', 'POST', 'PUT', 'DELETE'] or ':' in url_pattern:
            return None
        
        component_name = f"{url_pattern}:{entry.http_method}"
        hash_value = self.hash_utils.generate_content_hash(f"{component_name}_{entry.file_path}_{entry.line_start}")
        return {
            'project_id': project_id, 'file_id': entry.file_id, 'component_name': component_name,
            'component_type': 'API_URL', 'layer': 'API_ENTRY', 'line_start': entry.line_start,
            'line_end': entry.line_end, 'hash_value': hash_value, 'del_yn': 'N',
            'has_error': entry.has_error, 'error_message': entry.error_message, 'parent_id': None
        }

    def _create_api_components(self, entries: List[BackendEntryInfo], project_id: int, components_to_insert: List[Dict[str, Any]]):
        """API_URL 컴포넌트 생성 로직"""
        for entry in entries:
            component = self._create_api_url_component(entry, project_id)
            if component:
                components_to_insert.append(component)

    def _find_existing_method(self, entry: BackendEntryInfo, project_id: int) -> Optional[int]:
        """기존 METHOD 컴포넌트 찾기"""
        full_method_name = f"{entry.class_name}.{entry.method_name}"
        query = "SELECT c.component_id FROM components c WHERE c.project_id = ? AND c.component_type = 'METHOD' AND c.component_name = ? AND c.del_yn = 'N'"
        results = self.db.execute_query(query, (project_id, full_method_name), conn=self.conn)
        return results[0]['component_id'] if results else None

    def _create_api_relationships(self, entries: List[BackendEntryInfo], project_id: int, relationships_to_insert: List[Dict[str, Any]]):
        """API_URL → METHOD 관계 생성"""
        for entry in entries:
            api_url_name = f"{entry.url_pattern}:{entry.http_method}"
            api_url_id = self._get_component_id_by_type(project_id, api_url_name, 'API_URL')
            method_id = self._find_existing_method(entry, project_id)
            if api_url_id and method_id:
                relationships_to_insert.append({'src_id': api_url_id, 'dst_id': method_id, 'rel_type': 'CALL_METHOD', 'del_yn': 'N', 'has_error': 'N', 'error_message': None})

    def _get_component_id_by_type(self, project_id: int, component_name: str, component_type: str) -> Optional[int]:
        """컴포넌트명과 타입으로 컴포넌트 ID 조회"""
        query = "SELECT component_id FROM components WHERE project_id = ? AND component_name = ? AND component_type = ? AND del_yn = 'N'"
        results = self.db.execute_query(query, (project_id, component_name, component_type), conn=self.conn)
        return results[0]['component_id'] if results else None

    def _print_backend_entry_statistics(self) -> None:
        """분석 통계 출력"""
        self.stats.print_summary()

def execute_backend_entry_loading(project_name: str, conn: sqlite3.Connection) -> bool:
    """백엔드 진입점 분석 실행 편의 함수"""
    try:
        engine = BackendEntryLoadingEngine(project_name, conn)
        return engine.execute_backend_entry_loading()
    except Exception as e:
        handle_error(e, f"백엔드 진입점 분석 실행 실패: {project_name}")
        return False
