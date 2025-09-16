#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from reports.callchain_report_generator import CallChainReportGenerator
from util.path_utils import PathUtils
from util.database_utils import DatabaseUtils

def test_empty_tables():
    """빈 테이블 표시 테스트"""
    
    print("CallChain 리포트 생성 중...")
    
    try:
        path_utils = PathUtils()
        db_utils = DatabaseUtils()
        generator = CallChainReportGenerator('sampleSrc', 'reports/sample_report', db_utils, path_utils)
        
        result = generator.generate_report()
        print(f"CallChain 리포트 생성 완료: {result}")
        
        # 생성된 HTML 파일 확인
        html_file = 'reports/sample_report/callchain_report.html'
        if os.path.exists(html_file):
            print(f"HTML 파일 생성됨: {html_file}")
            
            # HTML 파일에서 NO-QUERY 검색
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            no_query_count = content.count('NO-QUERY')
            print(f"HTML에서 'NO-QUERY' 개수: {no_query_count}")
            
            if no_query_count == 0:
                print("✅ 'NO-QUERY' 텍스트가 제거되었습니다!")
            else:
                print("❌ 아직 'NO-QUERY' 텍스트가 남아있습니다.")
                
        else:
            print("❌ HTML 파일이 생성되지 않았습니다.")
            
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_empty_tables()
