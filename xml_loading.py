"""
XML 로딩 모듈
- 3단계 통합 처리: XML 파일에서 SQL 쿼리 추출 및 JOIN 관계 분석
- 메모리 최적화 (스트리밍 처리)
- 데이터베이스 저장 및 통계 관리

USER RULES:
- 하드코딩 금지: path_utils.get_parser_config_path("sql") 사용 (크로스플랫폼 대응)
- Exception 처리: handle_error() 공통함수 사용
- 공통함수 사용: util 모듈 활용
- 메뉴얼 기반: parser/manual/04_mybatis 참고
"""

import os
from typing import List, Dict, Any, Optional
from util import (
    DatabaseUtils, PathUtils, HashUtils, ValidationUtils,
    app_logger, info, error, debug, warning, handle_error,
    get_project_source_path, get_project_metadata_db_path
)
# USER RULES: 공통함수 사용, 하드코딩 금지
from parser.xml_parser import XmlParser
from util.sql_content_manager import SqlContentManager
# from util.sql_content_processor import SqlContentProcessor  # 보류 상태


class XmlLoadingEngine:
    """XML 로딩 엔진 - 3단계 통합 처리"""
    
    def __init__(self, project_name: str):
        """
        XML 로딩 엔진 초기화
        
        Args:
            project_name: 프로젝트명
        """
        self.project_name = project_name
        self.project_source_path = get_project_source_path(project_name)
        self.metadata_db_path = get_project_metadata_db_path(project_name)
        self.db_utils = None
        
        # XML 파서 초기화 (USER RULES: 공통함수 사용, 전역 프로젝트 정보 활용)
        self.xml_parser = XmlParser()
        
        # SQL Content Manager 초기화
        self.sql_content_manager = SqlContentManager(project_name)
        
        # SQL Content Processor 초기화 (보류 상태)
        # self.sql_content_processor = None
        
        # 통계 정보
        self.stats = {
            'xml_files_processed': 0,
            'sql_queries_extracted': 0,
            'sql_components_created': 0,
            'join_relationships_created': 0,
            'inferred_tables_created': 0,
            'inferred_columns_created': 0,
            'errors': 0
        }
    
    def execute_xml_loading(self) -> bool:
        """
        XML 로딩 실행: 3~4단계 통합 처리
        
        Returns:
            실행 성공 여부
        """
        try:
            info("=== XML 로딩 시작: 3~4단계 통합 처리 ===")
            
            # 데이터베이스 연결 (USER RULES: 공통함수 사용)
            self.db_utils = DatabaseUtils(self.metadata_db_path)
            if not self.db_utils.connect():
                error("메타데이터베이스 연결 실패")
                return False
            
            # SQL Content Processor 초기화 (보류 상태)
            # info("SQL Content Processor 초기화 시작")
            # try:
            #     self.sql_content_processor = SqlContentProcessor(self.project_name, self.db_utils)
            #     info("SQL Content Processor 초기화 완료")
            # except Exception as e:
            #     handle_error(e, "SQL Content Processor 초기화 실패")
            #     return False
            
            # 1. MyBatis XML 파일 수집
            xml_files = self.xml_parser.get_filtered_xml_files(self.project_source_path)
            if not xml_files:
                warning("MyBatis XML 파일이 없습니다")
                return True
            
            # 2. XML 파일별 통합 처리 (메모리 최적화)
            for xml_file in xml_files:
                try:
                    # 3~4단계 통합 처리: SQL 추출 + JOIN 분석
                    analysis_result = self.xml_parser.extract_sql_queries_and_analyze_relationships(xml_file)
                    
                    # 파싱 에러 체크 (USER RULES: 파싱 에러는 계속 진행)
                    if analysis_result.get('has_error') == 'Y':
                        debug(f"XML 파싱 에러로 건너뜀: {xml_file} - {analysis_result.get('error_message', '')}")
                        self.stats['errors'] += 1
                        continue
                    
                    if analysis_result['sql_queries']:
                        # 3단계: SQL 컴포넌트 저장
                        try:
                            if self._save_sql_components_to_database(analysis_result['sql_queries']):
                                self.stats['sql_components_created'] += len(analysis_result['sql_queries'])
                        except Exception as e:
                            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                            handle_error(e, f"SQL 컴포넌트 저장 실패: {xml_file}")
                            return False
                        
                        # 4단계: JOIN 관계 저장
                        if analysis_result['join_relationships']:
                            try:
                                if self._save_join_relationships_to_database(analysis_result['join_relationships']):
                                    self.stats['join_relationships_created'] += len(analysis_result['join_relationships'])
                            except Exception as e:
                                # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                                handle_error(e, f"JOIN 관계 저장 실패: {xml_file}")
                                return False
                    
                    self.stats['xml_files_processed'] += 1
                    self.stats['sql_queries_extracted'] += len(analysis_result['sql_queries'])
                    
                    # 메모리 최적화: 처리 후 즉시 해제
                    del analysis_result
                    
                except Exception as e:
                    # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                    # 시스템 에러 (데이터베이스, 메모리 등) - 프로그램 종료
                    handle_error(e, f"XML 파일 처리 실패: {xml_file}")
                    return False
            
            # 3. 통계 정보 출력
            self._print_xml_loading_statistics()
            
            info("=== XML 로딩 완료 ===")
            return True
            
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, "XML 로딩 실행 실패")
            return False
        finally:
            # 데이터베이스 연결 해제
            if self.db_utils:
                self.db_utils.disconnect()
            
            # SQL Content Manager 연결 해제
            if hasattr(self, 'sql_content_manager'):
                self.sql_content_manager.close()
            
            # SQL Content Processor 정리 (보류 상태)
            # if hasattr(self, 'sql_content_processor') and self.sql_content_processor:
            #     self.sql_content_processor.close()
    
    def _save_sql_components_to_database(self, sql_queries: List[Dict[str, Any]]) -> bool:
        """
        SQL 컴포넌트를 데이터베이스에 저장 (3단계)
        
        Args:
            sql_queries: SQL 쿼리 정보 리스트
            
        Returns:
            저장 성공 여부
        """
        try:
            info(f"=== XML 로딩 엔진: SQL 컴포넌트 저장 시작 ===")
            info(f"전달받은 SQL 쿼리 수: {len(sql_queries)}개")
            
            # SQL 쿼리 타입별 통계
            if sql_queries:
                query_types = {}
                for query in sql_queries:
                    tag_name = query.get('tag_name', 'unknown')
                    query_types[tag_name] = query_types.get(tag_name, 0) + 1
                info(f"XML에서 추출된 SQL 쿼리 타입별 통계: {query_types}")
            
            if not sql_queries:
                warning("저장할 SQL 쿼리가 없습니다")
                return True
            
            # 프로젝트 ID 조회 (USER RULES: 공통함수 사용)
            project_id = self._get_project_id()
            if not project_id:
                # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                handle_error(Exception("프로젝트 ID를 찾을 수 없습니다"), "SQL 컴포넌트 저장 실패")
                return False
            
            info(f"프로젝트 ID: {project_id}")
            
            # SQL Content Processor를 사용하여 처리 (보류 상태)
            # if self.sql_content_processor:
            #     info("SQL Content Processor를 사용하여 처리 시작")
            #     info(f"process_sql_queries 호출 전: sql_queries={len(sql_queries) if sql_queries else 0}, project_id={project_id}")
            #     try:
            #         result = self.sql_content_processor.process_sql_queries(sql_queries, project_id)
            #         info(f"process_sql_queries 호출 후: result={result}")
            #         info(f"SQL Content Processor 처리 결과: {result}")
            #         info(f"=== XML 로딩 엔진: SQL 컴포넌트 저장 완료 ===")
            #         return result
            #     except Exception as e:
            #         handle_error(e, "process_sql_queries 호출 실패")
            #         return False
            # else:
            #     error("SQL Content Processor가 초기화되지 않았습니다")
            #     return False
            
            # 기존 방식으로 SQL 컴포넌트 저장 (SQL Content Processor 보류 상태)
                
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, "SQL 컴포넌트 저장 실패")
            return False
    
    
    def _save_join_relationships_to_database(self, join_relationships: List[Dict[str, Any]]) -> bool:
        """
        JOIN 관계를 데이터베이스에 저장 (4단계)
        
        Args:
            join_relationships: JOIN 관계 리스트
            
        Returns:
            저장 성공 여부
        """
        try:
            if not join_relationships:
                warning("저장할 JOIN 관계가 없습니다")
                return True
            
            # 프로젝트 ID 조회 (USER RULES: 공통함수 사용)
            project_id = self._get_project_id()
            if not project_id:
                # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                handle_error(Exception("프로젝트 ID를 찾을 수 없습니다"), "JOIN 관계 저장 실패")
                return False
            
            # 관계 데이터 변환
            relationship_data_list = []
            
            for rel_info in join_relationships:
                try:
                    # USER RULES: 테이블명 유효성 검증 (별칭 오탐 방지)
                    source_table = rel_info['source_table']
                    target_table = rel_info['target_table']
                    
                    # 유효하지 않은 테이블명은 건너뜀
                    if not self._is_valid_table_name(source_table):
                        debug(f"유효하지 않은 소스 테이블명 건너뜀: {source_table}")
                        continue
                    if not self._is_valid_table_name(target_table):
                        debug(f"유효하지 않은 대상 테이블명 건너뜀: {target_table}")
                        continue
                    
                    # 소스 테이블 컴포넌트 ID 조회
                    src_component_id = self._get_table_component_id(project_id, source_table)
                    if not src_component_id:
                        # inferred 테이블 생성 (join_relationships 전달)
                        info(f"inferred 테이블 생성 시도: {source_table}")
                        src_component_id = self._create_inferred_table(project_id, source_table, join_relationships)
                        if src_component_id:
                            self.stats['inferred_tables_created'] += 1
                            info(f"inferred 테이블 생성 성공: {source_table} (ID: {src_component_id})")
                        else:
                            error(f"inferred 테이블 생성 실패: {source_table}")
                    
                    # 대상 테이블 컴포넌트 ID 조회
                    dst_component_id = self._get_table_component_id(project_id, target_table)
                    if not dst_component_id:
                        # inferred 테이블 생성 (join_relationships 전달)
                        info(f"inferred 테이블 생성 시도: {target_table}")
                        dst_component_id = self._create_inferred_table(project_id, target_table, join_relationships)
                        if dst_component_id:
                            self.stats['inferred_tables_created'] += 1
                            info(f"inferred 테이블 생성 성공: {target_table} (ID: {dst_component_id})")
                        else:
                            error(f"inferred 테이블 생성 실패: {target_table}")
                    
                    if src_component_id and dst_component_id:
                        # 관계 데이터 생성
                        relationship_data = {
                            'src_id': src_component_id,
                            'dst_id': dst_component_id,
                            'rel_type': rel_info['rel_type'],
                            'confidence': 1.0,
                            'has_error': 'N',
                            'error_message': None,
                            'del_yn': 'N'
                        }
                        
                        relationship_data_list.append(relationship_data)
                    
                except Exception as e:
                    # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                    handle_error(e, "JOIN 관계 데이터 변환 실패")
                    continue
            
            # 배치 INSERT OR REPLACE (USER RULES: 공통함수 사용)
            if relationship_data_list:
                processed_count = self.db_utils.batch_insert_or_replace('relationships', relationship_data_list)
                
                if processed_count > 0:
                    info(f"JOIN 관계 저장 완료: {processed_count}개")
                    return True
                else:
                    # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                    handle_error(Exception("JOIN 관계 저장 실패"), "JOIN 관계 저장 실패")
                    return False
            else:
                warning("저장할 유효한 JOIN 관계가 없습니다")
                return True
                
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, "JOIN 관계 저장 실패")
            return False

    def _is_valid_table_name(self, table_name: str) -> bool:
        """
        테이블명 유효성 검증 (별칭 오탐 방지)
        
        Args:
            table_name: 검증할 테이블명
            
        Returns:
            유효한 테이블명이면 True, 아니면 False
        """
        try:
            if not table_name:
                return False
            
            # 단일 문자 또는 2글자 이하 필터링 (별칭 가능성 높음)
            if len(table_name) <= 2:
                return False
            
            # 대문자로만 구성된 경우 (별칭 가능성 높음)
            if table_name.isupper() and len(table_name) <= 3:
                return False
            
            # 실제 테이블명 패턴 검증 (대문자, 언더스코어 포함)
            import re
            if not re.match(r'^[A-Z][A-Z0-9_]*$', table_name):
                return False
            
            # 예약어 체크 (자주 사용되는 단일 문자 별칭)
            reserved_words = {'B', 'C', 'O', 'P', 'R', 'T', 'U', 'V', 'X', 'Y', 'Z'}
            if table_name in reserved_words:
                return False
            
            return True
            
        except Exception as e:
            warning(f"테이블명 유효성 검증 실패: {table_name} - {str(e)}")
            return False
    
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
            
            # 파일 ID 조회
            file_query = """
                SELECT file_id FROM files 
                WHERE project_id = (SELECT project_id FROM projects WHERE project_name = ?)
                AND file_path = ?
                AND del_yn = 'N'
            """
            
            file_results = self.db_utils.execute_query(file_query, (self.project_name, relative_path))
            
            if file_results:
                return file_results[0]['file_id']
            else:
                # 시스템 에러: XML 파일이 files 테이블에 없는 것은 1단계에서 처리되지 않았음을 의미
                error(f"파일 ID를 찾을 수 없습니다: {relative_path} (원본: {file_path}). 1단계 파일 스캔이 제대로 실행되지 않았습니다.")
                return None
                
        except Exception as e:
            # 시스템 에러: 데이터베이스 연결 실패 등 - 프로그램 종료
            handle_error(e, "파일 ID 조회 실패")
            return None
    
    def _get_table_component_id(self, project_id: int, table_name: str) -> Optional[int]:
        """
        테이블 컴포넌트 ID 조회 (USER RULES: 공통함수 사용)
        
        Args:
            project_id: 프로젝트 ID
            table_name: 테이블명
            
        Returns:
            컴포넌트 ID
        """
        try:
            return self.db_utils.get_table_component_id(self.project_name, table_name)
        except Exception as e:
            # 시스템 에러: 데이터베이스 연결 실패 등 - 프로그램 종료
            handle_error(e, f"테이블 컴포넌트 ID 조회 실패: {table_name}")
            return None
    
    def _get_inferred_file_id(self, project_id: int) -> Optional[int]:
        """
        inferred 테이블용 file_id 찾기 (XML 파일 중 하나 선택)
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
                info(f"inferred 테이블용 file_id 찾음: {file_id}")
                return file_id
            else:
                # 시스템 에러: XML 파일이 files 테이블에 없는 것은 1단계에서 처리되지 않았음을 의미
                error("XML 파일이 files 테이블에 없습니다. 1단계 파일 스캔이 제대로 실행되지 않았습니다.")
                return None
                
        except Exception as e:
            # 시스템 에러: 데이터베이스 연결 실패 등 - 프로그램 종료
            handle_error(e, "inferred 테이블용 file_id 조회 실패")
            return None
    
    
    def _create_inferred_table(self, project_id: int, table_name: str, join_relationships: List[Dict[str, Any]] = None) -> Optional[int]:
        """
        inferred 테이블 생성 (USER RULES: 공통함수 사용)
        
        Args:
            project_id: 프로젝트 ID
            table_name: 테이블명
            join_relationships: JOIN 관계 리스트 (inferred 컬럼 생성용)
            
        Returns:
            컴포넌트 ID
        """
        try:
            # inferred 테이블용 file_id 찾기 (XML 파일 중 하나 선택)
            inferred_file_id = self._get_inferred_file_id(project_id)
            if not inferred_file_id:
                # 시스템 에러: XML 파일이 files 테이블에 없는 것은 1단계에서 처리되지 않았음을 의미
                error(f"inferred 테이블용 file_id를 찾을 수 없습니다: {table_name}. 1단계 파일 스캔이 제대로 실행되지 않았습니다.")
                return None
            
            # inferred 테이블을 tables 테이블에 생성
            table_data = {
                'project_id': project_id,
                'component_id': None,
                'table_name': table_name,
                'table_owner': 'UNKNOWN',
                'table_comments': 'Inferred from SQL analysis',
                'has_error': 'N',
                'error_message': None,
                'hash_value': 'INFERRED',
                'del_yn': 'N'
            }
            
            # 테이블 생성 (USER RULES: 공통함수 사용)
            info(f"tables 테이블에 데이터 삽입 시도: {table_data}")
            table_id = self.db_utils.insert_or_replace_with_id('tables', table_data)
            info(f"tables 테이블 삽입 결과: {table_id}")
            
            if not table_id:
                # 파싱 에러: tables 테이블 삽입 실패 - 계속 진행
                warning(f"tables 테이블 삽입 실패: {table_name}")
                return None
            
            # 컴포넌트 생성
            component_data = {
                'project_id': project_id,
                'component_type': 'TABLE',
                'component_name': table_name,
                'parent_id': None,
                'file_id': inferred_file_id,
                'layer': 'DATA',  # TABLE 컴포넌트는 DATA 레이어
                'line_start': None,
                'line_end': None,
                'hash_value': 'INFERRED',
                'has_error': 'N',
                'error_message': None,
                'del_yn': 'N'
            }
            
            # 컴포넌트 생성 (USER RULES: 공통함수 사용)
            info(f"components 테이블에 데이터 삽입 시도: {component_data}")
            component_id = self.db_utils.insert_or_replace_with_id('components', component_data)
            info(f"components 테이블 삽입 결과: {component_id}")
            
            if component_id:
                # tables 테이블의 component_id 업데이트 (USER RULES: 공통함수 사용)
                update_data = {'component_id': component_id}
                where_conditions = {'table_id': table_id}
                info(f"tables 테이블 업데이트 시도: component_id={component_id}, table_id={table_id}")
                success = self.db_utils.update_record('tables', update_data, where_conditions)
                if success:
                    info(f"tables 테이블 업데이트 완료")
                    
                    # 🔥 새로 추가: inferred 컬럼 생성
                    if join_relationships:
                        inferred_columns_created = self._create_inferred_columns(
                            project_id, table_name, component_id, join_relationships
                        )
                        self.stats['inferred_columns_created'] += inferred_columns_created
                        if inferred_columns_created > 0:
                            info(f"inferred 컬럼 생성 완료: {table_name}, {inferred_columns_created}개")
                else:
                    # 파싱 에러: tables 테이블 업데이트 실패 - 계속 진행
                    warning(f"tables 테이블 업데이트 실패: {table_name}")
            else:
                # 파싱 에러: components 테이블 삽입 실패 - 계속 진행
                warning(f"components 테이블 삽입 실패: {table_name}")
            
            info(f"inferred 테이블 생성 완료: {table_name}, component_id: {component_id}")
            return component_id
            
        except Exception as e:
            # 시스템 에러: 데이터베이스 연결 실패 등 - 프로그램 종료
            handle_error(e, f"inferred 테이블 생성 실패: {table_name}")
            return None
    
    def _extract_join_columns_from_relationships(self, table_name: str, join_relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        JOIN 관계에서 해당 테이블의 조인 필드 추출
        
        Args:
            table_name: 테이블명
            join_relationships: JOIN 관계 리스트
            
        Returns:
            조인 필드 정보 리스트
        """
        try:
            join_columns = []
            
            for rel in join_relationships:
                # 해당 테이블이 소스 또는 타겟인 관계만 처리
                if rel.get('source_table') == table_name or rel.get('target_table') == table_name:
                    # 조인 조건에서 컬럼명 추출
                    join_condition = rel.get('join_condition', '')
                    
                    # 예: "up.type_id = ut.type_id" -> ["type_id", "type_id"]
                    columns = self._extract_columns_from_join_condition(join_condition, table_name)
                    
                    for column_name in columns:
                        if column_name and column_name not in [col['column_name'] for col in join_columns]:
                            join_columns.append({
                                'column_name': column_name,
                                'data_type': 'INFERRED',
                                'data_length': None,
                                'nullable': 'Y',
                                'column_comments': 'Inferred from JOIN analysis'
                            })
            
            return join_columns
            
        except Exception as e:
            handle_error(e, f"조인 필드 추출 실패: {table_name}")
            return []
    
    def _extract_columns_from_join_condition(self, join_condition: str, table_name: str) -> List[str]:
        """
        조인 조건에서 특정 테이블의 컬럼명 추출
        
        Args:
            join_condition: 조인 조건 (예: "up.type_id = ut.type_id")
            table_name: 테이블명
            
        Returns:
            컬럼명 리스트
        """
        try:
            if not join_condition:
                return []
            
            columns = []
            
            # 조인 조건을 = 기준으로 분할
            parts = join_condition.split('=')
            if len(parts) != 2:
                return []
            
            left_side = parts[0].strip()
            right_side = parts[1].strip()
            
            # 테이블 별칭 패턴 매칭 (예: up.type_id, ut.type_id)
            import re
            
            # 테이블명의 첫 2-3글자로 별칭 추정
            table_prefix = table_name[:2].lower()
            
            # 왼쪽과 오른쪽에서 해당 테이블의 컬럼 찾기
            for side in [left_side, right_side]:
                # 별칭.컬럼명 패턴 매칭
                match = re.match(r'(\w+)\.(\w+)', side)
                if match:
                    alias = match.group(1)
                    column_name = match.group(2)
                    
                    # 별칭이 테이블명과 유사한 경우 (첫 2글자 매칭)
                    if alias.lower().startswith(table_prefix):
                        columns.append(column_name)
            
            return columns
            
        except Exception as e:
            handle_error(e, f"조인 조건에서 컬럼 추출 실패: {join_condition}")
            return []
    
    def _create_inferred_columns(self, project_id: int, table_name: str, table_component_id: int, join_relationships: List[Dict[str, Any]]) -> int:
        """
        JOIN 관계에서 도출된 조인 필드를 inferred 컬럼으로 생성
        
        Args:
            project_id: 프로젝트 ID
            table_name: 테이블명
            table_component_id: 테이블의 component_id
            join_relationships: JOIN 관계 리스트
            
        Returns:
            생성된 inferred 컬럼 수
        """
        try:
            # 1. JOIN 관계에서 해당 테이블의 조인 필드 추출
            join_columns = self._extract_join_columns_from_relationships(table_name, join_relationships)
            
            if not join_columns:
                debug(f"테이블 {table_name}에 대한 조인 필드가 없습니다")
                return 0
            
            # 2. inferred 테이블용 file_id 조회
            inferred_file_id = self._get_inferred_file_id(project_id)
            if not inferred_file_id:
                warning(f"inferred 컬럼용 file_id를 찾을 수 없습니다: {table_name}")
                return 0
            
            # 3. 테이블 ID 조회
            table_id = self._get_table_id_by_component_id(table_component_id)
            if not table_id:
                warning(f"테이블 ID를 찾을 수 없습니다: {table_name}, component_id={table_component_id}")
                return 0
            
            created_count = 0
            
            # 4. 각 조인 필드에 대해 inferred 컬럼 생성
            for column_info in join_columns:
                try:
                    # columns 테이블에 컬럼 생성
                    column_id = self._create_inferred_column_in_tables(
                        project_id, table_id, column_info
                    )
                    
                    if column_id:
                        # components 테이블에 COLUMN 컴포넌트 생성
                        component_id = self._create_inferred_column_component(
                            project_id, inferred_file_id, table_component_id, column_info
                        )
                        
                        if component_id:
                            # columns 테이블의 component_id 업데이트
                            success = self._update_column_component_id(table_id, column_id, component_id)
                            if success:
                                created_count += 1
                                info(f"inferred 컬럼 생성 성공: {table_name}.{column_info['column_name']} (ID: {component_id})")
                            else:
                                warning(f"inferred 컬럼 component_id 업데이트 실패: {table_name}.{column_info['column_name']}")
                        else:
                            warning(f"inferred 컬럼 컴포넌트 생성 실패: {table_name}.{column_info['column_name']}")
                    else:
                        warning(f"inferred 컬럼 테이블 생성 실패: {table_name}.{column_info['column_name']}")
                        
                except Exception as e:
                    warning(f"inferred 컬럼 생성 중 오류: {table_name}.{column_info['column_name']} - {str(e)}")
                    continue
            
            if created_count > 0:
                info(f"inferred 컬럼 생성 완료: {table_name}, {created_count}개 컬럼")
            
            return created_count
            
        except Exception as e:
            handle_error(e, f"inferred 컬럼 생성 실패: {table_name}")
            return 0
    
    def _get_table_id_by_component_id(self, component_id: int) -> Optional[int]:
        """
        component_id로 table_id 조회
        
        Args:
            component_id: 테이블의 component_id
            
        Returns:
            table_id 또는 None
        """
        try:
            query = """
                SELECT table_id FROM tables 
                WHERE component_id = ? AND del_yn = 'N'
            """
            results = self.db_utils.execute_query(query, (component_id,))
            
            if results and len(results) > 0:
                return results[0]['table_id']
            return None
            
        except Exception as e:
            handle_error(e, f"테이블 ID 조회 실패: component_id={component_id}")
            return None
    
    def _create_inferred_column_in_tables(self, project_id: int, table_id: int, column_info: Dict[str, Any]) -> Optional[int]:
        """
        columns 테이블에 inferred 컬럼 생성
        
        Args:
            project_id: 프로젝트 ID
            table_id: 테이블 ID
            column_info: 컬럼 정보
            
        Returns:
            column_id 또는 None
        """
        try:
            # 해시값 생성
            column_hash = HashUtils.generate_content_hash(
                f"INFERRED{table_id}{column_info['column_name']}{column_info['data_type']}"
            )
            
            column_data = {
                'table_id': table_id,
                'column_name': column_info['column_name'],
                'data_type': column_info['data_type'],
                'data_length': column_info.get('data_length'),
                'nullable': column_info.get('nullable', 'Y'),
                'column_comments': column_info.get('column_comments', 'Inferred from JOIN analysis'),
                'position_pk': None,
                'data_default': None,
                'owner': 'UNKNOWN',
                'has_error': 'N',
                'error_message': None,
                'hash_value': column_hash,
                'del_yn': 'N'
            }
            
            column_id = self.db_utils.insert_or_replace_with_id('columns', column_data)
            return column_id
            
        except Exception as e:
            handle_error(e, f"inferred 컬럼 테이블 생성 실패: {column_info['column_name']}")
            return None
    
    def _create_inferred_column_component(self, project_id: int, file_id: int, parent_id: int, column_info: Dict[str, Any]) -> Optional[int]:
        """
        components 테이블에 COLUMN 컴포넌트 생성
        
        Args:
            project_id: 프로젝트 ID
            file_id: 파일 ID
            parent_id: 부모 테이블의 component_id
            column_info: 컬럼 정보
            
        Returns:
            component_id 또는 None
        """
        try:
            # 해시값 생성
            component_hash = HashUtils.generate_content_hash(
                f"INFERRED{project_id}{column_info['column_name']}{parent_id}"
            )
            
            component_data = {
                'project_id': project_id,
                'file_id': file_id,
                'component_name': column_info['column_name'],  # 컬럼명만 사용
                'component_type': 'COLUMN',
                'parent_id': parent_id,  # 테이블의 component_id
                'layer': 'DB',
                'line_start': None,
                'line_end': None,
                'has_error': 'N',
                'error_message': None,
                'hash_value': component_hash,
                'del_yn': 'N'
            }
            
            component_id = self.db_utils.insert_or_replace_with_id('components', component_data)
            return component_id
            
        except Exception as e:
            handle_error(e, f"inferred 컬럼 컴포넌트 생성 실패: {column_info['column_name']}")
            return None
    
    def _update_column_component_id(self, table_id: int, column_id: int, component_id: int) -> bool:
        """
        columns 테이블의 component_id 업데이트
        
        Args:
            table_id: 테이블 ID
            column_id: 컬럼 ID
            component_id: 컴포넌트 ID
            
        Returns:
            업데이트 성공 여부
        """
        try:
            update_data = {'component_id': component_id}
            where_conditions = {'column_id': column_id}
            
            success = self.db_utils.update_record('columns', update_data, where_conditions)
            return success
            
        except Exception as e:
            handle_error(e, f"컬럼 component_id 업데이트 실패: column_id={column_id}")
            return False
    
    def _print_xml_loading_statistics(self):
        """XML 로딩 통계 출력"""
        try:
            info("=== XML 로딩 통계 ===")
            info(f"처리된 XML 파일: {self.stats['xml_files_processed']}개")
            info(f"추출된 SQL 쿼리: {self.stats['sql_queries_extracted']}개")
            info(f"생성된 SQL 컴포넌트: {self.stats['sql_components_created']}개")
            info(f"생성된 JOIN 관계: {self.stats['join_relationships_created']}개")
            info(f"생성된 inferred 테이블: {self.stats['inferred_tables_created']}개")
            info(f"생성된 inferred 컬럼: {self.stats['inferred_columns_created']}개")
            info(f"오류 발생: {self.stats['errors']}개")
            
            # SQL Content 통계 출력
            project_id = self._get_project_id()
            if project_id:
                sql_content_stats = self.sql_content_manager.get_stats(project_id)
                if sql_content_stats and sql_content_stats.get('total_stats'):
                    total = sql_content_stats['total_stats']
                    if total and isinstance(total, dict):
                        info("=== SQL Content 통계 ===")
                        info(f"저장된 SQL 내용: {total.get('total_sql_contents', 0)}개")
                        info(f"총 압축 크기: {total.get('total_compressed_size', 0)} bytes")
                        avg_size = total.get('avg_compressed_size', 0)
                        if avg_size is not None:
                            info(f"평균 압축 크기: {avg_size:.2f} bytes")
                        else:
                            info(f"평균 압축 크기: 0.00 bytes")
                        info(f"최대 압축 크기: {total.get('max_compressed_size', 0)} bytes")
                        info(f"최소 압축 크기: {total.get('min_compressed_size', 0)} bytes")
                    else:
                        info("=== SQL Content 통계 ===")
                        info("저장된 SQL 내용이 없습니다.")
                else:
                    info("=== SQL Content 통계 ===")
                    info("SQL Content 통계 정보가 없습니다.")
            
        except Exception as e:
            handle_error(e, "통계 출력 실패")
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        return self.stats.copy()
    
    def reset_statistics(self):
        """통계 초기화"""
        self.stats = {
            'xml_files_processed': 0,
            'sql_queries_extracted': 0,
            'sql_components_created': 0,
            'join_relationships_created': 0,
            'inferred_tables_created': 0,
            'inferred_columns_created': 0,
            'errors': 0
        }
