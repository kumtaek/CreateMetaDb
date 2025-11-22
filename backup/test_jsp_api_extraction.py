#!/usr/bin/env python3
"""
JSP API 호출 추출 테스트
- JSP 파서의 API 호출 분석 기능 테스트
- 실제 JSP 파일에서 API 호출이 올바르게 추출되는지 확인
"""

import sys
import os

# 현재 스크립트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from parser.jsp_parser import JspParser
from util import app_logger, info, error, debug


def test_jsp_api_extraction():
    """JSP API 호출 추출 테스트"""
    print("=== JSP API 호출 추출 테스트 ===")

    # JSP 파서 초기화
    parser = JspParser(project_name="SampleSrc")

    # 테스트할 JSP 파일 경로 (공통함수 사용)
    from util.path_utils import PathUtils
    path_utils = PathUtils()
    jsp_file = path_utils.join_path("projects", "SampleSrc", "src", "main", "webapp", "WEB-INF", "views", "user", "UserManagementPage.jsp")

    print(f"테스트 파일: {jsp_file}")

    # JSP 파일 전체 파싱
    print("\n1. JSP 파일 전체 파싱:")
    result = parser.parse_jsp_file(jsp_file)

    print(f"파싱 결과:")
    print(f"  - has_error: {result.get('has_error', 'N/A')}")
    print(f"  - error_message: {result.get('error_message', 'None')}")

    jsp_component = result.get('jsp_component')
    if jsp_component:
        print(f"  - JSP 이름: {jsp_component['jsp_name']}")
        print(f"  - 라인 수: {jsp_component['line_end'] - jsp_component['line_start'] + 1}")

    # parse_jsp_file에서 추출된 API 호출 확인
    parsed_api_calls = result.get('api_calls', [])
    print(f"  - parse_jsp_file에서 추출된 API 호출: {len(parsed_api_calls)}개")
    for i, api_call in enumerate(parsed_api_calls, 1):
        print(f"    {i}. {api_call['http_method']} {api_call['api_url']} (라인 {api_call['line_number']})")

    # JSP 파일 읽기
    from util import FileUtils
    file_utils = FileUtils()
    jsp_content = file_utils.read_file(jsp_file)

    # API 호출 직접 분석
    print("\n2. API 호출 직접 분석:")
    api_calls = parser.analyze_api_calls(jsp_content, "UserManagementPage.jsp")

    print(f"발견된 API 호출: {len(api_calls)}개")
    for i, api_call in enumerate(api_calls, 1):
        print(f"  {i}. {api_call['http_method']} {api_call['api_url']}")
        print(f"     라인 {api_call['line_number']}: {api_call['source_line'][:80]}...")

    # 설정 확인
    print("\n3. JSP 파서 설정 확인:")
    print(f"설정 파일 로드 여부: {bool(parser.config)}")

    api_patterns_text = parser.config.get('api_call_patterns', '')
    if api_patterns_text:
        api_patterns = [line.strip() for line in api_patterns_text.strip().split('\n') if line.strip()]
        print(f"API 패턴 개수: {len(api_patterns)}")
        for i, pattern in enumerate(api_patterns, 1):
            print(f"  {i}. {pattern}")
    else:
        print("API 패턴 설정 없음")

    # 수동으로 패턴 테스트
    print("\n4. 수동 패턴 테스트:")
    import re

    # jQuery AJAX 패턴 테스트
    ajax_pattern = r'\.ajax\s*\(\s*\{[^}]*url\s*:\s*["\']([^"\']+)["\']'
    ajax_matches = re.finditer(ajax_pattern, jsp_content, re.IGNORECASE | re.DOTALL)

    ajax_count = 0
    for match in ajax_matches:
        ajax_count += 1
        url = match.group(1)
        line_num = jsp_content[:match.start()].count('\n') + 1
        print(f"  AJAX {ajax_count}: {url} (라인 {line_num})")

    # 전체 URL 패턴 테스트
    url_pattern = r'["\']([^"\']*\/api\/[^"\']*)["\']'
    url_matches = re.finditer(url_pattern, jsp_content, re.IGNORECASE)

    url_count = 0
    for match in url_matches:
        url_count += 1
        url = match.group(1)
        line_num = jsp_content[:match.start()].count('\n') + 1
        print(f"  URL {url_count}: {url} (라인 {line_num})")


def main():
    """메인 테스트 실행"""
    print("JSP API 호출 추출 테스트 시작")
    print("=" * 50)

    try:
        test_jsp_api_extraction()

        print("\n=== 테스트 완료 ===")

    except Exception as e:
        print(f"\n테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)