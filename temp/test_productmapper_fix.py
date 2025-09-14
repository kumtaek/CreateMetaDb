#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from xml_loading import XmlLoading
from util.database_utils import DatabaseUtils

def test_productmapper_fix():
    """ProductMapper.xml 수정 테스트"""
    
    try:
        # XML 로딩 초기화
        xml_loading = XmlLoading('sampleSrc')
        
        # 데이터베이스 연결
        db_utils = DatabaseUtils('projects/sampleSrc/metadata.db')
        if not db_utils.connect():
            print("데이터베이스 연결 실패")
            return
        
        xml_loading.db_utils = db_utils
        
        # ProductMapper.xml 파일 경로
        productmapper_path = 'projects/sampleSrc/src/main/resources/mybatis/mapper/ProductMapper.xml'
        
        print('=== ProductMapper.xml 수정 테스트 ===')
        print(f'파일 경로: {productmapper_path}')
        
        # XML 파싱
        result = xml_loading.xml_parser.extract_sql_queries_and_analyze_relationships(productmapper_path)
        
        print(f'파싱 결과:')
        print(f'  - SQL 쿼리 수: {len(result.get("sql_queries", []))}')
        print(f'  - 오류 여부: {result.get("has_error", "N")}')
        
        if result.get("error_message"):
            print(f'  - 오류 메시지: {result["error_message"]}')
        
        # SQL 쿼리 상세 정보
        sql_queries = result.get("sql_queries", [])
        if sql_queries:
            print(f'  - SQL 쿼리 목록:')
            for i, query in enumerate(sql_queries, 1):
                query_id = query.get("sql_id", f"query_{i}")
                query_type = query.get("tag_name", "unknown")
                print(f'    {i}. {query_id} ({query_type})')
            
            # SQL 컴포넌트 저장 테스트
            print(f'\nSQL 컴포넌트 저장 테스트:')
            xml_loading.current_file_id = 38  # ProductMapper.xml의 file_id
            success = xml_loading._save_sql_components_to_database(sql_queries)
            print(f'저장 결과: {success}')
            
        else:
            print(f'  - SQL 쿼리가 추출되지 않음')
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db_utils' in locals():
            db_utils.close()

if __name__ == "__main__":
    test_productmapper_fix()
