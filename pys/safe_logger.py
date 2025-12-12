"""
안전한 로그 파일 핸들링을 위한 개선된 로깅 시스템
- 파일 락 문제 해결
- 멀티프로세스 환경 대응
- 회전 로그 파일 지원
"""
import os
import sys
import logging
import logging.handlers
from datetime import datetime
from typing import Optional
import threading
import time
from pathlib import Path

class SafeFileHandler(logging.handlers.RotatingFileHandler):
    """안전한 파일 핸들러 - 파일 락 문제 해결"""

    def __init__(self, filename, mode='a', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'):
        """
        Args:
            filename: 로그 파일 경로
            mode: 파일 오픈 모드
            maxBytes: 최대 파일 크기 (기본 10MB)
            backupCount: 백업 파일 개수
            encoding: 인코딩
        """
        self._lock = threading.RLock()
        super().__init__(filename, mode, maxBytes, backupCount, encoding=encoding, delay=True)

    def emit(self, record):
        """로그 레코드 출력 - 안전한 파일 접근"""
        with self._lock:
            try:
                super().emit(record)
                # 강제로 버퍼 플러시
                if self.stream:
                    self.stream.flush()
                    os.fsync(self.stream.fileno())
            except (OSError, IOError) as e:
                # 파일 접근 오류 시 콘솔로 출력
                print(f"[LOG ERROR] 파일 쓰기 실패: {e}")
                print(f"[LOG] {self.format(record)}")
            except Exception as e:
                # 기타 오류
                print(f"[LOG ERROR] 예상치 못한 오류: {e}")
                self.handleError(record)

    def close(self):
        """핸들러 종료"""
        with self._lock:
            try:
                if self.stream:
                    self.stream.flush()
                    os.fsync(self.stream.fileno())
                super().close()
            except:
                pass  # 종료 시에는 오류 무시

class SafeLogger:
    """안전한 로거 클래스 - 싱글톤 패턴"""

    _instance: Optional['SafeLogger'] = None
    _initialized: bool = False
    _lock = threading.RLock()

    def __new__(cls, logger_name: str = "SourceAnalyzer") -> 'SafeLogger':
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SafeLogger, cls).__new__(cls)
            return cls._instance

    def __init__(self, logger_name: str = "SourceAnalyzer"):
        if not SafeLogger._initialized:
            with SafeLogger._lock:
                if not SafeLogger._initialized:
                    self.logger_name = logger_name
                    self.logger = None
                    self.log_file_path = None
                    self._setup_logger()
                    SafeLogger._initialized = True

    def _get_log_file_path(self) -> str:
        """로그 파일 경로 생성"""
        # logs 디렉토리 생성
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # 오래된 로그 파일 정리 (24시간 이상)
        self._cleanup_old_logs(log_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return log_dir / f"SourceAnalyzer_{timestamp}.log"

    def _cleanup_old_logs(self, log_dir: Path) -> None:
        """24시간 이상 된 로그 파일 삭제"""
        try:
            current_time = time.time()
            for log_file in log_dir.glob("SourceAnalyzer_*.log*"):
                if log_file.is_file():
                    file_time = log_file.stat().st_mtime
                    # 24시간 (86400초) 이상 된 파일 삭제
                    if current_time - file_time > 86400:
                        try:
                            log_file.unlink()
                        except:
                            pass  # 삭제 실패는 무시
        except:
            pass  # 정리 실패는 무시

    def _setup_logger(self):
        """로거 설정"""
        try:
            # 로그 파일 경로 설정
            self.log_file_path = self._get_log_file_path()

            # 로거 생성
            self.logger = logging.getLogger(self.logger_name)
            self.logger.setLevel(logging.INFO)

            # 기존 핸들러 제거
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)

            # 안전한 파일 핸들러 추가
            file_handler = SafeFileHandler(
                str(self.log_file_path),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)

            # 포매터 설정
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)

            # 콘솔 핸들러 추가 (오류 시 백업용)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(formatter)

            # 핸들러 등록
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

            # 테스트 로그
            self.logger.info(f"안전한 로깅 시스템 초기화 완료 - 로그 파일: {self.log_file_path}")

        except Exception as e:
            # 로거 설정 실패 시 기본 로거 사용
            self.logger = logging.getLogger(self.logger_name)
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.error(f"로거 설정 실패, 기본 로거 사용: {e}")

    def get_logger(self) -> logging.Logger:
        """로거 인스턴스 반환"""
        return self.logger

    def info(self, message: str, filename: str = None, line_no: int = None):
        """INFO 레벨 로그"""
        if filename and line_no:
            self.logger.info(f"{filename}:{line_no} - {message}")
        else:
            self.logger.info(message)

    def warning(self, message: str, filename: str = None, line_no: int = None):
        """WARNING 레벨 로그"""
        if filename and line_no:
            self.logger.warning(f"{filename}:{line_no} - {message}")
        else:
            self.logger.warning(message)

    def error(self, message: str, filename: str = None, line_no: int = None):
        """ERROR 레벨 로그"""
        if filename and line_no:
            self.logger.error(f"{filename}:{line_no} - {message}")
        else:
            self.logger.error(message)

    def debug(self, message: str, filename: str = None, line_no: int = None):
        """DEBUG 레벨 로그"""
        if filename and line_no:
            self.logger.debug(f"{filename}:{line_no} - {message}")
        else:
            self.logger.debug(message)

    def close(self):
        """로거 종료"""
        if self.logger:
            for handler in self.logger.handlers[:]:
                try:
                    handler.close()
                    self.logger.removeHandler(handler)
                except:
                    pass

# 전역 싱글톤 인스턴스
_safe_logger: Optional[SafeLogger] = None

def get_safe_logger() -> SafeLogger:
    """안전한 로거 인스턴스 반환"""
    global _safe_logger
    if _safe_logger is None:
        _safe_logger = SafeLogger()
    return _safe_logger

def safe_info(message: str):
    """안전한 INFO 로그"""
    get_safe_logger().info(message)

def safe_warning(message: str):
    """안전한 WARNING 로그"""
    get_safe_logger().warning(message)

def safe_error(message: str):
    """안전한 ERROR 로그"""
    get_safe_logger().error(message)

def safe_debug(message: str):
    """안전한 DEBUG 로그"""
    get_safe_logger().debug(message)

def safe_handle_error(error: Exception, context: str = ""):
    """안전한 에러 핸들링"""
    logger = get_safe_logger()
    error_msg = f"ERROR: {context} - {str(error)}"
    logger.error(error_msg)

    # 스택 트레이스 로깅
    import traceback
    stack_trace = traceback.format_exc()
    logger.error(f"Stack trace: {stack_trace}")

    # 프로그램 종료
    print(f"FATAL ERROR: {error_msg}")
    sys.exit(1)