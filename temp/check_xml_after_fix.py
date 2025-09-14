#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def check_xml_after_fix():
    """수정 후 XML 파일별 SQL 쿼리 수 확인"""
    
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT f.file_name, COUNT(c.component_id) as query_count
            FROM files f
            LEFT JOIN components c ON f.file_id = c.file_id AND c.component_type LIKE 'SQL_%'
            WHERE f.file_type = 'XML'
            GROUP BY f.file_id, f.file_name
            ORDER BY query_count DESC
        ''')
        xml_files = cursor.fetchall()
        
        print('XML 파일별 SQL 쿼리 수 (수정 후):')
        for file_name, count in xml_files:
            print(f'  {file_name}: {count}개')
        
        # ProductMapper.xml 확인
        productmapper_found = False
        for file_name, count in xml_files:
            if 'ProductMapper.xml' in file_name:
                productmapper_found = True
                print(f'\nProductMapper.xml: {count}개 SQL 쿼리')
                if count > 0:
                    print('✅ 수정 성공!')
                else:
                    print('❌ 여전히 0개')
                break
        
        if not productmapper_found:
            print('\n❌ ProductMapper.xml이 처리되지 않음')
        
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_xml_after_fix()
