#!/usr/bin/env python3
"""
데이터베이스 구조 확인 스크립트
현재 API 관련 컴포넌트와 관계 구조를 분석합니다.
"""

import sqlite3
import sys
import os

def check_database_structure():
    """데이터베이스 구조 확인"""
    try:
        # 데이터베이스 연결
        db_path = "projects/sampleSrc/metadata.db"
        if not os.path.exists(db_path):
            print(f"데이터베이스 파일이 존재하지 않습니다: {db_path}")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== 데이터베이스 구조 분석 ===")
        
        # 1. 컴포넌트 타입별 개수 확인
        print("\n1. 컴포넌트 타입별 개수:")
        cursor.execute("""
            SELECT component_type, COUNT(*) 
            FROM components 
            WHERE project_id = 1 AND del_yn = 'N' 
            GROUP BY component_type 
            ORDER BY COUNT(*) DESC
        """)
        
        for comp_type, count in cursor.fetchall():
            print(f"  {comp_type}: {count}개")
        
        # 2. API 관련 컴포넌트 상세 확인
        print("\n2. API 관련 컴포넌트 상세:")
        cursor.execute("""
            SELECT component_type, component_name, file_id, layer
            FROM components 
            WHERE project_id = 1 AND del_yn = 'N' 
            AND component_type IN ('API_URL', 'FRONTEND_API', 'API_ENTRY')
            ORDER BY component_type, component_name
        """)
        
        api_components = cursor.fetchall()
        if api_components:
            for comp_type, comp_name, file_id, layer in api_components:
                print(f"  {comp_type}: {comp_name} (file_id: {file_id}, layer: {layer})")
        else:
            print("  API 관련 컴포넌트가 없습니다.")
        
        # 3. 관계 타입별 개수 확인
        print("\n3. 관계 타입별 개수:")
        cursor.execute("""
            SELECT rel_type, COUNT(*) 
            FROM relationships 
            WHERE del_yn = 'N' 
            GROUP BY rel_type 
            ORDER BY COUNT(*) DESC
        """)
        
        for rel_type, count in cursor.fetchall():
            print(f"  {rel_type}: {count}개")
        
        # 4. API 관련 관계 확인
        print("\n4. API 관련 관계:")
        cursor.execute("""
            SELECT r.rel_type, 
                   src.component_type as src_type, src.component_name as src_name,
                   dst.component_type as dst_type, dst.component_name as dst_name
            FROM relationships r
            JOIN components src ON r.src_id = src.component_id
            JOIN components dst ON r.dst_id = dst.component_id
            WHERE r.del_yn = 'N' 
            AND (src.component_type IN ('API_URL', 'FRONTEND_API', 'API_ENTRY')
                 OR dst.component_type IN ('API_URL', 'FRONTEND_API', 'API_ENTRY'))
            ORDER BY r.rel_type, src.component_type, dst.component_type
        """)
        
        api_relationships = cursor.fetchall()
        if api_relationships:
            for rel_type, src_type, src_name, dst_type, dst_name in api_relationships:
                print(f"  {rel_type}: {src_type}({src_name}) → {dst_type}({dst_name})")
        else:
            print("  API 관련 관계가 없습니다.")
        
        # 5. 파일 타입별 개수 (JSP 파일 확인)
        print("\n5. 파일 타입별 개수:")
        cursor.execute("""
            SELECT file_type, COUNT(*) 
            FROM files 
            WHERE project_id = 1 AND del_yn = 'N' 
            GROUP BY file_type 
            ORDER BY COUNT(*) DESC
        """)
        
        for file_type, count in cursor.fetchall():
            print(f"  {file_type}: {count}개")
        
        conn.close()
        
    except Exception as e:
        print(f"오류 발생: {e}")
        return

if __name__ == "__main__":
    check_database_structure()
