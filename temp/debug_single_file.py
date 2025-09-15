#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from backend_entry_loading import BackendEntryLoadingEngine
from parser.base_entry_analyzer import FileInfo

def debug_single_file():
    print("=== 단일 파일 디버깅 ===")
    
    # BackendEntryLoadingEngine 인스턴스 생성
    engine = BackendEntryLoadingEngine("sampleSrc")
    
    # ProductController.java 파일만 테스트
    file_path = "src/main/java/com/example/controller/ProductController.java"
    full_path = f"projects/sampleSrc/{file_path}"
    
    if os.path.exists(full_path):
        print(f"\n--- {file_path} 테스트 ---")
        
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
        
        print(f"파일 정보: {file_info.file_name}")
        print(f"로드된 분석기 수: {len(engine.analyzers)}")
        
        for i, analyzer in enumerate(engine.analyzers):
            print(f"  분석기 {i+1}: {analyzer.get_framework_name()}")
            
            # 필터링 테스트
            is_target = engine._is_target_for_analyzer(file_info, analyzer)
            print(f"    필터링 결과: {is_target}")
            
            if is_target:
                # 분석 실행
                print("    분석 실행 중...")
                entries = analyzer.analyze_backend_entry(file_info, engine.stats)
                print(f"    진입점 {len(entries)}개 발견")
                
                for entry in entries:
                    print(f"      - {entry.class_name}.{entry.method_name} {entry.http_method} {entry.url_pattern}")
            else:
                print("    -> 필터링에서 제외됨")
        
        # _filter_and_analyze_file 메서드 직접 테스트
        print(f"\n--- _filter_and_analyze_file 메서드 테스트 ---")
        file_entries = engine._filter_and_analyze_file(file_info)
        print(f"최종 결과: {len(file_entries)}개 진입점")
        
    else:
        print(f"파일 없음: {full_path}")

if __name__ == "__main__":
    debug_single_file()
