"""
SourceAnalyzer 명령행 인자 처리 공통 유틸리티 모듈
- --project-name 파라미터 처리
- 명령행 인자 검증
- 도움말 메시지 생성
"""

import argparse
import sys
from typing import Optional, List, Dict, Any
from .logger import app_logger, handle_error
from .validation_utils import ValidationUtils


class ArgUtils:
    """명령행 인자 처리 관련 공통 유틸리티 클래스"""
    
    def __init__(self):
        """인자 유틸리티 초기화"""
        self.parser = None
        self.args = None
    
    def create_parser(self, description: str = "SourceAnalyzer - 소스코드 분석 도구") -> argparse.ArgumentParser:
        """
        명령행 인자 파서 생성
        
        Args:
            description: 프로그램 설명
            
        Returns:
            ArgumentParser 인스턴스
        """
        try:
            self.parser = argparse.ArgumentParser(
                description=description,
                formatter_class=argparse.RawDescriptionHelpFormatter,
                epilog="""
사용 예시:
  python main.py --project-name sampleSrc
  python main.py --project-name myProject --clear-metadb
  python main.py --project-name testProject --verbose
  python main.py --project-name sampleSrc --sql-content
                """
            )
            
            # 필수 인자: 프로젝트명
            self.parser.add_argument(
                '--project-name',
                type=str,
                required=True,
                help='분석할 프로젝트명 (필수)'
            )
            
            # 선택적 인자들
            self.parser.add_argument(
                '--clear-metadb',
                action='store_true',
                help='메타데이터베이스를 초기화하고 새로 생성'
            )
            
            self.parser.add_argument(
                '--verbose',
                action='store_true',
                help='상세한 로그 출력'
            )
            
            self.parser.add_argument(
                '--output-format',
                type=str,
                choices=['html', 'markdown', 'json'],
                default='html',
                help='출력 형식 (기본값: html)'
            )
            
            self.parser.add_argument(
                '--config-file',
                type=str,
                help='사용할 설정 파일 경로 (기본값: config/config.yaml)'
            )
            
            self.parser.add_argument(
                '--log-level',
                type=str,
                choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                default='INFO',
                help='로그 레벨 (기본값: INFO)'
            )
            
            self.parser.add_argument(
                '--dry-run',
                action='store_true',
                help='실제 분석 없이 설정만 확인'
            )
            
            self.parser.add_argument(
                '--force',
                action='store_true',
                help='기존 결과를 덮어쓰기'
            )
            
            self.parser.add_argument(
                '--sql-content',
                action='store_true',
                help='SQL Content 데이터베이스 생성 기능 활성화 (부속 기능)'
            )
        
        except RecursionError as e:
            # Recursion limit 초과시 fallback
            from util.logger import info
            info(f"RecursionError in argparse: {str(e)}")
            info("Using fallback argument parser")
            # 간단한 fallback 파서 생성 (parser 대신 직접 args 반환)
            self.parser = None  # parser는 None으로 설정
            self.fallback_args = self._create_fallback_parser()  # fallback args 저장
        
        return self.parser
    
    def _create_fallback_parser(self):
        """RecursionError 발생시 사용할 간단한 fallback 파서"""
        # argparse도 RecursionError가 발생할 수 있으므로 수동 파싱 사용
        class FallbackArgs:
            def __init__(self):
                self.project_name = None
                self.clear_metadb = False
                self.verbose = False
                self.config_file = None
                self.log_level = 'INFO'
                self.output_format = 'html'
                self.dry_run = False
                self.force = False
                
            def parse_sys_argv(self):
                import sys
                args = sys.argv[1:]
                for i, arg in enumerate(args):
                    if arg == '--project-name' and i + 1 < len(args):
                        self.project_name = args[i + 1]
                    elif arg == '--clear-metadb':
                        self.clear_metadb = True
                    elif arg == '--verbose':
                        self.verbose = True
                return self
        
        return FallbackArgs().parse_sys_argv()
    
    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """
        명령행 인자 파싱
        
        Args:
            args: 파싱할 인자 리스트 (기본값: sys.argv[1:])
            
        Returns:
            파싱된 인자 네임스페이스
        """
        if self.parser is None:
            self.create_parser()
        
        # fallback args가 있는 경우 (RecursionError 발생)
        if hasattr(self, 'fallback_args') and self.fallback_args:
            from util.logger import info
            info("Using fallback argument parsing")
            return self.fallback_args
        
        try:
            self.args = self.parser.parse_args(args)
            app_logger.debug(f"명령행 인자 파싱 완료: {vars(self.args)}")
            return self.args
            
        except SystemExit as e:
            if e.code == 2:  # 인자 오류
                app_logger.error("명령행 인자 오류")
            elif e.code == 0:  # 도움말 출력
                app_logger.info("도움말 출력")
            sys.exit(e.code)
        except Exception as e:
            handle_error(e, "인자 파싱 실패")
            sys.exit(1)
    
    def validate_args(self, args: argparse.Namespace) -> bool:
        """
        파싱된 인자 검증
        
        Args:
            args: 검증할 인자 네임스페이스
            
        Returns:
            검증 성공 여부 (True/False)
        """
        try:
            # 프로젝트명 검증
            if not ValidationUtils.is_valid_project_name(args.project_name):
                app_logger.error(f"잘못된 프로젝트명: {args.project_name}")
                app_logger.error("프로젝트명은 영문자, 숫자, 하이픈, 언더스코어만 사용 가능합니다")
                return False
            
            # 설정 파일 경로 검증 (지정된 경우)
            if args.config_file:
                if not ValidationUtils.is_valid_file_path(args.config_file):
                    app_logger.error(f"잘못된 설정 파일 경로: {args.config_file}")
                    return False
            
            app_logger.debug("인자 검증 성공")
            return True
            
        except Exception as e:
            handle_error(e, "인자 검증 실패")
            return False
    
    def get_project_name(self) -> Optional[str]:
        """
        프로젝트명 반환
        
        Returns:
            프로젝트명 또는 None
        """
        if self.args:
            return self.args.project_name
        return None
    
    def get_clear_metadb(self) -> bool:
        """
        메타데이터베이스 초기화 여부 반환
        
        Returns:
            초기화 여부 (True/False)
        """
        if self.args:
            return getattr(self.args, 'clear_metadb', False)
        return False
    
    def get_verbose(self) -> bool:
        """
        상세 로그 출력 여부 반환
        
        Returns:
            상세 로그 여부 (True/False)
        """
        if self.args:
            return getattr(self.args, 'verbose', False)
        return False
    
    def get_output_format(self) -> str:
        """
        출력 형식 반환
        
        Returns:
            출력 형식 (html, markdown, json)
        """
        if self.args:
            return getattr(self.args, 'output_format', 'html')
        return 'html'
    
    def get_config_file(self) -> Optional[str]:
        """
        설정 파일 경로 반환
        
        Returns:
            설정 파일 경로 또는 None
        """
        if self.args:
            return getattr(self.args, 'config_file', None)
        return None
    
    def get_log_level(self) -> str:
        """
        로그 레벨 반환
        
        Returns:
            로그 레벨
        """
        if self.args:
            return getattr(self.args, 'log_level', 'INFO')
        return 'INFO'
    
    def get_dry_run(self) -> bool:
        """
        드라이런 모드 여부 반환
        
        Returns:
            드라이런 여부 (True/False)
        """
        if self.args:
            return getattr(self.args, 'dry_run', False)
        return False
    
    def get_force(self) -> bool:
        """
        강제 실행 여부 반환
        
        Returns:
            강제 실행 여부 (True/False)
        """
        if self.args:
            return getattr(self.args, 'force', False)
        return False
    
    def get_sql_content(self) -> bool:
        """
        SQL Content 기능 활성화 여부 반환
        
        Returns:
            SQL Content 기능 활성화 여부 (True/False)
        """
        if self.args:
            return getattr(self.args, 'sql_content', False)
        return False
    
    def get_all_args(self) -> Dict[str, Any]:
        """
        모든 인자를 딕셔너리로 반환
        
        Returns:
            인자 딕셔너리
        """
        if self.args:
            return vars(self.args)
        return {}
    
    def print_help(self):
        """도움말 출력"""
        if self.parser:
            self.parser.print_help()
    
    def print_usage(self):
        """사용법 출력"""
        if self.parser:
            self.parser.print_usage()
    
    def create_custom_parser(self, 
                           required_args: List[str] = None,
                           optional_args: List[Dict[str, Any]] = None) -> argparse.ArgumentParser:
        """
        커스텀 인자 파서 생성
        
        Args:
            required_args: 필수 인자 리스트
            optional_args: 선택적 인자 리스트
            
        Returns:
            커스텀 ArgumentParser 인스턴스
        """
        parser = argparse.ArgumentParser(
            description="SourceAnalyzer - 커스텀 인자 파서",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # 필수 인자 추가
        if required_args:
            for arg in required_args:
                if isinstance(arg, str):
                    parser.add_argument(f'--{arg}', type=str, required=True, help=f'{arg} (필수)')
                elif isinstance(arg, dict):
                    parser.add_argument(**arg)
        
        # 선택적 인자 추가
        if optional_args:
            for arg in optional_args:
                parser.add_argument(**arg)
        
        return parser
    
    def validate_project_name_required(self, project_name: str) -> bool:
        """
        프로젝트명 필수 검증 (에러 시 프로그램 종료)
        
        Args:
            project_name: 검증할 프로젝트명
            
        Returns:
            검증 성공 여부 (True/False)
        """
        if not project_name:
            app_logger.error("프로젝트명이 지정되지 않았습니다")
            app_logger.error("사용법: python main.py --project-name {project_name}")
            if self.parser:
                self.parser.print_usage()
            sys.exit(1)
        
        if not ValidationUtils.is_valid_project_name(project_name):
            app_logger.error(f"잘못된 프로젝트명: {project_name}")
            app_logger.error("프로젝트명은 영문자, 숫자, 하이픈, 언더스코어만 사용 가능합니다")
            sys.exit(1)
        
        return True


# 편의 함수들
def parse_command_line_args(description: str = "SourceAnalyzer - 소스코드 분석 도구") -> argparse.Namespace:
    """
    명령행 인자 파싱 편의 함수
    
    Args:
        description: 프로그램 설명
        
    Returns:
        파싱된 인자 네임스페이스
    """
    arg_utils = ArgUtils()
    return arg_utils.parse_args()


def get_project_name_from_args() -> Optional[str]:
    """
    명령행 인자에서 프로젝트명 추출 편의 함수
    
    Returns:
        프로젝트명 또는 None
    """
    arg_utils = ArgUtils()
    args = arg_utils.parse_args()
    return arg_utils.get_project_name()


def validate_and_get_project_name() -> str:
    """
    프로젝트명 검증 및 반환 편의 함수 (에러 시 프로그램 종료)
    
    Returns:
        검증된 프로젝트명
    """
    arg_utils = ArgUtils()
    args = arg_utils.parse_args()
    
    project_name = arg_utils.get_project_name()
    arg_utils.validate_project_name_required(project_name)
    
    return project_name


def create_simple_parser(project_name_required: bool = True) -> argparse.ArgumentParser:
    """
    간단한 인자 파서 생성 편의 함수
    
    Args:
        project_name_required: 프로젝트명 필수 여부
        
    Returns:
        ArgumentParser 인스턴스
    """
    parser = argparse.ArgumentParser(description="SourceAnalyzer")
    
    parser.add_argument(
        '--project-name',
        type=str,
        required=project_name_required,
        help='분석할 프로젝트명'
    )
    
    return parser


def print_usage_and_exit(message: str = None):
    """
    사용법 출력 후 프로그램 종료 편의 함수
    
    Args:
        message: 추가 메시지
    """
    if message:
        app_logger.error(message)
    
    app_logger.error("사용법: python main.py --project-name {project_name}")
    sys.exit(1)
