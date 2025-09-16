#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
샘플 컨트롤러 메타데이터 생성 누락 원인 파악 및 해결책 도출
"""

import os
import sqlite3
import sys
from pathlib import Path

def check_file_existence():
    """샘플 컨트롤러 파일들의 존재 여부 확인"""
    print("=== 1. 파일 존재 여부 확인 ===")
    
    sample_files = [
        "UserManagementController.java",
        "ProxyController.java", 
        "VersionedController.java",
        "MicroserviceController.java"
    ]
    
    base_path = Path("projects/sampleSrc/src/main/java/com/example/controller")
    
    for file_name in sample_files:
        file_path = base_path / file_name
        exists = file_path.exists()
        print(f"{file_name}: {'존재' if exists else '없음'}")
        if exists:
            stat = file_path.stat()
            print(f"  - 크기: {stat.st_size} bytes")
            print(f"  - 수정시간: {stat.st_mtime}")

def check_metadata_registration():
    """메타데이터베이스에서 파일 등록 현황 확인"""
    print("\n=== 2. 메타데이터베이스 파일 등록 현황 ===")
    
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    sample_files = [
        "UserManagementController.java",
        "ProxyController.java", 
        "VersionedController.java",
        "MicroserviceController.java"
    ]
    
    for file_name in sample_files:
        cursor.execute("""
            SELECT file_id, file_path, file_type, del_yn 
            FROM files 
            WHERE file_name = ? AND del_yn = 'N'
        """, (file_name,))
        
        result = cursor.fetchone()
        if result:
            print(f"{file_name}: 등록됨 (ID: {result[0]}, 경로: {result[1]}, 타입: {result[2]})")
        else:
            print(f"{file_name}: 등록되지 않음")
    
    conn.close()

def check_components_creation():
    """컴포넌트 생성 현황 확인"""
    print("\n=== 3. 컴포넌트 생성 현황 ===")
    
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    sample_files = [
        "UserManagementController.java",
        "ProxyController.java", 
        "VersionedController.java",
        "MicroserviceController.java"
    ]
    
    for file_name in sample_files:
        cursor.execute("""
            SELECT c.component_type, COUNT(*) as count
            FROM files f
            JOIN components c ON f.file_id = c.file_id
            WHERE f.file_name = ? AND f.del_yn = 'N' AND c.del_yn = 'N'
            GROUP BY c.component_type
            ORDER BY c.component_type
        """, (file_name,))
        
        results = cursor.fetchall()
        if results:
            print(f"{file_name}:")
            for component_type, count in results:
                print(f"  - {component_type}: {count}개")
        else:
            print(f"{file_name}: 컴포넌트 없음")
    
    conn.close()

def compare_with_working_controllers():
    """정상 작동하는 컨트롤러와 비교"""
    print("\n=== 4. 정상 작동하는 컨트롤러와 비교 ===")
    
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    working_files = ["ProductController.java", "UserController.java"]
    
    for file_name in working_files:
        cursor.execute("""
            SELECT f.file_id, f.file_path, f.file_type, f.del_yn,
                   COUNT(c.component_id) as component_count
            FROM files f
            LEFT JOIN components c ON f.file_id = c.file_id AND c.del_yn = 'N'
            WHERE f.file_name = ? AND f.del_yn = 'N'
            GROUP BY f.file_id, f.file_path, f.file_type, f.del_yn
        """, (file_name,))
        
        result = cursor.fetchone()
        if result:
            print(f"{file_name}:")
            print(f"  - 파일 ID: {result[0]}")
            print(f"  - 경로: {result[1]}")
            print(f"  - 타입: {result[2]}")
            print(f"  - 삭제여부: {result[3]}")
            print(f"  - 컴포넌트 수: {result[4]}개")
    
    conn.close()

def check_java_parsing_logs():
    """Java 파싱 로그 확인"""
    print("\n=== 5. Java 파싱 로그 확인 ===")
    
    log_file = "temp/meta_regeneration.log"
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Java 관련 로그 찾기
        java_logs = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'java' in line.lower() or 'controller' in line.lower():
                java_logs.append(f"라인 {i+1}: {line}")
        
        print(f"Java 관련 로그 {len(java_logs)}개 발견:")
        for log in java_logs[:10]:  # 처음 10개만 출력
            print(f"  {log}")
    else:
        print("메타데이터 생성 로그 파일이 없습니다.")

def check_file_scanning_pattern():
    """파일 스캔 패턴 확인"""
    print("\n=== 6. 파일 스캔 패턴 확인 ===")
    
    # 실제 파일 시스템에서 Java 파일들 확인
    controller_dir = Path("projects/sampleSrc/src/main/java/com/example/controller")
    
    if controller_dir.exists():
        java_files = list(controller_dir.glob("*.java"))
        print(f"컨트롤러 디렉토리의 Java 파일 수: {len(java_files)}")
        
        for java_file in java_files:
            print(f"  - {java_file.name}")
    else:
        print("컨트롤러 디렉토리가 존재하지 않습니다.")

def analyze_root_cause():
    """근본 원인 분석"""
    print("\n=== 7. 근본 원인 분석 ===")
    
    # 1. 파일 존재 여부
    sample_files = [
        "UserManagementController.java",
        "ProxyController.java", 
        "VersionedController.java",
        "MicroserviceController.java"
    ]
    
    base_path = Path("projects/sampleSrc/src/main/java/com/example/controller")
    missing_files = []
    
    for file_name in sample_files:
        if not (base_path / file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"❌ 파일 시스템에 없는 파일들: {missing_files}")
        return
    
    # 2. 메타데이터 등록 여부
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    unregistered_files = []
    for file_name in sample_files:
        cursor.execute("SELECT file_id FROM files WHERE file_name = ? AND del_yn = 'N'", (file_name,))
        if not cursor.fetchone():
            unregistered_files.append(file_name)
    
    if unregistered_files:
        print(f"❌ 메타데이터에 등록되지 않은 파일들: {unregistered_files}")
        print("원인: 파일 스캔 단계에서 누락됨")
        return
    
    # 3. 컴포넌트 생성 여부
    no_components_files = []
    for file_name in sample_files:
        cursor.execute("""
            SELECT COUNT(*) FROM files f
            JOIN components c ON f.file_id = c.file_id
            WHERE f.file_name = ? AND f.del_yn = 'N' AND c.del_yn = 'N'
        """, (file_name,))
        
        if cursor.fetchone()[0] == 0:
            no_components_files.append(file_name)
    
    if no_components_files:
        print(f"❌ 컴포넌트가 생성되지 않은 파일들: {no_components_files}")
        print("원인: Java 파싱 단계에서 실패함")
        return
    
    print("✅ 모든 파일이 정상적으로 처리되었습니다.")
    
    conn.close()

def suggest_solutions():
    """해결책 제안"""
    print("\n=== 8. 해결책 제안 ===")
    
    print("가능한 해결책들:")
    print("1. 메타데이터 재생성 (--force 옵션 사용)")
    print("2. 특정 파일만 재파싱")
    print("3. Java 파서 설정 확인")
    print("4. 파일 경로 및 권한 확인")
    print("5. 파싱 로그 상세 확인")

if __name__ == "__main__":
    print("샘플 컨트롤러 메타데이터 생성 누락 원인 파악")
    print("=" * 50)
    
    try:
        check_file_existence()
        check_metadata_registration()
        check_components_creation()
        compare_with_working_controllers()
        check_java_parsing_logs()
        check_file_scanning_pattern()
        analyze_root_cause()
        suggest_solutions()
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
