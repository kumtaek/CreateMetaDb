#!/usr/bin/env python3
"""
SQL 컴포넌트 상태 확인 스크립트
"""

import sqlite3
import os

def main():
    try:
        # 데이터베이스 경로
        db_path = "projects/sampleSrc/metadata.db"
        
        if not os.path.exists(db_path):
            print(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}")
            return
        
        print("=== SQL 컴포넌트 상태 확인 ===")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. SQL 관련 컴포넌트 개수
        print("\n1. SQL 관련 컴포넌트 개수:")
        cursor.execute("""
            SELECT component_type, COUNT(*) as count
            FROM components 
            WHERE component_type LIKE 'SQL_%' OR component_type = 'QUERY'
              AND del_yn = 'N'
            GROUP BY component_type
            ORDER BY count DESC
        """)
        sql_components = cursor.fetchall()
        for comp_type, count in sql_components:
            print(f"  {comp_type}: {count}개")
        
        # 2. METHOD 컴포넌트 개수
        print("\n2. METHOD 컴포넌트 개수:")
        cursor.execute("SELECT COUNT(*) FROM components WHERE component_type = 'METHOD' AND del_yn = 'N'")
        method_count = cursor.fetchone()[0]
        print(f"  METHOD: {method_count}개")
        
        # 3. CALL_QUERY 관계 개수
        print("\n3. CALL_QUERY 관계 개수:")
        cursor.execute("SELECT COUNT(*) FROM relationships WHERE rel_type = 'CALL_QUERY' AND del_yn = 'N'")
        call_query_count = cursor.fetchone()[0]
        print(f"  CALL_QUERY: {call_query_count}개")
        
        # 4. XML 파일 개수
        print("\n4. XML 파일 개수:")
        cursor.execute("SELECT COUNT(*) FROM files WHERE file_type = 'XML' AND del_yn = 'N'")
        xml_count = cursor.fetchone()[0]
        print(f"  XML 파일: {xml_count}개")
        
        # 5. XML 파일 목록
        print("\n5. XML 파일 목록:")
        cursor.execute("SELECT file_id, file_name FROM files WHERE file_type = 'XML' AND del_yn = 'N' LIMIT 5")
        xml_files = cursor.fetchall()
        for file_id, file_name in xml_files:
            print(f"  ID: {file_id}, Name: {file_name}")
        
        # 6. SQL 컴포넌트 샘플
        print("\n6. SQL 컴포넌트 샘플:")
        cursor.execute("""
            SELECT c.component_name, c.component_type, f.file_name
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            WHERE c.component_type LIKE 'SQL_%'
              AND c.del_yn = 'N'
            LIMIT 5
        """)
        sql_samples = cursor.fetchall()
        for sql_name, sql_type, file_name in sql_samples:
            print(f"  {sql_type}: '{sql_name}' (File: {file_name})")
        
        conn.close()
            
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
