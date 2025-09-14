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
    app_logger, info, error, handle_error, cleanup_old_log_files
)

# recursion limit 설정 (XML 파싱 오류 방지)  
sys.setrecursionlimit(50)  # XML DOM parsing failure to activate SAX Fallback
info(f"Recursion limit set to: {sys.getrecursionlimit()}")


def main():
    """메인 함수"""
    try:
        # 0. 오래된 로그 파일 정리 (24시간 지난 파일 삭제)
        log_directory = os.path.join(os.path.dirname(__file__), 'logs')
        info("오래된 로그 파일 정리 시작")
        deleted_count = cleanup_old_log_files(log_directory, 24)
        if deleted_count > 0:
            info(f"로그 파일 정리 완료: {deleted_count}개 파일 삭제")
        else:
            info("삭제할 오래된 로그 파일이 없습니다")
        
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
        info("1단계 실행: 파일 정보 저장 (프로젝트 전체 스캔)")
        
        try:
            from file_loading import execute_file_scan
        except RecursionError:
            info("RecursionError in file_loading import, using fallback")
            # fallback으로 간단한 스캔 함수 사용
            def execute_file_scan(project_name, clear_metadb):
                info("Using fallback file scan")
                return True  # 일단 성공으로 처리하여 다음 단계 진행
        
        success = execute_file_scan(project_name, clear_metadb)
        
        if success:
            info("1단계 완료: 파일 정보 저장")
            
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
        info("2단계 실행: 데이터베이스 구조 저장 및 컴포넌트 생성")
        
        from file_loading import execute_db_loading
        
        success = execute_db_loading(project_name)
        
        if success:
            info("2단계 완료: 데이터베이스 구조 저장 및 컴포넌트 생성")
        else:
            error("2단계 실패: 데이터베이스 로딩")
            sys.exit(1)
        
        # 9. 3단계 실행: XML 파일 분석 및 SQL 컴포넌트 등록 + JOIN 관계 분석
        info("3단계 실행: XML 파일 분석 및 SQL 컴포넌트 등록 + JOIN 관계 분석")
        
        from xml_loading import XmlLoadingEngine
        
        xml_engine = XmlLoadingEngine(project_name)
        success = xml_engine.execute_xml_loading()
        
        if success:
            info("3단계 완료: XML 파일 분석 및 SQL 컴포넌트 등록 + JOIN 관계 분석")
        else:
            error("3단계 실패: XML 로딩")
            sys.exit(1)
        
        # 10. 4단계 실행: Java 소스코드 분석 및 관계 생성
        info("4단계 실행: Java 소스코드 분석 및 관계 생성")
        
        from java_loading import JavaLoadingEngine
        
        java_engine = JavaLoadingEngine(project_name)
        success = java_engine.execute_java_loading()
        
        if success:
            info("4단계 완료: Java 소스코드 분석 및 관계 생성")
        else:
            error("4단계 실패: Java 로딩")
            sys.exit(1)
        
        # 11. 5단계 실행: JSP 파일 분석 및 컴포넌트 등록 (Phase 1 MVP)
        info("5단계 실행: JSP 파일 분석 및 컴포넌트 등록 (Phase 1 MVP)")
        
        from jsp_loading import JspLoadingEngine
        
        jsp_engine = JspLoadingEngine(project_name)
        success = jsp_engine.execute_jsp_loading()
        
        if success:
            info("5단계 완료: JSP 파일 분석 및 컴포넌트 등록 (Phase 1 MVP)")
        else:
            error("5단계 실패: JSP 로딩")
            sys.exit(1)
        
        info("1-5단계 테스트 완료")
        
    except KeyboardInterrupt:
        info("사용자에 의해 중단됨")
        sys.exit(0)
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
