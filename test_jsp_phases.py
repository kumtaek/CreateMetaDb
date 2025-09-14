"""
JSP 파서 Phase 2&3 테스트 스크립트
- Phase 1: 스크립틀릿, 표현식에서 Java 메서드 호출
- Phase 2: JSP 간 관계 (include 디렉티브, jsp 액션)
- Phase 3: EL 표현식, JSTL, Java Bean, 태그 라이브러리
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parser.jsp_parser import JspParser
from util import app_logger, info, error, debug, warning

def test_jsp_phases():
    """JSP 파서 Phase 2&3 테스트"""
    print("=" * 60)
    print("JSP 파서 Phase 2&3 기능 테스트")
    print("=" * 60)

    try:
        # JSP 파서 초기화
        jsp_parser = JspParser()

        # 테스트 JSP 파일 경로
        test_jsp_file = r"D:\Analyzer\CreateMetaDb\projects\sampleSrc\src\test.jsp"

        if not os.path.exists(test_jsp_file):
            print(f"테스트 파일을 찾을 수 없습니다: {test_jsp_file}")
            return

        print(f"분석 대상: {test_jsp_file}")
        print("-" * 60)

        # JSP 파일 분석
        result = jsp_parser.parse_jsp_file(test_jsp_file)

        if result['has_error'] == 'Y':
            print(f"[ERROR] 파싱 에러: {result['error_message']}")
            return

        print("[OK] JSP 파일 파싱 성공!")
        print()

        # Phase 1: Java 메서드 호출 관계
        print("[Phase 1] Java 메서드 호출 관계")
        print("-" * 40)
        java_methods = result['java_method_relationships']
        if java_methods:
            for method in java_methods:
                print(f"  - {method['jsp_name']} -> {method['class_name']}.{method['method_name']}() [Line {method['line_number']}]")
        else:
            print("  (Java 메서드 호출 없음)")
        print(f"  총 {len(java_methods)}개 관계 발견")
        print()

        # Phase 2: JSP 간 관계
        print("[Phase 2] JSP 간 관계")
        print("-" * 40)
        jsp_relations = result['jsp_relationships']
        if jsp_relations:
            for rel in jsp_relations:
                print(f"  - {rel['src_jsp']} -> {rel['dst_jsp']} ({rel['relationship_type']}) [Line {rel['line_number']}]")
        else:
            print("  (JSP 간 관계 없음)")
        print(f"  총 {len(jsp_relations)}개 관계 발견")
        print()

        # Phase 3: 고도화 관계
        print("[Phase 3] 고도화 관계")
        print("-" * 40)
        advanced_rels = result['advanced_relationships']

        # EL 표현식
        print("  [EL 표현식]")
        el_expressions = advanced_rels.get('el_expressions', [])
        if el_expressions:
            for el in el_expressions:
                print(f"    - {el['jsp_name']}: ${{{el['el_expression']}}} -> {el['bean_name']}.{el['property_or_method']} ({el['access_type']}) [Line {el['line_number']}]")
        else:
            print("    (EL 표현식 없음)")
        print(f"    소계: {len(el_expressions)}개")
        print()

        # JSTL 태그
        print("  [JSTL 태그]")
        jstl_tags = advanced_rels.get('jstl_tags', [])
        if jstl_tags:
            for jstl in jstl_tags:
                print(f"    - {jstl['jsp_name']}: <{jstl['jstl_tag']}> -> {jstl['bean_reference']} [Line {jstl['line_number']}]")
        else:
            print("    (JSTL 태그 없음)")
        print(f"    소계: {len(jstl_tags)}개")
        print()

        # Java Bean
        print("  [Java Bean]")
        java_beans = advanced_rels.get('java_beans', [])
        if java_beans:
            for bean in java_beans:
                bean_info = f"{bean['bean_name'] or 'N/A'}"
                if bean['bean_class']:
                    bean_info += f" ({bean['bean_class']})"
                print(f"    - {bean['jsp_name']}: <{bean['tag_type']}> -> {bean_info} [Line {bean['line_number']}]")
        else:
            print("    (Java Bean 없음)")
        print(f"    소계: {len(java_beans)}개")
        print()

        # 태그 라이브러리
        print("  [태그 라이브러리]")
        tag_libraries = advanced_rels.get('tag_libraries', [])
        if tag_libraries:
            for taglib in tag_libraries:
                taglib_info = f"prefix='{taglib['taglib_prefix'] or 'N/A'}'"
                if taglib['taglib_uri']:
                    taglib_info += f", uri='{taglib['taglib_uri']}'"
                if taglib['taglib_dir']:
                    taglib_info += f", tagdir='{taglib['taglib_dir']}'"
                print(f"    - {taglib['jsp_name']}: {taglib_info} [Line {taglib['line_number']}]")
        else:
            print("    (태그 라이브러리 없음)")
        print(f"    소계: {len(tag_libraries)}개")
        print()

        # 전체 통계
        total_advanced = sum(len(v) for v in advanced_rels.values())
        total_all = len(java_methods) + len(jsp_relations) + total_advanced

        print("[전체 통계]")
        print("-" * 40)
        print(f"  Phase 1 (Java 메서드): {len(java_methods)}개")
        print(f"  Phase 2 (JSP 관계): {len(jsp_relations)}개")
        print(f"  Phase 3 (고도화): {total_advanced}개")
        print(f"  전체: {total_all}개 관계")

        print("\n[OK] Phase 2&3 테스트 완료!")

    except Exception as e:
        print(f"[ERROR] 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


def test_jsp_dependency_graph():
    """JSP 의존성 그래프 테스트"""
    print("\n" + "=" * 60)
    print("JSP 의존성 그래프 테스트")
    print("=" * 60)

    try:
        jsp_parser = JspParser()

        # 프로젝트 내 모든 JSP 파일 수집
        project_path = r"D:\Analyzer\CreateMetaDb\projects\sampleSrc"
        jsp_files = jsp_parser.get_filtered_jsp_files(project_path)

        print(f"JSP 파일 수집: {len(jsp_files)}개")
        for jsp_file in jsp_files:
            print(f"  - {jsp_file}")
        print()

        # 의존성 그래프 생성
        dependency_graph = jsp_parser.generate_jsp_dependency_graph(jsp_files)

        print("[의존성 그래프 분석 결과]")
        print("-" * 40)
        print(f"  노드(JSP 파일): {len(dependency_graph['nodes'])}개")
        print(f"  엣지(관계): {len(dependency_graph['edges'])}개")
        print(f"  순환 의존성: {len(dependency_graph['circular_dependencies'])}개")
        print(f"  독립 노드: {len(dependency_graph['isolated_nodes'])}개")
        print(f"  진입점: {len(dependency_graph['entry_points'])}개")
        print(f"  리프 노드: {len(dependency_graph['leaf_nodes'])}개")
        print()

        # 엣지 상세 정보
        if dependency_graph['edges']:
            print("[JSP 의존성 관계]")
            for edge in dependency_graph['edges']:
                print(f"  - {edge['source']} -> {edge['target']} ({edge['type']})")

        # 순환 의존성 경고
        if dependency_graph['circular_dependencies']:
            print("\n[WARNING] 순환 의존성 발견:")
            for cycle in dependency_graph['circular_dependencies']:
                print(f"  - {' -> '.join(cycle)}")

        print("\n[OK] 의존성 그래프 테스트 완료!")

    except Exception as e:
        print(f"[ERROR] 의존성 그래프 테스트 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Phase 2&3 기능 테스트
    test_jsp_phases()

    # JSP 의존성 그래프 테스트
    test_jsp_dependency_graph()