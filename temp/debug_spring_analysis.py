#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from parser.spring_entry_analyzer import SpringEntryAnalyzer
from parser.base_entry_analyzer import FileInfo

def debug_spring_analysis():
    print("=== Spring 분석기 디버깅 ===")
    
    # Spring 분석기 생성
    analyzer = SpringEntryAnalyzer()
    
    # ProductController.java 파일 테스트
    file_path = "src/main/java/com/example/controller/ProductController.java"
    full_path = f"projects/sampleSrc/{file_path}"
    
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_info = FileInfo(
            file_id=1,
            file_path=file_path,
            file_name="ProductController.java",
            file_type='JAVA',
            content=content,
            hash_value='test',
            line_count=len(content.split('\n'))
        )
        
        print(f"파일: {file_info.file_name}")
        print(f"경로: {file_info.file_path}")
        print(f"내용 길이: {len(content)} 문자")
        
        # 필터링 테스트
        is_target = analyzer.is_target_file(file_info.file_path)
        print(f"필터링 결과: {is_target}")
        
        if is_target:
            # 분석 실행
            print("\n--- analyze_backend_entry 실행 ---")
            entries = analyzer.analyze_backend_entry(file_info, None)
            print(f"분석 결과: {len(entries)}개 진입점")
            
            for entry in entries:
                print(f"  - {entry.class_name}.{entry.method_name} {entry.http_method} {entry.url_pattern}")
        else:
            print("필터링에서 제외됨")
    else:
        print(f"파일 없음: {full_path}")

if __name__ == "__main__":
    debug_spring_analysis()
