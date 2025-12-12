"""
통합된 로거 및 에러 처리 사용 예시
"""

from logger import debug, info, warning, error, critical, handle_error, get_log_file_path


def example_integrated_logging():
    """통합 로깅 및 에러 처리 예시"""
    
    info("프로젝트 분석 시작")
    debug("설정 파일 로드 중...")
    
    try:
        # 파일 처리 시뮬레이션
        info("파일 스캔 중...")
        debug("파일: main.py, 크기: 1024 bytes")
        debug("파일: config.yaml, 크기: 512 bytes")
        
        # 의도적 에러 발생
        raise FileNotFoundError("설정 파일을 찾을 수 없습니다")
        
    except Exception as e:
        # 에러 처리 (프로그램 종료)
        handle_error(e, "파일 처리 중 오류 발생")
    
    # 이 코드는 실행되지 않음 (handle_error에서 exit)
    info("분석 완료")


def example_warning_only():
    """경고만 발생시키는 예시 (프로그램 종료하지 않음)"""
    
    info("경고 테스트 시작")
    warning("이 작업은 테스트용입니다")
    warning("실제 프로덕션에서는 주의하세요")
    info("경고 테스트 완료")


if __name__ == "__main__":
    print(f"로그 파일 위치: {get_log_file_path()}")
    
    # 경고 테스트 (프로그램 종료하지 않음)
    example_warning_only()
    
    print("\n" + "="*50)
    print("에러 테스트 (프로그램 종료됨)")
    print("="*50)
    
    # 에러 테스트 (프로그램 종료됨)
    example_integrated_logging()
