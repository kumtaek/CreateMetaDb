"""
XML 파서 모듈 (단순화 버전)
- 정규식 기반으로 MyBatis XML 파일에서 SQL 쿼리를 추출합니다.
- 복잡한 DOM/SAX 파서를 제거하여 단순성, 속도, 안정성을 높였습니다.

USER RULES:
- 하드코딩 금지
- Exception 처리: handle_error() 공통함수 사용
- 공통함수 사용: util 모듈 활용
"""

import os
import re
import html
from typing import List, Dict, Any

from util import (
    ConfigUtils, FileUtils, HashUtils, PathUtils,
    app_logger, info, error, debug, warning, handle_error
)
from .sql_join_analyzer import SqlJoinAnalyzer
from .sql_parser import SqlParser

class XmlParser:
    """XML 파서 - 3~4단계 통합 처리 (단순화된 정규식 기반)"""

    def __init__(self, config_path: str = None, project_name: str = None):
        from util.global_project import get_global_project_name, get_global_project_id, is_global_project_info_set

        if is_global_project_info_set():
            self.project_name = get_global_project_name()
            self.project_id = get_global_project_id()
        else:
            self.project_name = project_name
            self.project_id = None

        self.current_file_id = None
        self.path_utils = PathUtils()
        
        if config_path is None:
            sql_config_path = self.path_utils.get_parser_config_path("sql")
            xml_config_path = self.path_utils.get_config_path("parser/xml_parser_config.yaml")
            sql_config = self._load_config(sql_config_path)
            xml_config = self._load_config(xml_config_path)
            self.config = {**xml_config, **sql_config}
        else:
            self.config_path = config_path
            self.config = self._load_config()

        self.sql_join_analyzer = SqlJoinAnalyzer(self.config)

        self.stats = {
            'files_processed': 0,
            'sql_queries_extracted': 0,
            'join_relationships_created': 0,
            'errors': 0
        }

    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        try:
            config_utils = ConfigUtils()
            path = config_path
            config = config_utils.load_yaml_config(path)
            if not config:
                warning(f"Config file could not be loaded or is empty: {path}")
                return {}
            return config
        except Exception as e:
            error(f"Failed to load config file: {config_path} - {e}")
            return {}

    def get_filtered_xml_files(self, project_path: str) -> List[str]:
        try:
            file_utils = FileUtils()
            xml_files = []
            
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith('.xml'):
                        file_path = self.path_utils.normalize_path(os.path.join(root, file))
                        if self._is_mybatis_xml_file(file_path):
                            xml_files.append(file_path)
            
            info(f"MyBatis XML files collected: {len(xml_files)}")
            return xml_files
            
        except Exception as e:
            handle_error(e, "XML file collection failed", exit_code=1)
            return []
    
    def _is_mybatis_xml_file(self, file_path: str) -> bool:
        try:
            file_utils = FileUtils()
            content = file_utils.read_file(file_path)
            if not content:
                return False
            
            mybatis_indicators = ['mybatis.org', 'mybatis-3.org', 'mapper']
            if 'sql_statement_types' in self.config:
                mybatis_indicators.extend(self.config.get('sql_statement_types', {}).keys())
            
            content_lower = content.lower()
            return any(indicator in content_lower for indicator in mybatis_indicators)
            
        except Exception as e:
            warning(f"MyBatis XML file check failed: {file_path}, Error: {str(e)}")
            return False

    def extract_sql_queries_and_analyze_relationships(self, xml_file: str) -> Dict[str, Any]:
        """XML MyBatis 파일에서 SQL 쿼리를 추출하는 간단화된 방식
        MyBatis 태그만 제거하고 쿼리 내용만 남기는 심플한 로직"""
        sql_queries = []
        try:
            with open(xml_file, 'r', encoding='utf-8', errors='ignore') as f:
                xml_content = f.read()

            # MyBatis SQL 태그들 추출 (select, insert, update, delete, merge)
            # id 속성이 있는 태그만 처리
            mybatis_tags = ['select', 'insert', 'update', 'delete', 'merge']
            pattern = re.compile(
                rf'<({"|".join(mybatis_tags)})\s+id="([^"]+)"[^>]*>(.*?)</\1>',
                re.DOTALL | re.IGNORECASE
            )

            for match in pattern.finditer(xml_content):
                tag_name = match.group(1).lower()
                query_id = match.group(2)
                inner_content = match.group(3)

                # 1. CDATA 섹션 처리 (내용만 남기기)
                cleaned_content = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', inner_content, flags=re.DOTALL)

                # 2. 모든 XML 태그 제거 (MyBatis 동적 태그 포함)
                cleaned_content = re.sub(r'<[^>]+>', ' ', cleaned_content)

                # 3. HTML 엔티티 디코딩
                cleaned_content = html.unescape(cleaned_content)

                # 4. 공백 정리
                sql_content = ' '.join(cleaned_content.split())

                if not sql_content.strip():
                    continue

                # 5. SQL 타입 결정
                sql_upper = sql_content.upper().strip()
                if tag_name == 'select' or sql_upper.startswith('SELECT'):
                    query_type = 'SQL_SELECT'
                elif tag_name == 'insert' or sql_upper.startswith('INSERT'):
                    query_type = 'SQL_INSERT'
                elif tag_name == 'update' or sql_upper.startswith('UPDATE'):
                    query_type = 'SQL_UPDATE'
                elif tag_name == 'delete' or sql_upper.startswith('DELETE'):
                    query_type = 'SQL_DELETE'
                elif tag_name == 'merge' or sql_upper.startswith('MERGE'):
                    query_type = 'SQL_MERGE'
                else:
                    query_type = 'QUERY'  # 알 수 없는 타입

                query_info = {
                    'tag_name': tag_name,
                    'query_id': query_id,
                    'query_type': query_type,
                    'sql_content': sql_content,
                    'file_path': xml_file,
                    'line_start': 1,  # XML에서는 라인 번호를 정확히 계산하기 어려우므로 1로 설정
                    'line_end': 1,
                    'hash_value': HashUtils().generate_md5(sql_content),
                    'used_tables': [],  # 이후 공통 처리에서 추출
                    'join_relationships': []  # 이후 공통 처리에서 추출
                }
                sql_queries.append(query_info)
                debug(f"MyBatis XML 쿼리 추출: {query_id} - {query_type}")

            self.stats['files_processed'] += 1
            self.stats['sql_queries_extracted'] += len(sql_queries)

            return {
                'sql_queries': sql_queries,
                'join_relationships': [],  # 공통 처리에서 처리
                'file_path': xml_file,
                'has_error': 'N',
                'error_message': None
            }

        except Exception as e:
            handle_error(e, f"XML MyBatis 파싱 실패: {xml_file}")
            return {
                'sql_queries': [],
                'join_relationships': [],
                'file_path': xml_file,
                'has_error': 'Y',
                'error_message': f"XML 파싱 실패: {str(e)}"
            }

    def get_statistics(self) -> Dict[str, Any]:
        return self.stats.copy()

    def reset_statistics(self):
        self.stats = {
            'files_processed': 0,
            'sql_queries_extracted': 0,
            'join_relationships_created': 0,
            'errors': 0
        }