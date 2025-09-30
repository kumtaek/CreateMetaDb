"""
MyBatis XML 쿼리 추출기 - 심플 버전
목표: XML에서 MyBatis 태그만 제거하고 순수 SQL 추출
"""

import re
from typing import List, Dict, Any
from util import handle_error


class MyBatisAnalyzer:
    """MyBatis XML 쿼리 추출기 - 심플 버전"""
    
    def __init__(self):
        pass

    def analyze_xml_file(self, file_path: str) -> Dict[str, Any]:
        """
        XML 파일 분석 - MyBatis 쿼리 추출
        
        Returns:
            {
                'file_path': str,
                'queries': [{'query_id': 'methodName', 'sql_content': 'SELECT ...'}]
            }
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # MyBatis 쿼리 추출
            queries = self._extract_mybatis_queries(content)

            return {
                'file_path': file_path,
                'queries': queries
            }

        except Exception as e:
            handle_error(e, f"XML 파일 분석 실패: {file_path}")
            return {
                'file_path': file_path,
                'queries': []
            }

    def _extract_mybatis_queries(self, content: str) -> List[Dict[str, Any]]:
        """MyBatis 쿼리 추출 - 심플 버전"""
        queries = []
        try:
            # MyBatis 태그별 쿼리 추출
            for tag in ['select', 'insert', 'update', 'delete', 'merge']:
                tag_queries = self._extract_queries_by_tag(content, tag)
                queries.extend(tag_queries)
            
            return queries
            
        except Exception as e:
            handle_error(e, "MyBatis 쿼리 추출 실패")
            return []

    def _extract_queries_by_tag(self, content: str, tag: str) -> List[Dict[str, Any]]:
        """특정 태그의 쿼리 추출"""
        queries = []
        try:
            # 태그 패턴: <tag id="methodName">...</tag>
            pattern = rf'<{tag}\s+id="([^"]+)"[^>]*>(.*?)</{tag}>'
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                query_id = match.group(1)
                tag_content = match.group(2)
                
                # MyBatis 태그 제거하고 순수 SQL 추출
                sql_content = self._remove_mybatis_tags(tag_content)
                
                if sql_content and self._is_sql_query(sql_content):
                    queries.append({
                        'query_id': query_id,
                        'sql_content': sql_content,
                        'query_type': f'SQL_{tag.upper()}'
                    })
            
            return queries
            
        except Exception as e:
            handle_error(e, f"{tag} 태그 쿼리 추출 실패")
            return []

    def _remove_mybatis_tags(self, content: str) -> str:
        """MyBatis 태그 제거하고 순수 SQL 추출 - 심플 버전"""
        try:
            sql_content = content
            
            # 1. MyBatis 동적 태그 제거 (심플하게)
            mybatis_tags = ['if', 'choose', 'when', 'otherwise', 'foreach', 'set', 'where', 'trim', 'bind', 'include']
            
            for tag in mybatis_tags:
                # <tag>...</tag> 형태 제거
                sql_content = re.sub(rf'<{tag}(?:\s+[^>]*)?>.*?</{tag}>', '', sql_content, flags=re.DOTALL | re.IGNORECASE)
                # <tag/> 형태 제거
                sql_content = re.sub(rf'<{tag}(?:\s+[^>]*)?/>', '', sql_content, flags=re.IGNORECASE)
            
            # 2. 남은 XML 태그 제거
            sql_content = re.sub(r'<[^>]+>', '', sql_content)
            
            # 3. 주석 제거
            sql_content = re.sub(r'<!--.*?-->', '', sql_content, flags=re.DOTALL)
            
            # 4. 공백 정리
            sql_content = re.sub(r'\s+', ' ', sql_content).strip()
            
            return sql_content
            
        except Exception as e:
            handle_error(e, "MyBatis 태그 제거 실패")
            return content

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