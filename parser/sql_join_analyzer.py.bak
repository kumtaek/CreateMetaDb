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
                        r"([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\+\)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)"
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
        SQL 조인 관계 분석 (세 가지 유형 분리 처리)
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
            join_pattern = r'\bJOIN\s+[\w\.]+(?:\s+AS)?\s*\w*\s+ON\s*\(([^)]+)\)'
            on_clauses = re.findall(join_pattern, sql_content, re.IGNORECASE)
            
            for on_clause in on_clauses:
                condition_pattern = r'([\w\.]+)\s*=\s*([\w\.]+)'
                conditions = re.findall(condition_pattern, on_clause)
                for cond in conditions:
                    rel = self._create_relationship_from_condition(cond[0], cond[1], alias_map, 'JOIN_EXPLICIT')
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

    def _analyze_implicit_joins(self, sql_content: str, alias_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """WHERE 절에서 암시적 JOIN 관계를 분석합니다."""
        try:
            relationships = []
            where_match = re.search(r'\bWHERE\s+(.*?)(?=\bGROUP|\bORDER|\bHAVING|;|$)', sql_content, re.IGNORECASE)
            if where_match:
                where_clause = where_match.group(1)
                condition_pattern = r'([\w\.]+)\s*=\s*([\w\.]+)'
                conditions = re.findall(condition_pattern, where_clause)
                for cond in conditions:
                    rel = self._create_relationship_from_condition(cond[0], cond[1], alias_map, 'JOIN_IMPLICIT')
                    if rel:
                        relationships.append(rel)
            return relationships
        except Exception as e:
            handle_error(e, "IMPLICIT JOIN 분석 실패")
            return []
    
    def _normalize_sql_for_analysis(self, sql_content: str, dynamic_patterns: dict) -> str:
        """SQL 정규화 (주석 제거, 동적 태그 처리)"""
        try:
            normalized_sql = sql_content
            
            # SQL 주석 제거 - 한 줄 주석 (-- ...)
            normalized_sql = re.sub(r'--.*$', '', normalized_sql, flags=re.MULTILINE)
            
            # SQL 주석 제거 - 블록 주석 (/* ... */)
            normalized_sql = re.sub(r'/\*.*?\*/', '', normalized_sql, flags=re.DOTALL)
            
            # 동적 태그 처리 (MyBatis 등)
            dynamic_tag_patterns = dynamic_patterns.get('dynamic_tags', [])
            for pattern in dynamic_tag_patterns:
                normalized_sql = re.sub(pattern, r'\1', normalized_sql, flags=re.DOTALL | re.IGNORECASE)
            
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
            join_pattern = r'JOIN\s+[\w\.]+\s*(?:AS)?\s*\w*\s+ON\s+([^{;]*?)(?=\bWHERE|\bGROUP|\bORDER|\bJOIN|;|$)'
            on_clauses = re.findall(join_pattern, sql_content, re.IGNORECASE)
            
            for on_clause in on_clauses:
                condition_pattern = r'([\w\.]+)\s*=\s*([\w\.]+)'
                conditions = re.findall(condition_pattern, on_clause)
                for cond in conditions:
                    rel = self._create_relationship_from_condition(cond[0], cond[1], alias_map, 'JOIN_EXPLICIT')
                    if rel:
                        relationships.append(rel)
            return relationships
        except Exception as e:
            handle_error(e, "EXPLICIT JOIN 분석 실패")
            return []


    def _create_relationship_from_condition(self, part1: str, part2: str, alias_map: Dict[str, str], rel_type: str) -> Optional[Dict[str, Any]]:
        """조인 조건 파트에서 관계 딕셔너리를 생성합니다."""
        if '.' not in part1 or '.' not in part2:
            return None

        alias1, col1 = part1.split('.')
        alias2, col2 = part2.split('.')

        table1 = alias_map.get(alias1.upper())
        table2 = alias_map.get(alias2.upper())

        if table1 and table2 and table1 != table2:
            return {
                'source_table': table1,
                'target_table': table2,
                'source_column': col1.upper(),
                'target_column': col2.upper(),
                'rel_type': rel_type,
                'confidence': 0.9
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
                                join_type = "ORACLE_OUTER_JOIN" if "(+)" in str(match) else "IMPLICIT_JOIN"
                                relationships.append({
                                    'source_table': table1,
                                    'source_column': col1.upper(),
                                    'target_table': table2,
                                    'target_column': col2.upper(),
                                    'rel_type': 'JOIN_IMPLICIT',
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
            
            # SQL 키워드 제외 (간단한 버전)
            sql_keywords = {'SELECT', 'FROM', 'WHERE', 'JOIN', 'ON', 'AND', 'OR', 'NOT'}
            if table_name.upper() in sql_keywords:
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
            
            # 자기 자신과의 관계는 제외
            if relationship['source_table'] == relationship['target_table']:
                return False
            
            return True
        except Exception as e:
            handle_error(e, "관계 유효성 검증 실패")
            return False
