#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Java 파싱 단계에서 컴포넌트 생성 실패 원인 분석
"""

import sqlite3
import os
from pathlib import Path

def check_file_timestamps():
    """파일 생성 시간과 메타데이터 생성 시간 비교"""
    print("=== 1. 파일 생성 시간 vs 메타데이터 생성 시간 ===")
    
    sample_files = [
        "UserManagementController.java",
        "ProxyController.java", 
        "VersionedController.java",
        "MicroserviceController.java"
    ]
    
    base_path = Path("projects/sampleSrc/src/main/java/com/example/controller")
    
    for file_name in sample_files:
        file_path = base_path / file_name
        if file_path.exists():
            stat = file_path.stat()
            print(f"{file_name}:")
            print(f"  - 파일 생성시간: {stat.st_mtime}")
            print(f"  - 파일 크기: {stat.st_size} bytes")

def check_java_parsing_conditions():
    """Java 파싱 조건 확인"""
    print("\n=== 2. Java 파싱 조건 확인 ===")
    
    # 메타데이터베이스에서 Java 파일들의 처리 현황 확인
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    # 모든 Java 파일의 컴포넌트 생성 현황
    cursor.execute("""
        SELECT f.file_name, f.file_type, COUNT(c.component_id) as component_count
        FROM files f
        LEFT JOIN components c ON f.file_id = c.file_id AND c.del_yn = 'N'
        WHERE f.file_type = 'JAVA' AND f.del_yn = 'N'
        GROUP BY f.file_id, f.file_name, f.file_type
        ORDER BY component_count DESC
    """)
    
    results = cursor.fetchall()
    print("Java 파일별 컴포넌트 생성 현황:")
    
    zero_components = []
    for file_name, file_type, component_count in results:
        print(f"  {file_name}: {component_count}개")
        if component_count == 0:
            zero_components.append(file_name)
    
    print(f"\n컴포넌트가 0개인 Java 파일 수: {len(zero_components)}")
    if zero_components:
        print("컴포넌트가 0개인 파일들:")
        for file_name in zero_components:
            print(f"  - {file_name}")
    
    conn.close()

def check_parsing_errors():
    """파싱 오류 확인"""
    print("\n=== 3. 파싱 오류 확인 ===")
    
    # 샘플 컨트롤러 파일들의 문법 검사
    sample_files = [
        "UserManagementController.java",
        "ProxyController.java", 
        "VersionedController.java",
        "MicroserviceController.java"
    ]
    
    base_path = Path("projects/sampleSrc/src/main/java/com/example/controller")
    
    for file_name in sample_files:
        file_path = base_path / file_name
        if file_path.exists():
            print(f"\n{file_name} 문법 검사:")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 기본적인 Java 문법 검사
                if 'class' in content and '{' in content and '}' in content:
                    print("  ✅ 기본 클래스 구조: 정상")
                else:
                    print("  ❌ 기본 클래스 구조: 문제")
                
                if '@RestController' in content or '@Controller' in content:
                    print("  ✅ Spring 어노테이션: 있음")
                else:
                    print("  ❌ Spring 어노테이션: 없음")
                
                if '@RequestMapping' in content or '@GetMapping' in content or '@PostMapping' in content:
                    print("  ✅ API 매핑 어노테이션: 있음")
                else:
                    print("  ❌ API 매핑 어노테이션: 없음")
                
                # 괄호 균형 검사
                open_braces = content.count('{')
                close_braces = content.count('}')
                if open_braces == close_braces:
                    print("  ✅ 괄호 균형: 정상")
                else:
                    print(f"  ❌ 괄호 균형: 문제 (열림: {open_braces}, 닫힘: {close_braces})")
                
            except Exception as e:
                print(f"  ❌ 파일 읽기 오류: {e}")

def compare_with_working_file():
    """정상 작동하는 파일과 비교"""
    print("\n=== 4. 정상 작동하는 파일과 비교 ===")
    
    # ProductController.java와 샘플 컨트롤러 비교
    working_file = Path("projects/sampleSrc/src/main/java/com/example/controller/ProductController.java")
    sample_file = Path("projects/sampleSrc/src/main/java/com/example/controller/UserManagementController.java")
    
    if working_file.exists() and sample_file.exists():
        print("ProductController.java vs UserManagementController.java 비교:")
        
        with open(working_file, 'r', encoding='utf-8') as f:
            working_content = f.read()
        
        with open(sample_file, 'r', encoding='utf-8') as f:
            sample_content = f.read()
        
        print(f"  ProductController 크기: {len(working_content)} bytes")
        print(f"  UserManagementController 크기: {len(sample_content)} bytes")
        
        # 공통 요소 확인
        common_elements = ['@RestController', '@RequestMapping', '@GetMapping', '@PostMapping', 'public class']
        for element in common_elements:
            working_has = element in working_content
            sample_has = element in sample_content
            print(f"  {element}: ProductController({working_has}) vs UserManagementController({sample_has})")

def check_parsing_order():
    """파싱 순서 확인"""
    print("\n=== 5. 파싱 순서 확인 ===")
    
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    # 파일 ID 순서로 정렬해서 파싱 순서 확인
    cursor.execute("""
        SELECT file_id, file_name, file_path
        FROM files 
        WHERE file_type = 'JAVA' AND del_yn = 'N'
        ORDER BY file_id
    """)
    
    results = cursor.fetchall()
    print("Java 파일 파싱 순서 (file_id 기준):")
    
    sample_file_ids = []
    for file_id, file_name, file_path in results:
        if 'Controller' in file_name:
            print(f"  ID {file_id}: {file_name}")
            if file_name in ['UserManagementController.java', 'ProxyController.java', 
                           'VersionedController.java', 'MicroserviceController.java']:
                sample_file_ids.append(file_id)
    
    print(f"\n샘플 컨트롤러 파일 ID들: {sample_file_ids}")
    
    conn.close()

def suggest_root_cause():
    """근본 원인 제안"""
    print("\n=== 6. 근본 원인 제안 ===")
    
    print("가능한 원인들:")
    print("1. 파일 생성 시간 문제: 메타데이터 생성 후에 파일이 생성됨")
    print("2. Java 파서 설정 문제: 특정 조건을 만족하지 않아 파싱 스킵")
    print("3. 파일 경로 문제: 상대 경로나 절대 경로 인식 오류")
    print("4. 파싱 순서 문제: 특정 순서에서만 파싱이 실패")
    print("5. 메모리/리소스 문제: 파싱 중 메모리 부족으로 실패")
    print("6. 파일 권한 문제: 파일 읽기 권한 부족")
    
    print("\n해결책 제안:")
    print("1. 메타데이터 강제 재생성 (--force 옵션)")
    print("2. 특정 파일만 재파싱")
    print("3. Java 파서 로그 상세 확인")
    print("4. 파일 권한 및 경로 확인")
    print("5. 파싱 순서 변경 테스트")

if __name__ == "__main__":
    print("Java 파싱 단계 컴포넌트 생성 실패 원인 분석")
    print("=" * 50)
    
    try:
        check_file_timestamps()
        check_java_parsing_conditions()
        check_parsing_errors()
        compare_with_working_file()
        check_parsing_order()
        suggest_root_cause()
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
