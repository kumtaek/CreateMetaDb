import sqlite3

try:
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    # 컴포넌트 타입별 개수
    cursor.execute("SELECT component_type, COUNT(*) FROM components WHERE project_id = 1 AND del_yn = 'N' GROUP BY component_type ORDER BY COUNT(*) DESC")
    results = cursor.fetchall()
    
    print("=== 컴포넌트 타입별 개수 ===")
    for comp_type, count in results:
        print(f"{comp_type}: {count}개")
    
    # API 관련 컴포넌트 확인
    print("\n=== API 관련 컴포넌트 ===")
    cursor.execute("SELECT component_type, component_name, file_id FROM components WHERE project_id = 1 AND del_yn = 'N' AND component_type IN ('API_URL', 'FRONTEND_API', 'API_ENTRY') ORDER BY component_type, component_name")
    api_results = cursor.fetchall()
    
    if api_results:
        for comp_type, comp_name, file_id in api_results:
            print(f"{comp_type}: {comp_name} (file_id: {file_id})")
    else:
        print("API 관련 컴포넌트가 없습니다.")
    
    # 관계 타입별 개수
    print("\n=== 관계 타입별 개수 ===")
    cursor.execute("SELECT rel_type, COUNT(*) FROM relationships WHERE del_yn = 'N' GROUP BY rel_type ORDER BY COUNT(*) DESC")
    rel_results = cursor.fetchall()
    
    for rel_type, count in rel_results:
        print(f"{rel_type}: {count}개")
    
    conn.close()
    
except Exception as e:
    print(f"오류: {e}")
