#!/usr/bin/env python3
"""
현재 메타데이터 상태 확인 스크립트
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
        
        print("=== 현재 메타데이터 상태 확인 ===")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. API_URL 컴포넌트와 연결된 파일 확인
        print("\n1. API_URL 컴포넌트와 연결된 파일:")
        cursor.execute("""
            SELECT 
                api_url.component_name,
                f.file_name,
                f.file_type
            FROM components api_url
            JOIN files f ON api_url.file_id = f.file_id
            WHERE api_url.component_type = 'API_URL' 
              AND api_url.del_yn = 'N'
            ORDER BY api_url.component_name
            LIMIT 10
        """)
        api_url_files = cursor.fetchall()
        for api_name, file_name, file_type in api_url_files:
            print(f"  API: '{api_name}' → File: {file_name} ({file_type})")
        
        # 2. JSP 파일 개수 확인
        print("\n2. JSP 파일 개수:")
        cursor.execute("SELECT COUNT(*) FROM files WHERE file_type = 'JSP' AND del_yn = 'N'")
        jsp_count = cursor.fetchone()[0]
        print(f"  JSP 파일: {jsp_count}개")
        
        # 3. JSP 파일 목록
        print("\n3. JSP 파일 목록:")
        cursor.execute("SELECT file_id, file_name FROM files WHERE file_type = 'JSP' AND del_yn = 'N'")
        jsp_files = cursor.fetchall()
        for file_id, file_name in jsp_files:
            print(f"  ID: {file_id}, Name: {file_name}")
        
        # 4. API_URL → METHOD 관계 확인
        print("\n4. API_URL → METHOD 관계:")
        cursor.execute("""
            SELECT 
                api_url.component_name,
                method.component_name,
                r.src_id, r.dst_id
            FROM relationships r
            JOIN components api_url ON r.src_id = api_url.component_id
            JOIN components method ON r.dst_id = method.component_id
            WHERE r.rel_type = 'CALL_METHOD' 
              AND api_url.component_type = 'API_URL'
              AND method.component_type = 'METHOD'
              AND r.del_yn = 'N'
            LIMIT 5
        """)
        api_method_relations = cursor.fetchall()
        for api_name, method_name, src_id, dst_id in api_method_relations:
            print(f"  API: '{api_name}' → METHOD: '{method_name}' (src: {src_id}, dst: {dst_id})")
        
        # 5. METHOD → SQL 관계 확인
        print("\n5. METHOD → SQL 관계:")
        cursor.execute("""
            SELECT 
                method.component_name,
                sql_comp.component_name,
                sql_comp.component_type
            FROM relationships r
            JOIN components method ON r.src_id = method.component_id
            JOIN components sql_comp ON r.dst_id = sql_comp.component_id
            WHERE r.rel_type = 'CALL_QUERY'
              AND method.component_type = 'METHOD'
              AND sql_comp.component_type LIKE 'SQL_%'
              AND r.del_yn = 'N'
            LIMIT 5
        """)
        method_sql_relations = cursor.fetchall()
        for method_name, sql_name, sql_type in method_sql_relations:
            print(f"  METHOD: '{method_name}' → SQL: '{sql_name}' ({sql_type})")
        
        # 6. 완전한 체인 개수 확인
        print("\n6. 완전한 체인 개수:")
        cursor.execute("""
            SELECT COUNT(DISTINCT api_url.component_id)
            FROM components api_url
            JOIN relationships r1 ON api_url.component_id = r1.src_id AND r1.rel_type = 'CALL_METHOD'
            JOIN components method ON r1.dst_id = method.component_id
            JOIN relationships r2 ON method.component_id = r2.src_id AND r2.rel_type = 'CALL_QUERY'
            JOIN components sql_comp ON r2.dst_id = sql_comp.component_id
            WHERE api_url.component_type = 'API_URL'
              AND method.component_type = 'METHOD'
              AND sql_comp.component_type LIKE 'SQL_%'
              AND api_url.del_yn = 'N'
              AND method.del_yn = 'N'
              AND sql_comp.del_yn = 'N'
              AND r1.del_yn = 'N'
              AND r2.del_yn = 'N'
        """)
        full_chain_count = cursor.fetchone()[0]
        print(f"  완전한 체인: {full_chain_count}개")
        
        conn.close()
            
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
