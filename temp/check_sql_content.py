#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def check_sql_content_db():
    """SQL Content 데이터베이스 확인"""
    try:
        db_path = 'projects/sampleSrc/SqlContent.db'
        if not os.path.exists(db_path):
            print(f"SQL Content 데이터베이스가 존재하지 않습니다: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 목록 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("SQL Content 데이터베이스 테이블:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # sql_contents 테이블 데이터 확인
        if any('sql_contents' in table for table in tables):
            cursor.execute("SELECT COUNT(*) FROM sql_contents")
            count = cursor.fetchone()[0]
            print(f"\nsql_contents 테이블 데이터 개수: {count}")
            
            if count > 0:
                cursor.execute("SELECT content_id, component_name, query_type, created_at FROM sql_contents LIMIT 5")
                rows = cursor.fetchall()
                print("\n최근 5개 SQL Content:")
                for row in rows:
                    print(f"  ID: {row[0]}, Name: {row[1]}, Type: {row[2]}, Created: {row[3]}")
        
        conn.close()
        print("\nSQL Content 데이터베이스 확인 완료")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    check_sql_content_db()
