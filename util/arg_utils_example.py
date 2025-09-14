"""
ArgUtils 사용 예시
"""

import sys
from arg_utils import (
    ArgUtils, parse_command_line_args, get_project_name_from_args, 
    validate_and_get_project_name, create_simple_parser, print_usage_and_exit
)


def example_basic_usage():
    """기본 사용법 예시"""
    
    print("=== ArgUtils 기본 사용법 ===")
    
    # 1. 기본 파서 생성 및 사용
    print("\n1. 기본 파서 생성:")
    arg_utils = ArgUtils()
    parser = arg_utils.create_parser("테스트 프로그램")
    
    # 시뮬레이션된 명령행 인자
    test_args = ["--project-name", "sampleSrc", "--verbose", "--clear-metadb"]
    
    print(f"테스트 인자: {test_args}")
    
    # 인자 파싱
    args = arg_utils.parse_args(test_args)
    print(f"파싱된 인자: {vars(args)}")
    
    # 인자 검증
    if arg_utils.validate_args(args):
        print("인자 검증 성공")
        
        # 개별 인자 추출
        print(f"프로젝트명: {arg_utils.get_project_name()}")
        print(f"메타DB 초기화: {arg_utils.get_clear_metadb()}")
        print(f"상세 로그: {arg_utils.get_verbose()}")
        print(f"출력 형식: {arg_utils.get_output_format()}")
        print(f"로그 레벨: {arg_utils.get_log_level()}")
        print(f"드라이런: {arg_utils.get_dry_run()}")
        print(f"강제 실행: {arg_utils.get_force()}")
    else:
        print("인자 검증 실패")


def example_convenience_functions():
    """편의 함수 사용 예시"""
    
    print("\n=== 편의 함수 사용법 ===")
    
    # 1. 간단한 인자 파싱
    print("\n1. 간단한 인자 파싱:")
    test_args = ["--project-name", "myProject", "--output-format", "json"]
    
    try:
        args = parse_command_line_args("편의 함수 테스트")
        print(f"파싱된 인자: {vars(args)}")
    except SystemExit:
        print("인자 파싱 중 종료됨 (정상적인 도움말 출력)")
    
    # 2. 프로젝트명만 추출
    print("\n2. 프로젝트명 추출:")
    try:
        project_name = get_project_name_from_args()
        print(f"프로젝트명: {project_name}")
    except SystemExit:
        print("프로젝트명 추출 중 종료됨")
    
    # 3. 프로젝트명 검증 및 추출
    print("\n3. 프로젝트명 검증 및 추출:")
    try:
        project_name = validate_and_get_project_name()
        print(f"검증된 프로젝트명: {project_name}")
    except SystemExit:
        print("프로젝트명 검증 중 종료됨")


def example_custom_parser():
    """커스텀 파서 예시"""
    
    print("\n=== 커스텀 파서 예시 ===")
    
    # 1. 간단한 파서 생성
    print("\n1. 간단한 파서 생성:")
    simple_parser = create_simple_parser(project_name_required=True)
    
    # 2. 커스텀 파서 생성
    print("\n2. 커스텀 파서 생성:")
    arg_utils = ArgUtils()
    
    required_args = [
        {"dest": "project_name", "type": str, "required": True, "help": "프로젝트명 (필수)"}
    ]
    
    optional_args = [
        {"dest": "custom_option", "type": str, "default": "default_value", "help": "커스텀 옵션"},
        {"dest": "enable_feature", "action": "store_true", "help": "기능 활성화"}
    ]
    
    custom_parser = arg_utils.create_custom_parser(required_args, optional_args)
    
    print("커스텀 파서 생성 완료")


def example_error_handling():
    """에러 처리 예시"""
    
    print("\n=== 에러 처리 예시 ===")
    
    # 1. 잘못된 프로젝트명
    print("\n1. 잘못된 프로젝트명:")
    test_args = ["--project-name", "invalid@project#name"]
    
    arg_utils = ArgUtils()
    args = arg_utils.parse_args(test_args)
    
    if not arg_utils.validate_args(args):
        print("잘못된 프로젝트명으로 인한 검증 실패")
    
    # 2. 필수 인자 누락
    print("\n2. 필수 인자 누락:")
    test_args = ["--verbose"]  # --project-name 누락
    
    try:
        arg_utils = ArgUtils()
        args = arg_utils.parse_args(test_args)
    except SystemExit as e:
        if e.code == 2:
            print("필수 인자 누락으로 인한 오류")
    
    # 3. 사용법 출력
    print("\n3. 사용법 출력:")
    arg_utils = ArgUtils()
    arg_utils.create_parser()
    print("도움말:")
    arg_utils.print_help()


