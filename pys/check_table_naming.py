"""
테이블명 점(.) vs 언더스코어(_) 혼용 케이스 조사
"""
import sqlite3

def check_table_naming_conflicts():
    conn = sqlite3.connect('D:/Analyzer/CreateMetaDb/projects/sampleSrc/metadata.db')
    cursor = conn.cursor()

    print('=' * 80)
    print('NP.XXX vs NP_XXX 형식 테이블명 혼용 조사')
    print('=' * 80)
    print()

    # 1. components에서 점(.)이 포함된 테이블명 찾기
    print('[1] components 테이블에서 점(.) 포함 테이블명')
    cursor.execute("""
        SELECT component_id, component_name, component_type
        FROM components
        WHERE component_type = 'TABLE'
          AND component_name LIKE '%.%'
        ORDER BY component_name
        LIMIT 20
    """)
    dot_tables = cursor.fetchall()
    print(f'총 {len(dot_tables)}개')
    for row in dot_tables[:10]:
        print(f'  {row[0]:4d} | {row[1]:40s} | {row[2]}')

    print()
    print('[2] 유사한 이름으로 점(.)과 언더스코어(_) 동시 존재 여부')
    # 점(.)을 언더스코어(_)로 치환했을 때 동일한 이름이 있는지 확인
    cursor.execute("""
        SELECT
            c1.component_name as dot_name,
            c2.component_name as underscore_name,
            c1.component_id as dot_id,
            c2.component_id as underscore_id
        FROM components c1
        JOIN components c2
            ON REPLACE(c1.component_name, '.', '_') = c2.component_name
            AND c1.component_id != c2.component_id
        WHERE c1.component_type = 'TABLE'
          AND c2.component_type = 'TABLE'
          AND c1.component_name LIKE '%.%'
        LIMIT 10
    """)
    conflicts = cursor.fetchall()
    print(f'총 {len(conflicts)}개 충돌')
    if conflicts:
        for row in conflicts:
            print(f'  {row[0]:30s} (id={row[2]}) <-> {row[1]:30s} (id={row[3]})')
    else:
        print('  충돌 없음 (현재 sampleSrc에서는 발생하지 않음)')

    # 3. relationships에서 점(.)과 언더스코어(_) 혼용 사례 찾기
    print()
    print('[3] relationships에서 테이블명 정규화 필요 사례')
    cursor.execute("""
        SELECT
            src.component_name AS src_table,
            dst.component_name AS dst_table,
            r.rel_type,
            r.join_condition
        FROM relationships r
        JOIN components src ON r.src_id = src.component_id
        JOIN components dst ON r.dst_id = dst.component_id
        WHERE (src.component_name LIKE '%.%' OR dst.component_name LIKE '%.%')
          AND r.rel_type LIKE 'JOIN_%'
          AND r.del_yn = 'N'
        LIMIT 10
    """)
    rel_with_dots = cursor.fetchall()
    print(f'총 {len(rel_with_dots)}개 관계에서 점(.) 형식 사용')
    for row in rel_with_dots[:5]:
        print(f'  {row[0]:25s} - {row[1]:25s} [{row[2]}]')
        print(f'    조건: {row[3] or "N/A"}')

    # 4. USE_TABLE 관계 중복 상세 조사
    print()
    print('[4] USE_TABLE 관계 중복 상세 조사')
    cursor.execute("""
        SELECT
            src.component_name AS sql_comp,
            dst.component_name AS table_name,
            COUNT(*) AS dup_count,
            GROUP_CONCAT(r.relationship_id) AS rel_ids
        FROM relationships r
        JOIN components src ON r.src_id = src.component_id
        JOIN components dst ON r.dst_id = dst.component_id
        WHERE r.rel_type = 'USE_TABLE'
          AND r.del_yn = 'N'
        GROUP BY src.component_name, dst.component_name
        HAVING dup_count > 1
        ORDER BY dup_count DESC
        LIMIT 10
    """)
    use_table_dups = cursor.fetchall()
    print(f'총 {len(use_table_dups)}개 중복 USE_TABLE 관계')
    for row in use_table_dups:
        print(f'  {row[0]:50s} -> {row[1]:30s}')
        print(f'    중복: {row[2]}회, relationship_ids: {row[3]}')

    # 5. JOIN 관계 중복 상세 조사
    print()
    print('[5] JOIN 관계 중복 상세 조사 (동일 테이블 쌍, 동일 조인 조건)')
    cursor.execute("""
        SELECT
            src.component_name AS src_table,
            dst.component_name AS dst_table,
            r.rel_type,
            r.join_condition,
            COUNT(*) AS dup_count,
            GROUP_CONCAT(r.relationship_id) AS rel_ids
        FROM relationships r
        JOIN components src ON r.src_id = src.component_id
        JOIN components dst ON r.dst_id = dst.component_id
        WHERE r.rel_type LIKE 'JOIN_%'
          AND r.del_yn = 'N'
        GROUP BY src.component_name, dst.component_name, r.rel_type, r.join_condition
        HAVING dup_count > 1
        ORDER BY dup_count DESC
        LIMIT 10
    """)
    join_dups = cursor.fetchall()
    print(f'총 {len(join_dups)}개 중복 JOIN 관계')
    for row in join_dups:
        print(f'  {row[0]:20s} - {row[1]:20s} [{row[2]}]')
        print(f'    조건: {row[3] or "N/A"}')
        print(f'    중복: {row[4]}회, relationship_ids: {row[5]}')

    conn.close()


if __name__ == '__main__':
    check_table_naming_conflicts()
