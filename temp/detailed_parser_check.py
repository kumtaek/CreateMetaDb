#!/usr/bin/env python3
"""
상세 파서 점검 스크립트 - 개별 쿼리별로 파서 동작 확인
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser.sql_parser import SqlParser
from util import debug, info

def detailed_parser_check():
    """상세 파서 점검"""
    
    # SQL 파서 초기화
    parser = SqlParser()
    
    # 개별 테스트 케이스들
    test_cases = [
        {
            "name": "selectDashboardData - 서브쿼리 케이스",
            "sql": """
            SELECT 
                (SELECT COUNT(*) FROM users WHERE del_yn = 'N') as total_users,
                (SELECT COUNT(*) FROM products WHERE del_yn = 'N' AND status = 'ACTIVE') as total_products,
                (SELECT COUNT(*) FROM orders WHERE del_yn = 'N') as total_orders,
                (SELECT SUM(total_amount) FROM orders WHERE del_yn = 'N' AND status = 'COMPLETED') as total_revenue,
                (SELECT COUNT(*) FROM notifications WHERE del_yn = 'N' AND is_read = 'N') as unread_notifications,
                (SELECT COUNT(*) FROM recommendations WHERE del_yn = 'N' AND status = 'ACTIVE') as active_recommendations
            """
        },
        {
            "name": "selectOrdersV2 - 동적 SQL 케이스",
            "sql": """
            SELECT o.order_id, o.user_id, o.order_date, o.total_amount, o.status, o.created_at,
                   u.username, u.email, COUNT(oi.order_item_id) as item_count
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            LEFT JOIN order_items oi ON o.order_id = oi.order_id AND oi.del_yn = 'N'
            WHERE o.del_yn = 'N'
            <if test="status != null and status != ''">
                AND o.status = #{status}
            </if>
            <if test="dateFrom != null and dateFrom != ''">
                AND o.order_date >= #{dateFrom}
            </if>
            <if test="dateTo != null and dateTo != ''">
                AND o.order_date <= #{dateTo}
            </if>
            GROUP BY o.order_id
            ORDER BY o.order_date DESC
            """
        },
        {
            "name": "insertUserToV1 - INSERT 케이스",
            "sql": """
            INSERT INTO users_v1 (
                username, email, status, created_at, del_yn
            ) VALUES (
                #{userData.username}, #{userData.email}, #{userData.status}, NOW(), 'N'
            )
            """
        }
    ]
    
    print("=" * 80)
    print("상세 파서 점검 결과")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 60)
        
        # 파서로 테이블명 추출
        try:
            extracted_tables = parser.extract_table_names(test_case['sql'])
            
            print(f"추출된 테이블명: {list(extracted_tables)}")
            print(f"테이블 개수: {len(extracted_tables)}")
            
            # 각 테이블명이 유효한지 확인
            for table in extracted_tables:
                print(f"  - {table}: 유효함")
            
            if len(extracted_tables) == 0:
                print("[WARN] 테이블명이 추출되지 않음")
                
                # 전처리 과정 확인
                processed_sql = parser._preprocess_sql(test_case['sql'])
                print(f"전처리된 SQL (처음 200자): {processed_sql[:200]}...")
                
                # UNION 분할 확인
                union_queries = parser._split_union_queries(processed_sql)
                print(f"UNION 분할 결과: {len(union_queries)}개 쿼리")
                
                # 서브쿼리 추출 확인
                subquery_tables = parser._extract_from_subqueries(processed_sql)
                print(f"서브쿼리에서 추출된 테이블: {list(subquery_tables)}")
                
                # 메인 쿼리 추출 확인
                main_tables = parser._extract_from_main_query(processed_sql)
                print(f"메인 쿼리에서 추출된 테이블: {list(main_tables)}")
                
        except Exception as e:
            print(f"[ERROR] 파서 실행 오류: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    detailed_parser_check()
