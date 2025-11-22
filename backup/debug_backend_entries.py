#!/usr/bin/env python3
"""
백엔드 엔트리 디버깅 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parser.spring_entry_analyzer import SpringEntryAnalyzer
from parser.base_entry_analyzer import FileInfo

def debug_syntax_error_controller():
    """SyntaxErrorController 디버깅"""

    # 파일 읽기
    file_path = "projects/sampleSrc/src/main/java/com/example/controller/SyntaxErrorController.java"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    file_info = FileInfo(
        file_id=1,
        file_path=file_path,
        file_name="SyntaxErrorController.java",
        file_type="JAVA",
        hash_value="test",
        content=content
    )

    # Spring 분석기로 분석
    analyzer = SpringEntryAnalyzer()

    class MockStats:
        def log_file_result(self, **kwargs):
            pass

    results = analyzer.analyze_backend_entry(file_info, MockStats())

    print(f"분석 결과: {len(results)}개 백엔드 엔트리")
    print("=" * 50)

    for i, entry in enumerate(results, 1):
        print(f"{i}. {entry.method_name}")
        print(f"   URL: {entry.url_pattern}")
        print(f"   HTTP Method: {entry.http_method}")
        print(f"   Class URL: {entry.class_url}")
        print("---")

if __name__ == "__main__":
    debug_syntax_error_controller()