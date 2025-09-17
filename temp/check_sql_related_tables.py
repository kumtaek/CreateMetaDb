#!/usr/bin/env python3
"""
SQL 컴포넌트들의 관련 테이블 확인
"""

import sqlite3

def check_sql_related_tables():
    """SQL 컴포넌트들의 관련 테이블 확인"""
    
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    # SQL 타입 컴포넌트들
    target_queries = ['selectDashboardData', 'insertUserToV1']
    
    print("SQL 컴포넌트들의 관련 테이블:")
    print("=" * 60)
    
    for query_name in target_queries:
        print(f"\n{query_name}:")
        
        # SQL 컴포넌트 정보 조회
        cursor.execute("""
            SELECT c.component_id, c.component_name, c.component_type, f.file_name
            FROM components c 
            LEFT JOIN files f ON c.file_id = f.file_id
            WHERE c.component_name = ? AND c.component_type LIKE 'SQL_%'
        """, (query_name,))
        
        component_result = cursor.fetchone()
        
        if component_result:
            component_id, component_name, component_type, file_name = component_result
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
        else:
            print("  SQL 컴포넌트를 찾을 수 없음")
    
    conn.close()

if __name__ == "__main__":
    check_sql_related_tables()
