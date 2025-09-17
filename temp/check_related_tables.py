#!/usr/bin/env python3
"""
파싱불가쿼리.md 쿼리들의 관련 테이블 확인
"""

import sqlite3

def check_related_tables():
    """관련 테이블 확인"""
    
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    # 파싱불가쿼리.md에 있는 쿼리들
    target_queries = ['selectDashboardData', 'selectGlobalSearch', 'selectOrdersV2', 'insertUserToV1']
    
    print("파싱불가쿼리.md 쿼리들의 관련 테이블:")
    print("=" * 60)
    
    for query_name in target_queries:
        print(f"\n{query_name}:")
        
        # 해당 쿼리의 관련 테이블 조회
        cursor.execute("""
            SELECT comp.component_name as related_table
            FROM components c 
            LEFT JOIN relationships r ON c.component_id = r.src_id 
                AND r.rel_type = 'USE_TABLE'
            LEFT JOIN components comp ON r.dst_id = comp.component_id 
            WHERE c.component_name = ?
        """, (query_name,))
        
        results = cursor.fetchall()
        
        if results and results[0][0]:
            for row in results:
                if row[0]:  # None이 아닌 경우만 출력
                    print(f"  - {row[0]}")
        else:
            print("  - 관련 테이블 없음")
    
    conn.close()

if __name__ == "__main__":
    check_related_tables()
