#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from backend_entry_loading import BackendEntryLoadingEngine
from parser.base_entry_analyzer import FileInfo

def debug_filtering():
    print("=== 필터링 디버깅 ===")
    
    # BackendEntryLoadingEngine 인스턴스 생성
    engine = BackendEntryLoadingEngine("sampleSrc")
    
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
        print(f"로드된 분석기 수: {len(engine.analyzers)}")
        
        for i, analyzer in enumerate(engine.analyzers):
            print(f"\n--- 분석기 {i+1}: {analyzer.get_framework_name()} ---")
            
            # 직접 필터링 테스트
            try:
                is_target = analyzer.is_target_file(file_info.file_path)
                print(f"  analyzer.is_target_file() 결과: {is_target}")
            except Exception as e:
                print(f"  analyzer.is_target_file() 오류: {str(e)}")
            
            # _is_target_for_analyzer 메서드 테스트
            try:
                is_target2 = engine._is_target_for_analyzer(file_info, analyzer)
                print(f"  engine._is_target_for_analyzer() 결과: {is_target2}")
            except Exception as e:
                print(f"  engine._is_target_for_analyzer() 오류: {str(e)}")
            
            # 분석기 설정 확인
            if hasattr(analyzer, 'config'):
                print(f"  분석기 설정: {analyzer.config}")
            if hasattr(analyzer, 'include_patterns'):
                print(f"  include_patterns: {analyzer.include_patterns}")
            if hasattr(analyzer, 'exclude_patterns'):
                print(f"  exclude_patterns: {analyzer.exclude_patterns}")

if __name__ == "__main__":
    debug_filtering()
