"""
SQL Content 처리 모듈
- SQL 쿼리 정보를 components 테이블과 sql_contents 테이블에 저장
- 경로 변환 및 데이터 정규화 처리
"""

import os
from typing import List, Dict, Any, Optional
from .database_utils import DatabaseUtils
from .sql_content_manager import SqlContentManager
from .logger import app_logger, info, warning, error, handle_error


class SqlContentProcessor:
    """SQL Content 처리 클래스"""
    
    def __init__(self, project_name: str, db_utils: DatabaseUtils):
        """
        SQL Content Processor 초기화
        
        Args:
            project_name: 프로젝트명
            db_utils: 데이터베이스 유틸리티 인스턴스
        """
        self.project_name = project_name
        self.db_utils = db_utils
        self.sql_content_manager = SqlContentManager(project_name)
        
        # 프로젝트 소스 경로 (상대경로 변환용)
        self.project_source_path = self._get_project_source_path()
        
        # XML 파일 ID 매핑 테이블 (성능 최적화)
        self.xml_file_id_map = {}
        self._load_xml_file_id_map()
    
    def _get_project_source_path(self) -> str:
        """프로젝트 소스 경로 조회"""
        try:
            from .path_utils import get_project_source_path
            return get_project_source_path(self.project_name)
        except Exception as e:
            from .logger import handle_error
            handle_error(e, "프로젝트 소스 경로 조회 실패")
            return f"projects/{self.project_name}/src"
    
    def _load_xml_file_id_map(self):
        """XML 파일 ID 매핑 테이블을 메모리에 로드 (성능 최적화)"""
        try:
            from .path_utils import PathUtils
            
            query = """
                SELECT file_id, file_path, file_name 
                FROM files 
                WHERE file_type = 'XML' AND del_yn = 'N'
            """
            results = self.db_utils.execute_query(query)
            
            path_utils = PathUtils()
            
            for row in results:
                # 공통함수 사용: 크로스플랫폼 경로 정규화
                # file_path는 디렉토리 경로, file_name은 파일명
                full_path = os.path.join(row['file_path'], row['file_name'])
                
                # 프로젝트 루트 기준으로 상대경로 생성 (project_source_path가 아닌 project_root 사용)
                relative_path = path_utils.get_project_relative_path(full_path)
                
                # 크로스플랫폼 경로 구분자 정규화 (Unix 스타일로 통일)
                relative_path = path_utils.normalize_path_separator(relative_path, 'unix')
                
                self.xml_file_id_map[relative_path] = row['file_id']
                
                # 디버그 로그 추가
                app_logger.debug(f"LOAD XML ID 매핑: {row['file_path']} + {row['file_name']} -> {relative_path} (ID: {row['file_id']})")
                
            app_logger.info(f"XML 파일 ID 매핑 로드 완료: {len(self.xml_file_id_map)}개 파일")
            app_logger.debug(f"매핑 테이블 키들: {list(self.xml_file_id_map.keys())}")
            
        except Exception as e:
            from .logger import handle_error
            handle_error(e, "XML 파일 ID 매핑 로드 실패")
            self.xml_file_id_map = {}
    
    def process_sql_queries(self, sql_queries: List[Dict[str, Any]], project_id: int) -> bool:
        """
        SQL 쿼리들을 처리하여 components 테이블과 sql_contents 테이블에 저장
        
        Args:
            sql_queries: SQL 쿼리 정보 리스트
            project_id: 프로젝트 ID
            
        Returns:
            처리 성공 여부
        """
        try:
            app_logger.info(f"=== SQL 쿼리 처리 시작 ===")
            app_logger.info(f"전달받은 SQL 쿼리 수: {len(sql_queries) if sql_queries else 0}")
            app_logger.info(f"프로젝트 ID: {project_id}")
            
            # 답변파일 제안: 강제 출력으로 실행 흐름 확인
            print(f"PRINT: SQL 쿼리 리스트 검증 시작")
            print(f"PRINT: sql_queries 타입: {type(sql_queries)}")
            print(f"PRINT: sql_queries 길이: {len(sql_queries)}")
            print(f"PRINT: iteration 가능 여부: {hasattr(sql_queries, '__iter__')}")
            if sql_queries:
                print(f"PRINT: sql_queries 첫 번째 요소 타입: {type(sql_queries[0])}")
            
            if not sql_queries:
                warning("처리할 SQL 쿼리가 없습니다")
                return True
            
            app_logger.debug("SQL 쿼리 리스트 검증 시작")
            
            # 예외 발생 가능성 체크
            try:
                app_logger.debug(f"SQL 쿼리 리스트 타입: {type(sql_queries)}")
                app_logger.debug(f"SQL 쿼리 리스트 길이: {len(sql_queries)}")
                app_logger.debug(f"첫 번째 쿼리: {sql_queries[0] if sql_queries else 'None'}")
            except Exception as e:
                app_logger.error(f"SQL 쿼리 리스트 검증 실패: {str(e)}")
                from .logger import handle_error
                handle_error(e, "SQL 쿼리 리스트 검증 실패")
                return False
            
            app_logger.debug("SQL 쿼리 리스트 검증 완료")
            
            # SQL 쿼리 타입별 통계
            app_logger.debug("SQL 쿼리 타입별 통계 시작")
            
            # SQL 쿼리 타입별 통계
            query_types = {}
            for query in sql_queries:
                tag_name = query.get('tag_name', 'unknown')
                query_types[tag_name] = query_types.get(tag_name, 0) + 1
            
            app_logger.info(f"SQL 쿼리 타입별 통계: {query_types}")
            
            app_logger.debug("SQL 쿼리 타입별 통계 완료")
            
            component_id_map = {}  # query_id -> component_id 매핑
            processed_count = 0
            skipped_count = 0
            
            app_logger.debug(f"SQL 쿼리 리스트 크기: {len(sql_queries) if sql_queries else 0}")
            app_logger.debug(f"SQL 쿼리 리스트 타입: {type(sql_queries)}")
            
            if sql_queries:
                app_logger.debug(f"첫 번째 쿼리 정보: {sql_queries[0] if len(sql_queries) > 0 else 'None'}")
                app_logger.debug(f"모든 쿼리 정보: {sql_queries}")
            else:
                app_logger.debug("SQL 쿼리 리스트가 비어있습니다")
            
            app_logger.debug("SQL 쿼리 처리 루프 시작 전")
            
            print(f"PRINT: SQL 쿼리 처리 루프 시작 전")
            for i, query_info in enumerate(sql_queries):
                print(f"PRINT: SQL 쿼리 처리 루프 시작: {i+1}/{len(sql_queries)}")
                app_logger.debug(f"SQL 쿼리 처리 루프 시작: {i+1}/{len(sql_queries)}")
                try:
                    # 디버그 로그 추가
                    app_logger.debug(f"SQL 쿼리 처리 시작: {query_info.get('query_id', 'unknown')} ({query_info.get('tag_name', 'unknown')})")
                    
                    # 메모리에서 파일 ID 조회 (성능 최적화)
                    file_id = self._get_file_id_from_memory(query_info['file_path'])
                    if not file_id:
                        # 에러 상황: file_id 조회 실패 - 도움될만한 정보 로그 출력 후 종료
                        app_logger.error(f"파일 ID 조회 실패: {query_info['file_path']}")
                        app_logger.error(f"쿼리 정보: {query_info.get('query_id', 'unknown')} ({query_info.get('tag_name', 'unknown')})")
                        app_logger.error(f"메모리 매핑 테이블 크기: {len(self.xml_file_id_map)}")
                        app_logger.error(f"메모리 매핑 테이블 키들: {list(self.xml_file_id_map.keys())}")
                        app_logger.error(f"프로젝트 소스 경로: {self.project_source_path}")
                        
                        # handle_error()로 프로그램 종료
                        from .logger import handle_error
                        handle_error(Exception(f"파일 ID 조회 실패: {query_info['file_path']}"), "SQL 컴포넌트 등록 실패")
                        return False
                    
                    app_logger.debug(f"파일 ID 조회 성공: {file_id}")
                    
                    # 컴포넌트 저장 및 component_id 획득
                    component_id = self._save_component(query_info, project_id, file_id)
                    app_logger.debug(f"컴포넌트 저장 결과: component_id = {component_id}")
                    
                    if component_id:
                        component_id_map[query_info['query_id']] = component_id
                        
                        # SQL Content 저장
                        self._save_sql_content(query_info, project_id, file_id, component_id)
                        processed_count += 1
                        app_logger.debug(f"SQL 쿼리 처리 완료: {query_info.get('query_id', 'unknown')}")
                    else:
                        app_logger.error(f"컴포넌트 저장 실패로 건너뜀: {query_info.get('query_id', 'unknown')}")
                        skipped_count += 1
                    
                except Exception as e:
                    # 답변파일 제안: 예외 처리 강화 - exc_info=True로 스택 트레이스 확인
                    print(f"PRINT: SQL 쿼리 처리 예외 발생: {query_info.get('query_id', 'unknown')}, {str(e)}")
                    app_logger.error(f"SQL 쿼리 처리 예외: {query_info.get('query_id', 'unknown')}, {str(e)}", exc_info=True)
                    skipped_count += 1
                    continue
            
            app_logger.info(f"=== SQL 쿼리 처리 완료 ===")
            app_logger.info(f"처리된 쿼리 수: {processed_count}")
            app_logger.info(f"건너뜀 쿼리 수: {skipped_count}")
            app_logger.info(f"컴포넌트 ID 매핑 크기: {len(component_id_map)}")
            
            if component_id_map:
                info(f"SQL 컴포넌트 저장 완료: {processed_count}개 (건너뜀: {skipped_count}개)")
                return True
            else:
                warning(f"저장할 유효한 SQL 컴포넌트가 없습니다 (건너뜀: {skipped_count}개)")
                return True
                
        except Exception as e:
            # 시스템 에러: SQL 쿼리 처리 자체가 실패한 경우 - 프로그램 종료
            handle_error(e, "SQL 쿼리 처리 실패")
            return False
    
    def _get_file_id_from_memory(self, file_path: str) -> Optional[int]:
        """메모리에서 파일 ID 조회 (성능 최적화)"""
        try:
            from .path_utils import PathUtils
            
            # 공통함수 사용: 크로스플랫폼 경로 정규화
            path_utils = PathUtils()
            
            # 프로젝트 소스 경로 기준으로 상대경로 생성
            relative_path = path_utils.get_relative_path(file_path, self.project_source_path)
            
            # 크로스플랫폼 경로 구분자 정규화 (Unix 스타일로 통일)
            relative_path = path_utils.normalize_path_separator(relative_path, 'unix')
            
            # 디버그 로그 추가
            app_logger.debug(f"GET XML ID 조회: {file_path} -> {relative_path}")
            app_logger.debug(f"메모리 매핑 테이블 키들: {list(self.xml_file_id_map.keys())}")
            
            # 메모리 매핑 테이블에서 조회
            file_id = self.xml_file_id_map.get(relative_path)
            
            if file_id:
                app_logger.debug(f"메모리에서 file_id 조회 성공: {relative_path} -> {file_id}")
            else:
                # 에러 상황: file_id 조회 실패 - 도움될만한 정보 로그 출력 후 종료
                app_logger.error(f"메모리에서 file_id 조회 실패: {relative_path}")
                app_logger.error(f"매핑 테이블의 모든 키들:")
                for key in self.xml_file_id_map.keys():
                    app_logger.error(f"  - {key}")
                
                from .logger import handle_error
                handle_error(Exception(f"file_id 조회 실패: {relative_path}"), "XML 파일 ID 조회 실패")
                
            return file_id
            
        except Exception as e:
            from .logger import handle_error
            handle_error(e, f"메모리 file_id 조회 실패: {file_path}")
            return None
    
    
    def _save_component(self, query_info: Dict[str, Any], project_id: int, file_id: int) -> Optional[int]:
        """컴포넌트를 components 테이블에 저장하고 component_id 반환"""
        try:
            # 컴포넌트 데이터 생성
            component_data = {
                'project_id': project_id,
                'component_type': f"SQL_{query_info['tag_name'].upper()}",
                'component_name': query_info['query_id'],  # query_id 사용
                'parent_id': None,
                'layer': 'SQL',  # SQL 컴포넌트는 layer를 'SQL'로 설정
                'file_id': file_id,
                'line_start': query_info.get('line_start'),
                'line_end': query_info.get('line_end'),
                'hash_value': query_info['hash_value'],
                'has_error': 'N',
                'error_message': None,
                'del_yn': 'N'
            }
            
            # 디버그 로그 추가
            app_logger.debug(f"컴포넌트 저장 시도: {query_info['query_id']} ({query_info['tag_name']}) -> {component_data['component_type']}")
            
            # INSERT OR REPLACE WITH ID 실행
            component_id = self.db_utils.insert_or_replace_with_id('components', component_data)
            
            if component_id > 0:
                app_logger.debug(f"컴포넌트 저장 완료: {query_info['query_id']} (ID: {component_id})")
                return component_id
            else:
                # 에러 상황: 컴포넌트 저장 실패 - 도움될만한 정보 로그 출력 후 종료
                app_logger.error(f"컴포넌트 저장 실패: {query_info['query_id']} ({query_info['tag_name']}) - component_id: {component_id}")
                app_logger.error(f"컴포넌트 데이터: {component_data}")
                
                # handle_error()로 프로그램 종료
                from .logger import handle_error
                handle_error(Exception(f"컴포넌트 저장 실패: {query_info['query_id']}"), "SQL 컴포넌트 저장 실패")
                return None
                
        except Exception as e:
            # 에러 상황: 컴포넌트 저장 예외 - 도움될만한 정보 로그 출력 후 종료
            app_logger.error(f"컴포넌트 저장 예외: {query_info.get('query_id', 'unknown')} ({query_info.get('tag_name', 'unknown')}), {str(e)}")
            app_logger.error(f"컴포넌트 데이터: {component_data}")
            
            # handle_error()로 프로그램 종료
            from .logger import handle_error
            handle_error(e, "SQL 컴포넌트 저장 예외")
            return None
    
    def _save_sql_content(self, query_info: Dict[str, Any], project_id: int, file_id: int, component_id: int) -> bool:
        """SQL Content를 SqlContent DB에 저장 (실패 시 경고만 발생)"""
        try:
            # SqlContentManager가 초기화되지 않았으면 경고 후 종료
            if not self.sql_content_manager or not self.sql_content_manager.initialized:
                warning(f"SqlContentManager가 초기화되지 않아 SQL Content 저장을 건너뜁니다: {query_info.get('query_id', 'unknown')}")
                return False

            app_logger.debug(f"SQL Content 저장 시작: {query_info.get('query_id', 'unknown')} (component_id: {component_id})")
            
            from .path_utils import PathUtils
            path_utils = PathUtils()
            relative_file_path = path_utils.get_relative_path(query_info['file_path'], self.project_source_path)
            relative_file_path = os.path.dirname(relative_file_path)
            relative_file_path = path_utils.normalize_path_separator(relative_file_path, 'unix')
            
            app_logger.debug(f"SQL Content 상대경로: {relative_file_path}")
            
            success = self.sql_content_manager.save_sql_content(
                sql_content=query_info['sql_content'],
                project_id=project_id,
                file_id=file_id,
                component_id=component_id,
                query_type=f"SQL_{query_info['tag_name'].upper()}",
                file_path=relative_file_path,
                component_name=query_info['query_id'],
                file_name=os.path.basename(query_info['file_path']),
                line_start=query_info.get('line_start'),
                line_end=query_info.get('line_end'),
                hash_value=query_info['hash_value']
            )
            
            if success:
                app_logger.debug(f"SQL Content 저장 완료: {query_info['query_id']} - {relative_file_path}")
            else:
                # USER RULES: 파싱 에러가 아닌 모든 exception은 handle_error()로 exit()
                handle_error(Exception(f"SQL Content 저장 실패: {query_info.get('query_id', 'unknown')}"), "SQL Content 저장 실패")
            
            return success
            
        except Exception as e:
            # USER RULES: 파싱 에러가 아닌 모든 exception은 handle_error()로 exit()
            handle_error(e, f"SQL Content 저장 중 예외 발생: {query_info.get('query_id', 'unknown')}")
            return False
    
    
    def _convert_to_directory_path(self, absolute_path: str) -> str:
        """절대경로를 상대경로로 변환 (디렉토리 경로만)"""
        try:
            # 프로젝트 소스 경로를 기준으로 상대경로 계산
            if absolute_path.startswith(self.project_source_path):
                relative_path = os.path.relpath(absolute_path, self.project_source_path)
                # 파일명 제거 (디렉토리 경로만)
                dir_path = os.path.dirname(relative_path)
                app_logger.debug(f"경로 변환: 절대경로={absolute_path}, 상대경로={relative_path}, 디렉토리경로={dir_path}")
                return dir_path
            else:
                # 프로젝트 경로에 포함되지 않은 경우 원본 경로 사용
                dir_path = os.path.dirname(absolute_path)
                app_logger.debug(f"경로 변환 (프로젝트 외부): 절대경로={absolute_path}, 디렉토리경로={dir_path}")
                return dir_path
        except Exception as e:
            from .logger import handle_error
            handle_error(e, f"경로 변환 실패: {absolute_path}")
            return os.path.dirname(absolute_path)
    
    def close(self):
        """리소스 정리"""
        if self.sql_content_manager:
            self.sql_content_manager.close()
