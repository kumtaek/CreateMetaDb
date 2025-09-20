#!/usr/bin/env python3
"""
JSP-main.py 통합 테스트
- 6단계 JSP 처리 로직 테스트
- RelationshipBuilder 연동 테스트
"""

import sys
import os

# 현재 스크립트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from relationship_builder import RelationshipBuilder
from parser.jsp_parser import JspParser
from util import get_project_source_path, get_global_project_id, app_logger, info, error, debug


def test_jsp_main_integration():
    """JSP-main.py 통합 테스트"""
    print("=== JSP-main.py 통합 테스트 ===")

    project_name = "SampleSrc"

    try:
        # 프로젝트 ID 직접 설정 (테스트용)
        project_id = 1  # SampleSrc 프로젝트 ID
        print(f"프로젝트: {project_name} (ID: {project_id})")

        # RelationshipBuilder 초기화
        relationship_builder = RelationshipBuilder(project_name, project_id)

        # JSP 파일 분석 및 API 호출 추출
        print("JSP 파일 분석 시작...")
        jsp_parser = JspParser(project_name=project_name)
        project_source_path = get_project_source_path(project_name)
        jsp_files = jsp_parser.get_filtered_jsp_files(project_source_path)

        print(f"발견된 JSP 파일: {len(jsp_files)}개")
        for jsp_file in jsp_files[:5]:  # 첫 5개만 출력
            print(f"  - {jsp_file}")
        if len(jsp_files) > 5:
            print(f"  ... 총 {len(jsp_files)}개")

        jsp_processed = 0
        api_calls_found = 0

        for jsp_file in jsp_files:
            try:
                jsp_result = jsp_parser.parse_jsp_file(jsp_file)

                if jsp_result.get('has_error') == 'N':
                    jsp_processed += 1

                    # API 호출이 있으면 RelationshipBuilder에 추가
                    api_calls = jsp_result.get('api_calls', [])
                    if api_calls:
                        api_calls_found += len(api_calls)

                        # JSP를 프론트엔드 파일로 처리
                        frontend_result = {
                            'file_path': jsp_file,
                            'file_type': 'JSP',
                            'component_name': jsp_result['jsp_component']['jsp_name'] if jsp_result.get('jsp_component') else 'unknown',
                            'api_calls': api_calls,
                            'api_call_count': len(api_calls)
                        }

                        relationship_builder.add_frontend_analysis_result(frontend_result)

                        print(f"API 호출 발견: {jsp_result['jsp_component']['jsp_name']} - {len(api_calls)}개")
                        for api_call in api_calls[:3]:  # 첫 3개만 출력
                            print(f"  {api_call['http_method']} {api_call['api_url']}")
                        if len(api_calls) > 3:
                            print(f"  ... 총 {len(api_calls)}개")

            except Exception as e:
                print(f"JSP 파일 처리 실패: {jsp_file} - {str(e)}")

        print(f"\nJSP 파일 분석 완료: {jsp_processed}개 파일, {api_calls_found}개 API 호출 발견")

        # RelationshipBuilder 상태 확인
        print("\nRelationshipBuilder 수집된 데이터:")
        frontend_files = relationship_builder.collected_data['frontend_files']
        api_calls_data = relationship_builder.collected_data['api_calls']

        print(f"프론트엔드 파일: {len(frontend_files)}개")
        for file_info in frontend_files:
            print(f"  - {file_info['component_name']} ({file_info['file_type']}) - API 호출 {file_info['api_call_count']}개")

        print(f"API 호출: {len(api_calls_data)}개")
        for api_call in api_calls_data[:5]:  # 첫 5개만 출력
            print(f"  - {api_call['component_name']}: {api_call['http_method']} {api_call['api_url']}")
        if len(api_calls_data) > 5:
            print(f"  ... 총 {len(api_calls_data)}개")

        print("\n=== 테스트 완료 ===")

    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


def main():
    """메인 테스트 실행"""
    print("JSP-main.py 통합 테스트 시작")
    print("=" * 50)

    try:
        test_jsp_main_integration()

    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)