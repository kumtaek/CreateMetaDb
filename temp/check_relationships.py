import sqlite3

def check_relationships():
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    print('=== 관계 타입별 현황 ===')
    cursor.execute('''
        SELECT rel_type, COUNT(*) as count
        FROM relationships 
        GROUP BY rel_type 
        ORDER BY count DESC
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]}: {row[1]}개')
    
    print('\n=== 관계 데이터 샘플 ===')
    cursor.execute('''
        SELECT r.rel_type,
               c1.component_name as src_name,
               c1.component_type as src_type,
               c2.component_name as dst_name,
               c2.component_type as dst_type
        FROM relationships r
        JOIN components c1 ON r.src_id = c1.component_id
        JOIN components c2 ON r.dst_id = c2.component_id
        LIMIT 10
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]}: {row[1]}({row[2]}) -> {row[3]}({row[4]})')
    
    print('\n=== 테이블 조인 관계 샘플 ===')
    cursor.execute('''
        SELECT r.rel_type,
               t1.table_name as src_table,
               t2.table_name as dst_table
        FROM relationships r
        JOIN tables t1 ON r.src_id = t1.component_id
        JOIN tables t2 ON r.dst_id = t2.component_id
        LIMIT 10
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]}: {row[1]} -> {row[2]}')
    
    conn.close()

if __name__ == '__main__':
    check_relationships()
