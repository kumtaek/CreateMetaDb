"""
SourceAnalyzer 메인 실행 파일
- 명령행 인자 처리
- 프로젝트 분석 실행
"""

import sys
import os
import time
import logging  # logging 모듈 추가


def _pre_logger_cleanup(log_directory: str, hours_threshold: int = 24) -> None:
    """
    로거 기동 전에 오래된 로그를 삭제하여 잠금 충돌을 방지합니다.
    handle_error()를 호출할 수 없는 초기 구간이므로 치명 오류는 stderr 후 종료합니다.
    """
    try:
        if not os.path.exists(log_directory):
            return

        now = time.time()
        threshold_seconds = hours_threshold * 3600

        for filename in os.listdir(log_directory):
            file_path = os.path.join(log_directory, filename)

            if not filename.endswith(".log") or not os.path.isfile(file_path):
                continue

            file_age = now - os.path.getmtime(file_path)
            if file_age <= threshold_seconds:
                continue

            try:
                os.remove(file_path)
            except PermissionError as e:
                print(f"FATAL: 로그 파일 잠금으로 삭제 실패: {file_path} - {e}", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"FATAL: 로그 파일 삭제 실패: {file_path} - {e}", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"FATAL: 로그 정리 중 예외 발생: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """메인 함수"""
    try:
        # 0. 로거 기동 전에 오래된 로그 삭제 (잠금 회피)
        project_root = os.path.dirname(os.path.abspath(__file__))
        _pre_logger_cleanup(os.path.join(project_root, "logs"), hours_threshold=24)

        # util 로딩 (여기서 로거 초기화)
        from util import (
            ArgUtils, validate_and_get_project_name, print_usage_and_exit,
            PathUtils, get_project_source_path, project_exists,
            app_logger, info, error, debug, warning, handle_error, cleanup_old_log_files, safe_remove_file,
            get_global_project_id, set_global_project_info
        )

        # recursion limit 설정 (XML 파싱 오류 방지)
        # 재귀 제한을 너무 낮추면 표준 라이브러리(import 시)에서 오류가 발생하므로 여유 있게 설정
        sys.setrecursionlimit(1000)
        info(f"Recursion limit set to: {sys.getrecursionlimit()}")

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
        
        # 4. 프로젝트 존재 여부 확인 (대소문자 정확히 일치하는 프로젝트만 허용)
        projects_root = path_utils.join_path('projects')
        if os.path.exists(projects_root):
            # 실제 디렉토리 목록 가져오기 (대소문자 구분)
            real_projects = os.listdir(projects_root)
            
            # 프로젝트명이 정확히 일치하는지 확인 (문자열 비교)
            if project_name not in real_projects:
                # 대소문자만 다른 유사한 프로젝트명 찾기
                similar_projects = [p for p in real_projects if p.lower() == project_name.lower()]
                
                if similar_projects:
                    real_name = similar_projects[0]
                    error(f"프로젝트명 대소문자가 일치하지 않습니다.")
                    error(f"입력: '{project_name}' -> 실제: '{real_name}'")
                    print_usage_and_exit(f"프로젝트명이 정확하지 않습니다. '{project_name}' 대신 '{real_name}'를 사용하세요.")
                else:
                    error(f"프로젝트가 존재하지 않습니다: '{project_name}'")
                    print_usage_and_exit(f"프로젝트 '{project_name}'가 존재하지 않습니다.")
        
        # 프로젝트 디렉토리 존재 확인 (이중 검증)
        if not project_exists(project_name):
            error(f"프로젝트가 존재하지 않습니다: {project_name}")
            error(f"프로젝트 경로: {get_project_source_path(project_name)}")
            print_usage_and_exit("프로젝트를 먼저 생성해주세요")

        # 4.1. 프로젝트 ID는 1단계 완료 후 획득 (데이터베이스 초기화 후)

        # 5. 분석 옵션 확인
        clear_metadb = arg_utils.get_clear_metadb()
        verbose = arg_utils.get_verbose()

        dry_run = arg_utils.get_dry_run()

        # 5.1 메타데이터베이스 초기화 옵션 처리 (연결 전에 수행해야 잠금 회피)
        if clear_metadb:
            path_utils = PathUtils()
            metadata_db_path = path_utils.join_path(path_utils.project_root, "projects", project_name, "metadata.db")
            sql_content_db_path = path_utils.join_path(path_utils.project_root, "projects", project_name, "SqlContent.db")
            for target_path, label in [(metadata_db_path, "메타데이터베이스"), (sql_content_db_path, "SQL 콘텐츠 DB")]:
                if os.path.exists(target_path):
                    if safe_remove_file(target_path, max_retries=3, retry_delay=0.5):
                        info(f"기존 {label} 삭제: {target_path}")
            # 초기화 요청은 이 시점에 완결되므로 이후 단계에서는 재시도하지 않음
            clear_metadb = False


        # 로거 레벨 설정
        from util import app_logger
        if verbose:
            app_logger.logger.setLevel(logging.DEBUG)
            info("로거 레벨을 DEBUG로 설정합니다.")
        else:
            app_logger.logger.setLevel(logging.INFO)
            info("로거 레벨을 INFO로 설정합니다.")
        
        info(f"분석 옵션:")
        info(f"  - 메타데이터베이스 초기화: {clear_metadb}")
        info(f"  - 상세 로그: {verbose}")

        info(f"  - 드라이런 모드: {dry_run}")

        
        # 6. 드라이런 모드 확인
        if dry_run:
            info("드라이런 모드: 실제 분석을 수행하지 않습니다")
            info("설정 확인 완료")
            return
        
        # 7. 분석 단계 실행 (단일 트랜잭션으로 묶어서 처리)
        info("\n\n\n\n분석 단계 실행 시작 (단일 트랜잭션) ========================================")
        
        # 데이터베이스 유틸리티 인스턴스 생성
        from util import DatabaseUtils, get_project_metadata_db_path
        metadata_db_path = get_project_metadata_db_path(project_name)
        db_utils = DatabaseUtils(metadata_db_path)

        info("분석 단계 실행 시작 (Auto Commit 모드)")

        # 데이터베이스 스키마 생성 (1단계 실행 전)
        info(f"데이터베이스 경로 확인: {metadata_db_path}")
        info(f"데이터베이스 파일 존재 여부: {os.path.exists(metadata_db_path)}")
        
        if not db_utils.connect():
            raise Exception("데이터베이스 연결 실패")
        
        # 스키마가 존재하지 않으면 생성 (강제로 스키마 생성)
        info(f"스키마 생성 조건 확인: {not os.path.exists(metadata_db_path)}")
        info("강제로 스키마 생성 실행...")
        if True:  # 강제로 스키마 생성
            info("스키마 생성 시작...")
            path_utils = PathUtils()
            schema_path = path_utils.join_path(path_utils.project_root, 'database', 'create_table_script.sql')
            info(f"스키마 파일 경로: {schema_path}")
            info(f"스키마 파일 존재 여부: {os.path.exists(schema_path)}")
            
            if not db_utils.create_schema(schema_path):
                raise Exception("데이터베이스 스키마 생성 실패")
            info(f"메타데이터베이스 스키마 생성 완료: {metadata_db_path}")
        else:
            info(f"기존 메타데이터베이스 사용: {metadata_db_path}")
        
        db_utils.disconnect()

        # 1단계 실행: 파일 정보 저장 (프로젝트 전체 스캔)
        info("\n--- 1단계: 파일 정보 저장 ---")
        conn = db_utils.get_persistent_connection()
        from file_loading import FileLoadingEngine
        file_engine = FileLoadingEngine(project_name, conn)
        success = file_engine.execute_file_scan(clear_metadb)
        if not success:
            raise Exception("1단계 파일 스캔 실패")
        info("1단계 완료")
        stats = file_engine.stats
        info(f"  => 성공: {stats.get('scanned_files', 0)}개 파일 스캔, 실패: {stats.get('error_files', 0)}건")

        # 1단계 완료 후 프로젝트 ID 획득 및 전역 설정
        project_id = db_utils.get_project_id(project_name, conn)
        if project_id:
            set_global_project_info(project_name, project_id)
            info(f"전역 프로젝트 정보 설정: {project_name} (ID: {project_id})")
        else:
            raise Exception("프로젝트 ID 획득 실패")

        # 2단계 실행: 데이터베이스 구조 저장
        info("\n--- 2단계: DB 구조 저장 ---")
        success = file_engine.execute_db_loading()
        if not success:
            raise Exception("2단계 DB 구조 저장 실패")
        info("2단계 완료")
        stats = file_engine.stats
        info(f"  => 성공: 테이블 {stats.get('tables_loaded', 0)}개, 컬럼 {stats.get('columns_loaded', 0)}개, 컴포넌트 {stats.get('components_created', 0)}개")

        # 3단계 실행: XML 분석
        info("\n--- 3단계: XML 분석 ---")
        from xml_loading import XmlLoadingEngine
        sql_content_enabled = True
        xml_engine = XmlLoadingEngine(project_name, conn, sql_content_enabled)
        success = xml_engine.execute_xml_loading()
        if not success:
            raise Exception("3단계 XML 분석 실패")
        info("3단계 완료")
        stats = xml_engine.get_statistics()
        info(f"  => 성공: XML {stats.get('xml_files_processed', 0)}개, SQL 컴포넌트 {stats.get('sql_components_created', 0)}개, JOIN 관계 {stats.get('join_relationships_created', 0)}개")

        # 4단계 실행: Java 소스코드 분석
        info("\n--- 4단계: Java 분석 ---")
        from java_loading import load_java_files_simple
        success, java_stats = load_java_files_simple(project_name, project_id, conn)
        if not success:
            raise Exception("4단계 Java 분석 실패")
        info("4단계 완료")
        info(f"  => 성공: Java 파일 {java_stats.get('java_files_processed', 0)}개, 관계 {java_stats.get('relationships_created', 0)}개")

        # 5단계 실행: Spring API 진입점 분석
        info("\n--- 5단계: API 진입점 분석 ---")
        from backend_entry_loading import execute_backend_entry_loading
        success = execute_backend_entry_loading(project_name, conn)
        if not success:
            raise Exception("5단계 API 진입점 분석 실패")
        info("5단계 완료")

        # 6단계 실행: 프론트엔드 분석 및 연관관계 구축
        info("\n--- 6단계: 프론트엔드 분석 및 관계 구축 ---")
        from frontend_loading import FrontendLoadingEngine
        frontend_engine = FrontendLoadingEngine(project_name, conn)
        success = frontend_engine.execute_frontend_loading()
        if not success:
            warning("6-1단계 프론트엔드 분석 중 오류 발생")
        info("6-1단계 프론트엔드 분석 완료")
        stats = frontend_engine.stats
        info(f"  => 성공: API 호출 {stats.get('api_calls_found', 0)}개, 관계 {stats.get('relationships_created', 0)}개")

        from relationship_builder import RelationshipBuilder, execute_db_relationship_backfill
        relationship_builder = RelationshipBuilder(project_name, project_id, conn)
        relationship_stats = relationship_builder.build_all_relationships()
        info("6-2단계 연관관계 구축 완료")
        info(f"  => 성공: 총 관계 {relationship_stats.get('total_relationships', 0)}개 생성")

        # 7단계 실행: 일관성 검증
        info("\n--- 7단계: 일관성 검증 ---")
        # 6-3단계: DB 기반 필수 관계 보강 (CALL_API, CALL_METHOD)
        backfill_stats = execute_db_relationship_backfill(project_name, conn)
        info(f"6-3단계 DB 기반 관계 보강: CALL_API={backfill_stats.get('CALL_API',0)}, CALL_METHOD={backfill_stats.get('CALL_METHOD',0)}")

        from consistency_validator import execute_consistency_validation
        validation_success = execute_consistency_validation(project_name, conn)
        if validation_success:
            info("일관성 검증 완료: 모든 검사 통과")
        else:
            warning("일관성 검증 완료: 문제 발견됨 (상세 내용은 로그 확인)")

        info("\n\n분석 완료: 모든 단계가 성공적으로 Auto Commit 모드로 처리되었습니다.")
    except KeyboardInterrupt:
        info("사용자에 의해 중단됨")
        return
    except Exception as e:
        # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
        handle_error(e, "프로그램 실행 중 오류 발생")


def show_help():
    """도움말 표시"""
    from util import ArgUtils
    arg_utils = ArgUtils()
    arg_utils.create_parser()
    arg_utils.print_help()


def show_usage():
    """사용법 표시"""
    from util import ArgUtils
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
