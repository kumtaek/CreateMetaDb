"""
SourceAnalyzer 5단계 - 백엔드 진입점 분석 메인 엔진
- Spring Framework 기반 API 진입점 분석
- API_URL 컴포넌트 생성
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
                
                # 4. DB 저장 (진입점이 없어도 실행)
                self._save_results_to_db(all_backend_entries)
                app_logger.info("분석 결과 DB 저장 완료")

                # 5. API_URL → METHOD 관계는 _save_results_to_db에서 처리됨

                # 6. 통계 출력
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
                    app_logger.debug(f"분석기 {analyzer.get_framework_name()}에서 {len(entries)}개 진입점 발견")
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
        분석 결과를 components와 relationships 테이블에 저장

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
            relationships_to_insert = []

            # API_URL 컴포넌트 생성 (진입점이 있을 때만)
            if entries:
                self._create_api_components(entries, project_id, components_to_insert)

                # 배치 upsert 저장
                if components_to_insert:
                    self.db.batch_insert_or_replace('components', components_to_insert)
                    app_logger.debug(f"API_URL 컴포넌트 upsert 저장 완료: {len(components_to_insert)}개")

                # 관계 생성 (컴포넌트 저장 후)
                self._create_api_relationships(entries, project_id, relationships_to_insert)
            else:
                app_logger.info("백엔드 진입점이 없어 API_URL 컴포넌트를 생성하지 않습니다")

            if relationships_to_insert:
                self.db.batch_insert_or_replace('relationships', relationships_to_insert)
                app_logger.debug(f"관계 upsert 저장 완료: {len(relationships_to_insert)}개")

        except Exception as e:
            handle_error(e, f"분석 결과 DB 저장 실패: {self.project_name}")
    
    def _create_api_url_component(self, entry: BackendEntryInfo, project_id: int) -> Optional[Dict[str, Any]]:
        """
        API_URL 컴포넌트 생성 (과거 FRONTEND_API 로직을 참고한 JSP 파일 매칭)
        
        설계 컨셉:
        - 매칭 성공: JSP 파일의 file_id 사용 → 완전한 체인 (JSP → API_URL → METHOD)
        - 매칭 실패: Java 파일의 file_id 사용 → 끊어진 체인 (Java → API_URL → METHOD)
        
        CallChain 리포트에서:
        - 매칭 성공: Frontend 컬럼에 JSP 파일명 표시
        - 매칭 실패: Frontend 컬럼에 Java 파일명 표시 (개발자가 매칭 실패 파악 가능)
        
        Args:
            entry: 백엔드 진입점 정보
            project_id: 프로젝트 ID
            
        Returns:
            컴포넌트 데이터 딕셔너리 또는 None
        """
        try:
            # 5단계에서는 JSP 파일이 아직 분석되지 않았으므로 일단 Java file_id 사용
            # 6단계 JSP 분석 후 올바른 file_id로 업데이트됨
            file_id = entry.file_id
            app_logger.debug(f"5단계 API_URL 생성: {entry.url_pattern} → Java file_id: {entry.file_id} (6단계에서 JSP 매칭 예정)")
            app_logger.debug(f"API_URL 컴포넌트명: {entry.url_pattern}:{entry.http_method}")
            
            # API_URL 컴포넌트명 생성 (URL:HTTP_METHOD 형태)
            # 잘못된 URL 패턴 필터링 강화
            url_pattern = entry.url_pattern.strip()
            
            # 1. 빈 문자열이나 루트 경로만 있는 경우
            if url_pattern in ['/', '']:
                app_logger.debug(f"잘못된 URL 패턴으로 인해 API_URL 생성 건너뜀: '{url_pattern}:{entry.http_method}'")
                return None
            
            # 2. 콜론으로 시작하는 경우 (HTTP 메서드만 있는 경우)
            if url_pattern.startswith(':'):
                app_logger.debug(f"잘못된 URL 패턴으로 인해 API_URL 생성 건너뜀: '{url_pattern}:{entry.http_method}'")
                return None
            
            # 3. 슬래시로 시작하지 않는 경우
            if not url_pattern.startswith('/'):
                app_logger.debug(f"잘못된 URL 패턴으로 인해 API_URL 생성 건너뜀: '{url_pattern}:{entry.http_method}'")
                return None
            
            # 4. HTTP 메서드만 있는 경우 (예: GET, POST, PUT, DELETE)
            if url_pattern.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                app_logger.debug(f"잘못된 URL 패턴으로 인해 API_URL 생성 건너뜀: '{url_pattern}:{entry.http_method}'")
                return None
            
            # 5. 콜론이 포함된 경우 (이미 HTTP 메서드가 포함된 패턴)
            if ':' in url_pattern:
                app_logger.debug(f"잘못된 URL 패턴으로 인해 API_URL 생성 건너뜀: '{url_pattern}:{entry.http_method}'")
                return None
            
            component_name = f"{url_pattern}:{entry.http_method}"
            
            # 해시값 생성
            hash_value = self.hash_utils.generate_content_hash(f"{component_name}_{entry.file_path}_{entry.line_start}")
            
            return {
                'project_id': project_id,
                'file_id': file_id,  # JSP file_id (매칭 성공) 또는 Java file_id (매칭 실패)
                'component_name': component_name,
                'component_type': 'API_URL',
                'parent_id': None,
                'layer': 'API_ENTRY',
                'line_start': entry.line_start,
                'line_end': entry.line_end,
                'has_error': entry.has_error,
                'error_message': entry.error_message,
                'hash_value': hash_value,
                'del_yn': 'N'
            }
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"API_URL 컴포넌트 생성 실패: {entry.class_name}.{entry.method_name}")
    
    def _find_matching_frontend_file(self, api_url: str, http_method: str, project_id: int) -> Optional[int]:
        """
        API_URL에 매칭되는 프론트엔드 파일 찾기 (범용 프론트엔드 지원)
        
        매칭 로직:
        1. 프론트엔드 파일(JSP, JSX, Vue, TypeScript, JS 등)에서 해당 API URL을 호출하는지 확인
        2. 매칭 성공 시 프론트엔드 파일 ID 반환
        3. 매칭 실패 시 None 반환 (Java 파일 ID 사용됨)
        
        Args:
            api_url: API URL 패턴 (예: /api/user-profile)
            http_method: HTTP 메서드 (예: GET, POST)
            project_id: 프로젝트 ID
            
        Returns:
            프론트엔드 파일 ID (매칭 성공 시) 또는 None (매칭 실패 시)
        """
        try:
            # 1. 이미 생성된 API_URL 컴포넌트에서 해당 API를 호출하는 프론트엔드 파일 찾기
            # 7단계에서 프론트엔드 분석 시 생성된 API_URL 컴포넌트를 활용
            existing_api_query = """
                SELECT DISTINCT c.file_id, f.file_name, f.file_type
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                WHERE c.project_id = ? 
                  AND c.component_type = 'API_URL'
                  AND c.component_name = ?
                  AND f.file_type IN ('JSP', 'JSX', 'VUE', 'TS', 'JS', 'HTML')
                  AND c.del_yn = 'N'
                  AND f.del_yn = 'N'
                ORDER BY 
                    CASE f.file_type 
                        WHEN 'JSP' THEN 1 
                        WHEN 'JSX' THEN 2 
                        WHEN 'VUE' THEN 3 
                        WHEN 'TS' THEN 4 
                        WHEN 'JS' THEN 5 
                        WHEN 'HTML' THEN 6 
                        ELSE 7 
                    END
                LIMIT 1
            """
            api_component_name = f"{api_url}:{http_method}"
            results = self.db.execute_query(existing_api_query, (project_id, api_component_name))
            
            if results and len(results) > 0:
                frontend_file_id = results[0]['file_id']
                file_name = results[0]['file_name']
                file_type = results[0]['file_type']
                app_logger.debug(f"기존 API_URL 컴포넌트에서 매칭: {api_url}:{http_method} → {file_name} ({file_type}, file_id: {frontend_file_id})")
                return frontend_file_id
            
            # 2. 매칭 실패: 프론트엔드에서 해당 API를 호출하지 않음
            app_logger.debug(f"프론트엔드 파일 매칭 실패: {api_url}:{http_method} (프론트엔드에서 호출하지 않음)")
            return None
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"프론트엔드 파일 매칭 실패: {api_url}:{http_method}")
            return None
    
    
    def _create_api_components(self, entries: List[BackendEntryInfo], project_id: int, components_to_insert: List[Dict[str, Any]]) -> None:
        """
        API_URL 컴포넌트 생성 (설계 컨셉에 따른 단일 컴포넌트)
        
        Args:
            entries: 백엔드 진입점 정보 리스트
            project_id: 프로젝트 ID
            components_to_insert: 컴포넌트 데이터 리스트 (출력 파라미터)
        """
        try:
            app_logger.info("API_URL 컴포넌트 생성 시작")
            
            for entry in entries:
                try:
                    # API_URL 컴포넌트 생성
                    api_url_component = self._create_api_url_component(entry, project_id)
                    if api_url_component:
                        components_to_insert.append(api_url_component)
                        app_logger.debug(f"API_URL 컴포넌트 생성: {api_url_component['component_name']}")
                    
                except Exception as e:
                    # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                    handle_error(e, f"API_URL 컴포넌트 생성 실패: {entry.class_name}.{entry.method_name}")
            
            app_logger.debug(f"API_URL 컴포넌트 생성 완료: {len(components_to_insert)}개")
            
        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"API_URL 컴포넌트 생성 실패")

    def _find_existing_method(self, entry: BackendEntryInfo, project_id: int) -> Optional[int]:
        """
        백엔드 진입점 정보로 기존 METHOD 컴포넌트 찾기
        클래스명과 메서드명을 모두 사용하여 정확한 매칭

        Args:
            entry: 백엔드 진입점 정보
            project_id: 프로젝트 ID

        Returns:
            METHOD 컴포넌트 ID (없으면 None)
        """
        try:
            # 클래스명과 메서드명을 모두 사용한 정확한 매칭
            # FORMAT: 클래스명.메서드명으로 매칭
            full_method_name = f"{entry.class_name}.{entry.method_name}"

            # 먼저 정확한 클래스.메서드 형태로 검색
            query = """
                SELECT c.component_id
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                JOIN projects p ON f.project_id = p.project_id
                WHERE p.project_id = ?
                  AND c.component_type = 'METHOD'
                  AND c.component_name = ?
                  AND f.del_yn = 'N'
                  AND c.del_yn = 'N'
            """

            results = self.db.execute_query(query, (project_id, full_method_name))
            if results:
                return results[0]['component_id']

            # 정확한 매칭이 안되면 클래스명이 포함된 메서드 검색
            # (다른 파일의 동일 메서드명과 구분하기 위해)
            like_pattern = f"%{entry.class_name}.{entry.method_name}%"
            query_like = """
                SELECT c.component_id, c.component_name
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                JOIN projects p ON f.project_id = p.project_id
                WHERE p.project_id = ?
                  AND c.component_type = 'METHOD'
                  AND c.component_name LIKE ?
                  AND f.del_yn = 'N'
                  AND c.del_yn = 'N'
            """

            results_like = self.db.execute_query(query_like, (project_id, like_pattern))
            if results_like:
                # 정확한 클래스.메서드 패턴을 찾기
                for result in results_like:
                    component_name = result['component_name']
                    if component_name.endswith(f"{entry.class_name}.{entry.method_name}"):
                        return result['component_id']

            # 마지막으로 파일 기반 매칭 (파일 ID로 필터링)
            if entry.file_id and entry.file_id > 0:
                query_file = """
                    SELECT c.component_id
                    FROM components c
                    WHERE c.file_id = ?
                      AND c.component_type = 'METHOD'
                      AND c.component_name LIKE ?
                      AND c.del_yn = 'N'
                """
                method_pattern = f"%{entry.method_name}%"
                results_file = self.db.execute_query(query_file, (entry.file_id, method_pattern))
                if results_file:
                    return results_file[0]['component_id']

            # 모든 매칭 실패
            app_logger.debug(f"METHOD 컴포넌트 매칭 실패: {entry.class_name}.{entry.method_name} (file_id: {entry.file_id})")
            return None

        except Exception as e:
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(e, f"METHOD 컴포넌트 찾기 실패: {entry.class_name}.{entry.method_name}")

    def _create_api_relationships(self, entries: List[BackendEntryInfo], project_id: int, relationships_to_insert: List[Dict[str, Any]]) -> None:
        """
        API_URL → METHOD 관계 생성 (CALL_METHOD)

        Args:
            entries: 백엔드 진입점 정보 리스트
            project_id: 프로젝트 ID
            relationships_to_insert: 관계 데이터 리스트 (출력 파라미터)
        """
        try:
            app_logger.debug("API_URL → METHOD 관계 생성 시작")
            
            for entry in entries:
                try:
                    # API_URL 컴포넌트 ID 조회
                    api_url_name = f"{entry.url_pattern}:{entry.http_method}"
                    api_url_id = self._get_component_id_by_type(project_id, api_url_name, 'API_URL')
                    
                    # METHOD 컴포넌트 ID 조회 (기존 METHOD 찾기)
                    method_id = self._find_existing_method(entry, project_id)
                    
                    if api_url_id and method_id:
                        relationship = {
                            'src_id': api_url_id,  # API_URL 컴포넌트
                            'dst_id': method_id,   # METHOD 컴포넌트
                            'rel_type': 'CALL_METHOD',  # 통일된 관계 타입
                            'has_error': 'N',
                            'error_message': None,
                            'del_yn': 'N'
                        }
                        relationships_to_insert.append(relationship)
                        app_logger.debug(f"API_URL → METHOD 관계 생성: {api_url_name} → {entry.method_name}")
                    elif not api_url_id:
                        app_logger.debug(f"API_URL 컴포넌트를 찾을 수 없음: {api_url_name}")
                    elif not method_id:
                        app_logger.warning(f"METHOD 컴포넌트를 찾을 수 없음: {entry.class_name}.{entry.method_name}")
                    else:
                        app_logger.warning(f"컴포넌트 ID 조회 실패: API_URL={api_url_id}, METHOD={method_id}, 진입점: {entry.class_name}.{entry.method_name}")

                except Exception as e:
                    # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                    handle_error(e, f"관계 생성 실패: {entry.class_name}.{entry.method_name}")
            
            app_logger.debug(f"API_URL → METHOD 관계 생성 완료: {len(relationships_to_insert)}개")

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

    def _get_component_id_by_type(self, project_id: int, component_name: str, component_type: str) -> Optional[int]:
        """
        컴포넌트명과 타입으로 컴포넌트 ID 조회

        Args:
            project_id: 프로젝트 ID
            component_name: 컴포넌트명
            component_type: 컴포넌트 타입

        Returns:
            컴포넌트 ID 또는 None
        """
        try:
            query = """
                SELECT component_id
                FROM components
                WHERE project_id = ? AND component_name = ? AND component_type = ? AND del_yn = 'N'
            """

            results = self.db.execute_query(query, (project_id, component_name, component_type))
            return results[0]['component_id'] if results else None

        except Exception as e:
            # USER RULE: 데이터베이스 조회 실패는 handle_error()로 즉시 종료
            handle_error(e, f"컴포넌트 ID 조회 실패: {component_name} ({component_type})")

    
    # 기존 API_ENTRY 관련 메서드들은 제거됨 (새로운 API_URL 설계로 대체)

    def _get_project_id(self) -> Optional[int]:
        """프로젝트 ID 조회"""
        try:
            query = """
                SELECT project_id
                FROM projects
                WHERE project_name = ? AND del_yn = 'N'
            """

            results = self.db.execute_query(query, (self.project_name,))
            return results[0]['project_id'] if results else None

        except Exception as e:
            handle_error(e, f"프로젝트 ID 조회 실패: {self.project_name}")

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
    import sys
    from util.arg_utils import ArgUtils
    
    # 명령행 인자 파싱
    arg_utils = ArgUtils()
    parser = arg_utils.create_parser("백엔드 진입점 분석 도구")
    args = parser.parse_args()
    
    project_name = args.project_name
    print(f"백엔드 진입점 분석 시작: {project_name}")
    
    success = execute_backend_entry_loading(project_name)
    if success:
        print(f"백엔드 진입점 분석 완료: {project_name}")
    else:
        print(f"백엔드 진입점 분석 실패: {project_name}")
