#!/usr/bin/env python3
"""
실제 파일에서 정규식 매치 디버깅
"""

import re

def debug_real_file():
    """실제 SyntaxErrorController 파일 디버깅"""

    # 파일 읽기
    file_path = "projects/sampleSrc/src/main/java/com/example/controller/SyntaxErrorController.java"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Spring Entry Analyzer에서 사용하는 정규식
    improved_pattern = r'(@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*(?:\([^)]*\))?|@RequestMapping\s*\([^)]*(?:method\s*=|,\s*method\s*=)[^)]*\))\s*(?:\n\s*@\w+\s*)*\n\s*(?:public|private|protected)\s+(?:[\w\<\>\[\],\s\?]+\s+)(\w+)\s*\('
    improved_regex = re.compile(improved_pattern, re.DOTALL)

    matches = improved_regex.findall(content)

    print(f"실제 파일에서 정규식 매치 결과: {len(matches)}개")
    print("=" * 70)

    for i, match in enumerate(matches, 1):
        if isinstance(match, tuple) and len(match) >= 2:
            annotation_text = match[0]
            method_name = match[1]
            print(f"매치 {i}:")
            print(f"  어노테이션: {annotation_text}")
            print(f"  메서드명: {method_name}")

            # URL 추출 시뮬레이션
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from parser.spring_entry_analyzer import SpringEntryAnalyzer

            analyzer = SpringEntryAnalyzer()
            method_url = analyzer.extract_url_from_annotation(annotation_text)
            combined_url = analyzer._combine_urls("/syntax-fixed", method_url)

            print(f"  추출된 URL: {method_url}")
            print(f"  결합된 URL: {combined_url}")
            print("---")

if __name__ == "__main__":
    debug_real_file()