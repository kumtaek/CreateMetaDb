#!/usr/bin/env python3
"""
정규식에서 추출되는 어노테이션 디버깅
"""

import re

def debug_extracted_annotations():
    """정규식에서 추출되는 어노테이션 디버깅"""

    # 실제 SyntaxErrorController 파일 읽기
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

            print(f"매치 {i}: {method_name}")
            print(f"추출된 어노테이션: '{annotation_text}'")
            print(f"어노테이션 길이: {len(annotation_text)}")

            # 'method' 키워드 포함 여부 확인
            has_method = 'method' in annotation_text
            print(f"'method' 포함 여부: {has_method}")

            if not has_method:
                print("⚠️ 'method' 키워드가 없음 - 기본값 반환 예상")

            print("---")

if __name__ == "__main__":
    debug_extracted_annotations()