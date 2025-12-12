"""
주석 무시 기능 테스트
- 주석에 포함된 테이블명이 USE_TABLE로 추가되지 않는지 확인
"""
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.database_utils import DatabaseUtils
from util.path_utils import get_project_metadata_db_path

project_name = "sampleSrc"
metadata_db_path = get_project_metadata_db_path(project_name)

db_utils = DatabaseUtils(metadata_db_path)
if not db_utils.connect():
    print(f"데이터베이스 연결 실패: {metadata_db_path}")
    sys.exit(1)

print("="*80)
print("주석 무시 기능 테스트")
print("="*80)

# 각 쿼리별 주석에만 포함된 테이블 (실제로는 사용되지 않아야 함)
query_comment_tables = {
    'findUsersByCondition': [
        'ORDERS',  # 블록 주석
        'PRODUCTS',  # 블록 주석
        'CATEGORIES'  # 라인 주석
    ],
    'findUsersByAdvancedCondition': [
        'ORDER_ITEMS',  # 블록 주석
        'PRODUCT_CATEGORIES',  # 블록 주석
        'USER_ADDRESSES',  # 블록 주석
        'PAYMENT_HISTORY'  # 라인 주석
    ],
    'selectProductsByAdvancedCondition': [
        'CUSTOMER_REVIEWS',  # 라인 주석 (PRODUCTS, CATEGORIES는 실제 사용)
        'INVENTORY_LOGS',  # 라인 주석
        'SHIPPING_INFO',  # 블록 주석
        'SUPPLIER_CONTRACTS'  # 라인 주석
    ]
}

# 주석 추가한 쿼리 ID
test_query_ids = list(query_comment_tables.keys())

print(f"\n[테스트 대상 쿼리]")
for query_id in test_query_ids:
    print(f"  - {query_id}")

print(f"\n[쿼리별 주석에만 포함된 테이블]")
for query_id, tables in query_comment_tables.items():
    print(f"  {query_id}: {', '.join(tables)}")

print(f"\n{'='*80}")
print("테스트 시작: 주석에만 포함된 테이블이 USE_TABLE로 추가되었는지 확인")
print(f"{'='*80}\n")

# 각 쿼리에 대해 주석 테이블이 USE_TABLE로 등록되었는지 확인
failed_cases = []

for query_id in test_query_ids:
    # SQL 컴포넌트 조회
    sql_component = db_utils.execute_query("""
        SELECT component_id, component_name
        FROM components
        WHERE component_name = ?
          AND component_type LIKE 'SQL_%'
          AND del_yn = 'N'
        LIMIT 1
    """, (query_id,))

    if not sql_component:
        print(f"[WARN] 쿼리를 찾을 수 없음: {query_id}")
        continue

    sql_component_id = sql_component[0]['component_id']
    component_name = sql_component[0]['component_name']

    # 이 쿼리의 USE_TABLE 관계 조회
    use_tables = db_utils.execute_query("""
        SELECT t.table_name
        FROM relationships r
        JOIN components c ON r.dst_id = c.component_id
        JOIN tables t ON c.component_id = t.component_id
        WHERE r.src_id = ?
          AND r.rel_type = 'USE_TABLE'
          AND r.del_yn = 'N'
          AND c.del_yn = 'N'
          AND t.del_yn = 'N'
    """, (sql_component_id,))

    used_table_names = {row['table_name'] for row in use_tables}

    print(f"\n쿼리: {component_name}")
    print(f"  실제 사용 테이블: {', '.join(sorted(used_table_names)) if used_table_names else '없음'}")

    # 이 쿼리의 주석에만 포함된 테이블 목록 가져오기
    comment_only_for_this_query = query_comment_tables.get(query_id, [])
    print(f"  주석에만 포함된 테이블: {', '.join(comment_only_for_this_query) if comment_only_for_this_query else '없음'}")

    # 주석에만 포함된 테이블이 USE_TABLE로 등록되었는지 확인
    comment_tables_found = []
    for comment_table in comment_only_for_this_query:
        if comment_table in used_table_names:
            comment_tables_found.append(comment_table)

    if comment_tables_found:
        print(f"  [FAIL] 주석 테이블이 잘못 추가됨: {', '.join(comment_tables_found)}")
        failed_cases.append({
            'query': component_name,
            'tables': comment_tables_found
        })
    else:
        print(f"  [PASS] 주석 테이블이 추가되지 않음 (정상)")

print(f"\n{'='*80}")
print("테스트 결과")
print(f"{'='*80}\n")

if failed_cases:
    print(f"[FAIL] 테스트 실패: {len(failed_cases)}개 쿼리에서 주석 테이블이 잘못 추가됨\n")
    for case in failed_cases:
        print(f"  - {case['query']}: {', '.join(case['tables'])}")
    print("\n주석 제거 로직이 제대로 작동하지 않았습니다.")
else:
    print(f"[PASS] 테스트 성공: 모든 쿼리에서 주석 테이블이 정상적으로 무시됨")
    print("\n주석 제거 로직이 정상 작동합니다!")

db_utils.disconnect()
print(f"\n{'='*80}")
