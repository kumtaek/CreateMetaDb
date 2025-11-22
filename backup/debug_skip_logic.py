#!/usr/bin/env python3
"""
스킵 로직 디버깅
"""

def debug_skip_logic():
    """스킵 로직 디버깅"""

    test_annotations = [
        '@RequestMapping(value = "/test1", method = RequestMethod.GET)',
        '@RequestMapping(value = "/test2", method = RequestMethod.GET)',
        '@RequestMapping(value = "/users", method = RequestMethod.GET)',
        '@RequestMapping(value = "/user", method = RequestMethod.GET)',
        '@RequestMapping(value = "/user", method = RequestMethod.POST)',
        '@RequestMapping("/syntax-fixed")'  # 클래스 레벨 (비교용)
    ]

    print("스킵 로직 디버깅:")
    print("=" * 50)

    for i, annotation_text in enumerate(test_annotations, 1):
        print(f"테스트 {i}: {annotation_text}")

        # 조건 1: @RequestMapping이고 method가 없는 경우
        condition1 = annotation_text.startswith('@RequestMapping') and 'method' not in annotation_text
        print(f"  조건1 (RequestMapping & no method): {condition1}")

        if condition1:
            # 조건 2: URL이 있고 method가 없는 경우
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from parser.spring_entry_analyzer import SpringEntryAnalyzer

            analyzer = SpringEntryAnalyzer()
            extracted_url = analyzer.extract_url_from_annotation(annotation_text)
            condition2 = extracted_url and 'method' not in annotation_text
            print(f"  조건2 (has URL & no method): {condition2}")
            print(f"  추출된 URL: {extracted_url}")

            if condition2:
                print("  → 스킵됨 (클래스 레벨로 간주)")
            else:
                print("  → 처리됨")
        else:
            print("  → 처리됨")

        print("---")

if __name__ == "__main__":
    debug_skip_logic()