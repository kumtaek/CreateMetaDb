"""
JPA 쿼리 추출기 - 심플 버전
목표: @Query 어노테이션에서 쿼리 추출
"""

import re
from typing import List, Dict, Any
from util import handle_error


class JpaQueryExtractor:
    """JPA 쿼리 추출기 - 심플 버전"""
    
    def __init__(self):
        pass

    def extract_jpa_queries(self, content: str) -> List[Dict[str, Any]]:
        """JPA 쿼리 추출"""
        try:
            queries = []
            
            # @Query 어노테이션 패턴
            pattern = r'@Query\s*\([^)]*\)\s*(\w+)\s*\([^)]*\)\s*;'
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                method_name = match.group(1)
                full_match = match.group(0)
                
                # @Query에서 SQL 추출
                sql_content = self._extract_sql_from_query_annotation(full_match)
                
                if sql_content and self._is_sql_query(sql_content):
                    queries.append({
                        'query_id': method_name,
                        'sql_content': sql_content,
                        'query_type': 'SQL_SELECT'  # JPA는 주로 SELECT
                    })
            
            return queries
            
        except Exception as e:
            handle_error(e, "JPA 쿼리 추출 실패")
            return []

    def _extract_sql_from_query_annotation(self, query_annotation: str) -> str:
        """@Query 어노테이션에서 SQL 추출 - 심플 버전"""
        try:
            # @Query(...) 패턴에서 괄호 안 내용 추출
            query_pattern = r'@Query\s*\(\s*([^)]+?)\s*\)'
            match = re.search(query_pattern, query_annotation, re.DOTALL | re.IGNORECASE)
            
            if match:
                query_content = match.group(1)
                # 쌍따옴표 안 문자열만 추출
                string_parts = re.findall(r'"([^"]*)"', query_content, re.DOTALL)
                if string_parts:
                    return ' '.join(part.strip() for part in string_parts).strip()
            
            return ""
            
        except Exception as e:
            handle_error(e, "SQL 추출 실패")
            return ""

    def _is_sql_query(self, content: str) -> bool:
        """SQL 쿼리인지 확인"""
        try:
            if not content or len(content.strip()) < 3:
                return False
            
            # SQL 키워드로 시작하는지 확인
            sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'WITH']
            content_upper = content.upper().strip()
            
            for keyword in sql_keywords:
                if content_upper.startswith(keyword):
                    return True
            
            return False
            
        except Exception as e:
            handle_error(e, "SQL 쿼리 확인 실패")
            return False
