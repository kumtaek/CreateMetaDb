"""
Oracle 키워드 매니저 - 싱글톤 패턴으로 Oracle 키워드를 한 번만 로딩하고 공유
sql_keyword.yaml 파일에서 통합 키워드를 로드 (oracle_sql_keyword.yaml 삭제됨)
"""
import os
import re
import yaml
from typing import Set, List, Optional
from .path_utils import PathUtils
from .logger import debug, info, handle_error

class OracleKeywordManager:
    """Oracle 키워드와 리터럴 패턴을 관리하는 싱글톤 클래스"""

    _instance: Optional['OracleKeywordManager'] = None
    _keywords: Optional[Set[str]] = None
    _literal_keywords: Optional[Set[str]] = None
    _literal_patterns: Optional[List[re.Pattern]] = None
    _initialized: bool = False

    def __new__(cls) -> 'OracleKeywordManager':
        if cls._instance is None:
            cls._instance = super(OracleKeywordManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.path_utils = PathUtils()
            self._load_keywords()
            OracleKeywordManager._initialized = True

    def _load_keywords(self) -> None:
        """SQL 키워드와 리터럴 패턴을 YAML 파일에서 로드"""
        try:
            # sql_keyword.yaml (통합 키워드 파일) - 직접 경로 지정
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_path, "config", "parser", "sql_keyword.yaml")
            java_config_path = self.path_utils.get_parser_config_path("java_keyword")

            keywords = set()
            literal_keywords = set()
            literal_patterns = []

            # SQL 키워드 로드 (sql_keyword.yaml)
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                if isinstance(config, dict):
                    # 리터럴 키워드 로드 (조인에서 제외할 키워드)
                    if 'literal_keywords' in config:
                        raw_literal_kw = config.get('literal_keywords', [])
                        if isinstance(raw_literal_kw, list):
                            literal_keywords.update([kw.upper() for kw in raw_literal_kw])

                    # 리터럴 패턴 로드 (조인에서 제외할 정규식 패턴)
                    if 'literal_value_patterns' in config:
                        raw_patterns = config.get('literal_value_patterns', [])
                        if isinstance(raw_patterns, list):
                            for pattern_str in raw_patterns:
                                try:
                                    literal_patterns.append(re.compile(pattern_str, re.IGNORECASE))
                                except re.error:
                                    debug(f"리터럴 패턴 컴파일 실패: {pattern_str}")

                    # 키워드 수집 (기존 방식 유지)
                    for key, value in config.items():
                        if key.endswith('_keywords') or key.endswith('_functions'):
                            if isinstance(value, dict):
                                for sub_key, sub_value in value.items():
                                    if isinstance(sub_value, list):
                                        keywords.update([kw.upper() for kw in sub_value])
                            elif isinstance(value, list):
                                keywords.update([kw.upper() for kw in value])

            # Java 설정에서 oracle_reserved_keywords 로드
            if os.path.exists(java_config_path):
                with open(java_config_path, 'r', encoding='utf-8') as f:
                    java_config = yaml.safe_load(f)

                if isinstance(java_config, dict):
                    oracle_reserved = java_config.get('oracle_reserved_keywords', [])
                    if isinstance(oracle_reserved, list):
                        keywords.update([kw.upper() for kw in oracle_reserved])

            # 키워드가 없으면 기본 키워드 사용
            if not keywords:
                keywords = {
                    'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
                    'ALTER', 'TABLE', 'INDEX', 'VIEW', 'GRANT', 'REVOKE', 'USER', 'DUAL',
                    'SYSDATE', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ORDER', 'GROUP', 'BY',
                    'HAVING', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ON', 'AND', 'OR', 'NOT'
                }

            # 리터럴 키워드가 없으면 기본값 사용
            if not literal_keywords:
                literal_keywords = {
                    'SYSDATE', 'SYSTIMESTAMP', 'CURRENT_DATE', 'CURRENT_TIMESTAMP',
                    'LOCALTIMESTAMP', 'NULL', 'TRUE', 'FALSE', 'Y', 'N'
                }

            OracleKeywordManager._keywords = keywords
            OracleKeywordManager._literal_keywords = literal_keywords
            OracleKeywordManager._literal_patterns = literal_patterns
            info(f"SQL 키워드 {len(keywords)}개, 리터럴 키워드 {len(literal_keywords)}개, 리터럴 패턴 {len(literal_patterns)}개 로드 완료")

        except Exception as e:
            handle_error(e, "SQL 키워드 로드 실패")
            # 실패 시 기본 키워드 사용
            OracleKeywordManager._keywords = {
                'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
                'ALTER', 'TABLE', 'INDEX', 'VIEW', 'GRANT', 'REVOKE', 'USER', 'DUAL',
                'SYSDATE', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ORDER', 'GROUP', 'BY',
                'HAVING', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ON', 'AND', 'OR', 'NOT'
            }
            OracleKeywordManager._literal_keywords = {
                'SYSDATE', 'SYSTIMESTAMP', 'CURRENT_DATE', 'CURRENT_TIMESTAMP',
                'LOCALTIMESTAMP', 'NULL', 'TRUE', 'FALSE', 'Y', 'N'
            }
            OracleKeywordManager._literal_patterns = []

    def get_keywords(self) -> Set[str]:
        """Oracle 키워드 집합 반환"""
        if OracleKeywordManager._keywords is None:
            self._load_keywords()
        return OracleKeywordManager._keywords.copy()

    def is_oracle_keyword(self, word: str) -> bool:
        """주어진 단어가 Oracle 키워드인지 확인"""
        if OracleKeywordManager._keywords is None:
            self._load_keywords()
        return word.upper() in OracleKeywordManager._keywords

    def get_literal_keywords(self) -> Set[str]:
        """리터럴 키워드 집합 반환 (조인에서 컬럼으로 인식하지 않을 키워드)"""
        if OracleKeywordManager._literal_keywords is None:
            self._load_keywords()
        return OracleKeywordManager._literal_keywords.copy()

    def get_literal_patterns(self) -> List[re.Pattern]:
        """리터럴 패턴 목록 반환 (조인에서 컬럼으로 인식하지 않을 정규식 패턴)"""
        if OracleKeywordManager._literal_patterns is None:
            self._load_keywords()
        return OracleKeywordManager._literal_patterns.copy()

    def is_literal_value(self, value: str) -> bool:
        """
        주어진 값이 리터럴인지 확인
        리터럴: 숫자, 문자열, 바인드 변수, 특수 키워드 (SYSDATE, NULL 등)

        Args:
            value: 검사할 값 (예: '0', 'Y', 'SYSDATE', ':param')

        Returns:
            리터럴이면 True, 컬럼명이면 False
        """
        if not value or not isinstance(value, str):
            return False

        value_upper = value.strip().upper()

        # 빈 문자열 체크
        if not value_upper:
            return True

        # 리터럴 키워드 체크 (SYSDATE, NULL, TRUE 등)
        if OracleKeywordManager._literal_keywords is None:
            self._load_keywords()
        if value_upper in OracleKeywordManager._literal_keywords:
            return True

        # 리터럴 패턴 체크 (숫자, 문자열, 바인드 변수 등)
        if OracleKeywordManager._literal_patterns is None:
            self._load_keywords()
        for pattern in OracleKeywordManager._literal_patterns:
            if pattern.match(value):
                return True

        return False

    def reload_keywords(self) -> None:
        """키워드를 다시 로드 (테스트나 설정 변경 시 사용)"""
        OracleKeywordManager._keywords = None
        OracleKeywordManager._literal_keywords = None
        OracleKeywordManager._literal_patterns = None
        self._load_keywords()

# 전역 인스턴스 (편의 함수용)
_oracle_manager = None

def get_oracle_keyword_manager() -> OracleKeywordManager:
    """Oracle 키워드 매니저 인스턴스 반환"""
    global _oracle_manager
    if _oracle_manager is None:
        _oracle_manager = OracleKeywordManager()
    return _oracle_manager

def is_oracle_keyword(word: str) -> bool:
    """Oracle 키워드 여부 확인 (편의 함수)"""
    return get_oracle_keyword_manager().is_oracle_keyword(word)

def get_oracle_keywords() -> Set[str]:
    """Oracle 키워드 집합 반환 (편의 함수)"""
    return get_oracle_keyword_manager().get_keywords()

def is_literal_value(value: str) -> bool:
    """리터럴 값 여부 확인 (편의 함수) - 조인 조건에서 컬럼이 아닌 값 필터링용"""
    return get_oracle_keyword_manager().is_literal_value(value)

def get_literal_keywords() -> Set[str]:
    """리터럴 키워드 집합 반환 (편의 함수)"""
    return get_oracle_keyword_manager().get_literal_keywords()