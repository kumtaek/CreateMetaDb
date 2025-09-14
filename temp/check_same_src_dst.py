import sqlite3

def check_same_src_dst():
    try:
        conn = sqlite3.connect('projects/sampleSrc/metadata.db')
        cursor = conn.cursor()
        
        # src_id == dst_id인 관계들 확인
        cursor.execute('''
            SELECT src_id, dst_id, rel_type, COUNT(*) as count 
            FROM relationships 
            WHERE src_id = dst_id 
            GROUP BY src_id, dst_id, rel_type
        ''')
        results = cursor.fetchall()
        
        if results:
            print('src_id == dst_id인 관계들:')
            for row in results:
                print(f'  src_id: {row[0]}, dst_id: {row[1]}, rel_type: {row[2]}, count: {row[3]}')
        else:
            print('src_id == dst_id인 관계가 없습니다.')
        
        # 전체 관계 수 확인
        cursor.execute('SELECT COUNT(*) FROM relationships')
        total_count = cursor.fetchone()[0]
        print(f'전체 관계 수: {total_count}')
        
        # 컴포넌트 정보도 확인
        cursor.execute('''
            SELECT c.component_id, c.component_name, c.component_type, COUNT(r.src_id) as src_count, COUNT(r.dst_id) as dst_count
            FROM components c
            LEFT JOIN relationships r ON c.component_id = r.src_id OR c.component_id = r.dst_id
            GROUP BY c.component_id, c.component_name, c.component_type
            HAVING src_count > 0 OR dst_count > 0
            ORDER BY c.component_id
        ''')
        components = cursor.fetchall()
        
        print(f'\n컴포넌트별 관계 수:')
        for comp in components[:10]:  # 처음 10개만 출력
            print(f'  ID: {comp[0]}, Name: {comp[1]}, Type: {comp[2]}, src_count: {comp[3]}, dst_count: {comp[4]}')
        
        conn.close()
        
    except Exception as e:
        print(f'에러 발생: {e}')

if __name__ == '__main__':
    check_same_src_dst()
