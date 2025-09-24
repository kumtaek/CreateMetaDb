"""
Oracle 키워드 매니저 - 싱글톤 패턴으로 Oracle 키워드를 한 번만 로딩하고 공유
"""
import os
import yaml
from typing import Set, Optional
from .path_utils import PathUtils
from .logger import debug, info, handle_error

class OracleKeywordManager:
    """Oracle 키워드를 관리하는 싱글톤 클래스"""

    _instance: Optional['OracleKeywordManager'] = None
    _keywords: Optional[Set[str]] = None
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
        """Oracle 키워드를 YAML 파일에서 로드"""
        try:
            # Oracle 키워드 설정 파일 경로
            config_path = self.path_utils.get_parser_config_path("oracle_sql")
            java_config_path = self.path_utils.get_parser_config_path("java_keyword")

            keywords = set()

            # Oracle SQL 키워드 로드
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                if isinstance(config, dict):
                    # oracle_sql_keywords 하위의 모든 키워드들 수집
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

            OracleKeywordManager._keywords = keywords
            info(f"Oracle SQL 키워드 {len(keywords)}개 로드 완료 (싱글톤)")

        except Exception as e:
            handle_error(e, "Oracle 키워드 로드 실패")
            # 실패 시 기본 키워드 사용
            OracleKeywordManager._keywords = {
                'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
                'ALTER', 'TABLE', 'INDEX', 'VIEW', 'GRANT', 'REVOKE', 'USER', 'DUAL',
                'SYSDATE', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ORDER', 'GROUP', 'BY',
                'HAVING', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ON', 'AND', 'OR', 'NOT'
            }

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

    def reload_keywords(self) -> None:
        """키워드를 다시 로드 (테스트나 설정 변경 시 사용)"""
        OracleKeywordManager._keywords = None
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