#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os
import re
import gzip

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def analyze_parsing_cases():
    """파싱 불가능 사례들을 자동으로 분석"""
    
    print("=== 파싱 불가능 사례 분석 시작 ===")
    
    db_path = 'projects/sampleSrc/metadata.db'
    sql_content_db_path = 'projects/sampleSrc/SqlContent.db'
    
    try:
        # 1. 서브쿼리 케이스 분석
        print(f"\n1. 서브쿼리 케이스 분석:")
        print(f"   소스 파일: MicroserviceMapper.xml")
        print(f"   쿼리 ID: selectDashboardData")
        print(f"   라인: 59-67")
        
        subquery_example = """
        SELECT 
            (SELECT COUNT(*) FROM users WHERE del_yn = 'N') as total_users,
            (SELECT COUNT(*) FROM products WHERE del_yn = 'N' AND status = 'ACTIVE') as total_products,
            (SELECT COUNT(*) FROM orders WHERE del_yn = 'N') as total_orders,
            (SELECT SUM(total_amount) FROM orders WHERE del_yn = 'N' AND status = 'COMPLETED') as total_revenue,
            (SELECT COUNT(*) FROM notifications WHERE del_yn = 'N' AND is_read = 'N') as unread_notifications,
            (SELECT COUNT(*) FROM recommendations WHERE del_yn = 'N' AND status = 'ACTIVE') as active_recommendations
        """
        
        # 파서 시뮬레이션
        sql_upper = subquery_example.upper().strip()
        from_pattern = r'\bFROM\s+([A-Z_][A-Z0-9_]*(?:\s+[A-Z_][A-Z0-9_]*)?)'
        from_matches = re.findall(from_pattern, sql_upper)
        
        print(f"   파서 인식 결과: {from_matches}")
        print(f"   실제 테이블명: ['USERS', 'PRODUCTS', 'ORDERS', 'NOTIFICATIONS', 'RECOMMENDATIONS']")
        print(f"   파서 한계: 서브쿼리 내부 테이블명 인식 불가")
        
        # 2. UNION 케이스 분석
        print(f"\n2. UNION 케이스 분석:")
        print(f"   소스 파일: MicroserviceMapper.xml")
        print(f"   쿼리 ID: selectGlobalSearch")
        print(f"   라인: 70-108")
        
        union_example = """
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
        """
        
        # 파서 시뮬레이션
        sql_upper = union_example.upper().strip()
        from_pattern = r'\bFROM\s+([A-Z_][A-Z0-9_]*(?:\s+[A-Z_][A-Z0-9_]*)?)'
        from_matches = re.findall(from_pattern, sql_upper)
        
        print(f"   파서 인식 결과: {from_matches}")
        print(f"   실제 테이블명: ['USERS', 'PRODUCTS', 'ORDERS']")
        print(f"   파서 한계: UNION의 각 쿼리에서 테이블명을 개별적으로 인식해야 함")
        
        # 3. 동적 SQL 케이스 분석
        print(f"\n3. 동적 SQL 케이스 분석:")
        print(f"   소스 파일: VersionedMapper.xml")
        print(f"   쿼리 ID: selectOrdersV2")
        print(f"   라인: 90-116")
        
        dynamic_example = """
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
        
        # 파서 시뮬레이션 (동적 부분 제거)
        clean_sql = re.sub(r'<if[^>]*>.*?</if>', '', dynamic_example, flags=re.DOTALL)
        sql_upper = clean_sql.upper().strip()
        
        from_pattern = r'\bFROM\s+([A-Z_][A-Z0-9_]*(?:\s+[A-Z_][A-Z0-9_]*)?)'
        from_matches = re.findall(from_pattern, sql_upper)
        
        join_pattern = r'\b(?:JOIN|INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|OUTER\s+JOIN)\s+([A-Z_][A-Z0-9_]*(?:\s+[A-Z_][A-Z0-9_]*)?)'
        join_matches = re.findall(join_pattern, sql_upper)
        
        print(f"   파서 인식 결과 - FROM: {from_matches}, JOIN: {join_matches}")
        print(f"   실제 테이블명: ['ORDERS', 'USERS', 'ORDER_ITEMS']")
        print(f"   파서 한계: MyBatis 동적 태그 처리 후 파싱 필요")
        
        # 4. 시스템 함수 케이스 분석
        print(f"\n4. 시스템 함수 케이스 분석:")
        print(f"   소스 파일: ProxyMapper.xml")
        print(f"   쿼리 ID: insertUserToV1")
        print(f"   라인: 21-35")
        
        system_function_example = """
        INSERT INTO users_v1 (
            username, email, status, created_at, del_yn
        ) VALUES (
            #{userData.username}, #{userData.email}, #{userData.status}, NOW(), 'N'
        )
        """
        
        print(f"   SQL 내용: {system_function_example.strip()}")
        print(f"   파서 인식 결과: ['USERS_V1']")
        print(f"   실제 테이블명: ['USERS_V1']")
        print(f"   파서 한계: NOW() 같은 시스템 함수는 테이블이 아님")
        
        # 5. 실제 SqlContent.db에서 확인
        print(f"\n5. 실제 SqlContent.db 확인:")
        
        if os.path.exists(sql_content_db_path):
            try:
                sql_conn = sqlite3.connect(sql_content_db_path)
                sql_cursor = sql_conn.cursor()
                
                # 몇 개 쿼리 확인
                test_queries = ['selectDashboardData', 'selectGlobalSearch', 'selectOrdersV2']
                
                for query_id in test_queries:
                    sql_cursor.execute("""
                        SELECT sql_content_compressed 
                        FROM sql_contents 
                        WHERE component_name = ?
                    """, (query_id,))
                    result = sql_cursor.fetchone()
                    
                    if result:
                        try:
                            decompressed_sql = gzip.decompress(result[0]).decode('utf-8')
                            print(f"\n   {query_id}:")
                            print(f"   SQL 길이: {len(decompressed_sql)} 문자")
                            
                            # 간단한 테이블명 추출 시뮬레이션
                            sql_upper = decompressed_sql.upper().strip()
                            from_pattern = r'\bFROM\s+([A-Z_][A-Z0-9_]*(?:\s+[A-Z_][A-Z0-9_]*)?)'
                            from_matches = re.findall(from_pattern, sql_upper)
                            
                            join_pattern = r'\b(?:JOIN|INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|OUTER\s+JOIN)\s+([A-Z_][A-Z0-9_]*(?:\s+[A-Z_][A-Z0-9_]*)?)'
                            join_matches = re.findall(join_pattern, sql_upper)
                            
                            print(f"   파서 인식 테이블: FROM={from_matches}, JOIN={join_matches}")
                            
                        except Exception as e:
                            print(f"   {query_id}: SQL 압축 해제 실패 - {e}")
                    else:
                        print(f"   {query_id}: SQL 내용 없음")
                
                sql_conn.close()
                
            except Exception as e:
                print(f"   SqlContent.db 접근 실패: {e}")
        else:
            print(f"   SqlContent.db 파일이 존재하지 않음")
        
        print(f"\n=== 분석 완료 ===")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_parsing_cases()
