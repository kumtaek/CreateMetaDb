#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== JSP 파일 목록 ===")
cursor.execute("SELECT file_name FROM files WHERE file_type = 'JSP' AND del_yn = 'N'")
jsp_files = cursor.fetchall()
for row in jsp_files:
    print(f" - {row[0]}")

print("\n=== JSP 파일들의 관계 확인 ===")
cursor.execute("""
    SELECT f.file_name, r.rel_type, COUNT(*) as count
    FROM files f
    LEFT JOIN relationships r ON f.file_id = r.src_id AND r.del_yn = 'N'
    WHERE f.file_type = 'JSP' AND f.del_yn = 'N'
    GROUP BY f.file_name, r.rel_type
    ORDER BY f.file_name
""")
jsp_relations = cursor.fetchall()
for row in jsp_relations:
    if row[1] is None:
        print(f" - {row[0]}: 관계 없음")
    else:
        print(f" - {row[0]} -> {row[1]}: {row[2]}개")

print("\n=== CALL_METHOD 관계의 src_id 확인 ===")
cursor.execute("""
    SELECT f.file_name, f.file_type, COUNT(*) as count
    FROM relationships r
    JOIN files f ON r.src_id = f.file_id
    WHERE r.rel_type = 'CALL_METHOD' AND r.del_yn = 'N' AND f.del_yn = 'N'
    GROUP BY f.file_name, f.file_type
    ORDER BY count DESC
    LIMIT 10
""")
call_method_srcs = cursor.fetchall()
for row in call_method_srcs:
    print(f" - {row[0]} ({row[1]}): {row[2]}개")

print("\n=== CALL_METHOD 관계의 dst_id 확인 ===")
cursor.execute("""
    SELECT c.component_name, c.component_type, COUNT(*) as count
    FROM relationships r
    JOIN components c ON r.dst_id = c.component_id
    WHERE r.rel_type = 'CALL_METHOD' AND r.del_yn = 'N' AND c.del_yn = 'N'
    GROUP BY c.component_name, c.component_type
    ORDER BY count DESC
    LIMIT 10
""")
call_method_dsts = cursor.fetchall()
for row in call_method_dsts:
    print(f" - {row[0]} ({row[1]}): {row[2]}개")

print("\n=== JSP 컴포넌트와의 관계 확인 ===")
cursor.execute("""
    SELECT jsp_comp.component_name, r.rel_type, COUNT(*) as count
    FROM components jsp_comp
    LEFT JOIN relationships r ON jsp_comp.component_id = r.src_id AND r.del_yn = 'N'
    WHERE jsp_comp.component_type = 'JSP' AND jsp_comp.del_yn = 'N'
    GROUP BY jsp_comp.component_name, r.rel_type
    ORDER BY jsp_comp.component_name
""")
jsp_comp_relations = cursor.fetchall()
for row in jsp_comp_relations:
    if row[1] is None:
        print(f" - {row[0]}: 관계 없음")
    else:
        print(f" - {row[0]} -> {row[1]}: {row[2]}개")

conn.close()
