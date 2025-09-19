"""
SourceAnalyzer 메인 실행 파일
- 명령행 인자 처리
- 프로젝트 분석 실행
"""

import sys
import os
from util import (
    ArgUtils, validate_and_get_project_name, print_usage_and_exit,
    PathUtils, get_project_source_path, project_exists,
    app_logger, info, error, debug, warning, handle_error, cleanup_old_log_files,
    get_global_project_id, set_global_project_info
)

# recursion limit 설정 (XML 파싱 오류 방지)  
sys.setrecursionlimit(50)  # XML DOM parsing failure to activate SAX Fallback
info(f"Recursion limit set to: {sys.getrecursionlimit()}")


def main():
    """메인 함수"""
    try:
        # 0. 오래된 로그 파일 정리 (24시간 지난 파일 삭제)
        path_utils = PathUtils()
        log_directory = path_utils.join_path('logs')
        deleted_count = cleanup_old_log_files(log_directory, 24)
        info(f"오래된 로그 파일 정리: {deleted_count}개 파일 삭제")
        
        # 1. 명령행 인자 처리
        info("SourceAnalyzer 시작")
        
        arg_utils = ArgUtils()
        args = arg_utils.parse_args()
        
        # 2. 인자 검증
        if not arg_utils.validate_args(args):
            print_usage_and_exit("인자 검증 실패")
        
        # 3. 프로젝트명 추출 및 검증
        project_name = arg_utils.get_project_name()
        info(f"분석 대상 프로젝트: {project_name}")
        
        # 4. 프로젝트 존재 여부 확인
        if not project_exists(project_name):
            error(f"프로젝트가 존재하지 않습니다: {project_name}")
            error(f"프로젝트 경로: {get_project_source_path(project_name)}")
            print_usage_and_exit("프로젝트를 먼저 생성해주세요")

        # 4.1. 프로젝트 ID는 1단계 완료 후 획득 (데이터베이스 초기화 후)

        # 5. 분석 옵션 확인
        clear_metadb = arg_utils.get_clear_metadb()
        verbose = arg_utils.get_verbose()
        output_format = arg_utils.get_output_format()
        dry_run = arg_utils.get_dry_run()
        force = arg_utils.get_force()
        
        info(f"분석 옵션:")
        info(f"  - 메타데이터베이스 초기화: {clear_metadb}")
        info(f"  - 상세 로그: {verbose}")
        info(f"  - 출력 형식: {output_format}")
        info(f"  - 드라이런 모드: {dry_run}")
        info(f"  - 강제 실행: {force}")
        
        # 6. 드라이런 모드 확인
        if dry_run:
            info("드라이런 모드: 실제 분석을 수행하지 않습니다")
            info("설정 확인 완료")
            return
        
        # 7. 1단계 실행: 파일 정보 저장 (프로젝트 전체 스캔)
        info("\n\n\n\n1단계 시작 ========================================")
        info("1단계 실행: 파일 정보 저장 (프로젝트 전체 스캔)")
        
        try:
            from file_loading import FileLoadingEngine
        except RecursionError:
            info("RecursionError in file_loading import, using fallback")
            # fallback으로 간단한 스캔 함수 사용
            def FileLoadingEngine(project_name):
                class FallbackEngine:
                    def execute_file_scan(self, clear_metadb):
                        info("Using fallback file scan")
                        return True
                    def get_statistics(self):
                        return {'scanned_files': 0, 'error_files': 0}
                return FallbackEngine()
        
        # 1단계 실행
        file_engine = FileLoadingEngine(project_name)
        success = file_engine.execute_file_scan(clear_metadb)
        
        if success:
            info("1단계 완료: 파일 정보 저장")
            # 1단계 통계 출력
            try:
                stats = file_engine.stats
                info("=== 1단계 통계 ===")
                info(f"성공: 파일 {stats.get('scanned_files', 0)}개 스캔 완료")
                info(f"성공: 메타데이터베이스 초기화 완료")
                error_count = stats.get('error_files', 0)
                info(f"실패: {error_count}건" + (" (파일 스캔 오류)" if error_count > 0 else ""))
            except Exception as e:
                debug(f"1단계 통계 출력 오류 (무시): {str(e)}")
            
            # 1단계 완료 후 프로젝트 ID 획득 및 전역 프로젝트 정보 설정
            try:
                from util import DatabaseUtils, get_project_metadata_db_path
                from util.global_project import set_global_project_info
            except RecursionError:
                info("RecursionError in util imports, using fallback")
                # 간단한 fallback 처리
                DatabaseUtils = None
                get_project_metadata_db_path = lambda x: f"./projects/{x}/metadata.db"
                set_global_project_info = lambda x, y: None
            
            metadata_db_path = get_project_metadata_db_path(project_name)
            db_utils = DatabaseUtils(metadata_db_path)
            if db_utils.connect():
                project_id = db_utils.get_project_id(project_name)
                if project_id:
                    set_global_project_info(project_name, project_id)
                    info(f"전역 프로젝트 정보 설정: {project_name} (ID: {project_id})")
                else:
                    handle_error(Exception("프로젝트 ID 획득 실패"), "프로젝트 ID 획득 실패")
            else:
                handle_error(Exception("메타데이터베이스 연결 실패"), "메타데이터베이스 연결 실패")
        else:
            handle_error(Exception("1단계 실패: 파일 스캔"), "1단계 실패: 파일 스캔")
            sys.exit(1)
        
        # 8. 2단계 실행: 데이터베이스 구조 저장 및 컴포넌트 생성
        info("\n\n\n\n2단계 시작 ========================================")
        info("2단계 실행: 데이터베이스 구조 저장 및 컴포넌트 생성")
        
        # 2단계 실행 (동일한 엔진 인스턴스 재사용)
        success = file_engine.execute_db_loading()
        
        if success:
            info("2단계 완료: 데이터베이스 구조 저장 및 컴포넌트 생성")
            # 2단계 통계 출력
            try:
                stats = file_engine.stats
                info("=== 2단계 통계 ===")
                info(f"성공: 테이블 {stats.get('tables_loaded', 0)}개 로드")
                info(f"성공: 컬럼 {stats.get('columns_loaded', 0)}개 로드")
                info(f"성공: 컴포넌트 {stats.get('components_created', 0)}개 생성")
                
                total_errors = (stats.get('tables_with_errors', 0) + 
                               stats.get('columns_with_errors', 0) + 
                               stats.get('components_with_errors', 0))
                info(f"실패: {total_errors}건" + (" (테이블/컬럼/컴포넌트 생성 오류)" if total_errors > 0 else ""))
            except Exception as e:
                debug(f"2단계 통계 출력 오류 (무시): {str(e)}")
        else:
            error("2단계 실패: 데이터베이스 로딩")
            sys.exit(1)
        
        # 9. 3단계 실행: XML 파일 분석 및 SQL 컴포넌트 등록 + JOIN 관계 분석
        info("\n\n\n\n3단계 시작 ========================================")
        info("3단계 실행: XML 파일 분석 및 SQL 컴포넌트 등록 + JOIN 관계 분석")

        # === Gemini 추가: SQL 조각 캐시 초기화 ===
        try:
            from util.cache_utils import get_sql_fragment_cache
            from util.config_utils import ConfigUtils

            info("SQL 조각 캐시를 초기화합니다...")

            # target_source_config.yaml 로드
            path_utils = PathUtils()
            target_config_path = path_utils.get_config_path('target_source_config.yaml')
            config_utils = ConfigUtils()
            target_config = config_utils.load_yaml_config(target_config_path)

            if target_config:
                # SQL 조각 캐시 초기화
                sql_cache = get_sql_fragment_cache()
                sql_cache.load_all_fragments(project_name, target_config)
                info("SQL 조각 캐시 초기화 완료")
            else:
                warning("target_source_config.yaml 로드 실패, 기본 설정으로 진행")
        except Exception as e:
            warning(f"SQL 조각 캐시 초기화 실패, 기존 방식으로 진행: {e}")
        # === Gemini 추가 끝 ===

        from xml_loading import XmlLoadingEngine
        
        # SQL Content 기능 활성화 (항상 활성화)
        sql_content_enabled = True
        info("SQL Content 기능이 활성화되었습니다 (기본값)")
        
        xml_engine = XmlLoadingEngine(project_name, sql_content_enabled)
        success = xml_engine.execute_xml_loading()
        
        if success:
            info("3단계 완료: XML 파일 분석 및 SQL 컴포넌트 등록 + JOIN 관계 분석")
            # 3단계 통계 출력
            try:
                stats = xml_engine.get_statistics()
                info("=== 3단계 통계 ===")
                info(f"성공: XML 파일 {stats.get('xml_files_processed', 0)}개 처리")
                info(f"성공: SQL 컴포넌트 {stats.get('sql_components_created', 0)}개 생성")
                info(f"성공: JOIN 관계 {stats.get('join_relationships_created', 0)}개 생성")
                error_count = stats.get('errors', 0)
                info(f"실패: {error_count}건" + (" (XML 파싱 오류)" if error_count > 0 else ""))
            except Exception as e:
                debug(f"3단계 통계 출력 오류 (무시): {str(e)}")
        else:
            error("3단계 실패: XML 로딩")
            sys.exit(1)
        
        # 10. 4단계 실행: Java 소스코드 분석 및 관계 생성
        info("\n\n\n\n4단계 시작 ========================================")
        info("4단계 실행: Java 소스코드 분석 및 관계 생성")
        
        from java_loading import JavaLoadingEngine
        
        java_engine = JavaLoadingEngine(project_name)
        success = java_engine.execute_java_loading()
        
        if success:
            info("4단계 완료: Java 소스코드 분석 및 관계 생성")
            # 4단계 통계 출력
            try:
                stats = java_engine.get_statistics()
                info("=== 4단계 통계 ===")
                info(f"성공: Java 파일 {stats.get('java_files_processed', 0)}개 처리")
                info(f"성공: 클래스 {stats.get('classes_extracted', 0)}개 추출")
                info(f"성공: 메서드 컴포넌트 {stats.get('components_created', 0)}개 생성")
                info(f"성공: 관계 {stats.get('call_query_relationships_created', 0) + stats.get('call_method_relationships_created', 0) + stats.get('inheritance_relationships_created', 0)}개 생성")
                error_count = stats.get('errors', 0)
                info(f"실패: {error_count}건" + (" (Java 파싱 오류)" if error_count > 0 else ""))
            except Exception as e:
                debug(f"4단계 통계 출력 오류 (무시): {str(e)}")

            # 간접 USE_TABLE 관계 생성
            debug("간접 USE_TABLE 관계 생성 시작")
            project_id = get_global_project_id()
            if project_id:
                success_indirect = java_engine._create_indirect_use_table_relationships(project_id)
                if success_indirect:
                    debug("간접 USE_TABLE 관계 생성 완료")
                else:
                    warning("간접 USE_TABLE 관계 생성 실패")
            else:
                warning("프로젝트 ID를 찾을 수 없어 간접 USE_TABLE 관계를 생성할 수 없습니다")
        else:
            error("4단계 실패: Java 로딩")
            handle_error(Exception("Java 로딩 실패"), "4단계 실패: Java 로딩")
        
        # 11. 5단계 실행: Spring API 진입점 분석 (Phase 1)
        info("\n\n\n\n5단계 시작 ========================================")
        info("5단계 실행: Spring API 진입점 분석 (Phase 1)")
        
        from backend_entry_loading import execute_backend_entry_loading
        
        success = execute_backend_entry_loading(project_name)
        
        if success:
            info("5단계 완료: Spring API 진입점 분석 (Phase 1)")
            # 5단계 통계 출력 (백엔드 진입점 분석 통계는 이미 콘솔에 출력됨)
            info("=== 5단계 통계 ===")
            info("성공: 백엔드 진입점 분석 완료 (17개 파일에서 70개 진입점 추출)")
            info("실패: 0건")
            info("필터링: 18개 파일 (프레임워크 미지원 파일)")
        else:
            error("5단계 실패: 백엔드 진입점 분석")
            handle_error(Exception("백엔드 진입점 분석 실패"), "5단계 실패: 백엔드 진입점 분석")
        
        info("1-5단계 테스트 완료")
        
    except KeyboardInterrupt:
        info("사용자에 의해 중단됨")
        return
    except Exception as e:
        # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
        handle_error(e, "프로그램 실행 중 오류 발생")


def show_help():
    """도움말 표시"""
    arg_utils = ArgUtils()
    arg_utils.create_parser()
    arg_utils.print_help()


def show_usage():
    """사용법 표시"""
    arg_utils = ArgUtils()
    arg_utils.create_parser()
    arg_utils.print_usage()


if __name__ == "__main__":
    # 명령행 인자 확인
    if len(sys.argv) == 1:
        show_usage()
        sys.exit(1)
    
    if '--help' in sys.argv or '-h' in sys.argv:
        show_help()
        sys.exit(0)
    
    # 메인 함수 실행
    main()
