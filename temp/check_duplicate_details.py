import sqlite3

def check_duplicate_details():
    try:
        conn = sqlite3.connect('projects/sampleSrc/metadata.db')
        cursor = conn.cursor()
        
        # createUser 메서드의 상세 정보 확인
        cursor.execute('''
            SELECT c.component_id, c.component_name, c.file_id, f.file_name, f.file_path
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            WHERE c.component_name = 'createUser' AND c.component_type = 'METHOD'
            ORDER BY c.component_id
        ''')
        createUser_methods = cursor.fetchall()
        
        print('createUser 메서드 상세 정보:')
        for method in createUser_methods:
            print(f'  ID: {method[0]}, Name: {method[1]}, File_ID: {method[2]}, File: {method[3]}, Path: {method[4]}')
        
        # 파일별 메서드 수 확인
        cursor.execute('''
            SELECT f.file_name, COUNT(c.component_id) as method_count
            FROM files f
            LEFT JOIN components c ON f.file_id = c.file_id AND c.component_type = 'METHOD'
            WHERE f.file_type = 'JAVA'
            GROUP BY f.file_id, f.file_name
            ORDER BY method_count DESC
        ''')
        file_methods = cursor.fetchall()
        
        print(f'\n파일별 메서드 수:')
        for file_info in file_methods:
            print(f'  File: {file_info[0]}, Methods: {file_info[1]}')
        
        # inferred 메서드들 확인 (file_id = 4인 것들)
        cursor.execute('''
            SELECT c.component_id, c.component_name, c.file_id, f.file_name
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            WHERE c.file_id = 4 AND c.component_type = 'METHOD'
            ORDER BY c.component_name
        ''')
        inferred_methods = cursor.fetchall()
        
        print(f'\ninferred 메서드들 (file_id = 4):')
        for method in inferred_methods:
            print(f'  ID: {method[0]}, Name: {method[1]}, File_ID: {method[2]}, File: {method[3]}')
        
        conn.close()
        
    except Exception as e:
        print(f'에러 발생: {e}')

if __name__ == '__main__':
    check_duplicate_details()
