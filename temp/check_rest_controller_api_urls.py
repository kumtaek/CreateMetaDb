#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def check_rest_controller_api_urls():
    """@RestController의 API_URL 생성 상태 확인"""
    
    db_path = 'projects/sampleSrc/metadata.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== @RestController의 API_URL 생성 상태 확인 ===")
        
        # 1. ProxyController와 MicroserviceController 파일 찾기
        cursor.execute("""
            SELECT file_id, file_name, file_type 
            FROM files 
            WHERE file_name IN ('ProxyController.java', 'MicroserviceController.java')
              AND del_yn = 'N'
            ORDER BY file_name
        """)
        rest_controllers = cursor.fetchall()
        
        print(f"\n1. @RestController 파일들:")
        for file_id, file_name, file_type in rest_controllers:
            print(f"   - {file_name} (ID: {file_id}, Type: {file_type})")
        
        # 2. 각 파일에서 생성된 API_URL 컴포넌트들
        if rest_controllers:
            file_ids = [row[0] for row in rest_controllers]
            placeholders = ','.join(['?' for _ in file_ids])
            
            cursor.execute(f"""
                SELECT f.file_name, c.component_name, c.component_id, c.layer
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                WHERE c.file_id IN ({placeholders})
                  AND c.component_type = 'API_URL'
                  AND c.del_yn = 'N'
                ORDER BY f.file_name, c.component_name
            """, file_ids)
            api_urls = cursor.fetchall()
            
            print(f"\n2. 생성된 API_URL 컴포넌트들:")
            for file_name, api_url, comp_id, layer in api_urls:
                print(f"   - {file_name}: {api_url} (ID: {comp_id}, Layer: {layer})")
        
        # 3. 각 파일에서 생성된 METHOD 컴포넌트들
        if rest_controllers:
            cursor.execute(f"""
                SELECT f.file_name, c.component_name, c.component_id, c.layer
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                WHERE c.file_id IN ({placeholders})
                  AND c.component_type = 'METHOD'
                  AND c.del_yn = 'N'
                ORDER BY f.file_name, c.component_name
            """, file_ids)
            methods = cursor.fetchall()
            
            print(f"\n3. 생성된 METHOD 컴포넌트들:")
            for file_name, method_name, comp_id, layer in methods:
                print(f"   - {file_name}: {method_name} (ID: {comp_id}, Layer: {layer})")
        
        # 4. API_URL → METHOD 관계 확인
        if rest_controllers:
            cursor.execute(f"""
                SELECT api_url.component_name as api_endpoint,
                       method.component_name as method_name,
                       f.file_name as controller_file,
                       r.rel_type
                FROM components api_url
                JOIN relationships r ON api_url.component_id = r.src_id
                JOIN components method ON r.dst_id = method.component_id
                JOIN files f ON api_url.file_id = f.file_id
                WHERE api_url.file_id IN ({placeholders})
                  AND api_url.component_type = 'API_URL'
                  AND method.component_type = 'METHOD'
                  AND r.rel_type = 'CALL_METHOD'
                  AND api_url.del_yn = 'N'
                  AND method.del_yn = 'N'
                  AND r.del_yn = 'N'
                ORDER BY f.file_name, api_url.component_name
            """, file_ids)
            api_method_relationships = cursor.fetchall()
            
            print(f"\n4. API_URL → METHOD 관계들:")
            for api_endpoint, method_name, controller_file, rel_type in api_method_relationships:
                print(f"   - {controller_file}: {api_endpoint} --[{rel_type}]--> {method_name}")
        
        # 5. 연결되지 않은 API_URL들
        if rest_controllers:
            cursor.execute(f"""
                SELECT api_url.component_name as api_endpoint,
                       f.file_name as controller_file,
                       api_url.component_id
                FROM components api_url
                JOIN files f ON api_url.file_id = f.file_id
                LEFT JOIN relationships r ON api_url.component_id = r.src_id 
                    AND r.rel_type = 'CALL_METHOD' 
                    AND r.del_yn = 'N'
                WHERE api_url.file_id IN ({placeholders})
                  AND api_url.component_type = 'API_URL'
                  AND api_url.del_yn = 'N'
                  AND r.src_id IS NULL
                ORDER BY f.file_name, api_url.component_name
            """, file_ids)
            unconnected_api_urls = cursor.fetchall()
            
            print(f"\n5. 연결되지 않은 API_URL들:")
            for api_endpoint, controller_file, comp_id in unconnected_api_urls:
                print(f"   - {controller_file}: {api_endpoint} (ID: {comp_id})")
        
        # 6. 예상되는 API_URL 목록과 실제 비교
        expected_api_urls = {
            'ProxyController.java': [
                '/api/users:GET',
                '/api/users:POST', 
                '/api/products:GET',
                '/api/orders:GET',
                '/api/payment:POST'
            ],
            'MicroserviceController.java': [
                '/api/user-profile:GET',
                '/api/order-details:GET',
                '/api/dashboard:GET',
                '/api/search:GET',
                '/api/notify:POST'
            ]
        }
        
        print(f"\n6. 예상 vs 실제 API_URL 비교:")
        actual_api_urls = {}
        for file_name, api_url, comp_id, layer in api_urls:
            if file_name not in actual_api_urls:
                actual_api_urls[file_name] = []
            actual_api_urls[file_name].append(api_url)
        
        for file_name, expected_list in expected_api_urls.items():
            print(f"\n   {file_name}:")
            actual_list = actual_api_urls.get(file_name, [])
            
            for expected_url in expected_list:
                if expected_url in actual_list:
                    print(f"     ✓ {expected_url} - 생성됨")
                else:
                    print(f"     ✗ {expected_url} - 생성 안됨")
            
            # 추가로 생성된 것들
            for actual_url in actual_list:
                if actual_url not in expected_list:
                    print(f"     + {actual_url} - 추가 생성됨")
        
        conn.close()
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_rest_controller_api_urls()
