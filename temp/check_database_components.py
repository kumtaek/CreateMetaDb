#!/usr/bin/env python3
"""
데이터베이스 컴포넌트 확인 스크립트
"""

import sqlite3

def check_database_components():
    """데이터베이스 컴포넌트 확인"""
    
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    # 파싱불가쿼리.md에 있는 쿼리들
    target_queries = ['selectDashboardData', 'selectGlobalSearch', 'selectOrdersV2', 'insertUserToV1']
    
    print("데이터베이스 컴포넌트 확인:")
    print("=" * 60)
    
    for query_name in target_queries:
        print(f"\n{query_name}:")
        
        # 컴포넌트 정보 조회
        cursor.execute("""
            SELECT c.component_id, c.component_name, c.component_type, c.file_id, f.file_name
            FROM components c 
            LEFT JOIN files f ON c.file_id = f.file_id
            WHERE c.component_name = ?
        """, (query_name,))
        
        component_result = cursor.fetchone()
        
        if component_result:
            component_id, component_name, component_type, file_id, file_name = component_result
            print(f"  컴포넌트 ID: {component_id}")
            print(f"  컴포넌트 타입: {component_type}")
            print(f"  파일: {file_name}")
            
            # 관련 테이블 관계 조회
            cursor.execute("""
                SELECT r.rel_type, comp.component_name as related_table
                FROM relationships r 
                LEFT JOIN components comp ON r.dst_id = comp.component_id 
                WHERE r.src_id = ? AND r.rel_type = 'USE_TABLE'
            """, (component_id,))
            
            relationships = cursor.fetchall()
            
            if relationships:
                print(f"  관련 테이블 ({len(relationships)}개):")
                for rel_type, related_table in relationships:
                    if related_table:
                        print(f"    - {related_table}")
            else:
                print("  관련 테이블: 없음")
                
                # 테이블 컴포넌트가 존재하는지 확인
                cursor.execute("""
                    SELECT component_name FROM components 
                    WHERE component_type = 'TABLE' 
                    AND component_name IN ('USERS', 'PRODUCTS', 'ORDERS', 'NOTIFICATIONS', 'RECOMMENDATIONS', 'ORDER_ITEMS', 'USERS_V1')
                """)
                
                available_tables = cursor.fetchall()
                print(f"  사용 가능한 테이블들: {[row[0] for row in available_tables]}")
        else:
            print("  컴포넌트를 찾을 수 없음")
    
    conn.close()

if __name__ == "__main__":
    check_database_components()
