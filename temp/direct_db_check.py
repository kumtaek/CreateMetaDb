import sqlite3

conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== 현재 데이터베이스 상태 분석 ===")

print("\n1. 컴포넌트 타입별 개수:")
cursor.execute("""
    SELECT component_type, COUNT(*) as count 
    FROM components 
    WHERE del_yn = 'N' 
    GROUP BY component_type 
    ORDER BY count DESC
""")
component_counts = cursor.fetchall()
for comp_type, count in component_counts:
    print(f"  {comp_type}: {count}개")

print("\n2. 관계 타입별 개수:")
cursor.execute("""
    SELECT rel_type, COUNT(*) as count 
    FROM relationships 
    WHERE del_yn = 'N' 
    GROUP BY rel_type 
    ORDER BY count DESC
""")
relationship_counts = cursor.fetchall()
for rel_type, count in relationship_counts:
    print(f"  {rel_type}: {count}개")

print("\n3. API_URL 컴포넌트 샘플 (최대 5개):")
cursor.execute("""
    SELECT c.component_id, c.component_name, c.file_id, f.file_name, f.file_type
    FROM components c
    LEFT JOIN files f ON c.file_id = f.file_id
    WHERE c.component_type = 'API_URL' AND c.del_yn = 'N'
    LIMIT 5
""")
api_url_samples = cursor.fetchall()
for row in api_url_samples:
    print(f"  ID: {row[0]}, Name: '{row[1]}', File: {row[2]} ({row[3]} - {row[4]})")

print("\n4. FRONTEND_API 컴포넌트 샘플 (최대 5개):")
cursor.execute("""
    SELECT c.component_id, c.component_name, c.file_id, f.file_name, f.file_type
    FROM components c
    LEFT JOIN files f ON c.file_id = f.file_id
    WHERE c.component_type = 'FRONTEND_API' AND c.del_yn = 'N'
    LIMIT 5
""")
frontend_api_samples = cursor.fetchall()
for row in frontend_api_samples:
    print(f"  ID: {row[0]}, Name: '{row[1]}', File: {row[2]} ({row[3]} - {row[4]})")

print("\n5. API_ENTRY 컴포넌트 샘플 (최대 5개):")
cursor.execute("""
    SELECT c.component_id, c.component_name, c.file_id, f.file_name, f.file_type
    FROM components c
    LEFT JOIN files f ON c.file_id = f.file_id
    WHERE c.component_type = 'API_ENTRY' AND c.del_yn = 'N'
    LIMIT 5
""")
api_entry_samples = cursor.fetchall()
for row in api_entry_samples:
    print(f"  ID: {row[0]}, Name: '{row[1]}', File: {row[2]} ({row[3]} - {row[4]})")

print("\n6. CALL_METHOD 관계 샘플:")
cursor.execute("""
    SELECT 
        src_comp.component_type as src_type,
        src_comp.component_name as src_name,
        dst_comp.component_type as dst_type,
        dst_comp.component_name as dst_name
    FROM relationships r
    JOIN components src_comp ON r.src_id = src_comp.component_id
    JOIN components dst_comp ON r.dst_id = dst_comp.component_id
    WHERE r.rel_type = 'CALL_METHOD' AND r.del_yn = 'N'
    LIMIT 5
""")
call_method_samples = cursor.fetchall()
for row in call_method_samples:
    print(f"  {row[0]}: '{row[1]}' → {row[2]}: '{row[3]}'")

print("\n7. CALL_API_F2B 관계 샘플:")
cursor.execute("""
    SELECT 
        src_comp.component_type as src_type,
        src_comp.component_name as src_name,
        dst_comp.component_type as dst_type,
        dst_comp.component_name as dst_name
    FROM relationships r
    JOIN components src_comp ON r.src_id = src_comp.component_id
    JOIN components dst_comp ON r.dst_id = dst_comp.component_id
    WHERE r.rel_type = 'CALL_API_F2B' AND r.del_yn = 'N'
    LIMIT 5
""")
call_api_f2b_samples = cursor.fetchall()
for row in call_api_f2b_samples:
    print(f"  {row[0]}: '{row[1]}' → {row[2]}: '{row[3]}'")

print("\n8. 문제 있는 API_URL 이름들:")
cursor.execute("""
    SELECT component_name, COUNT(*) as count
    FROM components 
    WHERE component_type = 'API_URL' 
      AND del_yn = 'N'
      AND (component_name LIKE '/:%' OR component_name LIKE ':%' OR component_name = '/')
    GROUP BY component_name
    ORDER BY count DESC
""")
problematic_api_urls = cursor.fetchall()
for name, count in problematic_api_urls:
    print(f"  '{name}': {count}개")

conn.close()
