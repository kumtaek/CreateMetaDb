import sqlite3

conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== 1. API_URL 컴포넌트 확인 ===")
cursor.execute('SELECT component_id, component_name, file_id FROM components WHERE component_type = "API_URL" LIMIT 5')
api_urls = cursor.fetchall()
for api_url in api_urls:
    print(f" API_URL: {api_url[1]}, File_ID: {api_url[2]}")

print("\n=== 2. API_URL과 연결된 파일 확인 ===")
cursor.execute('''
    SELECT api_url.component_name, f.file_name, f.file_type 
    FROM components api_url 
    JOIN files f ON api_url.file_id = f.file_id 
    WHERE api_url.component_type = "API_URL" 
    LIMIT 5
''')
api_files = cursor.fetchall()
for api_file in api_files:
    print(f" API: {api_file[0]} → File: {api_file[1]} ({api_file[2]})")

print("\n=== 3. CALL_METHOD 관계 확인 ===")
cursor.execute('SELECT src_id, dst_id FROM relationships WHERE rel_type = "CALL_METHOD" LIMIT 5')
call_methods = cursor.fetchall()
for rel in call_methods:
    print(f" {rel[0]} → {rel[1]}")

print("\n=== 4. METHOD 컴포넌트 확인 ===")
cursor.execute('SELECT component_id, component_name, parent_id FROM components WHERE component_type = "METHOD" LIMIT 5')
methods = cursor.fetchall()
for method in methods:
    print(f" METHOD: {method[1]}, Parent_ID: {method[2]}")

print("\n=== 5. CLASSES 테이블 확인 ===")
try:
    cursor.execute('SELECT class_id, class_name FROM classes LIMIT 5')
    classes = cursor.fetchall()
    for cls in classes:
        print(f" CLASS: {cls[1]}, ID: {cls[0]}")
except Exception as e:
    print(f" CLASSES 테이블 오류: {e}")

print("\n=== 6. API_URL → METHOD 연결 테스트 ===")
cursor.execute('''
    SELECT 
        api_url.component_name as api_name,
        method.component_name as method_name
    FROM components api_url
    JOIN relationships r1 ON api_url.component_id = r1.src_id AND r1.rel_type = 'CALL_METHOD'
    JOIN components method ON r1.dst_id = method.component_id
    WHERE api_url.component_type = 'API_URL'
    LIMIT 3
''')
api_methods = cursor.fetchall()
for am in api_methods:
    print(f" API: {am[0]} → METHOD: {am[1]}")

conn.close()
