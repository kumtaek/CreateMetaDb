#!/usr/bin/env python3
"""
HTTP 메서드 추출 상세 디버깅
"""

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parser.spring_entry_analyzer import SpringEntryAnalyzer

def debug_http_method_detailed():
    """HTTP 메서드 추출 상세 디버깅"""

    test_annotation = '@RequestMapping(value = "/test1", method = RequestMethod.GET)'

    print(f"테스트 어노테이션: {test_annotation}")
    print("=" * 50)

    # 정규식 패턴들 개별 테스트
    method_patterns = [
        r'method\s*=\s*\{([^}]*)\}',           # 배열: {RequestMethod.GET, RequestMethod.POST}
        r'method\s*=\s*([^,\)]+)'              # 단일: RequestMethod.GET
    ]

    for i, pattern in enumerate(method_patterns, 1):
        match = re.search(pattern, test_annotation)
        print(f"패턴 {i}: {pattern}")
        print(f"매치 결과: {match}")
        if match:
            methods_text = match.group(1)
            print(f"추출된 텍스트: '{methods_text}'")
            methods = re.findall(r'RequestMethod\.(\w+)', methods_text)
            print(f"HTTP 메서드들: {methods}")
            if methods:
                result = [method.upper() for method in methods]
                print(f"최종 결과: {result}")
                break
        print("---")

    # 실제 Spring Entry Analyzer로 추출
    analyzer = SpringEntryAnalyzer()
    actual_methods = analyzer.extract_http_method_from_annotation(test_annotation)
    print(f"Spring Entry Analyzer 결과: {actual_methods}")

if __name__ == "__main__":
    debug_http_method_detailed()