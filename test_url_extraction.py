#!/usr/bin/env python3
"""
Spring Entry Analyzer URL 추출 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parser.spring_entry_analyzer import SpringEntryAnalyzer

def test_url_extraction():
    """URL 추출 테스트"""
    analyzer = SpringEntryAnalyzer()

    test_cases = [
        '@RequestMapping(value = "/test1", method = RequestMethod.GET)',
        '@RequestMapping(value = "/users", method = RequestMethod.GET)',
        '@RequestMapping("/syntax-fixed")',
        '@GetMapping("/api/users")',
        '@PostMapping(value = "/create")'
    ]

    print("URL 추출 테스트:")
    for annotation in test_cases:
        url = analyzer.extract_url_from_annotation(annotation)
        print(f"어노테이션: {annotation}")
        print(f"추출된 URL: {url}")
        print("---")

if __name__ == "__main__":
    test_url_extraction()