#!/usr/bin/env python3
"""
CallChain 리포트 자동 생성 스크립트
대화형 입력 없이 자동으로 실행
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reports.callchain_report_generator import CallChainReportGenerator

def main():
    try:
        print("=== CallChain 리포트 자동 생성 시작 ===")
        
        # 프로젝트명과 출력 디렉토리 설정
        project_name = "sampleSrc"
        output_dir = "reports/sample_report"
        
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        
        # 리포트 생성기 초기화
        generator = CallChainReportGenerator(project_name, output_dir)
        
        # 리포트 생성
        result = generator.generate_report()
        
        if result:
            print(f"CallChain 리포트 생성 완료: {output_dir}/callchain_report.html")
        else:
            print("CallChain 리포트 생성 실패")
            
        print("=== CallChain 리포트 자동 생성 완료 ===")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
