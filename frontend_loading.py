"""
범용 프론트엔드 로딩 모듈
- JSP, JSX, Vue, TS, JS, HTML 파일에서 컴포넌트 추출 및 관계 분석
- 기존 JSP 로딩 엔진을 범용화하여 모든 프론트엔드 파일 타입 지원
- 메모리 최적화 (스트리밍 처리)
- 데이터베이스 저장 및 통계 관리

USER RULES:
- 하드코딩 금지: path_utils.get_parser_config_path("frontend") 사용 (크로스플랫폼 대응)
- 파싱 에러 처리: has_error='Y', error_message 저장 후 계속 실행
- 시스템 에러 처리: handle_error() 공통함수 사용
- 공통함수 사용: util 모듈 활용
"""

import os
from typing import List, Dict, Any, Optional
from util import (
    DatabaseUtils, PathUtils, HashUtils, ValidationUtils,
    app_logger, info, error, debug, warning, handle_error,
    get_project_source_path, get_project_metadata_db_path
)
from parser.frontend_parser import FrontendParser


class FrontendLoadingEngine:
    """범용 프론트엔드 로딩 엔진 - JSP, JSX, Vue, TS, JS, HTML 지원"""

    def __init__(self, project_name: str):
        """
        프론트엔드 로딩 엔진 초기화

        Args:
            project_name: 프로젝트명
        """
        self.project_name = project_name
        self.project_source_path = get_project_source_path(project_name)
        self.metadata_db_path = get_project_metadata_db_path(project_name)
        self.db_utils = None

        # 프론트엔드 파서 초기화 (USER RULES: 공통함수 사용)
        self.frontend_parser = FrontendParser(project_name=project_name)
        
        # HashUtils 초기화
        self.hash_utils = HashUtils()

        # 현재 처리 중인 파일의 file_id (메모리 최적화)
        self.current_file_id = None

        # 통계 정보
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'error_files': 0,
            'jsp_files': 0,
            'jsx_files': 0,
            'vue_files': 0,
            'ts_files': 0,
            'tsx_files': 0,
            'js_files': 0,
            'html_files': 0,
            'components_created': 0,
            'api_calls_found': 0,
            'relationships_created': 0
        }

        # 지원하는 프론트엔드 파일 확장자
        self.supported_extensions = {
            '.jsp': 'JSP',
            '.jsx': 'JSX', 
            '.vue': 'VUE',
            '.ts': 'TS',
            '.tsx': 'TSX',
            '.js': 'JS',
            '.html': 'HTML'
        }

        info(f"프론트엔드 로딩 엔진 초기화 완료: {project_name}")

    def execute_frontend_loading(self) -> bool:
        """
        프론트엔드 파일 로딩 실행

        Returns:
            bool: 성공 여부
        """
        try:
            info("=== 프론트엔드 파일 로딩 시작 ===")
            
            # 데이터베이스 연결 초기화
            self.db_utils = DatabaseUtils(self.metadata_db_path)
            
            # 프로젝트 ID 조회
            project_id = self._get_project_id()
            if not project_id:
                error("프로젝트 ID를 찾을 수 없음")
                return False
            
            # 프론트엔드 파일 목록 조회
            frontend_files = self._get_frontend_files(project_id)
            if not frontend_files:
                info("처리할 프론트엔드 파일이 없음")
                return True
            
            self.stats['total_files'] = len(frontend_files)
            info(f"총 {len(frontend_files)}개 프론트엔드 파일 발견")
            
            # 파일 타입별 통계
            file_type_stats = {}
            for file_info in frontend_files:
                file_type = file_info['file_type']
                file_type_stats[file_type] = file_type_stats.get(file_type, 0) + 1
            
            for file_type, count in file_type_stats.items():
                info(f"{file_type} 파일: {count}개")
                self.stats[f'{file_type.lower()}_files'] = count
            
            # 각 프론트엔드 파일 처리
            for file_info in frontend_files:
                try:
                    self._process_frontend_file(file_info, project_id)
                    self.stats['processed_files'] += 1
                except Exception as e:
                    self.stats['error_files'] += 1
                    error(f"프론트엔드 파일 처리 실패: {file_info['file_path']} - {str(e)}")
                    continue
            
            # 통계 출력
            self._print_statistics()
            
            info("=== 프론트엔드 파일 로딩 완료 ===")
            return True
            
        except Exception as e:
            handle_error(e, "프론트엔드 파일 로딩 실행 실패")

    def _get_project_id(self) -> Optional[int]:
        """프로젝트 ID 조회"""
        try:
            query = "SELECT project_id FROM projects WHERE project_name = ? AND del_yn = 'N'"
            result = self.db_utils.execute_query(query, (self.project_name,))
            if result:
                return result[0]['project_id']
            return None
        except Exception as e:
            handle_error(e, "프로젝트 ID 조회 실패")

    def _get_frontend_files(self, project_id: int) -> List[Dict[str, Any]]:
        """프론트엔드 파일 목록 조회"""
        try:
            # 지원하는 프론트엔드 파일 타입들
            frontend_types = list(self.supported_extensions.values())
            placeholders = ','.join(['?' for _ in frontend_types])
            
            query = f"""
                SELECT file_id, file_name, file_path, file_type
                FROM files 
                WHERE project_id = ? 
                  AND file_type IN ({placeholders})
                  AND del_yn = 'N'
                ORDER BY file_type, file_name
            """
            
            params = [project_id] + frontend_types
            result = self.db_utils.execute_query(query, params)
            
            debug(f"프론트엔드 파일 조회: {len(result)}개 발견")
            return result
            
        except Exception as e:
            handle_error(e, "프론트엔드 파일 목록 조회 실패")

    def _process_frontend_file(self, file_info: Dict[str, Any], project_id: int) -> None:
        """개별 프론트엔드 파일 처리"""
        try:
            file_id = file_info['file_id']
            file_name = file_info['file_name']
            file_path = file_info['file_path']
            file_type = file_info['file_type']
            
            self.current_file_id = file_id
            
            debug(f"프론트엔드 파일 처리 시작: {file_name} (타입: {file_type})")
            
            # 파일 경로 구성
            full_file_path = os.path.join(self.project_source_path, file_path)
            if not os.path.exists(full_file_path):
                warning(f"파일이 존재하지 않음: {full_file_path}")
                return
            
            # 프론트엔드 파서로 파일 분석
            parse_result = self.frontend_parser.parse_frontend_file(full_file_path, file_type)
            
            if parse_result['has_error'] == 'Y':
                warning(f"파싱 에러: {file_name} - {parse_result['error_message']}")
                return
            
            # 컴포넌트 저장
            if parse_result['components']:
                self._save_frontend_components_to_database(
                    parse_result['components'], project_id, file_type
                )
            
            # API 호출 관계 저장
            if parse_result['api_calls']:
                self._save_api_call_relationships_to_database(
                    parse_result['api_calls'], project_id, file_type
                )
            
            self.stats['api_calls_found'] += len(parse_result['api_calls'])
            self.stats['components_created'] += len(parse_result['components'])
            
            debug(f"프론트엔드 파일 처리 완료: {file_name}")
            
        except Exception as e:
            handle_error(e, f"프론트엔드 파일 처리 실패: {file_info}")

    def _save_frontend_components_to_database(self, components: List[Dict[str, Any]], 
                                            project_id: int, file_type: str) -> None:
        """프론트엔드 컴포넌트를 데이터베이스에 저장"""
        try:
            debug(f"프론트엔드 컴포넌트 저장 시작: {len(components)}개 (타입: {file_type})")
            
            # 스키마정의서에 따르면 JSP/JSX/Vue 등 프론트엔드 파일은 files 테이블에만 저장
            # components 테이블에는 API_URL 컴포넌트만 저장
            # JSP 파일의 경우 JSP 컴포넌트를 components 테이블에 저장 (기존 JSP 로딩 방식과 동일)
            if file_type.upper() == 'JSP':
                for component in components:
                    # 중복 체크
                    check_query = """
                        SELECT component_id FROM components 
                        WHERE project_id = ? AND component_name = ? AND file_id = ? AND del_yn = 'N'
                    """
                    existing = self.db_utils.execute_query(
                        check_query, (project_id, component['component_name'], self.current_file_id)
                    )
                    
                    if existing:
                        debug(f"JSP 컴포넌트 이미 존재: {component['component_name']}")
                        continue
                    
                    # JSP 컴포넌트 데이터 준비
                    component_data = {
                        'project_id': project_id,
                        'file_id': self.current_file_id,
                        'component_name': component['component_name'],
                        'component_type': 'JSP',
                        'parent_id': None,
                        'layer': 'FRONTEND',
                        'line_start': component.get('line_start', 1),
                        'line_end': component.get('line_end', 1),
                        'hash_value': component.get('hash_value', '-'),
                        'has_error': 'N',
                        'error_message': None,
                        'del_yn': 'N'
                    }
                    
                    # 상세 로그 출력
                    debug(f"=== JSP 컴포넌트 저장 시도 ===")
                    debug(f"component_name: {component['component_name']}")
                    debug(f"project_id: {project_id}")
                    debug(f"file_id: {self.current_file_id}")
                    debug(f"component_data: {component_data}")
                    
                    # 참조 데이터 존재 여부 사전 확인 및 로그 출력
                    info(f"=== JSP 컴포넌트 저장 전 참조 데이터 확인 ===")
                    info(f"컴포넌트명: {component['component_name']}")
                    info(f"project_id: {project_id}")
                    info(f"file_id: {self.current_file_id}")
                    
                    self._verify_reference_data_before_insert(project_id, self.current_file_id)
                    
                    # INSERT OR IGNORE 사용하여 중복 방지
                    insert_query = """
                        INSERT OR IGNORE INTO components 
                        (project_id, file_id, component_name, component_type, parent_id, 
                         layer, line_start, line_end, hash_value, has_error, error_message, del_yn)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    values = (
                        component_data['project_id'],
                        component_data['file_id'],
                        component_data['component_name'],
                        component_data['component_type'],
                        component_data['parent_id'],
                        component_data['layer'],
                        component_data['line_start'],
                        component_data['line_end'],
                        component_data['hash_value'],
                        component_data['has_error'],
                        component_data['error_message'],
                        component_data['del_yn']
                    )
                    
                    debug(f"=== JSP 컴포넌트 저장 시도 ===")
                    debug(f"실행할 쿼리: {insert_query}")
                    debug(f"실행할 값들: {values}")
                    
                    result = self.db_utils.execute_update(insert_query, values)
                    if result > 0:
                        debug(f"JSP 컴포넌트 저장 성공: {component['component_name']}")
            else:
                # 다른 프론트엔드 파일 타입은 스키마정의서에 따라 components 테이블에 저장하지 않음
                debug(f"스키마정의서 준수: {file_type} 파일은 files 테이블에만 저장, components 테이블에는 API_URL만 저장")
            
        except Exception as e:
            handle_error(e, "프론트엔드 컴포넌트 저장 실패")

    def _verify_reference_data_before_insert(self, project_id: int, file_id: int) -> None:
        """컴포넌트 삽입 전 참조 데이터 존재 여부 확인"""
        try:
            # project_id 존재 여부 확인
            project_query = "SELECT COUNT(*) FROM projects WHERE project_id = ? AND del_yn = 'N'"
            project_result = self.db_utils.execute_query(project_query, (project_id,))
            project_exists = project_result[0]['COUNT(*)'] > 0 if project_result else False
            
            debug(f"프로젝트 존재 여부 확인: project_id={project_id}, 존재={project_exists}")
            
            if not project_exists:
                # 전체 프로젝트 목록 조회
                all_projects_query = "SELECT project_id, project_name FROM projects WHERE del_yn = 'N'"
                all_projects = self.db_utils.execute_query(all_projects_query)
                debug(f"사용 가능한 프로젝트 목록: {all_projects}")
            
            # file_id 존재 여부 확인
            file_query = "SELECT COUNT(*) FROM files WHERE file_id = ? AND del_yn = 'N'"
            file_result = self.db_utils.execute_query(file_query, (file_id,))
            file_exists = file_result[0]['COUNT(*)'] > 0 if file_result else False
            
            debug(f"파일 존재 여부 확인: file_id={file_id}, 존재={file_exists}")
            
            if not file_exists:
                # 최근 파일 목록 조회
                recent_files_query = """
                    SELECT file_id, file_name, file_type 
                    FROM files 
                    WHERE del_yn = 'N' 
                    ORDER BY file_id DESC 
                    LIMIT 10
                """
                recent_files = self.db_utils.execute_query(recent_files_query)
                debug(f"최근 파일 목록: {recent_files}")
                
        except Exception as e:
            debug(f"참조 데이터 확인 실패: {str(e)}")

    def _verify_relationship_references(self, src_id: int, dst_id: int) -> None:
        """관계 생성 전 참조 데이터 존재 여부 확인"""
        try:
            # src_id 존재 여부 확인
            src_query = "SELECT COUNT(*) FROM components WHERE component_id = ? AND del_yn = 'N'"
            src_result = self.db_utils.execute_query(src_query, (src_id,))
            src_exists = src_result[0]['COUNT(*)'] > 0 if src_result else False
            
            debug(f"소스 컴포넌트 존재 여부 확인: src_id={src_id}, 존재={src_exists}")
            
            if not src_exists:
                # 최근 컴포넌트 목록 조회
                recent_components_query = """
                    SELECT component_id, component_name, component_type 
                    FROM components 
                    WHERE del_yn = 'N' 
                    ORDER BY component_id DESC 
                    LIMIT 10
                """
                recent_components = self.db_utils.execute_query(recent_components_query)
                debug(f"최근 컴포넌트 목록: {recent_components}")
            
            # dst_id 존재 여부 확인
            dst_query = "SELECT COUNT(*) FROM components WHERE component_id = ? AND del_yn = 'N'"
            dst_result = self.db_utils.execute_query(dst_query, (dst_id,))
            dst_exists = dst_result[0]['COUNT(*)'] > 0 if dst_result else False
            
            debug(f"대상 컴포넌트 존재 여부 확인: dst_id={dst_id}, 존재={dst_exists}")
            
            if not dst_exists:
                # 최근 컴포넌트 목록 조회
                recent_components_query = """
                    SELECT component_id, component_name, component_type 
                    FROM components 
                    WHERE del_yn = 'N' 
                    ORDER BY component_id DESC 
                    LIMIT 10
                """
                recent_components = self.db_utils.execute_query(recent_components_query)
                debug(f"최근 컴포넌트 목록: {recent_components}")
                
        except Exception as e:
            debug(f"관계 참조 데이터 확인 실패: {str(e)}")

    def _save_api_call_relationships_to_database(self, api_calls: List[Dict[str, Any]], 
                                               project_id: int, file_type: str) -> None:
        """API 호출 관계를 데이터베이스에 저장"""
        try:
            debug(f"API 호출 관계 저장 시작: {len(api_calls)}개")
            
            # 현재 파일에서 사용된 프레임워크들 수집
            frameworks_in_file = set()
            
            for api_call in api_calls:
                # 프레임워크 정보 수집
                framework = api_call.get('framework')
                if framework:
                    frameworks_in_file.add(framework.lower())
                
                # API_URL 컴포넌트 찾기 또는 생성
                api_url_id = self._find_or_create_api_url_component(
                    api_call, project_id, file_type
                )
                
                if api_url_id:
                    # JSP 파일의 경우 JSP 컴포넌트와 관계 생성
                    if file_type.upper() == 'JSP':
                        jsp_component_id = self._find_frontend_component_id(
                            api_call['file_name'], project_id
                        )
                        
                        if jsp_component_id:
                            # JSP 컴포넌트와 API_URL 관계 생성
                            self._create_jsp_api_relationship(
                                jsp_component_id, api_url_id, api_call
                            )
                    
                    # API_URL과 METHOD 관계 생성 (기존 JSP 로딩 방식과 동일)
                    self._create_api_method_relationship(api_url_id, api_call)
            
            # 파일의 frameworks 필드 업데이트
            if frameworks_in_file and self.current_file_id:
                self._update_file_frameworks(frameworks_in_file)
            
            debug(f"API 호출 관계 저장 완료: {len(api_calls)}개")
            
        except Exception as e:
            handle_error(e, "API 호출 관계 저장 실패")

    def _find_or_create_api_url_component(self, api_call: Dict[str, Any], 
                                        project_id: int, file_type: str) -> Optional[int]:
        """프론트엔드 파일별 API_URL 컴포넌트 찾기 또는 생성"""
        try:
            api_url = api_call['api_url']
            http_method = api_call['http_method']
            component_name = f"{api_url}:{http_method}"
            
            debug(f"=== 프론트엔드 API_URL 컴포넌트 처리 ===")
            debug(f"API_URL: {component_name}")
            debug(f"현재 파일 ID: {self.current_file_id}")
            
            # 1. 현재 프론트엔드 파일에서 이미 해당 API_URL 컴포넌트가 있는지 확인
            existing_frontend_api_query = """
                SELECT component_id FROM components 
                WHERE project_id = ? AND component_name = ? AND component_type = 'API_URL' 
                  AND file_id = ? AND del_yn = 'N'
            """
            existing_frontend_api = self.db_utils.execute_query(
                existing_frontend_api_query, (project_id, component_name, self.current_file_id)
            )
            
            # 2. 현재 프론트엔드 파일에 이미 존재하면 재사용
            if existing_frontend_api:
                api_id = existing_frontend_api[0]['component_id']
                debug(f"현재 프론트엔드 파일에 이미 존재하는 API_URL 재사용: {component_name} (component_id: {api_id})")
                return api_id
            
            # 3. 현재 프론트엔드 파일에 없으면 새로 생성
            debug(f"현재 프론트엔드 파일에 새로운 API_URL 생성: {component_name}")
            new_api_id = self._create_frontend_api_url_component(api_call, project_id, component_name)
            
            if new_api_id:
                debug(f"새로운 프론트엔드 API_URL 생성 성공: {component_name} (component_id: {new_api_id})")
            else:
                debug(f"새로운 프론트엔드 API_URL 생성 실패: {component_name}")
                
            return new_api_id
            
        except Exception as e:
            handle_error(e, "API_URL 컴포넌트 찾기/생성 실패")


    def _update_file_frameworks(self, frameworks_in_file: set) -> None:
        """현재 파일의 frameworks 필드 업데이트"""
        try:
            if not self.current_file_id or not frameworks_in_file:
                return
            
            # 각 프레임워크를 파일에 추가
            for framework in frameworks_in_file:
                success = self.db_utils.update_file_frameworks(self.current_file_id, framework)
                if success:
                    debug(f"파일 frameworks 업데이트: file_id={self.current_file_id}, framework={framework}")
                else:
                    debug(f"파일 frameworks 업데이트 실패: file_id={self.current_file_id}, framework={framework}")
            
        except Exception as e:
            debug(f"파일 frameworks 업데이트 실패: {str(e)}")

    def _create_frontend_api_url_component(self, api_call: Dict[str, Any], project_id: int, component_name: str) -> Optional[int]:
        """
        새로운 프론트엔드 API_URL 컴포넌트 생성 (매칭 실패 시)
        
        Args:
            api_call: API 호출 정보
            project_id: 프로젝트 ID
            component_name: 컴포넌트명
            
        Returns:
            생성된 컴포넌트 ID
        """
        try:
            debug(f"=== API_URL 컴포넌트 생성 시도 ===")
            debug(f"component_name: {component_name}")
            debug(f"project_id: {project_id}")
            debug(f"file_id: {self.current_file_id}")
            
            # 참조 데이터 존재 여부 사전 확인
            self._verify_reference_data_before_insert(project_id, self.current_file_id)
            
            insert_query = """
                INSERT INTO components 
                (project_id, component_type, component_name, parent_id, file_id, 
                 layer, line_start, line_end, hash_value, has_error, error_message, del_yn)
                VALUES (?, 'API_URL', ?, NULL, ?, 'API_ENTRY', ?, ?, '-', 'N', NULL, 'N')
            """
            
            values = (
                project_id,
                component_name,
                self.current_file_id,  # 프론트엔드 파일 ID
                api_call.get('line_number', 1),
                api_call.get('line_number', 1)
            )
            
            debug(f"실행할 쿼리: {insert_query}")
            debug(f"실행할 값들: {values}")
            
            result = self.db_utils.execute_update(insert_query, values)
            if result > 0:
                # 생성된 컴포넌트 ID 조회
                find_query = """
                    SELECT component_id FROM components 
                    WHERE project_id = ? AND component_name = ? AND component_type = 'API_URL' 
                      AND file_id = ? AND del_yn = 'N'
                """
                created = self.db_utils.execute_query(find_query, (project_id, component_name, self.current_file_id))
                if created:
                    return created[0]['component_id']
            
            return None
            
        except Exception as e:
            debug(f"프론트엔드 API_URL 컴포넌트 생성 실패: {component_name} - {str(e)}")
            return None

    def _find_frontend_component_id(self, file_name: str, project_id: int) -> Optional[int]:
        """프론트엔드 컴포넌트 ID 찾기"""
        try:
            query = """
                SELECT component_id FROM components 
                WHERE project_id = ? AND component_name = ? AND file_id = ? AND del_yn = 'N'
            """
            result = self.db_utils.execute_query(query, (project_id, file_name, self.current_file_id))
            if result:
                return result[0]['component_id']
            return None
        except Exception as e:
            debug(f"프론트엔드 컴포넌트 ID 찾기 실패: {str(e)}")
            return None

    def _create_jsp_api_relationship(self, jsp_component_id: int, 
                                   api_url_id: int, api_call: Dict[str, Any]) -> None:
        """JSP 컴포넌트와 API_URL 관계 생성"""
        try:
            # 중복 관계 체크
            check_query = """
                SELECT relationship_id FROM relationships 
                WHERE src_id = ? AND dst_id = ? AND rel_type = ? AND del_yn = 'N'
            """
            existing = self.db_utils.execute_query(
                check_query, (jsp_component_id, api_url_id, 'CALL_METHOD')
            )
            
            if existing:
                debug(f"JSP-API 관계 이미 존재: {jsp_component_id} → {api_url_id}")
                return
            
            # 관계 생성 전 참조 데이터 확인
            debug(f"=== JSP-API 관계 생성 시도 ===")
            debug(f"jsp_component_id: {jsp_component_id}")
            debug(f"api_url_id: {api_url_id}")
            
            # 참조 데이터 존재 여부 확인
            debug(f"=== 관계 생성 전 참조 데이터 확인 ===")
            self._verify_relationship_references(jsp_component_id, api_url_id)
            
            # 관계 생성
            insert_query = """
                INSERT INTO relationships 
                (src_id, dst_id, rel_type, confidence, has_error, error_message, del_yn)
                VALUES (?, ?, 'CALL_METHOD', 1.0, 'N', NULL, 'N')
            """
            
            debug(f"=== JSP-API 관계 생성 시도 ===")
            debug(f"실행할 쿼리: {insert_query}")
            debug(f"실행할 값들: src_id={jsp_component_id}, dst_id={api_url_id}")
            
            result = self.db_utils.execute_update(insert_query, (jsp_component_id, api_url_id))
            if result > 0:
                self.stats['relationships_created'] += 1
                debug(f"JSP-API 관계 생성: {jsp_component_id} → {api_url_id}")
            
        except Exception as e:
            debug(f"JSP-API 관계 생성 실패: {str(e)}")

    def _create_api_method_relationship(self, api_url_id: int, api_call: Dict[str, Any]) -> None:
        """프론트엔드 API_URL과 백엔드 METHOD 관계 생성"""
        try:
            api_url = api_call['api_url']
            http_method = api_call['http_method']
            
            debug(f"=== 프론트엔드 API_URL → 백엔드 METHOD 관계 생성 ===")
            debug(f"프론트엔드 API_URL ID: {api_url_id}")
            debug(f"API_URL: {api_url}:{http_method}")
            
            # 백엔드 METHOD 컴포넌트 찾기 (더 정확한 매칭)
            method_query = """
                SELECT c.component_id, c.component_name, c.layer, f.file_name
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                WHERE c.project_id = ? 
                  AND c.component_type = 'METHOD'
                  AND f.file_type = 'JAVA'
                  AND c.del_yn = 'N'
                  AND f.del_yn = 'N'
                ORDER BY c.component_id
                LIMIT 10
            """
            
            from util.global_project import get_global_project_id
            current_project_id = get_global_project_id()
            methods = self.db_utils.execute_query(method_query, (current_project_id,))
            debug(f"찾은 백엔드 METHOD 개수: {len(methods)}")
            
            if methods:
                # 첫 번째 METHOD와 관계 생성 (향후 더 정교한 매칭 로직 추가 가능)
                method_component_id = methods[0]['component_id']
                method_name = methods[0]['component_name']
                method_file = methods[0]['file_name']
                
                debug(f"선택된 백엔드 METHOD: {method_name} (파일: {method_file}, ID: {method_component_id})")
                
                # 중복 관계 체크
                check_query = """
                    SELECT relationship_id FROM relationships 
                    WHERE src_id = ? AND dst_id = ? AND rel_type = ? AND del_yn = 'N'
                """
                existing = self.db_utils.execute_query(
                    check_query, (api_url_id, method_component_id, 'CALL_METHOD')
                )
                
                if existing:
                    debug(f"프론트엔드 API_URL → 백엔드 METHOD 관계 이미 존재: {api_url_id} → {method_component_id}")
                    return
                
                # 관계 생성
                insert_query = """
                    INSERT INTO relationships 
                    (src_id, dst_id, rel_type, confidence, has_error, error_message, del_yn)
                    VALUES (?, ?, 'CALL_METHOD', 1.0, 'N', NULL, 'N')
                """
                
                debug(f"실행할 관계 생성 쿼리: {insert_query}")
                debug(f"관계 생성 값: src_id={api_url_id}, dst_id={method_component_id}")
                
                result = self.db_utils.execute_update(insert_query, (api_url_id, method_component_id))
                if result > 0:
                    self.stats['relationships_created'] += 1
                    debug(f"프론트엔드 API_URL → 백엔드 METHOD 관계 생성 성공: {api_url_id} → {method_component_id}")
                else:
                    debug(f"프론트엔드 API_URL → 백엔드 METHOD 관계 생성 실패")
            else:
                debug(f"매칭되는 백엔드 METHOD 없음: {api_url}:{http_method}")
            
        except Exception as e:
            info(f"API-METHOD 관계 생성 실패: {str(e)}")

    def _print_statistics(self) -> None:
        """통계 정보 출력"""
        try:
            info("=== 프론트엔드 파일 로딩 통계 ===")
            info(f"총 파일: {self.stats['total_files']}개")
            info(f"처리 완료: {self.stats['processed_files']}개")
            info(f"에러 파일: {self.stats['error_files']}개")
            info(f"JSP 파일: {self.stats['jsp_files']}개")
            info(f"JSX 파일: {self.stats['jsx_files']}개")
            info(f"Vue 파일: {self.stats['vue_files']}개")
            info(f"TS 파일: {self.stats['ts_files']}개")
            info(f"TSX 파일: {self.stats['tsx_files']}개")
            info(f"JS 파일: {self.stats['js_files']}개")
            info(f"HTML 파일: {self.stats['html_files']}개")
            info(f"생성된 컴포넌트: {self.stats['components_created']}개")
            info(f"발견된 API 호출: {self.stats['api_calls_found']}개")
            info(f"생성된 관계: {self.stats['relationships_created']}개")
            
            # frameworks 사용 현황 통계
            self._print_frameworks_statistics()
            
        except Exception as e:
            handle_error(e, "통계 출력 실패")

    def _print_frameworks_statistics(self) -> None:
        """frameworks 사용 현황 통계 출력"""
        try:
            if not self.db_utils:
                return
            
            # 프로젝트 ID 조회
            from util.global_project import get_global_project_id
            project_id = get_global_project_id()
            if not project_id:
                return
            
            # 프론트엔드 파일들의 frameworks 현황 조회
            query = """
                SELECT file_type, frameworks, COUNT(*) as file_count
                FROM files 
                WHERE project_id = ? 
                  AND file_type IN ('JSP', 'JSX', 'VUE', 'TS', 'TSX', 'JS', 'HTML')
                  AND frameworks IS NOT NULL 
                  AND frameworks != ''
                  AND del_yn = 'N'
                GROUP BY file_type, frameworks
                ORDER BY file_type, frameworks
            """
            
            results = self.db_utils.execute_query(query, (project_id,))
            
            if results:
                info("=== 프론트엔드 Frameworks 사용 현황 ===")
                
                # 파일 타입별 frameworks 정리
                frameworks_by_type = {}
                all_frameworks = set()
                
                for row in results:
                    file_type = row['file_type']
                    frameworks_str = row['frameworks']
                    file_count = row['file_count']
                    
                    if file_type not in frameworks_by_type:
                        frameworks_by_type[file_type] = {}
                    
                    frameworks_by_type[file_type][frameworks_str] = file_count
                    
                    # 개별 프레임워크 수집
                    if frameworks_str:
                        for fw in frameworks_str.split(','):
                            all_frameworks.add(fw.strip())
                
                # 파일 타입별 출력
                for file_type in sorted(frameworks_by_type.keys()):
                    info(f"  {file_type} 파일:")
                    for frameworks_str, count in frameworks_by_type[file_type].items():
                        info(f"    {frameworks_str}: {count}개 파일")
                
                # 전체 프레임워크 요약
                if all_frameworks:
                    info(f"  사용된 프레임워크: {', '.join(sorted(all_frameworks))}")
            else:
                info("=== 프론트엔드 Frameworks 사용 현황 ===")
                info("  Frameworks를 사용하는 파일이 없습니다")
                
        except Exception as e:
            debug(f"frameworks 통계 출력 실패: {str(e)}")



def execute_frontend_loading(project_name: str) -> bool:
    """
    프론트엔드 파일 로딩 실행 함수

    Args:
        project_name: 프로젝트명

    Returns:
        bool: 성공 여부
    """
    try:
        frontend_engine = FrontendLoadingEngine(project_name)
        success = frontend_engine.execute_frontend_loading()
        
        # 프론트엔드 분석 완료 (각 파일별로 API_URL 컴포넌트가 이미 생성됨)
        
        return success
    except Exception as e:
        handle_error(e, "프론트엔드 로딩 실행 실패")
        return False
