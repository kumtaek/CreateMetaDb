"""
Java 로딩 모듈 - 4단계 통합 처리
- Java 파일에서 클래스/메서드 추출 및 상속 관계 분석
- 메모리 최적화 (스트리밍 처리)
- 데이터베이스 저장 및 통계 관리

USER RULES:
- 하드코딩 금지: path_utils.get_parser_config_path("java") 사용 (크로스플랫폼 대응)
- 파싱 에러 처리: has_error='Y', error_message 저장 후 계속 실행
- 시스템 에러 처리: handle_error() 공통함수 사용
- 공통함수 사용: util 모듈 활용
- 메뉴얼 기반: parser/manual/01_java 참고
"""

import os
from typing import List, Dict, Any, Optional
from util import (
    DatabaseUtils, PathUtils, HashUtils, ValidationUtils,
    app_logger, info, error, debug, warning, handle_error,
    get_project_source_path, get_project_metadata_db_path
)
# USER RULES: 공통함수 사용, 하드코딩 금지
from parser.java_parser import JavaParser


class JavaLoadingEngine:
    """Java 로딩 엔진 - 4단계 통합 처리"""

    def __init__(self, project_name: str):
        """
        Java 로딩 엔진 초기화

        Args:
            project_name: 프로젝트명
        """
        self.project_name = project_name
        self.project_source_path = get_project_source_path(project_name)
        self.metadata_db_path = get_project_metadata_db_path(project_name)
        self.db_utils = None

        # Java 파서 초기화 (USER RULES: 공통함수 사용)
        self.java_parser = JavaParser()

        # 통계 정보 (4~5단계 통합)
        self.stats = {
            'java_files_processed': 0,
            'classes_extracted': 0,
            'classes_created': 0,
            'methods_extracted': 0,
            'components_created': 0,
            'inheritance_relationships_created': 0,
            'call_query_relationships_created': 0,
            'call_method_relationships_created': 0,
            'use_table_relationships_created': 0,
            'business_methods_filtered': 0,
            'errors': 0,
            'processing_time': 0.0
        }

    def execute_java_loading(self) -> bool:
        """
        Java 로딩 실행: 4단계 통합 처리

        Returns:
            실행 성공 여부
        """
        import time
        start_time = time.time()

        try:
            info("=== Java 로딩 시작: 4단계 통합 처리 ===")

            # 데이터베이스 연결 (USER RULES: 공통함수 사용)
            self.db_utils = DatabaseUtils(self.metadata_db_path)
            if not self.db_utils.connect():
                error("메타데이터베이스 연결 실패")
                return False

            # 1. Java 파일 수집
            java_files = self.java_parser.get_filtered_java_files(self.project_source_path)
            if not java_files:
                warning("Java 파일이 없습니다")
                return True

            info(f"처리할 Java 파일 수: {len(java_files)}개")

            # 2. Java 파일별 통합 처리 (메모리 최적화)
            for java_file in java_files:
                try:
                    # 4단계 통합 처리: 클래스/메서드 추출 + 상속 관계 분석
                    debug(f"Java 파일 파싱 시작: {java_file}")
                    analysis_result = self.java_parser.parse_java_file(java_file)
                    debug(f"Java 파일 파싱 완료: {java_file}")

                    # 파싱 에러 체크 (USER RULES: 파싱 에러는 계속 진행)
                    if analysis_result.get('has_error') == 'Y':
                        warning(f"Java 파싱 에러로 건너뜀: {java_file} - {analysis_result.get('error_message', '')}")
                        self.stats['errors'] += 1
                        continue

                    # 클래스 정보 처리
                    if analysis_result.get('classes'):
                        try:
                            if self._save_classes_to_database(analysis_result['classes'], java_file):
                                self.stats['classes_extracted'] += len(analysis_result['classes'])

                                # 메서드 정보 처리
                                total_methods = sum(len(cls.get('methods', [])) for cls in analysis_result['classes'])
                                if total_methods > 0:
                                    self.stats['methods_extracted'] += total_methods
                        except Exception as e:
                            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                            handle_error(e, f"클래스 저장 실패: {java_file}")
                            return False

                    # 상속 관계 처리
                    if analysis_result.get('inheritance_relationships'):
                        try:
                            if self._save_inheritance_relationships_to_database(analysis_result['inheritance_relationships']):
                                self.stats['inheritance_relationships_created'] += len(analysis_result['inheritance_relationships'])
                        except Exception as e:
                            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                            handle_error(e, f"상속 관계 저장 실패: {java_file}")
                            return False

                    # 5단계 관계 분석 처리 (통합)
                    if analysis_result.get('call_query_relationships'):
                        try:
                            if self._save_call_query_relationships_to_database(analysis_result['call_query_relationships']):
                                self.stats['call_query_relationships_created'] += len(analysis_result['call_query_relationships'])
                        except Exception as e:
                            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                            handle_error(e, f"CALL_QUERY 관계 저장 실패: {java_file}")
                            return False

                    if analysis_result.get('call_method_relationships'):
                        try:
                            if self._save_call_method_relationships_to_database(analysis_result['call_method_relationships']):
                                self.stats['call_method_relationships_created'] += len(analysis_result['call_method_relationships'])
                        except Exception as e:
                            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                            handle_error(e, f"CALL_METHOD 관계 저장 실패: {java_file}")
                            return False

                    if analysis_result.get('use_table_relationships'):
                        try:
                            if self._save_use_table_relationships_to_database(analysis_result['use_table_relationships']):
                                self.stats['use_table_relationships_created'] += len(analysis_result['use_table_relationships'])
                        except Exception as e:
                            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                            handle_error(e, f"USE_TABLE 관계 저장 실패: {java_file}")
                            return False

                    self.stats['java_files_processed'] += 1

                    # 메모리 최적화: 처리 후 즉시 해제
                    del analysis_result

                except Exception as e:
                    # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                    # 시스템 에러 (데이터베이스, 메모리 등) - 프로그램 종료
                    handle_error(e, f"Java 파일 처리 실패: {java_file}")
                    return False

            # 3. 통계 정보 출력
            self.stats['processing_time'] = time.time() - start_time
            self._print_java_loading_statistics()

            info("=== Java 로딩 완료 ===")
            return True

        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, "Java 로딩 실행 실패")
            return False
        finally:
            # 데이터베이스 연결 해제
            if self.db_utils:
                self.db_utils.disconnect()

    def _save_classes_to_database(self, classes: List[Dict[str, Any]], java_file: str) -> bool:
        """
        Java 클래스를 데이터베이스에 저장 (classes/components 테이블)

        Args:
            classes: Java 클래스 정보 리스트
            java_file: Java 파일 경로

        Returns:
            저장 성공 여부
        """
        try:
            info(f"=== Java 클래스 저장 시작: {java_file} ===")
            info(f"저장할 클래스 수: {len(classes)}개")

            if not classes:
                warning("저장할 클래스가 없습니다")
                return True

            # 프로젝트 ID 조회 (USER RULES: 공통함수 사용)
            project_id = self._get_project_id()
            if not project_id:
                handle_error(Exception("프로젝트 ID를 찾을 수 없습니다"), "클래스 저장 실패")
                return False

            # 파일 ID 조회
            file_id = self._get_file_id(java_file)
            if not file_id:
                handle_error(Exception(f"파일 ID를 찾을 수 없습니다: {java_file}"), "클래스 저장 실패")
                return False

            info(f"프로젝트 ID: {project_id}, 파일 ID: {file_id}")

            # 각 클래스별로 처리
            for class_info in classes:
                try:
                    # file_id를 class_info에 추가
                    class_info['file_id'] = file_id
                    
                    # 1. classes 테이블에 저장
                    class_id = self._create_class_record(project_id, class_info)
                    if not class_id:
                        warning(f"클래스 레코드 생성 실패: {class_info.get('class_name', 'UNKNOWN')}")
                        continue

                    # 2. 클래스 생성 완료
                    self.stats['classes_created'] += 1
                    info(f"클래스 생성 완료: {class_info.get('class_name')} (ID: {class_id})")

                    # 3. 메서드 처리 (METHOD 컴포넌트 생성)
                    methods = class_info.get('methods', [])
                    if methods:
                        method_count = self._save_methods_to_database(
                            project_id, file_id, class_id, methods
                        )
                        if method_count > 0:
                            info(f"메서드 생성 완료: {class_info.get('class_name')}, {method_count}개")

                except Exception as e:
                    # 파싱 에러: 특정 클래스 처리 실패 - 계속 진행
                    warning(f"클래스 처리 중 오류: {class_info.get('class_name', 'UNKNOWN')} - {str(e)}")
                    continue

            info(f"=== Java 클래스 저장 완료: {java_file} ===")
            return True

        except Exception as e:
            handle_error(e, f"클래스 데이터베이스 저장 실패: {java_file}")
            return False

    def _create_class_record(self, project_id: int, class_info: Dict[str, Any]) -> Optional[int]:
        """
        classes 테이블에 클래스 레코드 생성

        Args:
            project_id: 프로젝트 ID
            class_info: 클래스 정보

        Returns:
            class_id 또는 None
        """
        try:
            # 해시값 생성 (USER RULES: 공통함수 사용)
            class_hash = HashUtils.generate_content_hash(
                f"{class_info.get('class_name', '')}{class_info.get('package_name', '')}{class_info.get('class_type', '')}"
            )

            class_data = {
                'project_id': project_id,
                'file_id': class_info.get('file_id'),
                'class_name': class_info.get('class_name', ''),
                'parent_class_id': class_info.get('parent_class_id'),
                'line_start': class_info.get('line_start'),
                'line_end': class_info.get('line_end'),
                'has_error': class_info.get('has_error', 'N'),
                'error_message': class_info.get('error_message'),
                'hash_value': class_hash,
                'del_yn': 'N'
            }

            # classes 테이블에 저장 (USER RULES: 공통함수 사용)
            class_id = self.db_utils.insert_or_replace_with_id('classes', class_data)
            return class_id

        except Exception as e:
            handle_error(e, f"클래스 레코드 생성 실패: {class_info.get('class_name', 'UNKNOWN')}")
            return None


    def _get_class_id_by_name(self, project_id: int, class_name: str) -> Optional[int]:
        """
        클래스명으로 클래스 ID 조회 (USER RULES: 공통함수 사용)

        Args:
            project_id: 프로젝트 ID
            class_name: 클래스명

        Returns:
            클래스 ID
        """
        try:
            query = """
                SELECT class_id FROM classes
                WHERE project_id = ? AND class_name = ? AND del_yn = 'N'
            """
            results = self.db_utils.execute_query(query, (project_id, class_name))
            
            if results:
                return results[0]['class_id']
            else:
                return None

        except Exception as e:
            handle_error(e, f"클래스 ID 조회 실패: class_name={class_name}")
            return None

    def _save_methods_to_database(self, project_id: int, file_id: int, class_id: int, methods: List[Dict[str, Any]]) -> int:
        """
        Java 메서드를 components 테이블에 저장

        Args:
            project_id: 프로젝트 ID
            file_id: 파일 ID
            class_id: 클래스 ID (classes 테이블의 class_id)
            methods: 메서드 정보 리스트

        Returns:
            생성된 메서드 컴포넌트 수
        """
        try:
            if not methods:
                return 0

            created_count = 0
            business_methods = 0

            for method_info in methods:
                try:
                    method_name = method_info.get('method_name', 'UNKNOWN')
                    debug(f"메서드 처리 시작: {method_name}")
                    
                    # 비즈니스 로직 메서드인지 확인 (USER RULES: 하드코딩 지양)
                    simple_complexity = self.java_parser.config.get('method_complexity', {}).get('simple_complexity', 'simple')
                    complexity = method_info.get('complexity', simple_complexity)
                    business_complexity = self.java_parser.config.get('method_complexity', {}).get('business_complexity', 'business')
                    complex_complexity = self.java_parser.config.get('method_complexity', {}).get('complex_business_complexity', 'complex_business')
                    
                    if complexity in [business_complexity, complex_complexity]:
                        business_methods += 1

                    # 메서드 컴포넌트 생성
                    debug(f"메서드 컴포넌트 생성 시도: {method_name} (복잡도: {complexity})")
                    method_component_id = self._create_method_component(
                        project_id, file_id, class_id, method_info
                    )

                    if method_component_id:
                        created_count += 1
                        debug(f"메서드 생성 성공: {method_info.get('method_name')} (ID: {method_component_id}, 복잡도: {complexity})")
                    else:
                        # 파싱 에러: 개별 메서드 컴포넌트 생성 실패 - 계속 진행
                        warning(f"메서드 컴포넌트 생성 실패: {method_info.get('method_name', 'UNKNOWN')}")

                except Exception as e:
                    # 파싱 에러: 특정 메서드 처리 실패 - 계속 진행
                    warning(f"메서드 처리 중 오류: {method_info.get('method_name', 'UNKNOWN')} - {str(e)}")
                    continue

            self.stats['business_methods_filtered'] += business_methods
            self.stats['components_created'] += created_count

            return created_count

        except Exception as e:
            handle_error(e, "메서드 데이터베이스 저장 실패")
            return 0

    def _create_method_component(self, project_id: int, file_id: int, parent_id: int, method_info: Dict[str, Any]) -> Optional[int]:
        """
        components 테이블에 메서드 컴포넌트 생성

        Args:
            project_id: 프로젝트 ID
            file_id: 파일 ID
            parent_id: 부모 클래스의 class_id (classes 테이블의 class_id)
            method_info: 메서드 정보

        Returns:
            component_id 또는 None
        """
        try:
            method_name = method_info.get('method_name', 'UNKNOWN')
            debug(f"_create_method_component 시작: {method_name}")
            
            # 해시값 생성 (USER RULES: 공통함수 사용)
            method_signature = method_info.get('method_signature', method_info.get('method_name', ''))
            component_hash = HashUtils.generate_content_hash(
                f"METHOD{project_id}{parent_id}{method_signature}"
            )

            component_data = {
                'project_id': project_id,
                'file_id': file_id,
                'component_name': method_info.get('method_name', ''),
                'component_type': 'METHOD',
                'parent_id': parent_id,  # 클래스의 component_id
                'layer': 'APPLICATION',
                'line_start': method_info.get('line_start'),
                'line_end': method_info.get('line_end'),
                'has_error': method_info.get('has_error', 'N'),
                'error_message': method_info.get('error_message'),
                'hash_value': component_hash,
                'del_yn': 'N'
            }

            # components 테이블에 저장 (USER RULES: 공통함수 사용)
            component_id = self.db_utils.insert_or_replace_with_id('components', component_data)
            return component_id

        except Exception as e:
            # 파싱 에러: 개별 메서드 컴포넌트 생성 실패 - 계속 진행
            warning(f"메서드 컴포넌트 생성 실패: {method_info.get('method_name', 'UNKNOWN')} - {str(e)}")
            return None

    def _save_inheritance_relationships_to_database(self, inheritance_relationships: List[Dict[str, Any]]) -> bool:
        """
        상속 관계를 relationships 테이블에 저장

        Args:
            inheritance_relationships: 상속 관계 리스트

        Returns:
            저장 성공 여부
        """
        try:
            if not inheritance_relationships:
                warning("저장할 상속 관계가 없습니다")
                return True

            info(f"저장할 상속 관계 수: {len(inheritance_relationships)}개")

            # 프로젝트 ID 조회 (USER RULES: 공통함수 사용)
            project_id = self._get_project_id()
            if not project_id:
                handle_error(Exception("프로젝트 ID를 찾을 수 없습니다"), "상속 관계 저장 실패")
                return False

            # 관계 데이터 변환
            relationship_data_list = []

            for rel_info in inheritance_relationships:
                try:
                    # 자식 클래스 컴포넌트 ID 조회
                    child_component_id = self._get_class_component_id(project_id, rel_info['child_class'])
                    if not child_component_id:
                        warning(f"자식 클래스 컴포넌트 ID를 찾을 수 없습니다: {rel_info['child_class']}")
                        continue

                    # 부모 클래스 컴포넌트 ID 조회
                    parent_component_id = self._get_class_component_id(project_id, rel_info['parent_class'])
                    if not parent_component_id:
                        # inferred 클래스 생성 시도
                        info(f"inferred 클래스 생성 시도: {rel_info['parent_class']}")
                        parent_component_id = self._create_inferred_class(project_id, rel_info['parent_class'])
                        if parent_component_id:
                            info(f"inferred 클래스 생성 성공: {rel_info['parent_class']} (ID: {parent_component_id})")
                        else:
                            warning(f"inferred 클래스 생성 실패: {rel_info['parent_class']}")
                            continue

                    # 관계 데이터 생성
                    relationship_data = {
                        'src_id': child_component_id,  # 자식 → 부모로 관계 설정
                        'dst_id': parent_component_id,
                        'rel_type': 'INHERITANCE',
                        'confidence': 1.0,
                        'has_error': 'N',
                        'error_message': None,
                        'del_yn': 'N'
                    }

                    relationship_data_list.append(relationship_data)

                except Exception as e:
                    # 파싱 에러: 특정 관계 처리 실패 - 계속 진행
                    warning(f"상속 관계 데이터 변환 실패: {rel_info.get('child_class', 'UNKNOWN')} → {rel_info.get('parent_class', 'UNKNOWN')} - {str(e)}")
                    continue

            # 배치 INSERT OR REPLACE (USER RULES: 공통함수 사용)
            if relationship_data_list:
                processed_count = self.db_utils.batch_insert_or_replace('relationships', relationship_data_list)

                if processed_count > 0:
                    info(f"상속 관계 저장 완료: {processed_count}개")
                    return True
                else:
                    warning("상속 관계 저장 실패: processed_count = 0")
                    return False
            else:
                warning("저장할 유효한 상속 관계가 없습니다")
                return True

        except Exception as e:
            handle_error(e, "상속 관계 저장 실패")
            return False

    def _get_class_component_id(self, project_id: int, class_name: str) -> Optional[int]:
        """
        클래스 컴포넌트 ID 조회

        Args:
            project_id: 프로젝트 ID
            class_name: 클래스명

        Returns:
            컴포넌트 ID
        """
        try:
            # 클래스명으로 컴포넌트 ID 조회 (USER RULES: 공통함수 사용)
            query = """
                SELECT component_id FROM components
                WHERE project_id = ?
                AND component_name = ?
                AND component_type = 'CLASS'
                AND del_yn = 'N'
            """

            results = self.db_utils.execute_query(query, (project_id, class_name))

            if results and len(results) > 0:
                return results[0]['component_id']
            return None

        except Exception as e:
            handle_error(e, f"클래스 컴포넌트 ID 조회 실패: {class_name}")
            return None

    def _create_inferred_class(self, project_id: int, class_name: str) -> Optional[int]:
        """
        inferred 클래스 생성 (classes/components 테이블)

        Args:
            project_id: 프로젝트 ID
            class_name: 클래스명

        Returns:
            component_id 또는 None
        """
        try:
            # inferred 클래스용 file_id 찾기 (Java 파일 중 하나 선택)
            inferred_file_id = self._get_inferred_file_id(project_id)
            if not inferred_file_id:
                error(f"inferred 클래스용 file_id를 찾을 수 없습니다: {class_name}")
                return None

            # 1. classes 테이블에 inferred 클래스 생성
            class_data = {
                'project_id': project_id,
                'component_id': None,  # 나중에 업데이트
                'class_name': class_name,
                'class_type': 'class',
                'package_name': 'UNKNOWN',
                'access_modifier': 'public',
                'is_abstract': 'N',
                'is_final': 'N',
                'extends_class': '',
                'implements_interfaces': '',
                'class_comments': 'Inferred from inheritance analysis',
                'annotations': '',
                'has_error': 'N',
                'error_message': None,
                'hash_value': 'INFERRED',
                'del_yn': 'N'
            }

            # classes 테이블에 저장 (USER RULES: 공통함수 사용)
            class_id = self.db_utils.insert_or_replace_with_id('classes', class_data)
            if not class_id:
                warning(f"inferred 클래스 레코드 생성 실패: {class_name}")
                return None

            # 2. components 테이블에 클래스 컴포넌트 생성
            component_data = {
                'project_id': project_id,
                'file_id': inferred_file_id,
                'component_name': class_name,
                'component_type': 'CLASS',
                'parent_id': None,
                'layer': 'APPLICATION',
                'line_start': None,
                'line_end': None,
                'has_error': 'N',
                'error_message': None,
                'hash_value': 'INFERRED',
                'del_yn': 'N'
            }

            # components 테이블에 저장 (USER RULES: 공통함수 사용)
            component_id = self.db_utils.insert_or_replace_with_id('components', component_data)
            if component_id:
                # 3. classes 테이블의 component_id 업데이트
                success = self._update_class_component_id(class_id, component_id)
                if success:
                    info(f"inferred 클래스 생성 완료: {class_name} (ID: {component_id})")
                    return component_id
                else:
                    warning(f"inferred 클래스 component_id 업데이트 실패: {class_name}")
            else:
                warning(f"inferred 클래스 컴포넌트 생성 실패: {class_name}")

            return None

        except Exception as e:
            handle_error(e, f"inferred 클래스 생성 실패: {class_name}")
            return None

    def _save_call_query_relationships_to_database(self, call_query_relationships: List[Dict[str, Any]]) -> bool:
        """
        CALL_QUERY 관계를 relationships 테이블에 저장

        Args:
            call_query_relationships: CALL_QUERY 관계 리스트

        Returns:
            저장 성공 여부
        """
        try:
            if not call_query_relationships:
                info("저장할 CALL_QUERY 관계가 없습니다")
                return True

            info(f"저장할 CALL_QUERY 관계 수: {len(call_query_relationships)}개")

            # 프로젝트 ID 조회 (USER RULES: 공통함수 사용)
            project_id = self._get_project_id()
            if not project_id:
                handle_error(Exception("프로젝트 ID를 찾을 수 없습니다"), "CALL_QUERY 관계 저장 실패")
                return False

            # 관계 데이터 변환
            relationship_data_list = []

            for rel_info in call_query_relationships:
                try:
                    # 소스 메서드 컴포넌트 ID 조회
                    src_component_id = self._get_method_component_id(project_id, rel_info['src_name'])
                    if not src_component_id:
                        # 시스템 에러: 메서드 컴포넌트가 존재하지 않음 - 프로그램 종료
                        handle_error(Exception(f"소스 메서드 컴포넌트 ID를 찾을 수 없습니다: {rel_info['src_name']}"), "CALL_QUERY 관계 저장 실패")

                    # 대상 쿼리 컴포넌트 ID 조회 (inferred 쿼리 생성)
                    dst_component_id = self._get_query_component_id(project_id, rel_info['dst_name'])
                    if not dst_component_id:
                        # inferred 쿼리 생성 시도
                        info(f"inferred 쿼리 생성 시도: {rel_info['dst_name']}")
                        dst_component_id = self._create_inferred_query(project_id, rel_info['dst_name'])
                        if dst_component_id:
                            info(f"inferred 쿼리 생성 성공: {rel_info['dst_name']} (ID: {dst_component_id})")
                        else:
                            # 시스템 에러: inferred 쿼리 생성 실패 - 프로그램 종료
                            handle_error(Exception(f"inferred 쿼리 생성 실패: {rel_info['dst_name']}"), "CALL_QUERY 관계 저장 실패")

                    # 관계 데이터 생성
                    relationship_data = {
                        'src_id': src_component_id,
                        'dst_id': dst_component_id,
                        'rel_type': 'CALL_QUERY',
                        'confidence': 1.0,
                        'has_error': 'N',
                        'error_message': None,
                        'del_yn': 'N'
                    }

                    relationship_data_list.append(relationship_data)

                except Exception as e:
                    # 파싱 에러: 특정 관계 처리 실패 - 계속 진행
                    warning(f"CALL_QUERY 관계 데이터 변환 실패: {rel_info.get('src_name', 'UNKNOWN')} → {rel_info.get('dst_name', 'UNKNOWN')} - {str(e)}")
                    continue

            # 배치 INSERT OR REPLACE (USER RULES: 공통함수 사용)
            if relationship_data_list:
                processed_count = self.db_utils.batch_insert_or_replace('relationships', relationship_data_list)

                if processed_count > 0:
                    info(f"CALL_QUERY 관계 저장 완료: {processed_count}개")
                    return True
                else:
                    # 시스템 에러: 관계 저장 실패 - 프로그램 종료
                    handle_error(Exception("CALL_QUERY 관계 저장 실패: processed_count = 0"), "CALL_QUERY 관계 저장 실패")
            else:
                info("저장할 유효한 CALL_QUERY 관계가 없습니다")
                return True

        except Exception as e:
            handle_error(e, "CALL_QUERY 관계 저장 실패")
            return False

    def _save_call_method_relationships_to_database(self, call_method_relationships: List[Dict[str, Any]]) -> bool:
        """
        CALL_METHOD 관계를 relationships 테이블에 저장

        Args:
            call_method_relationships: CALL_METHOD 관계 리스트

        Returns:
            저장 성공 여부
        """
        try:
            if not call_method_relationships:
                warning("저장할 CALL_METHOD 관계가 없습니다")
                return True

            info(f"저장할 CALL_METHOD 관계 수: {len(call_method_relationships)}개")

            # 프로젝트 ID 조회 (USER RULES: 공통함수 사용)
            project_id = self._get_project_id()
            if not project_id:
                handle_error(Exception("프로젝트 ID를 찾을 수 없습니다"), "CALL_METHOD 관계 저장 실패")
                return False

            # 관계 데이터 변환
            relationship_data_list = []

            for rel_info in call_method_relationships:
                try:
                    # 소스 메서드 컴포넌트 ID 조회
                    src_component_id = self._get_method_component_id(project_id, rel_info['src_name'])
                    if not src_component_id:
                        # 시스템 에러: 메서드 컴포넌트가 존재하지 않음 - 프로그램 종료
                        handle_error(Exception(f"소스 메서드 컴포넌트 ID를 찾을 수 없습니다: {rel_info['src_name']}"), "CALL_METHOD 관계 저장 실패")

                    # 대상 메서드 컴포넌트 ID 조회 (inferred 메서드 생성)
                    dst_component_id = self._get_method_component_id(project_id, rel_info['dst_name'])
                    if not dst_component_id:
                        # inferred 메서드 생성 시도
                        info(f"inferred 메서드 생성 시도: {rel_info['dst_name']}")
                        dst_component_id = self._create_inferred_method(project_id, rel_info['dst_name'])
                        if dst_component_id:
                            info(f"inferred 메서드 생성 성공: {rel_info['dst_name']} (ID: {dst_component_id})")
                        else:
                            # 시스템 에러: inferred 메서드 생성 실패 - 프로그램 종료
                            handle_error(Exception(f"inferred 메서드 생성 실패: {rel_info['dst_name']}"), "CALL_METHOD 관계 저장 실패")

                    # 관계 데이터 생성
                    relationship_data = {
                        'src_id': src_component_id,
                        'dst_id': dst_component_id,
                        'rel_type': 'CALL_METHOD',
                        'confidence': 1.0,
                        'has_error': 'N',
                        'error_message': None,
                        'del_yn': 'N'
                    }

                    relationship_data_list.append(relationship_data)

                except Exception as e:
                    # 파싱 에러: 특정 관계 처리 실패 - 계속 진행
                    warning(f"CALL_METHOD 관계 데이터 변환 실패: {rel_info.get('src_name', 'UNKNOWN')} → {rel_info.get('dst_name', 'UNKNOWN')} - {str(e)}")
                    continue

            # 배치 INSERT OR REPLACE (USER RULES: 공통함수 사용)
            if relationship_data_list:
                processed_count = self.db_utils.batch_insert_or_replace('relationships', relationship_data_list)

                if processed_count > 0:
                    info(f"CALL_METHOD 관계 저장 완료: {processed_count}개")
                    return True
                else:
                    warning("CALL_METHOD 관계 저장 실패: processed_count = 0")
                    return False
            else:
                warning("저장할 유효한 CALL_METHOD 관계가 없습니다")
                return True

        except Exception as e:
            handle_error(e, "CALL_METHOD 관계 저장 실패")
            return False

    def _save_use_table_relationships_to_database(self, use_table_relationships: List[Dict[str, Any]]) -> bool:
        """
        USE_TABLE 관계를 relationships 테이블에 저장

        Args:
            use_table_relationships: USE_TABLE 관계 리스트

        Returns:
            저장 성공 여부
        """
        try:
            if not use_table_relationships:
                warning("저장할 USE_TABLE 관계가 없습니다")
                return True

            info(f"저장할 USE_TABLE 관계 수: {len(use_table_relationships)}개")

            # 프로젝트 ID 조회 (USER RULES: 공통함수 사용)
            project_id = self._get_project_id()
            if not project_id:
                handle_error(Exception("프로젝트 ID를 찾을 수 없습니다"), "USE_TABLE 관계 저장 실패")
                return False

            # 관계 데이터 변환
            relationship_data_list = []

            for rel_info in use_table_relationships:
                try:
                    # 소스 메서드 컴포넌트 ID 조회
                    src_component_id = self._get_method_component_id(project_id, rel_info['src_name'])
                    if not src_component_id:
                        warning(f"소스 메서드 컴포넌트 ID를 찾을 수 없습니다: {rel_info['src_name']}")
                        continue

                    # 대상 테이블 컴포넌트 ID 조회 (inferred 테이블 생성)
                    dst_component_id = self._get_table_component_id(project_id, rel_info['dst_name'])
                    if not dst_component_id:
                        # inferred 테이블 생성 시도
                        info(f"inferred 테이블 생성 시도: {rel_info['dst_name']}")
                        dst_component_id = self._create_inferred_table(project_id, rel_info['dst_name'])
                        if dst_component_id:
                            info(f"inferred 테이블 생성 성공: {rel_info['dst_name']} (ID: {dst_component_id})")
                        else:
                            warning(f"inferred 테이블 생성 실패: {rel_info['dst_name']}")
                            continue

                    # 관계 데이터 생성
                    relationship_data = {
                        'src_id': src_component_id,
                        'dst_id': dst_component_id,
                        'rel_type': 'USE_TABLE',
                        'confidence': 1.0,
                        'has_error': 'N',
                        'error_message': None,
                        'del_yn': 'N'
                    }

                    relationship_data_list.append(relationship_data)

                except Exception as e:
                    # 파싱 에러: 특정 관계 처리 실패 - 계속 진행
                    warning(f"USE_TABLE 관계 데이터 변환 실패: {rel_info.get('src_name', 'UNKNOWN')} → {rel_info.get('dst_name', 'UNKNOWN')} - {str(e)}")
                    continue

            # 배치 INSERT OR REPLACE (USER RULES: 공통함수 사용)
            if relationship_data_list:
                processed_count = self.db_utils.batch_insert_or_replace('relationships', relationship_data_list)

                if processed_count > 0:
                    info(f"USE_TABLE 관계 저장 완료: {processed_count}개")
                    return True
                else:
                    warning("USE_TABLE 관계 저장 실패: processed_count = 0")
                    return False
            else:
                warning("저장할 유효한 USE_TABLE 관계가 없습니다")
                return True

        except Exception as e:
            handle_error(e, "USE_TABLE 관계 저장 실패")
            return False

    def _get_method_component_id(self, project_id: int, method_name: str) -> Optional[int]:
        """
        메서드 컴포넌트 ID 조회

        Args:
            project_id: 프로젝트 ID
            method_name: 메서드명 (클래스명.메서드명 형식 또는 메서드명만)

        Returns:
            컴포넌트 ID
        """
        try:
            # 클래스명.메서드명 형식에서 메서드명만 추출
            if '.' in method_name:
                method_name_only = method_name.split('.')[-1]
            else:
                method_name_only = method_name

            debug(f"메서드 컴포넌트 ID 조회: {method_name} -> {method_name_only}")

            # 메서드명으로 컴포넌트 ID 조회 (USER RULES: 공통함수 사용)
            query = """
                SELECT component_id FROM components
                WHERE project_id = ?
                AND component_name = ?
                AND component_type = 'METHOD'
                AND del_yn = 'N'
            """

            results = self.db_utils.execute_query(query, (project_id, method_name_only))

            if results and len(results) > 0:
                debug(f"메서드 컴포넌트 ID 조회 성공: {method_name_only} -> {results[0]['component_id']}")
                return results[0]['component_id']
            else:
                debug(f"메서드 컴포넌트 ID 조회 실패: {method_name_only} (존재하지 않음)")
                return None

        except Exception as e:
            handle_error(e, f"메서드 컴포넌트 ID 조회 실패: {method_name}")
            return None

    def _get_query_component_id(self, project_id: int, query_id: str) -> Optional[int]:
        """
        쿼리 컴포넌트 ID 조회

        Args:
            project_id: 프로젝트 ID
            query_id: 쿼리 ID

        Returns:
            컴포넌트 ID
        """
        try:
            # 쿼리 ID로 컴포넌트 ID 조회 (USER RULES: 공통함수 사용)
            query = """
                SELECT component_id FROM components
                WHERE project_id = ?
                AND component_name = ?
                AND component_type = 'QUERY'
                AND del_yn = 'N'
            """

            results = self.db_utils.execute_query(query, (project_id, query_id))

            if results and len(results) > 0:
                return results[0]['component_id']
            return None

        except Exception as e:
            handle_error(e, f"쿼리 컴포넌트 ID 조회 실패: {query_id}")
            return None

    def _get_table_component_id(self, project_id: int, table_name: str) -> Optional[int]:
        """
        테이블 컴포넌트 ID 조회

        Args:
            project_id: 프로젝트 ID
            table_name: 테이블명

        Returns:
            컴포넌트 ID
        """
        try:
            # 테이블명으로 컴포넌트 ID 조회 (USER RULES: 공통함수 사용)
            query = """
                SELECT component_id FROM components
                WHERE project_id = ?
                AND component_name = ?
                AND component_type = 'TABLE'
                AND del_yn = 'N'
            """

            results = self.db_utils.execute_query(query, (project_id, table_name))

            if results and len(results) > 0:
                return results[0]['component_id']
            return None

        except Exception as e:
            handle_error(e, f"테이블 컴포넌트 ID 조회 실패: {table_name}")
            return None

    def _create_inferred_query(self, project_id: int, query_id: str) -> Optional[int]:
        """
        inferred 쿼리 생성 (components 테이블)

        Args:
            project_id: 프로젝트 ID
            query_id: 쿼리 ID

        Returns:
            component_id 또는 None
        """
        try:
            # inferred 쿼리용 file_id 찾기 (XML 파일 중 하나 선택)
            inferred_file_id = self._get_inferred_xml_file_id(project_id)
            if not inferred_file_id:
                error(f"inferred 쿼리용 file_id를 찾을 수 없습니다: {query_id}")
                return None

            # components 테이블에 쿼리 컴포넌트 생성
            component_data = {
                'project_id': project_id,
                'file_id': inferred_file_id,
                'component_name': query_id,
                'component_type': 'QUERY',
                'parent_id': None,
                'layer': 'DATA',
                'line_start': None,
                'line_end': None,
                'has_error': 'N',
                'error_message': None,
                'hash_value': 'INFERRED',
                'del_yn': 'N'
            }

            # components 테이블에 저장 (USER RULES: 공통함수 사용)
            component_id = self.db_utils.insert_or_replace_with_id('components', component_data)
            if component_id:
                info(f"inferred 쿼리 생성 완료: {query_id} (ID: {component_id})")
                return component_id
            else:
                warning(f"inferred 쿼리 컴포넌트 생성 실패: {query_id}")
                return None

        except Exception as e:
            handle_error(e, f"inferred 쿼리 생성 실패: {query_id}")
            return None

    def _create_inferred_method(self, project_id: int, method_name: str) -> Optional[int]:
        """
        inferred 메서드 생성 (components 테이블)

        Args:
            project_id: 프로젝트 ID
            method_name: 메서드명

        Returns:
            component_id 또는 None
        """
        try:
            # inferred 메서드용 file_id 찾기 (Java 파일 중 하나 선택)
            inferred_file_id = self._get_inferred_file_id(project_id)
            if not inferred_file_id:
                error(f"inferred 메서드용 file_id를 찾을 수 없습니다: {method_name}")
                return None

            # components 테이블에 메서드 컴포넌트 생성
            component_data = {
                'project_id': project_id,
                'file_id': inferred_file_id,
                'component_name': method_name,
                'component_type': 'METHOD',
                'parent_id': None,
                'layer': 'APPLICATION',
                'line_start': None,
                'line_end': None,
                'has_error': 'N',
                'error_message': None,
                'hash_value': 'INFERRED',
                'del_yn': 'N'
            }

            # components 테이블에 저장 (USER RULES: 공통함수 사용)
            component_id = self.db_utils.insert_or_replace_with_id('components', component_data)
            if component_id:
                info(f"inferred 메서드 생성 완료: {method_name} (ID: {component_id})")
                return component_id
            else:
                warning(f"inferred 메서드 컴포넌트 생성 실패: {method_name}")
                return None

        except Exception as e:
            handle_error(e, f"inferred 메서드 생성 실패: {method_name}")
            return None

    def _create_inferred_table(self, project_id: int, table_name: str) -> Optional[int]:
        """
        inferred 테이블 생성 (components 테이블)

        Args:
            project_id: 프로젝트 ID
            table_name: 테이블명

        Returns:
            component_id 또는 None
        """
        try:
            # inferred 테이블용 file_id 찾기 (SQL 파일 중 하나 선택)
            inferred_file_id = self._get_inferred_sql_file_id(project_id)
            if not inferred_file_id:
                error(f"inferred 테이블용 file_id를 찾을 수 없습니다: {table_name}")
                return None

            # components 테이블에 테이블 컴포넌트 생성
            component_data = {
                'project_id': project_id,
                'file_id': inferred_file_id,
                'component_name': table_name,
                'component_type': 'TABLE',
                'parent_id': None,
                'layer': 'DATA',
                'line_start': None,
                'line_end': None,
                'has_error': 'N',
                'error_message': None,
                'hash_value': 'INFERRED',
                'del_yn': 'N'
            }

            # components 테이블에 저장 (USER RULES: 공통함수 사용)
            component_id = self.db_utils.insert_or_replace_with_id('components', component_data)
            if component_id:
                info(f"inferred 테이블 생성 완료: {table_name} (ID: {component_id})")
                return component_id
            else:
                warning(f"inferred 테이블 컴포넌트 생성 실패: {table_name}")
                return None

        except Exception as e:
            handle_error(e, f"inferred 테이블 생성 실패: {table_name}")
            return None

    def _get_inferred_xml_file_id(self, project_id: int) -> Optional[int]:
        """
        inferred 쿼리용 file_id 찾기 (XML 파일 중 하나 선택)
        USER RULES: 공통함수 사용, 하드코딩 금지

        Args:
            project_id: 프로젝트 ID

        Returns:
            file_id 또는 None
        """
        try:
            # USER RULES: 공통함수 사용 - DatabaseUtils의 execute_query 사용
            query = """
                SELECT file_id
                FROM files
                WHERE project_id = ? AND file_type = 'XML' AND del_yn = 'N'
                LIMIT 1
            """
            result = self.db_utils.execute_query(query, (project_id,))

            if result and len(result) > 0:
                file_id = result[0]['file_id']
                debug(f"inferred 쿼리용 file_id 찾음: {file_id}")
                return file_id
            else:
                # 시스템 에러: XML 파일이 files 테이블에 없는 것은 1단계에서 처리되지 않았음을 의미
                error("XML 파일이 files 테이블에 없습니다. 1단계 파일 스캔이 제대로 실행되지 않았습니다.")
                return None

        except Exception as e:
            # 시스템 에러: 데이터베이스 연결 실패 등 - 프로그램 종료
            handle_error(e, "inferred 쿼리용 file_id 조회 실패")
            return None

    def _get_inferred_sql_file_id(self, project_id: int) -> Optional[int]:
        """
        inferred 테이블용 file_id 찾기 (SQL 파일 중 하나 선택)
        USER RULES: 공통함수 사용, 하드코딩 금지

        Args:
            project_id: 프로젝트 ID

        Returns:
            file_id 또는 None
        """
        try:
            # USER RULES: 공통함수 사용 - DatabaseUtils의 execute_query 사용
            query = """
                SELECT file_id
                FROM files
                WHERE project_id = ? AND file_type = 'SQL' AND del_yn = 'N'
                LIMIT 1
            """
            result = self.db_utils.execute_query(query, (project_id,))

            if result and len(result) > 0:
                file_id = result[0]['file_id']
                debug(f"inferred 테이블용 file_id 찾음: {file_id}")
                return file_id
            else:
                # inferred 테이블용으로는 Java 파일도 사용 가능
                return self._get_inferred_file_id(project_id)

        except Exception as e:
            # 시스템 에러: 데이터베이스 연결 실패 등 - 프로그램 종료
            handle_error(e, "inferred 테이블용 file_id 조회 실패")
            return None

    def _get_inferred_file_id(self, project_id: int) -> Optional[int]:
        """
        inferred 클래스용 file_id 찾기 (Java 파일 중 하나 선택)
        USER RULES: 공통함수 사용, 하드코딩 금지

        Args:
            project_id: 프로젝트 ID

        Returns:
            file_id 또는 None
        """
        try:
            # USER RULES: 공통함수 사용 - DatabaseUtils의 execute_query 사용
            query = """
                SELECT file_id
                FROM files
                WHERE project_id = ? AND file_type = 'JAVA' AND del_yn = 'N'
                LIMIT 1
            """
            result = self.db_utils.execute_query(query, (project_id,))

            if result and len(result) > 0:
                file_id = result[0]['file_id']
                debug(f"inferred 클래스용 file_id 찾음: {file_id}")
                return file_id
            else:
                # 시스템 에러: Java 파일이 files 테이블에 없는 것은 1단계에서 처리되지 않았음을 의미
                error("Java 파일이 files 테이블에 없습니다. 1단계 파일 스캔이 제대로 실행되지 않았습니다.")
                return None

        except Exception as e:
            # 시스템 에러: 데이터베이스 연결 실패 등 - 프로그램 종료
            handle_error(e, "inferred 클래스용 file_id 조회 실패")
            return None

    def _get_project_id(self) -> Optional[int]:
        """프로젝트 ID 조회 (USER RULES: 공통함수 사용)"""
        try:
            return self.db_utils.get_project_id(self.project_name)
        except Exception as e:
            # 시스템 에러: 데이터베이스 연결 실패 등 - 프로그램 종료
            handle_error(e, "프로젝트 ID 조회 실패")
            return None

    def _get_file_id(self, file_path: str) -> Optional[int]:
        """
        파일 ID 조회 (USER RULES: 공통함수 사용)

        Args:
            file_path: 파일 경로

        Returns:
            파일 ID
        """
        try:
            # USER RULES: 공통함수 사용 - PathUtils로 상대경로 변환
            path_utils = PathUtils()
            # 프로젝트 소스 경로 기준으로 상대경로 생성
            relative_path = path_utils.get_relative_path(file_path, self.project_source_path)
            
            # USER RULES: 경로 구분자 정규화 - Unix 스타일로 통일 (1단계에서 저장된 형태와 일치)
            relative_path = path_utils.normalize_path_separator(relative_path, 'unix')

            # 파일 ID 조회 - file_path와 file_name을 합쳐서 조회
            # relative_path에서 디렉토리와 파일명 분리
            import os
            dir_path = os.path.dirname(relative_path)
            file_name = os.path.basename(relative_path)
            
            # 경로 구분자 정규화 (Windows 스타일로 변환 - 1단계에서 저장된 형태와 일치)
            dir_path = path_utils.normalize_path_separator(dir_path, 'windows')
            
            file_query = """
                SELECT file_id FROM files
                WHERE project_id = (SELECT project_id FROM projects WHERE project_name = ?)
                AND file_path = ?
                AND file_name = ?
                AND del_yn = 'N'
            """

            file_results = self.db_utils.execute_query(file_query, (self.project_name, dir_path, file_name))

            if file_results:
                return file_results[0]['file_id']
            else:
                # 시스템 에러: Java 파일이 files 테이블에 없는 것은 1단계에서 처리되지 않았음을 의미
                error(f"파일 ID를 찾을 수 없습니다: {relative_path} (원본: {file_path}). 1단계 파일 스캔이 제대로 실행되지 않았습니다.")
                return None

        except Exception as e:
            # 시스템 에러: 데이터베이스 연결 실패 등 - 프로그램 종료
            handle_error(e, "파일 ID 조회 실패")
            return None

    def _print_java_loading_statistics(self):
        """Java 로딩 통계 출력 (4~5단계 통합)"""
        try:
            info("=== Java 로딩 통계 (4~5단계 통합) ===")
            info(f"처리된 Java 파일: {self.stats['java_files_processed']}개")
            info(f"추출된 클래스: {self.stats['classes_extracted']}개")
            info(f"추출된 메서드: {self.stats['methods_extracted']}개")
            info(f"생성된 컴포넌트: {self.stats['components_created']}개")
            info(f"생성된 상속 관계: {self.stats['inheritance_relationships_created']}개")
            info(f"생성된 CALL_QUERY 관계: {self.stats['call_query_relationships_created']}개")
            info(f"생성된 CALL_METHOD 관계: {self.stats['call_method_relationships_created']}개")
            info(f"생성된 USE_TABLE 관계: {self.stats['use_table_relationships_created']}개")
            info(f"비즈니스 로직 메서드: {self.stats['business_methods_filtered']}개")
            info(f"처리 시간: {self.stats['processing_time']:.2f}초")
            info(f"오류 발생: {self.stats['errors']}개")

        except Exception as e:
            handle_error(e, "통계 출력 실패")

    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        return self.stats.copy()

    def reset_statistics(self):
        """통계 초기화"""
        self.stats = {
            'java_files_processed': 0,
            'classes_extracted': 0,
            'classes_created': 0,
            'methods_extracted': 0,
            'components_created': 0,
            'inheritance_relationships_created': 0,
            'call_query_relationships_created': 0,
            'call_method_relationships_created': 0,
            'use_table_relationships_created': 0,
            'business_methods_filtered': 0,
            'errors': 0,
            'processing_time': 0.0
        }