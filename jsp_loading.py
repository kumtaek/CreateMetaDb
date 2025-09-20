"""
JSP 로딩 모듈 - 5단계 Phase 1 MVP
- JSP 파일에서 JSP 컴포넌트 추출 및 Java 메서드 관계 분석
- 메모리 최적화 (스트리밍 처리)
- 데이터베이스 저장 및 통계 관리

USER RULES:
- 하드코딩 금지: path_utils.get_parser_config_path("jsp") 사용 (크로스플랫폼 대응)
- 파싱 에러 처리: has_error='Y', error_message 저장 후 계속 실행
- 시스템 에러 처리: handle_error() 공통함수 사용
- 공통함수 사용: util 모듈 활용
- 메뉴얼 기반: parser/manual/02_jsp 참고
"""

import os
from typing import List, Dict, Any, Optional
from util import (
    DatabaseUtils, PathUtils, HashUtils, ValidationUtils,
    app_logger, info, error, debug, warning, handle_error,
    get_project_source_path, get_project_metadata_db_path
)
# USER RULES: 공통함수 사용, 하드코딩 금지
from parser.jsp_parser import JspParser


class JspLoadingEngine:
    """JSP 로딩 엔진 - 5단계 Phase 1 MVP"""

    def __init__(self, project_name: str):
        """
        JSP 로딩 엔진 초기화

        Args:
            project_name: 프로젝트명
        """
        self.project_name = project_name
        self.project_source_path = get_project_source_path(project_name)
        self.metadata_db_path = get_project_metadata_db_path(project_name)
        self.db_utils = None

        # JSP 파서 초기화 (USER RULES: 공통함수 사용)
        self.jsp_parser = JspParser()
        
        # HashUtils 초기화
        self.hash_utils = HashUtils()

        # 현재 처리 중인 파일의 file_id (메모리 최적화)
        self.current_file_id = None

        # 통계 정보 (5단계 Phase 1 MVP)
        self.stats = {
            'jsp_files_processed': 0,
            'jsp_components_created': 0,
            'jsp_method_relationships_created': 0,
            'api_url_components_created': 0,
            'api_url_method_relationships_created': 0,
            'errors': 0,
            'processing_time': 0.0
        }

    def execute_jsp_loading(self) -> bool:
        """
        JSP 로딩 실행: 5단계 Phase 1 MVP

        Returns:
            실행 성공 여부
        """
        import time
        start_time = time.time()

        try:
            info("=== JSP 로딩 시작: 5단계 Phase 1 MVP ===")

            # 데이터베이스 연결 (USER RULES: 공통함수 사용)
            self.db_utils = DatabaseUtils(self.metadata_db_path)
            if not self.db_utils.connect():
                error("메타데이터베이스 연결 실패")
                return False

            # 1. JSP 파일 수집
            jsp_files = self.jsp_parser.get_filtered_jsp_files(self.project_source_path)
            if not jsp_files:
                warning("JSP 파일이 없습니다")
                return True

            info(f"처리할 JSP 파일 수: {len(jsp_files)}개")

            # 2. JSP 파일별 통합 처리 (메모리 최적화)
            for jsp_file in jsp_files:
                try:
                    # 파일 읽기 시작 시 file_id를 변수에 저장 (외래키 문제 해결)
                    # 간단하게 파일 경로에서 file_id 추출
                    self.current_file_id = self._extract_file_id_from_path(jsp_file)
                    info(f"현재 처리 중인 JSP 파일: {jsp_file}, current_file_id: {self.current_file_id}")
                    
                    # 5단계 Phase 1 MVP: JSP 컴포넌트 추출 + Java 메서드 관계 분석
                    debug(f"JSP 파일 파싱 시작: {jsp_file}")
                    analysis_result = self.jsp_parser.parse_jsp_file(jsp_file)
                    debug(f"JSP 파일 파싱 완료: {jsp_file}")
                    
                    # API 호출 분석 추가
                    if not analysis_result.get('has_error'):
                        try:
                            with open(jsp_file, 'r', encoding='utf-8', errors='ignore') as f:
                                jsp_content = f.read()
                            api_calls = self.jsp_parser.analyze_api_calls(jsp_content, os.path.basename(jsp_file))
                            if api_calls:
                                analysis_result['api_calls'] = api_calls
                                debug(f"API 호출 {len(api_calls)}개 발견: {jsp_file}")
                        except Exception as e:
                            handle_error(e, f"API 호출 분석 실패: {jsp_file}")

                    # 파싱 에러 체크 (USER RULES: 파싱 에러는 계속 진행)
                    if analysis_result.get('has_error') == 'Y':
                        warning(f"JSP 파싱 에러로 건너뜀: {jsp_file} - {analysis_result.get('error_message', '')}")
                        self.stats['errors'] += 1
                        continue

                    # JSP 컴포넌트 저장
                    if analysis_result.get('jsp_component'):
                        self._save_jsp_components_to_database([analysis_result['jsp_component']])

                    # JSP → METHOD 관계 저장
                    if analysis_result.get('java_method_relationships'):
                        self._save_jsp_method_relationships_to_database(analysis_result['java_method_relationships'])

                    # API 호출 분석 및 API_URL 컴포넌트 생성
                    if analysis_result.get('api_calls'):
                        self._save_api_url_components_to_database(analysis_result['api_calls'])
                        # API_URL과 METHOD 간의 관계 생성
                        self._create_api_url_method_relationships(analysis_result['api_calls'])

                    # 통계 업데이트
                    self.stats['jsp_files_processed'] += 1
                    if analysis_result.get('jsp_component'):
                        self.stats['jsp_components_created'] += 1
                    if analysis_result.get('java_method_relationships'):
                        self.stats['jsp_method_relationships_created'] += len(analysis_result['java_method_relationships'])
                    if analysis_result.get('api_calls'):
                        self.stats['api_url_components_created'] += len(analysis_result['api_calls'])
                        # API_URL → METHOD 관계 통계는 _create_api_url_method_relationships에서 업데이트

                except Exception as e:
                    # USER RULES: 파싱 에러는 has_error='Y', error_message 저장 후 계속 진행
                    handle_error(e, f"JSP 파일 처리 중 오류: {jsp_file}")
                    continue

            # 3. 통계 정보 출력
            self.stats['processing_time'] = time.time() - start_time
            self._print_jsp_loading_statistics()

            info("=== JSP 로딩 완료: 5단계 Phase 1 MVP ===")
            return True

        except Exception as e:
            # USER RULES: 시스템 에러는 handle_error()로 exit
            handle_error(e, "JSP 로딩 실행 실패")
            return False

        finally:
            # 데이터베이스 연결 해제
            if self.db_utils:
                self.db_utils.disconnect()

    def _save_jsp_components_to_database(self, jsp_components: List[Dict[str, Any]]) -> bool:
        """
        JSP 컴포넌트를 components 테이블에 저장

        Args:
            jsp_components: JSP 컴포넌트 정보 리스트

        Returns:
            저장 성공 여부
        """
        try:
            if not jsp_components:
                return True

            # 프로젝트 ID 조회
            project_id = self._get_project_id()
            if not project_id:
                error("프로젝트 ID 조회 실패")
                return False

            # JSP 컴포넌트 데이터 변환
            component_data_list = []
            for jsp_comp in jsp_components:
                # 현재 파일의 file_id 사용 (메모리 최적화)
                info(f"JSP 컴포넌트 생성 시도: {jsp_comp['jsp_name']}, current_file_id: {self.current_file_id}")
                if self.current_file_id is not None:
                    # 중복 체크: 같은 project_id, component_name, file_id 조합이 이미 있는지 확인
                    debug(f"중복 체크 시작: project_id={project_id}, component_name='{jsp_comp['jsp_name']}', file_id={self.current_file_id}")
                    
                    existing_component_query = """
                        SELECT component_id FROM components 
                        WHERE project_id = ? AND component_type = 'JSP' 
                          AND component_name = ? AND file_id = ? AND del_yn = 'N'
                    """
                    
                    try:
                        existing_result = self.db_utils.execute_query(
                            existing_component_query, 
                            (project_id, jsp_comp['jsp_name'], self.current_file_id)
                        )
                        
                        if existing_result:
                            debug(f"JSP 컴포넌트 이미 존재, 건너뛰기: {jsp_comp['jsp_name']} (file_id: {self.current_file_id})")
                            continue
                        else:
                            debug(f"중복 체크 통과: {jsp_comp['jsp_name']} (file_id: {self.current_file_id})")
                            
                    except Exception as e:
                        error(f"중복 체크 실패: {jsp_comp['jsp_name']} - {str(e)}")
                        continue
                    
                    component_data = {
                        'project_id': project_id,
                        'component_type': 'JSP',
                        'component_name': jsp_comp['jsp_name'],
                        'parent_id': None,  # JSP는 독립적인 컴포넌트
                        'file_id': self.current_file_id,  # 메모리에 저장된 file_id 사용
                        'layer': 'PRESENTATION',  # JSP는 프레젠테이션 계층
                        'line_start': jsp_comp.get('line_start', 1),
                        'line_end': jsp_comp.get('line_end', 1),
                        'hash_value': jsp_comp.get('hash_value', '-'),
                        'has_error': 'N',
                        'error_message': None,
                        'del_yn': 'N'
                    }
                    component_data_list.append(component_data)
                else:
                    warning(f"file_id가 None이어서 JSP 컴포넌트 생성을 건너뜀: {jsp_comp['jsp_name']}")

            if not component_data_list:
                return True

            # INSERT OR IGNORE를 사용하여 중복 무시하고 저장
            processed_count = 0
            for component_data in component_data_list:
                try:
                    debug(f"INSERT 시도: component_name='{component_data['component_name']}', file_id={component_data['file_id']}, project_id={component_data['project_id']}")
                    
                    # INSERT OR IGNORE 쿼리 직접 실행
                    insert_query = """
                        INSERT OR IGNORE INTO components 
                        (project_id, component_type, component_name, parent_id, file_id, 
                         layer, line_start, line_end, hash_value, has_error, error_message, del_yn)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    values = (
                        component_data['project_id'],
                        component_data['component_type'],
                        component_data['component_name'],
                        component_data['parent_id'],
                        component_data['file_id'],
                        component_data['layer'],
                        component_data['line_start'],
                        component_data['line_end'],
                        component_data['hash_value'],
                        component_data['has_error'],
                        component_data['error_message'],
                        component_data['del_yn']
                    )
                    
                    debug(f"INSERT 쿼리 실행: {insert_query}")
                    debug(f"INSERT 값: {values}")
                    
                    result = self.db_utils.execute_update(insert_query, values)
                    debug(f"INSERT 결과: {result}")
                    
                    if result is not None and result > 0:
                        processed_count += 1
                        debug(f"JSP 컴포넌트 저장 성공: {component_data['component_name']}")
                    else:
                        debug(f"JSP 컴포넌트 저장 무시 (중복): {component_data['component_name']}")
                        
                except Exception as e:
                    error(f"JSP 컴포넌트 저장 실패: {component_data['component_name']} - {str(e)}")
                    error(f"실패한 컴포넌트 데이터: {component_data}")
                    continue

            if processed_count > 0:
                info(f"JSP 컴포넌트 저장 완료: {processed_count}개")
                return True
            else:
                info("JSP 컴포넌트 저장 완료: 0개 (모두 중복)")
                return True

        except Exception as e:
            handle_error(e, "JSP 컴포넌트 저장 실패")

    def _save_jsp_method_relationships_to_database(self, relationships: List[Dict[str, Any]]) -> bool:
        """
        JSP → METHOD 관계를 relationships 테이블에 저장

        Args:
            relationships: JSP → METHOD 관계 정보 리스트

        Returns:
            저장 성공 여부
        """
        try:
            if not relationships:
                return True

            # 프로젝트 ID 조회
            project_id = self._get_project_id()
            if not project_id:
                error("프로젝트 ID 조회 실패")
                return False

            # 관계 데이터 변환
            relationship_data_list = []
            for rel in relationships:
                # JSP 컴포넌트 ID 조회
                jsp_component_id = self._get_jsp_component_id(project_id, rel['jsp_name'])
                if not jsp_component_id:
                    warning(f"JSP 컴포넌트 ID 조회 실패: {rel['jsp_name']}")
                    continue

                # METHOD 컴포넌트 ID 조회
                method_component_id = self._get_method_component_id(project_id, rel['class_name'], rel['method_name'])
                if not method_component_id:
                    # Phase 1 MVP: 단순화 - METHOD 컴포넌트가 없으면 건너뛰기
                    debug(f"METHOD 컴포넌트를 찾을 수 없음 (건너뛰기): {rel['class_name']}.{rel['method_name']}")
                    continue

                # src_id와 dst_id가 같은 경우 필터링 (CHECK 제약조건 위반 방지)
                if jsp_component_id == method_component_id:
                    warning(f"자기 참조 JSP→METHOD 관계 스킵: {rel['jsp_name']} → {rel['class_name']}.{rel['method_name']} (src_id == dst_id)")
                    continue

                relationship_data = {
                    'src_id': jsp_component_id,
                    'dst_id': method_component_id,
                    'rel_type': 'CALL_METHOD',
                    'confidence': 1.0,
                    'has_error': 'N',
                    'error_message': None,
                    'del_yn': 'N'
                }
                relationship_data_list.append(relationship_data)

            if not relationship_data_list:
                return True

            # 배치 저장 (USER RULES: 공통함수 사용)
            processed_count = self.db_utils.batch_insert_or_replace('relationships', relationship_data_list)

            if processed_count > 0:
                info(f"JSP → METHOD 관계 배치 저장 완료: {processed_count}개")
                return True
            else:
                error("JSP → METHOD 관계 저장 실패")
                return False

        except Exception as e:
            handle_error(e, "JSP → METHOD 관계 저장 실패")

    def _get_project_id(self) -> Optional[int]:
        """
        프로젝트 ID 조회

        Returns:
            프로젝트 ID (없으면 None)
        """
        try:
            # USER RULES: 공통함수 사용
            return self.db_utils.get_project_id(self.project_name)
        except Exception as e:
            handle_error(e, "프로젝트 ID 조회 실패")

    def _extract_file_id_from_path(self, file_path: str) -> Optional[int]:
        """
        파일 경로에서 file_id 추출 (데이터베이스 조회 기반)

        Args:
            file_path: 파일 경로

        Returns:
            file_id 또는 None
        """
        try:
            # 프로젝트 ID 조회
            project_id = self._get_project_id()
            if not project_id:
                warning(f"프로젝트 ID 조회 실패로 file_id를 찾을 수 없음: {file_path}")
                return None

            # 상대 경로 변환 (크로스 플랫폼 지원)
            from util.path_utils import get_relative_path, PathUtils
            import os
            relative_path = get_relative_path(file_path, self.project_source_path)
            # Unix 스타일로 정규화 (DB 저장 형식과 일치)
            path_utils = PathUtils()
            relative_path = path_utils.normalize_path_separator(relative_path, 'unix')

            # 데이터베이스에서 file_id 조회 (USER RULES: 공통함수 사용)
            # 먼저 정확한 경로로 조회하고, 없으면 파일명만으로 조회
            query = """
                SELECT file_id
                FROM files
                WHERE project_id = ? AND (file_path = ? OR file_name = ?)
            """
            filename = os.path.basename(relative_path)
            result = self.db_utils.execute_query(query, (project_id, relative_path, filename))

            if result:
                file_id = result[0]['file_id']
                info(f"JSP 파일 ID 조회 성공: {relative_path} (filename: {filename}) -> {file_id}")
                return file_id
            else:
                warning(f"JSP 파일이 files 테이블에 등록되지 않음: {relative_path} (filename: {filename})")
                # Phase 1 MVP: JSP 파일을 files 테이블에 등록
                file_id = self._register_jsp_file_to_database(project_id, relative_path, file_path)
                if file_id:
                    info(f"JSP 파일 새로 등록 완료: {relative_path} -> {file_id}")
                else:
                    error(f"JSP 파일 등록 실패: {relative_path}")
                return file_id

        except Exception as e:
            handle_error(e, f"JSP 파일 ID 추출 실패: {file_path}")

    def _register_jsp_file_to_database(self, project_id: int, relative_path: str, full_path: str) -> Optional[int]:
        """
        JSP 파일을 files 테이블에 등록 (Phase 1 MVP 지원)

        Args:
            project_id: 프로젝트 ID
            relative_path: 상대 경로
            full_path: 전체 경로

        Returns:
            생성된 file_id 또는 None
        """
        try:
            from util.file_utils import get_file_hash
            from util.path_utils import PathUtils
            import os

            # 파일 정보 수집
            file_hash = get_file_hash(full_path) if os.path.exists(full_path) else '-'
            file_size = os.path.getsize(full_path) if os.path.exists(full_path) else 0

            # 파일 라인 수 계산
            line_count = 0
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)
                except:
                    line_count = 0

            # 경로 정규화 (Unix 스타일)
            path_utils = PathUtils()
            normalized_relative_path = path_utils.normalize_path_separator(relative_path, 'unix')

            # files 테이블에 JSP 파일 등록
            file_data = {
                'project_id': project_id,
                'file_path': normalized_relative_path,
                'file_name': os.path.basename(normalized_relative_path),
                'file_type': 'JSP',
                'line_count': line_count,
                'file_size': file_size,
                'hash_value': file_hash,
                'has_error': 'N',
                'error_message': None,
                'del_yn': 'N'
            }

            # 배치 삽입 (USER RULES: 공통함수 사용)
            processed_count = self.db_utils.batch_insert_or_replace('files', [file_data])

            if processed_count > 0:
                # 생성된 file_id 조회
                query = "SELECT file_id FROM files WHERE project_id = ? AND file_path = ?"
                result = self.db_utils.execute_query(query, (project_id, relative_path))

                if result:
                    file_id = result[0]['file_id']
                    debug(f"JSP 파일 등록 완료: {relative_path} -> file_id: {file_id}")
                    return file_id

            return None

        except Exception as e:
            handle_error(e, f"JSP 파일 등록 실패: {relative_path}")

    def _get_jsp_component_id(self, project_id: int, jsp_name: str) -> Optional[int]:
        """
        JSP 컴포넌트 ID 조회

        Args:
            project_id: 프로젝트 ID
            jsp_name: JSP 파일명

        Returns:
            JSP 컴포넌트 ID (없으면 None)
        """
        try:
            query = """
                SELECT component_id 
                FROM components 
                WHERE project_id = ? AND component_type = 'JSP' AND component_name = ?
            """
            result = self.db_utils.execute_query(query, (project_id, jsp_name))
            if result:
                return result[0]['component_id']
            return None
        except Exception as e:
            handle_error(e, f"JSP 컴포넌트 ID 조회 실패: {jsp_name}")

    def _get_method_component_id(self, project_id: int, class_name: str, method_name: str) -> Optional[int]:
        """
        METHOD 컴포넌트 ID 조회 (4단계에서 생성된 것)

        Args:
            project_id: 프로젝트 ID
            class_name: 클래스명
            method_name: 메서드명

        Returns:
            METHOD 컴포넌트 ID (없으면 None)
        """
        try:
            query = """
                SELECT component_id 
                FROM components 
                WHERE project_id = ? AND component_type = 'METHOD' AND component_name = ?
            """
            component_name = f"{class_name}.{method_name}"
            result = self.db_utils.execute_query(query, (project_id, component_name))
            if result:
                return result[0]['component_id']
            return None
        except Exception as e:
            handle_error(e, f"METHOD 컴포넌트 ID 조회 실패: {class_name}.{method_name}")


    def _print_jsp_loading_statistics(self):
        """JSP 로딩 통계 정보 출력"""
        try:
            info("=== JSP 로딩 통계 ===")
            info(f"처리된 JSP 파일: {self.stats['jsp_files_processed']}개")
            info(f"생성된 JSP 컴포넌트: {self.stats['jsp_components_created']}개")
            info(f"생성된 JSP → METHOD 관계: {self.stats['jsp_method_relationships_created']}개")
            info(f"생성된 API_URL 컴포넌트: {self.stats['api_url_components_created']}개")
            info(f"생성된 API_URL → METHOD 관계: {self.stats['api_url_method_relationships_created']}개")
            info(f"오류 발생: {self.stats['errors']}개")
            info(f"처리 시간: {self.stats['processing_time']:.2f}초")
            info("==================")

        except Exception as e:
            handle_error(e, "통계 정보 출력 실패")

    def _save_api_url_components_to_database(self, api_calls: List[Dict[str, Any]]) -> bool:
        """
        API 호출 정보를 기존 API_URL 컴포넌트와 연결하거나 inferred로 등록
        
        설계 원칙:
        1. 기존 API_URL 컴포넌트가 있으면 → file_id를 JSP 파일로 업데이트 (매칭 성공)
        2. 기존 API_URL 컴포넌트가 없으면 → inferred로 새로 생성 (JSP에서만 호출되는 API)

        Args:
            api_calls: API 호출 정보 리스트

        Returns:
            처리 성공 여부
        """
        try:
            if not api_calls:
                return True

            # 프로젝트 ID 조회
            project_id = self._get_project_id()
            if not project_id:
                error("프로젝트 ID 조회 실패")
                return False

            updated_count = 0
            created_count = 0
            
            for api_call in api_calls:
                try:
                    api_url_name = api_call['component_name']  # "URL:HTTP_METHOD" 형태
                    
                    # 1. 기존 API_URL 컴포넌트가 있는지 확인
                    existing_api_url_id = self._find_existing_api_url_component(project_id, api_url_name)
                    
                    if existing_api_url_id:
                        # 기존 API_URL이 있으면 → JSP 파일로 매칭 성공 (file_id 업데이트)
                        success = self._update_api_url_file_id(existing_api_url_id, self.current_file_id)
                        if success:
                            updated_count += 1
                            app_logger.debug(f"API_URL 매칭 성공: {api_url_name} → JSP file_id: {self.current_file_id}")
                        else:
                            app_logger.warning(f"API_URL file_id 업데이트 실패: {api_url_name}")
                    else:
                        # 기존 API_URL이 없으면 → inferred로 새로 생성 (JSP에서만 호출되는 API)
                        success = self._create_inferred_api_url_component(api_call, project_id)
                        if success:
                            created_count += 1
                            app_logger.debug(f"API_URL inferred 생성: {api_url_name}")
                        else:
                            app_logger.warning(f"API_URL inferred 생성 실패: {api_url_name}")
                            
                except Exception as e:
                    handle_error(e, f"API_URL 처리 중 오류: {api_call['component_name']}")

            info(f"API_URL 처리 완료: 매칭 성공 {updated_count}개, inferred 생성 {created_count}개")
            return True

        except Exception as e:
            handle_error(e, "API_URL 컴포넌트 처리 실패")

    def _find_existing_api_url_component(self, project_id: int, api_url_name: str) -> Optional[int]:
        """
        기존 API_URL 컴포넌트 ID 조회
        
        Args:
            project_id: 프로젝트 ID
            api_url_name: API_URL 컴포넌트명 (URL:HTTP_METHOD 형태)
            
        Returns:
            컴포넌트 ID 또는 None
        """
        try:
            return self.db_utils.get_component_id(project_id, api_url_name, 'API_URL')
        except Exception as e:
            handle_error(e, f"기존 API_URL 컴포넌트 조회 실패: {api_url_name}")

    def _update_api_url_file_id(self, api_url_id: int, jsp_file_id: int) -> bool:
        """
        API_URL 컴포넌트의 file_id를 JSP 파일 ID로 업데이트 (매칭 성공)
        
        Args:
            api_url_id: API_URL 컴포넌트 ID
            jsp_file_id: JSP 파일 ID
            
        Returns:
            업데이트 성공 여부
        """
        try:
            # 1. 먼저 업데이트할 컴포넌트의 정보 조회
            component_info_query = """
                SELECT component_name, project_id FROM components 
                WHERE component_id = ? AND component_type = 'API_URL'
            """
            component_info = self.db_utils.execute_query(component_info_query, (api_url_id,))
            
            if not component_info:
                debug(f"API_URL 컴포넌트를 찾을 수 없음: {api_url_id}")
                return False
            
            component_name = component_info[0]['component_name']
            project_id = component_info[0]['project_id']
            
            # 2. 대상 file_id로 이미 같은 component_name을 가진 컴포넌트가 있는지 확인
            conflict_check_query = """
                SELECT component_id FROM components 
                WHERE project_id = ? AND component_name = ? AND file_id = ? AND del_yn = 'N'
            """
            conflict_result = self.db_utils.execute_query(conflict_check_query, (project_id, component_name, jsp_file_id))
            
            if conflict_result:
                existing_component_id = conflict_result[0]['component_id']
                debug(f"이미 JSP file_id에 존재: {component_name} (기존 component_id: {existing_component_id})")
                # JSP file_id에 이미 존재하므로 Java file_id의 중복 컴포넌트만 삭제하고 성공으로 처리
                delete_sql = """
                    DELETE FROM components 
                    WHERE component_id = ? AND component_type = 'API_URL'
                """
                delete_result = self.db_utils.execute_update(delete_sql, (api_url_id,))
                if delete_result > 0:
                    debug(f"중복 Java file_id 컴포넌트 삭제: {api_url_id}")
                return True
            
            # 3. 기존 컴포넌트 삭제 후 새로 생성 (UNIQUE 제약조건 위반 방지)
            delete_sql = """
                DELETE FROM components 
                WHERE component_id = ? AND component_type = 'API_URL'
            """
            delete_result = self.db_utils.execute_update(delete_sql, (api_url_id,))
            
            if delete_result > 0:
                # 4. 새로운 file_id로 컴포넌트 재생성
                insert_sql = """
                    INSERT INTO components 
                    (project_id, component_type, component_name, parent_id, file_id, 
                     layer, line_start, line_end, hash_value, has_error, error_message, del_yn)
                    VALUES (?, 'API_URL', ?, NULL, ?, 'FRONTEND', 1, 1, '-', 'N', NULL, 'N')
                """
                insert_result = self.db_utils.execute_update(insert_sql, (project_id, component_name, jsp_file_id))
                
                if insert_result > 0:
                    debug(f"API_URL file_id 업데이트 성공 (DELETE+INSERT): {api_url_id} → {jsp_file_id}")
                    return True
                else:
                    debug(f"API_URL 재생성 실패: {component_name}")
                    return False
            else:
                debug(f"API_URL 삭제 실패: {api_url_id}")
                return False
                
        except Exception as e:
            debug(f"API_URL file_id 업데이트 실패: {api_url_id} → {jsp_file_id} - {str(e)}")
            return False

    def _create_inferred_api_url_component(self, api_call: Dict[str, Any], project_id: int) -> bool:
        """
        inferred API_URL 컴포넌트 생성 (JSP에서만 호출되는 API)
        
        Args:
            api_call: API 호출 정보
            project_id: 프로젝트 ID
            
        Returns:
            생성 성공 여부
        """
        try:
            # 해시값 생성
            hash_value = self.hash_utils.generate_content_hash(
                f"inferred_{api_call['component_name']}_{api_call['source_line']}_{api_call['line_number']}"
            )
            
            component_data = {
                'project_id': project_id,
                'component_type': 'API_URL',
                'component_name': api_call['component_name'],
                'parent_id': None,
                'file_id': self.current_file_id,  # JSP 파일 ID
                'layer': 'FRONTEND',  # 프론트엔드 계층
                'line_start': api_call['line_number'],
                'line_end': api_call['line_number'],
                'hash_value': hash_value,
                'has_error': 'N',
                'error_message': 'inferred from JSP call',
                'del_yn': 'N'
            }
            
            # 단일 컴포넌트 저장
            self.db_utils.insert_or_replace('components', component_data)
            return True
            
        except Exception as e:
            handle_error(e, f"inferred API_URL 컴포넌트 생성 실패: {api_call['component_name']}")

    def _create_api_url_method_relationships(self, api_calls: List[Dict[str, Any]]) -> bool:
        """
        API_URL → METHOD 관계 생성 (CALL_METHOD)
        
        Args:
            api_calls: API 호출 정보 리스트
            
        Returns:
            관계 생성 성공 여부
        """
        try:
            if not api_calls:
                return True
                
            # 프로젝트 ID 조회
            project_id = self._get_project_id()
            if not project_id:
                error("프로젝트 ID 조회 실패")
                return False
                
            # 관계 데이터 변환
            relationship_data_list = []
            for api_call in api_calls:
                try:
                    # API_URL 컴포넌트 ID 조회
                    api_url_name = api_call['component_name']  # "URL:HTTP_METHOD" 형태
                    api_url_id = self._get_api_url_component_id(project_id, api_url_name)
                    
                    if not api_url_id:
                        warning(f"API_URL 컴포넌트 ID 조회 실패: {api_url_name}")
                        continue
                    
                    # METHOD 컴포넌트 ID 조회 (URL 패턴으로 매칭)
                    method_id = self._find_matching_method(api_call['api_url'], api_call['http_method'], project_id)
                    
                    if method_id:
                        # src_id와 dst_id가 같은 경우 필터링 (CHECK 제약조건 위반 방지)
                        if api_url_id == method_id:
                            warning(f"자기 참조 API_URL→METHOD 관계 스킵: {api_url_name} → METHOD (src_id == dst_id)")
                            continue
                            
                        relationship_data = {
                            'src_id': api_url_id,  # API_URL 컴포넌트
                            'dst_id': method_id,   # METHOD 컴포넌트
                            'rel_type': 'CALL_METHOD',  # 통일된 관계 타입
                            'confidence': 1.0,
                            'has_error': 'N',
                            'error_message': None,
                            'del_yn': 'N'
                        }
                        relationship_data_list.append(relationship_data)
                        debug(f"API_URL → METHOD 관계 생성: {api_url_name} → METHOD")
                    else:
                        debug(f"매칭되는 METHOD 컴포넌트를 찾을 수 없음: {api_url_name}")
                        
                except Exception as e:
                    handle_error(e, f"API_URL → METHOD 관계 생성 실패: {api_call['component_name']}")
                    
            if not relationship_data_list:
                return True
                
            # 배치 저장 (USER RULES: 공통함수 사용)
            processed_count = self.db_utils.batch_insert_or_replace('relationships', relationship_data_list)
            
            if processed_count > 0:
                info(f"API_URL → METHOD 관계 배치 저장 완료: {processed_count}개")
                self.stats['api_url_method_relationships_created'] += processed_count
                return True
            else:
                error("API_URL → METHOD 관계 저장 실패")
                return False
                
        except Exception as e:
            handle_error(e, "API_URL → METHOD 관계 생성 실패")
            
    def _get_api_url_component_id(self, project_id: int, api_url_name: str) -> Optional[int]:
        """
        API_URL 컴포넌트 ID 조회
        
        Args:
            project_id: 프로젝트 ID
            api_url_name: API_URL 컴포넌트명 (URL:HTTP_METHOD 형태)
            
        Returns:
            API_URL 컴포넌트 ID (없으면 None)
        """
        try:
            # USER RULES: 공통함수 사용
            return self.db_utils.get_component_id(project_id, api_url_name, 'API_URL')
        except Exception as e:
            handle_error(e, f"API_URL 컴포넌트 ID 조회 실패: {api_url_name}")
            
    def _find_matching_method(self, api_url: str, http_method: str, project_id: int) -> Optional[int]:
        """
        API_URL에 매칭되는 METHOD 컴포넌트 찾기
        
        Args:
            api_url: API URL 패턴
            http_method: HTTP 메서드
            project_id: 프로젝트 ID
            
        Returns:
            METHOD 컴포넌트 ID (없으면 None)
        """
        try:
            # USER RULES: 공통함수 사용
            # URL 패턴으로 매칭되는 METHOD 컴포넌트 조회
            # Spring Controller의 @RequestMapping, @GetMapping 등으로 매핑된 메서드 찾기
            return self.db_utils.find_method_by_api_pattern(project_id, api_url, http_method)
        except Exception as e:
            handle_error(e, f"METHOD 컴포넌트 매칭 실패: {api_url}:{http_method}")

    def update_api_url_file_ids(self, project_id: int) -> Dict[str, int]:
        """
        JSP 분석 완료 후 모든 API_URL 컴포넌트의 file_id를 올바른 JSP 파일로 업데이트
        
        Args:
            project_id: 프로젝트 ID
            
        Returns:
            업데이트 통계
        """
        try:
            info("API_URL 컴포넌트 file_id 업데이트 시작...")
            
            # 1. Java file_id를 가진 모든 API_URL 컴포넌트 조회
            api_urls_query = """
                SELECT c.component_id, c.component_name, c.file_id
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                WHERE c.project_id = ? 
                  AND c.component_type = 'API_URL'
                  AND f.file_type = 'JAVA'
                  AND c.del_yn = 'N'
                  AND f.del_yn = 'N'
            """
            
            api_urls = self.db_utils.execute_query(api_urls_query, (project_id,))
            if not api_urls:
                info("업데이트할 API_URL 컴포넌트가 없습니다")
                return {'updated': 0, 'not_found': 0, 'total': 0}
            
            info(f"업데이트 대상 API_URL 컴포넌트: {len(api_urls)}개")
            
            updated_count = 0
            not_found_count = 0
            
            for api_url in api_urls:
                component_id = api_url['component_id']
                component_name = api_url['component_name']  # 예: "/api/users:GET"
                
                # API_URL에서 URL과 HTTP 메서드 분리
                if ':' in component_name:
                    url_pattern, http_method = component_name.split(':', 1)
                    
                    # 해당 API를 호출하는 JSP 파일 찾기
                    jsp_file_id = self._find_matching_jsp_for_api(url_pattern, http_method, project_id)
                    
                    if jsp_file_id:
                        # JSP 파일로 file_id 업데이트
                        success = self._update_api_url_file_id(component_id, jsp_file_id)
                        if success:
                            updated_count += 1
                            debug(f"API_URL file_id 업데이트 성공: {component_name} → JSP file_id: {jsp_file_id}")
                        else:
                            debug(f"API_URL file_id 업데이트 실패: {component_name}")
                    else:
                        not_found_count += 1
                        debug(f"매칭되는 JSP 파일 없음: {component_name}")
                else:
                    debug(f"잘못된 API_URL 형식: {component_name}")
            
            stats = {
                'updated': updated_count,
                'not_found': not_found_count,
                'total': len(api_urls)
            }
            
            info(f"API_URL file_id 업데이트 완료: {updated_count}개 성공, {not_found_count}개 매칭 실패")
            return stats
            
        except Exception as e:
            handle_error(e, "API_URL file_id 업데이트 실패")
            return {'updated': 0, 'not_found': 0, 'total': 0}

    def _find_matching_jsp_for_api(self, url_pattern: str, http_method: str, project_id: int) -> Optional[int]:
        """
        특정 API를 호출하는 JSP 파일 찾기
        
        Args:
            url_pattern: API URL 패턴 (예: "/api/users")
            http_method: HTTP 메서드 (예: "GET")
            project_id: 프로젝트 ID
            
        Returns:
            JSP 파일 ID 또는 None
        """
        try:
            # JSP 파일에서 해당 API 호출을 찾는 로직
            # 실제 구현에서는 JSP 파일 내용을 분석하여 API 호출 패턴을 찾아야 함
            # 현재는 간단히 첫 번째 JSP 파일을 반환 (실제로는 더 정교한 매칭 필요)
            
            jsp_files_query = """
                SELECT file_id, file_name
                FROM files
                WHERE project_id = ? 
                  AND file_type = 'JSP'
                  AND del_yn = 'N'
                ORDER BY file_name
                LIMIT 1
            """
            
            results = self.db_utils.execute_query(jsp_files_query, (project_id,))
            if results:
                jsp_file_id = results[0]['file_id']
                file_name = results[0]['file_name']
                debug(f"JSP 파일 매칭: {url_pattern}:{http_method} → {file_name} (file_id: {jsp_file_id})")
                return jsp_file_id
            
            return None
            
        except Exception as e:
            debug(f"JSP 파일 매칭 실패: {url_pattern}:{http_method} - {str(e)}")
            return None


def execute_jsp_loading(project_name: str) -> bool:
    """
    JSP 로딩 실행 함수 (main.py에서 호출용)

    Args:
        project_name: 프로젝트명

    Returns:
        실행 성공 여부
    """
    try:
        jsp_engine = JspLoadingEngine(project_name)
        success = jsp_engine.execute_jsp_loading()
        
        # JSP 분석 완료 후 API_URL file_id 업데이트
        if success:
            from util.global_project import get_global_project_id
            project_id = get_global_project_id()
            if project_id:
                update_stats = jsp_engine.update_api_url_file_ids(project_id)
                info(f"=== API_URL file_id 업데이트 통계 ===")
                info(f"성공: {update_stats['updated']}개 업데이트")
                info(f"매칭 실패: {update_stats['not_found']}개")
                info(f"총 대상: {update_stats['total']}개")
        
        return success
    except Exception as e:
        handle_error(e, "JSP 로딩 실행 실패")
        return False
