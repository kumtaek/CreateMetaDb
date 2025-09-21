#!/usr/bin/env python3
"""
URL 결합 간단 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parser.spring_entry_analyzer import SpringEntryAnalyzer

def test_simple_combination():
    """간단한 URL 결합 테스트"""
    analyzer = SpringEntryAnalyzer()

    # 테스트 케이스
    class_url = "/syntax-fixed"
    method_url = "/test1"

    print(f"클래스 URL: '{class_url}'")
    print(f"메서드 URL: '{method_url}'")

    # URL 결합
    combined = analyzer._combine_urls(class_url, method_url)
    print(f"결합된 URL: '{combined}'")

    # None 또는 빈 문자열인 경우
    print("\n=== None/빈 문자열 테스트 ===")
    test_cases = [
        (class_url, None),
        (class_url, ""),
        (class_url, "/test1"),
        (class_url, "test1")
    ]

    for i, (cls_url, meth_url) in enumerate(test_cases, 1):
        result = analyzer._combine_urls(cls_url, meth_url)
        print(f"테스트 {i}: '{cls_url}' + '{meth_url}' = '{result}'")

if __name__ == "__main__":
    test_simple_combination()