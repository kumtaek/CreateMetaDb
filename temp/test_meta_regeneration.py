#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메타데이터베이스 재생성 테스트 및 원인 파악
"""

import os
import sqlite3
import subprocess
import time
from pathlib import Path

def backup_metadata():
    """기존 메타데이터베이스 백업"""
    print("=== 1. 기존 메타데이터베이스 백업 ===")
    
    metadata_path = Path("projects/sampleSrc/metadata.db")
    if metadata_path.exists():
        backup_path = Path("projects/sampleSrc/metadata_backup.db")
        if backup_path.exists():
            backup_path.unlink()
        
        import shutil
        shutil.copy2(metadata_path, backup_path)
        print(f"백업 완료: {backup_path}")
    else:
        print("기존 메타데이터베이스가 없습니다.")

def delete_metadata():
    """메타데이터베이스 삭제"""
    print("\n=== 2. 메타데이터베이스 삭제 ===")
    
    metadata_files = [
        "projects/sampleSrc/metadata.db",
        "projects/sampleSrc/metadata.db-shm", 
        "projects/sampleSrc/metadata.db-wal"
    ]
    
    for file_path in metadata_files:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            print(f"삭제됨: {file_path}")
        else:
            print(f"없음: {file_path}")

def check_sample_files_before():
    """재생성 전 샘플 파일 상태 확인"""
    print("\n=== 3. 재생성 전 샘플 파일 상태 확인 ===")
    
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
            print(f"{file_name}: 존재 (크기: {stat.st_size} bytes, 수정시간: {stat.st_mtime})")
        else:
            print(f"{file_name}: 없음")

def regenerate_metadata():
    """메타데이터베이스 재생성"""
    print("\n=== 4. 메타데이터베이스 재생성 ===")
    
    start_time = time.time()
    
    try:
        # main.py 실행
        result = subprocess.run([
            "python", "main.py", "--project-name", "sampleSrc"
        ], capture_output=True, text=True, encoding='utf-8')
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"실행 시간: {duration:.2f}초")
        print(f"반환 코드: {result.returncode}")
        
        if result.stdout:
            print("표준 출력:")
            print(result.stdout[-1000:])  # 마지막 1000자만 출력
        
        if result.stderr:
            print("표준 오류:")
            print(result.stderr[-1000:])  # 마지막 1000자만 출력
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"실행 오류: {e}")
        return False

def check_sample_files_after():
    """재생성 후 샘플 파일 상태 확인"""
    print("\n=== 5. 재생성 후 샘플 파일 상태 확인 ===")
    
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
            print(f"{file_name}: 존재 (크기: {stat.st_size} bytes, 수정시간: {stat.st_mtime})")
        else:
            print(f"{file_name}: 없음")

def check_metadata_registration():
    """메타데이터 등록 현황 확인"""
    print("\n=== 6. 메타데이터 등록 현황 확인 ===")
    
    metadata_path = Path("projects/sampleSrc/metadata.db")
    if not metadata_path.exists():
        print("메타데이터베이스가 생성되지 않았습니다.")
        return
    
    conn = sqlite3.connect(str(metadata_path))
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
    print("\n=== 7. 컴포넌트 생성 현황 확인 ===")
    
    metadata_path = Path("projects/sampleSrc/metadata.db")
    if not metadata_path.exists():
        print("메타데이터베이스가 생성되지 않았습니다.")
        return
    
    conn = sqlite3.connect(str(metadata_path))
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

def check_api_components():
    """API 컴포넌트 현황 확인"""
    print("\n=== 8. API 컴포넌트 현황 확인 ===")
    
    metadata_path = Path("projects/sampleSrc/metadata.db")
    if not metadata_path.exists():
        print("메타데이터베이스가 생성되지 않았습니다.")
        return
    
    conn = sqlite3.connect(str(metadata_path))
    cursor = conn.cursor()
    
    # 전체 API 컴포넌트 수
    cursor.execute("""
        SELECT component_type, COUNT(*) as count
        FROM components 
        WHERE component_type IN ('API_ENTRY', 'FRONTEND_API') AND del_yn = 'N'
        GROUP BY component_type
    """)
    
    results = cursor.fetchall()
    print("전체 API 컴포넌트 현황:")
    for component_type, count in results:
        print(f"  - {component_type}: {count}개")
    
    # 샘플 컨트롤러의 API 컴포넌트
    sample_files = [
        "UserManagementController.java",
        "ProxyController.java", 
        "VersionedController.java",
        "MicroserviceController.java"
    ]
    
    print("\n샘플 컨트롤러의 API 컴포넌트:")
    for file_name in sample_files:
        cursor.execute("""
            SELECT c.component_name, c.component_type
            FROM files f
            JOIN components c ON f.file_id = c.file_id
            WHERE f.file_name = ? AND f.del_yn = 'N' AND c.del_yn = 'N'
            AND c.component_type IN ('API_ENTRY', 'FRONTEND_API')
            ORDER BY c.component_type, c.component_name
        """, (file_name,))
        
        results = cursor.fetchall()
        if results:
            print(f"{file_name}:")
            for component_name, component_type in results:
                print(f"  - {component_name} ({component_type})")
        else:
            print(f"{file_name}: API 컴포넌트 없음")
    
    conn.close()

def analyze_results():
    """결과 분석 및 해결책 제안"""
    print("\n=== 9. 결과 분석 및 해결책 제안 ===")
    
    metadata_path = Path("projects/sampleSrc/metadata.db")
    if not metadata_path.exists():
        print("❌ 메타데이터베이스 생성 실패")
        print("해결책: 메타데이터 생성 로그 확인 및 오류 수정")
        return
    
    conn = sqlite3.connect(str(metadata_path))
    cursor = conn.cursor()
    
    # 샘플 파일들의 컴포넌트 생성 현황 확인
    sample_files = [
        "UserManagementController.java",
        "ProxyController.java", 
        "VersionedController.java",
        "MicroserviceController.java"
    ]
    
    success_count = 0
    for file_name in sample_files:
        cursor.execute("""
            SELECT COUNT(*) FROM files f
            JOIN components c ON f.file_id = c.file_id
            WHERE f.file_name = ? AND f.del_yn = 'N' AND c.del_yn = 'N'
        """, (file_name,))
        
        component_count = cursor.fetchone()[0]
        if component_count > 0:
            success_count += 1
            print(f"✅ {file_name}: {component_count}개 컴포넌트 생성됨")
        else:
            print(f"❌ {file_name}: 컴포넌트 생성 실패")
    
    conn.close()
    
    print(f"\n성공률: {success_count}/{len(sample_files)} ({success_count/len(sample_files)*100:.1f}%)")
    
    if success_count == len(sample_files):
        print("🎉 모든 샘플 파일이 성공적으로 처리되었습니다!")
        print("해결책: CallChain 리포트 재생성하여 확인")
    elif success_count > 0:
        print("⚠️ 일부 샘플 파일만 성공적으로 처리되었습니다.")
        print("해결책: 실패한 파일들의 문법 및 구조 확인")
    else:
        print("❌ 모든 샘플 파일 처리 실패")
        print("해결책:")
        print("1. Java 파서 설정 확인")
        print("2. 파일 문법 오류 확인")
        print("3. 파싱 로그 상세 분석")

if __name__ == "__main__":
    print("메타데이터베이스 재생성 테스트")
    print("=" * 50)
    
    try:
        backup_metadata()
        delete_metadata()
        check_sample_files_before()
        
        success = regenerate_metadata()
        if success:
            print("✅ 메타데이터 재생성 성공")
        else:
            print("❌ 메타데이터 재생성 실패")
        
        check_sample_files_after()
        check_metadata_registration()
        check_components_creation()
        check_api_components()
        analyze_results()
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
