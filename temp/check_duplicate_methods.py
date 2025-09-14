import sqlite3

def check_duplicate_methods():
    try:
        conn = sqlite3.connect('projects/sampleSrc/metadata.db')
        cursor = conn.cursor()
        
        # 같은 이름의 METHOD 컴포넌트가 여러 개 있는지 확인
        cursor.execute('''
            SELECT component_name, COUNT(*) as count, GROUP_CONCAT(component_id) as ids
            FROM components 
            WHERE component_type = 'METHOD'
            GROUP BY component_name
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        ''')
        duplicates = cursor.fetchall()
        
        if duplicates:
            print('중복된 METHOD 컴포넌트들:')
            for dup in duplicates:
                print(f'  Name: {dup[0]}, Count: {dup[1]}, IDs: {dup[2]}')
        else:
            print('중복된 METHOD 컴포넌트가 없습니다.')
        
        # inferred 메서드들 확인
        cursor.execute('''
            SELECT component_id, component_name, file_id
            FROM components 
            WHERE component_type = 'METHOD' AND component_name IN ('isEmpty', 'for', 'size', 'get', 'set')
            ORDER BY component_name, component_id
        ''')
        inferred_methods = cursor.fetchall()
        
        print(f'\ninferred 메서드들:')
        for method in inferred_methods:
            print(f'  ID: {method[0]}, Name: {method[1]}, File_ID: {method[2]}')
        
        # CALL_METHOD 관계에서 src_id == dst_id인 경우 확인
        cursor.execute('''
            SELECT r.src_id, r.dst_id, r.rel_type, 
                   c1.component_name as src_name, c2.component_name as dst_name
            FROM relationships r
            JOIN components c1 ON r.src_id = c1.component_id
            JOIN components c2 ON r.dst_id = c2.component_id
            WHERE r.src_id = r.dst_id
        ''')
        same_relationships = cursor.fetchall()
        
        if same_relationships:
            print(f'\nsrc_id == dst_id인 관계들:')
            for rel in same_relationships:
                print(f'  src_id: {rel[0]}, dst_id: {rel[1]}, type: {rel[2]}, src_name: {rel[3]}, dst_name: {rel[4]}')
        else:
            print(f'\nsrc_id == dst_id인 관계가 없습니다.')
        
        conn.close()
        
    except Exception as e:
        print(f'에러 발생: {e}')

if __name__ == '__main__':
    check_duplicate_methods()
