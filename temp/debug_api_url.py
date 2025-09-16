#!/usr/bin/env python3
"""
API_URL 컴포넌트와 관계 디버깅 스크립트
"""

import sqlite3
import os

def debug_api_url_structure():
    """API_URL 구조 디버깅"""
    try:
        db_path = "projects/sampleSrc/metadata.db"
        if not os.path.exists(db_path):
            print(f"데이터베이스 파일이 존재하지 않습니다: {db_path}")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== API_URL 구조 디버깅 ===")
        
        # 1. API_URL 컴포넌트 확인
        print("\n1. API_URL 컴포넌트:")
        cursor.execute("""
            SELECT component_id, component_name, file_id, layer
            FROM components 
            WHERE project_id = 1 AND del_yn = 'N' AND component_type = 'API_URL'
            ORDER BY component_id
            LIMIT 10
        """)
        
        api_urls = cursor.fetchall()
        if api_urls:
            for comp_id, comp_name, file_id, layer in api_urls:
                print(f"  ID: {comp_id}, Name: {comp_name}, File_ID: {file_id}, Layer: {layer}")
        else:
            print("  API_URL 컴포넌트가 없습니다!")
        
        # 2. API_URL → METHOD 관계 확인
        print(f"\n2. API_URL → METHOD 관계:")
        cursor.execute("""
            SELECT r.src_id, r.dst_id, r.rel_type,
                   src.component_name as api_url_name,
                   dst.component_name as method_name
            FROM relationships r
            JOIN components src ON r.src_id = src.component_id
            JOIN components dst ON r.dst_id = dst.component_id
            WHERE src.component_type = 'API_URL' 
              AND dst.component_type = 'METHOD'
              AND r.del_yn = 'N'
            ORDER BY r.src_id
            LIMIT 10
        """)
        
        api_relations = cursor.fetchall()
        if api_relations:
            for src_id, dst_id, rel_type, api_url_name, method_name in api_relations:
                print(f"  {api_url_name} → {method_name} ({rel_type})")
        else:
            print("  API_URL → METHOD 관계가 없습니다!")
        
        # 3. JSP 파일과 API_URL 연결 확인
        print(f"\n3. JSP 파일과 API_URL 연결:")
        cursor.execute("""
            SELECT f.file_name, f.file_id,
                   c.component_id, c.component_name, c.component_type
            FROM files f
            LEFT JOIN components c ON f.file_id = c.file_id
            WHERE f.project_id = 1 AND f.file_type = 'JSP' AND f.del_yn = 'N'
            ORDER BY f.file_name
            LIMIT 5
        """)
        
        jsp_connections = cursor.fetchall()
        if jsp_connections:
            for file_name, file_id, comp_id, comp_name, comp_type in jsp_connections:
                print(f"  JSP: {file_name} (ID: {file_id}) → {comp_type}: {comp_name}")
        else:
            print("  JSP 파일이 없습니다!")
        
        # 4. CallChain 리포트용 쿼리 확인
        print(f"\n4. CallChain 리포트용 쿼리 테스트:")
        cursor.execute("""
            SELECT r.relationship_id,
                   frontend.component_name as frontend_name,
                   api.component_name as api_url_name,
                   method.component_name as method_name,
                   xml.component_name as xml_name,
                   query.component_name as query_name
            FROM relationships r
            JOIN components method ON r.src_id = method.component_id AND method.component_type = 'METHOD'
            LEFT JOIN relationships r2 ON r2.src_id = r.src_id AND r2.rel_type = 'CALL_QUERY'
            LEFT JOIN components query ON r2.dst_id = query.component_id
            LEFT JOIN components xml ON query.file_id = xml.file_id AND xml.component_type = 'XML'
            LEFT JOIN relationships r3 ON r3.dst_id = r.src_id AND r3.rel_type = 'CALL_METHOD'
            LEFT JOIN components api ON r3.src_id = api.component_id AND api.component_type = 'API_URL'
            LEFT JOIN components frontend ON api.file_id = frontend.file_id AND frontend.component_type = 'JSP'
            WHERE r.del_yn = 'N'
            ORDER BY r.relationship_id
            LIMIT 5
        """)
        
        callchain_results = cursor.fetchall()
        if callchain_results:
            for rel_id, frontend, api_url, method, xml, query in callchain_results:
                print(f"  ID: {rel_id}, Frontend: {frontend}, API_URL: {api_url}, Method: {method}, XML: {xml}, Query: {query}")
        else:
            print("  CallChain 결과가 없습니다!")
        
        conn.close()
        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    debug_api_url_structure()
