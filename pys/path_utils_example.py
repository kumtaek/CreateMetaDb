"""
PathUtils 사용 예시
"""

from path_utils import (
    PathUtils, normalize_path, get_relative_path, get_absolute_path, is_within_project, join_path,
    get_project_source_path, get_project_config_path, get_project_src_path, get_project_db_schema_path,
    get_project_report_path, get_project_metadata_db_path, get_config_path, get_database_schema_path,
    get_parser_config_path, list_projects, project_exists
)


def example_path_utils():
    """PathUtils 사용 예시"""
    
    # 프로젝트 루트 자동 설정 (하드코딩 제거)
    path_utils = PathUtils()  # 자동으로 현재 스크립트 기준 프로젝트 루트 설정
    
    print("=== PathUtils 사용 예시 ===")
    
    # 1. 경로 정규화
    print("\n1. 경로 정규화:")
    relative_path = "projects/sampleSrc/src/main/java"
    absolute_path = path_utils.normalize_path(relative_path)
    print(f"상대경로: {relative_path}")
    print(f"절대경로: {absolute_path}")
    
    # 2. 상대경로 생성
    print("\n2. 상대경로 생성:")
    target_path = "D:/Analyzer/CreateMetaDb/projects/sampleSrc/src/main/java/User.java"
    relative = path_utils.get_project_relative_path(target_path)
    print(f"대상 경로: {target_path}")
    print(f"프로젝트 기준 상대경로: {relative}")
    
    # 3. 절대경로 생성
    print("\n3. 절대경로 생성:")
    abs_path = path_utils.get_absolute_path("config/config.yaml")
    print(f"절대경로: {abs_path}")
    
    # 4. 프로젝트 내부 경로 확인
    print("\n4. 프로젝트 내부 경로 확인:")
    test_paths = [
        "projects/sampleSrc/src/main/java",
        "D:/Analyzer/CreateMetaDb/projects/sampleSrc",
        "D:/OtherProject/src/main/java"
    ]
    
    for path in test_paths:
        is_within = path_utils.is_within_project(path)
        print(f"경로: {path}")
        print(f"프로젝트 내부: {is_within}")
    
    # 5. 경로 결합
    print("\n5. 경로 결합:")
    combined = path_utils.join_path("projects", "sampleSrc", "config", "target_source_config.yaml")
    print(f"결합된 경로: {combined}")
    
    # 6. 경로 구성 요소 분해
    print("\n6. 경로 구성 요소 분해:")
    file_path = "projects/sampleSrc/src/main/java/com/example/User.java"
    components = path_utils.get_path_components(file_path)
    print(f"원본 경로: {file_path}")
    print(f"디렉토리: {components.get('directory', 'N/A')}")
    print(f"파일명: {components.get('filename', 'N/A')}")
    print(f"확장자: {components.get('suffix', 'N/A')}")
    print(f"파일명(확장자 제외): {components.get('stem', 'N/A')}")
    
    # 7. 경로 깊이 계산
    print("\n7. 경로 깊이 계산:")
    test_paths = [
        "projects",
        "projects/sampleSrc",
        "projects/sampleSrc/src/main/java/com/example/User.java"
    ]
    
    for path in test_paths:
        depth = path_utils.get_path_depth(path)
        print(f"경로: {path}")
        print(f"깊이: {depth}")
    
    # 8. 경로 형식 검증
    print("\n8. 경로 형식 검증:")
    test_paths = [
        "projects/sampleSrc/src/main/java",
        "D:/Analyzer/CreateMetaDb/projects/sampleSrc",
        "invalid<path>with|special*chars",
        ""
    ]
    
    for path in test_paths:
        validation = path_utils.validate_path_format(path)
        print(f"경로: {path}")
        print(f"유효성: {validation['is_valid']}")
        if not validation['is_valid']:
            print(f"오류: {validation['errors']}")
    
    # 9. 패턴으로 파일 찾기
    print("\n9. 패턴으로 파일 찾기:")
    java_files = path_utils.find_files_by_pattern("projects/sampleSrc", "*.java", recursive=True)
    print(f"Java 파일 수: {len(java_files)}")
    for file in java_files[:3]:  # 처음 3개만 출력
        print(f"  - {file}")
    
    # 10. 경로 비교
    print("\n10. 경로 비교:")
    path1 = "projects/sampleSrc/src/main/java"
    path2 = "D:/Analyzer/CreateMetaDb/projects/sampleSrc/src/main/java"
    is_same = path_utils.is_same_path(path1, path2)
    print(f"경로1: {path1}")
    print(f"경로2: {path2}")
    print(f"같은 경로: {is_same}")
    
    # 11. 프로젝트 관련 경로 생성 (하드코딩 제거)
    print("\n11. 프로젝트 관련 경로 생성:")
    project_name = "sampleSrc"
    
    print(f"프로젝트 소스 경로: {path_utils.get_project_source_path(project_name)}")
    print(f"프로젝트 설정 경로: {path_utils.get_project_config_path(project_name)}")
    print(f"프로젝트 소스코드 경로: {path_utils.get_project_src_path(project_name)}")
    print(f"프로젝트 DB 스키마 경로: {path_utils.get_project_db_schema_path(project_name)}")
    print(f"프로젝트 리포트 경로: {path_utils.get_project_report_path(project_name)}")
    print(f"프로젝트 메타데이터 DB 경로: {path_utils.get_project_metadata_db_path(project_name)}")
    
    # 12. 시스템 경로 생성
    print("\n12. 시스템 경로 생성:")
    print(f"설정 파일 경로: {path_utils.get_config_path('config.yaml')}")
    print(f"데이터베이스 스키마 경로: {path_utils.get_database_schema_path()}")
    print(f"로그 디렉토리 경로: {path_utils.get_logs_path()}")
    print(f"리포트 디렉토리 경로: {path_utils.get_reports_path()}")
    print(f"Java 파서 설정 경로: {path_utils.get_parser_config_path('java')}")
    
    # 13. 프로젝트 관리
    print("\n13. 프로젝트 관리:")
    projects = path_utils.list_projects()
    print(f"프로젝트 목록: {projects}")
    
    for project in projects:
        exists = path_utils.project_exists(project)
        print(f"프로젝트 '{project}' 존재 여부: {exists}")


