#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from parser.xml_parser import XmlParser
from util.config_utils import ConfigUtils

def debug_xml_parsing():
    """XML 파싱 디버깅 - ProductMapper.xml vs UserMapper.xml"""
    
    try:
        # 설정 로드
        config_utils = ConfigUtils()
        xml_config = config_utils.load_yaml_config('config/parser/xml_parser_config.yaml')
        
        # XML 파서 초기화
        xml_parser = XmlParser(xml_config)
        xml_parser.project_name = 'sampleSrc'
        
        # 테스트할 XML 파일들
        test_files = [
            'projects/sampleSrc/src/main/resources/mybatis/mapper/ProductMapper.xml',
            'projects/sampleSrc/src/main/resources/mybatis/mapper/UserMapper.xml'
        ]
        
        print('=== XML 파싱 디버깅 ===')
        
        for xml_file in test_files:
            print(f'\n--- {os.path.basename(xml_file)} ---')
            
            if not os.path.exists(xml_file):
                print(f'파일이 존재하지 않음: {xml_file}')
                continue
            
            # XML 파싱 시도
            try:
                result = xml_parser.extract_sql_queries_and_analyze_relationships(xml_file)
                
                print(f'파싱 결과:')
                print(f'  - SQL 쿼리 수: {len(result.get("sql_queries", []))}')
                print(f'  - JOIN 관계 수: {len(result.get("join_relationships", []))}')
                print(f'  - 오류 여부: {result.get("has_error", "N")}')
                
                if result.get("error_message"):
                    print(f'  - 오류 메시지: {result["error_message"]}')
                
                # SQL 쿼리 상세 정보
                sql_queries = result.get("sql_queries", [])
                if sql_queries:
                    print(f'  - SQL 쿼리 목록:')
                    for i, query in enumerate(sql_queries, 1):
                        query_id = query.get("id", f"query_{i}")
                        query_type = query.get("type", "unknown")
                        print(f'    {i}. {query_id} ({query_type})')
                else:
                    print(f'  - SQL 쿼리가 추출되지 않음')
                
            except Exception as e:
                print(f'파싱 오류: {e}')
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_xml_parsing()
