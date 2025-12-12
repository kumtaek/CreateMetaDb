"""
JOIN 관계 중복 상세 분석
- 동일 테이블 쌍에서 조인 조건이 다른 경우 분석
- relationships 순서 정규화 필요성 검토
"""
import sqlite3

def analyze_join_duplicates():
    conn = sqlite3.connect('D:/Analyzer/CreateMetaDb/projects/sampleSrc/metadata.db')
    cursor = conn.cursor()

    print('=' * 80)
    print('JOIN 관계 중복 및 순서 분석')
    print('=' * 80)
    print()

    # 1. 동일 테이블 쌍, 다른 조인 조건
    print('[1] 동일 테이블 쌍에서 조인 조건이 다른 케이스 (순서 무시)')
    cursor.execute("""
        SELECT
            CASE
                WHEN src.component_name < dst.component_name
                THEN src.component_name || ' - ' || dst.component_name
                ELSE dst.component_name || ' - ' || src.component_name
            END AS table_pair,
            r.rel_type,
            COUNT(DISTINCT r.join_condition) AS condition_count,
            GROUP_CONCAT(r.join_condition, ' | ') AS conditions,
            COUNT(*) AS total_count
        FROM relationships r
        JOIN components src ON r.src_id = src.component_id
        JOIN components dst ON r.dst_id = dst.component_id
        WHERE r.rel_type LIKE 'JOIN_%'
          AND r.del_yn = 'N'
          AND src.component_type = 'TABLE'
          AND dst.component_type = 'TABLE'
        GROUP BY table_pair, r.rel_type
        HAVING total_count > 1 OR condition_count > 1
        ORDER BY total_count DESC
        LIMIT 20
    """)
    same_pair_diff_cond = cursor.fetchall()
    print(f'총 {len(same_pair_diff_cond)}개 테이블 쌍에서 중복 또는 다양한 조인 조건')
    for row in same_pair_diff_cond:
        print(f'  {row[0]:45s} [{row[1]}]')
        print(f'    조인 조건 종류: {row[2]}개, 총 관계: {row[4]}개')
        conditions = (row[3] or 'N/A')[:100]
        print(f'    조건: {conditions}')

    # 2. 양방향 중복 (A->B, B->A)
    print()
    print('[2] 양방향 중복 관계 (A->B와 B->A가 모두 존재)')
    cursor.execute("""
        SELECT
            r1.relationship_id AS rel1_id,
            r2.relationship_id AS rel2_id,
            src1.component_name AS r1_src,
            dst1.component_name AS r1_dst,
            src2.component_name AS r2_src,
            dst2.component_name AS r2_dst,
            r1.rel_type,
            r1.join_condition AS r1_cond,
            r2.join_condition AS r2_cond
        FROM relationships r1
        JOIN relationships r2
            ON r1.src_id = r2.dst_id
            AND r1.dst_id = r2.src_id
            AND r1.rel_type = r2.rel_type
            AND r1.relationship_id < r2.relationship_id
        JOIN components src1 ON r1.src_id = src1.component_id
        JOIN components dst1 ON r1.dst_id = dst1.component_id
        JOIN components src2 ON r2.src_id = src2.component_id
        JOIN components dst2 ON r2.dst_id = dst2.component_id
        WHERE r1.rel_type LIKE 'JOIN_%'
          AND r1.del_yn = 'N'
          AND r2.del_yn = 'N'
        LIMIT 20
    """)
    bidirectional = cursor.fetchall()
    print(f'총 {len(bidirectional)}개 양방향 중복 관계')
    for row in bidirectional:
        print(f'  rel_id {row[0]:4d}: {row[2]:20s} -> {row[3]:20s} [{row[6]}]')
        print(f'  rel_id {row[1]:4d}: {row[4]:20s} -> {row[5]:20s} [{row[6]}]')
        print(f'    조건1: {row[7] or "N/A"}')
        print(f'    조건2: {row[8] or "N/A"}')
        print()

    # 3. ERD 관계 방향 로직 재현 (PK-FK 기반)
    print('[3] ERD 관계 방향 로직 분석 (PK-FK 기반)')
    print('  ERD 생성 시 관계 방향 결정:')
    print('    - PK 쪽이 1(one), FK 쪽이 N(many)')
    print('    - one_side ||--o{ many_side')
    print()
    print('  relationships 저장 시 제안:')
    print('    - src: PK 테이블 (1 side)')
    print('    - dst: FK 테이블 (N side)')
    print('    - 이렇게 통일하면 양방향 중복 방지')
    print()

    # 4. 실제 PK 정보 기반 올바른 방향 확인
    print('[4] 샘플 JOIN 관계의 PK 정보 기반 올바른 방향')
    cursor.execute("""
        SELECT
            r.relationship_id,
            src.component_name AS src_table,
            dst.component_name AS dst_table,
            r.src_column,
            r.dst_column,
            (SELECT COUNT(*)
             FROM columns c
             JOIN tables t ON c.table_id = t.table_id
             WHERE t.table_name = src.component_name
               AND c.column_name = r.src_column
               AND c.position_pk IS NOT NULL) AS src_is_pk,
            (SELECT COUNT(*)
             FROM columns c
             JOIN tables t ON c.table_id = t.table_id
             WHERE t.table_name = dst.component_name
               AND c.column_name = r.dst_column
               AND c.position_pk IS NOT NULL) AS dst_is_pk
        FROM relationships r
        JOIN components src ON r.src_id = src.component_id
        JOIN components dst ON r.dst_id = dst.component_id
        WHERE r.rel_type LIKE 'JOIN_%'
          AND r.del_yn = 'N'
          AND r.src_column IS NOT NULL
          AND r.dst_column IS NOT NULL
        LIMIT 20
    """)
    pk_analysis = cursor.fetchall()
    print(f'총 {len(pk_analysis)}개 JOIN 관계 PK 분석')
    correct_direction = 0
    wrong_direction = 0
    unclear = 0

    for row in pk_analysis:
        rel_id, src_table, dst_table, src_col, dst_col, src_pk, dst_pk = row
        status = ''
        if src_pk > 0 and dst_pk == 0:
            status = '올바름 (src=PK, dst=FK)'
            correct_direction += 1
        elif src_pk == 0 and dst_pk > 0:
            status = '역방향 (src=FK, dst=PK) <- 뒤집어야 함'
            wrong_direction += 1
        else:
            status = '불명확 (둘 다 PK 또는 둘 다 non-PK)'
            unclear += 1

        print(f'  rel_id {rel_id:4d}: {src_table:20s}.{src_col:15s} -> {dst_table:20s}.{dst_col:15s}')
        print(f'    src_pk={src_pk}, dst_pk={dst_pk} => {status}')

    print()
    print(f'방향 통계: 올바름={correct_direction}, 역방향={wrong_direction}, 불명확={unclear}')

    conn.close()


if __name__ == '__main__':
    analyze_join_duplicates()
