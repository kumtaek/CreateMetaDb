"""
폴백 테이블 관계 생성 결과 확인 스크립트
"""
import sqlite3
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

# 1. 전체 USE_TABLE 관계 수
total_use_table = db_utils.execute_query("""
    SELECT COUNT(*) as count
    FROM relationships
    WHERE rel_type = 'USE_TABLE' AND del_yn = 'N'
""")
print(f"전체 USE_TABLE 관계: {total_use_table[0]['count']}개")

# 2. USE_TABLE 관계 상세 (상위 10개)
use_table_details = db_utils.execute_query("""
    SELECT
        c1.component_name as sql_query,
        c2.component_name as table_name
    FROM relationships r
    JOIN components c1 ON r.src_id = c1.component_id
    JOIN components c2 ON r.dst_id = c2.component_id
    WHERE r.rel_type = 'USE_TABLE'
      AND r.del_yn = 'N'
    LIMIT 10
""")

if use_table_details:
    print("\nUSE_TABLE 관계 상세 (상위 10개):")
    for i, detail in enumerate(use_table_details, 1):
        print(f"  {i}. {detail['sql_query']} -> {detail['table_name']}")

# 4. USE_TABLE이 없는 SQL 컴포넌트 수
sql_without_table = db_utils.execute_query("""
    SELECT COUNT(*) as count
    FROM components c
    WHERE c.component_type LIKE 'SQL_%'
      AND c.del_yn = 'N'
      AND NOT EXISTS (
          SELECT 1 FROM relationships r
          WHERE r.src_id = c.component_id
            AND r.rel_type = 'USE_TABLE'
            AND r.del_yn = 'N'
      )
""")
print(f"\nUSE_TABLE이 없는 SQL 컴포넌트: {sql_without_table[0]['count']}개")

# 5. SQL 컴포넌트별 USE_TABLE 수 (상위 10개)
sql_table_count = db_utils.execute_query("""
    SELECT
        c.component_name,
        COUNT(r.relationship_id) as table_count
    FROM components c
    LEFT JOIN relationships r ON c.component_id = r.src_id
        AND r.rel_type = 'USE_TABLE'
        AND r.del_yn = 'N'
    WHERE c.component_type LIKE 'SQL_%'
      AND c.del_yn = 'N'
    GROUP BY c.component_name
    ORDER BY table_count DESC
    LIMIT 10
""")

print("\nSQL 컴포넌트별 USE_TABLE 수 (상위 10개):")
for i, detail in enumerate(sql_table_count, 1):
    print(f"  {i}. {detail['component_name']}: {detail['table_count']}개 테이블")

db_utils.disconnect()
print("\n분석 완료!")
