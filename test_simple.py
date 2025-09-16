import sqlite3

conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== 단계별 JOIN 테스트 ===")

# 1단계: API_URL 컴포넌트만 확인
print("\n1. API_URL 컴포넌트:")
cursor.execute('SELECT component_id, component_name, file_id FROM components WHERE component_type = "API_URL" LIMIT 3')
results = cursor.fetchall()
for comp_id, comp_name, file_id in results:
    print(f"  ID: {comp_id}, Name: {comp_name}, File_ID: {file_id}")

# 2단계: API_URL + JSP 파일 JOIN
print("\n2. API_URL + JSP 파일 JOIN:")
cursor.execute('''
    SELECT api_url.component_name, jsp_file.file_name, jsp_file.file_type 
    FROM components api_url 
    JOIN files jsp_file ON api_url.file_id = jsp_file.file_id 
    WHERE api_url.component_type = "API_URL" 
    LIMIT 3
''')
results = cursor.fetchall()
for api_name, file_name, file_type in results:
    print(f"  API: {api_name}, File: {file_name}, Type: {file_type}")

# 3단계: API_URL + CALL_METHOD 관계
print("\n3. API_URL + CALL_METHOD 관계:")
cursor.execute('''
    SELECT api_url.component_name, r.rel_type 
    FROM components api_url 
    JOIN relationships r ON api_url.component_id = r.src_id 
    WHERE api_url.component_type = "API_URL" AND r.rel_type = "CALL_METHOD" 
    LIMIT 3
''')
results = cursor.fetchall()
for api_name, rel_type in results:
    print(f"  API: {api_name}, Relation: {rel_type}")

# 4단계: API_URL + METHOD 컴포넌트
print("\n4. API_URL + METHOD 컴포넌트:")
cursor.execute('''
    SELECT api_url.component_name, method.component_name 
    FROM components api_url 
    JOIN relationships r ON api_url.component_id = r.src_id 
    JOIN components method ON r.dst_id = method.component_id 
    WHERE api_url.component_type = "API_URL" AND method.component_type = "METHOD" AND r.rel_type = "CALL_METHOD" 
    LIMIT 3
''')
results = cursor.fetchall()
for api_name, method_name in results:
    print(f"  API: {api_name} → Method: {method_name}")

conn.close()
