#!/usr/bin/env python3
"""
체인 연결 상태 확인 스크립트
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
        
        print("=== 체인 연결 상태 확인 ===")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. API_URL → METHOD 관계의 METHOD들이 SQL과 연결되어 있는지 확인
        print("\n1. API_URL → METHOD 관계의 METHOD들이 SQL과 연결되어 있는지 확인:")
        cursor.execute("""
            SELECT 
                api_url.component_name as api_name,
                method.component_name as method_name,
                COUNT(sql_rel.dst_id) as sql_connections
            FROM relationships api_method_rel
            JOIN components api_url ON api_method_rel.src_id = api_url.component_id
            JOIN components method ON api_method_rel.dst_id = method.component_id
            LEFT JOIN relationships sql_rel ON method.component_id = sql_rel.src_id 
                AND sql_rel.rel_type = 'CALL_QUERY' AND sql_rel.del_yn = 'N'
            WHERE api_method_rel.rel_type = 'CALL_METHOD'
              AND api_method_rel.del_yn = 'N'
              AND api_url.component_type = 'API_URL'
              AND method.component_type = 'METHOD'
            GROUP BY api_url.component_name, method.component_name
            ORDER BY sql_connections DESC
            LIMIT 10
        """)
        api_method_sql = cursor.fetchall()
        for api_name, method_name, sql_count in api_method_sql:
            print(f"  API: '{api_name}' → METHOD: '{method_name}' → SQL 연결: {sql_count}개")
        
        # 2. 특정 METHOD가 SQL과 연결되어 있는지 상세 확인
        print("\n2. getUserProfile 메서드의 SQL 연결 확인:")
        cursor.execute("""
            SELECT 
                method.component_name,
                sql_comp.component_name,
                sql_comp.component_type
            FROM components method
            JOIN relationships r ON method.component_id = r.src_id
            JOIN components sql_comp ON r.dst_id = sql_comp.component_id
            WHERE method.component_name = 'getUserProfile'
              AND r.rel_type = 'CALL_QUERY'
              AND r.del_yn = 'N'
        """)
        method_sql_details = cursor.fetchall()
        for method_name, sql_name, sql_type in method_sql_details:
            print(f"  METHOD: '{method_name}' → SQL: '{sql_name}' ({sql_type})")
        
        # 3. API_URL → METHOD 관계에서 사용된 METHOD ID들 확인
        print("\n3. API_URL → METHOD 관계에서 사용된 METHOD ID들:")
        cursor.execute("""
            SELECT DISTINCT method.component_id, method.component_name
            FROM relationships api_method_rel
            JOIN components api_url ON api_method_rel.src_id = api_url.component_id
            JOIN components method ON api_method_rel.dst_id = method.component_id
            WHERE api_method_rel.rel_type = 'CALL_METHOD'
              AND api_method_rel.del_yn = 'N'
              AND api_url.component_type = 'API_URL'
            ORDER BY method.component_name
            LIMIT 10
        """)
        api_method_ids = cursor.fetchall()
        for method_id, method_name in api_method_ids:
            print(f"  METHOD ID: {method_id}, Name: '{method_name}'")
        
        # 4. 이 METHOD ID들이 CALL_QUERY 관계에 있는지 확인
        print("\n4. 이 METHOD ID들이 CALL_QUERY 관계에 있는지 확인:")
        for method_id, method_name in api_method_ids[:3]:  # 처음 3개만 확인
            cursor.execute("""
                SELECT COUNT(*)
                FROM relationships r
                WHERE r.src_id = ? AND r.rel_type = 'CALL_QUERY' AND r.del_yn = 'N'
            """, (method_id,))
            call_query_count = cursor.fetchone()[0]
            print(f"  METHOD '{method_name}' (ID: {method_id}) → CALL_QUERY 관계: {call_query_count}개")
        
        conn.close()
            
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
