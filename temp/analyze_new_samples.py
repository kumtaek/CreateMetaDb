#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def analyze_new_samples():
    """새로 생성된 샘플 파일들의 메타데이터 분석"""
    
    # 메타데이터베이스 연결
    db_path = 'projects/sampleSrc/metadata.db'
    if not os.path.exists(db_path):
        print(f"❌ 메타데이터베이스가 존재하지 않습니다: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== 새로 생성된 샘플 파일들 메타데이터 분석 ===\n")
    
    # 1. 컴포넌트 타입별 개수
    print("1. 컴포넌트 타입별 개수:")
    cursor.execute("""
        SELECT component_type, COUNT(*) as count 
        FROM components 
        WHERE del_yn = 'N' 
        GROUP BY component_type 
        ORDER BY count DESC
    """)
    results = cursor.fetchall()
    for comp_type, count in results:
        print(f"  {comp_type}: {count}개")
    
    print("\n" + "="*50 + "\n")
    
    # 2. 새로 생성한 샘플 컨트롤러들의 API_ENTRY 확인
    print("2. 새로 생성한 샘플 컨트롤러들의 API_ENTRY:")
    sample_controllers = [
        'UserManagementController',
        'ProxyController', 
        'VersionedController',
        'MicroserviceController'
    ]
    
    for controller in sample_controllers:
        cursor.execute("""
            SELECT c.component_name, c.component_type, f.file_name
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            WHERE c.component_type = 'API_ENTRY' 
              AND f.file_name LIKE ?
              AND c.del_yn = 'N'
            ORDER BY c.component_name
        """, (f'%{controller}%',))
        
        results = cursor.fetchall()
        print(f"\n  {controller}:")
        if results:
            for comp_name, comp_type, file_name in results:
                print(f"    - {comp_name} ({file_name})")
        else:
            print("    - API_ENTRY 없음")
    
    print("\n" + "="*50 + "\n")
    
    # 3. 새로 생성한 프론트엔드 파일들의 FRONTEND_API 확인
    print("3. 새로 생성한 프론트엔드 파일들의 FRONTEND_API:")
    frontend_files = [
        'VersionedUserManagement.jsx',
        'ProxyServiceManagement.jsx',
        'UserManagementPage.jsp',
        'MicroserviceDashboard.jsp'
    ]
    
    for frontend_file in frontend_files:
        cursor.execute("""
            SELECT c.component_name, c.component_type, f.file_name
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            WHERE c.component_type = 'FRONTEND_API' 
              AND f.file_name LIKE ?
              AND c.del_yn = 'N'
            ORDER BY c.component_name
        """, (f'%{frontend_file}%',))
        
        results = cursor.fetchall()
        print(f"\n  {frontend_file}:")
        if results:
            for comp_name, comp_type, file_name in results:
                print(f"    - {comp_name} ({file_name})")
        else:
            print("    - FRONTEND_API 없음")
    
    print("\n" + "="*50 + "\n")
    
    # 4. FRONTEND_API -> API_ENTRY 관계 확인
    print("4. FRONTEND_API -> API_ENTRY 관계:")
    cursor.execute("""
        SELECT 
            frontend.component_name as frontend_api,
            api.component_name as api_entry,
            f1.file_name as frontend_file,
            f2.file_name as backend_file
        FROM components frontend
        JOIN relationships r ON frontend.component_id = r.src_id AND r.rel_type = 'CALL_API_F2B'
        JOIN components api ON r.dst_id = api.component_id
        JOIN files f1 ON frontend.file_id = f1.file_id
        JOIN files f2 ON api.file_id = f2.file_id
        WHERE frontend.component_type = 'FRONTEND_API' 
          AND api.component_type = 'API_ENTRY'
          AND frontend.del_yn = 'N'
          AND api.del_yn = 'N'
        ORDER BY frontend.component_name, api.component_name
    """)
    
    results = cursor.fetchall()
    if results:
        for frontend_api, api_entry, frontend_file, backend_file in results:
            print(f"  {frontend_api} ({frontend_file}) -> {api_entry} ({backend_file})")
    else:
        print("  FRONTEND_API -> API_ENTRY 관계 없음")
    
    print("\n" + "="*50 + "\n")
    
    # 5. 전체 API_ENTRY와 FRONTEND_API 개수
    print("5. 전체 API_ENTRY와 FRONTEND_API 개수:")
    cursor.execute("SELECT COUNT(*) FROM components WHERE component_type = 'API_ENTRY' AND del_yn = 'N'")
    api_entry_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM components WHERE component_type = 'FRONTEND_API' AND del_yn = 'N'")
    frontend_api_count = cursor.fetchone()[0]
    
    print(f"  API_ENTRY: {api_entry_count}개")
    print(f"  FRONTEND_API: {frontend_api_count}개")
    
    conn.close()
    print("\n=== 분석 완료 ===")

if __name__ == "__main__":
    analyze_new_samples()
