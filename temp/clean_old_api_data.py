#!/usr/bin/env python3
"""
과거 버전의 잘못된 API 데이터 정리 스크립트
FRONTEND_API, API_ENTRY 컴포넌트와 관련 관계들을 삭제합니다.
"""

import sqlite3
import os
from datetime import datetime

def clean_old_api_data():
    """과거 버전의 잘못된 API 데이터 정리"""
    try:
        # 데이터베이스 연결
        db_path = "projects/sampleSrc/metadata.db"
        if not os.path.exists(db_path):
            print(f"데이터베이스 파일이 존재하지 않습니다: {db_path}")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== 과거 버전 API 데이터 정리 시작 ===")
        
        # 1. 삭제 전 현재 상태 확인
        print("\n1. 삭제 전 상태:")
        
        # FRONTEND_API 컴포넌트 개수
        cursor.execute("SELECT COUNT(*) FROM components WHERE project_id = 1 AND del_yn = 'N' AND component_type = 'FRONTEND_API'")
        frontend_count = cursor.fetchone()[0]
        print(f"  FRONTEND_API 컴포넌트: {frontend_count}개")
        
        # API_ENTRY 컴포넌트 개수
        cursor.execute("SELECT COUNT(*) FROM components WHERE project_id = 1 AND del_yn = 'N' AND component_type = 'API_ENTRY'")
        api_entry_count = cursor.fetchone()[0]
        print(f"  API_ENTRY 컴포넌트: {api_entry_count}개")
        
        # CALL_API_F2B 관계 개수
        cursor.execute("SELECT COUNT(*) FROM relationships WHERE del_yn = 'N' AND rel_type = 'CALL_API_F2B'")
        call_f2b_count = cursor.fetchone()[0]
        print(f"  CALL_API_F2B 관계: {call_f2b_count}개")
        
        # API_URL 컴포넌트 개수 (올바른 구조)
        cursor.execute("SELECT COUNT(*) FROM components WHERE project_id = 1 AND del_yn = 'N' AND component_type = 'API_URL'")
        api_url_count = cursor.fetchone()[0]
        print(f"  API_URL 컴포넌트: {api_url_count}개 (올바른 구조)")
        
        # 2. 삭제 실행
        if frontend_count > 0 or api_entry_count > 0 or call_f2b_count > 0:
            print(f"\n2. 삭제 실행 중...")
            
            # FRONTEND_API 컴포넌트 삭제 (논리 삭제)
            if frontend_count > 0:
                cursor.execute("""
                    UPDATE components 
                    SET del_yn = 'Y', updated_at = datetime('now', '+9 hours')
                    WHERE project_id = 1 AND component_type = 'FRONTEND_API' AND del_yn = 'N'
                """)
                print(f"  FRONTEND_API 컴포넌트 {frontend_count}개 삭제 완료")
            
            # API_ENTRY 컴포넌트 삭제 (논리 삭제)
            if api_entry_count > 0:
                cursor.execute("""
                    UPDATE components 
                    SET del_yn = 'Y', updated_at = datetime('now', '+9 hours')
                    WHERE project_id = 1 AND component_type = 'API_ENTRY' AND del_yn = 'N'
                """)
                print(f"  API_ENTRY 컴포넌트 {api_entry_count}개 삭제 완료")
            
            # CALL_API_F2B 관계 삭제 (논리 삭제)
            if call_f2b_count > 0:
                cursor.execute("""
                    UPDATE relationships 
                    SET del_yn = 'Y', updated_at = datetime('now', '+9 hours')
                    WHERE rel_type = 'CALL_API_F2B' AND del_yn = 'N'
                """)
                print(f"  CALL_API_F2B 관계 {call_f2b_count}개 삭제 완료")
            
            # API_ENTRY → METHOD 관계 삭제 (API_ENTRY가 삭제되므로)
            cursor.execute("""
                SELECT COUNT(*) FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                WHERE src.component_type = 'API_ENTRY' AND r.del_yn = 'N'
            """)
            api_entry_relations_count = cursor.fetchone()[0]
            
            if api_entry_relations_count > 0:
                cursor.execute("""
                    UPDATE relationships 
                    SET del_yn = 'Y', updated_at = datetime('now', '+9 hours')
                    WHERE src_id IN (
                        SELECT component_id FROM components 
                        WHERE project_id = 1 AND component_type = 'API_ENTRY' AND del_yn = 'N'
                    ) AND del_yn = 'N'
                """)
                print(f"  API_ENTRY → METHOD 관계 {api_entry_relations_count}개 삭제 완료")
            
            # 변경사항 커밋
            conn.commit()
            print(f"\n  모든 삭제 작업 완료!")
            
        else:
            print(f"\n2. 삭제할 과거 데이터가 없습니다.")
        
        # 3. 삭제 후 상태 확인
        print(f"\n3. 삭제 후 상태:")
        
        cursor.execute("SELECT COUNT(*) FROM components WHERE project_id = 1 AND del_yn = 'N' AND component_type = 'FRONTEND_API'")
        frontend_count_after = cursor.fetchone()[0]
        print(f"  FRONTEND_API 컴포넌트: {frontend_count_after}개")
        
        cursor.execute("SELECT COUNT(*) FROM components WHERE project_id = 1 AND del_yn = 'N' AND component_type = 'API_ENTRY'")
        api_entry_count_after = cursor.fetchone()[0]
        print(f"  API_ENTRY 컴포넌트: {api_entry_count_after}개")
        
        cursor.execute("SELECT COUNT(*) FROM relationships WHERE del_yn = 'N' AND rel_type = 'CALL_API_F2B'")
        call_f2b_count_after = cursor.fetchone()[0]
        print(f"  CALL_API_F2B 관계: {call_f2b_count_after}개")
        
        cursor.execute("SELECT COUNT(*) FROM components WHERE project_id = 1 AND del_yn = 'N' AND component_type = 'API_URL'")
        api_url_count_after = cursor.fetchone()[0]
        print(f"  API_URL 컴포넌트: {api_url_count_after}개 (올바른 구조)")
        
        conn.close()
        
        print(f"\n=== 정리 작업 완료 ===")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        return

if __name__ == "__main__":
    clean_old_api_data()
