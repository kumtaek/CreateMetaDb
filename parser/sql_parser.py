"""
SQL 파서 (UTF-8, no BOM)
- 단일 패스 보강: 테이블/조인/컬럼 추출
"""

import re
from typing import List, Dict, Set, Any, Optional
from util import debug, handle_error, PathUtils, ValidationUtils
from util.oracle_keyword_manager import get_oracle_keyword_manager


class SqlParser:
    _instance: Optional['SqlParser'] = None
    _initialized: bool = False

    def __new__(cls) -> 'SqlParser':
        if cls._instance is None:
            cls._instance = super(SqlParser, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not SqlParser._initialized:
            self.path_utils = PathUtils()
            self.oracle_keyword_manager = get_oracle_keyword_manager()
            self.oracle_keywords = self.oracle_keyword_manager.get_keywords()
            SqlParser._initialized = True

    # ===== 전처리 =====

    def _remove_comments(self, sql: str) -> str:
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        return sql

    def _normalize_whitespace(self, sql: str) -> str:
        return re.sub(r'\s+', ' ', sql).strip()

    def _normalize_binding_variables(self, sql: str) -> str:
        sql = re.sub(r'#\{[^}]*\}', '?', sql)
        sql = re.sub(r'\$\{[^}]*\}', '?', sql)
        return sql

    def _remove_mybatis_tags(self, sql: str) -> str:
        patterns = [
            (r'<if\s+test=["\'][^"\']*["\'][^>]*>(.*?)</if>', r'\1'),
            (r'<choose\s*>(.*?)</choose>', r'\1'),
            (r'<when\s+test=["\'][^"\']*["\'][^>]*>(.*?)</when>', r'\1'),
            (r'<otherwise\s*>(.*?)</otherwise>', r'\1'),
            (r'<where\s*>(.*?)</where>', r' WHERE \1'),
            (r'<set\s*>(.*?)</set>', r' SET \1'),
            (r'<trim[^>]*>(.*?)</trim>', r'\1'),
            (r'<foreach[^>]*>(.*?)</foreach>', r'\1'),
        ]
        processed = sql
        for p, r in patterns:
            processed = re.sub(p, r, processed, flags=re.DOTALL | re.IGNORECASE)
        return processed

    def _preprocess_sql(self, sql: str) -> str:
        processed = self._remove_mybatis_tags(sql)
        processed = self._remove_comments(processed)
        processed = self._normalize_whitespace(processed)
        processed = self._normalize_binding_variables(processed)
        return processed.upper()

    # ===== 테이블/별칭 =====

    def extract_tables_and_aliases(self, sql_content: str) -> Dict[str, str]:
        alias_map: Dict[str, str] = {}
        try:
            processed_sql = self._preprocess_sql(sql_content)
            patterns = [
                r"\bFROM\s+(.*?)(?=\bWHERE\b|\bGROUP\b|\bORDER\b|\bUNION\b|\bHAVING\b|\bFOR\b|\bLIMIT\b|\bFETCH\b|\bCONNECT\b|\bMODEL\b|\bPIVOT\b|,\s*\(\s*SELECT|;|$)",
                r"\bUPDATE\s+(.*?)(?=\bSET)",
                r"\bDELETE\s+FROM\s+(.*?)(?=\bWHERE|;|$)",
                r"\bINSERT\s+INTO\s+(.*?)(?=\s*\(|\bSELECT)",
                r"\bMERGE\s+INTO\s+(.*?)(?=\bUSING)",
                r"\bJOIN\s+(.*?)(?=\bON)",
                r"\bUSING\s+(.*?)(?=\bON)",
            ]
            found = ""
            temp = processed_sql
            for pat in patterns:
                for m in re.finditer(pat, temp, re.IGNORECASE | re.DOTALL):
                    decl = m.group(1)
                    found += decl + ", "
                    s, e = m.span(1)
                    temp = temp[:s] + (' ' * (e - s)) + temp[e:]

            for part in found.split(','):
                tokens = part.strip().split()
                if not tokens:
                    continue
                table_name = tokens[0].split('.')[-1].upper()
                if table_name in self.oracle_keywords or not ValidationUtils.is_valid_table_name(table_name):
                    continue
                alias = table_name
                if len(tokens) > 1:
                    cand = tokens[1].upper()
                    if cand not in self.oracle_keywords and cand != 'AS':
                        alias = cand
                if alias not in alias_map:
                    alias_map[alias] = table_name
        except Exception as e:
            handle_error(e, "extract_tables_and_aliases 실패")
        return alias_map

    def extract_table_names(self, sql_content: str) -> Set[str]:
        try:
            if not sql_content or not sql_content.strip():
                return set()
            processed_sql = self._preprocess_sql(sql_content)
            patterns = [
                r"\bFROM\s+([\w\.]+)",
                r"\bJOIN\s+([\w\.]+)",
                r"\bUPDATE\s+([\w\.]+)",
                r"\bINTO\s+([\w\.]+)",
                r"\bUSING\s+([\w\.]+)",
                r"\bMERGE\s+INTO\s+([\w\.]+)",
            ]
            candidates: Set[str] = set()
            for pat in patterns:
                for match in re.findall(pat, processed_sql, re.IGNORECASE):
                    table_name = match.split('.')[-1]
                    candidates.add(table_name.upper())
            return {t for t in candidates if t not in self.oracle_keywords and ValidationUtils.is_valid_table_name(t)}
        except Exception as e:
            debug(f"extract_table_names 오류: {e}")
            return set()

    # ===== 컬럼 =====

    def extract_columns(self, sql_content: str) -> List[str]:
        try:
            processed_sql = self._preprocess_sql(sql_content)
            cols = set()
            m = re.search(r"\bSELECT\b(.*?)\bFROM\b", processed_sql, flags=re.IGNORECASE | re.DOTALL)
            if m:
                seg = m.group(1)
                cols.update(re.findall(r"\b([A-Z_][A-Z0-9_]*)\.([A-Z_][A-Z0-9_]*)\b", seg))
            for kw in ("WHERE", "ON"):
                for seg in re.findall(rf"\b{kw}\b(.*?)(?=\bGROUP\b|\bORDER\b|\bHAVING\b|\bUNION\b|$)", processed_sql, flags=re.IGNORECASE | re.DOTALL):
                    cols.update(re.findall(r"\b([A-Z_][A-Z0-9_]*)\.([A-Z_][A-Z0-9_]*)\b", seg))
            return [f"{a}.{c}" for a, c in cols]
        except Exception:
            return []

    # ===== 조인 =====

    def analyze_join_relationships(self, sql_content: str) -> List[Dict[str, Any]]:
        try:
            processed_sql = self._preprocess_sql(sql_content)
            joins: List[Dict[str, Any]] = []
            joins.extend(self._analyze_explicit_joins(processed_sql))
            joins.extend(self._analyze_implicit_joins(processed_sql))
            joins.extend(self._analyze_merge_joins(processed_sql))
            return joins
        except Exception as e:
            debug(f"analyze_join_relationships 오류: {e}")
            return []

    def _analyze_explicit_joins(self, sql_content: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        try:
            patterns = [
                (r'INNER\s+JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)\s+ON\s+([^,\s]+)\s*=\s*([^,\s]+)', 'INNER_JOIN'),
                (r'LEFT\s+(?:OUTER\s+)?JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)\s+ON\s+([^,\s]+)\s*=\s*([^,\s]+)', 'LEFT_JOIN'),
                (r'RIGHT\s+(?:OUTER\s+)?JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)\s+ON\s+([^,\s]+)\s*=\s*([^,\s]+)', 'RIGHT_JOIN'),
                (r'FULL\s+(?:OUTER\s+)?JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)\s+ON\s+([^,\s]+)\s*=\s*([^,\s]+)', 'FULL_JOIN'),
            ]
            for pat, jt in patterns:
                for m in re.finditer(pat, sql_content):
                    out.append({'join_type': jt, 'table_name': m.group(1), 'table_alias': m.group(2), 'left_column': m.group(3), 'right_column': m.group(4), 'relationship_type': 'JOIN_EXPLICIT'})
            return out
        except Exception:
            return out

    def _analyze_implicit_joins(self, sql_content: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        try:
            m = re.search(r'WHERE\s+(.+?)(?=\s+(?:GROUP|ORDER|HAVING|UNION|$))', sql_content, re.DOTALL | re.IGNORECASE)
            if not m:
                return out
            where = m.group(1)
            patterns = [
                r'([A-Z_][A-Z0-9_]*)\.([A-Z_][A-Z0-9_]*)\s*=\s*([A-Z_][A-Z0-9_]*)\.([A-Z_][A-Z0-9_]*)',
                r'([A-Z_][A-Z0-9_]*)\.([A-Z_][A-Z0-9_]*)\s*\(\+\)\s*=\s*([A-Z_][A-Z0-9_]*)\.([A-Z_][A-Z0-9_]*)',
            ]
            for pat in patterns:
                for m2 in re.finditer(pat, where):
                    out.append({'join_type': 'IMPLICIT', 'left_table_alias': m2.group(1), 'left_column': m2.group(2), 'right_table_alias': m2.group(3), 'right_column': m2.group(4), 'relationship_type': 'JOIN_IMPLICIT'})
            return out
        except Exception:
            return out

    def _analyze_merge_joins(self, sql_content: str) -> List[Dict[str, Any]]:
        joins: List[Dict[str, Any]] = []
        try:
            m = re.search(r"\bMERGE\b\s+INTO\s+.*?\bUSING\b\s+.*?\bON\b\s*\((.*?)\)", sql_content, flags=re.IGNORECASE | re.DOTALL)
            if not m:
                return []
            block = m.group(1)
            for la, lc, ra, rc in re.findall(r"\b([A-Z_][A-Z0-9_]*)\.([A-Z_][A-Z0-9_]*)\s*=\s*([A-Z_][A-Z0-9_]*)\.([A-Z_][A-Z0-9_]*)\b", block, flags=re.IGNORECASE):
                joins.append({'join_type': 'MERGEON', 'left_column': f"{la}.{lc}", 'right_column': f"{ra}.{rc}", 'relationship_type': 'JOIN_MERGEON'})
            return joins
        except Exception:
            return []

