import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== 프로젝트 경로 샘플 ===")
cursor.execute('SELECT project_path FROM projects LIMIT 5')
results = cursor.fetchall()
for r in results:
    print(f'프로젝트 경로: {r[0]}')

print("\n=== 파일 경로 샘플 ===")
cursor.execute('SELECT file_path FROM files LIMIT 10')
results = cursor.fetchall()
for r in results:
    print(f'파일 경로: {r[0]}')

print("\n=== 프로젝트명과 경로 ===")
cursor.execute('SELECT project_name, project_path FROM projects')
results = cursor.fetchall()
for r in results:
    print(f'프로젝트명: {r[0]}, 경로: {r[1]}')

conn.close()
