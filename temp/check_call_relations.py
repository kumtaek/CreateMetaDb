import sqlite3

def check_call_relations():
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    print('=== CALL_METHOD 관계 샘플 ===')
    cursor.execute('''
        SELECT c1.component_name as src_method,
               c1.component_type as src_type,
               c2.component_name as dst_method,
               c2.component_type as dst_type
        FROM relationships r
        JOIN components c1 ON r.src_id = c1.component_id
        JOIN components c2 ON r.dst_id = c2.component_id
        WHERE r.rel_type = 'CALL_METHOD'
        LIMIT 10
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]}({row[1]}) -> {row[2]}({row[3]})')
    
    print('\n=== CALL_QUERY 관계 샘플 ===')
    cursor.execute('''
        SELECT c1.component_name as src_component,
               c1.component_type as src_type,
               c2.component_name as dst_query,
               c2.component_type as dst_type
        FROM relationships r
        JOIN components c1 ON r.src_id = c1.component_id
        JOIN components c2 ON r.dst_id = c2.component_id
        WHERE r.rel_type = 'CALL_QUERY'
        LIMIT 10
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]}({row[1]}) -> {row[2]}({row[3]})')
    
    print('\n=== METHOD -> QUERY 연계 체인 샘플 ===')
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
    check_call_relations()
