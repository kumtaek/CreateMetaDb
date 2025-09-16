#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def check_java_frontend_connections():
    """Java 프론트엔드 파일들의 연결 상태 확인"""
    
    db_path = 'projects/sampleSrc/metadata.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== Java 프론트엔드 파일들의 연결 상태 분석 ===")
        
        # 1. Java 파일 중 API_URL과 연결된 것들 찾기
        cursor.execute("""
            SELECT DISTINCT f.file_name, f.file_id, api_url.component_name as api_endpoint
            FROM files f
            JOIN components api_url ON f.file_id = api_url.file_id
            WHERE f.file_type = 'JAVA' 
              AND api_url.component_type = 'API_URL'
              AND api_url.del_yn = 'N'
              AND f.del_yn = 'N'
            ORDER BY f.file_name, api_url.component_name
        """)
        java_api_connections = cursor.fetchall()
        
        print(f"\n1. Java 파일 중 API_URL과 연결된 것들:")
        for file_name, file_id, api_endpoint in java_api_connections:
            print(f"   - {file_name} (ID: {file_id}) → {api_endpoint}")
        
        # 2. 각 Java 파일에서 생성된 METHOD 컴포넌트들
        if java_api_connections:
            java_file_ids = [row[1] for row in java_api_connections]
            placeholders = ','.join(['?' for _ in java_file_ids])
            
            cursor.execute(f"""
                SELECT f.file_name, c.component_name, c.component_id, c.layer
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                WHERE c.file_id IN ({placeholders})
                  AND c.component_type = 'METHOD'
                  AND c.del_yn = 'N'
                  AND f.del_yn = 'N'
                ORDER BY f.file_name, c.component_name
            """, java_file_ids)
            java_methods = cursor.fetchall()
            
            print(f"\n2. 이 Java 파일들의 METHOD 컴포넌트들:")
            for file_name, method_name, method_id, layer in java_methods:
                print(f"   - {file_name}: {method_name} (ID: {method_id}, Layer: {layer})")
        
        # 3. API_URL → METHOD 관계 확인
        if java_api_connections:
            cursor.execute(f"""
                SELECT api_url.component_name as api_endpoint,
                       method.component_name as method_name,
                       f.file_name as java_file,
                       r.rel_type
                FROM components api_url
                JOIN relationships r ON api_url.component_id = r.src_id
                JOIN components method ON r.dst_id = method.component_id
                JOIN files f ON api_url.file_id = f.file_id
                WHERE api_url.component_type = 'API_URL'
                  AND method.component_type = 'METHOD'
                  AND r.rel_type = 'CALL_METHOD'
                  AND api_url.del_yn = 'N'
                  AND method.del_yn = 'N'
                  AND r.del_yn = 'N'
                  AND f.del_yn = 'N'
                ORDER BY f.file_name, api_url.component_name
            """)
            api_method_relationships = cursor.fetchall()
            
            print(f"\n3. API_URL → METHOD 관계들:")
            for api_endpoint, method_name, java_file, rel_type in api_method_relationships:
                print(f"   - {java_file}: {api_endpoint} --[{rel_type}]--> {method_name}")
        
        # 4. 끊어진 API_URL들 (METHOD로 연결되지 않은 것들)
        cursor.execute("""
            SELECT api_url.component_name as api_endpoint,
                   f.file_name as java_file,
                   f.file_id
            FROM components api_url
            JOIN files f ON api_url.file_id = f.file_id
            LEFT JOIN relationships r ON api_url.component_id = r.src_id 
                AND r.rel_type = 'CALL_METHOD' 
                AND r.del_yn = 'N'
            WHERE api_url.component_type = 'API_URL'
              AND api_url.del_yn = 'N'
              AND f.del_yn = 'N'
              AND f.file_type = 'JAVA'
              AND r.src_id IS NULL
            ORDER BY f.file_name, api_url.component_name
        """)
        disconnected_api_urls = cursor.fetchall()
        
        print(f"\n4. 끊어진 API_URL들 (METHOD로 연결되지 않은 Java 파일의 API_URL):")
        for api_endpoint, java_file, file_id in disconnected_api_urls:
            print(f"   - {java_file}: {api_endpoint} (file_id: {file_id})")
        
        # 5. ProxyController와 MicroserviceController 상세 분석
        print(f"\n5. ProxyController와 MicroserviceController 상세 분석:")
        
        # ProxyController 분석
        cursor.execute("""
            SELECT f.file_id, f.file_name
            FROM files f
            WHERE f.file_name LIKE '%ProxyController%'
              AND f.del_yn = 'N'
        """)
        proxy_controller = cursor.fetchone()
        
        if proxy_controller:
            proxy_file_id, proxy_file_name = proxy_controller
            print(f"\n   ProxyController (ID: {proxy_file_id}):")
            
            # ProxyController의 모든 컴포넌트
            cursor.execute("""
                SELECT c.component_type, c.component_name, c.component_id
                FROM components c
                WHERE c.file_id = ? AND c.del_yn = 'N'
                ORDER BY c.component_type, c.component_name
            """, (proxy_file_id,))
            proxy_components = cursor.fetchall()
            
            for comp_type, comp_name, comp_id in proxy_components:
                print(f"     - {comp_type}: {comp_name} (ID: {comp_id})")
            
            # ProxyController의 관계들
            cursor.execute("""
                SELECT r.rel_type, 
                       src_c.component_name as src_name,
                       dst_c.component_name as dst_name
                FROM relationships r
                JOIN components src_c ON r.src_id = src_c.component_id
                JOIN components dst_c ON r.dst_id = dst_c.component_id
                WHERE (src_c.file_id = ? OR dst_c.file_id = ?)
                  AND r.del_yn = 'N'
                ORDER BY r.rel_type
            """, (proxy_file_id, proxy_file_id))
            proxy_relationships = cursor.fetchall()
            
            print(f"     관계들:")
            for rel_type, src_name, dst_name in proxy_relationships:
                print(f"       - {src_name} --[{rel_type}]--> {dst_name}")
        
        # MicroserviceController 분석
        cursor.execute("""
            SELECT f.file_id, f.file_name
            FROM files f
            WHERE f.file_name LIKE '%MicroserviceController%'
              AND f.del_yn = 'N'
        """)
        microservice_controller = cursor.fetchone()
        
        if microservice_controller:
            microservice_file_id, microservice_file_name = microservice_controller
            print(f"\n   MicroserviceController (ID: {microservice_file_id}):")
            
            # MicroserviceController의 모든 컴포넌트
            cursor.execute("""
                SELECT c.component_type, c.component_name, c.component_id
                FROM components c
                WHERE c.file_id = ? AND c.del_yn = 'N'
                ORDER BY c.component_type, c.component_name
            """, (microservice_file_id,))
            microservice_components = cursor.fetchall()
            
            for comp_type, comp_name, comp_id in microservice_components:
                print(f"     - {comp_type}: {comp_name} (ID: {comp_id})")
            
            # MicroserviceController의 관계들
            cursor.execute("""
                SELECT r.rel_type, 
                       src_c.component_name as src_name,
                       dst_c.component_name as dst_name
                FROM relationships r
                JOIN components src_c ON r.src_id = src_c.component_id
                JOIN components dst_c ON r.dst_id = dst_c.component_id
                WHERE (src_c.file_id = ? OR dst_c.file_id = ?)
                  AND r.del_yn = 'N'
                ORDER BY r.rel_type
            """, (microservice_file_id, microservice_file_id))
            microservice_relationships = cursor.fetchall()
            
            print(f"     관계들:")
            for rel_type, src_name, dst_name in microservice_relationships:
                print(f"       - {src_name} --[{rel_type}]--> {dst_name}")
        
        # 6. 결론
        print(f"\n6. 결론:")
        print(f"   - Java 파일이 프론트엔드로 나타나는 경우는 @RestController인 경우")
        print(f"   - @RestController는 API_URL 컴포넌트를 생성함")
        print(f"   - 이 API_URL들은 METHOD와 연결되어야 완전한 체인이 됨")
        print(f"   - 끊어진 API_URL들은 METHOD로 연결되지 않은 것들")
        
        conn.close()
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_java_frontend_connections()
