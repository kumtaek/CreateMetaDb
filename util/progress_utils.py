"""
진행 상황 로그 및 tqdm 출력 공통 유틸리티
"""

from __future__ import annotations

import sys
import time
from typing import Optional

from .logger import app_logger

try:
    from tqdm import tqdm
except Exception:
    tqdm = None


class ProgressTracker:
    """진행 로그와 tqdm 진행바를 함께 관리하는 클래스"""

    def __init__(
        self,
        total: Optional[int],
        desc: str,
        unit: str = "it",
        log_interval_sec: float = 1.0,
        leave: bool = False,
        mininterval: float = 0.1,
    ):
        """
        진행 추적기 초기화

        Args:
            total: 전체 작업 수 (없으면 tqdm 비활성화)
            desc: tqdm 표시용 설명
            unit: tqdm 단위 표시
            log_interval_sec: 로그 출력 최소 간격(초)
            leave: tqdm 종료 후 표시 유지 여부
            mininterval: tqdm 최소 갱신 간격(초)
        """
        self.total = total
        self.desc = desc
        self.unit = unit
        self.log_interval_sec = log_interval_sec
        self.leave = leave
        self.mininterval = mininterval
        self._last_log_time = time.time()
        self._current = 0
        self._bar = None

        if tqdm is not None and (total is None or total > 0):
            self._bar = tqdm(
                total=total,
                desc=desc,
                unit=unit,
                leave=leave,
                mininterval=mininterval,
                dynamic_ncols=True,
                file=sys.stdout,
                disable=False
            )

    def update(
        self,
        current: Optional[int] = None,
        increment: int = 1,
        log_message: Optional[str] = None,
        force_log: bool = False,
    ) -> float:
        """
        진행 상태 업데이트 및 로그 출력

        Args:
            current: 현재 처리 수 (지정 시 해당 값으로 갱신)
            increment: current 미지정 시 증가량
            log_message: 출력할 로그 메시지
            force_log: 로그 강제 출력 여부

        Returns:
            마지막 로그 출력 시간
        """
        if current is not None:
            delta = current - self._current
            if delta < 0:
                delta = 0
            self._current = current
        else:
            delta = increment
            self._current += increment

        if self._bar is not None and delta:
            self._bar.update(delta)

        if log_message:
            now = time.time()
            if force_log or (now - self._last_log_time >= self.log_interval_sec):
                app_logger.info(log_message)
                self._last_log_time = now

        return self._last_log_time

    def close(self) -> None:
        """tqdm 진행바 종료"""
        if self._bar is not None:
            self._bar.close()

    def __enter__(self) -> "ProgressTracker":
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """컨텍스트 매니저 종료"""
        self.close()
