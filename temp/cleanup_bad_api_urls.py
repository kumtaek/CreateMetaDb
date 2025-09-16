import sqlite3

def cleanup_bad_api_urls():
    """
    잘못된 API_URL 컴포넌트들을 삭제 (/:GET, /:POST, :GET, :POST 등)
    """
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    try:
        print("=== 잘못된 API_URL 컴포넌트 정리 시작 ===")
        
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
            return
        
        # 2. 관련 관계들도 함께 삭제
        cursor.execute("""
            SELECT COUNT(*)
            FROM relationships r
            JOIN components c ON (r.src_id = c.component_id OR r.dst_id = c.component_id)
            WHERE c.component_type = 'API_URL' 
              AND c.del_yn = 'N'
              AND (
                  c.component_name LIKE '/:%' 
                  OR c.component_name LIKE ':%'
                  OR c.component_name = '/'
                  OR c.component_name = ''
              )
              AND r.del_yn = 'N'
        """)
        related_relationships = cursor.fetchone()[0]
        print(f"관련 관계 개수: {related_relationships}개")
        
        # 3. 사용자 확인
        confirm = input(f"잘못된 API_URL {total_bad_count}개와 관련 관계 {related_relationships}개를 삭제하시겠습니까? (y/N): ")
        if confirm.lower() != 'y':
            print("취소되었습니다.")
            return
        
        # 4. 트랜잭션 시작
        cursor.execute("BEGIN TRANSACTION")
        
        # 5. 관련 관계들 먼저 삭제
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
        
        # 6. 잘못된 API_URL 컴포넌트 삭제
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
        
        # 7. 트랜잭션 커밋
        cursor.execute("COMMIT")
        
        print("=== 잘못된 API_URL 정리 완료 ===")
        print(f"총 삭제: 컴포넌트 {deleted_components}개, 관계 {deleted_relationships}개")
        
        # 8. 정리 후 상태 확인
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
            
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"오류 발생: {str(e)}")
        print("롤백되었습니다.")
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_bad_api_urls()
