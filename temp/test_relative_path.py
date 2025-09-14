#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from util.path_utils import PathUtils

def test_relative_path():
    """relative_path 테스트"""
    
    path_utils = PathUtils()
    
    # 실제 XML 파일 경로
    xml_file = r'D:\Analyzer\CreateMetaDb\projects\sampleSrc\src\main\resources\mybatis\mapper\ProductMapper.xml'
    project_source_path = r'D:\Analyzer\CreateMetaDb\projects\sampleSrc'
    
    print(f'XML 파일: {xml_file}')
    print(f'프로젝트 경로: {project_source_path}')
    
    # 상대경로 변환
    relative_path = path_utils.get_relative_path(xml_file, project_source_path)
    print(f'PathUtils 변환 결과: "{relative_path}"')
    
    # Windows 경로 구분자로 변환
    windows_path = relative_path.replace('/', '\\')
    print(f'Windows 경로 변환: "{windows_path}"')
    
    # files 테이블의 실제 경로
    files_table_path = r'src\main\resources\mybatis\mapper'
    print(f'files 테이블 경로: "{files_table_path}"')
    
    # 매칭 확인
    print(f'매칭 여부: {windows_path == files_table_path}')
    
    # 각 문자별 비교
    print(f'길이 비교: {len(windows_path)} vs {len(files_table_path)}')
    for i, (c1, c2) in enumerate(zip(windows_path, files_table_path)):
        if c1 != c2:
            print(f'차이점 위치 {i}: "{c1}" vs "{c2}"')

if __name__ == "__main__":
    test_relative_path()
