"""
파일/컴포넌트 컨텍스트 전역 관리자
- 현재 처리 중인 파일과 컴포넌트, 단계 정보를 전역적으로 보관하여 ID 유실을 방지
- 크로스플랫폼 경로 정규화 (항상 Unix 구분자) 적용
"""

from dataclasses import dataclass
from threading import Lock
from typing import Optional, Dict, Any, List
from util.path_utils import PathUtils
from util.logger import handle_error


@dataclass
class FileContext:
    """현재 파일/컴포넌트 컨텍스트 정보"""
    project_name: Optional[str] = None
    project_id: Optional[int] = None
    file_id: Optional[int] = None
    file_path: Optional[str] = None  # 디렉터리 경로 (Unix 구분자)
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    component_id: Optional[int] = None
    component_name: Optional[str] = None
    component_type: Optional[str] = None
    source_type: Optional[str] = None  # XML/JAVA/JSP/SQL/FRONT 등
    stage: Optional[str] = None        # XML/Java/Frontend/BackendEntry 등
    line_start: Optional[int] = None
    line_end: Optional[int] = None


class FileContextManager:
    """
    파일 컨텍스트 전역 관리자 (싱글턴)
    - 파서가 처리 중인 파일/컴포넌트 정보를 저장/조회하여 file_id 유실을 방지
    - push/pop 스택으로 중첩 파싱에도 안전하게 복원
    """
    _instance = None
    _lock = Lock()

    def __init__(self):
        self._context = FileContext()
        self._stack: List[FileContext] = []
        self._path_utils = PathUtils()

    @classmethod
    def instance(cls) -> "FileContextManager":
        """싱글턴 인스턴스 반환"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def set_current(
        self,
        *,
        project_name: Optional[str] = None,
        project_id: Optional[int] = None,
        file_id: Optional[int] = None,
        file_path: Optional[str] = None,
        file_name: Optional[str] = None,
        file_type: Optional[str] = None,
        component_id: Optional[int] = None,
        component_name: Optional[str] = None,
        component_type: Optional[str] = None,
        source_type: Optional[str] = None,
        stage: Optional[str] = None,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
    ) -> None:
        """
        현재 처리 중인 파일/컴포넌트 정보를 설정한다.

        Args:
            project_name: 프로젝트명
            project_id: 프로젝트 ID
            file_id: 파일 ID
            file_path: 파일 디렉터리 경로
            file_name: 파일명
            file_type: 파일 타입 (JAVA/XML/JSP 등)
            component_id/component_name/component_type: 현재 컴포넌트 정보
            source_type: 소스 유형 (XML/JAVA/JSP/SQL/FRONT 등)
            stage: 처리 단계 식별자
            line_start/line_end: 소스 내 위치 정보
        """
        normalized_path = self._path_utils.normalize_path_separator(file_path or '', 'unix')
        self._context = FileContext(
            project_name=project_name or self._context.project_name,
            project_id=project_id if project_id is not None else self._context.project_id,
            file_id=file_id,
            file_path=normalized_path,
            file_name=file_name,
            file_type=file_type,
            component_id=component_id,
            component_name=component_name,
            component_type=component_type,
            source_type=source_type,
            stage=stage,
            line_start=line_start,
            line_end=line_end
        )

    def push(self, **kwargs) -> None:
        """현재 컨텍스트를 스택에 저장하고 새 컨텍스트를 설정한다."""
        self._stack.append(self._context)
        self.set_current(**kwargs)

    def pop(self) -> None:
        """스택에서 이전 컨텍스트를 복원한다."""
        if self._stack:
            self._context = self._stack.pop()
        else:
            self.clear()

    def get_current(self) -> FileContext:
        """현재 컨텍스트를 반환"""
        return self._context

    def require_current_file(self) -> FileContext:
        """현재 파일 컨텍스트가 없으면 예외 발생 (file_id 필수)"""
        if not self._context.file_id:
            handle_error(Exception("현재 파일 컨텍스트가 설정되지 않았습니다"), "파일 컨텍스트 조회 실패")
        return self._context

    def as_dict(self) -> Dict[str, Any]:
        """현재 컨텍스트를 딕셔너리로 반환"""
        return {
            'project_name': self._context.project_name,
            'project_id': self._context.project_id,
            'file_id': self._context.file_id,
            'file_path': self._context.file_path,
            'file_name': self._context.file_name,
            'file_type': self._context.file_type,
            'component_id': self._context.component_id,
            'component_name': self._context.component_name,
            'component_type': self._context.component_type,
            'source_type': self._context.source_type,
            'stage': self._context.stage,
            'line_start': self._context.line_start,
            'line_end': self._context.line_end,
        }

    def clear(self) -> None:
        """컨텍스트 초기화"""
        self._context = FileContext()
        self._stack = []


def get_file_context_manager() -> FileContextManager:
    """전역 파일 컨텍스트 매니저 싱글턴 반환"""
    return FileContextManager.instance()
