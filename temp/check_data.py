import sqlite3

def check_data():
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    print('=== CallChain 연계 데이터 샘플 ===')
    cursor.execute('''
        SELECT c1.component_name as class_name, 
               c2.component_name as method_name, 
               f.file_name as xml_file, 
               c3.component_name as query_id, 
               c3.component_type as query_type 
        FROM components c1 
        JOIN components c2 ON c1.component_id = c2.parent_id 
        JOIN relationships r ON c2.component_id = r.src_id 
        JOIN components c3 ON r.dst_id = c3.component_id 
        JOIN files f ON c3.file_id = f.file_id 
        WHERE c1.component_type = "CLASS" 
          AND c2.component_type = "METHOD" 
          AND c3.component_type LIKE "SQL_%" 
        LIMIT 5
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]} -> {row[1]} -> {row[2]} -> {row[3]} ({row[4]})')
    
    print('\n=== 테이블별 컬럼 정보 샘플 ===')
    cursor.execute('''
        SELECT t.table_name, COUNT(c.column_id) as column_count 
        FROM tables t 
        LEFT JOIN columns c ON t.table_id = c.table_id 
        GROUP BY t.table_id, t.table_name 
        LIMIT 5
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]}: {row[1]}개 컬럼')
    
    print('\n=== 조인 관계 샘플 ===')
    cursor.execute('''
        SELECT r.rel_type, 
               t1.table_name as src_table, 
               t2.table_name as dst_table
        FROM relationships r
        JOIN tables t1 ON r.src_id = t1.component_id
        JOIN tables t2 ON r.dst_id = t2.component_id
        WHERE r.rel_type LIKE "JOIN_%"
        LIMIT 5
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]}: {row[1]} -> {row[2]}')
    
    conn.close()

if __name__ == '__main__':
    check_data()
