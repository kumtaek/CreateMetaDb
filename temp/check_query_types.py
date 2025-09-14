import sqlite3

def check_query_types():
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    print('=== QUERY vs SQL_% 타입 비교 ===')
    cursor.execute('''
        SELECT 'QUERY' as type, COUNT(*) as count
        FROM components 
        WHERE component_type = 'QUERY'
        UNION ALL
        SELECT 'SQL_SELECT' as type, COUNT(*) as count
        FROM components 
        WHERE component_type = 'SQL_SELECT'
        UNION ALL
        SELECT 'SQL_INSERT' as type, COUNT(*) as count
        FROM components 
        WHERE component_type = 'SQL_INSERT'
        UNION ALL
        SELECT 'SQL_UPDATE' as type, COUNT(*) as count
        FROM components 
        WHERE component_type = 'SQL_UPDATE'
        UNION ALL
        SELECT 'SQL_DELETE' as type, COUNT(*) as count
        FROM components 
        WHERE component_type = 'SQL_DELETE'
        UNION ALL
        SELECT 'SQL_MERGE' as type, COUNT(*) as count
        FROM components 
        WHERE component_type = 'SQL_MERGE'
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]}: {row[1]}개')
    
    print('\n=== QUERY 컴포넌트 샘플 ===')
    cursor.execute('''
        SELECT component_name, file_id
        FROM components 
        WHERE component_type = 'QUERY'
        LIMIT 10
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]} (file_id: {row[1]})')
    
    print('\n=== SQL_SELECT 컴포넌트 샘플 ===')
    cursor.execute('''
        SELECT component_name, file_id
        FROM components 
        WHERE component_type = 'SQL_SELECT'
        LIMIT 10
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]} (file_id: {row[1]})')
    
    print('\n=== METHOD -> SQL_% 연계 체인 샘플 ===')
    cursor.execute('''
        SELECT c1.component_name as method_name,
               f.file_name,
               c2.component_name as query_name,
               c2.component_type as query_type
        FROM relationships r1
        JOIN components c1 ON r1.src_id = c1.component_id
        JOIN components c2 ON r1.dst_id = c2.component_id
        JOIN files f ON c2.file_id = f.file_id
        WHERE r1.rel_type = 'CALL_QUERY'
          AND c1.component_type = 'METHOD'
          AND c2.component_type LIKE 'SQL_%'
        LIMIT 10
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]} -> {row[1]} -> {row[2]} ({row[3]})')
    
    conn.close()

if __name__ == '__main__':
    check_query_types()
