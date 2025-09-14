"""
전역 프로젝트 정보 관리 모듈

실행 중 변경되지 않는 프로젝트명과 프로젝트 ID를 전역적으로 관리

USER RULES:
- 하드코딩 지양: 실행시 설정된 값을 전역적으로 사용
- Exception 처리: handle_error() 공통함수 사용
- 공통함수 사용: util 모듈 활용
"""

from typing import Optional
from util import handle_error

# 전역 변수 (실행 중 변경되지 않는 값)
_project_name: Optional[str] = None
_project_id: Optional[int] = None


def set_global_project_info(project_name: str, project_id: int) -> None:
    """
    전역 프로젝트 정보 설정 (최초 실행시 한 번만 호출)

    Args:
        project_name: 프로젝트명
        project_id: 프로젝트 ID
    """
    global _project_name, _project_id
    _project_name = project_name
    _project_id = project_id


def get_global_project_name() -> str:
    """
    전역 프로젝트명 획득

    Returns:
        프로젝트명

    Raises:
        Exception: 프로젝트명이 설정되지 않은 경우
    """
    if _project_name is None:
        # USER RULES: Exception 발생시 handle_error()로 exit()
        handle_error(Exception("전역 프로젝트명이 설정되지 않았습니다"), "전역 프로젝트명 획득 실패")
    return _project_name


def get_global_project_id() -> int:
    """
    전역 프로젝트 ID 획득

    Returns:
        프로젝트 ID

    Raises:
        Exception: 프로젝트 ID가 설정되지 않은 경우
    """
    if _project_id is None:
        # USER RULES: Exception 발생시 handle_error()로 exit()
        handle_error(Exception("전역 프로젝트 ID가 설정되지 않았습니다"), "전역 프로젝트 ID 획득 실패")
    return _project_id


def is_global_project_info_set() -> bool:
    """
    전역 프로젝트 정보 설정 여부 확인

    Returns:
        설정 여부
    """
    return _project_name is not None and _project_id is not None


def get_global_project_info() -> tuple[str, int]:
    """
    전역 프로젝트 정보 일괄 획득

    Returns:
        (프로젝트명, 프로젝트 ID)

    Raises:
        Exception: 프로젝트 정보가 설정되지 않은 경우
    """
    return get_global_project_name(), get_global_project_id()