import sqlite3

def check_all_relations():
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    print('=== 모든 관계 타입별 상세 현황 ===')
    cursor.execute('''
        SELECT rel_type, COUNT(*) as count
        FROM relationships 
        GROUP BY rel_type 
        ORDER BY count DESC
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]}: {row[1]}개')
    
    print('\n=== CALL_QUERY 관계 상세 분석 ===')
    cursor.execute('''
        SELECT c1.component_type as src_type,
               c2.component_type as dst_type,
               COUNT(*) as count
        FROM relationships r
        JOIN components c1 ON r.src_id = c1.component_id
        JOIN components c2 ON r.dst_id = c2.component_id
        WHERE r.rel_type = 'CALL_QUERY'
        GROUP BY c1.component_type, c2.component_type
        ORDER BY count DESC
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]} -> {row[1]}: {row[2]}개')
    
    print('\n=== QUERY와 TABLE의 관계 확인 ===')
    cursor.execute('''
        SELECT DISTINCT r.rel_type
        FROM relationships r
        JOIN components c1 ON r.src_id = c1.component_id
        JOIN components c2 ON r.dst_id = c2.component_id
        WHERE (c1.component_type LIKE 'SQL_%' OR c1.component_type = 'QUERY')
           OR (c2.component_type LIKE 'SQL_%' OR c2.component_type = 'QUERY')
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]}')
    
    print('\n=== TABLE과 관련된 모든 관계 ===')
    cursor.execute('''
        SELECT r.rel_type,
               c1.component_name as src_name,
               c1.component_type as src_type,
               c2.component_name as dst_name,
               c2.component_type as dst_type
        FROM relationships r
        JOIN components c1 ON r.src_id = c1.component_id
        JOIN components c2 ON r.dst_id = c2.component_id
        WHERE c1.component_type = 'TABLE' OR c2.component_type = 'TABLE'
        LIMIT 10
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]}: {row[1]}({row[2]}) -> {row[3]}({row[4]})')
    
    conn.close()

if __name__ == '__main__':
    check_all_relations()
