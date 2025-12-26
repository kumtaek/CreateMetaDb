"""
세 가지 문제 원인 파악 스크립트
1. INFERRED 테이블이 고아로 ERD에 표시되는 문제
2. CSV 테이블이 INFERRED로 잘못 표시되는 문제 (예: NP.SUS_CTR_BAS -> NP_SUS_CTR_BAS)
3. 백엔드 매핑 리포트에서 테이블/조인조건 중복 표시 문제
"""

import sqlite3
import sys

def investigate_issue_1_inferred_orphan(db_path):
    """문제1: INFERRED 테이블이 고아로 표시되는 원인 파악"""
    print("=" * 80)
    print("문제 1: INFERRED 테이블이 고아(관계 없음)로 ERD에 표시되는 원인")
    print("=" * 80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1-1. file_type이 CSV가 아닌 TABLE 컴포넌트 조회 (INFERRED 테이블 후보)
    print("\n[1-1] file_type != 'CSV'인 TABLE 컴포넌트 (INFERRED 후보)")
    cursor.execute("""
        SELECT c.component_id, c.component_name, c.component_type, f.file_type, f.file_name
        FROM components c
        JOIN files f ON c.file_id = f.file_id
        WHERE c.component_type = 'TABLE'
          AND f.file_type != 'CSV'
          AND c.del_yn = 'N'
        ORDER BY c.component_name
        LIMIT 20
    """)
    inferred_candidates = cursor.fetchall()
    print(f"총 {len(inferred_candidates)}개 발견")
    for row in inferred_candidates[:10]:
        print(f"  comp_id={row[0]:4d} | {row[1]:30s} | file_type={row[3]:10s} | file={row[4]}")

    # 1-2. 위 INFERRED 후보 중에서 관계가 있는지 확인
    print("\n[1-2] INFERRED 후보 테이블의 관계 확인 (JOIN_EXPLICIT, JOIN_IMPLICIT)")
    if inferred_candidates:
        comp_ids = [str(row[0]) for row in inferred_candidates[:20]]
        placeholders = ','.join(['?'] * len(comp_ids))

        query = f"""
            SELECT src.component_id, src.component_name,
                   r.rel_type,
                   dst.component_id, dst.component_name
            FROM relationships r
            JOIN components src ON r.src_id = src.component_id
            JOIN components dst ON r.dst_id = dst.component_id
            WHERE (r.src_id IN ({placeholders}) OR r.dst_id IN ({placeholders}))
              AND r.rel_type IN ('JOIN_EXPLICIT', 'JOIN_IMPLICIT')
              AND r.del_yn = 'N'
            LIMIT 30
        """
        cursor.execute(query, comp_ids + comp_ids)
        relations = cursor.fetchall()
        print(f"총 {len(relations)}개 관계 발견")
        for row in relations[:10]:
            print(f"  {row[1]:30s} --[{row[2]}]--> {row[4]:30s}")

        if len(relations) == 0:
            print("\n  ** 원인: INFERRED 테이블로 추론되었으나 JOIN 관계가 등록되지 않음 **")
            print("  => xml_loading.py 또는 java_loading.py에서 테이블은 추출했지만")
            print("     JOIN 관계를 제대로 파싱하지 못했거나 relationships에 INSERT하지 않음")

    conn.close()


def investigate_issue_2_csv_as_inferred(db_path):
    """문제2: CSV 테이블이 INFERRED로 잘못 표시되는 원인 파악"""
    print("\n\n" + "=" * 80)
    print("문제 2: CSV 테이블이 INFERRED로 잘못 표시되는 원인 (예: NP.SUS_CTR_BAS)")
    print("=" * 80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 2-1. tables 테이블에서 스키마.테이블 형식 확인
    print("\n[2-1] tables 테이블의 실제 저장 형식 (table_name, table_owner)")
    cursor.execute("""
        SELECT table_name, table_owner, component_id
        FROM tables
        WHERE del_yn = 'N'
        ORDER BY table_name
        LIMIT 20
    """)
    tables_sample = cursor.fetchall()
    for row in tables_sample[:10]:
        print(f"  table_name={row[0]:30s} | owner={row[1]:15s} | comp_id={row[2]}")

    # 2-2. components 테이블의 TABLE 타입 저장 형식 확인
    print("\n[2-2] components 테이블의 TABLE 타입 저장 형식 (component_name)")
    cursor.execute("""
        SELECT c.component_id, c.component_name, f.file_type
        FROM components c
        JOIN files f ON c.file_id = f.file_id
        WHERE c.component_type = 'TABLE'
          AND c.del_yn = 'N'
          AND f.file_type = 'CSV'
        ORDER BY c.component_name
        LIMIT 20
    """)
    components_sample = cursor.fetchall()
    for row in components_sample[:10]:
        print(f"  comp_id={row[0]:4d} | component_name={row[1]:40s} | file_type={row[2]}")

    # 2-3. 스키마.테이블 vs 스키마_테이블 불일치 확인
    print("\n[2-3] tables.table_name과 components.component_name 비교")
    cursor.execute("""
        SELECT t.table_name, t.table_owner, c.component_name
        FROM tables t
        JOIN components c ON t.component_id = c.component_id
        WHERE t.del_yn = 'N' AND c.del_yn = 'N'
        ORDER BY t.table_name
        LIMIT 20
    """)
    comparison = cursor.fetchall()
    for row in comparison[:10]:
        expected = f"{row[1]}.{row[0]}" if row[1] else row[0]
        actual = row[2]
        match = "일치" if expected.upper() == actual.upper() else "불일치"
        print(f"  tables: {row[0]:20s} (owner={row[1]:10s}) | components: {actual:30s} [{match}]")

    print("\n  ** 원인 분석 **")
    print("  1) tables 테이블: table_name='SUS_CTR_BAS', table_owner='NP' (분리 저장)")
    print("  2) components 테이블: component_name='NP.SUS_CTR_BAS' 또는 'SUS_CTR_BAS'")
    print("  3) ERD 생성 시 조인 관계 조회: components.component_name을 기준으로 조회")
    print("  4) 조인 조건 파싱 시: 'NP_SUS_CTR_BAS' (언더스코어) 형식으로 저장되는 경우")
    print("     => CSV에서 'NP.SUS_CTR_BAS'로 등록했지만")
    print("        조인 조건에서 'NP_SUS_CTR_BAS'로 추출되면 별개 테이블로 인식")
    print("  5) 결과: 'NP_SUS_CTR_BAS'가 INFERRED 테이블로 생성됨 (file_type != CSV)")

    conn.close()


def investigate_issue_3_duplicate_backend(db_path):
    """문제3: 백엔드 매핑 리포트에서 테이블/조인조건 중복 표시 원인 파악"""
    print("\n\n" + "=" * 80)
    print("문제 3: 백엔드 매핑 리포트에서 테이블/조인조건 중복 표시 원인")
    print("=" * 80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 3-1. 동일한 SQL 컴포넌트가 동일한 테이블을 여러 번 참조하는지 확인
    print("\n[3-1] USE_TABLE 관계에서 중복 테이블 사용 확인")
    cursor.execute("""
        SELECT src.component_name AS sql_comp,
               dst.component_name AS table_name,
               COUNT(*) AS count
        FROM relationships r
        JOIN components src ON r.src_id = src.component_id
        JOIN components dst ON r.dst_id = dst.component_id
        WHERE r.rel_type = 'USE_TABLE'
          AND r.del_yn = 'N'
        GROUP BY src.component_name, dst.component_name
        HAVING count > 1
        ORDER BY count DESC
        LIMIT 10
    """)
    duplicates = cursor.fetchall()
    print(f"중복된 USE_TABLE 관계: {len(duplicates)}개")
    for row in duplicates:
        print(f"  {row[0]:50s} -> {row[1]:30s} (중복 {row[2]}회)")

    if len(duplicates) > 0:
        print("\n  ** 원인 1: USE_TABLE 관계 중복 등록 **")
        print("     => xml_loading.py, java_loading.py에서 동일한 테이블을 여러 번 INSERT")
        print("     => INSERT OR IGNORE가 아니라 UNIQUE 제약 없이 중복 INSERT 가능")

    # 3-2. JOIN 관계에서 중복 조인 조건 확인
    print("\n[3-2] JOIN 관계에서 동일한 테이블 쌍의 중복 조인 조건 확인")
    cursor.execute("""
        SELECT src.component_name AS src_table,
               dst.component_name AS dst_table,
               r.join_condition,
               COUNT(*) AS count
        FROM relationships r
        JOIN components src ON r.src_id = src.component_id
        JOIN components dst ON r.dst_id = dst.component_id
        WHERE r.rel_type LIKE 'JOIN_%'
          AND r.del_yn = 'N'
        GROUP BY src.component_name, dst.component_name, r.join_condition
        HAVING count > 1
        ORDER BY count DESC
        LIMIT 10
    """)
    join_duplicates = cursor.fetchall()
    print(f"중복된 JOIN 관계: {len(join_duplicates)}개")
    for row in join_duplicates:
        print(f"  {row[0]:20s} - {row[1]:20s} | 조건: {row[2]:40s} (중복 {row[3]}회)")

    if len(join_duplicates) > 0:
        print("\n  ** 원인 2: JOIN 관계 중복 등록 **")
        print("     => 동일한 조인 조건이 여러 번 파싱되어 relationships에 중복 INSERT")
        print("     => UNIQUE INDEX가 (src_id, dst_id, rel_type)만 포함하고")
        print("        join_condition은 포함하지 않아 중복 허용")

    # 3-3. 백엔드 리포트 생성 로직 확인
    print("\n[3-3] 백엔드 리포트 생성 로직 분석")
    print("  backend_mapping_report_generator.py:")
    print("  - _load_metadata_use_tables(): USE_TABLE 관계 조회 (중복 가능)")
    print("  - _load_metadata_join_conditions(): JOIN 관계 조회 후 정규화")
    print("    * 366-377줄: normalized_conditions = set() 으로 중복 제거 시도")
    print("    * 하지만 테이블 목록은 중복 제거 없이 그대로 표시")
    print("  ")
    print("  ** 원인 3: 리포트 생성 시 중복 제거 로직 부족 **")
    print("     => USE_TABLE에서 조회한 테이블 목록을 set()으로 중복 제거 안함")
    print("     => 조인 조건도 정규화는 하지만 relationships에서 이미 중복 데이터 존재")

    conn.close()


def main():
    db_path = 'D:/Analyzer/CreateMetaDb/projects/sampleSrc/metadata.db'

    print("세 가지 문제 원인 파악 시작")
    print("=" * 80)

    investigate_issue_1_inferred_orphan(db_path)
    investigate_issue_2_csv_as_inferred(db_path)
    investigate_issue_3_duplicate_backend(db_path)

    print("\n\n" + "=" * 80)
    print("종합 분석 결과")
    print("=" * 80)
    print()
    print("문제 1: INFERRED 테이블이 고아로 표시")
    print("-------")
    print("원인:")
    print("  - erd_metadata_service.py:255-298 (_get_tables_with_relationships)")
    print("  - file_type != 'CSV'인 테이블을 INFERRED로 판단 (257줄)")
    print("  - 하지만 relationships에 JOIN 관계가 없으면 조회되지 않음")
    print("  - 테이블은 components에 등록되었지만 JOIN 관계가 누락된 경우")
    print()
    print("해결 방안:")
    print("  1) xml_loading.py, java_loading.py에서 JOIN 관계 파싱 로직 강화")
    print("  2) consistency_validator.py에서 테이블 간 관계 보강 로직 추가")
    print("  3) ERD 생성 시 고아 INFERRED 테이블을 별도로 표시하거나 제외")
    print()
    print()
    print("문제 2: CSV 테이블이 INFERRED로 잘못 표시 (예: NP.SUS_CTR_BAS)")
    print("-------")
    print("원인:")
    print("  - tables 테이블: table_name='SUS_CTR_BAS', table_owner='NP' (분리 저장)")
    print("  - components 테이블: component_name='NP.SUS_CTR_BAS' (결합 저장)")
    print("  - 조인 조건 파싱 시: 'NP_SUS_CTR_BAS' (언더스코어)로 추출되는 경우")
    print("  - SQL에서 'NP.SUS_CTR_BAS'와 'NP_SUS_CTR_BAS'를 별개로 인식")
    print("  - 'NP_SUS_CTR_BAS'는 CSV에 없으므로 INFERRED 테이블로 생성")
    print()
    print("해결 방안:")
    print("  1) 테이블명 정규화 통일: 스키마.테이블 형식 vs 스키마_테이블 형식")
    print("  2) parser/common_sql_analyzer.py에서 테이블명 추출 시 정규화")
    print("  3) components 생성 시 table_owner를 고려한 매칭 로직 추가")
    print("  4) consistency_validator.py에서 동일 테이블 다른 형식 병합")
    print()
    print()
    print("문제 3: 백엔드 매핑 리포트에서 테이블/조인조건 중복 표시")
    print("-------")
    print("원인:")
    print("  1) relationships 테이블에 중복 데이터 저장")
    print("     - UNIQUE INDEX: (src_id, dst_id, rel_type)만 포함")
    print("     - join_condition이 다르면 중복 INSERT 가능")
    print("  2) backend_mapping_report_generator.py:")
    print("     - _load_metadata_use_tables(): 중복 제거 없이 테이블 목록 수집")
    print("     - _load_metadata_join_conditions(): 조인 조건 정규화만 하고 중복 데이터는 그대로")
    print()
    print("해결 방안:")
    print("  1) relationships INSERT 시 중복 체크 강화")
    print("     - xml_loading.py, java_loading.py에서 INSERT 전에 중복 확인")
    print("  2) 백엔드 리포트 생성 시 중복 제거:")
    print("     - _load_metadata_use_tables()에서 set() 사용하여 테이블 중복 제거")
    print("     - _format_tables()에서 중복 owner.table 제거")
    print("  3) relationships UNIQUE INDEX 수정 (주의: 기존 데이터 마이그레이션 필요)")
    print("     - CREATE UNIQUE INDEX ix_relationships_01")
    print("       ON relationships (src_id, dst_id, rel_type, join_condition)")
    print()


if __name__ == '__main__':
    main()
