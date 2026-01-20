"""
리포트 폴더 필터 유틸리티
- 리포트 생성 시 폴더 기준 필터링 기능 제공
"""

from typing import List, Dict, Any

from util.logger import app_logger
from util.path_utils import PathUtils


class ReportFilterUtils:
    """리포트 폴더 필터 유틸리티 클래스"""

    def __init__(self) -> None:
        """초기화"""
        self.path_utils = PathUtils()

    def normalize_folders(self, folders: List[str]) -> List[str]:
        """
        폴더 목록을 UNIX 경로로 정규화

        Args:
            folders: 입력 폴더 목록

        Returns:
            정규화된 폴더 목록
        """
        normalized = []
        for folder in folders or []:
            if not folder:
                continue
            clean = self.path_utils.normalize_path_separator(str(folder).strip(), 'unix')
            clean = clean.strip().strip('/')
            if clean:
                normalized.append(clean)

        seen = set()
        unique = []
        for item in normalized:
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)

        return unique

    def is_path_in_folders(self, file_path: str, folders: List[str]) -> bool:
        """
        파일 경로가 폴더 필터에 포함되는지 확인

        Args:
            file_path: 파일 경로
            folders: 폴더 필터 목록

        Returns:
            포함 여부 (True/False)
        """
        if not folders:
            return True
        if not file_path:
            return False

        normalized_path = self.path_utils.normalize_path_separator(str(file_path).strip(), 'unix').strip()
        normalized_path = normalized_path.strip('/')
        if not normalized_path:
            return False

        path_token = f"/{normalized_path}/".lower()
        for folder in folders:
            folder_token = f"/{str(folder).strip('/')}/".lower()
            if folder_token in path_token:
                return True
        return False

    def filter_rows_by_paths(self, rows: List[Dict[str, Any]], path_keys: List[str], folders: List[str]) -> List[Dict[str, Any]]:
        """
        경로 키 기준으로 결과 목록을 폴더 필터링

        Args:
            rows: 결과 목록
            path_keys: 경로 키 목록
            folders: 폴더 필터 목록

        Returns:
            필터링된 결과 목록
        """
        if not folders or not rows:
            return rows

        filtered = []
        for row in rows:
            for key in path_keys:
                if self.is_path_in_folders(row.get(key, ''), folders):
                    filtered.append(row)
                    break

        app_logger.info(f"폴더 필터 적용 결과: {len(filtered)}/{len(rows)}건")
        return filtered
