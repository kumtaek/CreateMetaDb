#!/usr/bin/env python3
"""
심플 Java 파서 테스트
"""

import os
import sys
from java_loading import SimpleJavaLoader

def test_simple_parser():
    print("심플 Java 파서 테스트 시작")

    project_name = "sampleSrc"
    project_id = 1

    # SimpleJavaLoader 인스턴스 생성
    loader = SimpleJavaLoader(project_name)

    # 데이터베이스 초기화 (원래는 execute_java_loading에서 하는 작업)
    from util import DatabaseUtils
    loader.db_utils = DatabaseUtils(loader.metadata_db_path)

    # 테스트용 Java 파일 하나만 처리해보기
    test_file = os.path.join(loader.project_source_path, "src", "main", "java", "com", "example", "model", "User.java")

    if os.path.exists(test_file):
        print(f"테스트 파일: {test_file}")

        # 파일 ID 조회 과정 디버깅
        relative_path = os.path.relpath(test_file, loader.project_source_path)
        relative_path = relative_path.replace('\\', '/')
        print(f"프로젝트 경로: {loader.project_source_path}")
        print(f"절대 경로: {test_file}")
        print(f"상대 경로: {relative_path}")

        # SQL 쿼리 직접 실행해보기
        query = "SELECT file_id FROM files WHERE file_path = ?"
        result = loader.db_utils.execute_query(query, (relative_path,))
        print(f"SQL 쿼리 결과: {result}")

        file_id = loader._get_file_id(test_file)
        print(f"파일 ID: {file_id}")

        if file_id:
            # Java 파싱
            parse_result = loader.java_parser.parse_java_file(test_file)
            print(f"파싱 결과: {parse_result}")

            # 컴포넌트 데이터 생성
            components = loader.java_parser.get_component_data(parse_result, file_id, project_id)
            print(f"컴포넌트 데이터: {len(components)}개")
            for comp in components:
                print(f"  - {comp['component_type']}: {comp['component_name']}")
        else:
            print("파일 ID를 찾을 수 없습니다.")
    else:
        print(f"테스트 파일을 찾을 수 없습니다: {test_file}")

        # 다른 파일 찾아보기
        for root, dirs, files in os.walk(loader.project_source_path):
            for file in files:
                if file.endswith('.java'):
                    java_file = os.path.join(root, file)
                    print(f"찾은 Java 파일: {java_file}")
                    break
            break

if __name__ == "__main__":
    test_simple_parser()