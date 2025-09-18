"""
XML 파서 모듈
- 3~4단계 통합 처리: XML 파일에서 SQL 쿼리 추출 및 JOIN 관계 분석
- MyBatis 동적 SQL 태그 처리 및 Oracle 암시적 JOIN 분석
- 메모리 최적화 (스트리밍 처리)

USER RULES:
- 하드코딩 금지: path_utils.get_parser_config_path("sql") 사용 (크로스플랫폼 대응)
- Exception 처리: handle_error() 공통함수 사용
- 공통함수 사용: util 모듈 활용
- 메뉴얼 기반: parser/manual/04_mybatis 참고
"""

import os
import re
import sys
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from util import (
    ConfigUtils, FileUtils, HashUtils, ValidationUtils, PathUtils,
    app_logger, info, error, debug, warning, handle_error
)
from util.sql_join_analyzer import SqlJoinAnalyzer


class XmlParser:
    """XML 파서 - 3~4단계 통합 처리"""

    def __init__(self, config_path: str = None, project_name: str = None):
        """
        XML 파서 초기화

        Args:
            config_path: 설정 파일 경로
            project_name: 프로젝트명 (선택적, 전역에서 가져옴)
        """
        # USER RULES: 하드코딩 지양 - 프로젝트 정보 전역 관리
        from util.global_project import get_global_project_name, get_global_project_id, is_global_project_info_set

        # 전역 프로젝트 정보 활용 (실행 중 변경되지 않는 값)
        if is_global_project_info_set():
            self.project_name = get_global_project_name()
            self.project_id = get_global_project_id()
        else:
            # 개별 설정이 있는 경우 (테스트 등)
            self.project_name = project_name
            self.project_id = None

        # 현재 처리 중인 파일의 file_id (메모리 최적화)
        self.current_file_id = None

        # PathUtils 인스턴스 생성 (공통함수 사용)
        self.path_utils = PathUtils()
        
        if config_path is None:
            # USER RULES: 하드코딩 지양 - 공통함수 사용 (크로스플랫폼 대응)
            sql_config_path = self.path_utils.get_parser_config_path("sql")
            xml_config_path = self.path_utils.get_config_path("parser/xml_parser_config.yaml")
            dom_rules_path = self.path_utils.get_config_path("parser/mybatis_dom_rules.yaml")
            sql_config = self._load_config(sql_config_path)
            xml_config = self._load_config(xml_config_path)
            self.dom_rules = self._load_config(dom_rules_path)
            self.config = {**xml_config, **sql_config}
        else:
            self.config_path = config_path
            self.config = self._load_config()
            self.dom_rules = {}  # 개별 설정 시에는 DOM 규칙 없음

        self.stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'sql_queries_extracted': 0,
            'join_relationships_created': 0,
            'errors': 0
        }
        
        # 공통 SQL 조인 분석기 초기화
        self.sql_join_analyzer = SqlJoinAnalyzer(self.config)

    def _get_project_id(self) -> int:
        """
        현재 프로젝트 ID 반환 (전역 정보 우선 활용)

        Returns:
            프로젝트 ID

        Raises:
            Exception: 프로젝트 ID가 설정되지 않은 경우
        """
        # 전역 프로젝트 정보가 있으면 우선 사용
        from util.global_project import get_global_project_id, is_global_project_info_set

        if is_global_project_info_set():
            return get_global_project_id()
        elif self.project_id is not None:
            return self.project_id
        else:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            # USER RULES: Exception 발생시 handle_error()로 exit()
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(Exception("프로젝트 ID가 설정되지 않았습니다"), "프로젝트 ID 획득 실패")


    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        try:
            # USER RULES: 공통함수 사용 지향
            config_utils = ConfigUtils()
            path = config_path or self.config_path
            config = config_utils.load_yaml_config(path)
            if not config:
                # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
                # USER RULES: Exception 발생시 handle_error()로 exit()
                # exception은 handle_error()로 exit해야 에러 인지가 가능하다
                handle_error(Exception(f"설정 파일을 로드할 수 없습니다: {path}"), "설정 파일 로드 실패")
                return self._get_default_config()
            return config
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            # USER RULES: Exception 발생시 handle_error()로 exit()
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, f"설정 파일 로드 실패: {config_path or self.config_path}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            'sql_patterns': {
                'explicit_joins': [],
                'implicit_joins': []
            }
        }

    def get_filtered_xml_files(self, project_path: str = None) -> List[str]:
        try:
            # USER RULES: 공통함수 사용 지향
            file_utils = FileUtils()

            # USER RULES: 하드코딩 지양 - PathUtils 공통함수 사용
            if project_path is None and self.project_name:
                from util import PathUtils
                path_utils = PathUtils()
                project_path = path_utils.get_project_source_path(self.project_name)

            if not project_path:
                # USER RULES: Exception 발생시 handle_error()로 exit()
                # exception은 handle_error()로 exit해야 에러 인지가 가능하다
                handle_error(Exception("프로젝트 경로가 지정되지 않았습니다"), "XML 파일 수집 실패")

            xml_files = []
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    # USER RULES: 하드코딩 지양 - 설정에서 XML 확장자 가져오기
                    xml_extensions = self.config.get('xml_extensions', ['.xml'])
                    if any(file.endswith(ext) for ext in xml_extensions):
                        file_path = self.path_utils.join_path(root, file)
                        if self._is_mybatis_xml_file(file_path):
                            xml_files.append(file_path)
            info(f"MyBatis XML 파일 수집 완료: {len(xml_files)}개")
            return xml_files
        except Exception as e:
            # USER RULES: Exception 발생시 handle_error()로 exit()
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, "XML 파일 수집 실패")
            return []

    def _is_mybatis_xml_file(self, file_path: str) -> bool:
        try:
            file_utils = FileUtils()
            content = file_utils.read_file(file_path)
            if not content:
                return False
            # USER RULES: 하드코딩 지양 - 설정에서 MyBatis 지시자 가져오기
            mybatis_indicators = self.config.get('mybatis_indicators', ['mybatis.org', 'mybatis-3.org', 'mapper'])
            mybatis_indicators.extend(self.config.get('sql_statement_types', {}).keys())
            content_lower = content.lower()
            return any(indicator in content_lower for indicator in mybatis_indicators)
        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, f"MyBatis XML 파일 확인 실패: {file_path}")

    def extract_sql_queries_and_analyze_relationships(self, xml_file: str) -> Dict[str, Any]:
        """
        XML 파일에서 SQL 쿼리를 추출하고 관계를 분석합니다.
        DOM → SAX → 정규식 순서로 파싱을 시도하고, 모두 실패하면 has_error='Y' 처리합니다.
        """
        # current_file_id는 외부(xml_loading.py)에서 설정되므로 여기서 재설정하지 않음
        if self.current_file_id is None:
            handle_error(Exception("file_id가 설정되지 않았습니다. xml_loading.py에서 current_file_id를 설정해야 합니다."), "file_id 설정 오류")
        
        debug(f"현재 처리 중인 XML 파일: {xml_file}, file_id: {self.current_file_id}")
        
        # 1단계: DOM 기반 파싱 시도
        debug(f"DOM 기반 파싱 시도: {xml_file}")
        dom_result = self._parse_with_dom(xml_file)
        
        if dom_result and not dom_result.get('has_error'):
            debug(f"DOM 기반 파싱 성공: {xml_file}")
            self.stats['files_processed'] += 1
            self.stats['sql_queries_extracted'] += len(dom_result.get('sql_queries', []))
            self.stats['join_relationships_created'] += len(dom_result.get('join_relationships', []))
            return dom_result
        else:
            debug(f"DOM 기반 파싱 실패, SAX 파서로 Fallback: {xml_file}")
            if dom_result:
                debug(f"DOM 파싱 오류 메시지: {dom_result.get('error_message')}")

        # 2단계: SAX 파서로 Fallback
        debug(f"SAX 파서로 Fallback: {xml_file}")
        try:
            from .sax_fallback_parser import MyBatisSaxParser
            sax_parser = MyBatisSaxParser()
            sax_result = sax_parser.parse_file(xml_file)
            
            if sax_result and not sax_result.get('has_error'):
                debug(f"SAX 파싱 성공: {xml_file}")
                self.stats['files_processed'] += 1
                self.stats['sql_queries_extracted'] += len(sax_result.get('sql_queries', []))
                self.stats['join_relationships_created'] += len(sax_result.get('join_relationships', []))
                return sax_result
            else:
                debug(f"SAX 파싱도 실패, 정규식 파서로 최종 Fallback: {xml_file}")
                if sax_result:
                    debug(f"SAX 파싱 오류 메시지: {sax_result.get('error_message')}")
        except Exception as sax_e:
            debug(f"SAX 파서 초기화 실패: {sax_e}")

        # 3단계: 최종 Fallback - 정규식 기반 파싱
        debug(f"정규식 기반 파서로 최종 Fallback: {xml_file}")
        try:
            regex_result = self._parse_with_regex(xml_file)
            if regex_result and not regex_result.get('has_error'):
                debug(f"정규식 파싱 성공: {xml_file}")
                self.stats['files_processed'] += 1
                self.stats['sql_queries_extracted'] += len(regex_result.get('sql_queries', []))
                self.stats['join_relationships_created'] += len(regex_result.get('join_relationships', []))
                return regex_result
            else:
                # 모든 파싱 방법이 실패한 경우
                error_message = f"모든 파싱 방법(DOM, SAX, 정규식)이 실패했습니다: {xml_file}"
                self.stats['errors'] += 1
                return {'sql_queries': [], 'join_relationships': [], 'file_path': xml_file, 'has_error': 'Y', 'error_message': error_message}
        except Exception as regex_e:
            # 정규식 파싱마저 실패하는 경우
            error_message = f"정규식 파싱도 실패: {xml_file} - {str(regex_e)}"
            self.stats['errors'] += 1
            return {'sql_queries': [], 'join_relationships': [], 'file_path': xml_file, 'has_error': 'Y', 'error_message': error_message}

    def _parse_with_dom(self, xml_file: str) -> Optional[Dict[str, Any]]:
        """
        (신규) DOM 기반으로 MyBatis XML을 파싱하고 SQL을 재구성합니다.
        """
        try:
            # XML 파일을 DOM으로 파싱
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # MyBatis XML 파일인지 확인
            if not self._is_mybatis_xml(root):
                return None

            # MyBatis DOM 파서 생성
            mybatis_parser = MybatisParser(self.dom_rules)

            # SQL 매퍼 파싱하여 재구성된 SQL들 추출
            reconstructed_sqls = mybatis_parser.parse_sql_mapper(root)

            if not reconstructed_sqls:
                return None

            # 재구성된 SQL들을 분석하여 관계 추출
            sql_queries = []
            join_relationships = []

            for sql_info in reconstructed_sqls:
                sql_id = sql_info.get('sql_id')
                sql_content = sql_info.get('sql_content')
                tag_name = sql_info.get('tag_name', 'select')

                if sql_content and sql_content.strip():
                    # SQL 쿼리 정보 생성
                    query_info = {
                        'tag_name': tag_name,
                        'query_id': sql_id,
                        'query_type': tag_name,
                        'sql_content': sql_content,
                        'file_path': xml_file,
                        'line_start': 1,  # DOM에서는 정확한 라인 번호 추출이 어려움
                        'line_end': 1,
                        'hash_value': HashUtils().generate_md5(sql_content)
                    }
                    sql_queries.append(query_info)

                    # JOIN 관계 분석
                    relationships = self._analyze_join_relationships(
                        sql_content, xml_file, 0
                    )
                    join_relationships.extend(relationships)

            return {
                'sql_queries': sql_queries,
                'join_relationships': join_relationships,
                'file_path': xml_file
            }

        except Exception as e:
            # DOM 파싱 실패는 일반적인 상황이므로 info 레벨로 처리하고 SAX로 fallback
            debug(f"DOM 파싱 불가, SAX로 fallback합니다: {xml_file} (사유: {e})")
            # None을 반환하여 상위 메소드가 SAX 파서로 fallback 하도록 유도
            return None

    def _is_mybatis_xml(self, root: ET.Element) -> bool:
        """MyBatis XML 파일인지 확인"""
        # 루트 태그가 mapper인지 확인
        if root.tag == 'mapper':
            return True

        # configuration 태그도 MyBatis XML로 간주 (mybatis-config.xml)
        if root.tag == 'configuration':
            return True

        # SQL 태그가 포함된 XML 파일도 MyBatis로 간주
        sql_tags = ['select', 'insert', 'update', 'delete']
        for tag in sql_tags:
            if root.find(f'.//{tag}') is not None:
                return True

        return False

    def _parse_with_regex(self, xml_file: str) -> Dict[str, Any]:
        """
        (기존) 정규식 기반으로 XML을 분석합니다.
        """
        try:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
            except ET.ParseError as e:
                return {
                    'sql_queries': [],
                    'join_relationships': [],
                    'has_error': 'Y',
                    'error_message': f"XML 파싱 오류: {str(e)}"
                }
            
            sql_queries = []
            join_relationships = []
            sql_tags = self.config.get('sql_statement_types', {}).keys()

            for element in root.iter():
                if element.tag in sql_tags:
                    query_info = self._extract_sql_query_info(element, xml_file)
                    if query_info:
                        sql_queries.append(query_info)
                        relationships = self._analyze_join_relationships(
                            query_info['sql_content'], 
                            xml_file, 
                            0
                        )
                        join_relationships.extend(relationships)
            
            self.stats['files_processed'] += 1
            self.stats['sql_queries_extracted'] += len(sql_queries)
            self.stats['join_relationships_created'] += len(join_relationships)
            
            return {
                'sql_queries': sql_queries,
                'join_relationships': join_relationships,
                'file_path': xml_file
            }
        except Exception as e:
            # 파싱 에러로 has_error='Y' 처리하고 계속 진행
            error_message = f"모든 XML 파싱 방법 실패: {xml_file} - {str(e)}"
            self.stats['errors'] += 1
            return {
                'sql_queries': [], 
                'join_relationships': [], 
                'file_path': xml_file,
                'has_error': 'Y',
                'error_message': f"모든 XML 파싱 방법 실패: {str(e)}"
            }

    def _extract_sql_query_info(self, element: ET.Element, file_path: str) -> Optional[Dict[str, Any]]:
        try:
            tag_name = element.tag
            query_id = element.get('id', '')
            if not query_id:
                # exception은 handle_error()로 exit해야 에러 인지가 가능하다
                handle_error(f"쿼리 ID가 없습니다: {file_path}")
                return None
            
            sql_content = self._extract_sql_content(element)
            if not sql_content:
                # exception은 handle_error()로 exit해야 에러 인지가 가능하다
                handle_error(f"SQL 내용이 없습니다: {query_id}")
                return None
            
            line_start, line_end = self._extract_line_numbers(element, file_path)
            hash_utils = HashUtils()
            hash_value = hash_utils.generate_md5(sql_content)
            
            return {
                'tag_name': tag_name,
                'query_id': query_id,
                'query_type': tag_name,
                'sql_content': sql_content,
                'file_path': file_path,
                'line_start': line_start,
                'line_end': line_end,
                'hash_value': hash_value
            }
        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, "SQL 쿼리 정보 추출 실패")

    def _extract_sql_content(self, element: ET.Element) -> str:
        try:
            xml_str = ET.tostring(element, encoding='unicode')
            sql_content = ' '.join(xml_str.split()).strip()
            return sql_content
        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, "SQL 내용 추출 실패")

    def _extract_line_numbers(self, element: ET.Element, file_path: str) -> tuple[Optional[int], Optional[int]]:
        try:
            file_utils = FileUtils()
            content = file_utils.read_file(file_path)
            if not content:
                return None, None
            lines = content.split('\n')
            element_text = ET.tostring(element, encoding='unicode')
            for i, line in enumerate(lines, 1):
                if element.tag in line and element.get('id', '') in line:
                    return i, i + len(element_text.split('\n')) - 1
            return None, None
        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, "라인 번호 추출 실패")

    def _analyze_join_relationships(self, sql_content: str, file_path: str, component_id: int) -> List[Dict[str, Any]]:
        """
        JOIN 관계 분석 (공통 모듈 사용 래퍼)
        
        기존 XML 파서 호출자들을 위해 메서드 시그니처를 유지하면서
        내부적으로는 공통 SQL 조인 분석 모듈을 사용합니다.

        Args:
            sql_content: SQL 내용
            file_path: 파일 경로
            component_id: SQL 컴포넌트 ID

        Returns:
            모든 JOIN 관계 리스트
        """
        try:
            # XML 파서 특화 처리 (DOM 파싱, XML 파싱 에러 체크 등)
            # 0단계: DOM 파싱 시도 (XML 파서만의 기능)
            try:
                xml_extensions = self.config.get('xml_extensions', ['.xml'])
                if file_path and os.path.exists(file_path) and any(file_path.endswith(ext) for ext in xml_extensions):
                    dom_result = self._parse_with_dom(file_path)
                    if dom_result:
                        info(f"DOM 파싱 성공: {file_path}")
                        join_relationships = dom_result.get('join_relationships', [])
                        if join_relationships:
                            info(f"DOM 기반 JOIN 관계 {len(join_relationships)}개 추출: {file_path}")
                            return join_relationships
                        else:
                            return []
            except Exception as dom_error:
                info(f"DOM 파싱 실패, 공통 분석 모듈 사용: {file_path} - {str(dom_error)}")

            # 동적 쿼리 사전 분석 (XML 파서 특화)
            dynamic_patterns = self.config.get('dynamic_sql_patterns', {})
            has_dynamic_join = self._detect_dynamic_join(sql_content, dynamic_patterns)
            if has_dynamic_join:
                debug(f"동적 JOIN 구문 감지: {file_path}")

            # XML 파싱 에러 검사 (XML 파서 특화)
            parsing_error = self._check_xml_parsing_handle_error(sql_content, file_path)
            if parsing_error:
                self._mark_parsing_handle_error(component_id, parsing_error)

            # 공통 SQL 조인 분석 모듈 사용
            join_relationships = self.sql_join_analyzer.analyze_join_relationships(
                sql_content, file_path, component_id
            )
            
            # XML 파서 특화 후처리 (INFERRED 컬럼 생성 등)
            if join_relationships:
                # INFERRED 컬럼 생성 (XML 파서만의 기능)
                all_join_conditions = self._extract_all_join_conditions(join_relationships, [])
                alias_map = {}  # 공통 모듈에서 이미 처리했으므로 빈 맵 사용
                inferred_relationships = self._find_and_create_inferred_columns(
                    all_join_conditions, alias_map, component_id
                )
                join_relationships.extend(inferred_relationships)
            
            return join_relationships

        except Exception as e:
            handle_error(e, f"JOIN 관계 분석 실패: {file_path}")
            return []

    def _normalize_sql_for_analysis(self, sql_content: str, dynamic_patterns: dict) -> str:
        try:
            normalized_sql = sql_content
            # SQL 주석 제거 - 한 줄 주석 (-- ...)
            normalized_sql = re.sub(r'--.*$', '', normalized_sql, flags=re.MULTILINE)
            # SQL 주석 제거 - 블록 주석 (/* ... */)
            normalized_sql = re.sub(r'/\*.*?\*/', '', normalized_sql, flags=re.DOTALL)
            
            dynamic_tag_patterns = dynamic_patterns.get('dynamic_tags', [])
            for pattern in dynamic_tag_patterns:
                normalized_sql = re.sub(pattern, r'\1', normalized_sql, flags=re.DOTALL | re.IGNORECASE)
            
            normalized_sql = re.sub(r'\s+', ' ', normalized_sql).strip()
            return normalized_sql.upper()
        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, "SQL 정규화 실패")
            return sql_content.upper()

    def _find_base_and_aliases(self, sql_content: str, analysis_patterns: dict) -> tuple:
        try:
            alias_map = {}
            base_table = ""
            from_patterns = analysis_patterns.get('from_clause', [])
            for pattern in from_patterns:
                matches = re.findall(pattern, sql_content, re.IGNORECASE)
                if matches:
                    match = matches[0]
                    if isinstance(match, tuple):
                        base_table = match[0].upper().strip()
                        base_alias = match[1].upper().strip() if match[1] else base_table
                        alias_map[base_alias] = base_table
                        if len(match) > 2 and match[2]:
                            second_table = match[2].upper().strip()
                            second_alias = match[3].upper().strip() if len(match) > 3 and match[3] else second_table
                            alias_map[second_alias] = second_table
                    break
            
            explicit_patterns = analysis_patterns.get('explicit_joins', [])
            for pattern in explicit_patterns:
                matches = re.findall(pattern, sql_content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        join_table = match[1].upper().strip()
                        join_alias = match[2].upper().strip() if len(match) > 2 and match[2] else join_table
                        alias_map[join_alias] = join_table
            return base_table, alias_map
        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, "테이블-별칭 매핑 생성 실패")
            return "", {}

    def _analyze_explicit_join_chain(self, sql_content: str, base_table: str, alias_map: dict, analysis_patterns: dict, join_type_mapping: dict) -> List[Dict[str, Any]]:
        try:
            relationships = []
            explicit_patterns = analysis_patterns.get('explicit_joins', [])
            previous_table = base_table
            
            for pattern in explicit_patterns:
                matches = re.findall(pattern, sql_content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        join_type_raw = match[0].upper().strip()
                        join_table = match[1].upper().strip()
                        on_condition = match[3].strip() if len(match) > 3 and match[3] else ""
                        join_type = self._get_join_type_from_pattern(join_type_raw, join_type_mapping)
                        
                        if join_type in ['CROSS_JOIN', 'NATURAL_JOIN']:
                            source_table, target_table = previous_table, join_table
                        else:
                            source_table, target_table = self._parse_on_condition_for_tables(on_condition, alias_map)

                        if source_table and target_table:
                            relationships.append({
                                'source_table': source_table,
                                'target_table': target_table,
                                'rel_type': 'JOIN_EXPLICIT',
                                'join_type': join_type,
                                'description': f"{join_type} between {source_table} and {target_table} (ON: {on_condition})"
                            })
                        previous_table = join_table
            return relationships
        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, "EXPLICIT JOIN 체인 분석 실패")
            return []

    def _analyze_implicit_joins_in_where(self, sql_content: str, alias_map: dict, analysis_patterns: dict) -> List[Dict[str, Any]]:
        try:
            relationships = []
            implicit_patterns = analysis_patterns.get('implicit_joins', [])

            # WHERE 절 추출
            where_match = re.search(r'\bWHERE\b(.*?)(?:\bGROUP\b|\bORDER\b|\bHAVING\b|$)', sql_content, re.IGNORECASE | re.DOTALL)
            if not where_match:
                return relationships
            where_clause = where_match.group(1)

            # FROM 절에서 콤마로 구분된 테이블들도 IMPLICIT JOIN으로 처리 (기존 alias_map 업데이트만)
            from_match = re.search(r'\bFROM\b([^WHERE^GROUP^ORDER^HAVING]+)', sql_content, re.IGNORECASE | re.DOTALL)
            if from_match:
                from_clause = from_match.group(1)
                # 콤마로 구분된 테이블들 찾기
                table_matches = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)', from_clause)
                for table_match in table_matches:
                    table_name = table_match[0].upper()
                    alias = table_match[1].upper()
                    alias_map[alias] = table_name

            # WHERE 절에서 조인 조건 분석
            for pattern in implicit_patterns:
                matches = re.findall(pattern, where_clause, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        if len(match) == 4: # alias1.col1 = alias2.col2
                            alias1, col1, alias2, col2 = match
                            table1 = alias_map.get(alias1.upper(), alias1.upper())
                            table2 = alias_map.get(alias2.upper(), alias2.upper())

                            # 유효한 테이블명인지 확인 (컬럼명 필터링)
                            if (table1 != table2 and table1 and table2 and
                                self._is_valid_table_name(table1) and self._is_valid_table_name(table2)):
                                join_type = "ORACLE_OUTER_JOIN" if "(+)" in str(match) else "IMPLICIT_JOIN"
                                relationships.append({
                                    'source_table': table1,
                                    'target_table': table2,
                                    'rel_type': 'JOIN_IMPLICIT',
                                    'join_type': join_type,
                                    'description': f"WHERE {alias1}.{col1} = {alias2}.{col2}"
                                })
                        elif len(match) == 2: # 단순한 경우
                            alias1, alias2 = match
                            table1 = alias_map.get(alias1.upper(), alias1.upper())
                            table2 = alias_map.get(alias2.upper(), alias2.upper())

                            # 유효한 테이블명인지 확인 (컬럼명 필터링)
                            if (table1 != table2 and table1 and table2 and
                                self._is_valid_table_name(table1) and self._is_valid_table_name(table2)):
                                relationships.append({
                                    'source_table': table1,
                                    'target_table': table2,
                                    'rel_type': 'JOIN_IMPLICIT',
                                    'join_type': 'IMPLICIT_JOIN',
                                    'description': f"Implicit JOIN: {table1} = {table2}"
                                })

            return relationships
        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, "IMPLICIT JOIN 분석 실패")
            return []

    def _get_join_type_from_pattern(self, join_type_raw: str, join_type_mapping: dict) -> str:
        try:
            for pattern, mapped_type in join_type_mapping.items():
                if re.match(pattern, join_type_raw, re.IGNORECASE):
                    return mapped_type
            return "UNKNOWN_JOIN"
        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, "JOIN 타입 매핑 실패")
            return "UNKNOWN_JOIN"

    def _parse_on_condition_for_tables(self, on_condition: str, alias_map: dict) -> tuple:
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
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, "ON 조건절 테이블 추출 실패")
            return None, None

    def _remove_duplicate_relationships(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        try:
            unique_relationships = []
            seen = set()
            for rel in relationships:
                key = tuple(sorted((rel['source_table'], rel['target_table'])))
                if key not in seen:
                    seen.add(key)
                    unique_relationships.append(rel)
            return unique_relationships
        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, "중복 관계 제거 실패")

    def _post_process_relationships(self, relationships: List[Dict], alias_map: dict) -> List[Dict]:
        try:
            processed_relationships = []
            for rel in relationships:
                if 'source_table' in rel:
                    rel['source_table'] = rel['source_table'].upper()
                if 'target_table' in rel:
                    rel['target_table'] = rel['target_table'].upper()
                if self._is_valid_relationship(rel):
                    processed_relationships.append(rel)
            return processed_relationships
        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, "관계 후처리 실패")
            return relationships

    def _is_valid_relationship(self, relationship: Dict) -> bool:
        try:
            required_fields = ['source_table', 'target_table', 'rel_type']
            for field in required_fields:
                if field not in relationship or not relationship[field]:
                    return False
            if relationship['source_table'] == relationship['target_table']:
                return False
            return True
        except Exception as e:
            # exception은 handle_error()로 exit해야 에러 인지가 가능하다
            handle_error(e, "관계 유효성 검증 실패")
            return False

    def _detect_dynamic_join(self, sql_content: str, dynamic_patterns: dict) -> bool:
        """
        동적 쿼리에서 JOIN이 포함된 동적 태그 감지 (통합개발계획서 0단계)

        Args:
            sql_content: SQL 내용
            dynamic_patterns: 동적 SQL 패턴 설정

        Returns:
            동적 JOIN 감지 여부
        """
        try:
            # 동적 JOIN 감지 패턴들
            dynamic_join_patterns = dynamic_patterns.get('dynamic_join_detection', [])

            for pattern in dynamic_join_patterns:
                if re.search(pattern, sql_content, re.IGNORECASE | re.DOTALL):
                    debug(f"동적 JOIN 패턴 감지: {pattern}")
                    return True

            # MyBatis 동적 태그 내부의 JOIN 키워드 검사
            mybatis_tags = ['if', 'choose', 'when', 'otherwise', 'foreach', 'where']
            for tag in mybatis_tags:
                pattern = f'<{tag}[^>]*>.*?(?:LEFT|RIGHT|FULL|INNER|CROSS|NATURAL)\\s+JOIN.*?</{tag}>'
                if re.search(pattern, sql_content, re.IGNORECASE | re.DOTALL):
                    debug(f"MyBatis {tag} 태그 내 JOIN 감지")
                    return True

            return False

        except Exception as e:
            # USER RULES: Exception 발생시 handle_error()로 exit()
            handle_error(e, "동적 JOIN 감지 실패")
            return False

    def _check_xml_parsing_handle_error(self, sql_content: str, file_path: str) -> str:
        """
        XML 파싱 에러 검사 (사용자 소스 수정 필요 케이스) - 통합개발계획서 0.1단계

        Args:
            sql_content: SQL 내용
            file_path: 파일 경로

        Returns:
            파싱 에러 메시지 (에러가 없으면 None)
        """
        try:
            # XML 파싱 에러 패턴 검사
            error_patterns = [
                r'not well-formed.*line (\d+), column (\d+)',
                r'invalid token.*line (\d+), column (\d+)',
                r'unexpected end of file',
                r'mismatched tag',
                r'attribute.*not properly quoted',
                r'<![^>]*>.*?[^>]$',  # 잘못된 CDATA 섹션
                r'&(?!amp;|lt;|gt;|quot;|apos;)[^;]*;'  # 잘못된 엔티티 참조
            ]

            for pattern in error_patterns:
                match = re.search(pattern, sql_content, re.IGNORECASE)
                if match:
                    return f"XML 파싱 에러: {match.group(0)}"

            # XML 태그 불일치 검사
            open_tags = re.findall(r'<([^/!?][^>]*)>', sql_content)
            close_tags = re.findall(r'</([^>]+)>', sql_content)

            if len(open_tags) != len(close_tags):
                return f"XML 태그 불일치: 열림태그 {len(open_tags)}개, 닫힘태그 {len(close_tags)}개"

            return None

        except Exception as e:
            # 파싱 에러로 has_error='Y' 처리하고 계속 진행
            return None

    def _mark_parsing_handle_error(self, component_id: int, error_message: str) -> None:
        """
        파싱 에러를 컴포넌트에 표시 (USER RULES: has_error='Y', error_message 남기고 계속 진행)

        Args:
            component_id: 컴포넌트 ID
            error_message: 에러 메시지
        """
        try:
            # USER RULES: 공통함수 사용 지향
            from util import DatabaseUtils, PathUtils
            path_utils = PathUtils()

            # USER RULES: 하드코딩 지양 - PathUtils로 DB 경로 획득
            if not self.project_name:
                handle_error("프로젝트명이 설정되지 않아 에러 표시를 건너뜁니다")
                return

            try:
                db_path = path_utils.get_metadata_db_path(self.project_name)
                db_utils = DatabaseUtils(db_path)

                update_data = {
                    'has_error': 'Y',
                    'error_message': error_message
                    # updated_at은 DEFAULT 값 사용
                }

                db_utils.update_record('components', update_data, {'component_id': component_id})

            except Exception as e:
                # 테스트 환경에서는 로그만 출력
                handle_error(f"데이터베이스 접근 실패: {str(e)}")
                print(f"파싱 에러 표시 (테스트): component_id={component_id}, error={error_message}")

        except Exception as e:
            # USER RULES: 에러 표시는 치명적이지 않으므로 warning만 출력
            handle_error(f"에러 표시 실패: {str(e)}")

    def _extract_all_join_conditions(self, explicit_relationships: List[Dict], implicit_relationships: List[Dict]) -> List[str]:
        """
        EXPLICIT과 IMPLICIT JOIN에서 모든 조건절 추출 (통합개발계획서 5단계)

        Args:
            explicit_relationships: EXPLICIT JOIN 관계 리스트
            implicit_relationships: IMPLICIT JOIN 관계 리스트

        Returns:
            모든 JOIN 조건절 리스트
        """
        try:
            join_conditions = []

            # EXPLICIT JOIN 조건절 추출
            for rel in explicit_relationships:
                if 'description' in rel and 'ON:' in rel['description']:
                    on_condition = rel['description'].split('ON:')[-1].strip().rstrip(')')
                    if on_condition:
                        join_conditions.append(on_condition)

            # IMPLICIT JOIN 조건절 추출
            for rel in implicit_relationships:
                if 'description' in rel and 'WHERE' in rel['description']:
                    where_condition = rel['description'].replace('WHERE ', '').strip()
                    if where_condition:
                        join_conditions.append(where_condition)

            return join_conditions

        except Exception as e:
            # USER RULES: Exception 발생시 handle_error()로 exit()
            handle_error(e, "JOIN 조건절 추출 실패")
            return []

    def _find_and_create_inferred_columns(self, join_conditions: List[str], alias_map: dict, component_id: int) -> List[Dict[str, Any]]:
        """
        JOIN 조건에서 존재하지 않는 컬럼을 찾아 inferred 컬럼 생성 (통합개발계획서 5단계)

        Args:
            join_conditions: JOIN 조건절 리스트
            alias_map: 테이블 별칭 매핑
            component_id: SQL 컴포넌트 ID

        Returns:
            inferred 관계 리스트
        """
        try:
            inferred_relationships = []

            for condition in join_conditions:
                # 조건절에서 table.column = table.column 패턴 추출
                column_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)'
                matches = re.findall(column_pattern, condition, re.IGNORECASE)

                for match in matches:
                    alias1, col1, alias2, col2 = match
                    
                    # USER RULES: 테이블 별칭 필터링 - 단일 문자 별칭은 실제 테이블명으로 인식하지 않음
                    table1 = self._resolve_table_alias(alias1.upper(), alias_map)
                    table2 = self._resolve_table_alias(alias2.upper(), alias_map)
                    
                    # 유효한 테이블명인지 검증
                    if not self._is_valid_table_name(table1) or not self._is_valid_table_name(table2):
                        debug(f"유효하지 않은 테이블명 건너뜀: {table1}, {table2}")
                        continue

                    if table1 != table2:
                        # 존재하지 않는 컬럼 검사 및 생성 - 프로젝트 ID 전역 관리
                        if self._should_create_inferred_column(table1, col1):
                            self._create_inferred_column(table1, col1, component_id)

                        if self._should_create_inferred_column(table2, col2):
                            self._create_inferred_column(table2, col2, component_id)

                        # inferred 관계 추가
                        inferred_relationships.append({
                            'source_table': table1,
                            'target_table': table2,
                            'rel_type': 'JOIN_INFERRED',
                            'join_type': 'INFERRED_JOIN',
                            'description': f"Inferred JOIN: {table1}.{col1} = {table2}.{col2}"
                        })

            return inferred_relationships

        except Exception as e:
            # USER RULES: Exception 발생시 handle_error()로 exit()
            handle_error(e, "Inferred Column 분석 실패")
            return []

    def _is_valid_table_name(self, table_name: str) -> bool:
        """
        테이블명 유효성 검증 (별칭 및 컬럼명 오탐 방지)
        실제 데이터베이스 스키마를 참조하여 검증

        Args:
            table_name: 검증할 테이블명

        Returns:
            유효한 테이블명이면 True, 아니면 False
        """
        try:
            if not table_name:
                return False

            # 단일 문자 또는 2글자 이하 필터링 (별칭 가능성 높음)
            if len(table_name) <= 2:
                return False

            # 대문자로만 구성된 경우 (별칭 가능성 높음)
            if table_name.isupper() and len(table_name) <= 3:
                return False

            # 실제 테이블명 패턴 검증 (대문자, 언더스코어 포함)
            if not re.match(r'^[A-Z][A-Z0-9_]*$', table_name):
                return False

            # 예약어 체크 (자주 사용되는 단일 문자 별칭)
            reserved_words = {'B', 'C', 'O', 'P', 'R', 'T', 'U', 'V', 'X', 'Y', 'Z'}
            if table_name in reserved_words:
                return False

            # 실제 데이터베이스에 존재하는 테이블인지 확인
            if self._is_existing_table(table_name):
                return True

            # 실제 데이터베이스에 존재하는 컬럼명인지 확인
            if self._is_existing_column(table_name):
                return False

            # 기본적인 컬럼명 패턴 확인 (_ID로 끝나는 경우)
            if table_name.endswith('_ID'):
                return False

            # 단독 ID 패턴
            if table_name == 'ID':
                return False

            # 그 외의 경우는 유효한 테이블명으로 간주
            return True

        except Exception as e:
            handle_error(e, f"테이블명 유효성 검증 실패: {table_name}")

    def _is_existing_table(self, table_name: str) -> bool:
        """
        실제 데이터베이스에 존재하는 테이블인지 확인

        Args:
            table_name: 확인할 테이블명

        Returns:
            존재하면 True, 아니면 False
        """
        try:
            from util.database_utils import get_database_manager

            db_manager = get_database_manager()
            query = """
                SELECT COUNT(*) FROM components c
                JOIN tables t ON c.component_id = t.component_id
                WHERE c.component_type = 'TABLE'
                AND UPPER(c.component_name) = UPPER(?)
                AND c.del_yn = 'N' AND t.del_yn = 'N'
            """

            result = db_manager.execute_query(query, (table_name,))
            return result and len(result) > 0 and result[0][0] > 0

        except Exception:
            # 에러 발생시 False 반환 (보수적 접근)
            return False

    def _is_existing_column(self, column_name: str) -> bool:
        """
        실제 데이터베이스에 존재하는 컬럼명인지 확인

        Args:
            column_name: 확인할 컬럼명

        Returns:
            존재하면 True, 아니면 False
        """
        try:
            from util.database_utils import get_database_manager

            db_manager = get_database_manager()
            query = """
                SELECT COUNT(*) FROM components c
                JOIN columns col ON c.component_id = col.component_id
                WHERE c.component_type = 'COLUMN'
                AND UPPER(c.component_name) = UPPER(?)
                AND c.del_yn = 'N' AND col.del_yn = 'N'
            """

            result = db_manager.execute_query(query, (column_name,))
            return result and len(result) > 0 and result[0][0] > 0

        except Exception:
            # 에러 발생시 False 반환 (보수적 접근)
            return False

    def _resolve_table_alias(self, alias: str, alias_map: dict) -> str:
        """
        테이블 별칭을 실제 테이블명으로 변환
        
        Args:
            alias: 테이블 별칭
            alias_map: 별칭-테이블명 매핑
            
        Returns:
            실제 테이블명 또는 None (유효하지 않은 경우)
        """
        try:
            # 별칭 매핑에서 실제 테이블명 찾기
            actual_table = alias_map.get(alias)
            if actual_table:
                return actual_table
            
            # 별칭이 매핑에 없으면 유효성 검증 후 반환
            if self._is_valid_table_name(alias):
                return alias
            
            # 유효하지 않은 별칭은 None 반환
            return None
            
        except Exception as e:
            handle_error(e, f"테이블 별칭 변환 실패: {alias}")

    def _should_create_inferred_column(self, table_name: str, column_name: str) -> bool:
        """
        inferred 컬럼 생성이 필요한지 검사

        Args:
            table_name: 테이블명
            column_name: 컬럼명

        Returns:
            생성 필요 여부
        """
        try:
            # USER RULES: 공통함수 사용 지향
            from util import DatabaseUtils, PathUtils
            path_utils = PathUtils()

            # USER RULES: 하드코딩 지양 - PathUtils로 DB 경로 획득
            if not self.project_name:
                # USER RULES: Exception 발생시 handle_error()로 exit()
                handle_error(Exception("프로젝트명이 설정되지 않았습니다"), "Inferred 컬럼 검사 실패")

            try:
                db_path = path_utils.get_metadata_db_path(self.project_name)
                db_utils = DatabaseUtils(db_path)

                # 이미 존재하는 컬럼인지 검사 - project_id도 고려
                project_id = self._get_project_id()
                query = """
                    SELECT COUNT(*) as cnt
                    FROM columns c
                    JOIN tables t ON c.table_id = t.table_id
                    WHERE UPPER(t.table_name) = ? AND UPPER(c.column_name) = ? AND t.project_id = ?
                """
                result = db_utils.execute_query(query, (table_name.upper(), column_name.upper(), project_id))

                return result[0]['cnt'] == 0 if result else True

            except Exception as e:
                # 테스트 환경에서는 항상 생성 필요로 반환
                handle_error(f"데이터베이스 접근 실패: {str(e)}")
                return True

        except Exception as e:
            # USER RULES: Exception 발생시 handle_error()로 exit()
            handle_error(e, "Inferred 컬럼 검사 실패")
            return True

    def _create_inferred_column(self, table_name: str, column_name: str, component_id: int) -> None:
        """
        inferred 컬럼 생성

        Args:
            table_name: 테이블명
            column_name: 컬럼명
            component_id: SQL 컴포넌트 ID
        """
        try:
            # USER RULES: 공통함수 사용 지향
            from util import DatabaseUtils, PathUtils
            path_utils = PathUtils()

            # USER RULES: 하드코딩 지양 - PathUtils로 DB 경로 획득
            if not self.project_name:
                # USER RULES: Exception 발생시 handle_error()로 exit()
                handle_error(Exception("프로젝트명이 설정되지 않았습니다"), "Inferred 컬럼 생성 실패")

            try:
                db_path = path_utils.get_metadata_db_path(self.project_name)
                db_utils = DatabaseUtils(db_path)

                # 프로젝트 ID 전역 관리
                project_id = self._get_project_id()

                # 테이블 ID 획득 (없으면 생성)
                table_id = self._get_or_create_inferred_table(table_name)

                # inferred 컬럼 데이터 (project_id는 columns 테이블에 없음)
                column_data = {
                    'table_id': table_id,
                    'column_name': column_name.upper(),
                    'data_type': 'UNKNOWN',
                    'nullable': 'Y',
                    'column_comments': 'Inferred from SQL JOIN analysis',
                    'owner': 'UNKNOWN',  # inferred 컬럼은 owner를 UNKNOWN으로 설정
                    'hash_value': 'INFERRED',
                    'del_yn': 'N'
                    # created_at은 DEFAULT 값 사용
                }

                column_id = db_utils.insert_or_replace('columns', column_data)

                # components 테이블에도 추가 - project_id와 file_id 추가
                current_file_id = getattr(self, 'current_file_id', None)
                if current_file_id is not None:  # file_id가 유효할 때만 생성
                    component_data = {
                        'project_id': project_id,
                        'file_id': current_file_id,  # 현재 파일의 file_id 사용
                        'component_type': 'COLUMN',
                        'component_name': column_name.upper(),
                        'parent_id': self._get_table_component_id(table_id),
                        'layer': 'DB',  # COLUMN 컴포넌트는 DB 레이어
                        'hash_value': 'INFERRED',
                        'del_yn': 'N'
                        # created_at은 DEFAULT 값 사용
                    }

                    db_utils.insert_or_replace('components', component_data)
                else:
                    handle_error(f"file_id가 None이어서 inferred 컬럼 컴포넌트 생성을 건너뜀: {column_name}")

            except Exception as e:
                # 테스트 환경에서는 로그만 출력
                handle_error(f"데이터베이스 접근 실패: {str(e)}")
                print(f"Inferred 컬럼 생성 (테스트): {table_name}.{column_name}")

        except Exception as e:
            # USER RULES: Exception 발생시 handle_error()로 exit()
            handle_error(e, "Inferred 컬럼 생성 실패")

    def _get_or_create_inferred_table(self, table_name: str) -> int:
        """
        inferred 테이블 획득 또는 생성

        Args:
            table_name: 테이블명

        Returns:
            테이블 ID
        """
        try:
            # USER RULES: 공통함수 사용 지향
            from util import DatabaseUtils, PathUtils
            path_utils = PathUtils()

            # USER RULES: 하드코딩 지양 - PathUtils로 DB 경로 획득
            if not self.project_name:
                # USER RULES: Exception 발생시 handle_error()로 exit()
                handle_error(Exception("프로젝트명이 설정되지 않았습니다"), "Inferred 테이블 생성 실패")

            try:
                db_path = path_utils.get_metadata_db_path(self.project_name)
                db_utils = DatabaseUtils(db_path)

                # 프로젝트 ID 전역 관리
                project_id = self._get_project_id()

                # 기존 테이블 확인
                query = "SELECT table_id FROM tables WHERE table_name = ? AND project_id = ?"
                result = db_utils.execute_query(query, (table_name, project_id))

                if result:
                    return result[0]['table_id']

                # 새 테이블 생성 (inferred)
                table_data = {
                    'project_id': project_id,
                    'table_name': table_name,
                    'table_owner': 'UNKNOWN',  # inferred 테이블은 owner를 UNKNOWN으로 설정
                    'table_comments': 'Inferred from SQL analysis',
                    'hash_value': 'INFERRED',
                    'del_yn': 'N'
                    # created_at은 DEFAULT 값 사용
                }

                table_id = db_utils.insert_or_replace('tables', table_data)

                # components 테이블에도 추가
                current_file_id = getattr(self, 'current_file_id', None)
                if current_file_id is not None:  # file_id가 유효할 때만 생성
                    component_data = {
                        'project_id': project_id,
                        'file_id': current_file_id,  # 현재 파일의 file_id 사용
                        'component_type': 'TABLE',
                        'component_name': table_name,
                        'parent_id': None,
                        'layer': 'TABLE',  # TABLE 컴포넌트는 TABLE 레이어
                        'hash_value': 'INFERRED',
                        'del_yn': 'N'
                        # created_at은 DEFAULT 값 사용
                    }

                    component_id = db_utils.insert_or_replace('components', component_data)
                    db_utils.update_record('tables', {'component_id': component_id}, {'table_id': table_id})
                else:
                    handle_error(f"file_id가 None이어서 inferred 테이블 컴포넌트 생성을 건너뜀: {table_name}")

                return table_id

            except Exception as e:
                # 테스트 환경에서는 임시 ID 반환
                handle_error(f"데이터베이스 접근 실패: {str(e)}")
                return 9999

        except Exception as e:
            # USER RULES: Exception 발생시 handle_error()로 exit()
            handle_error(e, "Inferred 테이블 생성 실패")
            return 9999

    def _get_table_component_id(self, table_id: int) -> int:
        """테이블의 컴포넌트 ID 반환"""
        try:
            from util import DatabaseUtils
            from util.path_utils import PathUtils
            # USER RULES: DatabaseUtils는 db_path가 필요하므로 공통 함수 사용
            try:
                path_utils = PathUtils()
                # 현재 처리 중인 프로젝트의 메타데이터베이스 경로 동적 생성
                if hasattr(self, 'project_name') and self.project_name:
                    db_path = path_utils.get_project_metadata_db_path(self.project_name)
                else:
                    # 프로젝트명을 알 수 없는 경우 에러 처리 (하드코딩 금지)
                    from util.logger import handle_error
                    handle_error(Exception("프로젝트명을 알 수 없어 테이블 컴포넌트 ID를 조회할 수 없습니다"), "XML 파서에서 프로젝트명 누락")
                db_utils = DatabaseUtils(db_path)
            except:
                # 테스트 환경에서는 임시 ID 반환
                return 9998

            query = "SELECT component_id FROM tables WHERE table_id = ?"
            result = db_utils.execute_query(query, (table_id,))

            return result[0]['component_id'] if result else 9998

        except Exception as e:
            # 테스트 환경에서는 임시 ID 반환
            return 9998

    def get_statistics(self) -> Dict[str, Any]:
        return self.stats.copy()

    def reset_statistics(self):
        self.stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'sql_queries_extracted': 0,
            'join_relationships_created': 0,
            'errors': 0
        }



