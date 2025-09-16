import sqlite3

def cleanup_old_components():
    """
    구버전 FRONTEND_API, API_ENTRY 컴포넌트와 관련 관계들을 삭제
    """
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    try:
        print("=== 구버전 컴포넌트 정리 시작 ===")
        
        # 1. 삭제할 컴포넌트 개수 확인
        cursor.execute("SELECT COUNT(*) FROM components WHERE component_type IN ('FRONTEND_API', 'API_ENTRY') AND del_yn = 'N'")
        old_component_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM relationships WHERE rel_type = 'CALL_API_F2B' AND del_yn = 'N'")
        old_relationship_count = cursor.fetchone()[0]
        
        print(f"삭제 대상: FRONTEND_API/API_ENTRY 컴포넌트 {old_component_count}개, CALL_API_F2B 관계 {old_relationship_count}개")
        
        if old_component_count == 0 and old_relationship_count == 0:
            print("삭제할 구버전 컴포넌트가 없습니다.")
            return
        
        # 2. 사용자 확인
        confirm = input(f"구버전 컴포넌트 {old_component_count}개와 관계 {old_relationship_count}개를 삭제하시겠습니까? (y/N): ")
        if confirm.lower() != 'y':
            print("취소되었습니다.")
            return
        
        # 3. 트랜잭션 시작
        cursor.execute("BEGIN TRANSACTION")
        
        # 4. 구버전 관계 삭제 (CALL_API_F2B)
        cursor.execute("""
            UPDATE relationships 
            SET del_yn = 'Y', updated_at = datetime('now', '+9 hours')
            WHERE rel_type = 'CALL_API_F2B' AND del_yn = 'N'
        """)
        deleted_relationships = cursor.rowcount
        print(f"CALL_API_F2B 관계 삭제: {deleted_relationships}개")
        
        # 5. 구버전 컴포넌트 삭제 (FRONTEND_API, API_ENTRY)
        cursor.execute("""
            UPDATE components 
            SET del_yn = 'Y', updated_at = datetime('now', '+9 hours')
            WHERE component_type IN ('FRONTEND_API', 'API_ENTRY') AND del_yn = 'N'
        """)
        deleted_components = cursor.rowcount
        print(f"구버전 컴포넌트 삭제: {deleted_components}개")
        
        # 6. api_components 테이블의 관련 레코드도 삭제
        cursor.execute("""
            UPDATE api_components 
            SET del_yn = 'Y', updated_at = datetime('now', '+9 hours')
            WHERE api_type IN ('FRONTEND_API', 'API_ENTRY') AND del_yn = 'N'
        """)
        deleted_api_components = cursor.rowcount
        print(f"api_components 삭제: {deleted_api_components}개")
        
        # 7. 트랜잭션 커밋
        cursor.execute("COMMIT")
        
        print("=== 구버전 컴포넌트 정리 완료 ===")
        print(f"총 삭제: 컴포넌트 {deleted_components}개, 관계 {deleted_relationships}개, api_components {deleted_api_components}개")
        
        # 8. 정리 후 상태 확인
        print("\n=== 정리 후 상태 ===")
        cursor.execute("SELECT component_type, COUNT(*) FROM components WHERE del_yn = 'N' GROUP BY component_type ORDER BY COUNT(*) DESC")
        component_counts = cursor.fetchall()
        for comp_type, count in component_counts:
            print(f"  {comp_type}: {count}개")
        
        cursor.execute("SELECT rel_type, COUNT(*) FROM relationships WHERE del_yn = 'N' GROUP BY rel_type ORDER BY COUNT(*) DESC")
        rel_counts = cursor.fetchall()
        for rel_type, count in rel_counts:
            print(f"  {rel_type}: {count}개")
            
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"오류 발생: {str(e)}")
        print("롤백되었습니다.")
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_old_components()
