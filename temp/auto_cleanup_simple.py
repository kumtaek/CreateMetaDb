#!/usr/bin/env python3
"""
잘못된 API_URL 컴포넌트 자동 정리 스크립트
대화형 입력 없이 자동으로 실행
"""

import sqlite3
import os

def main():
    try:
        # 데이터베이스 경로
        db_path = "projects/sampleSrc/metadata.db"
        
        if not os.path.exists(db_path):
            print(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}")
            return
        
        print("=== 잘못된 API_URL 컴포넌트 자동 정리 시작 ===")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 삭제할 잘못된 API_URL 개수 확인
        cursor.execute("""
            SELECT component_name, COUNT(*) as count
            FROM components 
            WHERE component_type = 'API_URL' 
              AND del_yn = 'N'
              AND (
                  component_name LIKE '/:%' 
                  OR component_name LIKE ':%'
                  OR component_name = '/'
                  OR component_name = ''
              )
            GROUP BY component_name
            ORDER BY count DESC
        """)
        bad_api_urls = cursor.fetchall()
        
        total_bad_count = sum(count for _, count in bad_api_urls)
        print(f"삭제 대상 잘못된 API_URL들:")
        for name, count in bad_api_urls:
            print(f"  '{name}': {count}개")
        
        if total_bad_count == 0:
            print("삭제할 잘못된 API_URL이 없습니다.")
            conn.close()
            return
        
        # 2. 자동으로 삭제 실행
        print(f"자동으로 {total_bad_count}개의 잘못된 API_URL을 삭제합니다...")
        
        # 트랜잭션 시작
        cursor.execute("BEGIN TRANSACTION")
        
        # 관련 관계들 먼저 삭제
        cursor.execute("""
            UPDATE relationships 
            SET del_yn = 'Y', updated_at = datetime('now', '+9 hours')
            WHERE (src_id IN (
                SELECT component_id 
                FROM components 
                WHERE component_type = 'API_URL' 
                  AND del_yn = 'N'
                  AND (
                      component_name LIKE '/:%' 
                      OR component_name LIKE ':%'
                      OR component_name = '/'
                      OR component_name = ''
                  )
            ) OR dst_id IN (
                SELECT component_id 
                FROM components 
                WHERE component_type = 'API_URL' 
                  AND del_yn = 'N'
                  AND (
                      component_name LIKE '/:%' 
                      OR component_name LIKE ':%'
                      OR component_name = '/'
                      OR component_name = ''
                  )
            )) AND del_yn = 'N'
        """)
        deleted_relationships = cursor.rowcount
        print(f"관련 관계 삭제: {deleted_relationships}개")
        
        # 잘못된 API_URL 컴포넌트 삭제
        cursor.execute("""
            UPDATE components 
            SET del_yn = 'Y', updated_at = datetime('now', '+9 hours')
            WHERE component_type = 'API_URL' 
              AND del_yn = 'N'
              AND (
                  component_name LIKE '/:%' 
                  OR component_name LIKE ':%'
                  OR component_name = '/'
                  OR component_name = ''
              )
        """)
        deleted_components = cursor.rowcount
        print(f"잘못된 API_URL 컴포넌트 삭제: {deleted_components}개")
        
        # 트랜잭션 커밋
        cursor.execute("COMMIT")
        
        print("=== 잘못된 API_URL 정리 완료 ===")
        print(f"총 삭제: 컴포넌트 {deleted_components}개, 관계 {deleted_relationships}개")
        
        # 정리 후 상태 확인
        print("\n=== 정리 후 API_URL 상태 ===")
        cursor.execute("""
            SELECT component_name, COUNT(*) as count
            FROM components 
            WHERE component_type = 'API_URL' AND del_yn = 'N'
            GROUP BY component_name
            ORDER BY count DESC
            LIMIT 10
        """)
        remaining_api_urls = cursor.fetchall()
        print("남은 API_URL들 (상위 10개):")
        for name, count in remaining_api_urls:
            print(f"  '{name}': {count}개")
        
        conn.close()
            
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