class MybatisParser:
    """MyBatis DOM 파서 - 동적 SQL 태그를 시뮬레이션하여 실행 가능한 SQL로 재구성"""

    def __init__(self, dom_rules: Dict[str, Any]):
        """
        MyBatis DOM 파서 초기화

        Args:
            dom_rules: mybatis_dom_rules.yaml에서 로드한 설정
        """
        self.intelligent_tags = dom_rules.get('intelligent_tags', {})
        self.sample_data = dom_rules.get('sample_data', {}).get('default', {})
        self.bind_context = {}
        self.max_depth = 0  # 최대 recursion depth 추적
        self.current_depth = 0  # 현재 recursion depth

    def _log_recursion_depth(self, method_name: str):
        """recursion depth를 로그로 출력하고 10회 제한"""
        self.current_depth += 1
        if self.current_depth > self.max_depth:
            self.max_depth = self.current_depth
        
        # 10회 초과시 에러 발생
        if self.current_depth > 10:
            raise RecursionError(f"Recursion depth exceeded limit (10) in {method_name}")
        
        # 5회 이상이면 경고
        if self.current_depth > 5:
            handle_error(f"High recursion depth warning: {self.current_depth} in {method_name}")

    def _decrease_recursion_depth(self):
        """recursion depth 감소"""
        self.current_depth -= 1


    def parse_sql_mapper(self, xml_root: ET.Element) -> List[Dict[str, str]]:
        """
        매퍼 파싱의 시작점. 컨텍스트를 초기화하고 각 SQL 문을 파싱

        Args:
            xml_root: XML 루트 엘리먼트

        Returns:
            재구성된 SQL 정보 리스트 [{'sql_id': '', 'sql_content': '', 'tag_name': ''}]
        """
        self.bind_context = {}  # 컨텍스트 초기화
        reconstructed_sqls = []

        # 각 SQL 문(select, insert, update, delete) 처리
        sql_tags = ['select', 'insert', 'update', 'delete']

        for tag_name in sql_tags:
            for statement_node in xml_root.findall(f'.//{tag_name}'):
                statement_id = statement_node.get('id')
                if statement_id:
                    # 각 구문은 독립적인 컨텍스트를 가짐
                    context = self.bind_context.copy()
                    reconstructed_sql = self._process_node(statement_node, context)

                    if reconstructed_sql and reconstructed_sql.strip():
                        reconstructed_sqls.append({
                            'sql_id': statement_id,
                            'sql_content': reconstructed_sql,
                            'tag_name': tag_name
                        })

        return reconstructed_sqls

    def _process_node(self, node: ET.Element, context: Dict[str, str]) -> str:
        """
        DOM 노드를 태그 종류에 따라 분기하여 처리

        Args:
            node: 처리할 XML 노드
            context: bind 변수 컨텍스트

        Returns:
            처리된 SQL 조각
        """
        # recursion depth 추적
        self._log_recursion_depth("_process_node")
        
        try:
            tag_name = node.tag.lower()

            if tag_name == 'bind':
                self._process_bind_tag(node, context)
                return ""  # bind 태그 자체는 SQL을 생성하지 않음

            elif tag_name in self.intelligent_tags or tag_name == 'trim':
                return self._simulate_intelligent_tag(node, context)

            elif tag_name == 'foreach':
                return self._reconstruct_foreach_tag(node, context)

            elif tag_name == 'if':
                return self._process_if_tag(node, context)

            elif tag_name == 'choose':
                return self._process_choose_tag(node, context)

            else:
                # 일반 텍스트 노드는 컨텍스트 변수 치환 후 반환
                node_text = self._get_full_text_content(node)
                result = self._replace_context_vars(node_text, context)
                return result
        
        finally:
            # recursion depth 감소
            self._decrease_recursion_depth()

    def _process_bind_tag(self, node: ET.Element, context: Dict[str, str]):
        """
        <bind> 태그를 처리하여 컨텍스트에 변수를 저장

        Args:
            node: bind 태그 노드
            context: bind 변수 컨텍스트
        """
        name = node.get('name')
        # value는 OGNL 표현식이므로, 분석을 위해 대표적인 결과값으로 치환
        value_placeholder = "'%sample_pattern%'"

        if name:
            context[name] = value_placeholder

    def _simulate_intelligent_tag(self, node: ET.Element, context: Dict[str, str]) -> str:
        """
        <trim>, <where>, <set> 태그의 동작을 시뮬레이션

        Args:
            node: 처리할 태그 노드
            context: bind 변수 컨텍스트

        Returns:
            처리된 SQL 조각
        """
        # recursion depth 추적
        self._log_recursion_depth("_simulate_intelligent_tag")
        
        try:
            tag_name = node.tag.lower()

            # 자식 노드들의 SQL 조각을 재귀적으로 처리하여 조합 (10회 제한)
            child_sql_parts = [self._process_node(child, context) for child in node]
            content = "".join(child_sql_parts).strip()

            if not content:
                return ""

            # 규칙 적용: <trim>은 속성에서, <where>/<set>은 설정 파일에서 가져옴
            rules = self.intelligent_tags.get(tag_name, {})
            prefix = node.get('prefix', rules.get('prefix', ''))
            suffix = node.get('suffix', rules.get('suffix', ''))

            prefix_overrides_str = node.get('prefixOverrides', '')
            suffix_overrides_str = node.get('suffixOverrides', '')

            # 설정 파일의 기본값과 노드 속성을 결합
            prefix_overrides = rules.get('prefix_overrides', [])
            suffix_overrides = rules.get('suffix_overrides', [])

            if prefix_overrides_str:
                prefix_overrides.extend(prefix_overrides_str.split('|'))
            if suffix_overrides_str:
                suffix_overrides.extend(suffix_overrides_str.split('|'))

            # 불필요한 접두사/접미사 제거
            for override in prefix_overrides:
                if override and content.upper().startswith(override.strip().upper()):
                    content = content[len(override):].strip()
                    break

            for override in suffix_overrides:
                if override and content.upper().endswith(override.strip().upper()):
                    content = content[:-len(override)].strip()
                    break

            # 최종 SQL 조각에 접두사/접미사 추가
            if content:
                result = f" {prefix} {content} {suffix} ".strip()
                return f" {result} " if result else ""
            return ""
        
        finally:
            # recursion depth 감소
            self._decrease_recursion_depth()

    def _reconstruct_foreach_tag(self, node: ET.Element, context: Dict[str, str]) -> str:
        """
        <foreach> 태그를 샘플 데이터 기반의 SQL로 재구성

        Args:
            node: foreach 태그 노드
            context: bind 변수 컨텍스트

        Returns:
            재구성된 SQL 조각
        """
        open_str = node.get('open', '')
        close_str = node.get('close', '')
        separator = node.get('separator', ', ')
        item_variable = node.get('item')

        if not item_variable:
            return ""

        # 내부 템플릿 추출
        template = self._get_full_text_content(node)

        if not template:
            return ""

        # 샘플 항목으로 재구성
        sample_values = self.sample_data.get('string', ["'sample_val_1'", "'sample_val_2'"])

        # #{item} 또는 #{item.property} 형태 모두 대응
        reconstructed_items = []
        for sample_val in sample_values:
            # #{item}을 샘플값으로 치환
            item_sql = template.replace(f"#{{{item_variable}}}", sample_val)
            # #{item.xxx} 패턴도 치환
            item_sql = re.sub(fr'#\{{{item_variable}\.[\w]+\}}', sample_val, item_sql)

            if item_sql.strip():
                reconstructed_items.append(item_sql.strip())

        if reconstructed_items:
            content = separator.join(reconstructed_items)
            result = f" {open_str}{content}{close_str} "
            return result

        return ""

    def _process_if_tag(self, node: ET.Element, context: Dict[str, str]) -> str:
        """
        <if> 태그 처리 - 조건을 true로 가정하고 내용 포함

        Args:
            node: if 태그 노드
            context: bind 변수 컨텍스트

        Returns:
            처리된 SQL 조각
        """
        # if 조건은 항상 true로 가정
        child_sql_parts = [self._process_node(child, context) for child in node]
        node_text = node.text or ""
        tail_text = node.tail or ""

        content = node_text + "".join(child_sql_parts) + tail_text
        return self._replace_context_vars(content, context)

    def _process_choose_tag(self, node: ET.Element, context: Dict[str, str]) -> str:
        """
        <choose><when><otherwise> 태그 처리 - 첫 번째 when 선택

        Args:
            node: choose 태그 노드
            context: bind 변수 컨텍스트

        Returns:
            처리된 SQL 조각
        """
        # 첫 번째 when 요소 선택
        when_elements = node.findall('.//when')
        if when_elements:
            return self._process_node(when_elements[0], context)

        # when이 없으면 otherwise 선택
        otherwise_elements = node.findall('.//otherwise')
        if otherwise_elements:
            return self._process_node(otherwise_elements[0], context)

        return ""

    def _replace_context_vars(self, text: str, context: Dict[str, str]) -> str:
        """
        주어진 텍스트에서 컨텍스트 변수들을 치환

        Args:
            text: 원본 텍스트
            context: bind 변수 컨텍스트

        Returns:
            변수가 치환된 텍스트
        """
        if not text:
            return ""

        result = text
        for name, value in context.items():
            result = result.replace(f"#{{{name}}}", value)

        return result

    def _get_full_text_content(self, element: ET.Element) -> str:
        """
        엘리먼트의 모든 텍스트 내용을 재귀적으로 추출 (태그 제외)

        Args:
            element: XML 엘리먼트

        Returns:
            텍스트 내용
        """
        # recursion depth 추적
        self._log_recursion_depth("_get_full_text_content")
        
        try:
            text_parts = []

            # 현재 엘리먼트의 텍스트
            if element.text:
                text_parts.append(element.text)

            # 자식 엘리먼트들의 텍스트 재귀적으로 추출 (10회 제한)
            for child in element:
                child_text = self._get_full_text_content(child)
                if child_text.strip():
                    text_parts.append(child_text)

            # 자식 엘리먼트 뒤의 텍스트
            if child.tail:
                text_parts.append(child.tail)

            return ' '.join(text_parts)
        
        finally:
            # recursion depth 감소
            self._decrease_recursion_depth()