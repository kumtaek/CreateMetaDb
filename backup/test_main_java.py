#!/usr/bin/env python3
"""
main.py의 Java 로딩 부분만 테스트
"""

import os
import sys

# 프로젝트 정보
project_name = "sampleSrc"
project_id = 1

print("=== Java 로딩 테스트 시작 ===")

try:
    from java_loading import load_java_files_simple
    print("java_loading 모듈 import 성공")

    # 함수 호출
    print(f"load_java_files_simple 호출: project_name={project_name}, project_id={project_id}")
    success = load_java_files_simple(project_name, project_id)

    print(f"Java 로딩 결과: {success}")

except Exception as e:
    print(f"에러 발생: {e}")
    import traceback
    traceback.print_exc()

print("=== Java 로딩 테스트 종료 ===")