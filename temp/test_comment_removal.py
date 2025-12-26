"""
주석 제거 로직 테스트
"""
import re

# 테스트 쿼리 샘플
test_queries = [
    # 1. 블록 주석 /* */
    """
    SELECT * FROM USERS
    /* 이 테이블은 DEPARTMENTS와 조인할 예정 */
    WHERE user_id = 1
    """,

    # 2. 라인 주석 --
    """
    SELECT * FROM USERS
    -- 다음 버전에서 ORDERS 테이블 조인 추가
    WHERE status = 'ACTIVE'
    """,

    # 3. 혼합 주석
    """
    SELECT u.*, d.dept_name
    FROM USERS u  /* 사용자 테이블 */
    -- 부서 테이블 조인
    LEFT JOIN DEPARTMENTS d ON u.dept_id = d.dept_id
    /* ORDERS 테이블은 나중에 추가 */
    WHERE u.status = 'ACTIVE'  -- 활성 사용자만
    """,

    # 4. 여러 줄 블록 주석
    """
    SELECT *
    FROM USERS
    /*
     * TODO: PRODUCTS 테이블 조인 필요
     * 작성자: 홍길동
     * 날짜: 2024-01-01
     */
    WHERE user_id > 0
    """
]

def remove_comments(query_content):
    """주석 제거 (consistency_validator.py와 동일한 로직)"""
    # 1) /* */ 블록 주석 제거
    query_content = re.sub(r'/\*.*?\*/', ' ', query_content, flags=re.DOTALL)
    # 2) -- 라인 주석 제거
    query_content = re.sub(r'--[^\n]*', ' ', query_content)
    return query_content

# 테스트 실행
for i, test_query in enumerate(test_queries, 1):
    print(f"\n{'='*80}")
    print(f"테스트 케이스 {i}")
    print(f"{'='*80}")
    print(f"\n[원본 쿼리]")
    print(test_query)

    # 주석 제거
    cleaned_query = remove_comments(test_query)

    print(f"\n[주석 제거 후]")
    print(cleaned_query)

    # 테이블명 검색 시뮬레이션
    test_table_names = ['USERS', 'DEPARTMENTS', 'ORDERS', 'PRODUCTS']
    found_tables = []

    cleaned_upper = cleaned_query.upper()
    for table_name in test_table_names:
        if table_name in cleaned_upper:
            found_tables.append(table_name)

    print(f"\n[검색된 테이블]")
    print(f"  실제로 사용된 테이블: {', '.join(found_tables)}")

print(f"\n{'='*80}")
print("테스트 완료!")
print("주석 안의 테이블명(DEPARTMENTS, ORDERS, PRODUCTS)이 제외되고")
print("실제 쿼리에 사용된 테이블(USERS, DEPARTMENTS)만 검색되어야 정상입니다.")
print(f"{'='*80}")
