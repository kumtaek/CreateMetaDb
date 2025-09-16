#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def analyze_specific_cases():
    """특정 케이스들 분석"""
    
    db_path = 'projects/sampleSrc/metadata.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== 특정 케이스별 분석 ===")
        
        # 1. insertUserToV1 케이스 분석
        print(f"\n1. insertUserToV1 케이스 분석:")
        
        # SqlContent.db에서 실제 SQL 확인
        sql_content_db_path = 'projects/sampleSrc/SqlContent.db'
        if os.path.exists(sql_content_db_path):
            try:
                sql_conn = sqlite3.connect(sql_content_db_path)
                sql_cursor = sql_conn.cursor()
                
                sql_cursor.execute("""
                    SELECT sql_content_compressed 
                    FROM sql_contents 
                    WHERE component_name = 'insertUserToV1'
                """)
                result = sql_cursor.fetchone()
                
                if result:
                    import gzip
                    try:
                        decompressed_sql = gzip.decompress(result[0]).decode('utf-8')
                        print(f"   실제 SQL 내용:")
                        print(f"   {decompressed_sql}")
                        
                        # 테이블명 추출 시뮬레이션
                        import re
                        sql_upper = decompressed_sql.upper().strip()
                        insert_pattern = r'\bINSERT\s+INTO\s+([A-Z_][A-Z0-9_]*)'
                        insert_matches = re.findall(insert_pattern, sql_upper)
                        
                        print(f"   파서가 인식한 테이블명: {insert_matches}")
                        
                    except Exception as e:
                        print(f"   SQL 압축 해제 실패: {e}")
                else:
                    print(f"   insertUserToV1 SQL 내용 없음")
                
                sql_conn.close()
            except Exception as e:
                print(f"   SqlContent.db 접근 실패: {e}")
        
        # 2. searchByName 케이스 분석
        print(f"\n2. searchByName 케이스 분석:")
        
        if os.path.exists(sql_content_db_path):
            try:
                sql_conn = sqlite3.connect(sql_content_db_path)
                sql_cursor = sql_conn.cursor()
                
                sql_cursor.execute("""
                    SELECT sql_content_compressed 
                    FROM sql_contents 
                    WHERE component_name = 'searchByName'
                """)
                result = sql_cursor.fetchone()
                
                if result:
                    import gzip
                    try:
                        decompressed_sql = gzip.decompress(result[0]).decode('utf-8')
                        print(f"   실제 SQL 내용:")
                        print(f"   {decompressed_sql}")
                        
                        # 테이블명 추출 시뮬레이션
                        import re
                        sql_upper = decompressed_sql.upper().strip()
                        
                        # FROM 절 추출
                        from_pattern = r'\bFROM\s+([A-Z_][A-Z0-9_]*(?:\s+[A-Z_][A-Z0-9_]*)?)'
                        from_matches = re.findall(from_pattern, sql_upper)
                        
                        # JOIN 절 추출
                        join_pattern = r'\b(?:JOIN|INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|OUTER\s+JOIN)\s+([A-Z_][A-Z0-9_]*(?:\s+[A-Z_][A-Z0-9_]*)?)'
                        join_matches = re.findall(join_pattern, sql_upper)
                        
                        print(f"   파서가 인식한 FROM 테이블명: {from_matches}")
                        print(f"   파서가 인식한 JOIN 테이블명: {join_matches}")
                        
                    except Exception as e:
                        print(f"   SQL 압축 해제 실패: {e}")
                else:
                    print(f"   searchByName SQL 내용 없음")
                
                sql_conn.close()
            except Exception as e:
                print(f"   SqlContent.db 접근 실패: {e}")
        
        # 3. 파서 한계 예시들
        print(f"\n3. 파서 한계 예시들:")
        
        example_queries = [
            # 서브쿼리 케이스
            "SELECT * FROM (SELECT u.id, u.name FROM users u WHERE u.status = 'A') t",
            
            # WITH 절 케이스  
            "WITH user_data AS (SELECT * FROM users WHERE active = 1) SELECT * FROM user_data",
            
            # UNION 케이스
            "SELECT * FROM users WHERE type = 'A' UNION ALL SELECT * FROM customers WHERE status = 'ACTIVE'",
            
            # 동적 조건 케이스
            "SELECT * FROM users WHERE 1=1 AND (status = 'A' OR status = 'B')",
            
            # 복잡한 JOIN 케이스
            "SELECT * FROM users u1 JOIN users u2 ON u1.parent_id = u2.id"
        ]
        
        for i, query in enumerate(example_queries, 1):
            print(f"\n   예시 {i}: {query}")
            
            # 파서 시뮬레이션
            import re
            sql_upper = query.upper().strip()
            
            # FROM 절 추출
            from_pattern = r'\bFROM\s+([A-Z_][A-Z0-9_]*(?:\s+[A-Z_][A-Z0-9_]*)?)'
            from_matches = re.findall(from_pattern, sql_upper)
            
            # JOIN 절 추출
            join_pattern = r'\b(?:JOIN|INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|OUTER\s+JOIN)\s+([A-Z_][A-Z0-9_]*(?:\s+[A-Z_][A-Z0-9_]*)?)'
            join_matches = re.findall(join_pattern, sql_upper)
            
            print(f"     파서 인식 결과 - FROM: {from_matches}, JOIN: {join_matches}")
            
            # 실제 테이블명과 비교
            if i == 1:  # 서브쿼리
                print(f"     실제 테이블명: ['USERS'] (서브쿼리 내부)")
                print(f"     파서 한계: 서브쿼리 내부 테이블명 인식 불가")
            elif i == 2:  # WITH 절
                print(f"     실제 테이블명: ['USERS'] (WITH 절 내부)")
                print(f"     파서 한계: WITH 절 내부 테이블명 인식 불가")
            elif i == 3:  # UNION
                print(f"     실제 테이블명: ['USERS', 'CUSTOMERS']")
                print(f"     파서 한계: UNION의 두 번째 쿼리 테이블명 놓칠 수 있음")
        
        conn.close()
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_specific_cases()
