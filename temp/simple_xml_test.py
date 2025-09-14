#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import os

def test_xml_parsing():
    """간단한 XML 파싱 테스트"""
    
    test_files = [
        'projects/sampleSrc/src/main/resources/mybatis/mapper/ProductMapper.xml',
        'projects/sampleSrc/src/main/resources/mybatis/mapper/UserMapper.xml'
    ]
    
    print('=== 간단한 XML 파싱 테스트 ===')
    
    for xml_file in test_files:
        print(f'\n--- {os.path.basename(xml_file)} ---')
        
        if not os.path.exists(xml_file):
            print(f'파일이 존재하지 않음: {xml_file}')
            continue
        
        try:
            # XML 파싱
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            print(f'루트 태그: {root.tag}')
            print(f'네임스페이스: {root.get("namespace", "없음")}')
            
            # SQL 태그들 찾기
            sql_tags = ['select', 'insert', 'update', 'delete']
            total_queries = 0
            
            for tag_name in sql_tags:
                statements = root.findall(f'.//{tag_name}')
                count = len(statements)
                total_queries += count
                print(f'  {tag_name} 태그: {count}개')
                
                # 각 statement의 id 출력
                for i, stmt in enumerate(statements[:3], 1):  # 처음 3개만
                    stmt_id = stmt.get('id', f'id_{i}')
                    print(f'    {i}. {stmt_id}')
            
            print(f'총 SQL 쿼리 수: {total_queries}개')
            
            # XML 구조 확인
            print(f'전체 자식 요소 수: {len(list(root))}')
            
        except ET.ParseError as e:
            print(f'XML 파싱 오류: {e}')
        except Exception as e:
            print(f'오류 발생: {e}')

if __name__ == "__main__":
    test_xml_parsing()
