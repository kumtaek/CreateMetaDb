import sqlite3

def check_real_chain():
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    print('=== 실제 연계 체인 데이터 ===')
    
    # 1. METHOD -> QUERY 관계
    print('\n1. METHOD -> QUERY 관계:')
    cursor.execute('''
        SELECT c1.component_name as method_name,
               c2.component_name as query_name,
               c2.component_type as query_type
        FROM relationships r
        JOIN components c1 ON r.src_id = c1.component_id
        JOIN components c2 ON r.dst_id = c2.component_id
        WHERE r.rel_type = 'CALL_QUERY'
          AND c1.component_type = 'METHOD'
        LIMIT 5
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]} -> {row[1]} ({row[2]})')
    
    # 2. QUERY -> TABLE 관계 (QUERY_TABLE 타입)
    print('\n2. QUERY -> TABLE 관계:')
    cursor.execute('''
        SELECT c1.component_name as query_name,
               t.table_name,
               r.rel_type
        FROM relationships r
        JOIN components c1 ON r.src_id = c1.component_id
        JOIN tables t ON r.dst_id = t.component_id
        WHERE r.rel_type = 'QUERY_TABLE'
        LIMIT 5
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]} -> {row[1]} ({row[2]})')
    
    # 3. 전체 연계 체인 (METHOD -> QUERY -> TABLE)
    print('\n3. 전체 연계 체인 (METHOD -> QUERY -> TABLE):')
    cursor.execute('''
        SELECT m.component_name as method_name,
               f1.file_name as xml_file,
               q.component_name as query_name,
               q.component_type as query_type,
               t.table_name
        FROM relationships r1
        JOIN components m ON r1.src_id = m.component_id
        JOIN components q ON r1.dst_id = q.component_id
        JOIN files f1 ON q.file_id = f1.file_id
        JOIN relationships r2 ON q.component_id = r2.src_id
        JOIN tables t ON r2.dst_id = t.component_id
        WHERE r1.rel_type = 'CALL_QUERY'
          AND r2.rel_type = 'QUERY_TABLE'
          AND m.component_type = 'METHOD'
        LIMIT 10
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]} -> {row[1]} -> {row[2]} ({row[3]}) -> {row[4]}')
    
    # 4. 클래스 정보 포함
    print('\n4. 클래스 정보 포함 연계 체인:')
    cursor.execute('''
        SELECT cls.component_name as class_name,
               m.component_name as method_name,
               f1.file_name as xml_file,
               q.component_name as query_name,
               q.component_type as query_type,
               t.table_name
        FROM relationships r1
        JOIN components m ON r1.src_id = m.component_id
        JOIN components cls ON m.parent_id = cls.component_id
        JOIN components q ON r1.dst_id = q.component_id
        JOIN files f1 ON q.file_id = f1.file_id
        JOIN relationships r2 ON q.component_id = r2.src_id
        JOIN tables t ON r2.dst_id = t.component_id
        WHERE r1.rel_type = 'CALL_QUERY'
          AND r2.rel_type = 'QUERY_TABLE'
          AND m.component_type = 'METHOD'
          AND cls.component_type = 'CLASS'
        LIMIT 10
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]} -> {row[1]} -> {row[2]} -> {row[3]} ({row[4]}) -> {row[5]}')
    
    conn.close()

if __name__ == '__main__':
    check_real_chain()
