#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== classes 테이블 스키마 ===")
cursor.execute('PRAGMA table_info(classes)')
schema = cursor.fetchall()
for row in schema:
    print(f" - {row}")

print("\n=== classes 테이블 레코드 수 ===")
cursor.execute('SELECT COUNT(*) FROM classes WHERE del_yn = "N"')
count = cursor.fetchone()[0]
print(f"classes 테이블 레코드 수: {count}")

print("\n=== classes 테이블 샘플 데이터 ===")
cursor.execute('SELECT * FROM classes WHERE del_yn = "N" LIMIT 5')
samples = cursor.fetchall()
for row in samples:
    print(f" - {row}")

print("\n=== JSP -> CLASS 관계 확인 ===")
cursor.execute("""
    SELECT COUNT(*) as count
    FROM files jsp_file
    JOIN relationships r1 ON jsp_file.file_id = r1.src_id AND r1.rel_type = 'CALL_METHOD'
    JOIN components m ON r1.dst_id = m.component_id AND m.component_type = 'METHOD'
    JOIN classes cls ON m.parent_id = cls.class_id
    WHERE jsp_file.file_type = 'JSP' AND jsp_file.del_yn = 'N' AND m.del_yn = 'N' AND cls.del_yn = 'N'
""")
jsp_class_count = cursor.fetchone()[0]
print(f"JSP -> METHOD -> CLASS 관계 수: {jsp_class_count}")

print("\n=== METHOD의 parent_id가 classes를 참조하는지 확인 ===")
cursor.execute("""
    SELECT COUNT(*) as count
    FROM components m
    JOIN classes cls ON m.parent_id = cls.class_id
    WHERE m.component_type = 'METHOD' AND m.del_yn = 'N' AND cls.del_yn = 'N'
""")
method_class_count = cursor.fetchone()[0]
print(f"METHOD -> CLASS 관계 수: {method_class_count}")

conn.close()