def example_integration_with_path_utils():
    """PathUtils와의 통합 예시"""
    
    print("\n=== PathUtils와의 통합 예시 ===")
    
    from path_utils import PathUtils, get_project_source_path, project_exists
    
    # 시뮬레이션된 명령행 인자
    test_args = ["--project-name", "sampleSrc", "--clear-metadb"]
    
    try:
        # 1. 인자 파싱
        arg_utils = ArgUtils()
        args = arg_utils.parse_args(test_args)
        
        if not arg_utils.validate_args(args):
            print("인자 검증 실패")
            return
        
        # 2. 프로젝트명 추출
        project_name = arg_utils.get_project_name()
        print(f"분석 대상 프로젝트: {project_name}")
        
        # 3. 프로젝트 경로 확인
        path_utils = PathUtils()
        project_path = path_utils.get_project_source_path(project_name)
        print(f"프로젝트 경로: {project_path}")
        
        # 4. 프로젝트 존재 여부 확인
        if project_exists(project_name):
            print("프로젝트가 존재합니다")
            
            # 5. 프로젝트 관련 경로들 출력
            print(f"소스코드 경로: {path_utils.get_project_src_path(project_name)}")
            print(f"설정 경로: {path_utils.get_project_config_path(project_name)}")
            print(f"DB 스키마 경로: {path_utils.get_project_db_schema_path(project_name)}")
            print(f"리포트 경로: {path_utils.get_project_report_path(project_name)}")
            print(f"메타데이터 DB 경로: {path_utils.get_project_metadata_db_path(project_name)}")
            
        else:
            print("프로젝트가 존재하지 않습니다")
            print(f"프로젝트를 다음 경로에 생성해주세요: {project_path}")
        
        # 6. 분석 옵션 확인
        clear_metadb = arg_utils.get_clear_metadb()
        verbose = arg_utils.get_verbose()
        
        print(f"분석 옵션:")
        print(f"  - 메타데이터베이스 초기화: {clear_metadb}")
        print(f"  - 상세 로그: {verbose}")
        
    except SystemExit:
        print("프로그램 종료")
    except Exception as e:
        print(f"오류 발생: {str(e)}")


def simulate_main_py_usage():
    """main.py 사용법 시뮬레이션"""
    
    print("\n=== main.py 사용법 시뮬레이션 ===")
    
    # 다양한 명령행 인자 시나리오
    scenarios = [
        {
            "name": "기본 사용법",
            "args": ["--project-name", "sampleSrc"]
        },
        {
            "name": "메타DB 초기화",
            "args": ["--project-name", "sampleSrc", "--clear-metadb"]
        },
        {
            "name": "상세 로그 + JSON 출력",
            "args": ["--project-name", "sampleSrc", "--verbose", "--output-format", "json"]
        },
        {
            "name": "드라이런 모드",
            "args": ["--project-name", "sampleSrc", "--dry-run"]
        },
        {
            "name": "강제 실행",
            "args": ["--project-name", "sampleSrc", "--force"]
        },
        {
            "name": "모든 옵션",
            "args": [
                "--project-name", "sampleSrc",
                "--clear-metadb",
                "--verbose",
                "--output-format", "markdown",
                "--log-level", "DEBUG",
                "--force"
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print(f"명령어: python main.py {' '.join(scenario['args'])}")
        
        try:
            arg_utils = ArgUtils()
            args = arg_utils.parse_args(scenario['args'])
            
            if arg_utils.validate_args(args):
                print("  ✓ 인자 파싱 및 검증 성공")
                print(f"  - 프로젝트명: {arg_utils.get_project_name()}")
                print(f"  - 메타DB 초기화: {arg_utils.get_clear_metadb()}")
                print(f"  - 상세 로그: {arg_utils.get_verbose()}")
                print(f"  - 출력 형식: {arg_utils.get_output_format()}")
                print(f"  - 로그 레벨: {arg_utils.get_log_level()}")
                print(f"  - 드라이런: {arg_utils.get_dry_run()}")
                print(f"  - 강제 실행: {arg_utils.get_force()}")
            else:
                print("  ✗ 인자 검증 실패")
                
        except SystemExit:
            print("  ✗ 인자 파싱 실패")
        except Exception as e:
            print(f"  ✗ 오류: {str(e)}")


if __name__ == "__main__":
    example_basic_usage()
    example_convenience_functions()
    example_custom_parser()
    example_error_handling()
    example_integration_with_path_utils()
    simulate_main_py_usage()
