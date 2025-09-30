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
        from java_loading import JavaLoader
        java_loader = JavaLoader(project_name, conn)
        success = java_loader.execute_java_loading(project_id)
        if not success:
            raise Exception("4단계 Java 분석 실패")
        info("4단계 완료")
        java_stats = java_loader.get_statistics()
        info(f"  => 성공: Java 파일 {java_stats.get('java_files_processed', 0)}개, 클래스 {java_stats.get('classes_extracted', 0)}개, 메서드 {java_stats.get('methods_extracted', 0)}개")

        # 4.5단계 실행: 통합 쿼리 분석
        info("\n--- 4.5단계: 통합 쿼리 분석 ---")
        from parser.integrated_query_analyzer import IntegratedQueryAnalyzer
        query_analyzer = IntegratedQueryAnalyzer(project_name, conn)
        result = query_analyzer.analyze_all_queries()
        if not result['success']:
            raise Exception("4.5단계 통합 쿼리 분석 실패")
        info("4.5단계 완료")
        query_stats = query_analyzer.get_statistics()
        info(f"  => 성공: Java 파일 {query_stats.get('java_files_processed', 0)}개, XML 파일 {query_stats.get('xml_files_processed', 0)}개, 쿼리 {query_stats.get('queries_extracted', 0)}개")

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

        from relationship_builder import RelationshipBuilder
        relationship_builder = RelationshipBuilder(project_name, project_id, conn)
        relationship_stats = relationship_builder.build_all_relationships()
        info("6-2단계 연관관계 구축 완료")
        info(f"  => 성공: 총 관계 {relationship_stats.get('total_relationships', 0)}개 생성")

        # 7단계 실행: 일관성 검증
        info("\n--- 7단계: 일관성 검증 ---")
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
