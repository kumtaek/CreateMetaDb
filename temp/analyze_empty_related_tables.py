#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def analyze_empty_related_tables():
    """관련 테이블이 비어있는 쿼리들 분석"""
    
    db_path = 'projects/sampleSrc/metadata.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== 관련 테이블이 비어있는 쿼리들 분석 ===")
        
        # 1. 관련 테이블이 비어있는 쿼리들 찾기
        cursor.execute("""
            SELECT 
                q.component_name as query_name,
                q.component_type as query_type,
                f.file_name as xml_file,
                q.component_id as query_id
            FROM components q
            JOIN files f ON q.file_id = f.file_id
            LEFT JOIN relationships r ON q.component_id = r.src_id AND r.rel_type = 'USE_TABLE' AND r.del_yn = 'N'
            JOIN projects p ON q.project_id = p.project_id
            WHERE p.project_name = 'sampleSrc'
              AND q.component_type LIKE 'SQL_%'
              AND q.del_yn = 'N'
              AND f.del_yn = 'N'
              AND r.src_id IS NULL
            ORDER BY f.file_name, q.component_name
        """)
        empty_table_queries = cursor.fetchall()
        
        print(f"\n1. 관련 테이블이 비어있는 쿼리들 ({len(empty_table_queries)}개):")
        for query_name, query_type, xml_file, query_id in empty_table_queries:
            print(f"   - {xml_file}: {query_name} ({query_type}, ID: {query_id})")
        
        # 2. insertUserToV1과 searchByName 쿼리 상세 분석
        target_queries = ['insertUserToV1', 'searchByName']
        
        for target_query in target_queries:
            print(f"\n2. {target_query} 쿼리 상세 분석:")
            
            # 쿼리 정보 조회
            cursor.execute("""
                SELECT 
                    q.component_id,
                    q.component_name,
                    q.component_type,
                    f.file_name as xml_file
                FROM components q
                JOIN files f ON q.file_id = f.file_id
                JOIN projects p ON q.project_id = p.project_id
                WHERE p.project_name = 'sampleSrc'
                  AND q.component_name = ?
                  AND q.del_yn = 'N'
            """, (target_query,))
            query_info = cursor.fetchone()
            
            if query_info:
                query_id, query_name, query_type, xml_file = query_info
                print(f"   쿼리 정보: {xml_file} - {query_name} ({query_type}, ID: {query_id})")
                
                # 해당 쿼리의 관계들 확인
                cursor.execute("""
                    SELECT 
                        r.rel_type,
                        dst_c.component_name as dst_name,
                        dst_c.component_type as dst_type
                    FROM relationships r
                    JOIN components dst_c ON r.dst_id = dst_c.component_id
                    WHERE r.src_id = ? AND r.del_yn = 'N'
                    ORDER BY r.rel_type
                """, (query_id,))
                relationships = cursor.fetchall()
                
                print(f"   관계들:")
                if relationships:
                    for rel_type, dst_name, dst_type in relationships:
                        print(f"     - {rel_type}: {dst_name} ({dst_type})")
                else:
                    print(f"     - 관계 없음")
                
                # USE_TABLE 관계가 없는 이유 확인
                cursor.execute("""
                    SELECT 
                        r.rel_type,
                        dst_c.component_name as dst_name,
                        dst_c.component_type as dst_type,
                        r.del_yn
                    FROM relationships r
                    JOIN components dst_c ON r.dst_id = dst_c.component_id
                    WHERE r.src_id = ? AND r.rel_type = 'USE_TABLE'
                """, (query_id,))
                use_table_rels = cursor.fetchall()
                
                print(f"   USE_TABLE 관계:")
                if use_table_rels:
                    for rel_type, dst_name, dst_type, del_yn in use_table_rels:
                        print(f"     - {rel_type}: {dst_name} ({dst_type}, del_yn: {del_yn})")
                else:
                    print(f"     - USE_TABLE 관계 없음")
            else:
                print(f"   {target_query} 쿼리를 찾을 수 없습니다.")
        
        # 3. USE_TABLE 관계가 생성되는 로직 확인
        print(f"\n3. USE_TABLE 관계 생성 로직 분석:")
        
        # 모든 USE_TABLE 관계 확인
        cursor.execute("""
            SELECT 
                src_c.component_name as query_name,
                dst_c.component_name as table_name,
                src_f.file_name as xml_file,
                r.del_yn
            FROM relationships r
            JOIN components src_c ON r.src_id = src_c.component_id
            JOIN components dst_c ON r.dst_id = dst_c.component_id
            JOIN files src_f ON src_c.file_id = src_f.file_id
            JOIN projects p ON r.project_id = p.project_id
            WHERE p.project_name = 'sampleSrc'
              AND r.rel_type = 'USE_TABLE'
            ORDER BY src_f.file_name, src_c.component_name
        """)
        use_table_relationships = cursor.fetchall()
        
        print(f"   전체 USE_TABLE 관계 ({len(use_table_relationships)}개):")
        for query_name, table_name, xml_file, del_yn in use_table_relationships:
            print(f"     - {xml_file}: {query_name} → {table_name} (del_yn: {del_yn})")
        
        # 4. 테이블 컴포넌트 확인
        cursor.execute("""
            SELECT 
                t.component_name as table_name,
                t.component_type,
                f.file_name
            FROM components t
            JOIN files f ON t.file_id = f.file_id
            JOIN projects p ON t.project_id = p.project_id
            WHERE p.project_name = 'sampleSrc'
              AND t.component_type = 'TABLE'
              AND t.del_yn = 'N'
            ORDER BY t.component_name
        """)
        table_components = cursor.fetchall()
        
        print(f"\n4. 테이블 컴포넌트들 ({len(table_components)}개):")
        for table_name, comp_type, file_name in table_components:
            print(f"   - {table_name} ({comp_type}, File: {file_name})")
        
        # 5. 가능한 원인 분석
        print(f"\n5. 관련 테이블이 비어있는 가능한 원인:")
        print(f"   a) SQL 쿼리가 실제로 테이블을 참조하지 않는 경우")
        print(f"     - 상수 반환 쿼리: SELECT 1, SELECT NOW()")
        print(f"     - 시스템 함수 호출: SELECT VERSION(), SELECT USER()")
        print(f"   b) 메타데이터 분석 과정에서 테이블 매핑 실패")
        print(f"     - 동적 SQL (PreparedStatement)")
        print(f"     - 복잡한 서브쿼리나 JOIN")
        print(f"     - 별칭 사용으로 인한 매핑 실패")
        print(f"   c) USE_TABLE 관계 생성 로직의 문제")
        print(f"     - 파서가 테이블명을 인식하지 못함")
        print(f"     - 관계 생성 시 오류 발생")
        
        # 6. 실제 SQL 내용 확인 (SqlContent.db)
        print(f"\n6. SqlContent.db에서 실제 SQL 내용 확인:")
        sql_content_db_path = 'projects/sampleSrc/SqlContent.db'
        
        if os.path.exists(sql_content_db_path):
            try:
                sql_conn = sqlite3.connect(sql_content_db_path)
                sql_cursor = sql_conn.cursor()
                
                for target_query in target_queries:
                    sql_cursor.execute("""
                        SELECT sql_content_compressed 
                        FROM sql_contents 
                        WHERE component_name = ?
                    """, (target_query,))
                    result = sql_cursor.fetchone()
                    
                    if result:
                        import gzip
                        try:
                            decompressed_sql = gzip.decompress(result[0]).decode('utf-8')
                            print(f"\n   {target_query} SQL 내용:")
                            print(f"   {decompressed_sql[:200]}...")
                        except Exception as e:
                            print(f"   {target_query} SQL 압축 해제 실패: {e}")
                    else:
                        print(f"   {target_query} SQL 내용 없음")
                
                sql_conn.close()
            except Exception as e:
                print(f"   SqlContent.db 접근 실패: {e}")
        else:
            print(f"   SqlContent.db 파일이 존재하지 않음: {sql_content_db_path}")
        
        conn.close()
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_empty_related_tables()
