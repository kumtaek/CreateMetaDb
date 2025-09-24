"""
SourceAnalyzer 공통 로깅 및 에러 처리 모듈
- 파일명.라인번호 포함한 로그
- SourceAnalyzer_{timestamp}.log 파일에 기록
- Exception 발생 시 라인번호 포함한 에러 로그 기록 및 프로그램 종료
- 중앙 집중식 로깅 설정 사용
- 안전한 로그 파일 핸들링 적용
"""

import sys
import logging
import logging.config
import os
import traceback
import yaml
from datetime import datetime
from typing import Optional


class SourceAnalyzerLogger:
    """SourceAnalyzer 전용 로거 클래스"""
    
    def __init__(self, logger_name: str = "SourceAnalyzer"):
        """
        Args:
            logger_name: 로거 이름
        """
        self.logger_name = logger_name
        self.logger = logging.getLogger(logger_name)
        self.log_file_path = self._get_log_file_path()
        self._setup_logger()
    
    def _get_log_file_path(self) -> str:
        """로그 파일 경로 생성"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"logs/SourceAnalyzer_{timestamp}.log"
    
    def _setup_logger(self):
        """로거 설정 - 중앙 집중식 설정 파일 사용"""
        try:
            # 로깅 설정 파일 로드 (circular import 완전 방지)
            config_path = os.path.join("config", "logging.yaml")
            print(f"[DEBUG] 로깅 설정 파일 경로: {config_path}")
            print(f"[DEBUG] 로깅 설정 파일 존재: {os.path.exists(config_path)}")
            
            if os.path.exists(config_path):
                try:
                    print(f"[DEBUG] 로깅 설정 파일 읽기 시도")
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                    print(f"[DEBUG] YAML 파싱 성공")
                    
                    # 로그 디렉토리 생성
                    os.makedirs("logs", exist_ok=True)
                    print(f"[DEBUG] logs 디렉토리 생성 완료")
                    
                    # 로깅 설정 적용
                    logging.config.dictConfig(config)
                    print(f"[DEBUG] 로깅 설정 적용 완료")
                    
                    # SourceAnalyzer 전용 로거 가져오기
                    self.logger = logging.getLogger('SourceAnalyzer')
                    print(f"[DEBUG] SourceAnalyzer 로거 생성 완료")
                    
                    # 파일 핸들러에 타임스탬프가 포함된 파일명 설정
                    print(f"[DEBUG] 기존 핸들러 수: {len(self.logger.handlers)}")
                    
                    for handler in self.logger.handlers:
                        print(f"[DEBUG] 핸들러 타입: {type(handler)}")
                        if isinstance(handler, logging.FileHandler):
                            # 기존 핸들러 제거하고 새로운 파일 핸들러 추가
                            print(f"[DEBUG] 기존 파일 핸들러 제거")
                            self.logger.removeHandler(handler)
                            
                    # 새로운 파일 핸들러 추가
                    new_file_handler = logging.FileHandler(
                        self.log_file_path,
                        encoding='utf-8'
                    )
                    new_file_handler.setLevel(logging.INFO)
                    formatter = logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
                    )
                    new_file_handler.setFormatter(formatter)
                    self.logger.addHandler(new_file_handler)
                    print(f"[DEBUG] 새로운 파일 핸들러 추가 완료")
                    
                    self.logger.setLevel(logging.INFO)
                    print(f"[DEBUG] 로거 레벨 설정: INFO")
                    print(f"[DEBUG] 최종 핸들러 수: {len(self.logger.handlers)}")
                    print(f"[DEBUG] 로깅 시스템 초기화 완료")
                    
                    # 테스트 로그 출력
                    self.logger.info("로깅 시스템 테스트 - 이 메시지가 보이면 정상 작동")
                    print(f"[DEBUG] 테스트 로그 출력 완료")
                    
                except Exception as config_error:
                    # USER RULES: 설정 파일 처리 오류는 치명적, print 후 exit
                    print(f"로깅 설정 처리 실패: {config_error}")
                    print("FATAL: 로깅 설정 파일 처리 실패로 프로그램을 종료합니다.")
                    sys.exit(1)
            else:
                # USER RULES: 설정 파일이 없으면 치명적 오류, print 후 exit
                print(f"로깅 설정 파일이 없습니다: {config_path}")
                print("FATAL: 로깅 설정 파일 부재로 프로그램을 종료합니다.")
                sys.exit(1)
                
        except Exception as e:
            # USER RULES: exception 발생시 로그 남기고 Exit! (handle_error import 순환 끊음)
            print(f"로깅 시스템 초기화 실패: {e}")
            print("FATAL: 로깅 시스템 초기화 실패로 프로그램을 종료합니다.")
            sys.exit(1)  # handle_error() import 순환을 끊고 바로 Exit
    
    def _setup_default_logger(self):
        """기본 로거 설정 (fallback)"""
        if not self.logger.handlers:
            # 로그 디렉토리 생성
            os.makedirs("logs", exist_ok=True)
            
            # 콘솔 핸들러
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # 파일 핸들러
            file_handler = logging.FileHandler(
                self.log_file_path,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            
            # 포맷터 (파일명.라인번호 포함)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
            )
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.INFO)
    
    def debug(self, message: str) -> None:
        """DEBUG 레벨 로그"""
        try:
            # stacklevel=2: debug() -> 실제 호출한 코드 (logger.py의 debug 메서드를 건너뛰고 실제 호출자로 이동)
            self.logger.debug(message, stacklevel=2)
        except RecursionError:
            # Recursion limit 초과시 print로 fallback
            print(f"[DEBUG] {message}")
    
    def info(self, message: str) -> None:
        """INFO 레벨 로그"""
        try:
            # stacklevel=2: info() -> 실제 호출한 코드
            self.logger.info(message, stacklevel=2)
        except RecursionError:
            # Recursion limit 초과시 print로 fallback
            print(f"[INFO] {message}")
    
    def warning(self, message: str) -> None:
        """WARNING 레벨 로그"""
        try:
            # stacklevel=2: warning() -> 실제 호출한 코드
            self.logger.warning(message, stacklevel=2)
        except RecursionError:
            # Recursion limit 초과시 print로 fallback
            print(f"[WARNING] {message}")
    
    def error(self, message: str) -> None:
        """ERROR 레벨 로그"""
        try:
            # stacklevel=2: error() -> 실제 호출한 코드
            self.logger.error(message, stacklevel=2)
        except RecursionError:
            # Recursion limit 초과시 print로 fallback
            print(f"[ERROR] {message}")
    
    def critical(self, message: str) -> None:
        """CRITICAL 레벨 로그"""
        try:
            # stacklevel=2: critical() -> 실제 호출한 코드
            self.logger.critical(message, stacklevel=2)
        except RecursionError:
            # Recursion limit 초과시 print로 fallback
            print(f"[CRITICAL] {message}")
    
    def get_log_file_path(self) -> str:
        """현재 로그 파일 경로 반환"""
        return self.log_file_path
    
    def handle_error(self, 
                    error, 
                    custom_message: Optional[str] = None,
                    exit_code: int = 1) -> None:
        """
        에러 로그 기록 후 프로그램 종료
        
        Args:
            error: 발생한 Exception 또는 에러 메시지 문자열
            custom_message: 추가 메시지
            exit_code: 종료 코드 (기본값: 1)
        """
        # error가 문자열인 경우 현재 호출 스택에서 실제 호출 위치 찾기
        if isinstance(error, str):
            error_message = error
            custom_message = custom_message or error_message
            
            # 현재 호출 스택에서 handle_error를 호출한 위치 찾기
            try:
                current_stack = traceback.extract_stack()
                # handle_error 호출한 프레임 찾기 (마지막에서 2번째)
                if len(current_stack) >= 2:
                    caller_frame = current_stack[-2]  # handle_error를 호출한 위치
                    filename = caller_frame.filename
                    line_number = caller_frame.lineno
                    function_name = caller_frame.name
                    code_line = caller_frame.line
                    
                    # 에러 메시지 구성
                    error_msg = f"FATAL ERROR at {filename}:{line_number} in {function_name}()"
                    if code_line:
                        error_msg += f"\nCode: {code_line.strip()}"
                    
                    if custom_message:
                        error_msg += f"\nMessage: {custom_message}"
                    
                    error_msg += f"\nException: {error_message}"
                    
                    self.logger.error(error_msg)
                    sys.exit(exit_code)
                    return
                    
            except Exception:
                # 스택 추출 실패시 단순 메시지만 출력
                self.logger.error(f"FATAL ERROR: {error_message}")
                if custom_message:
                    self.logger.error(f"Message: {custom_message}")
                sys.exit(exit_code)
                return
        
        # Exception 객체인 경우 기존 방식으로 처리
        try:
            tb = traceback.extract_tb(error.__traceback__)
        except (AttributeError, RecursionError):
            # traceback 처리에서 오류 발생시 fallback
            self.logger.error(f"[ERROR] Traceback processing failed")
            tb = None
        if tb:
            # 가장 최근 프레임 (에러 발생 위치)
            frame = tb[-1]
            filename = frame.filename
            line_number = frame.lineno
            function_name = frame.name
            code_line = frame.line
            
            # 에러 메시지 구성
            error_msg = f"FATAL ERROR at {filename}:{line_number} in {function_name}()"
            if code_line:
                error_msg += f"\nCode: {code_line.strip()}"
            
            if custom_message:
                error_msg += f"\nMessage: {custom_message}"
            
            error_msg += f"\nException: {type(error).__name__}: {str(error)}"
            
            # 스택 트레이스 추가
            error_msg += f"\nStack Trace:\n{traceback.format_exc()}"
            
        else:
            # 스택 트레이스가 없는 경우
            error_msg = f"FATAL ERROR: {type(error).__name__}: {str(error)}"
            if custom_message:
                error_msg += f"\nMessage: {custom_message}"
        
        # 에러 로그 기록
        self.logger.error(error_msg)
        
        # 로그 파일에 쓰기 완료를 보장하기 위해 잠시 대기
        import time
        time.sleep(0.2)  # 200ms 대기
        
        # 프로그램 종료
        self.logger.error(f"\n[FATAL ERROR] 프로그램이 에러로 인해 종료됩니다. (종료코드: {exit_code})")
        self.logger.error(f"자세한 내용은 로그 파일을 확인하세요: {self.log_file_path}")
        
        # 종료 전 추가 대기
        time.sleep(0.1)
        sys.exit(exit_code)


# 전역 로거 인스턴스
app_logger = SourceAnalyzerLogger()


# 편의 함수들
def debug(message: str) -> None:
    """DEBUG 로그 편의 함수"""
    try:
        app_logger.logger.debug(message, stacklevel=2)
    except RecursionError:
        print(f"[DEBUG] {message}")


def info(message: str) -> None:
    """INFO 로그 편의 함수"""
    try:
        app_logger.logger.info(message, stacklevel=2)
    except RecursionError:
        print(f"[INFO] {message}")


def warning(message: str) -> None:
    """WARNING 로그 편의 함수"""
    try:
        app_logger.logger.warning(message, stacklevel=2)
    except RecursionError:
        print(f"[WARNING] {message}")


def error(message: str) -> None:
    """ERROR 로그 편의 함수"""
    try:
        app_logger.logger.error(message, stacklevel=2)
    except RecursionError:
        print(f"[ERROR] {message}")


def critical(message: str) -> None:
    """CRITICAL 로그 편의 함수"""
    try:
        app_logger.logger.critical(message, stacklevel=2)
    except RecursionError:
        print(f"[CRITICAL] {message}")


def get_log_file_path() -> str:
    """현재 로그 파일 경로 반환"""
    return app_logger.get_log_file_path()


def handle_error(error: Exception, 
                custom_message: Optional[str] = None,
                exit_code: int = 1) -> None:
    """
    전역 에러 처리 함수 (편의 함수)
    
    Args:
        error: 발생한 Exception
        custom_message: 추가 메시지
        exit_code: 종료 코드
    """
    # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
    app_logger.handle_error(error, custom_message, exit_code)


# 사용 예시
if __name__ == "__main__":
    debug("디버그 메시지 테스트")
    info("정보 메시지 테스트")
    warning("경고 메시지 테스트")
    error("에러 메시지 테스트")
    critical("치명적 에러 메시지 테스트")
    
    info(f"로그 파일 위치: {get_log_file_path()}")
    
    # 에러 처리 테스트
    try:
        result = 1 / 0
    except Exception as e:
        handle_error(e, "테스트 에러 발생")


# =============================================================================
# 안전한 로거 통합 (하위 호환성 유지)
# =============================================================================

# 안전한 로거를 기본 로거로 설정하는 옵션
USE_SAFE_LOGGER = True

if USE_SAFE_LOGGER:
    try:
        from .safe_logger import (
            get_safe_logger, safe_info, safe_warning,
            safe_error, safe_debug, safe_handle_error
        )

        # 기존 함수들을 안전한 로거로 대체
        def safe_info_wrapper(message: str):
            safe_info(message)

        def safe_warning_wrapper(message: str):
            safe_warning(message)

        def safe_error_wrapper(message: str):
            safe_error(message)

        def safe_debug_wrapper(message: str):
            safe_debug(message)

        def safe_handle_error_wrapper(error, context: str = ""):
            safe_handle_error(error, context)

        # 안전한 로거가 사용 가능한 경우 기본 함수들을 대체
        # 단, 기존 코드 호환성을 위해 원래 함수들도 유지
        info_safe = safe_info_wrapper
        warning_safe = safe_warning_wrapper
        error_safe = safe_error_wrapper
        debug_safe = safe_debug_wrapper
        handle_error_safe = safe_handle_error_wrapper

    except ImportError:
        # 안전한 로거 모듈을 찾을 수 없는 경우 기존 로거 사용
        info_safe = info
        warning_safe = warning
        error_safe = error
        debug_safe = debug
        handle_error_safe = handle_error
