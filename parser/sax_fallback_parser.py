"""
SAX Fallback 파서 모듈
- DOM 파싱 실패 시 SAX 파서로 자동 전환
- MyBatis XML 매퍼 파일 파싱
- RecursionError 해결을 위한 이벤트 기반 파싱

USER RULES:
- 하드코딩 금지: path_utils.get_config_path("parser/mybatis_keyword.yaml") 사용 (크로스플랫폼 대응)
- Exception 처리: 파싱에러는 has_error='Y', error_message 저장 후 계속 실행
- 공통함수 사용: util 모듈 활용
- 메뉴얼 기반: parser/manual/04_mybatis 참고
"""

import xml.sax
from xml.sax import expatreader
import os
import re
from typing import List, Dict, Any, Optional
from util import (
    ConfigUtils, FileUtils, HashUtils, ValidationUtils,
    app_logger, info, error, debug, warning, handle_error
)


class MyBatisSaxHandler(xml.sax.ContentHandler):
    """
    MyBatis 매퍼 XML을 파싱하기 위한 SAX 이벤트 핸들러
    - 이벤트 기반으로 XML 구조를 파싱하여 재귀 문제 해결
    """

    def __init__(self, config: Dict[str, Any]):
        """
        SAX 핸들러 초기화
        
        Args:
            config: MyBatis 키워드 설정
        """
        super().__init__()
        
        # 설정에서 SQL 태그 타입 가져오기 (하드코딩 지양)
        self.sql_tags = list(config.get('sql_statement_types', {}).keys())
        if not self.sql_tags:
            # USER RULES: 하드코딩 지양 - 설정에서 기본값 가져오기
            default_sql_tags = config.get('default_sql_tags', [])
            if default_sql_tags:
                self.sql_tags = default_sql_tags
            else:
                # 최후의 수단으로만 하드코딩 사용
                warning("설정에서 SQL 태그를 찾을 수 없어 기본값 사용")
                self.sql_tags = ['select', 'insert', 'update', 'delete']
        
        # 상태 관리 변수
        self.is_in_sql_tag = False      # SQL 태그 내부에 있는지 여부
        self.current_tag = ""           # 현재 처리 중인 태그 이름
        self.current_sql_id = ""        # 현재 SQL 태그의 ID
        self.current_sql_type = ""      # 현재 SQL 태그의 타입
        self.sql_buffer = []            # SQL 구문 조각을 모으는 버퍼
        self.tag_stack = []             # 중첩 구조 추적용 스택
        
        # 최종 결과물
        self.parsed_components = []
        self.join_relationships = []

    def startElement(self, tag: str, attributes: xml.sax.xmlreader.AttributesImpl):
        """
        여는 태그를 만났을 때 호출
        
        Args:
            tag: 태그 이름
            attributes: 태그 속성
        """
        self.current_tag = tag
        self.tag_stack.append(tag)
        
        if tag in self.sql_tags:
            self.is_in_sql_tag = True
            self.current_sql_type = tag
            self.current_sql_id = attributes.get("id", "")
            self.sql_buffer = []  # 새 SQL 태그 시작 시 버퍼 초기화
            info(f"SAX: SQL 태그 시작 - {tag} (id: {self.current_sql_id})")

    def characters(self, content: str):
        """
        태그 내의 텍스트 데이터를 만났을 때 호출
        
        Args:
            content: 텍스트 내용
        """
        # characters는 여러 번 호출될 수 있으므로 버퍼에 계속 추가
        if self.is_in_sql_tag and content.strip():
            self.sql_buffer.append(content)

    def endElement(self, tag: str):
        """
        닫는 태그를 만났을 때 호출
        
        Args:
            tag: 태그 이름
        """
        if self.tag_stack:
            self.tag_stack.pop()
        
        if tag in self.sql_tags:
            # SQL 태그가 끝나면, 버퍼에 모인 텍스트를 합쳐서 결과물에 추가
            full_sql = "".join(self.sql_buffer).strip()
            
            if full_sql and self.current_sql_id:
                # SQL 내용이 있고 ID가 있는 경우만 추가
                component = {
                    "sql_id": self.current_sql_id,
                    "sql_content": full_sql,
                    "tag_name": self.current_sql_type
                }
                self.parsed_components.append(component)
                info(f"SAX: SQL 컴포넌트 추출 완료 - {self.current_sql_id}")
            
            # 상태 변수 초기화
            self.is_in_sql_tag = False
            self.current_tag = ""
            self.current_sql_id = ""
            self.current_sql_type = ""
            self.sql_buffer = []


