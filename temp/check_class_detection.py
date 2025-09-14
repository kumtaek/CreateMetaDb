import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

# 클래스 검출 건수 확인
query = """
SELECT 
    COUNT(*) as total_classes,
    COUNT(CASE WHEN has_error = 'Y' THEN 1 END) as error_classes,
    COUNT(CASE WHEN has_error = 'N' THEN 1 END) as success_classes
FROM classes 
WHERE del_yn = 'N'
"""

cursor.execute(query)
result = cursor.fetchone()

print(f'총 클래스 수: {result[0]}개')
print(f'성공한 클래스: {result[2]}개')
print(f'에러 클래스: {result[1]}개')

# 파일별 클래스 검출 현황
file_query = """
SELECT 
    f.file_name,
    COUNT(c.class_id) as class_count,
    COUNT(CASE WHEN c.has_error = 'Y' THEN 1 END) as error_count
FROM files f
LEFT JOIN classes c ON f.file_id = c.file_id AND c.del_yn = 'N'
WHERE f.file_type = 'JAVA' AND f.del_yn = 'N'
GROUP BY f.file_id, f.file_name
ORDER BY class_count DESC
"""

cursor.execute(file_query)
file_results = cursor.fetchall()

print(f'\n파일별 클래스 검출 현황:')
for file_name, class_count, error_count in file_results:
    print(f'  {file_name}: {class_count}개 (에러: {error_count}개)')

conn.close()