def example_convenience_functions():
    """편의 함수 사용 예시 (하드코딩 제거)"""
    
    print("\n=== 편의 함수 사용 예시 (하드코딩 제거) ===")
    
    # 1. 경로 정규화 (프로젝트 루트 자동 설정)
    print("\n1. 경로 정규화:")
    normalized = normalize_path("projects/sampleSrc")  # project_root 자동 설정
    print(f"정규화된 경로: {normalized}")
    
    # 2. 상대경로 생성
    print("\n2. 상대경로 생성:")
    relative = get_relative_path("D:/Analyzer/CreateMetaDb/projects/sampleSrc/src/main/java")  # project_root 자동 설정
    print(f"상대경로: {relative}")
    
    # 3. 절대경로 생성
    print("\n3. 절대경로 생성:")
    absolute = get_absolute_path("config/config.yaml")  # project_root 자동 설정
    print(f"절대경로: {absolute}")
    
    # 4. 프로젝트 내부 확인
    print("\n4. 프로젝트 내부 확인:")
    is_within = is_within_project("projects/sampleSrc")  # project_root 자동 설정
    print(f"프로젝트 내부: {is_within}")
    
    # 5. 경로 결합
    print("\n5. 경로 결합:")
    combined = join_path("projects", "sampleSrc", "config", "target_source_config.yaml")  # project_root 자동 설정
    print(f"결합된 경로: {combined}")
    
    # 6. 프로젝트 관련 경로 생성 (편의 함수)
    print("\n6. 프로젝트 관련 경로 생성 (편의 함수):")
    project_name = "sampleSrc"
    
    print(f"프로젝트 소스 경로: {get_project_source_path(project_name)}")
    print(f"프로젝트 설정 경로: {get_project_config_path(project_name)}")
    print(f"프로젝트 소스코드 경로: {get_project_src_path(project_name)}")
    print(f"프로젝트 DB 스키마 경로: {get_project_db_schema_path(project_name)}")
    print(f"프로젝트 리포트 경로: {get_project_report_path(project_name)}")
    print(f"프로젝트 메타데이터 DB 경로: {get_project_metadata_db_path(project_name)}")
    
    # 7. 시스템 경로 생성 (편의 함수)
    print("\n7. 시스템 경로 생성 (편의 함수):")
    print(f"설정 파일 경로: {get_config_path('config.yaml')}")
    print(f"데이터베이스 스키마 경로: {get_database_schema_path()}")
    print(f"Java 파서 설정 경로: {get_parser_config_path('java')}")
    
    # 8. 프로젝트 관리 (편의 함수)
    print("\n8. 프로젝트 관리 (편의 함수):")
    projects = list_projects()
    print(f"프로젝트 목록: {projects}")
    
    for project in projects:
        exists = project_exists(project)
        print(f"프로젝트 '{project}' 존재 여부: {exists}")


if __name__ == "__main__":
    example_path_utils()
    example_convenience_functions()
