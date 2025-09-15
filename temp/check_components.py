#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== 컴포넌트 타입 확인 ===")
cursor.execute("SELECT DISTINCT component_type FROM components WHERE del_yn = 'N' ORDER BY component_type")
component_types = cursor.fetchall()
for row in component_types:
    print(f" - {row[0]}")

print("\n=== JSP -> METHOD 관계 확인 ===")
cursor.execute("""
    SELECT COUNT(*) as count
    FROM files jsp_file
    JOIN relationships r1 ON jsp_file.file_id = r1.src_id AND r1.rel_type = 'CALL_METHOD'
    JOIN components m ON r1.dst_id = m.component_id AND m.component_type = 'METHOD'
    WHERE jsp_file.file_type = 'JSP' AND jsp_file.del_yn = 'N' AND m.del_yn = 'N'
""")
jsp_method_count = cursor.fetchone()[0]
print(f"JSP -> METHOD 관계 수: {jsp_method_count}")

print("\n=== METHOD -> QUERY 관계 확인 ===")
cursor.execute("""
    SELECT COUNT(*) as count
    FROM components m
    JOIN relationships r2 ON m.component_id = r2.src_id AND r2.rel_type = 'CALL_QUERY'
    JOIN components q ON r2.dst_id = q.component_id AND q.component_type IN ('QUERY', 'SQL_SELECT', 'SQL_INSERT', 'SQL_UPDATE', 'SQL_DELETE', 'SQL_MERGE')
    WHERE m.component_type = 'METHOD' AND m.del_yn = 'N' AND q.del_yn = 'N'
""")
method_query_count = cursor.fetchone()[0]
print(f"METHOD -> QUERY 관계 수: {method_query_count}")

print("\n=== METHOD의 parent_id 확인 ===")
cursor.execute("""
    SELECT COUNT(*) as count, 
           COUNT(CASE WHEN parent_id IS NOT NULL THEN 1 END) as with_parent,
           COUNT(CASE WHEN parent_id IS NULL THEN 1 END) as without_parent
    FROM components 
    WHERE component_type = 'METHOD' AND del_yn = 'N'
""")
parent_stats = cursor.fetchone()
print(f"전체 METHOD 수: {parent_stats[0]}")
print(f"parent_id가 있는 METHOD: {parent_stats[1]}")
print(f"parent_id가 없는 METHOD: {parent_stats[2]}")

print("\n=== parent_id가 있는 METHOD의 상위 컴포넌트 타입 확인 ===")
cursor.execute("""
    SELECT c.component_type, COUNT(*) as count
    FROM components m
    JOIN components c ON m.parent_id = c.component_id
    WHERE m.component_type = 'METHOD' AND m.del_yn = 'N' AND c.del_yn = 'N'
    GROUP BY c.component_type
    ORDER BY count DESC
""")
parent_types = cursor.fetchall()
for row in parent_types:
    print(f" - {row[0]}: {row[1]}개")

conn.close()
