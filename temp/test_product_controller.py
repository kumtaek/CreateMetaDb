#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser.spring_entry_analyzer import SpringEntryAnalyzer
from parser.base_entry_analyzer import FileInfo

def test_product_controller():
    """ProductController 테스트"""
    print("=== ProductController 분석 테스트 ===")
    
    # Spring 분석기 초기화
    analyzer = SpringEntryAnalyzer()
    
    # ProductController 파일 내용 읽기
    with open('projects/sampleSrc/src/main/java/com/example/controller/ProductController.java', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # FileInfo 객체 생성
    file_info = FileInfo(
        file_id=1,
        file_path='src/main/java/com/example/controller',
        file_name='ProductController.java',
        file_type='JAVA',
        content=content,
        hash_value='test',
        line_count=len(content.split('\n'))
    )
    
    print(f"파일 내용 길이: {len(content)} 문자")
    print(f"파일 라인 수: {len(content.split('\n'))} 라인")
    
    # 클래스 정보 추출 테스트
    print("\n=== 클래스 정보 추출 테스트 ===")
    try:
        import javalang
        tree = javalang.parse.parse(content)
        for path, node in tree:
            if isinstance(node, javalang.tree.ClassDeclaration):
                print(f"클래스명: {node.name}")
                print(f"어노테이션 수: {len(node.annotations) if node.annotations else 0}")
                
                # 어노테이션 상세 분석
                if node.annotations:
                    for i, annotation in enumerate(node.annotations):
                        print(f"  어노테이션 {i+1}: {annotation.name}")
                        print(f"    annotation type: {type(annotation)}")
                        print(f"    annotation dir: {[attr for attr in dir(annotation) if not attr.startswith('_')]}")
                        
                        if hasattr(annotation, 'elements') and annotation.elements:
                            print(f"    elements 수: {len(annotation.elements)}")
                            for j, element in enumerate(annotation.elements):
                                print(f"      element {j+1}: name={element.name}")
                                print(f"        element type: {type(element)}")
                                print(f"        element dir: {[attr for attr in dir(element) if not attr.startswith('_')]}")
                                if hasattr(element, 'value'):
                                    print(f"        value type: {type(element.value)}")
                                    if hasattr(element.value, 'value'):
                                        print(f"        value.value: '{element.value.value}'")
                                    elif hasattr(element.value, 'values'):
                                        print(f"        value.values: {element.value.values}")
                                        if element.value.values:
                                            for k, val in enumerate(element.value.values):
                                                print(f"          values[{k}]: {val}")
                                else:
                                    print(f"        value: {element.value}")
                        else:
                            print(f"    elements: None")
                            
                        # @RequestMapping 특별 처리
                        if annotation.name == 'RequestMapping':
                            print(f"    RequestMapping 특별 분석:")
                            print(f"      annotation: {annotation}")
                            if hasattr(annotation, 'args'):
                                print(f"      args: {annotation.args}")
                            if hasattr(annotation, 'arguments'):
                                print(f"      arguments: {annotation.arguments}")
                
                class_info = analyzer._extract_class_info(node, content.split('\n'))
                if class_info:
                    print(f"추출된 클래스 URL: '{class_info['url']}'")
                break
    except Exception as e:
        print(f"클래스 정보 추출 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 분석 실행
    results = analyzer.analyze_backend_entry(file_info, None)
    
    print(f"\nProductController 분석 결과: {len(results)}개 진입점")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.http_method} {result.url_pattern} - {result.class_name}.{result.method_name}")
        print(f"     파일: {result.file_path}")
        print(f"     라인: {result.line_start}-{result.line_end}")
        print(f"     파라미터: {result.parameters}")
        print(f"     어노테이션: {result.annotations}")
        print()

if __name__ == "__main__":
    test_product_controller()
