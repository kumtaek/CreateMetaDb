#!/usr/bin/env python3
"""
파싱불가쿼리.md에 있는 쿼리들의 개선 상태 점검 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser.sql_parser import SqlParser
from util import debug, info

def test_parser_improvement():
    """파서 개선 상태 테스트"""
    
    # SQL 파서 초기화
    parser = SqlParser()
    
    # 테스트 케이스들 (파싱불가쿼리.md에서 추출)
    test_cases = [
        {
            "name": "1. 서브쿼리 케이스 - selectDashboardData",
            "sql": """
            SELECT 
                (SELECT COUNT(*) FROM users WHERE del_yn = 'N') as total_users,
                (SELECT COUNT(*) FROM products WHERE del_yn = 'N' AND status = 'ACTIVE') as total_products,
                (SELECT COUNT(*) FROM orders WHERE del_yn = 'N') as total_orders,
                (SELECT SUM(total_amount) FROM orders WHERE del_yn = 'N' AND status = 'COMPLETED') as total_revenue,
                (SELECT COUNT(*) FROM notifications WHERE del_yn = 'N' AND is_read = 'N') as unread_notifications,
                (SELECT COUNT(*) FROM recommendations WHERE del_yn = 'N' AND status = 'ACTIVE') as active_recommendations
            """,
            "expected_tables": ["users", "products", "orders", "notifications", "recommendations"],
            "previous_result": ["USERS WHERE", "PRODUCTS WHERE", "ORDERS WHERE", "ORDERS WHERE", "NOTIFICATIONS WHERE", "RECOMMENDATIONS WHERE"]
        },
        {
            "name": "2. UNION 케이스 - selectGlobalSearch",
            "sql": """
            SELECT 'user' as type, user_id as id, username as name, email as description, created_at
            FROM users
            WHERE (username LIKE CONCAT('%', #{query}, '%') OR email LIKE CONCAT('%', #{query}, '%'))
              AND del_yn = 'N'

            UNION ALL

            SELECT 'product' as type, product_id as id, product_name as name, description, created_at
            FROM products
            WHERE (product_name LIKE CONCAT('%', #{query}, '%') OR description LIKE CONCAT('%', #{query}, '%'))
              AND del_yn = 'N'
              AND status = 'ACTIVE'

            UNION ALL

            SELECT 'order' as type, order_id as id, CONCAT('Order #', order_id) as name, 
                   CONCAT('Total: $', total_amount) as description, order_date as created_at
            FROM orders
            WHERE order_id LIKE CONCAT('%', #{query}, '%')
              AND del_yn = 'N'

            ORDER BY created_at DESC
            LIMIT 50
            """,
            "expected_tables": ["users", "products", "orders"],
            "previous_result": ["USERS\n        WHERE", "PRODUCTS\n        WHERE", "ORDERS\n        WHERE"]
        },
        {
            "name": "3. 동적 SQL 케이스 - selectOrdersV2",
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
            """,
            "expected_tables": ["orders", "users", "order_items"],
            "previous_result": ["ORDERS O", "USERS U", "ORDER_ITEMS OI"]
        },
        {
            "name": "4. INSERT 케이스 - insertUserToV1",
            "sql": """
            INSERT INTO users_v1 (
                username, email, status, created_at, del_yn
            ) VALUES (
                #{userData.username}, #{userData.email}, #{userData.status}, NOW(), 'N'
            )
            """,
            "expected_tables": ["users_v1"],
            "previous_result": ["USERS_V1"]
        }
    ]
    
    print("=" * 80)
    print("파싱불가쿼리.md 개선 상태 점검 결과")
    print("=" * 80)
    
    total_cases = len(test_cases)
    improved_cases = 0
    perfect_cases = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 60)
        
        # 파서로 테이블명 추출
        try:
            extracted_tables = parser.extract_table_names(test_case['sql'])
            extracted_tables_lower = {table.lower() for table in extracted_tables}
            expected_tables_lower = {table.lower() for table in test_case['expected_tables']}
            
            print(f"기존 파서 결과: {test_case['previous_result']}")
            print(f"개선된 파서 결과: {list(extracted_tables)}")
            print(f"예상 결과: {test_case['expected_tables']}")
            
            # 개선 상태 평가
            if extracted_tables_lower == expected_tables_lower:
                print("[OK] 완벽 매칭 - 모든 테이블명이 정확히 추출됨")
                perfect_cases += 1
                improved_cases += 1
            elif extracted_tables_lower.issubset(expected_tables_lower) and len(extracted_tables_lower) > 0:
                print("[OK] 부분 개선 - 일부 테이블명이 정확히 추출됨")
                improved_cases += 1
            elif len(extracted_tables_lower) > 0:
                print("[WARN] 부분 개선 - 테이블명이 추출되었지만 정확도 개선 필요")
                improved_cases += 1
            else:
                print("[FAIL] 개선 없음 - 여전히 테이블명 추출 실패")
            
            # 누락된 테이블 확인
            missing_tables = expected_tables_lower - extracted_tables_lower
            if missing_tables:
                print(f"누락된 테이블: {list(missing_tables)}")
            
            # 잘못 추출된 테이블 확인
            extra_tables = extracted_tables_lower - expected_tables_lower
            if extra_tables:
                print(f"잘못 추출된 테이블: {list(extra_tables)}")
                
        except Exception as e:
            print(f"[ERROR] 파서 실행 오류: {str(e)}")
    
    # 전체 결과 요약
    print("\n" + "=" * 80)
    print("전체 개선 상태 요약")
    print("=" * 80)
    print(f"총 테스트 케이스: {total_cases}")
    print(f"개선된 케이스: {improved_cases} ({improved_cases/total_cases*100:.1f}%)")
    print(f"완벽 매칭 케이스: {perfect_cases} ({perfect_cases/total_cases*100:.1f}%)")
    print(f"개선 필요 케이스: {total_cases - improved_cases} ({(total_cases - improved_cases)/total_cases*100:.1f}%)")
    
    if improved_cases == total_cases:
        print("\n[SUCCESS] 모든 케이스에서 개선됨!")
    elif improved_cases > total_cases // 2:
        print("\n[GOOD] 대부분의 케이스에서 개선됨!")
    else:
        print("\n[WARN] 추가 개선이 필요합니다.")

if __name__ == "__main__":
    test_parser_improvement()
