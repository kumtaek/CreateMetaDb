"""
공통 SQL 조인 분석 모듈
- Oracle SQL의 EXPLICIT/IMPLICIT JOIN 분석
- XML과 Java 파서에서 공통 사용
- INFERRED 테이블/컬럼 생성 지원

USER RULES:
- 공통함수 사용 지향
- 하드코딩 금지: 설정 파일 기반
- Exception은 handle_error()로 처리
- 크로스플랫폼 대응
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from util.logger import app_logger, info, warning, debug, error, handle_error
from util.path_utils import PathUtils


class SqlJoinAnalyzer:
    """공통 SQL 조인 분석 클래스"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        SQL 조인 분석기 초기화
        
        Args:
            config: SQL 분석 설정 (없으면 기본 설정 사용)
        """
        self.config = config or self._load_default_config()
        
    def _load_default_config(self) -> Dict:
        """기본 SQL 분석 설정 로드"""
        try:
            # USER RULES: 공통함수 사용 - PathUtils로 설정 파일 경로 처리
            path_utils = PathUtils()
            config_path = path_utils.get_parser_config_path("sql")
            
            # YAML 설정 파일 로드 (향후 구현)
            # 현재는 하드코딩된 기본값 사용
            return {
                'sql_analysis_patterns': {
                    'from_clause': [
                        r"FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?(?:\s*,\s*([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?)?"
                    ],
                    'explicit_joins': [
                        r"(LEFT\s+(?:OUTER\s+)?JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?\\s+ON\\s+(.+?)(?=\\s+(?:LEFT|RIGHT|FULL|INNER|CROSS|NATURAL|WHERE|GROUP|ORDER|$))",
                        r"(INNER\s+JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?\\s+ON\\s+(.+?)(?=\\s+(?:LEFT|RIGHT|FULL|INNER|CROSS|NATURAL|WHERE|GROUP|ORDER|$))",
                        r"(RIGHT\s+(?:OUTER\s+)?JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?\\s+ON\\s+(.+?)(?=\\s+(?:LEFT|RIGHT|FULL|INNER|CROSS|NATURAL|WHERE|GROUP|ORDER|$))"
                    ],
                    'implicit_joins': [
                        r"([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)",
                        r"([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\+\)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)",
                        r"([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\+\)"
                    ]
                },
                'join_type_mapping': {
                    r"LEFT\s+(?:OUTER\s+)?JOIN": "LEFT_JOIN",
                    r"INNER\s+JOIN": "INNER_JOIN",
                    r"RIGHT\s+(?:OUTER\s+)?JOIN": "RIGHT_JOIN",
                    r"FULL\s+OUTER\s+JOIN": "FULL_OUTER_JOIN",
                    r"ORACLE_OUTER": "ORACLE_OUTER_JOIN"
                },
                'dynamic_sql_patterns': {
                    'dynamic_tags': [
                        r"<if\s+test=[\"'][^\"']*[\"'][^>]*>(.*?)</if>",
                        r"<choose\s*>(.*?)</choose>",
                        r"<when\s+test=[\"'][^\"']*[\"'][^>]*>(.*?)</when>",
                        r"<otherwise\s*>(.*?)</otherwise>",
                        r"<foreach\s+[^>]*>(.*?)</foreach>"
                    ]
                }
            }
            
        except Exception as e:
            handle_error(e, "SQL 분석 기본 설정 로드 실패")
            return {}
    
    def analyze_join_relationships(self, sql_content: str, alias_map: Dict[str, str], file_path: str = "", component_id: int = 0) -> List[Dict[str, Any]]:
        """
        SQL 조인 관계 분석
        - EXPLICIT JOIN: JOIN ... ON
        - MERGE JOIN: MERGE ... USING ... ON
        - IMPLICIT JOIN: WHERE ...
        - CONNECT BY: Oracle 계층형 쿼리(셀프조인 성격) 관계 도출
        """
        try:
            debug(f"SQL 조인 분석 시작: {file_path or 'source'}")
            relationships = []
            
            normalized_sql = self._normalize_sql_for_analysis(sql_content, self.config.get('dynamic_sql_patterns', {}))
            
            # 1. EXPLICIT JOIN 분석 (JOIN ... ON)
            explicit_joins = self._analyze_explicit_joins(normalized_sql, alias_map)
            relationships.extend(explicit_joins)
            
            # 2. MERGE JOIN 분석 (MERGE ... USING ... ON)
            merge_joins = self._analyze_merge_joins(normalized_sql, alias_map)
            relationships.extend(merge_joins)

            # 3. IMPLICIT JOIN 분석 (WHERE ...)
            implicit_joins = self._analyze_implicit_joins(normalized_sql, alias_map)
            relationships.extend(implicit_joins)

            # 4. CONNECT BY 분석 (계층형 쿼리 / 셀프조인 성격)
            connect_by_joins = self._analyze_connect_by_joins(normalized_sql, alias_map)
            relationships.extend(connect_by_joins)
            
            unique_relationships = self._remove_duplicate_relationships(relationships)
            final_relationships = self._post_process_relationships(unique_relationships, alias_map)
            
            debug(f"SQL 조인 분석 완료: {len(final_relationships)}개 관계 발견")
            return final_relationships
            
        except Exception as e:
            handle_error(e, f"SQL 조인 분석 실패: {file_path}")
            return []

    def _analyze_explicit_joins(self, sql_content: str, alias_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """JOIN ... ON ... 구문에서 명시적 JOIN 관계를 분석합니다."""
        try:
            relationships = []
            join_pattern = r'((?:LEFT|RIGHT|FULL|INNER)\s+(?:OUTER\s+)?JOIN|JOIN)\s+[\w\.]+(?:\s+AS)?\s*\w*\s+ON\s*\(([^)]+)\)'
            on_clauses = re.findall(join_pattern, sql_content, re.IGNORECASE)
            
            for join_keyword, on_clause in on_clauses:
                join_keyword_upper = join_keyword.upper()
                if 'FULL' in join_keyword_upper:
                    rel_type = 'JOIN_EXPLICIT_FULL_OUTER'
                elif 'LEFT' in join_keyword_upper or 'RIGHT' in join_keyword_upper:
                    rel_type = 'JOIN_EXPLICIT_OUTER'
                else:
                    rel_type = 'JOIN_EXPLICIT'
                condition_pattern = r'([\w\.]+)\s*=\s*([\w\.]+)'
                conditions = re.findall(condition_pattern, on_clause)
                for cond in conditions:
                    rel = self._create_relationship_from_condition(cond[0], cond[1], alias_map, rel_type)
                    if rel:
                        relationships.append(rel)
            return relationships
        except Exception as e:
            handle_error(e, "EXPLICIT JOIN 분석 실패")
            return []

    def _analyze_merge_joins(self, sql_content: str, alias_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """MERGE ... USING ... ON ... 구문에서 JOIN_MERGEON 관계를 분석합니다."""
        try:
            relationships = []
            merge_pattern = r'\bMERGE\s+INTO[\s\S]*?\bUSING[\s\S]*?\bON\s*\(([^)]+)\)'
            on_clauses = re.findall(merge_pattern, sql_content, re.IGNORECASE)

            for on_clause in on_clauses:
                condition_pattern = r'([\w\.]+)\s*=\s*([\w\.]+)'
                conditions = re.findall(condition_pattern, on_clause)
                for cond in conditions:
                    rel = self._create_relationship_from_condition(cond[0], cond[1], alias_map, 'JOIN_MERGEON')
                    if rel:
                        relationships.append(rel)
            return relationships
        except Exception as e:
            handle_error(e, "MERGE JOIN 분석 실패")
            return []
    def _normalize_sql_for_analysis(self, sql_content: str, dynamic_patterns: dict) -> str:
        """SQL 정규화 (주석 제거, 동적 태그 처리)"""
        try:
            normalized_sql = sql_content
            
            # SQL 주석 제거 - 한 줄 주석 (-- ... / // ...)
            normalized_sql = re.sub(r'--[^\r\n]*', '', normalized_sql)
            normalized_sql = re.sub(r'//[^\r\n]*', '', normalized_sql)

            # SQL 주석 제거 - 블록 주석 (/* ... */)
            normalized_sql = re.sub(r'/\*.*?\*/', '', normalized_sql, flags=re.DOTALL)
            
            # 동적 태그 처리 (MyBatis 등)
            dynamic_tag_patterns = dynamic_patterns.get('dynamic_tags', [])
            for pattern in dynamic_tag_patterns:
                normalized_sql = re.sub(pattern, r'\1', normalized_sql, flags=re.DOTALL | re.IGNORECASE)
            
            # 모든 XML/동적 태그 제거: <...> 패턴을 공백으로 치환하여 조인/테이블/컬럼 추출에 집중
            normalized_sql = re.sub(r'<[^>]+>', ' ', normalized_sql, flags=re.IGNORECASE | re.DOTALL)
            
            # 공백 정규화 및 대문자 변환
            normalized_sql = re.sub(r'\s+', ' ', normalized_sql).strip()
            return normalized_sql.upper()
            
        except Exception as e:
            handle_error(e, "SQL 정규화 실패")
            return sql_content.upper()
    
    def _analyze_explicit_joins(self, sql_content: str, alias_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """ON 절에서 명시적 JOIN 관계를 분석합니다."""
        try:
            relationships = []
            # JOIN ... ON ... 패턴
            join_pattern = r'((?:LEFT|RIGHT|FULL|INNER)\s+(?:OUTER\s+)?JOIN|JOIN)\s+[\w\.]+\s*(?:AS)?\s*\w*\s+ON\s+([^{;]*?)(?=\bWHERE|\bGROUP|\bORDER|\bJOIN|;|$)'
            on_clauses = re.findall(join_pattern, sql_content, re.IGNORECASE)
            
            for join_keyword, on_clause in on_clauses:
                join_keyword_upper = join_keyword.upper()
                if 'FULL' in join_keyword_upper:
                    rel_type = 'JOIN_EXPLICIT_FULL_OUTER'
                elif 'LEFT' in join_keyword_upper or 'RIGHT' in join_keyword_upper:
                    rel_type = 'JOIN_EXPLICIT_OUTER'
                else:
                    rel_type = 'JOIN_EXPLICIT'
                condition_pattern = r'([\w\.]+)\s*=\s*([\w\.]+)'
                conditions = re.findall(condition_pattern, on_clause)
                for cond in conditions:
                    rel = self._create_relationship_from_condition(cond[0], cond[1], alias_map, rel_type)
                    if rel:
                        relationships.append(rel)
            return relationships
        except Exception as e:
            handle_error(e, "EXPLICIT JOIN 분석 실패")
            return []


    def _analyze_implicit_joins(self, sql_content: str, alias_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """WHERE 절에서 암시적 JOIN 관계를 분석합니다."""
        relationships: List[Dict[str, Any]] = []
        try:
            where_match = re.search(
                r'\bWHERE\s+(.*?)(?=\bCONNECT\b|\bGROUP\b|\bORDER\b|\bHAVING\b|\bUNION\b|;|$)',
                sql_content,
                re.IGNORECASE | re.DOTALL
            )
            if not where_match:
                return relationships

            where_clause = where_match.group(1)

            # Oracle (+) Outer Join 구문 처리
            has_outer = '(+)' in where_clause
            where_clause = re.sub(r'\(\+\)', '', where_clause)

            condition_pattern = r'([\w\.]+)\s*=\s*([\w\.]+)'
            rel_type = 'JOIN_IMPLICIT_OUTER' if has_outer else 'JOIN_IMPLICIT'

            for left_part, right_part in re.findall(condition_pattern, where_clause):
                rel = self._create_relationship_from_condition(left_part, right_part, alias_map, rel_type)
                if rel:
                    relationships.append(rel)

            return relationships
        except Exception as e:
            handle_error(e, "IMPLICIT JOIN 분석 실패")
            return []

    def _analyze_connect_by_joins(self, sql_content: str, alias_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Oracle CONNECT BY 절에서 계층형(셀프조인 성격) 관계를 분석합니다.

        예)
        - CONNECT BY PRIOR E.EMPNO = E.MGR
        - CONNECT BY PRIOR EMPNO = MGR (단일 테이블일 때 컬럼만 사용되는 케이스)

        주의)
        - CONNECT BY는 동일 테이블 내 부모/자식 행을 연결하는 구조이므로, source_table == target_table 관계가 정상입니다.
        """
        relationships: List[Dict[str, Any]] = []
        try:
            connect_by_match = re.search(
                r'\bCONNECT\s+BY\b\s+(.*?)(?=\bGROUP\b|\bORDER\b|\bHAVING\b|\bUNION\b|;|$)',
                sql_content,
                re.IGNORECASE | re.DOTALL
            )
            if not connect_by_match:
                return relationships

            connect_by_clause = connect_by_match.group(1)
            connect_by_clause = re.sub(r'\bNOCYCLE\b', ' ', connect_by_clause, flags=re.IGNORECASE)

            default_table = self._infer_single_table(alias_map)

            patterns = [
                r'\bPRIOR\s+([\w\.]+)\s*=\s*([\w\.]+)',
                r'([\w\.]+)\s*=\s*\bPRIOR\s+([\w\.]+)',
            ]

            for pat in patterns:
                for left_token, right_token in re.findall(pat, connect_by_clause, flags=re.IGNORECASE):
                    left_table, left_col, left_alias = self._resolve_table_and_column(left_token, alias_map, default_table)
                    right_table, right_col, right_alias = self._resolve_table_and_column(right_token, alias_map, default_table)

                    if not left_table or not right_table or not left_col or not right_col:
                        continue

                    relationships.append({
                        'source_table': left_table,
                        'target_table': right_table,
                        'source_column': left_col.upper(),
                        'target_column': right_col.upper(),
                        'rel_type': 'JOIN_CONNECT_BY',
                        'confidence': 0.85,
                        'source_alias': (left_alias or 'PRIOR').upper(),
                        'target_alias': (right_alias or 'CURRENT').upper(),
                    })

            return relationships
        except Exception as e:
            handle_error(e, "CONNECT BY 분석 실패")
            return []

    def _infer_single_table(self, alias_map: Dict[str, str]) -> Optional[str]:
        """alias_map에서 단일 테이블만 존재할 때 기본 테이블명을 반환합니다."""
        try:
            tables = {t.upper() for t in alias_map.values() if t}
            if len(tables) == 1:
                return next(iter(tables))
            return None
        except Exception as e:
            handle_error(e, "단일 테이블 추론 실패")
            return None

    def _resolve_table_and_column(
        self,
        token: str,
        alias_map: Dict[str, str],
        default_table: Optional[str],
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        토큰에서 (테이블, 컬럼, 별칭)을 해석합니다.
        - 'A.COL' 형태면 A를 alias_map으로 테이블로 해석
        - 'COL' 형태면 default_table이 있을 때만 테이블을 채움
        """
        try:
            token = token.strip()
            if not token:
                return None, None, None

            if '.' in token:
                alias, col = token.split('.', 1)
                alias_u = alias.upper()
                table = alias_map.get(alias_u, alias_u)
                return table, col, alias_u

            if default_table:
                return default_table, token, None

            return None, token, None
        except Exception as e:
            handle_error(e, "토큰 테이블/컬럼 해석 실패")
            return None, None, None

    def _create_relationship_from_condition(self, part1: str, part2: str, alias_map: Dict[str, str], rel_type: str) -> Optional[List[Dict[str, Any]]]:
        """조인 조건 파트에서 JOIN 관계 1개와 USE_COLUMN 관계 2개를 생성하여 리스트로 반환합니다."""
        part1_has_dot = '.' in part1
        part2_has_dot = '.' in part2

        table1, col1, table2, col2 = None, None, None, None
        alias1_u, alias2_u = None, None

        if part1_has_dot:
            alias1, col1 = part1.split('.', 1)
            alias1_u = alias1.upper()
            table1 = alias_map.get(alias1_u, alias1_u)
        else:
            col1 = part1

        if part2_has_dot:
            alias2, col2 = part2.split('.', 1)
            alias2_u = alias2.upper()
            table2 = alias_map.get(alias2_u, alias2_u)
        else:
            col2 = part2

        if col1 and col2:
            # 같은 테이블이라도(SELF JOIN) alias가 다르면 조인으로 인정합니다.
            # 단, 동일 alias 내 비교(예: T.A = T.B)는 필터로 취급하여 제외합니다.
            if table1 and table2 and table1 == table2 and alias1_u and alias2_u and alias1_u == alias2_u:
                return None

            return {
                'source_table': table1,
                'target_table': table2,
                'source_column': col1.upper(),
                'target_column': col2.upper(),
                'rel_type': rel_type,
                'confidence': 0.8,
                'alias_map': alias_map,
                'source_alias': alias1_u,
                'target_alias': alias2_u,
            }

        return None
    
    def _analyze_implicit_joins_in_where(self, sql_content: str, alias_map: dict, 
                                       analysis_patterns: dict) -> List[Dict[str, Any]]:
        """IMPLICIT JOIN 분석 (WHERE 절, Oracle 전통 방식)"""
        try:
            relationships = []
            implicit_patterns = analysis_patterns.get('implicit_joins', [])
            
            for pattern in implicit_patterns:
                matches = re.findall(pattern, sql_content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        if len(match) == 4:  # alias1.col1 = alias2.col2
                            alias1, col1, alias2, col2 = match
                            table1 = alias_map.get(alias1.upper(), alias1.upper())
                            table2 = alias_map.get(alias2.upper(), alias2.upper())
                            
                            # 유효한 테이블명인지 확인
                            if (table1 != table2 and table1 and table2 and
                                self._is_valid_table_name(table1) and self._is_valid_table_name(table2)):
                                is_outer = '\\(\\+\\)' in pattern
                                join_type = "ORACLE_OUTER_JOIN" if is_outer else "IMPLICIT_JOIN"
                                rel_type = 'JOIN_IMPLICIT_OUTER' if is_outer else 'JOIN_IMPLICIT'
                                relationships.append({
                                    'source_table': table1,
                                    'source_column': col1.upper(),
                                    'target_table': table2,
                                    'target_column': col2.upper(),
                                    'rel_type': rel_type,
                                    'join_type': join_type,
                                    'confidence': 0.9
                                })
            
            return relationships
            
        except Exception as e:
            handle_error(e, "IMPLICIT JOIN 분석 실패")
            return []
    
    def _get_join_type_from_pattern(self, join_type_raw: str, join_type_mapping: dict) -> str:
        """JOIN 타입 매핑"""
        try:
            for pattern, mapped_type in join_type_mapping.items():
                if re.match(pattern, join_type_raw, re.IGNORECASE):
                    return mapped_type
            return "UNKNOWN_JOIN"
        except Exception as e:
            handle_error(e, "JOIN 타입 매핑 실패")
            return "UNKNOWN_JOIN"
    
    def _parse_on_condition_for_tables(self, on_condition: str, alias_map: dict) -> Tuple[Optional[str], Optional[str]]:
        """ON 조건절에서 테이블 관계 추출"""
        try:
            pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)'
            match = re.search(pattern, on_condition, re.IGNORECASE)
            if match:
                alias1, _, alias2, _ = match.groups()
                table1 = alias_map.get(alias1.upper(), alias1.upper())
                table2 = alias_map.get(alias2.upper(), alias2.upper())
                return table1, table2
            return None, None
        except Exception as e:
            handle_error(e, "ON 조건절 테이블 추출 실패")
            return None, None
    
    def _is_valid_table_name(self, table_name: str) -> bool:
        """유효한 테이블명인지 검증"""
        try:
            # 기본 검증 규칙
            if not table_name or len(table_name) < 2:
                return False

            # 리터럴 값 체크 (YAML 설정 기반)
            from util.oracle_keyword_manager import is_literal_value, is_oracle_keyword
            if is_literal_value(table_name):
                return False

            # Oracle 키워드 체크 (YAML 설정 기반)
            if is_oracle_keyword(table_name):
                return False

            return True
        except Exception as e:
            handle_error(e, "테이블명 유효성 검증 실패")
            return False
    
    def _remove_duplicate_relationships(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 관계 제거"""
        try:
            unique_relationships = []
            seen = set()
            
            for rel in relationships:
                key = tuple(sorted((rel.get('source_table', ''), rel.get('target_table', ''))))
                if key not in seen:
                    seen.add(key)
                    unique_relationships.append(rel)
            
            return unique_relationships
        except Exception as e:
            handle_error(e, "중복 관계 제거 실패")
            return relationships
    
    def _post_process_relationships(self, relationships: List[Dict], alias_map: dict) -> List[Dict]:
        """관계 후처리 (정규화, 유효성 검증)"""
        try:
            processed_relationships = []
            
            for rel in relationships:
                # 테이블명 대문자 정규화
                if 'source_table' in rel:
                    rel['source_table'] = rel['source_table'].upper()
                if 'target_table' in rel:
                    rel['target_table'] = rel['target_table'].upper()
                
                # 유효성 검증
                if self._is_valid_relationship(rel):
                    processed_relationships.append(rel)
            
            return processed_relationships
        except Exception as e:
            handle_error(e, "관계 후처리 실패")
            return relationships
    
    def _is_valid_relationship(self, relationship: Dict) -> bool:
        """관계 유효성 검증"""
        try:
            required_fields = ['source_table', 'target_table', 'rel_type']
            for field in required_fields:
                if field not in relationship or not relationship[field]:
                    return False
            
            # 자기 자신과의 관계(SELF JOIN)는 기본적으로 제외하되,
            # - CONNECT BY(계층형) 관계는 허용
            # - EXPLICIT/IMPLICIT SELF JOIN은 alias가 다를 때만 허용
            if relationship['source_table'] == relationship['target_table']:
                rel_type = (relationship.get('rel_type') or '').upper()
                if rel_type == 'JOIN_CONNECT_BY':
                    src_col = relationship.get('source_column')
                    dst_col = relationship.get('target_column')
                    return bool(src_col and dst_col and src_col != dst_col)

                src_alias = relationship.get('source_alias')
                dst_alias = relationship.get('target_alias')
                if src_alias and dst_alias and src_alias != dst_alias:
                    return True

                return False
            
            return True
        except Exception as e:
            handle_error(e, "관계 유효성 검증 실패")
            return False
