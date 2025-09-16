import sqlite3

conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== JSP 파일 확인 ===")

# JSP 파일들 조회
cursor.execute('SELECT file_id, file_name, file_type FROM files WHERE file_type = "JSP" LIMIT 5')
results = cursor.fetchall()
print("JSP 파일들:")
for file_id, file_name, file_type in results:
    print(f"  ID: {file_id}, Name: {file_name}, Type: {file_type}")

print("\n=== API_URL 컴포넌트와 연결된 파일 확인 ===")

# API_URL 컴포넌트와 연결된 파일들 조회
cursor.execute('''
    SELECT api_url.component_name, f.file_name, f.file_type, f.file_id
    FROM components api_url 
    JOIN files f ON api_url.file_id = f.file_id 
    WHERE api_url.component_type = "API_URL" 
    LIMIT 5
''')
results = cursor.fetchall()
print("API_URL과 연결된 파일들:")
for api_name, file_name, file_type, file_id in results:
    print(f"  API: {api_name} → File: {file_name} (Type: {file_type}, ID: {file_id})")

print("\n=== 해결 방안 ===")
print("API_URL 컴포넌트가 JSP 파일이 아닌 Java 파일과 연결되어 있습니다.")
print("backend_entry_loading.py에서 API_URL 생성 시 JSP 파일의 file_id를 사용해야 합니다.")

conn.close()
