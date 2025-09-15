#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== CALL_METHOD 관계의 src_id 상세 분석 ===")
cursor.execute("""
    SELECT 
        r.src_id,
        f.file_name,
        f.file_type,
        c.component_name,
        c.component_type,
        COUNT(*) as count
    FROM relationships r
    LEFT JOIN files f ON r.src_id = f.file_id
    LEFT JOIN components c ON r.src_id = c.component_id
    WHERE r.rel_type = 'CALL_METHOD' AND r.del_yn = 'N'
    GROUP BY r.src_id, f.file_name, f.file_type, c.component_name, c.component_type
    ORDER BY count DESC
    LIMIT 20
""")
src_analysis = cursor.fetchall()
for row in src_analysis:
    src_id, file_name, file_type, comp_name, comp_type, count = row
    if file_name:
        print(f" - src_id {src_id}: {file_name} ({file_type}) -> {count}개")
    elif comp_name:
        print(f" - src_id {src_id}: {comp_name} ({comp_type}) -> {count}개")
    else:
        print(f" - src_id {src_id}: 알 수 없음 -> {count}개")

print("\n=== CALL_METHOD 관계의 dst_id 상세 분석 ===")
cursor.execute("""
    SELECT 
        r.dst_id,
        c.component_name,
        c.component_type,
        cls.class_name,
        COUNT(*) as count
    FROM relationships r
    JOIN components c ON r.dst_id = c.component_id
    LEFT JOIN classes cls ON c.parent_id = cls.class_id
    WHERE r.rel_type = 'CALL_METHOD' AND r.del_yn = 'N' AND c.del_yn = 'N'
    GROUP BY r.dst_id, c.component_name, c.component_type, cls.class_name
    ORDER BY count DESC
    LIMIT 10
""")
dst_analysis = cursor.fetchall()
for row in dst_analysis:
    dst_id, comp_name, comp_type, class_name, count = row
    if class_name:
        print(f" - dst_id {dst_id}: {comp_name} ({comp_type}) in {class_name} -> {count}개")
    else:
        print(f" - dst_id {dst_id}: {comp_name} ({comp_type}) -> {count}개")

print("\n=== 실제 연계 체인 샘플 (METHOD -> CLASS -> METHOD -> QUERY) ===")
cursor.execute("""
    SELECT 
        m.component_name as method_name,
        cls.class_name,
        q.component_name as query_name,
        q.component_type as query_type
    FROM components m
    JOIN classes cls ON m.parent_id = cls.class_id
    JOIN relationships r ON m.component_id = r.src_id AND r.rel_type = 'CALL_QUERY'
    JOIN components q ON r.dst_id = q.component_id AND q.component_type IN ('QUERY', 'SQL_SELECT', 'SQL_INSERT', 'SQL_UPDATE', 'SQL_DELETE', 'SQL_MERGE')
    WHERE m.component_type = 'METHOD' 
      AND m.del_yn = 'N' 
      AND cls.del_yn = 'N'
      AND q.del_yn = 'N'
    LIMIT 10
""")
samples = cursor.fetchall()
for row in samples:
    print(f" - {row[0]} ({row[1]}) -> {row[2]} ({row[3]})")

conn.close()
