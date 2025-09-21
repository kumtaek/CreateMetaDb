#!/usr/bin/env python3
"""
URL 결합 디버깅 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parser.spring_entry_analyzer import SpringEntryAnalyzer

def debug_url_combination():
    """URL 결합 디버깅"""
    analyzer = SpringEntryAnalyzer()

    # 테스트 케이스들
    test_cases = [
        {
            'annotation': '@RequestMapping(value = "/test1", method = RequestMethod.GET)',
            'class_url': '/syntax-fixed'
        },
        {
            'annotation': '@RequestMapping(value = "/users", method = RequestMethod.GET)',
            'class_url': '/syntax-fixed'
        },
        {
            'annotation': '@RequestMapping(value = "/user", method = RequestMethod.POST)',
            'class_url': '/syntax-fixed'
        }
    ]

    print("URL 결합 디버깅:")
    print("=" * 50)

    for i, case in enumerate(test_cases, 1):
        annotation = case['annotation']
        class_url = case['class_url']

        # URL 추출
        method_url = analyzer.extract_url_from_annotation(annotation)

        # URL 결합
        combined_url = analyzer._combine_urls(class_url, method_url)

        print(f"테스트 케이스 {i}:")
        print(f"  어노테이션: {annotation}")
        print(f"  클래스 URL: {class_url}")
        print(f"  추출된 메서드 URL: {method_url}")
        print(f"  결합된 URL: {combined_url}")
        print("---")

if __name__ == "__main__":
    debug_url_combination()