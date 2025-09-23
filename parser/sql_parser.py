"""
SQL 파서 모듈
- 서브쿼리, UNION, MyBatis 동적 SQL 지원
- 시스템 테이블 및 별칭 필터링
- 설정 기반 패턴 매칭
"""

import re
import yaml
import os
from typing import List, Dict, Set, Any, Optional, Tuple
from util import debug, error, handle_error, PathUtils, ValidationUtils, info, warning


class SqlParser:
    """SQL 파서 클래스"""

    def __init__(self):
        """SQL 파서 초기화"""
        self.path_utils = PathUtils()
        self.oracle_keywords = set()
        self._load_sql_configuration()

    def _load_sql_configuration(self) -> None:
        """oracle_sql_keyword.yaml 파일에서 키워드를 로드하여 self.oracle_keywords 세트에 저장합니다."""
        try:
            config_path = self.path_utils.get_parser_config_path("oracle_sql")
            if not os.path.exists(config_path):
                warning(f"Oracle 키워드 설정 파일을 찾을 수 없습니다: {config_path}")
                return

            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            keywords = set()
            if isinstance(config, dict):
                for key, value in config.items():
                    if key.endswith('_keywords') or key.endswith('_functions'):
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                if isinstance(sub_value, list):
                                    keywords.update([kw.upper() for kw in sub_value])
                        elif isinstance(value, list):
                             keywords.update([kw.upper() for kw in value])

            self.oracle_keywords = keywords
            info(f"Oracle SQL 키워드 {len(self.oracle_keywords)}개 로드 완료.")

        except Exception as e:
            handle_error(e, "Oracle SQL 키워드 설정 로드 실패")

    def extract_tables_and_aliases(self, sql_content: str) -> Dict[str, str]:
        """SQL에서 테이블명과 별칭을 추출하여 맵으로 반환합니다. (사용자 정의 패턴 기반)"""
        alias_map = {}
        try:
            processed_sql = self._preprocess_sql(sql_content)

            patterns = [
                r"\bFROM\s+(.*?)(?=\bWHERE|\bGROUP|\bORDER|\bUNION|\bHAVING|\bFOR|\bLIMIT|\bFETCH|\bCONNECT|\bMODEL|\bPIVOT|\s*,\s*\(|;|$)",
                r"\bUPDATE\s+(.*?)(?=\bSET)",
                r"\bDELETE\s+FROM\s+(.*?)(?=\bWHERE|;|$)",
                r"\bINSERT\s+INTO\s+(.*?)(?=\s*\(|\bSELECT)",
                r"\bMERGE\s+INTO\s+(.*?)(?=\bUSING)",
                r"\bJOIN\s+(.*?)(?=\bON)",
                r"\bUSING\s+(.*?)(?=\bON)"
            ]

            found_tables_str = ""
            temp_sql = processed_sql
            
            for pattern in patterns:
                for match in re.finditer(pattern, temp_sql, re.IGNORECASE | re.DOTALL):
                    table_declarations = match.group(1)
                    found_tables_str += table_declarations + ", "
                    start, end = match.span(1)
                    temp_sql = temp_sql[:start] + (' ' * (end - start)) + temp_sql[end:]

            for part in found_tables_str.split(','):
                tokens = part.strip().split()
                if not tokens:
                    continue
                
                table_name = tokens[0].split('.')[-1].upper()
                
                if table_name in self.oracle_keywords or not ValidationUtils.is_valid_table_name(table_name):
                    continue

                alias = table_name
                if len(tokens) > 1:
                    potential_alias = tokens[1].upper()
                    if potential_alias not in self.oracle_keywords and potential_alias != 'AS':
                        alias = potential_alias
                
                if alias not in alias_map:
                    alias_map[alias] = table_name

        except Exception as e:
            handle_error(e, "테이블 및 별칭 추출 실패")
        
        debug(f"추출된 테이블/별칭 맵: {alias_map}")
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
                r"\bUSING\s+([\w\.]+)" 
            ] 
            
            candidates = set()
            for pattern in patterns:
                matches = re.findall(pattern, processed_sql, re.IGNORECASE)
                for match in matches:
                    table_name = match.split('.')[-1]
                    candidates.add(table_name.upper())

            validated_tables = {tbl for tbl in candidates if tbl not in self.oracle_keywords and ValidationUtils.is_valid_table_name(tbl)}
            
            debug(f"테이블명 추출 결과: {validated_tables}")
            return validated_tables

        except Exception as e:
            debug(f"테이블명 추출 중 오류: {str(e)}")
            return set()

    def determine_query_type(self, sql_content: str) -> str:
        try:
            if not sql_content or not sql_content.strip():
                return 'SQL_UNKNOWN'

            processed_sql = self._preprocess_sql(sql_content)
            
            first_word = processed_sql.strip().split()[0] if processed_sql.strip() else ""
            
            if first_word == 'INSERT':
                return 'SQL_INSERT'
            elif first_word == 'UPDATE':
                return 'SQL_UPDATE'
            elif first_word == 'DELETE':
                return 'SQL_DELETE'
            elif first_word == 'MERGE':
                return 'SQL_MERGE'
            else:
                return 'SQL_SELECT'
                
        except Exception as e:
            debug(f"쿼리 종류 인식 중 오류: {str(e)}")
            return 'SQL_UNKNOWN'

    def _preprocess_sql(self, sql_content: str) -> str:
        try:
            processed = self._remove_mybatis_tags(sql_content)
            processed = self._remove_comments(processed)
            processed = self._normalize_whitespace(processed)
            processed = self._normalize_binding_variables(processed)
            processed = processed.upper()
            return processed
        except Exception as e:
            debug(f"SQL 전처리 중 오류: {str(e)}")
            return sql_content.upper()

    def _remove_mybatis_tags(self, sql_content: str) -> str:
        try:
            tag_patterns = [
                (r'<if\s+test=["\'][^"\"]*["\'][^>]*>(.*?)</if>', r'\1'),
                (r'<choose\s*>(.*?)</choose>', r'\1'),
                (r'<when\s+test=["\'][^"\"]*["\'][^>]*>(.*?)</when>', r'\1'),
                (r'<otherwise\s*>(.*?)</otherwise>', r'\1'),
                (r'<where\s*>(.*?)</where>', r' WHERE \1'),
                (r'<set\s*>(.*?)</set>', r' SET \1'),
                (r'<trim[^>]*>(.*?)</trim>', r'\1'),
                (r'<foreach[^>]*>(.*?)</foreach>', r'\1')
            ]
            processed = sql_content
            for pattern, replacement in tag_patterns:
                processed = re.sub(pattern, replacement, processed, flags=re.DOTALL | re.IGNORECASE)
            return processed
        except Exception as e:
            debug(f"MyBatis 태그 제거 중 오류: {str(e)}")
            return sql_content

    def _remove_comments(self, sql_content: str) -> str:
        try:
            processed = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
            processed = re.sub(r'/\*.*?\*/', '', processed, flags=re.DOTALL)
            return processed
        except Exception as e:
            debug(f"SQL 주석 제거 중 오류: {str(e)}")
            return sql_content

    def _normalize_whitespace(self, sql_content: str) -> str:
        try:
            processed = re.sub(r'\s+', ' ', sql_content)
            processed = processed.strip()
            return processed
        except Exception as e:
            debug(f"공백 정규화 중 오류: {str(e)}")
            return sql_content

    def _normalize_binding_variables(self, sql_content: str) -> str:
        try:
            processed = re.sub(r'#\{[^}]*\}', '?', sql_content)
            processed = re.sub(r'\$\{[^}]*\}', '?', processed)
            return processed
        except Exception as e:
            debug(f"바인딩 변수 제거 중 오류: {str(e)}")
            return sql_content

    def analyze_join_relationships(self, sql_content: str) -> List[Dict[str, Any]]:
        try:
            processed_sql = self._preprocess_sql(sql_content)
            join_relationships = []
            explicit_joins = self._analyze_explicit_joins(processed_sql)
            join_relationships.extend(explicit_joins)
            implicit_joins = self._analyze_implicit_joins(processed_sql)
            join_relationships.extend(implicit_joins)
            return join_relationships
        except Exception as e:
            debug(f"JOIN 관계 분석 중 오류: {str(e)}")
            return []

    def _analyze_explicit_joins(self, sql_content: str) -> List[Dict[str, Any]]:
        try:
            join_relationships = []
            explicit_join_patterns = [
                (r'INNER\s+JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)\s+ON\s+([^,\s]+)\s*=\s*([^,\s]+)', 'INNER_JOIN'),
                (r'LEFT\s+(?:OUTER\s+)?JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)\s+ON\s+([^,\s]+)\s*=\s*([^,\s]+)', 'LEFT_JOIN'),
                (r'RIGHT\s+(?:OUTER\s+)?JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)\s+ON\s+([^,\s]+)\s*=\s*([^,\s]+)', 'RIGHT_JOIN'),
                (r'FULL\s+(?:OUTER\s+)?JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)\s+ON\s+([^,\s]+)\s*=\s*([^,\s]+)', 'FULL_JOIN'),
                (r'CROSS\s+JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)', 'CROSS_JOIN'),
                (r'NATURAL\s+JOIN\s+([A-Z_][A-Z0-9_]*)\s+([A-Z_][A-Z0-9_]*)', 'NATURAL_JOIN')
            ]
            for pattern, join_type in explicit_join_patterns:
                matches = re.finditer(pattern, sql_content)
                for match in matches:
                    if join_type in ['CROSS_JOIN', 'NATURAL_JOIN']:
                        table_name = match.group(1)
                        table_alias = match.group(2)
                        join_info = {
                            'join_type': join_type,
                            'table_name': table_name,
                            'table_alias': table_alias,
                            'relationship_type': 'JOIN_EXPLICIT'
                        }
                    else:
                        table_name = match.group(1)
                        table_alias = match.group(2)
                        left_col = match.group(3)
                        right_col = match.group(4)
                        join_info = {
                            'join_type': join_type,
                            'table_name': table_name,
                            'table_alias': table_alias,
                            'left_column': left_col,
                            'right_column': right_col,
                            'relationship_type': 'JOIN_EXPLICIT'
                        }
                    if ValidationUtils.is_valid_table_name(table_name):
                        join_relationships.append(join_info)
                        debug(f"명시적 JOIN 분석: {join_info}")
            return join_relationships
        except Exception as e:
            debug(f"명시적 JOIN 분석 중 오류: {str(e)}")
            return []

    def _analyze_implicit_joins(self, sql_content: str) -> List[Dict[str, Any]]:
        try:
            join_relationships = []
            where_pattern = r'WHERE\s+(.+?)(?=\s+(?:GROUP|ORDER|HAVING|UNION|$))'
            where_match = re.search(where_pattern, sql_content, re.DOTALL)
            if where_match:
                where_clause = where_match.group(1)
                implicit_join_patterns = [
                    r'([A-Z_][A-Z0-9_]*)\\.([A-Z_][A-Z0-9_]*)\s*=\s*([A-Z_][A-Z0-9_]*)\\.([A-Z_][A-Z0-9_]*)',
                    r'([A-Z_][A-Z0-9_]*)\\.([A-Z_][A-Z0-9_]*)\s*\(\+\)\s*=\s*([A-Z_][A-Z0-9_]*)\\.([A-Z_][A-Z0-9_]*)',
                    r'\b([A-Z_][A-Z0-9_]*)\s*=\s*([A-Z_][A-Z0-9_]*)\b'
                ]
                for pattern in implicit_join_patterns:
                    matches = re.finditer(pattern, where_clause)
                    for match in matches:
                        if len(match.groups()) == 4:
                            left_alias = match.group(1)
                            left_col = match.group(2)
                            right_alias = match.group(3)
                            right_col = match.group(4)
                            join_info = {
                                'join_type': 'IMPLICIT',
                                'left_table_alias': left_alias,
                                'left_column': left_col,
                                'right_table_alias': right_alias,
                                'right_column': right_col,
                                'relationship_type': 'JOIN_IMPLICIT'
                            }
                        elif len(match.groups()) == 2:
                            left_col = match.group(1)
                            right_col = match.group(2)
                            join_info = {
                                'join_type': 'IMPLICIT',
                                'left_column': left_col,
                                'right_column': right_col,
                                'relationship_type': 'WHERE_JOIN'
                            }
                        else:
                            continue
                        join_relationships.append(join_info)
                        debug(f"암시적 JOIN 분석: {join_info}")
            return join_relationships
        except Exception as e:
            debug(f"암시적 JOIN 분석 중 오류: {str(e)}")
            return []