"""
실행 옵션 전역 관리 모듈
- 명령행 플래그 등을 중앙에서 관리하여 함수 인자 중복을 줄이고 일관성 유지
"""

from typing import Optional

# 전역 옵션 값
_sql_compress: bool = False


def set_sql_compress(value: bool) -> None:
    """SQL 압축 사용 여부 설정"""
    global _sql_compress
    _sql_compress = bool(value)


def get_sql_compress() -> bool:
    """SQL 압축 사용 여부 반환 (기본 False)"""
    return _sql_compress


def reset_runtime_options() -> None:
    """테스트용 리셋 함수"""
    set_sql_compress(False)
