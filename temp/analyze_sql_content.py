#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def analyze_sql_content():
    """SQL Content 저장 현황 분석"""
    try:
        db_path = 'projects/sampleSrc/SqlContent.db'
        if not os.path.exists(db_path):
            print(f"SQL Content 데이터베이스가 존재하지 않습니다: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # SQL Content 저장된 데이터 조회
        cursor.execute("""
            SELECT component_name, query_type, LENGTH(sql_content_compressed) as size, 
                   file_id, component_id, created_at
            FROM sql_contents 
            ORDER BY created_at
        """)
        rows = cursor.fetchall()
        
        print("SQL Content 저장된 데이터:")
        print(f"총 {len(rows)}건 저장됨")
        print("-" * 80)
        
        for row in rows:
            print(f"  - {row[0]} ({row[1]}) - {row[2]} bytes")
            print(f"    file_id: {row[3]}, component_id: {row[4]}, created: {row[5]}")
        
        # 메인 메타데이터베이스에서 SQL 컴포넌트 개수 확인
        metadata_db_path = 'projects/sampleSrc/metadata.db'
        if os.path.exists(metadata_db_path):
            metadata_conn = sqlite3.connect(metadata_db_path)
            metadata_cursor = metadata_conn.cursor()
            
            # SQL 컴포넌트 개수 조회
            metadata_cursor.execute("""
                SELECT component_type, COUNT(*) as count 
                FROM components 
                WHERE component_type LIKE 'SQL_%' AND del_yn = 'N'
                GROUP BY component_type
            """)
            sql_components = metadata_cursor.fetchall()
            
            print("\n메인 메타데이터베이스의 SQL 컴포넌트:")
            total_sql_components = 0
            for comp_type, count in sql_components:
                print(f"  - {comp_type}: {count}개")
                total_sql_components += count
            
            print(f"\n총 SQL 컴포넌트: {total_sql_components}개")
            print(f"SQL Content 저장: {len(rows)}개")
            print(f"저장률: {len(rows)/total_sql_components*100:.1f}%" if total_sql_components > 0 else "저장률: 0%")
            
            metadata_conn.close()
        
        conn.close()
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    analyze_sql_content()
