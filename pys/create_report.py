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
from util.runtime_options import set_sql_compress, get_sql_compress
from reports.callchain_report_generator import CallChainReportGenerator
from reports.erd_report_generator import ERDReportGenerator
from reports.architecture_report_generator import ArchitectureReportGenerator
from reports.erd_dagre_report_generator import ERDDagreReportGenerator
from reports.architecture_layer_report_generator import ArchitectureLayerReportGenerator
from reports.sequence_diagram_report_generator import SequenceDiagramReportGenerator
from reports.query_list_report_generator import QueryListReportGenerator
from reports.backend_mapping_report_generator import BackendMappingReportGenerator
from reports.frontend_mapping_report_generator import FrontendMappingReportGenerator


def parse_arguments():
    """명령행 인자 파싱"""
    parser = argparse.ArgumentParser(
        description='SourceAnalyzer 리포트 생성 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python create_report.py --project-name <프로젝트명>
  python create_report.py --project-name <프로젝트명> --report-type callchain
  python create_report.py --project-name <프로젝트명> --report-type erd
  python create_report.py --project-name <프로젝트명> --report-type erd-dagre
  python create_report.py --project-name <프로젝트명> --report-type erd-dagre-no-attribute
  python create_report.py --project-name <프로젝트명> --report-type architecture
  python create_report.py --project-name <프로젝트명> --report-type sequence
  python create_report.py --project-name <프로젝트명> --report-type query-list
        """
    )
    
    parser.add_argument(
        '--project-name', '-p',
        required=True,
        help='분석할 프로젝트명 (필수)'
    )
    
    parser.add_argument(
        '--report-type', '-t',
        choices=['callchain', 'erd', 'erd-dagre', 'erd-dagre-no-attribute', 'architecture', 'architecture-layer', 'sequence', 'query-list', 'backend-mapping', 'frontend-mapping', 'all'],
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

    parser.add_argument(
        '--sql-compress',
        action='store_true',
        help='SqlContent_compressed.db를 사용하여 압축 모드 리포트 생성'
    )
    
    
    return parser.parse_args()


def validate_project(project_name: str, path_utils: PathUtils) -> bool:
    """
    프로젝트 유효성 검증 (대소문자 정확히 일치하는 프로젝트만 허용)
    
    Args:
        project_name: 검증할 프로젝트명
        path_utils: 경로 유틸리티
        
    Returns:
        프로젝트가 유효하면 True, 아니면 False
        
    Raises:
        Exception: 프로젝트가 존재하지 않거나 메타데이터베이스가 없는 경우
    """
    try:
        import os
        
        # 1. projects 디렉토리 확인
        projects_root = path_utils.join_path('projects')
        if not os.path.exists(projects_root):
            app_logger.error(f"projects 디렉토리가 존재하지 않습니다: {projects_root}")
            return False
        
        # 2. 프로젝트명 정확성 검증 (대소문자 엄격 구분)
        real_projects = os.listdir(projects_root)
        
        if project_name not in real_projects:
            # 대소문자만 다른 프로젝트가 있는지 확인 (에러 메시지용)
            candidates = [p for p in real_projects if p.lower() == project_name.lower()]
            if candidates:
                app_logger.error(f"프로젝트명 대소문자가 일치하지 않습니다.")
                app_logger.error(f"입력: '{project_name}' -> 실제: '{candidates[0]}'")
                raise Exception(f"프로젝트명이 정확하지 않습니다. '{project_name}' 대신 '{candidates[0]}'를 사용하세요.")
            else:
                app_logger.error(f"프로젝트가 존재하지 않습니다: '{project_name}'")
                return False
        
        # 3. 메타데이터베이스 파일 존재 확인
        metadata_db_path = path_utils.get_project_metadata_db_path(project_name)
        if not os.path.exists(metadata_db_path):
            app_logger.error(f"메타데이터베이스가 존재하지 않습니다: {metadata_db_path}")
            return False
            
        # 4. DB 내용 검증 (빈 깡통 DB 확인)
        try:
            import sqlite3
            conn = sqlite3.connect(f"file:{metadata_db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            
            # tables 테이블 존재 확인
            cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='tables'")
            if cursor.fetchone()[0] == 0:
                conn.close()
                app_logger.error(f"메타데이터 DB가 초기화되지 않았습니다 (테이블 스키마 없음).")
                return False
                
            # 데이터 존재 확인
            cursor.execute("SELECT count(*) FROM tables")
            table_count = cursor.fetchone()[0]
            conn.close()
            
            if table_count == 0:
                app_logger.error(f"메타데이터 DB에 분석된 데이터가 없습니다 (테이블 0개).")
                return False
                
        except Exception as db_err:
            app_logger.error(f"DB 검증 중 오류 발생: {db_err}")
            return False
        
        app_logger.info(f"프로젝트 유효성 검증 완료: {project_name} (테이블 {table_count}개)")
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
        
        app_logger.debug(f"출력 디렉토리 준비 완료: {output_path}")
        return output_path
        
    except Exception as e:
        handle_error(e, f"출력 디렉토리 생성 실패: {output_path}")
        return ""


def generate_callchain_report(project_name: str, output_dir: str) -> bool:
    """CallChain Report 생성"""
    try:
        generator = CallChainReportGenerator(project_name, output_dir)
        success = generator.generate_report()
        return success
            
    except Exception as e:
        handle_error(e, "CallChain Report 생성 중 오류 발생")
        return False


def generate_erd_report(project_name: str, output_dir: str) -> bool:
    """ERD Report 생성 (고아 테이블 자동 제외)"""
    try:
        # 고아 테이블은 무조건 제외 (include_orphan_tables=False 고정)
        generator = ERDReportGenerator(project_name, output_dir, include_orphan_tables=False)
        success = generator.generate_report()
        return success

    except Exception as e:
        handle_error(e, "ERD Report 생성 중 오류 발생")
        return False




def generate_erd_dagre_report(project_name: str, output_dir: str, show_attributes: bool = True) -> bool:
    """ERD(Dagre) Report 생성 (고아 테이블 자동 제외)"""
    try:
        # 고아 테이블은 무조건 제외 (include_orphan_tables=False 고정)
        generator = ERDDagreReportGenerator(project_name, output_dir, include_orphan_tables=False, show_attributes=show_attributes)
        success = generator.generate_report()
        return success

    except Exception as e:
        handle_error(e, "ERD(Dagre) Report 생성 중 오류 발생")
        return False


def generate_architecture_report(project_name: str, output_dir: str) -> bool:
    """Architecture Report 생성"""
    try:
        generator = ArchitectureReportGenerator(project_name, output_dir)
        success = generator.generate_report()
        return success
            
    except Exception as e:
        handle_error(e, "Architecture Report 생성 중 오류 발생")
        return False


def generate_architecture_layer_report(project_name: str, output_dir: str) -> bool:
    """새로운 아키텍처 레이어 다이어그램 리포트 생성 (USER RULES 준수)"""
    try:
        # USER RULES: 공통함수 사용, 하드코딩 금지
        generator = ArchitectureLayerReportGenerator(project_name, output_dir)
        success = generator.generate_report()
        return success
            
    except Exception as e:
        # USER RULES: handle_error()로 예외 처리 및 Exit
        handle_error(e, "Architecture Layer Report 생성 중 오류 발생")
        return False


def generate_sequence_diagram_report(project_name: str, output_dir: str) -> bool:
    """Sequence Diagram Report 생성 (USER RULES 준수)"""
    try:
        # USER RULES: 공통함수 사용, 하드코딩 금지, 예외처리 handle_error() 적용
        generator = SequenceDiagramReportGenerator(project_name, output_dir)
        success = generator.generate_report()
        return success
            
    except Exception as e:
        # USER RULES: handle_error()로 예외 처리 및 Exit
        handle_error(e, "Sequence Diagram Report 생성 중 오류 발생")
        return False


def generate_query_list_report(project_name: str, output_dir: str) -> bool:
    """Query List Report 생성"""
    try:
        generator = QueryListReportGenerator(project_name, output_dir)
        success = generator.generate_report()
        return success
            
    except Exception as e:
        handle_error(e, "Query List Report 생성 중 오류 발생")
        return False


def generate_backend_mapping_report(project_name: str, output_dir: str) -> bool:
    """Backend Mapping Report 생성"""
    try:
        generator = BackendMappingReportGenerator(project_name, output_dir)
        success = generator.generate_report()
        return success

    except Exception as e:
        handle_error(e, "Backend Mapping Report 생성 중 오류 발생")
        return False


def generate_frontend_mapping_report(project_name: str, output_dir: str) -> bool:
    """Frontend Mapping Report 생성"""
    try:
        generator = FrontendMappingReportGenerator(project_name, output_dir)
        success = generator.generate_report()
        return success

    except Exception as e:
        handle_error(e, "Frontend Mapping Report 생성 중 오류 발생")
        return False


def main():
    """메인 함수"""
    try:
        app_logger.info("SourceAnalyzer 리포트 생성 도구 시작")
        
        # 명령행 인자 파싱
        args = parse_arguments()

        # 런타임 옵션 설정 (압축 여부)
        set_sql_compress(getattr(args, "sql_compress", False))
        app_logger.info(f"SQL 압축 리포트 모드: {get_sql_compress()}")

        # 상세 로그 설정
        if getattr(args, "verbose", False):
            app_logger.logger.setLevel("DEBUG")
        
        # 경로 유틸리티 초기화
        path_utils = PathUtils()
        
        # 프로젝트 유효성 검증
        if not validate_project(args.project_name, path_utils):
            handle_error(Exception("프로젝트 유효성 검증 실패"), "프로젝트 유효성 검증 실패")
            sys.exit(1)  # 검증 실패 시 즉시 종료
        
        # 출력 디렉토리 생성
        output_dir = create_output_directory(args.project_name, path_utils, args.output_dir)
        if not output_dir:
            handle_error(Exception("출력 디렉토리 생성 실패"), "출력 디렉토리 생성 실패")
            sys.exit(1)  # 디렉토리 생성 실패 시 즉시 종료
        
        # 리포트 생성
        success_count = 0
        total_count = 0
        failed_reports = []
        
        if args.report_type in ['callchain', 'all']:
            app_logger.info("\n\n\n\n1단계 시작 ========================================")
            app_logger.info("CallChain Report 생성")
            total_count += 1
            if generate_callchain_report(args.project_name, output_dir):
                success_count += 1
                app_logger.info("성공: CallChain Report 생성 완료")
            else:
                failed_reports.append("CallChain Report")
                app_logger.info("실패: CallChain Report 생성 실패")
        
        if args.report_type in ['erd', 'all']:
            app_logger.info("\n\n\n\n2단계 시작 ========================================")
            app_logger.info("ERD Report 생성 (고아 테이블 자동 제외)")
            total_count += 1
            if generate_erd_report(args.project_name, output_dir):
                success_count += 1
                app_logger.info("성공: ERD Report 생성 완료")
            else:
                failed_reports.append("ERD Report")
                app_logger.info("실패: ERD Report 생성 실패")
        
        if args.report_type in ['erd-dagre', 'all']:
            app_logger.info("\n\n\n\n3단계 시작 ========================================")
            app_logger.info("ERD(Dagre) Report 생성 (컬럼 표시, 고아 테이블 자동 제외)")
            total_count += 1
            if generate_erd_dagre_report(args.project_name, output_dir, show_attributes=True):
                success_count += 1
                app_logger.info("성공: ERD(Dagre) Report 생성 완료")
            else:
                failed_reports.append("ERD(Dagre) Report")
                app_logger.info("실패: ERD(Dagre) Report 생성 실패")

        if args.report_type == 'erd-dagre-no-attribute':
            app_logger.info("\n\n\n\n3단계 시작 ========================================")
            app_logger.info("ERD(Dagre) Report 생성 (컬럼 미표시, 고아 테이블 자동 제외)")
            total_count += 1
            if generate_erd_dagre_report(args.project_name, output_dir, show_attributes=False):
                success_count += 1
                app_logger.info("성공: ERD(Dagre-No-Attribute) Report 생성 완료")
            else:
                failed_reports.append("ERD(Dagre-No-Attribute) Report")
                app_logger.info("실패: ERD(Dagre-No-Attribute) Report 생성 실패")
        
        if args.report_type in ['architecture', 'all']:
            app_logger.info("\n\n\n\n4단계 시작 ========================================")
            app_logger.info("Architecture Report 생성")
            total_count += 1
            if generate_architecture_report(args.project_name, output_dir):
                success_count += 1
                app_logger.info("성공: Architecture Report 생성 완료")
            else:
                failed_reports.append("Architecture Report")
                app_logger.info("실패: Architecture Report 생성 실패")
        
        if args.report_type in ['architecture-layer', 'all']:
            app_logger.info("\n\n\n\n5단계 시작 ========================================")
            app_logger.info("Architecture Layer Report 생성")
            total_count += 1
            if generate_architecture_layer_report(args.project_name, output_dir):
                success_count += 1
                app_logger.info("성공: Architecture Layer Report 생성 완료")
            else:
                failed_reports.append("Architecture Layer Report")
                app_logger.info("실패: Architecture Layer Report 생성 실패")
        
        if args.report_type in ['sequence', 'all']:
            app_logger.info("\n\n\n\n6단계 시작 ========================================")
            app_logger.info("Sequence Diagram Report 생성")
            total_count += 1
            if generate_sequence_diagram_report(args.project_name, output_dir):
                success_count += 1
                app_logger.info("성공: Sequence Diagram Report 생성 완료")
            else:
                failed_reports.append("Sequence Diagram Report")
                app_logger.info("실패: Sequence Diagram Report 생성 실패")
        
        if args.report_type in ['query-list', 'all']:
            app_logger.info("\n\n\n\n7단계 시작 ========================================")
            app_logger.info("Query List Report 생성")
            total_count += 1
            if generate_query_list_report(args.project_name, output_dir):
                success_count += 1
                app_logger.info("성공: Query List Report 생성 완료")
            else:
                failed_reports.append("Query List Report")
                app_logger.info("실패: Query List Report 생성 실패")
        
        if args.report_type in ['backend-mapping', 'all']:
            app_logger.info("\n\n\n\n8단계 시작 ========================================")
            app_logger.info("Backend Mapping Report 생성")
            total_count += 1
            if generate_backend_mapping_report(args.project_name, output_dir):
                success_count += 1
                app_logger.info("성공: Backend Mapping Report 생성 완료")
            else:
                failed_reports.append("Backend Mapping Report")
                app_logger.info("실패: Backend Mapping Report 생성 실패")

        if args.report_type in ['frontend-mapping', 'all']:
            app_logger.info("\n\n\n\n9단계 시작 ========================================")
            app_logger.info("Frontend Mapping Report 생성")
            total_count += 1
            if generate_frontend_mapping_report(args.project_name, output_dir):
                success_count += 1
                app_logger.info("성공: Frontend Mapping Report 생성 완료")
            else:
                failed_reports.append("Frontend Mapping Report")
                app_logger.info("실패: Frontend Mapping Report 생성 실패")
        
        # 결과 출력
        app_logger.info(f"\n\n\n\n=== 리포트 생성 완료 ===")
        app_logger.info(f"성공: {success_count}/{total_count}")
        if failed_reports:
            app_logger.info(f"실패: {len(failed_reports)}건 ({', '.join(failed_reports)})")
        else:
            app_logger.info("실패: 0건")
        app_logger.info(f"출력 디렉토리: {output_dir}")
        
        if success_count == total_count:
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
