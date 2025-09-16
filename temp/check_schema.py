import sqlite3

# 데이터베이스 스키마 확인
conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== components 테이블 컬럼 ===")
cursor.execute('PRAGMA table_info(components)')
columns = cursor.fetchall()
for col in columns:
    print(f" {col[1]} ({col[2]})")

print("\n=== METHOD 타입 컴포넌트 샘플 ===")
cursor.execute('SELECT component_id, component_name, parent_id FROM components WHERE component_type = "METHOD" LIMIT 3')
methods = cursor.fetchall()
for method in methods:
    print(f" ID: {method[0]}, Name: {method[1]}, Parent_ID: {method[2]}")

print("\n=== classes 테이블 확인 ===")
try:
    cursor.execute('PRAGMA table_info(classes)')
    class_columns = cursor.fetchall()
    print("classes 테이블 컬럼:")
    for col in class_columns:
        print(f" {col[1]} ({col[2]})")
except:
    print("classes 테이블이 존재하지 않습니다.")

conn.close()
