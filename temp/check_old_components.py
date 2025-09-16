import sqlite3

conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== 1. 구버전 FRONTEND_API 컴포넌트 확인 ===")
cursor.execute("""
    SELECT c.component_id, c.component_name, c.file_id, f.file_name, f.file_type
    FROM components c
    LEFT JOIN files f ON c.file_id = f.file_id
    WHERE c.component_type = 'FRONTEND_API'
    ORDER BY c.component_name
""")
frontend_apis = cursor.fetchall()
print(f"총 FRONTEND_API 개수: {len(frontend_apis)}")
for row in frontend_apis:
    print(f" ID: {row[0]}, Name: '{row[1]}', File_ID: {row[2]}, File: {row[3]} ({row[4]})")

print("\n=== 2. 구버전 API_ENTRY 컴포넌트 확인 ===")
cursor.execute("""
    SELECT c.component_id, c.component_name, c.file_id, f.file_name, f.file_type
    FROM components c
    LEFT JOIN files f ON c.file_id = f.file_id
    WHERE c.component_type = 'API_ENTRY'
    ORDER BY c.component_name
""")
api_entries = cursor.fetchall()
print(f"총 API_ENTRY 개수: {len(api_entries)}")
for row in api_entries:
    print(f" ID: {row[0]}, Name: '{row[1]}', File_ID: {row[2]}, File: {row[3]} ({row[4]})")

print("\n=== 3. 구버전 FRONTEND_API → API_ENTRY 관계 확인 ===")
cursor.execute("""
    SELECT 
        fa.component_name as frontend_api,
        ae.component_name as api_entry,
        r.src_id, r.dst_id, r.del_yn
    FROM relationships r
    JOIN components fa ON r.src_id = fa.component_id AND fa.component_type = 'FRONTEND_API'
    JOIN components ae ON r.dst_id = ae.component_id AND ae.component_type = 'API_ENTRY'
    WHERE r.rel_type = 'CALL_API_F2B'
    ORDER BY fa.component_name
""")
f2b_relations = cursor.fetchall()
print(f"총 CALL_API_F2B 관계 개수: {len(f2b_relations)}")
for row in f2b_relations:
    print(f" FRONTEND_API: '{row[0]}' → API_ENTRY: '{row[1]}' (src: {row[2]}, dst: {row[3]}, del: {row[4]})")

print("\n=== 4. 구버전 API_ENTRY → METHOD 관계 확인 ===")
cursor.execute("""
    SELECT 
        ae.component_name as api_entry,
        method.component_name as method_name,
        r.src_id, r.dst_id, r.del_yn
    FROM relationships r
    JOIN components ae ON r.src_id = ae.component_id AND ae.component_type = 'API_ENTRY'
    JOIN components method ON r.dst_id = method.component_id AND method.component_type = 'METHOD'
    WHERE r.rel_type = 'CALL_METHOD'
    ORDER BY ae.component_name
""")
entry_method_relations = cursor.fetchall()
print(f"총 API_ENTRY → METHOD 관계 개수: {len(entry_method_relations)}")
for row in entry_method_relations:
    print(f" API_ENTRY: '{row[0]}' → METHOD: '{row[1]}' (src: {row[2]}, dst: {row[3]}, del: {row[4]})")

print("\n=== 5. 끊어진 API_ENTRY 찾기 (METHOD로 연결되지 않은 것들) ===")
cursor.execute("""
    SELECT 
        ae.component_id,
        ae.component_name,
        ae.file_id,
        f.file_name,
        f.file_type
    FROM components ae
    LEFT JOIN files f ON ae.file_id = f.file_id
    LEFT JOIN relationships r ON ae.component_id = r.src_id AND r.rel_type = 'CALL_METHOD' AND r.del_yn = 'N'
    WHERE ae.component_type = 'API_ENTRY'
      AND ae.del_yn = 'N'
      AND r.src_id IS NULL
    ORDER BY ae.component_name
""")
broken_api_entries = cursor.fetchall()
print(f"METHOD로 연결되지 않은 API_ENTRY 개수: {len(broken_api_entries)}")
for row in broken_api_entries:
    print(f" ID: {row[0]}, Name: '{row[1]}', File_ID: {row[2]}, File: {row[3]} ({row[4]})")

print("\n=== 6. 끊어진 FRONTEND_API 찾기 (API_ENTRY로 연결되지 않은 것들) ===")
cursor.execute("""
    SELECT 
        fa.component_id,
        fa.component_name,
        fa.file_id,
        f.file_name,
        f.file_type
    FROM components fa
    LEFT JOIN files f ON fa.file_id = f.file_id
    LEFT JOIN relationships r ON fa.component_id = r.src_id AND r.rel_type = 'CALL_API_F2B' AND r.del_yn = 'N'
    WHERE fa.component_type = 'FRONTEND_API'
      AND fa.del_yn = 'N'
      AND r.src_id IS NULL
    ORDER BY fa.component_name
""")
broken_frontend_apis = cursor.fetchall()
print(f"API_ENTRY로 연결되지 않은 FRONTEND_API 개수: {len(broken_frontend_apis)}")
for row in broken_frontend_apis:
    print(f" ID: {row[0]}, Name: '{row[1]}', File_ID: {row[2]}, File: {row[3]} ({row[4]})")

conn.close()
