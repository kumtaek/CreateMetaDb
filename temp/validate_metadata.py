import sqlite3

conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== 1. API_URL 컴포넌트 상세 검증 ===")
cursor.execute("""
    SELECT c.component_id, c.component_name, c.file_id, c.del_yn, f.file_name, f.file_path
    FROM components c
    LEFT JOIN files f ON c.file_id = f.file_id
    WHERE c.component_type = 'API_URL'
    ORDER BY c.component_name
""")
api_urls_details = cursor.fetchall()
print(f"총 API_URL 개수: {len(api_urls_details)}")
for row in api_urls_details:
    print(f" ID: {row[0]}, Name: '{row[1]}', File_ID: {row[2]}, Del: {row[3]}")

print("\n=== 2. 문제 있는 API_URL 필터링 ===")
problematic_api_urls = [row for row in api_urls_details if row[1].strip() in ['/', '/:GET', '/:POST', '/:PUT', '/:DELETE', ':GET', ':POST', ':PUT', ':DELETE']]
print(f"문제 있는 API_URL들:")
for row in problematic_api_urls:
    print(f" - '{row[1]}' (ID: {row[0]})")

print("\n=== 3. API_URL과 연결된 파일 확인 ===")
cursor.execute("""
    SELECT 
        api_url.component_name, 
        f.file_name, 
        f.file_type,
        f.file_path
    FROM components api_url
    JOIN files f ON api_url.file_id = f.file_id
    WHERE api_url.component_type = 'API_URL'
    ORDER BY api_url.component_name
""")
api_files_details = cursor.fetchall()
for api_name, file_name, file_type, file_path in api_files_details:
    print(f" API: '{api_name}' → File: {file_name} ({file_type}) - {file_path}")

print("\n=== 4. CALL_METHOD 관계 상세 확인 ===")
cursor.execute("""
    SELECT 
        api_url.component_name as api_name,
        method.component_name as method_name,
        r.src_id, r.dst_id, r.del_yn
    FROM relationships r
    JOIN components api_url ON r.src_id = api_url.component_id AND api_url.component_type = 'API_URL'
    JOIN components method ON r.dst_id = method.component_id AND method.component_type = 'METHOD'
    WHERE r.rel_type = 'CALL_METHOD'
    ORDER BY api_url.component_name
""")
call_method_details = cursor.fetchall()
print(f"총 CALL_METHOD 관계 개수: {len(call_method_details)}")
for row in call_method_details:
    print(f" API: '{row[0]}' → METHOD: {row[1]} (src: {row[2]}, dst: {row[3]}, del: {row[4]})")

print("\n=== 5. METHOD → SQL 관계 확인 ===")
cursor.execute("""
    SELECT 
        method.component_name as method_name,
        sql_comp.component_name as sql_name,
        sql_comp.component_type as sql_type,
        r.del_yn
    FROM relationships r
    JOIN components method ON r.src_id = method.component_id AND method.component_type = 'METHOD'
    JOIN components sql_comp ON r.dst_id = sql_comp.component_id AND sql_comp.component_type LIKE 'SQL_%'
    WHERE r.rel_type = 'CALL_QUERY'
    ORDER BY method.component_name
""")
call_query_details = cursor.fetchall()
print(f"총 CALL_QUERY 관계 개수: {len(call_query_details)}")
for row in call_query_details:
    print(f" METHOD: {row[0]} → SQL: {row[1]} ({row[2]}, del: {row[3]})")

print("\n=== 6. SQL → TABLE 관계 확인 ===")
cursor.execute("""
    SELECT 
        sql_comp.component_name as sql_name,
        tbl.table_name,
        r.del_yn
    FROM relationships r
    JOIN components sql_comp ON r.src_id = sql_comp.component_id AND sql_comp.component_type LIKE 'SQL_%'
    JOIN tables tbl ON r.dst_id = tbl.component_id
    WHERE r.rel_type = 'USE_TABLE'
    ORDER BY sql_comp.component_name
""")
use_table_details = cursor.fetchall()
print(f"총 USE_TABLE 관계 개수: {len(use_table_details)}")
for row in use_table_details:
    print(f" SQL: {row[0]} → TABLE: {row[1]} (del: {row[2]})")

print("\n=== 7. 완전한 체인 존재 여부 확인 ===")
cursor.execute("""
    SELECT COUNT(DISTINCT api_url.component_id)
    FROM components api_url
    JOIN relationships r1 ON api_url.component_id = r1.src_id AND r1.rel_type = 'CALL_METHOD'
    JOIN components method ON r1.dst_id = method.component_id
    JOIN relationships r2 ON method.component_id = r2.src_id AND r2.rel_type = 'CALL_QUERY'
    JOIN components sql_comp ON r2.dst_id = sql_comp.component_id
    LEFT JOIN relationships r3 ON sql_comp.component_id = r3.src_id AND r3.rel_type = 'USE_TABLE'
    WHERE api_url.component_type = 'API_URL'
      AND method.component_type = 'METHOD'
      AND sql_comp.component_type LIKE 'SQL_%'
      AND api_url.del_yn = 'N'
      AND method.del_yn = 'N'
      AND sql_comp.del_yn = 'N'
      AND r1.del_yn = 'N'
      AND r2.del_yn = 'N'
""")
full_chain_count = cursor.fetchone()[0]
print(f"완전한 체인 개수: {full_chain_count}")

conn.close()