class MyBatisSaxParser:
    """
    SAX 파서를 감싸는 래퍼 클래스
    - DOM 파싱 실패 시 Fallback으로 사용
    - MyBatis XML 매퍼 파일 전용 파싱
    """

    def __init__(self, config_path: str = None):
        """
        SAX 파서 초기화
        
        Args:
            config_path: 설정 파일 경로 (선택적)
        """
        try:
            # USER RULES: 공통함수 사용 지향
            config_utils = ConfigUtils()
            
            if config_path is None:
                # USER RULES: 공통함수 사용 지향 - 경로 처리
                from util import PathUtils
                path_utils = PathUtils()
                config_path = path_utils.get_config_path("parser/mybatis_keyword.yaml")
            
            self.config = config_utils.load_yaml_config(config_path)
            if not self.config:
                # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                # USER RULES: Exception 발생시 handle_error()로 exit()
                handle_error(Exception(f"설정 파일을 로드할 수 없습니다: {config_path}"), "SAX 파서 설정 로드 실패")
                return
            
            self.stats = {
                'files_processed': 0,
                'files_skipped': 0,
                'sql_queries_extracted': 0,
                'join_relationships_created': 0,
                'errors': 0
            }
            
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            # USER RULES: Exception 발생시 handle_error()로 exit()
            handle_error(e, f"SAX 파서 초기화 실패: {config_path}")

    def parse_file(self, xml_file_path: str) -> Dict[str, Any]:
        """
        주어진 XML 파일을 SAX 방식으로 파싱
        
        Args:
            xml_file_path: XML 파일 경로
            
        Returns:
            파싱 결과 딕셔너리
        """
        try:
            # USER RULES: 공통함수 사용 지향 - 경로 검증
            if not os.path.exists(xml_file_path):
                error_message = f"XML 파일이 존재하지 않습니다: {xml_file_path}"
                warning(error_message)
                return {
                    'has_error': 'Y', 
                    'error_message': error_message,
                    'sql_queries': [],
                    'join_relationships': [],
                    'file_path': xml_file_path
                }
            
            debug(f"SAX 파싱 시작: {xml_file_path}")
            
            # 1. 파서와 핸들러 인스턴스 생성 (Expat 파서 명시)
            parser = expatreader.create_parser()
            
            # 재귀적 DTD 엔티티로 인한 RecursionError 방지 (보안 설정 강화)
            # 외부 일반 엔티티와 외부 파라미터 엔티티 모두 비활성화
            parser.setFeature(xml.sax.handler.feature_external_ges, False)
            parser.setFeature(xml.sax.handler.feature_external_pes, False)
            
            handler = MyBatisSaxHandler(self.config)
            parser.setContentHandler(handler)
            
            # 2. 파싱 실행
            parser.parse(xml_file_path)
            
            # 3. SQL 쿼리 정보 생성
            sql_queries = []
            for component in handler.parsed_components:
                sql_id = component.get('sql_id')
                sql_content = component.get('sql_content')
                tag_name = component.get('tag_name', 'select')
                
                if sql_content and sql_content.strip():
                    query_info = {
                        'tag_name': tag_name,
                        'query_id': sql_id,
                        'query_type': tag_name,
                        'sql_content': sql_content,
                        'file_path': xml_file_path,
                        'line_start': 1,  # SAX에서는 정확한 라인 번호 추출이 어려움
                        'line_end': 1,
                        'hash_value': HashUtils().generate_md5(sql_content)
                    }
                    sql_queries.append(query_info)
            
            # 4. JOIN 관계 분석 (간단한 버전)
            join_relationships = self._analyze_joins_simple(sql_queries)
            
            # 5. 통계 업데이트
            self.stats['files_processed'] += 1
            self.stats['sql_queries_extracted'] += len(sql_queries)
            self.stats['join_relationships_created'] += len(join_relationships)
            
            debug(f"SAX 파싱 성공: {xml_file_path} - SQL {len(sql_queries)}개, 관계 {len(join_relationships)}개")
            
            # 6. 성공 결과 반환 (통합 데이터 구조에 맞춰)
            return {
                'has_error': 'N',
                'error_message': '',
                'sql_queries': sql_queries,
                'join_relationships': join_relationships,
                'file_path': xml_file_path
            }
            
        except xml.sax.SAXParseException as e:
            # USER RULES: 파싱에러는 has_error='Y', error_message 저장 후 계속 실행
            error_message = f"SAX 파싱 실패 (XML 문법 오류): {xml_file_path} - {str(e)}"
            warning(error_message)
            self.stats['errors'] += 1
            return {
                'has_error': 'Y', 
                'error_message': error_message,
                'sql_queries': [],
                'join_relationships': [],
                'file_path': xml_file_path
            }
            
        except Exception as e:
            # USER RULES: 파싱에러는 has_error='Y', error_message 저장 후 계속 실행
            error_message = f"SAX 파싱 중 예상치 못한 오류: {xml_file_path} - {str(e)}"
            warning(error_message)
            self.stats['errors'] += 1
            return {
                'has_error': 'Y', 
                'error_message': error_message,
                'sql_queries': [],
                'join_relationships': [],
                'file_path': xml_file_path
            }

    def _analyze_joins_simple(self, sql_queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        간단한 JOIN 관계 분석 (SAX용)
        USER RULES: 하드코딩 지양 - 설정 기반 패턴 매칭
        
        Args:
            sql_queries: SQL 쿼리 리스트
            
        Returns:
            JOIN 관계 리스트
        """
        join_relationships = []
        
        try:
            # USER RULES: 하드코딩 지양 - 설정에서 패턴 가져오기
            join_patterns = self.config.get('join_patterns', {})
            from_pattern = join_patterns.get('from_pattern', r'FROM\s+(\w+)')
            join_pattern = join_patterns.get('join_pattern', r'JOIN\s+(\w+)')
            join_keywords = join_patterns.get('join_keywords', ['JOIN'])
            
            for query in sql_queries:
                sql_content = query.get('sql_content', '').upper()
                
                # 설정 기반 JOIN 키워드 매칭
                has_join = any(keyword in sql_content for keyword in join_keywords)
                if has_join:
                    # FROM 절에서 테이블 추출 (설정 기반 패턴)
                    from_match = re.search(from_pattern, sql_content)
                    if from_match:
                        base_table = from_match.group(1)
                        
                        # JOIN 절에서 테이블 추출 (설정 기반 패턴)
                        join_matches = re.findall(join_pattern, sql_content)
                        for join_table in join_matches:
                            relationship = {
                                'source_table': base_table,
                                'target_table': join_table,
                                'relationship_type': 'JOIN',
                                'description': f"JOIN relationship from {base_table} to {join_table}",
                                'source_file': query.get('file_path', ''),
                                'source_line': query.get('line_start', 1)
                            }
                            join_relationships.append(relationship)
            
            return join_relationships
            
        except Exception as e:
            # USER RULES: 파싱에러는 has_error='Y', error_message 저장 후 계속 실행
            warning(f"SAX JOIN 분석 실패: {str(e)}")
            return []

    def get_stats(self) -> Dict[str, int]:
        """
        파싱 통계 반환
        
        Returns:
            통계 딕셔너리
        """
        return self.stats.copy()
