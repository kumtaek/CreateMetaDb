#!/usr/bin/env python3
"""
AST 구조 디버깅
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_ast_structure():
    """AST 구조 디버깅"""

    # 파일 읽기
    file_path = "projects/sampleSrc/src/main/java/com/example/controller/SyntaxErrorController.java"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        import javalang

        tree = javalang.parse.parse(content)

        print("AST 구조 분석:")
        print("=" * 50)

        # 클래스와 메서드 찾기
        for path, node in tree:
            if isinstance(node, javalang.tree.ClassDeclaration):
                print(f"클래스: {node.name}")

                # 클래스 어노테이션 확인
                if hasattr(node, 'annotations') and node.annotations:
                    for anno in node.annotations:
                        print(f"  클래스 어노테이션: @{anno.name}")
                        if hasattr(anno, 'element') and anno.element:
                            print(f"    element: {anno.element}")
                        if hasattr(anno, 'elements') and anno.elements:
                            for elem in anno.elements:
                                print(f"    elements: {elem.name} = {elem.value}")

                # 메서드 찾기
                for method_path, method_node in tree:
                    if (isinstance(method_node, javalang.tree.MethodDeclaration) and
                        method_path[0] == path[0]):  # 같은 클래스 내 메서드

                        print(f"  메서드: {method_node.name}")

                        # 메서드 어노테이션 확인
                        if hasattr(method_node, 'annotations') and method_node.annotations:
                            for anno in method_node.annotations:
                                print(f"    어노테이션: @{anno.name}")

                                # annotation 구조 상세 분석
                                print(f"      type: {type(anno)}")
                                if hasattr(anno, 'element'):
                                    print(f"      element: {anno.element}")
                                    if anno.element and hasattr(anno.element, 'value'):
                                        print(f"        element.value: {anno.element.value}")

                                if hasattr(anno, 'elements'):
                                    print(f"      elements: {anno.elements}")
                                    if anno.elements:
                                        for i, elem in enumerate(anno.elements):
                                            print(f"        elements[{i}].name: {elem.name}")
                                            print(f"        elements[{i}].value: {elem.value}")
                                            print(f"        elements[{i}].value type: {type(elem.value)}")
                                            if hasattr(elem.value, 'value'):
                                                print(f"        elements[{i}].value.value: {elem.value.value}")
                                            if hasattr(elem.value, 'member'):
                                                print(f"        elements[{i}].value.member: {elem.value.member}")
                                print("    ---")
                        print("  ---")
                print("---")

    except Exception as e:
        print(f"AST 파싱 오류: {e}")

if __name__ == "__main__":
    debug_ast_structure()