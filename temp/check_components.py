import sqlite3

def check_components():
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    print('=== 컴포넌트 타입별 현황 ===')
    cursor.execute('''
        SELECT component_type, COUNT(*) as count
        FROM components 
        GROUP BY component_type 
        ORDER BY count DESC
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]}: {row[1]}개')
    
    print('\n=== CLASS와 METHOD 관계 샘플 ===')
    cursor.execute('''
        SELECT c1.component_name as class_name, 
               c2.component_name as method_name
        FROM components c1 
        JOIN components c2 ON c1.component_id = c2.parent_id 
        WHERE c1.component_type = "CLASS" 
          AND c2.component_type = "METHOD"
        LIMIT 5
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]} -> {row[1]}')
    
    print('\n=== METHOD와 SQL 관계 샘플 ===')
    cursor.execute('''
        SELECT c1.component_name as method_name, 
               c2.component_name as sql_name,
               c2.component_type as sql_type
        FROM components c1 
        JOIN relationships r ON c1.component_id = r.src_id 
        JOIN components c2 ON r.dst_id = c2.component_id 
        WHERE c1.component_type = "METHOD" 
          AND c2.component_type LIKE "SQL_%"
        LIMIT 5
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]} -> {row[1]} ({row[2]})')
    
    print('\n=== SQL과 TABLE 관계 샘플 ===')
    cursor.execute('''
        SELECT c1.component_name as sql_name, 
               t.table_name,
               r.rel_type
        FROM components c1 
        JOIN relationships r ON c1.component_id = r.src_id 
        JOIN tables t ON r.dst_id = t.component_id 
        WHERE c1.component_type LIKE "SQL_%"
        LIMIT 5
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f'  {row[0]} -> {row[1]} ({row[2]})')
    
    conn.close()

if __name__ == '__main__':
    check_components()
