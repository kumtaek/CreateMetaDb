#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def check_files_table():
    """files 테이블 내용 확인"""
    
    conn = sqlite3.connect('projects/sampleSrc/metadata.db')
    cursor = conn.cursor()
    
    try:
        # files 테이블의 모든 파일 확인
        cursor.execute('''
            SELECT file_id, file_name, file_path, file_type
            FROM files
            ORDER BY file_type, file_name
        ''')
        files = cursor.fetchall()
        
        print('files 테이블의 모든 파일:')
        print(f'총 {len(files)}개 파일')
        
        # 파일 타입별 통계
        file_types = {}
        for file_id, file_name, file_path, file_type in files:
            if file_type not in file_types:
                file_types[file_type] = []
            file_types[file_type].append((file_id, file_name, file_path))
        
        for file_type, file_list in file_types.items():
            print(f'\n{file_type} 파일: {len(file_list)}개')
            for file_id, file_name, file_path in file_list:
                print(f'  {file_id}: {file_name} ({file_path})')
        
        # XML 파일만 따로 확인
        xml_files = [f for f in files if f[3] == 'XML']
        print(f'\nXML 파일: {len(xml_files)}개')
        for file_id, file_name, file_path, file_type in xml_files:
            print(f'  {file_id}: {file_name} ({file_path})')
        
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_files_table()
