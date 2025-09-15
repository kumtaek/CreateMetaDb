import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== 프로젝트 정보 ===")
cursor.execute('SELECT project_name, project_path FROM projects')
results = cursor.fetchall()
for r in results:
    print(f'프로젝트명: {r[0]}')
    print(f'프로젝트 경로: {r[1]}')
    print()

print("=== 파일 정보 샘플 (처음 10개) ===")
cursor.execute('SELECT file_path, file_name FROM files LIMIT 10')
results = cursor.fetchall()
for r in results:
    print(f'파일 경로: {r[0]}')
    print(f'파일명: {r[1]}')
    print()

print("=== 파일 타입별 샘플 ===")
cursor.execute('SELECT DISTINCT file_type FROM files')
file_types = cursor.fetchall()
for ft in file_types:
    print(f'\n--- {ft[0]} 타입 파일 샘플 ---')
    cursor.execute('SELECT file_path, file_name FROM files WHERE file_type = ? LIMIT 3', (ft[0],))
    results = cursor.fetchall()
    for r in results:
        print(f'경로: {r[0]}, 파일명: {r[1]}')

conn.close()
