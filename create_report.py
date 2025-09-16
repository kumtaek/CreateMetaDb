#!/usr/bin/env python3
"""
SourceAnalyzer 리포트 생성 메인 실행 파일
- CallChain Report 생성
- ERD Report 생성
"""

import sys
import argparse
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가 (공통함수 사용)
sys.path.append(str(__file__).replace('create_report.py', ''))

from util.logger import app_logger, handle_error
from util.path_utils import PathUtils
from util.database_utils import DatabaseUtils
from reports.callchain_report_generator import CallChainReportGenerator
from reports.erd_report_generator import ERDReportGenerator
from reports.architecture_report_generator import ArchitectureReportGenerator
from reports.erd_dagre_report_generator import ERDDagreReportGenerator


def parse_arguments():
    """명령행 인자 파싱"""
    parser = argparse.ArgumentParser(
        description='SourceAnalyzer 리포트 생성 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python create_report.py --project-name sampleSrc
  python create_report.py --project-name sampleSrc --report-type callchain
  python create_report.py --project-name sampleSrc --report-type erd
  python create_report.py --project-name sampleSrc --report-type architecture
        """
    )
    
    parser.add_argument(
        '--project-name', '-p',
        required=True,
        help='분석할 프로젝트명 (필수)'
    )
    
    parser.add_argument(
        '--report-type', '-t',
        choices=['callchain', 'erd', 'erd-dagre', 'architecture', 'all'],
        default='all',
        help='생성할 리포트 타입 (기본값: all - 모든 리포트 생성)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        help='출력 디렉토리 (기본값: ./projects/{project_name}/report)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='상세 로그 출력'
    )
    
    return parser.parse_args()


def validate_project(project_name: str, path_utils: PathUtils) -> bool:
    """프로젝트 유효성 검증"""
    try:
        # 프로젝트 디렉토리 존재 확인
        if not path_utils.project_exists(project_name):
            app_logger.error(f"프로젝트가 존재하지 않습니다: {project_name}")
            return False
        
        # 메타데이터베이스 파일 존재 확인 (공통함수 사용)
        metadata_db_path = path_utils.get_project_metadata_db_path(project_name)
        from util.file_utils import FileUtils
        if not FileUtils.get_file_info(metadata_db_path)['exists']:
            app_logger.error(f"메타데이터베이스가 존재하지 않습니다: {metadata_db_path}")
            return False
        
        app_logger.info(f"프로젝트 유효성 검증 완료: {project_name}")
        return True
        
    except Exception as e:
        handle_error(e, f"프로젝트 유효성 검증 실패: {project_name}")
        return False


def create_output_directory(project_name: str, path_utils: PathUtils, output_dir: str = None) -> str:
    """출력 디렉토리 생성"""
    try:
        if output_dir:
            output_path = path_utils.normalize_path(output_dir)
        else:
            output_path = path_utils.get_project_report_path(project_name)
        
        # 공통함수 사용 (하드코딩 금지)
        from util.file_utils import FileUtils
        if not FileUtils.ensure_directory_exists(output_path):
            handle_error(Exception(f"디렉토리 생성 실패: {output_path}"), f"출력 디렉토리 생성 실패: {output_path}")
        
        app_logger.info(f"출력 디렉토리 준비 완료: {output_path}")
        return output_path
        
    except Exception as e:
        handle_error(e, f"출력 디렉토리 생성 실패: {output_path}")
        return ""


def generate_callchain_report(project_name: str, output_dir: str) -> bool:
    """CallChain Report 생성"""
    try:
        app_logger.info("CallChain Report 생성 시작")
        
        generator = CallChainReportGenerator(project_name, output_dir)
        success = generator.generate_report()
        
        if success:
            app_logger.info("CallChain Report 생성 완료")
            return True
        else:
            app_logger.error("CallChain Report 생성 실패")
            return False
            
    except Exception as e:
        handle_error(e, "CallChain Report 생성 중 오류 발생")
        return False


def generate_erd_report(project_name: str, output_dir: str) -> bool:
    """ERD Report 생성"""
    try:
        app_logger.info("ERD Report 생성 시작")
        
        generator = ERDReportGenerator(project_name, output_dir)
        success = generator.generate_report()
        
        if success:
            app_logger.info("ERD Report 생성 완료")
            return True
        else:
            app_logger.error("ERD Report 생성 실패")
            return False
            
    except Exception as e:
        handle_error(e, "ERD Report 생성 중 오류 발생")
        return False




def generate_erd_dagre_report(project_name: str, output_dir: str) -> bool:
    """ERD(Dagre) Report 생성"""
    try:
        app_logger.info("ERD(Dagre) Report 생성 시작")
        
        generator = ERDDagreReportGenerator(project_name, output_dir)
        success = generator.generate_report()
        
        if success:
            app_logger.info("ERD(Dagre) Report 생성 완료")
            return True
        else:
            app_logger.error("ERD(Dagre) Report 생성 실패")
            return False
            
    except Exception as e:
        handle_error(e, "ERD(Dagre) Report 생성 중 오류 발생")
        return False


def generate_architecture_report(project_name: str, output_dir: str) -> bool:
    """Architecture Report 생성"""
    try:
        app_logger.info("Architecture Report 생성 시작")
        
        generator = ArchitectureReportGenerator(project_name, output_dir)
        success = generator.generate_report()
        
        if success:
            app_logger.info("Architecture Report 생성 완료")
            return True
        else:
            app_logger.error("Architecture Report 생성 실패")
            return False
            
    except Exception as e:
        handle_error(e, "Architecture Report 생성 중 오류 발생")
        return False


def main():
    """메인 함수"""
    try:
        app_logger.info("=== SourceAnalyzer 리포트 생성 도구 시작 ===")
        
        # 명령행 인자 파싱
        args = parse_arguments()
        
        # 경로 유틸리티 초기화
        path_utils = PathUtils()
        
        # 프로젝트 유효성 검증
        if not validate_project(args.project_name, path_utils):
            handle_error(Exception("프로젝트 유효성 검증 실패"), "프로젝트 유효성 검증 실패")
        
        # 출력 디렉토리 생성
        output_dir = create_output_directory(args.project_name, path_utils, args.output_dir)
        if not output_dir:
            handle_error(Exception("출력 디렉토리 생성 실패"), "출력 디렉토리 생성 실패")
        
        # 리포트 생성
        success_count = 0
        total_count = 0
        
        if args.report_type in ['callchain', 'all']:
            total_count += 1
            if generate_callchain_report(args.project_name, output_dir):
                success_count += 1
        
        if args.report_type in ['erd', 'all']:
            total_count += 1
            if generate_erd_report(args.project_name, output_dir):
                success_count += 1
        
        if args.report_type in ['erd-dagre', 'all']:
            total_count += 1
            if generate_erd_dagre_report(args.project_name, output_dir):
                success_count += 1
        
        if args.report_type in ['architecture', 'all']:
            total_count += 1
            if generate_architecture_report(args.project_name, output_dir):
                success_count += 1
        
        # 결과 출력
        app_logger.info(f"=== 리포트 생성 완료 ===")
        app_logger.info(f"성공: {success_count}/{total_count}")
        app_logger.info(f"출력 디렉토리: {output_dir}")
        
        if success_count == total_count:
            app_logger.info("모든 리포트가 성공적으로 생성되었습니다.")
            return
        else:
            handle_error(Exception("일부 리포트 생성 실패"), "일부 리포트 생성에 실패했습니다.")
            
    except KeyboardInterrupt:
        app_logger.info("사용자에 의해 중단되었습니다.")
        return
    except Exception as e:
        handle_error(e, "리포트 생성 도구 실행 중 치명적 오류 발생")


if __name__ == '__main__':
    main()

