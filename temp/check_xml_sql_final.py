import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

# XML 파일별 SQL 쿼리 수 확인
query = """
SELECT f.file_name, COUNT(c.component_id) as query_count 
FROM files f 
LEFT JOIN components c ON f.file_id = c.file_id AND c.component_type LIKE 'SQL_%' 
WHERE f.file_type = 'XML' 
GROUP BY f.file_id, f.file_name 
ORDER BY query_count DESC
"""

cursor.execute(query)
xml_files = cursor.fetchall()

print('XML 파일별 SQL 쿼리 수 (최종 수정 후):')
for file_name, count in xml_files:
    print(f'  {file_name}: {count}개')

# ProductMapper.xml 특별 확인
product_query = """
SELECT c.component_name, c.component_type 
FROM files f 
JOIN components c ON f.file_id = c.file_id 
WHERE f.file_name = 'ProductMapper.xml' AND c.component_type LIKE 'SQL_%'
"""

cursor.execute(product_query)
product_queries = cursor.fetchall()

print(f'\nProductMapper.xml의 SQL 쿼리들:')
for name, comp_type in product_queries:
    print(f'  - {name} ({comp_type})')

conn.close()
