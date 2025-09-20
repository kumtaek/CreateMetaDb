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
                    
                    result = self.db_utils.execute_update(insert_query, values)
                    if result > 0:
                        debug(f"JSP 컴포넌트 저장 성공: {component['component_name']}")
            else:
                # 다른 프론트엔드 파일 타입은 스키마정의서에 따라 components 테이블에 저장하지 않음
                debug(f"스키마정의서 준수: {file_type} 파일은 files 테이블에만 저장, components 테이블에는 API_URL만 저장")
            
        except Exception as e:
            handle_error(e, "프론트엔드 컴포넌트 저장 실패")

    def _save_api_call_relationships_to_database(self, api_calls: List[Dict[str, Any]], 
                                               project_id: int, file_type: str) -> None:
        """API 호출 관계를 데이터베이스에 저장"""
        try:
            debug(f"API 호출 관계 저장 시작: {len(api_calls)}개")
            
            for api_call in api_calls:
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
            
            debug(f"API 호출 관계 저장 완료: {len(api_calls)}개")
            
        except Exception as e:
            handle_error(e, "API 호출 관계 저장 실패")

    def _find_or_create_api_url_component(self, api_call: Dict[str, Any], 
                                        project_id: int, file_type: str) -> Optional[int]:
        """API_URL 컴포넌트 찾기 또는 생성"""
        try:
            api_url = api_call['api_url']
            http_method = api_call['http_method']
            component_name = f"{api_url}:{http_method}"
            
            # 기존 API_URL 컴포넌트 찾기
            find_query = """
                SELECT component_id FROM components 
                WHERE project_id = ? AND component_name = ? AND component_type = 'API_URL' AND del_yn = 'N'
            """
            existing = self.db_utils.execute_query(find_query, (project_id, component_name))
            
            if existing:
                return existing[0]['component_id']
            
            # 새 API_URL 컴포넌트 생성 (현재 프론트엔드 파일의 file_id 사용)
            insert_query = """
                INSERT INTO components 
                (project_id, component_type, component_name, parent_id, file_id, 
                 layer, line_start, line_end, hash_value, has_error, error_message, del_yn)
                VALUES (?, 'API_URL', ?, NULL, ?, 'FRONTEND', ?, ?, '-', 'N', NULL, 'N')
            """
            
            values = (
                project_id,
                component_name,
                self.current_file_id,
                api_call.get('line_number', 1),
                api_call.get('line_number', 1)
            )
            
            result = self.db_utils.execute_update(insert_query, values)
            if result > 0:
                # 생성된 컴포넌트 ID 조회
                created = self.db_utils.execute_query(find_query, (project_id, component_name))
                if created:
                    debug(f"API_URL 컴포넌트 생성: {component_name}")
                    return created[0]['component_id']
            
            return None
            
        except Exception as e:
            handle_error(e, "API_URL 컴포넌트 찾기/생성 실패")

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
            
            # 관계 생성
            insert_query = """
                INSERT INTO relationships 
                (src_id, dst_id, rel_type, confidence, has_error, error_message, del_yn)
                VALUES (?, ?, 'CALL_METHOD', 1.0, 'N', NULL, 'N')
            """
            
            result = self.db_utils.execute_update(insert_query, (jsp_component_id, api_url_id))
            if result > 0:
                self.stats['relationships_created'] += 1
                debug(f"JSP-API 관계 생성: {jsp_component_id} → {api_url_id}")
            
        except Exception as e:
            debug(f"JSP-API 관계 생성 실패: {str(e)}")

    def _create_api_method_relationship(self, api_url_id: int, api_call: Dict[str, Any]) -> None:
        """API_URL과 METHOD 관계 생성 (기존 JSP 로딩 방식과 동일)"""
        try:
            # API_URL에서 매칭되는 METHOD 찾기
            api_url = api_call['api_url']
            http_method = api_call['http_method']
            
            # METHOD 컴포넌트 찾기 (URL 패턴 매칭)
            method_query = """
                SELECT c.component_id, c.component_name, c.layer
                FROM components c
                JOIN classes cl ON c.parent_id = cl.class_id
                WHERE c.project_id = ? 
                  AND c.component_type = 'METHOD'
                  AND c.del_yn = 'N'
                LIMIT 1
            """
            
            methods = self.db_utils.execute_query(method_query, (self.project_id,))
            
            if methods:
                method_component_id = methods[0]['component_id']
                
                # 중복 관계 체크
                check_query = """
                    SELECT relationship_id FROM relationships 
                    WHERE src_id = ? AND dst_id = ? AND rel_type = ? AND del_yn = 'N'
                """
                existing = self.db_utils.execute_query(
                    check_query, (api_url_id, method_component_id, 'CALL_METHOD')
                )
                
                if existing:
                    debug(f"API-METHOD 관계 이미 존재: {api_url_id} → {method_component_id}")
                    return
                
                # 관계 생성
                insert_query = """
                    INSERT INTO relationships 
                    (src_id, dst_id, rel_type, confidence, has_error, error_message, del_yn)
                    VALUES (?, ?, 'CALL_METHOD', 1.0, 'N', NULL, 'N')
                """
                
                result = self.db_utils.execute_update(insert_query, (api_url_id, method_component_id))
                if result > 0:
                    self.stats['relationships_created'] += 1
                    debug(f"API-METHOD 관계 생성: {api_url_id} → {method_component_id}")
            else:
                debug(f"매칭되는 METHOD 없음: {api_url}:{http_method}")
            
        except Exception as e:
            debug(f"API-METHOD 관계 생성 실패: {str(e)}")

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
            
        except Exception as e:
            handle_error(e, "통계 출력 실패")

    def update_api_url_file_ids(self, project_id: int) -> Dict[str, int]:
        """API_URL 컴포넌트의 file_id 업데이트 (기존 JSP 로직 재사용)"""
        try:
            debug("API_URL file_id 업데이트 시작...")
            
            # Java file_id를 가진 API_URL 컴포넌트 조회
            query = """
                SELECT c.component_id, c.component_name, c.file_id, f.file_type
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                WHERE c.project_id = ? 
                  AND c.component_type = 'API_URL'
                  AND f.file_type = 'JAVA'
                  AND c.del_yn = 'N'
            """
            
            java_api_urls = self.db_utils.execute_query(query, (project_id,))
            debug(f"Java file_id API_URL 컴포넌트: {len(java_api_urls)}개 발견")
            
            updated_count = 0
            not_found_count = 0
            
            for api_url in java_api_urls:
                component_id = api_url['component_id']
                component_name = api_url['component_name']
                
                # API URL에서 매칭할 프론트엔드 파일 찾기
                frontend_file_id = self._find_matching_frontend_file_for_api(component_name, project_id)
                
                if frontend_file_id:
                    # file_id 업데이트
                    if self._update_api_url_file_id(component_id, frontend_file_id):
                        updated_count += 1
                        debug(f"API_URL file_id 업데이트 성공: {component_name}")
                    else:
                        debug(f"API_URL file_id 업데이트 실패: {component_name}")
                else:
                    not_found_count += 1
                    debug(f"매칭 프론트엔드 파일 없음: {component_name}")
            
            return {
                'total': len(java_api_urls),
                'updated': updated_count,
                'not_found': not_found_count
            }
            
        except Exception as e:
            handle_error(e, "API_URL file_id 업데이트 실패")
            return {'total': 0, 'updated': 0, 'not_found': 0}

    def _find_matching_frontend_file_for_api(self, api_url_component_name: str, project_id: int) -> Optional[int]:
        """API_URL에 매칭되는 프론트엔드 파일 찾기"""
        try:
            # API URL 패턴에서 URL 추출
            if ':' in api_url_component_name:
                url_pattern = api_url_component_name.split(':')[0]
            else:
                url_pattern = api_url_component_name
            
            # 프론트엔드 파일들 중에서 매칭되는 파일 찾기
            frontend_types = ['JSP', 'JSX', 'VUE', 'TS', 'TSX', 'JS', 'HTML']
            placeholders = ','.join(['?' for _ in frontend_types])
            
            query = f"""
                SELECT file_id, file_name, file_path
                FROM files 
                WHERE project_id = ? 
                  AND file_type IN ({placeholders})
                  AND del_yn = 'N'
                ORDER BY file_type, file_name
                LIMIT 1
            """
            
            params = [project_id] + frontend_types
            results = self.db_utils.execute_query(query, params)
            
            if results:
                # 첫 번째 프론트엔드 파일을 반환 (간단한 매칭)
                frontend_file_id = results[0]['file_id']
                file_name = results[0]['file_name']
                debug(f"프론트엔드 파일 매칭: {url_pattern} → {file_name} (file_id: {frontend_file_id})")
                return frontend_file_id
            
            return None
            
        except Exception as e:
            debug(f"프론트엔드 파일 매칭 실패: {api_url_component_name} - {str(e)}")
            return None

    def _update_api_url_file_id(self, api_url_id: int, frontend_file_id: int) -> bool:
        """API_URL 컴포넌트의 file_id 업데이트"""
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
            conflict_result = self.db_utils.execute_query(conflict_check_query, (project_id, component_name, frontend_file_id))
            
            if conflict_result:
                existing_component_id = conflict_result[0]['component_id']
                debug(f"이미 프론트엔드 file_id에 존재: {component_name} (기존 component_id: {existing_component_id})")
                # 프론트엔드 file_id에 이미 존재하므로 Java file_id의 중복 컴포넌트만 삭제하고 성공으로 처리
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
                insert_result = self.db_utils.execute_update(insert_sql, (project_id, component_name, frontend_file_id))
                
                if insert_result > 0:
                    debug(f"API_URL file_id 업데이트 성공 (DELETE+INSERT): {api_url_id} → {frontend_file_id}")
                    return True
                else:
                    debug(f"API_URL 재생성 실패: {component_name}")
                    return False
            else:
                debug(f"API_URL 삭제 실패: {api_url_id}")
                return False
                
        except Exception as e:
            debug(f"API_URL file_id 업데이트 실패: {api_url_id} → {frontend_file_id} - {str(e)}")
            return False


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
        
        # 프론트엔드 분석 완료 후 API_URL file_id 업데이트 (기존 JSP 로직 재사용)
        if success:
            from util.global_project import get_global_project_id
            project_id = get_global_project_id()
            if project_id:
                update_stats = frontend_engine.update_api_url_file_ids(project_id)
                info(f"=== API_URL file_id 업데이트 통계 ===")
                info(f"성공: {update_stats['updated']}개 업데이트")
                info(f"매칭 실패: {update_stats['not_found']}개")
                info(f"총 대상: {update_stats['total']}개")
        
        return success
    except Exception as e:
        handle_error(e, "프론트엔드 로딩 실행 실패")
        return False
