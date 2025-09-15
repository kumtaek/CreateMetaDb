#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== JSP 컴포넌트와 METHOD 관계 확인 ===")
cursor.execute("""
    SELECT COUNT(*) as count
    FROM components jsp_comp
    JOIN relationships r ON jsp_comp.component_id = r.src_id AND r.rel_type = 'CALL_METHOD'
    JOIN components m ON r.dst_id = m.component_id AND m.component_type = 'METHOD'
    WHERE jsp_comp.component_type = 'JSP' AND jsp_comp.del_yn = 'N' AND m.del_yn = 'N'
""")
jsp_method_count = cursor.fetchone()[0]
print(f"JSP 컴포넌트 -> METHOD 관계 수: {jsp_method_count}")

print("\n=== JSP 파일과 METHOD 관계 확인 ===")
cursor.execute("""
    SELECT COUNT(*) as count
    FROM files jsp_file
    JOIN relationships r ON jsp_file.file_id = r.src_id AND r.rel_type = 'CALL_METHOD'
    JOIN components m ON r.dst_id = m.component_id AND m.component_type = 'METHOD'
    WHERE jsp_file.file_type = 'JSP' AND jsp_file.del_yn = 'N' AND m.del_yn = 'N'
""")
jsp_file_method_count = cursor.fetchone()[0]
print(f"JSP 파일 -> METHOD 관계 수: {jsp_file_method_count}")

print("\n=== CALL_METHOD 관계의 src_id 타입 확인 ===")
cursor.execute("""
    SELECT c.component_type, COUNT(*) as count
    FROM relationships r
    JOIN components c ON r.src_id = c.component_id
    WHERE r.rel_type = 'CALL_METHOD' AND r.del_yn = 'N' AND c.del_yn = 'N'
    GROUP BY c.component_type
    ORDER BY count DESC
""")
src_types = cursor.fetchall()
for row in src_types:
    print(f" - {row[0]}: {row[1]}개")

print("\n=== CALL_METHOD 관계의 dst_id 타입 확인 ===")
cursor.execute("""
    SELECT c.component_type, COUNT(*) as count
    FROM relationships r
    JOIN components c ON r.dst_id = c.component_id
    WHERE r.rel_type = 'CALL_METHOD' AND r.del_yn = 'N' AND c.del_yn = 'N'
    GROUP BY c.component_type
    ORDER BY count DESC
""")
dst_types = cursor.fetchall()
for row in dst_types:
    print(f" - {row[0]}: {row[1]}개")

print("\n=== 실제 연계 체인 샘플 (METHOD -> CLASS -> METHOD -> QUERY) ===")
cursor.execute("""
    SELECT 
        m1.component_name as method1_name,
        cls.class_name,
        m2.component_name as method2_name,
        q.component_name as query_name,
        q.component_type as query_type
    FROM components m1
    JOIN classes cls ON m1.parent_id = cls.class_id
    JOIN relationships r2 ON m1.component_id = r2.src_id AND r2.rel_type = 'CALL_QUERY'
    JOIN components q ON r2.dst_id = q.component_id AND q.component_type IN ('QUERY', 'SQL_SELECT', 'SQL_INSERT', 'SQL_UPDATE', 'SQL_DELETE', 'SQL_MERGE')
    WHERE m1.component_type = 'METHOD' 
      AND m1.del_yn = 'N' 
      AND cls.del_yn = 'N'
      AND q.del_yn = 'N'
    LIMIT 5
""")
samples = cursor.fetchall()
for row in samples:
    print(f" - {row[0]} -> {row[1]} -> {row[2]} -> {row[3]} ({row[4]})")

conn.close()
