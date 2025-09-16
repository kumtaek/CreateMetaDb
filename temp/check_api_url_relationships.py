import sqlite3

conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== API_URL → METHOD 관계 확인 ===")

print("\n1. API_URL → METHOD 관계 개수:")
cursor.execute("""
    SELECT COUNT(*)
    FROM relationships r
    JOIN components api_url ON r.src_id = api_url.component_id AND api_url.component_type = 'API_URL'
    JOIN components method ON r.dst_id = method.component_id AND method.component_type = 'METHOD'
    WHERE r.rel_type = 'CALL_METHOD' AND r.del_yn = 'N'
""")
api_to_method_count = cursor.fetchone()[0]
print(f"  API_URL → METHOD 관계: {api_to_method_count}개")

print("\n2. API_URL → METHOD 관계 샘플:")
cursor.execute("""
    SELECT 
        api_url.component_name as api_name,
        method.component_name as method_name,
        api_url.file_id as api_file_id,
        f.file_name as api_file_name,
        method.file_id as method_file_id,
        mf.file_name as method_file_name
    FROM relationships r
    JOIN components api_url ON r.src_id = api_url.component_id AND api_url.component_type = 'API_URL'
    JOIN components method ON r.dst_id = method.component_id AND method.component_type = 'METHOD'
    JOIN files f ON api_url.file_id = f.file_id
    JOIN files mf ON method.file_id = mf.file_id
    WHERE r.rel_type = 'CALL_METHOD' AND r.del_yn = 'N'
    LIMIT 5
""")
api_to_method_samples = cursor.fetchall()
for row in api_to_method_samples:
    print(f"  API: '{row[0]}' (File: {row[3]}) → METHOD: '{row[1]}' (File: {row[5]})")

print("\n3. METHOD → METHOD 관계 개수 (현재 잘못된 관계들):")
cursor.execute("""
    SELECT COUNT(*)
    FROM relationships r
    JOIN components src_method ON r.src_id = src_method.component_id AND src_method.component_type = 'METHOD'
    JOIN components dst_method ON r.dst_id = dst_method.component_id AND dst_method.component_type = 'METHOD'
    WHERE r.rel_type = 'CALL_METHOD' AND r.del_yn = 'N'
""")
method_to_method_count = cursor.fetchone()[0]
print(f"  METHOD → METHOD 관계: {method_to_method_count}개")

print("\n4. METHOD → METHOD 관계 샘플:")
cursor.execute("""
    SELECT 
        src_method.component_name as src_method_name,
        dst_method.component_name as dst_method_name
    FROM relationships r
    JOIN components src_method ON r.src_id = src_method.component_id AND src_method.component_type = 'METHOD'
    JOIN components dst_method ON r.dst_id = dst_method.component_id AND dst_method.component_type = 'METHOD'
    WHERE r.rel_type = 'CALL_METHOD' AND r.del_yn = 'N'
    LIMIT 5
""")
method_to_method_samples = cursor.fetchall()
for row in method_to_method_samples:
    print(f"  METHOD: '{row[0]}' → METHOD: '{row[1]}'")

print("\n5. 연결되지 않은 API_URL 개수:")
cursor.execute("""
    SELECT COUNT(DISTINCT api_url.component_id)
    FROM components api_url
    LEFT JOIN relationships r ON api_url.component_id = r.src_id AND r.rel_type = 'CALL_METHOD' AND r.del_yn = 'N'
    WHERE api_url.component_type = 'API_URL' 
      AND api_url.del_yn = 'N'
      AND r.src_id IS NULL
""")
unconnected_api_count = cursor.fetchone()[0]
print(f"  연결되지 않은 API_URL: {unconnected_api_count}개")

print("\n6. 연결되지 않은 API_URL 샘플:")
cursor.execute("""
    SELECT 
        api_url.component_name,
        f.file_name,
        f.file_type
    FROM components api_url
    LEFT JOIN files f ON api_url.file_id = f.file_id
    LEFT JOIN relationships r ON api_url.component_id = r.src_id AND r.rel_type = 'CALL_METHOD' AND r.del_yn = 'N'
    WHERE api_url.component_type = 'API_URL' 
      AND api_url.del_yn = 'N'
      AND r.src_id IS NULL
    LIMIT 5
""")
unconnected_api_samples = cursor.fetchall()
for row in unconnected_api_samples:
    print(f"  API: '{row[0]}' → File: {row[1]} ({row[2]})")

conn.close()
