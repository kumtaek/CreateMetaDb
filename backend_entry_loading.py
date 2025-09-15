"""
SourceAnalyzer 5단계 - 백엔드 진입점 분석 메인 엔진
- Spring Framework 기반 API 진입점 분석
- API_ENTRY, FRONTEND_API 컴포넌트 생성
- CALL_API_F2B 관계 생성
- 캐싱 및 통계 수집
"""

import time
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
    
    def __init__(self, project_name: str):
        """
        엔진 초기화
        
        Args:
            project_name: 프로젝트명
        """
        self.project_name = project_name
        self.path_utils = PathUtils()
        self.hash_utils = HashUtils()
        self.cache = get_global_cache()
        self.stats = get_global_collector()
        self.factory = get_global_factory()
        
        # 데이터베이스 연결
        self.db_path = self.path_utils.get_project_metadata_db_path(project_name)
        self.db = DatabaseUtils(self.db_path)
        
        # web.xml 파싱하여 servlet_url_map 생성
        self.servlet_url_map = self._parse_web_xml()
        
        # 분석기 로드 (servlet_url_map 전달)
        self.analyzers = self._load_analyzers()
        app_logger.debug(f"로드된 분석기: {[analyzer.get_framework_name() for analyzer in self.analyzers]}")
        
        app_logger.info(f"백엔드 진입점 분석 엔진 초기화 완료: {project_name}")
    
    def _load_analyzers(self) -> List:
        """
        설정에서 분석기 로드
        
        Returns:
            분석기 인스턴스 리스트
        """
        try:
            analyzers = self.factory.load_analyzers_from_config(self.project_name, self.servlet_url_map)
            app_logger.debug(f"분석기 로드 완료: {len(analyzers)}개")
            return analyzers
            
        except Exception as e:
            handle_error(e, f"분석기 로드 실패: {self.project_name}")
            return []
    
    def _parse_web_xml(self) -> Dict[str, str]:
        """
        프로젝트의 web.xml 파일들을 파싱하여 서블릿 클래스와 URL 패턴 맵을 생성
        
        Returns:
            {'클래스 FQDN': 'URL 패턴'} 형태의 딕셔너리
        """
        try:
            # web.xml 파일들 조회
            query = """
                SELECT f.file_id, f.file_path, f.file_name
                FROM files f
                JOIN projects p ON f.project_id = p.project_id
                WHERE p.project_name = ? AND f.file_name = 'web.xml' AND f.del_yn = 'N'
            """
            
            results = self.db.execute_query(query, (self.project_name,))
            if not results:
                app_logger.debug("web.xml 파일을 찾을 수 없습니다")
                return {}
            
            url_map = {}
            
            for row in results:
                try:
                    # 공통함수 사용 - 하드코딩 금지
                    # file_path에 이미 전체 경로(파일명 포함)가 저장됨
                    web_xml_path = self.path_utils.join_path("projects", self.project_name, row['file_path'])
                    web_xml_content = self._read_file_content(web_xml_path)
                    
                    if web_xml_content:
                        # XML 파싱
                        root = ET.fromstring(web_xml_content)
                        
                        # servlet-mapping과 servlet 정보 수집
                        servlet_mappings = {}
                        servlet_classes = {}
                        
                        # servlet-mapping 태그 파싱
                        for servlet_mapping in root.findall('servlet-mapping'):
                            servlet_name_elem = servlet_mapping.find('servlet-name')
                            url_pattern_elem = servlet_mapping.find('url-pattern')
                            
                            if servlet_name_elem is not None and url_pattern_elem is not None:
                                servlet_name = servlet_name_elem.text
                                url_pattern = url_pattern_elem.text
                                servlet_mappings[servlet_name] = url_pattern
                        
                        # servlet 태그 파싱
                        for servlet in root.findall('servlet'):
                            servlet_name_elem = servlet.find('servlet-name')
                            servlet_class_elem = servlet.find('servlet-class')
                            
                            if servlet_name_elem is not None and servlet_class_elem is not None:
                                servlet_name = servlet_name_elem.text
                                servlet_class = servlet_class_elem.text
                                servlet_classes[servlet_name] = servlet_class
                        
                        # servlet-mapping과 servlet 정보를 결합하여 URL 맵 생성
                        for servlet_name, url_pattern in servlet_mappings.items():
                            if servlet_name in servlet_classes:
                                servlet_class = servlet_classes[servlet_name]
                                url_map[servlet_class] = url_pattern
                        
                        app_logger.debug(f"web.xml 파싱 완료: {web_xml_path}, {len(url_map)}개 매핑 발견")
                        
                except Exception as e:
                    # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                    handle_error(e, f"web.xml 파싱 실패: {row['file_path']}/{row['file_name']}")
            
            app_logger.debug(f"web.xml 파싱 완료. 총 {len(url_map)}개의 서블릿 매핑을 로드했습니다")
            return url_map
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"web.xml 파싱 중 오류 발생")
    
    def execute_backend_entry_loading(self) -> bool:
        """
        5단계 백엔드 진입점 분석 실행
        
        Returns:
            실행 성공 여부 (True/False)
        """
        try:
            app_logger.info("=== 백엔드 진입점 분석 시작 ===")
            self.stats.start_analysis()
            
            # 1. 데이터베이스 연결
            if not self.db.connect():
                handle_error(Exception("데이터베이스 연결 실패"), 
                           f"백엔드 진입점 분석 실패: {self.project_name}")
            
            try:
                # 2. Java 파일 수집
                java_files = self._get_java_files()
                app_logger.debug(f"Java 파일 수집 완료: {len(java_files)}개 파일")
                
                if not java_files:
                    # USER RULE: 분석할 파일이 없으면 handle_error()로 즉시 종료
                    handle_error(Exception("분석할 Java 파일이 없음"), 
                               f"프로젝트 {self.project_name}에 분석할 Java 파일이 없습니다")
                
                # 3. 진입점 분석
                all_backend_entries = self._analyze_backend_entries(java_files)
                app_logger.info(f"백엔드 진입점 분석 완료: {len(all_backend_entries)}개 진입점")
                
                # 4. DB 저장
                if all_backend_entries:
                    self._save_results_to_db(all_backend_entries)
                    app_logger.info("분석 결과 DB 저장 완료")
                
                # 5. 통계 출력
                self._print_backend_entry_statistics()
                
                app_logger.info("=== 백엔드 진입점 분석 완료 ===")
                return True
                
            finally:
                self.db.disconnect()
                self.stats.end_analysis()
                
        except Exception as e:
            # USER RULE: 예측하지 못한 예외는 handle_error()로 즉시 종료
            handle_error(e, f"백엔드 진입점 분석 프로세스 실패: {self.project_name}")
            return False
    
    def _get_java_files(self) -> List[FileInfo]:
        """
        분석 대상 Java 파일 수집
        
        Returns:
            Java 파일 정보 리스트
        """
        try:
            # files 테이블에서 Java 파일 조회 (대소문자 구분 없이 검색 - 크로스플랫폼 대응)
            query = """
                SELECT f.file_id, f.file_path, f.file_name, f.file_type, f.hash_value
                FROM files f
                JOIN projects p ON f.project_id = p.project_id
                WHERE p.project_name = ? AND UPPER(f.file_type) = 'JAVA' AND f.del_yn = 'N'
            """
            
            results = self.db.execute_query(query, (self.project_name,))
            if not results:
                return []
            
            java_files = []
            for row in results:
                # 파일 내용 읽기 (file_path에 이미 전체 경로(파일명 포함)가 저장됨) - 공통함수 사용
                # 공통함수 사용 - 하드코딩 금지
                full_file_path = self.path_utils.join_path("projects", self.project_name, row['file_path'])
                content = self._read_file_content(full_file_path)
                
                if content is not None:
                    file_info = FileInfo(
                        file_id=row['file_id'],
                        file_path=row['file_path'],
                        file_name=row['file_name'],
                        file_type=row['file_type'],
                        content=content,
                        hash_value=row['hash_value'],
                        line_count=len(content.split('\n'))
                    )
                    java_files.append(file_info)
            
            return java_files
            
        except Exception as e:
            handle_error(e, f"Java 파일 수집 실패: {self.project_name}")
            return []
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        """
        파일 내용 읽기
        
        Args:
            file_path: 파일 경로
            
        Returns:
            파일 내용 또는 None (실패시)
        """
        try:
            # 경로 정규화 (크로스플랫폼 대응) - 공통함수 사용
            normalized_path = self.path_utils.normalize_path(file_path)
            app_logger.debug(f"파일 읽기 시도: {normalized_path}")
            
            with open(normalized_path, 'r', encoding='utf-8') as file:
                content = file.read()
                app_logger.debug(f"파일 읽기 성공: {normalized_path}, 크기: {len(content)} 문자")
                return content
                
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"파일 읽기 실패: {file_path}")
    
    def _analyze_backend_entries(self, java_files: List[FileInfo]) -> List[BackendEntryInfo]:
        """
        백엔드 진입점 분석
        
        Args:
            java_files: Java 파일 리스트
            
        Returns:
            백엔드 진입점 정보 리스트
        """
        all_entries = []
        
        for java_file in java_files:
            try:
                # 캐시 확인
                cached_entries = self.cache.get(java_file.hash_value)
                if cached_entries:
                    all_entries.extend(cached_entries)
                    app_logger.debug(f"캐시에서 분석 결과 사용: {java_file.file_path}")
                    continue
                
                # 2차 필터링 및 분석 실행
                file_entries = self._filter_and_analyze_file(java_file)
                
                # 캐시 저장 및 결과 취합
                if file_entries:
                    self.cache.set(java_file.hash_value, file_entries)
                    all_entries.extend(file_entries)
                
            except Exception as e:
                # USER RULE: 파일 분석 실패는 handle_error()로 즉시 종료
                handle_error(e, f"파일 분석 실패: {java_file.file_path}")
        
        return all_entries
    
    def _filter_and_analyze_file(self, java_file: FileInfo) -> List[BackendEntryInfo]:
        """
        2차 필터링을 수행하고, 통과 시 등록된 분석기로 분석
        
        Args:
            java_file: Java 파일 정보
            
        Returns:
            백엔드 진입점 정보 리스트
        """
        file_entries = []
        
        for analyzer in self.analyzers:
            try:
                # 공통함수 사용 - 하드코딩 금지 (프로젝트 경로 포함)
                full_file_path = self.path_utils.join_path("projects", self.project_name, java_file.file_path, java_file.file_name)
                
                # 각 분석기는 자신의 설정에 따라 2차 필터링 수행
                app_logger.debug(f"분석기 {analyzer.get_framework_name()}로 파일 {full_file_path} 필터링 확인")
                if self._is_target_for_analyzer_with_full_path(java_file, analyzer, full_file_path):
                    app_logger.debug(f"파일 {full_file_path}이 분석기 {analyzer.get_framework_name()}의 대상임")
                    entries = analyzer.analyze_backend_entry(java_file, self.stats)
                    app_logger.info(f"분석기 {analyzer.get_framework_name()}에서 {len(entries)}개 진입점 발견")
                    file_entries.extend(entries)
                else:
                    app_logger.debug(f"파일 {full_file_path}이 분석기 {analyzer.get_framework_name()}의 대상이 아님")
                    
            except Exception as e:
                # USER RULE: 분석기 실행 실패는 handle_error()로 즉시 종료
                handle_error(e, f"분석기 실행 실패: {analyzer.get_framework_name()}, 파일: {java_file.file_path}")
        
        return file_entries
    
    def _is_target_for_analyzer(self, java_file: FileInfo, analyzer) -> bool:
        """
        분석기의 2차 필터링(include/exclude) 규칙에 맞는지 확인
        
        Args:
            java_file: Java 파일 정보
            analyzer: 분석기 인스턴스
            
        Returns:
            분석 대상 여부 (True/False)
        """
        try:
            return analyzer.is_target_file(java_file.file_path)
            
        except Exception as e:
            # USER RULE: 파일 필터링 확인 실패는 handle_error()로 즉시 종료
            handle_error(e, f"파일 필터링 확인 실패: {java_file.file_path}")
    
    def _is_target_for_analyzer_with_full_path(self, java_file: FileInfo, analyzer, full_file_path: str) -> bool:
        """
        전체 파일 경로로 분석기의 2차 필터링(include/exclude) 규칙에 맞는지 확인
        
        Args:
            java_file: Java 파일 정보
            analyzer: 분석기 인스턴스
            full_file_path: 전체 파일 경로
            
        Returns:
            분석 대상 여부 (True/False)
        """
        try:
            return analyzer.is_target_file(full_file_path)
            
        except Exception as e:
            # USER RULE: 파일 필터링 확인 실패는 handle_error()로 즉시 종료
            handle_error(e, f"파일 필터링 확인 실패: {full_file_path}")
    
    def _save_results_to_db(self, entries: List[BackendEntryInfo]) -> None:
        """
        분석 결과를 components, api_components와 relationships 테이블에 저장

        Args:
            entries: 백엔드 진입점 정보 리스트
        """
        try:
            # 프로젝트 ID 조회
            project_id = self.db.get_project_id(self.project_name)
            if not project_id:
                handle_error(Exception("프로젝트 ID 조회 실패"),
                           f"DB 저장 실패: {self.project_name}")

            # 컴포넌트 데이터 준비
            components_to_insert = []
            api_components_to_insert = []
            relationships_to_insert = []

            for entry in entries:
                try:
                    # API_ENTRY 컴포넌트 생성
                    api_entry_component = self._create_api_entry_component(entry, project_id)
                    if api_entry_component:
                        components_to_insert.append(api_entry_component)

                    # FRONTEND_API 컴포넌트 생성
                    frontend_api_component = self._create_frontend_api_component(entry, project_id)
                    if frontend_api_component:
                        components_to_insert.append(frontend_api_component)

                except Exception as e:
                    # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                    handle_error(e, f"컴포넌트 생성 실패: {entry.class_name}.{entry.method_name}")

            # 배치 upsert 저장
            if components_to_insert:
                self.db.batch_insert_or_replace('components', components_to_insert)
                app_logger.debug(f"컴포넌트 upsert 저장 완료: {len(components_to_insert)}개")

            # API 컴포넌트 생성 (컴포넌트 저장 후)
            self._create_api_components(entries, project_id, api_components_to_insert)

            if api_components_to_insert:
                self.db.batch_insert_or_replace('api_components', api_components_to_insert)
                app_logger.debug(f"API 컴포넌트 upsert 저장 완료: {len(api_components_to_insert)}개")

            # 관계 생성 (컴포넌트 저장 후)
            self._create_api_relationships(entries, project_id, relationships_to_insert)

            if relationships_to_insert:
                self.db.batch_insert_or_replace('relationships', relationships_to_insert)
                app_logger.debug(f"관계 upsert 저장 완료: {len(relationships_to_insert)}개")

        except Exception as e:
            handle_error(e, f"분석 결과 DB 저장 실패: {self.project_name}")
    
    def _create_api_entry_component(self, entry: BackendEntryInfo, project_id: int) -> Optional[Dict[str, Any]]:
        """
        API_ENTRY 컴포넌트 생성
        
        Args:
            entry: 백엔드 진입점 정보
            project_id: 프로젝트 ID
            
        Returns:
            컴포넌트 데이터 딕셔너리 또는 None
        """
        try:
            # 파일 ID 직접 사용 (메모리에서 전달받음)
            file_id = entry.file_id
            
            # 컴포넌트명 생성 (유일성 보장)
            url_pattern_safe = entry.url_pattern.replace('/', '_').replace('{', '').replace('}', '')
            class_name_safe = entry.class_name.replace('.', '_')
            component_name = f"API_ENTRY.{entry.http_method}_{url_pattern_safe}-{class_name_safe}"
            
            # 해시값 생성
            hash_value = self.hash_utils.generate_content_hash(f"{component_name}_{entry.file_path}_{entry.line_start}")
            
            return {
                'project_id': project_id,
                'file_id': file_id,
                'component_name': component_name,
                'component_type': 'API_ENTRY',
                'parent_id': None,
                'layer': 'API',
                'line_start': entry.line_start,
                'line_end': entry.line_end,
                'has_error': entry.has_error,
                'error_message': entry.error_message,
                'hash_value': hash_value,
                'del_yn': 'N'
            }
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"API_ENTRY 컴포넌트 생성 실패: {entry.class_name}.{entry.method_name}")
    
    def _create_frontend_api_component(self, entry: BackendEntryInfo, project_id: int) -> Optional[Dict[str, Any]]:
        """
        FRONTEND_API 컴포넌트 생성
        
        Args:
            entry: 백엔드 진입점 정보
            project_id: 프로젝트 ID
            
        Returns:
            컴포넌트 데이터 딕셔너리 또는 None
        """
        try:
            # inferred 파일 ID 조회 (가상 컴포넌트용)
            inferred_file_id = self._get_inferred_file_id(project_id)
            if not inferred_file_id:
                # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                handle_error(Exception(f"inferred 파일 ID 조회 실패: {entry.class_name}.{entry.method_name}"), "inferred 파일 ID 조회 실패")
            
            # 컴포넌트명 생성 (유일성 보장)
            url_pattern_safe = entry.url_pattern.replace('/', '_').replace('{', '').replace('}', '')
            class_name_safe = entry.class_name.replace('.', '_')
            component_name = f"FRONTEND_API.{entry.http_method}_{url_pattern_safe}-{class_name_safe}"
            
            # 해시값 생성
            hash_value = self.hash_utils.generate_content_hash(f"{component_name}_virtual")
            
            return {
                'project_id': project_id,
                'file_id': inferred_file_id,  # inferred 파일 ID 사용
                'component_name': component_name,
                'component_type': 'FRONTEND_API',
                'parent_id': None,
                'layer': 'FRONTEND',
                'line_start': None,
                'line_end': None,
                'has_error': 'N',
                'error_message': None,
                'hash_value': hash_value,
                'del_yn': 'N'
            }
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"FRONTEND_API 컴포넌트 생성 실패: {entry.class_name}.{entry.method_name}")
    
    def _create_api_components(self, entries: List[BackendEntryInfo], project_id: int, api_components_to_insert: List[Dict[str, Any]]) -> None:
        """
        API 컴포넌트 생성 (중복 제거하여 효율적으로 처리)
        
        개선사항:
        - UNIQUE 제약조건 오류 방지를 위해 component_id별로 중복 제거
        - 같은 component_id에 대해 여러 entry가 있어도 첫 번째만 처리
        - 불필요한 중복 처리 로직 제거로 성능 향상

        Args:
            entries: 백엔드 진입점 정보 리스트
            project_id: 프로젝트 ID
            api_components_to_insert: API 컴포넌트 데이터 리스트 (출력 파라미터)
        """
        try:
            # STEP 1: component_id별로 그룹화하여 중복 제거
            # 같은 component_id에 대해 여러 entry가 있을 수 있으므로 첫 번째만 사용
            component_id_to_entry = {}
            
            for entry in entries:
                try:
                    # API_ENTRY 컴포넌트명 생성 (URL 패턴을 안전한 문자열로 변환)
                    url_pattern_safe = entry.url_pattern.replace('/', '_').replace('{', '').replace('}', '')
                    class_name_safe = entry.class_name.replace('.', '_')
                    api_entry_name = f"API_ENTRY.{entry.http_method}_{url_pattern_safe}-{class_name_safe}"

                    # components 테이블에서 해당 API_ENTRY의 component_id 조회
                    component_id = self._get_component_id(project_id, api_entry_name)

                    if component_id:
                        # 중복 제거: 같은 component_id가 있으면 첫 번째 entry만 사용
                        if component_id not in component_id_to_entry:
                            component_id_to_entry[component_id] = entry
                            app_logger.debug(f"API 컴포넌트 ID 등록: {component_id}")
                        else:
                            app_logger.debug(f"중복된 API 컴포넌트 ID 스킵: {component_id}")
                    else:
                        app_logger.warning(f"API_ENTRY 컴포넌트 ID를 찾을 수 없음: {api_entry_name}")

                except Exception as e:
                    # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                    handle_error(e, f"API 컴포넌트 ID 조회 실패: {entry.class_name}.{entry.method_name}")

            # STEP 2: hash_value 기반 변동분 처리
            # 기존 데이터와 비교해서 변경된 것만 UPSERT
            for component_id, entry in component_id_to_entry.items():
                try:
                    # 기술 스택 결정 (Spring vs Servlet)
                    tech_stack = 'SPRING_MVC' if hasattr(entry, 'framework') and entry.framework == 'spring' else 'SERVLET'

                    # 기본 메타데이터 생성 (JSON 형태로 저장)
                    import json
                    metadata = {
                        'http_method': entry.http_method,
                        'url_pattern': entry.url_pattern,
                        'class_name': entry.class_name,
                        'method_name': entry.method_name
                    }

                    # 프레임워크별 추가 메타데이터
                    if hasattr(entry, 'framework') and entry.framework == 'spring':
                        # Spring MVC 관련 메타데이터
                        metadata['request_mapping'] = getattr(entry, 'class_url', '')
                        metadata['parameters'] = getattr(entry, 'parameters', [])
                        metadata['annotations'] = getattr(entry, 'annotations', [])
                    elif hasattr(entry, 'framework') and entry.framework == 'servlet':
                        # Servlet 관련 메타데이터
                        metadata['servlet_type'] = 'WEB_SERVLET'
                        metadata['url_patterns'] = [entry.url_pattern]

                    # 변경 감지용 해시값 생성
                    hash_value = self.hash_utils.generate_content_hash(f"{component_id}_{entry.url_pattern}_{entry.http_method}")

                    # 기존 데이터와 hash_value 비교 (변동분만 처리)
                    existing_hash = self._get_existing_api_component_hash(component_id)
                    if existing_hash and existing_hash == hash_value:
                        app_logger.debug(f"API 컴포넌트 변경 없음, 스킵: {component_id}")
                        continue

                    # api_components 테이블에 저장할 데이터 구성
                    api_component = {
                        'component_id': component_id,  # components 테이블의 component_id 참조
                        'api_type': 'API_ENTRY',       # API 타입 (백엔드 진입점)
                        'tech_stack': tech_stack,      # 기술 스택 (SPRING_MVC 또는 SERVLET)
                        'interface_type': getattr(entry, 'return_type', 'String'),  # 반환 타입
                        'metadata': json.dumps(metadata, ensure_ascii=False),  # JSON 메타데이터
                        'has_error': entry.has_error,  # 오류 여부
                        'error_message': entry.error_message,  # 오류 메시지
                        'hash_value': hash_value,      # 해시값
                        'del_yn': 'N'                  # 삭제 여부
                    }
                    api_components_to_insert.append(api_component)
                    app_logger.debug(f"API 컴포넌트 UPSERT 대상: {component_id} (hash: {hash_value})")

                except Exception as e:
                    # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                    handle_error(e, f"API 컴포넌트 생성 실패: {entry.class_name}.{entry.method_name}")

        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"API 컴포넌트 생성 실패")

    def _create_api_relationships(self, entries: List[BackendEntryInfo], project_id: int, relationships_to_insert: List[Dict[str, Any]]) -> None:
        """
        API 호출 관계 생성

        Args:
            entries: 백엔드 진입점 정보 리스트
            project_id: 프로젝트 ID
            relationships_to_insert: 관계 데이터 리스트 (출력 파라미터)
        """
        try:
            for entry in entries:
                try:
                    # API_ENTRY와 FRONTEND_API 컴포넌트 ID 조회
                    url_pattern_safe = entry.url_pattern.replace('/', '_').replace('{', '').replace('}', '')
                    class_name_safe = entry.class_name.replace('.', '_')

                    api_entry_name = f"API_ENTRY.{entry.http_method}_{url_pattern_safe}-{class_name_safe}"
                    frontend_api_name = f"FRONTEND_API.{entry.http_method}_{url_pattern_safe}-{class_name_safe}"

                    # 컴포넌트 ID 조회
                    src_id = self._get_component_id(project_id, frontend_api_name)
                    dst_id = self._get_component_id(project_id, api_entry_name)

                    if src_id and dst_id:
                        relationship = {
                            'src_id': src_id,
                            'dst_id': dst_id,
                            'rel_type': 'CALL_API_F2B',
                            'has_error': 'N',
                            'error_message': None,
                            'del_yn': 'N'
                        }
                        relationships_to_insert.append(relationship)

                except Exception as e:
                    # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                    handle_error(e, f"관계 생성 실패: {entry.class_name}.{entry.method_name}")

        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"API 관계 생성 실패")
    
    def _get_file_id(self, file_path: str) -> Optional[int]:
        """
        파일 경로로 파일 ID 조회
        
        Args:
            file_path: 파일 경로 (디렉토리 경로)
            
        Returns:
            파일 ID 또는 None
        """
        try:
            # 경로 정규화 (크로스플랫폼 대응) - 공통함수 사용
            normalized_path = self.path_utils.normalize_path(file_path)
            
            # file_path는 디렉토리 경로이므로, 해당 디렉토리의 첫 번째 파일을 찾음
            query = """
                SELECT f.file_id
                FROM files f
                JOIN projects p ON f.project_id = p.project_id
                WHERE p.project_name = ? AND f.file_path = ? AND f.del_yn = 'N'
                LIMIT 1
            """
            
            results = self.db.execute_query(query, (self.project_name, normalized_path))
            if results:
                file_id = results[0]['file_id']
                app_logger.debug(f"파일 ID 조회 성공: {file_path} -> {file_id}")
                return file_id
            else:
                # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                handle_error(Exception(f"파일 ID 조회 실패: {file_path} (경로: {normalized_path})"), "파일 ID 조회 실패")
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"파일 ID 조회 실패: {file_path}")
    
    def _get_inferred_file_id(self, project_id: int) -> Optional[int]:
        """
        inferred 컴포넌트용 file_id 조회 (Java 파일 중 하나 선택)
        
        Args:
            project_id: 프로젝트 ID
            
        Returns:
            file_id 또는 None
        """
        try:
            query = """
                SELECT file_id
                FROM files
                WHERE project_id = ? AND file_type = 'JAVA' AND del_yn = 'N'
                LIMIT 1
            """
            result = self.db.execute_query(query, (project_id,))
            
            if result and len(result) > 0:
                file_id = result[0]['file_id']
                app_logger.debug(f"inferred 파일 ID 찾음: {file_id}")
                return file_id
            else:
                # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                handle_error(Exception("inferred 파일 ID를 찾을 수 없습니다"), "inferred 파일 ID 조회 실패")
                
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"inferred 파일 ID 조회 실패")
    
    def _get_component_id(self, project_id: int, component_name: str) -> Optional[int]:
        """
        컴포넌트명으로 컴포넌트 ID 조회

        Args:
            project_id: 프로젝트 ID
            component_name: 컴포넌트명

        Returns:
            컴포넌트 ID 또는 None
        """
        try:
            query = """
                SELECT component_id
                FROM components
                WHERE project_id = ? AND component_name = ? AND del_yn = 'N'
            """

            results = self.db.execute_query(query, (project_id, component_name))
            return results[0]['component_id'] if results else None

        except Exception as e:
            # USER RULE: 데이터베이스 조회 실패는 handle_error()로 즉시 종료
            handle_error(e, f"컴포넌트 ID 조회 실패: {component_name}")

    def _get_existing_api_component_hash(self, component_id: int) -> Optional[str]:
        """
        기존 API 컴포넌트의 hash_value 조회

        Args:
            component_id: 컴포넌트 ID

        Returns:
            기존 hash_value 또는 None (존재하지 않는 경우)
        """
        try:
            query = """
                SELECT hash_value
                FROM api_components
                WHERE component_id = ? AND del_yn = 'N'
            """

            results = self.db.execute_query(query, (component_id,))
            return results[0]['hash_value'] if results else None

        except Exception as e:
            # USER RULE: 데이터베이스 조회 실패는 handle_error()로 즉시 종료
            handle_error(e, f"API 컴포넌트 hash_value 조회 실패: {component_id}")
    
    def _print_backend_entry_statistics(self) -> None:
        """백엔드 진입점 분석 통계 출력"""
        try:
            self.stats.print_summary()
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"통계 출력 실패")


# 편의 함수
def execute_backend_entry_loading(project_name: str) -> bool:
    """
    백엔드 진입점 분석 실행 편의 함수
    
    Args:
        project_name: 프로젝트명
        
    Returns:
        실행 성공 여부 (True/False)
    """
    try:
        engine = BackendEntryLoadingEngine(project_name)
        return engine.execute_backend_entry_loading()
        
    except Exception as e:
        handle_error(e, f"백엔드 진입점 분석 실행 실패: {project_name}")
        return False


# 사용 예시
if __name__ == "__main__":
    # 백엔드 진입점 분석 테스트
    project_name = "sampleSrc"
    
    success = execute_backend_entry_loading(project_name)
    if success:
        print("백엔드 진입점 분석 완료")
    else:
        print("백엔드 진입점 분석 실패")
