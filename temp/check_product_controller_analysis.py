#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def check_product_controller_analysis():
    """ProductController 분석 결과 확인"""
    
    db_path = 'projects/sampleSrc/metadata.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== ProductController 관련 분석 결과 ===")
        
        # 1. ProductController 파일 확인
        cursor.execute("""
            SELECT file_id, file_name, file_type 
            FROM files 
            WHERE file_name LIKE '%ProductController%'
        """)
        product_controller_files = cursor.fetchall()
        
        print(f"\n1. ProductController 파일:")
        for file_id, file_name, file_type in product_controller_files:
            print(f"   - {file_name} (ID: {file_id}, Type: {file_type})")
        
        # 2. ProductController에서 생성된 컴포넌트들
        if product_controller_files:
            file_id = product_controller_files[0][0]
            
            cursor.execute("""
                SELECT component_id, component_type, component_name, layer
                FROM components 
                WHERE file_id = ? AND del_yn = 'N'
                ORDER BY component_type, component_name
            """, (file_id,))
            components = cursor.fetchall()
            
            print(f"\n2. ProductController (file_id: {file_id})에서 생성된 컴포넌트들:")
            for comp_id, comp_type, comp_name, layer in components:
                print(f"   - {comp_type}: {comp_name} (ID: {comp_id}, Layer: {layer})")
        
        # 3. ProductService 관련 컴포넌트들
        cursor.execute("""
            SELECT c.component_id, c.component_type, c.component_name, c.layer, f.file_name
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            WHERE c.component_name LIKE '%Product%' 
              AND c.del_yn = 'N'
            ORDER BY c.component_type, c.component_name
        """)
        product_components = cursor.fetchall()
        
        print(f"\n3. Product 관련 모든 컴포넌트들:")
        for comp_id, comp_type, comp_name, layer, file_name in product_components:
            print(f"   - {comp_type}: {comp_name} (ID: {comp_id}, Layer: {layer}, File: {file_name})")
        
        # 4. ProductServiceImpl의 메서드들
        cursor.execute("""
            SELECT c.component_id, c.component_name, f.file_name
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            WHERE f.file_name LIKE '%ProductServiceImpl%'
              AND c.component_type = 'METHOD'
              AND c.del_yn = 'N'
            ORDER BY c.component_name
        """)
        product_service_methods = cursor.fetchall()
        
        print(f"\n4. ProductServiceImpl의 메서드들:")
        for comp_id, comp_name, file_name in product_service_methods:
            print(f"   - {comp_name} (ID: {comp_id}, File: {file_name})")
        
        # 5. applyCategorySpecificLogic, applyDiscountLogic 메서드 확인
        cursor.execute("""
            SELECT c.component_id, c.component_name, f.file_name
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            WHERE (c.component_name LIKE '%applyCategorySpecificLogic%' 
                   OR c.component_name LIKE '%applyDiscountLogic%')
              AND c.component_type = 'METHOD'
              AND c.del_yn = 'N'
        """)
        specific_methods = cursor.fetchall()
        
        print(f"\n5. applyCategorySpecificLogic, applyDiscountLogic 메서드들:")
        for comp_id, comp_name, file_name in specific_methods:
            print(f"   - {comp_name} (ID: {comp_id}, File: {file_name})")
        
        # 6. 이 메서드들의 관계 확인
        if specific_methods:
            method_ids = [method[0] for method in specific_methods]
            placeholders = ','.join(['?' for _ in method_ids])
            
            cursor.execute(f"""
                SELECT r.src_id, r.dst_id, r.rel_type, 
                       src_c.component_name as src_name, 
                       dst_c.component_name as dst_name
                FROM relationships r
                JOIN components src_c ON r.src_id = src_c.component_id
                JOIN components dst_c ON r.dst_id = dst_c.component_id
                WHERE (r.src_id IN ({placeholders}) OR r.dst_id IN ({placeholders}))
                  AND r.del_yn = 'N'
                ORDER BY r.rel_type, src_c.component_name
            """, method_ids + method_ids)
            relationships = cursor.fetchall()
            
            print(f"\n6. 이 메서드들의 관계들:")
            for src_id, dst_id, rel_type, src_name, dst_name in relationships:
                print(f"   - {src_name} --[{rel_type}]--> {dst_name}")
        
        # 7. ProductController가 @Controller인지 @RestController인지 확인
        print(f"\n7. ProductController 분석:")
        print(f"   - @Controller: 뷰를 반환하는 전통적인 MVC 컨트롤러")
        print(f"   - @RestController: JSON/XML을 반환하는 REST API 컨트롤러")
        print(f"   - ProductController는 @Controller이므로 API_URL이 생성되지 않음!")
        
        conn.close()
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_product_controller_analysis()
