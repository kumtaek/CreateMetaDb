"""
SQL 정규화 유틸리티
- 정확한 문법 파싱이 아니라 테이블/컬럼/조인 추출에 필요한 최소한의 정제만 수행한다.
"""

from typing import Optional, Dict, Any
import re

# 기본 정규화 설정 (딕셔너리로 유지해 순환 import 회피)
DEFAULT_SQL_NORMALIZATION_CONFIG: Dict[str, Any] = {
    "enabled": True,
    "remove_tags": True,
    "remove_comments": True,
    "remove_bind_params": True,
    "remove_non_sql_chars": False,
    "keep_sql_blocks_only": True,
    "uppercase": True,
}


def normalize_sql_loose(
    sql_content: str,
    remove_tags: bool = True,
    remove_comments: bool = True,
    remove_bind_params: bool = False,
    remove_non_sql_chars: bool = False,
    keep_sql_blocks_only: bool = False,
    uppercase: bool = True,
) -> str:
    """
    느슨한 SQL 정규화 수행.

    Args:
        sql_content: 원본 SQL 문자열
        remove_tags: <...> 형태의 태그 제거 여부
        remove_comments: --, /* */ 주석 제거 여부
        remove_bind_params: #{}, ${}, :param 형태의 바인딩 표기를 단순화할지 여부
        remove_non_sql_chars: SQL에 불필요한 문자를 공백으로 치환할지 여부
        keep_sql_blocks_only: SELECT/UPDATE/DELETE/INSERT/MERGE 로 시작하는 블록만 남길지 여부
        uppercase: 대문자 변환 여부

    Returns:
        정규화된 SQL 문자열
    """
    if not sql_content:
        return ""

    sql = sql_content

    # 태그 제거
    if remove_tags:
        sql = re.sub(r"<[^>]+>", " ", sql, flags=re.IGNORECASE | re.DOTALL)

    # 주석 제거
    if remove_comments:
        # 한 줄 주석 (--, // ... CR/LF까지)
        sql = re.sub(r"--[^\r\n]*", "", sql)
        sql = re.sub(r"//[^\r\n]*", "", sql)
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)

    # 바인딩 파라미터 단순화
    if remove_bind_params:
        sql = re.sub(r"[#$]\{\s*[^}]+\s*}", " ", sql)  # #{param}, ${param}
        sql = re.sub(r":\w+", " ", sql)  # :param

    # SQL 블록만 남기기
    if keep_sql_blocks_only:
        blocks = [m.group(0) for m in re.finditer(
            r"\b(SELECT|UPDATE|DELETE|INSERT|MERGE)\b[\s\S]*?(?=;|$)",
            sql,
            flags=re.IGNORECASE,
        )]
        if blocks:
            sql = " ".join(blocks)

    # 비SQL 문자 제거
    if remove_non_sql_chars:
        sql = re.sub(r"[^a-zA-Z0-9_,\\.\\s\\(\\)]", " ", sql)

    # 공백 정규화
    sql = re.sub(r"\s+", " ", sql).strip()

    if uppercase:
        sql = sql.upper()

    return sql


def normalize_sql_loose_with_config(sql_content: str, config: Dict[str, Any]) -> str:
    """
    설정 딕셔너리 기반 느슨한 SQL 정규화
    - 정확 문법 파싱이 아니라 테이블/컬럼/조인 추출용으로 최소한의 정제만 수행
    """
    cfg = DEFAULT_SQL_NORMALIZATION_CONFIG.copy()
    if config:
        cfg.update(config)

    if not cfg.get("enabled", True):
        return sql_content or ""
    return normalize_sql_loose(
        sql_content=sql_content,
        remove_tags=cfg.get("remove_tags", True),
        remove_comments=cfg.get("remove_comments", True),
        remove_bind_params=cfg.get("remove_bind_params", False),
        remove_non_sql_chars=cfg.get("remove_non_sql_chars", False),
        keep_sql_blocks_only=cfg.get("keep_sql_blocks_only", False),
        uppercase=cfg.get("uppercase", True),
    )
