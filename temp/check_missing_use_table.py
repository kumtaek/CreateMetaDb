"""
USE_TABLE이 없는 SQL 컴포넌트 중 실제로 테이블을 사용하는 쿼리 확인
"""
import sqlite3
import sys
import os
import re

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

# 1. USE_TABLE이 없는 SQL 컴포넌트 조회
sql_without_table = db_utils.execute_query("""
    SELECT c.component_id, c.component_name
    FROM components c
    WHERE c.component_type LIKE 'SQL_%'
      AND c.del_yn = 'N'
      AND NOT EXISTS (
          SELECT 1 FROM relationships r
          WHERE r.src_id = c.component_id
            AND r.rel_type = 'USE_TABLE'
            AND r.del_yn = 'N'
      )
    LIMIT 5
""")

if not sql_without_table:
    print("모든 SQL 컴포넌트에 USE_TABLE 관계가 있습니다!")
    db_utils.disconnect()
    sys.exit(0)

print(f"USE_TABLE이 없는 SQL 컴포넌트 샘플 (5개):")
print("=" * 80)

# 2. tables 테이블에서 모든 테이블명 조회
all_tables = db_utils.execute_query("""
    SELECT DISTINCT table_name
    FROM tables
    WHERE del_yn = 'N'
    ORDER BY LENGTH(table_name) DESC
""")

table_names = [row['table_name'] for row in all_tables]

# 3. SqlContent.db에서 쿼리 내용 조회
sql_content_db_path = metadata_db_path.replace('metadata.db', 'SqlContent.db')
if not os.path.exists(sql_content_db_path):
    print(f"SqlContent.db가 없습니다: {sql_content_db_path}")
    db_utils.disconnect()
    sys.exit(1)

conn_sql_content = sqlite3.connect(sql_content_db_path)
conn_sql_content.row_factory = sqlite3.Row
cursor = conn_sql_content.cursor()

for sql in sql_without_table:
    print(f"\nSQL 컴포넌트: {sql['component_name']}")
    print(f"  component_id: {sql['component_id']}")

    # SqlContent.db에서 쿼리 내용 조회
    cursor.execute("""
        SELECT sql_content_original
        FROM sql_contents
        WHERE component_id = ?
        LIMIT 1
    """, (sql['component_id'],))

    result = cursor.fetchone()
    if result:
        sql_content = result['sql_content_original']
        sql_content_upper = sql_content.upper()

        print(f"  쿼리 내용 (처음 200자):\n    {sql_content[:200]}")

        # 테이블명 검색
        found_tables = []
        for table_name in table_names:
            pattern = r'\b' + re.escape(table_name) + r'\b'
            if re.search(pattern, sql_content_upper):
                found_tables.append(table_name)

        if found_tables:
            print(f"  발견된 테이블: {', '.join(found_tables[:5])}")
        else:
            print(f"  발견된 테이블: 없음")
    else:
        print(f"  SqlContent.db에 쿼리 내용 없음")

    print("-" * 80)

conn_sql_content.close()
db_utils.disconnect()
print("\n분석 완료!")
