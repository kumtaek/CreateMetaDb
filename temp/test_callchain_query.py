#!/usr/bin/env python3
"""
CallChain 쿼리 테스트 스크립트
"""

import sqlite3
import os

def test_callchain_query():
    """CallChain 쿼리 테스트"""
    try:
        db_path = "projects/sampleSrc/metadata.db"
        if not os.path.exists(db_path):
            print(f"데이터베이스 파일이 존재하지 않습니다: {db_path}")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== CallChain 쿼리 테스트 ===")
        
        # 수정된 API_URL 체인 쿼리 테스트
        api_chain_query = """
            SELECT 
                ROW_NUMBER() OVER (ORDER BY jsp_file.file_name, api_url.component_name) as chain_id,
                jsp_file.file_name as jsp_file,
                api_url.component_name as api_entry,
                '' as virtual_endpoint,
                class.class_name as class_name,
                method.component_name as method_name,
                xml_file.file_name as xml_file,
                sql.component_name as query_id,
                sql.component_type as query_type,
                GROUP_CONCAT(DISTINCT t.table_name) as related_tables
            FROM components api_url
            JOIN files jsp_file ON api_url.file_id = jsp_file.file_id
            JOIN relationships r1 ON api_url.component_id = r1.src_id AND r1.rel_type = 'CALL_METHOD'
            JOIN components method ON r1.dst_id = method.component_id
            JOIN files java_file ON method.file_id = java_file.file_id
            JOIN classes class ON method.parent_id = class.class_id
            JOIN relationships r2 ON method.component_id = r2.src_id AND r2.rel_type = 'CALL_QUERY'
            JOIN components sql ON r2.dst_id = sql.component_id
            JOIN files xml_file ON sql.file_id = xml_file.file_id
            LEFT JOIN relationships r3 ON sql.component_id = r3.src_id AND r3.rel_type = 'USE_TABLE'
            LEFT JOIN tables t ON r3.dst_id = t.component_id
            JOIN projects p ON api_url.project_id = p.project_id
            WHERE p.project_name = 'sampleSrc'
              AND api_url.component_type = 'API_URL'
              AND method.component_type = 'METHOD'
              AND sql.component_type LIKE 'SQL_%'
              AND api_url.del_yn = 'N'
              AND method.del_yn = 'N'
              AND sql.del_yn = 'N'
              AND r1.del_yn = 'N'
              AND r2.del_yn = 'N'
              AND (r3.rel_type = 'USE_TABLE' OR r3.rel_type IS NULL)
            GROUP BY jsp_file.file_name, api_url.component_name, class.class_name, 
                     method.component_name, xml_file.file_name, sql.component_name, sql.component_type
            LIMIT 10
        """
        
        print("\n1. API_URL 체인 쿼리 결과:")
        cursor.execute(api_chain_query)
        results = cursor.fetchall()
        
        if results:
            print(f"  총 {len(results)}개 결과 발견:")
            for row in results:
                chain_id, jsp_file, api_entry, virtual_endpoint, class_name, method_name, xml_file, query_id, query_type, related_tables = row
                print(f"    ID: {chain_id}")
                print(f"    JSP: {jsp_file}")
                print(f"    API_URL: {api_entry}")
                print(f"    Class: {class_name}")
                print(f"    Method: {method_name}")
                print(f"    XML: {xml_file}")
                print(f"    Query: {query_id} ({query_type})")
                print(f"    Tables: {related_tables}")
                print(f"    ---")
        else:
            print("  결과가 없습니다!")
        
        # 단계별 디버깅 쿼리들
        print("\n2. 단계별 디버깅:")
        
        # API_URL 컴포넌트 확인
        print("\n  2-1. API_URL 컴포넌트:")
        cursor.execute("""
            SELECT c.component_id, c.component_name, f.file_name, f.file_type
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            JOIN projects p ON c.project_id = p.project_id
            WHERE p.project_name = 'sampleSrc' 
              AND c.component_type = 'API_URL' 
              AND c.del_yn = 'N'
            LIMIT 5
        """)
        api_urls = cursor.fetchall()
        if api_urls:
            for comp_id, comp_name, file_name, file_type in api_urls:
                print(f"    API_URL: {comp_name} (file: {file_name}, type: {file_type})")
        else:
            print("    API_URL 컴포넌트가 없습니다!")
        
        # API_URL → METHOD 관계 확인
        print("\n  2-2. API_URL → METHOD 관계:")
        cursor.execute("""
            SELECT r.src_id, r.dst_id, r.rel_type,
                   src.component_name as api_url_name,
                   dst.component_name as method_name
            FROM relationships r
            JOIN components src ON r.src_id = src.component_id
            JOIN components dst ON r.dst_id = dst.component_id
            JOIN projects p ON src.project_id = p.project_id
            WHERE p.project_name = 'sampleSrc'
              AND src.component_type = 'API_URL'
              AND dst.component_type = 'METHOD'
              AND r.rel_type = 'CALL_METHOD'
              AND r.del_yn = 'N'
            LIMIT 5
        """)
        api_relations = cursor.fetchall()
        if api_relations:
            for src_id, dst_id, rel_type, api_url_name, method_name in api_relations:
                print(f"    {api_url_name} → {method_name} ({rel_type})")
        else:
            print("    API_URL → METHOD 관계가 없습니다!")
        
        # METHOD → QUERY 관계 확인
        print("\n  2-3. METHOD → QUERY 관계:")
        cursor.execute("""
            SELECT r.src_id, r.dst_id, r.rel_type,
                   src.component_name as method_name,
                   dst.component_name as query_name
            FROM relationships r
            JOIN components src ON r.src_id = src.component_id
            JOIN components dst ON r.dst_id = dst.component_id
            JOIN projects p ON src.project_id = p.project_id
            WHERE p.project_name = 'sampleSrc'
              AND src.component_type = 'METHOD'
              AND dst.component_type LIKE 'SQL_%'
              AND r.rel_type = 'CALL_QUERY'
              AND r.del_yn = 'N'
            LIMIT 5
        """)
        method_relations = cursor.fetchall()
        if method_relations:
            for src_id, dst_id, rel_type, method_name, query_name in method_relations:
                print(f"    {method_name} → {query_name} ({rel_type})")
        else:
            print("    METHOD → QUERY 관계가 없습니다!")
        
        conn.close()
        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    test_callchain_query()
