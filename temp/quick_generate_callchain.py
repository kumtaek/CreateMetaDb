#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from reports.callchain_report_generator import CallChainReportGenerator
from util.path_utils import PathUtils
from util.database_utils import DatabaseUtils

def quick_generate_callchain():
    """CallChain 리포트 빠른 생성"""
    
    try:
        # 경로 유틸리티 초기화
        path_utils = PathUtils()
        
        # 데이터베이스 유틸리티 초기화
        db_utils = DatabaseUtils()
        
        # CallChain 리포트 생성기 초기화
        generator = CallChainReportGenerator(
            project_name="sampleSrc",
            output_dir="reports/sample_report",
            db_utils=db_utils,
            path_utils=path_utils
        )
        
        # 리포트 생성
        print("CallChain 리포트 생성 중...")
        result_path = generator.generate_report()
        print(f"CallChain 리포트 생성 완료: {result_path}")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_generate_callchain()
