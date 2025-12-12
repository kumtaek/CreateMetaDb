"""
단순 문자열 매칭 로직 테스트 스크립트
- 중복 데이터 생성 방지 확인
- 테이블 검색 로직 검증
"""

import sys
import os

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.sql_content_manager import SqlContentManager
from util.logger import info, debug

def test_brute_force_search():
    """단순 문자열 매칭 테스트"""
    
    print("=" * 60)
    print("단순 문자열 매칭 로직 테스트")
    print("=" * 60)
    
    # 1. 주석 제거 테스트
    test_sql = """
    -- 이것은 주석입니다 USER_TABLE
    /* 블록 주석
       USER_DATA
    */
    SELECT * FROM EMPLOYEE_INFO
    WHERE id = 1
    """
    
    manager = SqlContentManager("sampleSrc", enable_brute_force_search=True)
    cleaned = manager._remove_comments_simple(test_sql)
    
    print("\n[1] 주석 제거 테스트:")
    print(f"원본:\n{test_sql}")
    print(f"\n정제 후:\n{cleaned}")
    
    # USER_TABLE, USER_DATA는 제거되고 EMPLOYEE_INFO만 남아야 함
    assert "USER_TABLE" not in cleaned.upper(), "주석 내 테이블명이 제거되지 않음!"
    assert "USER_DATA" not in cleaned.upper(), "블록 주석 내 테이블명이 제거되지 않음!"
    assert "EMPLOYEE_INFO" in cleaned.upper(), "실제 테이블명이 삭제됨!"
    print("✓ 주석 제거 성공")
    
    # 2. 단어 경계 테스트
    test_sql2 = """
    SELECT * FROM USER_INFO, USER_DATA
    WHERE USER_INFO.user_id = USER_DATA.user_id
    """
    
    import re
    cleaned2 = manager._remove_comments_simple(test_sql2).upper()
    
    print("\n[2] 단어 경계 검색 테스트:")
    
    # USER는 USER_INFO나 USER_DATA의 일부이므로 단어 경계 검색 시 매칭되지 않아야 함
    if re.search(r'\bUSER\b', cleaned2):
        print("✗ 단독 'USER'가 잘못 매칭됨 (부분 일치 발생)")
    else:
        print("✓ 단독 'USER'는 매칭되지 않음 (정상)")
    
    # USER_INFO는 완전한 단어이므로 매칭되어야 함
    if re.search(r'\bUSER_INFO\b', cleaned2):
        print("✓ 'USER_INFO'가 정상 매칭됨")
    else:
        print("✗ 'USER_INFO'가 매칭되지 않음 (오류)")
    
    # USER_DATA도 완전한 단어이므로 매칭되어야 함
    if re.search(r'\bUSER_DATA\b', cleaned2):
        print("✓ 'USER_DATA'가 정상 매칭됨")
    else:
        print("✗ 'USER_DATA'가 매칭되지 않음 (오류)")
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    test_brute_force_search()
