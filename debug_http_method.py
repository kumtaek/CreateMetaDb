#!/usr/bin/env python3
"""
HTTP 메서드 추출 디버깅
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parser.spring_entry_analyzer import SpringEntryAnalyzer

def debug_http_method_extraction():
    """HTTP 메서드 추출 디버깅"""

    analyzer = SpringEntryAnalyzer()

    test_annotations = [
        '@RequestMapping(value = "/test1", method = RequestMethod.GET)',
        '@RequestMapping(value = "/test2", method = RequestMethod.GET)',
        '@RequestMapping(value = "/users", method = RequestMethod.GET)',
        '@RequestMapping(value = "/user", method = RequestMethod.GET)',
        '@RequestMapping(value = "/user", method = RequestMethod.POST)'
    ]

    print("HTTP 메서드 추출 디버깅:")
    print("=" * 50)

    for i, annotation_text in enumerate(test_annotations, 1):
        print(f"테스트 {i}: {annotation_text}")

        # HTTP 메서드 추출
        http_methods = analyzer.extract_http_method_from_annotation(annotation_text)

        print(f"  추출된 HTTP 메서드들: {http_methods}")
        print(f"  메서드 개수: {len(http_methods) if http_methods else 0}")
        print("---")

if __name__ == "__main__":
    debug_http_method_extraction()