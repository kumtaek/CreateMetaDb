"""
Java 동적 쿼리 추출기 - 심플 버전
목표: Java 파일에서 동적 SQL 쿼리 추출
"""

import re
from typing import List, Dict, Any
from util import handle_error


class JavaQueryExtractor:
    """Java 동적 쿼리 추출기 - 심플 버전"""
    
    def __init__(self):
        pass

    def extract_java_queries(self, content: str) -> List[Dict[str, Any]]:
        """Java 동적 쿼리 추출"""
        try:
            queries = []
            
            # 문자열 변수 추출
            string_variables = self._extract_string_variables(content)
            
            # 쿼리 변수만 필터링
            for var_name, var_content in string_variables.items():
                if self._is_sql_query(var_content):
                    queries.append({
                        'query_id': var_name,
                        'sql_content': var_content,
                        'query_type': self._detect_query_type(var_content)
                    })
            
            return queries
            
        except Exception as e:
            handle_error(e, "Java 동적 쿼리 추출 실패")
            return []

    def _extract_string_variables(self, content: str) -> Dict[str, str]:
        """문자열 변수 추출 - 심플 버전"""
        try:
            variables = {}
            
            # String 변수 선언 패턴
            patterns = [
                r'String\s+(\w+)\s*=\s*"([^"]*)"',
                r'String\s+(\w+)\s*=\s*\'([^\']*)\'',
                r'StringBuilder\s+(\w+)\s*=\s*new\s+StringBuilder\s*\(\s*"([^"]*)"\s*\)',
                r'StringBuffer\s+(\w+)\s*=\s*new\s+StringBuffer\s*\(\s*"([^"]*)"\s*\)'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    var_name = match.group(1)
                    var_content = match.group(2)
                    
                    # 공백, 탭, 주석 제거
                    var_content = re.sub(r'^\s+', '', var_content)
                    var_content = re.sub(r'\s+$', '', var_content)
                    
                    if var_content:
                        variables[var_name] = var_content
            
            # += 연산으로 누적된 문자열 처리
            append_patterns = [
                r'(\w+)\s*\+=\s*"([^"]*)"',
                r'(\w+)\.append\s*\(\s*"([^"]*)"\s*\)'
            ]
            
            for pattern in append_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    var_name = match.group(1)
                    append_content = match.group(2)
                    
                    if var_name in variables:
                        variables[var_name] += append_content
            
            return variables
            
        except Exception as e:
            handle_error(e, "문자열 변수 추출 실패")
            return {}

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

    def _detect_query_type(self, content: str) -> str:
        """쿼리 타입 감지"""
        try:
            content_upper = content.upper().strip()
            
            if content_upper.startswith('SELECT'):
                return 'SQL_SELECT'
            elif content_upper.startswith('INSERT'):
                return 'SQL_INSERT'
            elif content_upper.startswith('UPDATE'):
                return 'SQL_UPDATE'
            elif content_upper.startswith('DELETE'):
                return 'SQL_DELETE'
            elif content_upper.startswith('MERGE'):
                return 'SQL_MERGE'
            else:
                return 'SQL_SELECT'  # 기본값
                
        except Exception as e:
            handle_error(e, "쿼리 타입 감지 실패")
            return 'SQL_SELECT'
