#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from backend_entry_loading import BackendEntryLoadingEngine

def debug_analyze_entries():
    print("=== _analyze_backend_entries 디버깅 ===")
    
    # BackendEntryLoadingEngine 인스턴스 생성
    engine = BackendEntryLoadingEngine("sampleSrc")
    
    # Java 파일 수집
    java_files = engine._get_java_files()
    print(f"수집된 Java 파일 수: {len(java_files)}")
    
    # Controller 파일만 필터링
    controller_files = [f for f in java_files if 'Controller' in f.file_name]
    print(f"Controller 파일 수: {len(controller_files)}")
    
    for i, file_info in enumerate(controller_files):
        print(f"\n--- 파일 {i+1}: {file_info.file_name} ---")
        print(f"  파일 경로: {file_info.file_path}")
        print(f"  해시값: {file_info.hash_value}")
        print(f"  라인 수: {file_info.line_count}")
        
        # 캐시 확인
        cached_entries = engine.cache.get(file_info.hash_value)
        if cached_entries:
            print(f"  캐시에서 발견: {len(cached_entries)}개 진입점")
            continue
        
        # 2차 필터링 및 분석 실행
        print("  _filter_and_analyze_file 실행 중...")
        file_entries = engine._filter_and_analyze_file(file_info)
        print(f"  분석 결과: {len(file_entries)}개 진입점")
        
        if file_entries:
            for entry in file_entries:
                print(f"    - {entry.class_name}.{entry.method_name} {entry.http_method} {entry.url_pattern}")
    
    # 전체 분석 실행
    print(f"\n--- 전체 분석 실행 ---")
    all_entries = engine._analyze_backend_entries(java_files)
    print(f"전체 진입점 수: {len(all_entries)}")

if __name__ == "__main__":
    debug_analyze_entries()
