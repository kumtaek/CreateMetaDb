"""
RelationshipBuilder - Parser-Builder 패턴 구현
- 모든 파서의 결과를 종합하여 최종 연관관계 설정
- 단서 수집 → 관계 설정 분리
- relationships 테이블 완성이 목표
"""

from typing import List, Dict, Any, Set, Optional
from util import (
    DatabaseUtils, PathUtils, app_logger, info, error, debug, warning, handle_error
)
from util.oracle_keyword_manager import get_oracle_keyword_manager
from util.simple_relationship_analyzer import SimpleRelationshipAnalyzer
from util.java_query_analyzer import JavaQueryAnalyzer
from util.frontend_api_analyzer import FrontendApiAnalyzer


class RelationshipBuilder:
    """연관관계 빌더 - 모든 파서 결과를 종합하여 최종 관계 설정"""

    def __init__(self, project_name: str, project_id: int):
        """
        RelationshipBuilder 초기화

        Args:
            project_name: 프로젝트명
            project_id: 프로젝트 ID
        """
        self.project_name = project_name
        self.project_id = project_id

        # 공통 유틸리티 초기화
        self.path_utils = PathUtils()
        self.db_path = self.path_utils.get_metadata_db_path(project_name)
        self.db_utils = DatabaseUtils(self.db_path)
        self.sql_analyzer = SimpleRelationshipAnalyzer()
        self.java_analyzer = JavaQueryAnalyzer()
        self.frontend_analyzer = FrontendApiAnalyzer()

        # Oracle 키워드 매니저 초기화 (싱글톤)
        self.oracle_keyword_manager = get_oracle_keyword_manager()

        # 수집된 단서들
        self.collected_data = {
            'xml_queries': [],        # XML에서 추출한 쿼리 정보
            'java_methods': [],       # Java에서 추출한 메서드 정보
            'jpa_entities': [],       # JPA Entity 정보
            'api_calls': [],          # 프론트엔드 API 호출
            'api_implementations': [], # Controller API 구현
            'frontend_files': [],     # 프론트엔드 파일 정보
            'controller_apis': []     # Spring Controller API 정보
        }

        # 통계
        self.stats = {
            'method_query_relationships': 0,
            'query_table_relationships': 0,
            'table_join_relationships': 0,
            'entity_table_relationships': 0,
            'frontend_api_relationships': 0,
            'api_method_relationships': 0,
            'total_relationships': 0
        }

    def add_xml_analysis_result(self, xml_result: Dict[str, Any]) -> None:
        """XML 분석 결과 추가"""
        try:
            if not xml_result or xml_result.get('has_error') == 'Y':
                debug(f"XML 분석 결과 스킵 (에러): {xml_result.get('file_path', 'unknown')}")
                return

            sql_queries = xml_result.get('sql_queries', [])
            for query in sql_queries:
                self.collected_data['xml_queries'].append({
                    'file_path': xml_result.get('file_path'),
                    'query_id': query.get('query_id'),
                    'sql_content': query.get('sql_content'),
                    'query_type': query.get('query_type'),
                    'namespace': self._extract_namespace_from_xml(xml_result.get('file_path', ''))
                })

            info(f"XML 분석 결과 추가: {len(sql_queries)}개 쿼리")

        except Exception as e:
            handle_error(e, f"XML 분석 결과 추가 실패: {xml_result}")

    def add_java_analysis_result(self, java_result: Dict[str, Any]) -> None:
        """Java 분석 결과 추가"""
        try:
            if not java_result or java_result.get('error'):
                debug(f"Java 분석 결과 스킵 (에러): {java_result.get('file_path', 'unknown')}")
                return

            file_type = java_result.get('file_type')

            if file_type == 'MYBATIS_MAPPER':
                self._add_mybatis_mapper_result(java_result)
            elif file_type == 'JPA_REPOSITORY':
                self._add_jpa_repository_result(java_result)
            elif file_type == 'JPA_ENTITY':
                self._add_jpa_entity_result(java_result)

            info(f"Java 분석 결과 추가: {file_type}, {java_result.get('file_path')}")

        except Exception as e:
            handle_error(e, f"Java 분석 결과 추가 실패: {java_result}")

    def build_all_relationships(self) -> Dict[str, int]:
        """모든 연관관계 구축"""
        try:
            info("연관관계 구축 시작")

            # 1. MyBatis METHOD → QUERY 관계
            self._build_mybatis_method_query_relationships()

            # 2. JPA METHOD → ENTITY/TABLE 관계
            self._build_jpa_method_entity_relationships()

            # 3. QUERY → TABLE 관계
            self._build_query_table_relationships()

            # 4. TABLE JOIN 관계
            self._build_table_join_relationships()

            # 5. JPA ENTITY → TABLE 관계
            self._build_entity_table_relationships()

            # 6. 프론트엔드 → API → METHOD 관계
            self._build_frontend_api_relationships()

            # 통계 계산
            self.stats['total_relationships'] = sum([
                self.stats['method_query_relationships'],
                self.stats['query_table_relationships'],
                self.stats['table_join_relationships'],
                self.stats['entity_table_relationships'],
                self.stats['frontend_api_relationships'],
                self.stats['api_method_relationships']
            ])

            info(f"연관관계 구축 완료: 총 {self.stats['total_relationships']}개 관계 생성")
            return self.stats

        except Exception as e:
            handle_error(e, "연관관계 구축 실패")
            return self.stats

    def _add_mybatis_mapper_result(self, java_result: Dict[str, Any]) -> None:
        """MyBatis Mapper 결과 추가"""
        method_mappings = java_result.get('method_query_mappings', [])
        for mapping in method_mappings:
            self.collected_data['java_methods'].append({
                'file_path': java_result.get('file_path'),
                'class_name': java_result.get('class_name'),
                'namespace': java_result.get('namespace'),
                'method_name': mapping.get('method_name'),
                'query_id': mapping.get('query_id'),
                'xml_namespace': mapping.get('xml_namespace'),
                'mapping_type': 'MYBATIS_METHOD',
                'confidence': mapping.get('confidence', 0.8)
            })

    def _add_jpa_repository_result(self, java_result: Dict[str, Any]) -> None:
        """JPA Repository 결과 추가"""
        method_mappings = java_result.get('method_query_mappings', [])
        for mapping in method_mappings:
            self.collected_data['java_methods'].append({
                'file_path': java_result.get('file_path'),
                'class_name': java_result.get('class_name'),
                'method_name': mapping.get('method_name'),
                'query_sql': mapping.get('query_sql') or mapping.get('estimated_query'),
                'entity_name': mapping.get('entity_name'),
                'mapping_type': 'JPA_METHOD',
                'confidence': mapping.get('confidence', 0.7)
            })

        # Entity 매핑 정보도 추가
        entity_mappings = java_result.get('entity_table_mappings', [])
        for mapping in entity_mappings:
            if mapping.get('mapping_type') == 'JPA_REPOSITORY_ENTITY':
                self.collected_data['jpa_entities'].append(mapping)

    def _add_jpa_entity_result(self, java_result: Dict[str, Any]) -> None:
        """JPA Entity 결과 추가"""
        entity_mappings = java_result.get('entity_table_mappings', [])
        for mapping in entity_mappings:
            self.collected_data['jpa_entities'].append(mapping)

    def _build_mybatis_method_query_relationships(self) -> None:
        """MyBatis METHOD → QUERY 관계 구축"""
        try:
            count = 0

            for method_data in self.collected_data['java_methods']:
                if method_data.get('mapping_type') != 'MYBATIS_METHOD':
                    continue

                # 1. METHOD 컴포넌트 찾기
                method_full_name = f"{method_data['class_name']}.{method_data['method_name']}"
                method_id = self._find_component_id(method_full_name, 'METHOD')

                if not method_id:
                    debug(f"METHOD 컴포넌트를 찾을 수 없음: {method_full_name}")
                    continue

                # 2. QUERY 컴포넌트 찾기 (XML에서)
                query_id = self._find_query_component_id(
                    method_data['query_id'],
                    method_data.get('xml_namespace', '')
                )

                if not query_id:
                    debug(f"QUERY 컴포넌트를 찾을 수 없음: {method_data['query_id']}")
                    continue

                # 3. METHOD → QUERY 관계 생성
                self._insert_relationship(method_id, query_id, 'EXECUTES_QUERY')
                count += 1

            self.stats['method_query_relationships'] = count
            info(f"MyBatis METHOD → QUERY 관계 구축 완료: {count}개")

        except Exception as e:
            handle_error(e, "MyBatis METHOD → QUERY 관계 구축 실패")

    def _build_jpa_method_entity_relationships(self) -> None:
        """JPA METHOD → ENTITY/TABLE 관계 구축"""
        try:
            count = 0

            for method_data in self.collected_data['java_methods']:
                if method_data.get('mapping_type') != 'JPA_METHOD':
                    continue

                # 1. METHOD 컴포넌트 찾기
                method_full_name = f"{method_data['class_name']}.{method_data['method_name']}"
                method_id = self._find_component_id(method_full_name, 'METHOD')

                if not method_id:
                    debug(f"JPA METHOD 컴포넌트를 찾을 수 없음: {method_full_name}")
                    continue

                # 2. ENTITY 또는 TABLE 컴포넌트 찾기
                entity_name = method_data.get('entity_name')
                if entity_name:
                    # Entity 컴포넌트 찾기
                    entity_id = self._find_component_id(entity_name, 'CLASS')
                    if entity_id:
                        self._insert_relationship(method_id, entity_id, 'USES_ENTITY')
                        count += 1

                    # Entity에 매핑된 테이블 찾기
                    table_name = self._find_table_by_entity(entity_name)
                    if table_name:
                        table_id = self._find_component_id(table_name, 'TABLE')
                        if table_id:
                            self._insert_relationship(method_id, table_id, 'USES_TABLE')
                            count += 1

            self.stats['method_query_relationships'] += count
            info(f"JPA METHOD → ENTITY/TABLE 관계 구축 완료: {count}개")

        except Exception as e:
            handle_error(e, "JPA METHOD → ENTITY/TABLE 관계 구축 실패")

    def _build_query_table_relationships(self) -> None:
        """QUERY → TABLE 관계 구축"""
        try:
            count = 0

            # XML 쿼리 분석
            for query_data in self.collected_data['xml_queries']:
                sql_content = query_data.get('sql_content', '')
                if not sql_content:
                    continue

                # 1. QUERY 컴포넌트 찾기
                query_id = self._find_query_component_id(
                    query_data['query_id'],
                    query_data.get('namespace', '')
                )

                if not query_id:
                    debug(f"QUERY 컴포넌트를 찾을 수 없음: {query_data['query_id']}")
                    continue

                # 2. 이미 분석된 JOIN 관계에서 테이블 추출
                # (sql_join_analyzer에서 이미 테이블 추출 및 인퍼드 등록 완료)
                from parser.sql_parser import SqlParser
                sql_parser = SqlParser()
                tables = sql_parser.extract_table_names(sql_content)

                # 3. QUERY → TABLE 관계 생성
                for table_name in tables:
                    table_id = self._find_or_create_table_component(table_name)
                    if table_id:
                        self._insert_relationship(query_id, table_id, 'USE_TABLE')
                        count += 1

            # JPA 쿼리 분석
            for method_data in self.collected_data['java_methods']:
                if method_data.get('mapping_type') != 'JPA_METHOD':
                    continue

                query_sql = method_data.get('query_sql', '')
                if not query_sql or query_sql.startswith('--'):
                    continue

                # METHOD 컴포넌트 찾기
                method_full_name = f"{method_data['class_name']}.{method_data['method_name']}"
                method_id = self._find_component_id(method_full_name, 'METHOD')

                if not method_id:
                    continue

                # SQL에서 테이블 추출 (동일한 SQL 파서 사용)
                from parser.sql_parser import SqlParser
                sql_parser = SqlParser()
                tables = sql_parser.extract_table_names(query_sql)

                # METHOD → TABLE 관계 생성 (JPA는 직접 연결)
                for table_name in tables:
                    table_id = self._find_or_create_table_component(table_name)
                    if table_id:
                        self._insert_relationship(method_id, table_id, 'USES_TABLE')
                        count += 1

            self.stats['query_table_relationships'] = count
            info(f"QUERY → TABLE 관계 구축 완료: {count}개")

        except Exception as e:
            handle_error(e, "QUERY → TABLE 관계 구축 실패")

    def _build_table_join_relationships(self) -> None:
        """TABLE JOIN 관계 구축"""
        try:
            count = 0

            # XML 쿼리에서 조인 관계 추출
            for query_data in self.collected_data['xml_queries']:
                sql_content = query_data.get('sql_content', '')
                if not sql_content:
                    continue

                # 테이블 추출
                tables = self.sql_analyzer.extract_tables_from_sql(sql_content)

                # 조인 관계 추출
                join_relationships = self.sql_analyzer.extract_join_relationships(sql_content, tables)

                # TABLE → TABLE 조인 관계 생성
                for join_rel in join_relationships:
                    source_table = join_rel.get('source_table')
                    target_table = join_rel.get('target_table')
                    join_type = join_rel.get('join_type', 'UNKNOWN_JOIN')

                    if source_table and target_table:
                        source_id = self._find_or_create_table_component(source_table)
                        target_id = self._find_or_create_table_component(target_table)

                        if source_id and target_id and source_id != target_id:
                            self._insert_relationship(source_id, target_id, 'JOINS_WITH')
                            count += 1

            # JPA 쿼리에서도 조인 관계 추출
            for method_data in self.collected_data['java_methods']:
                if method_data.get('mapping_type') != 'JPA_METHOD':
                    continue

                query_sql = method_data.get('query_sql', '')
                if not query_sql or query_sql.startswith('--'):
                    continue

                tables = self.sql_analyzer.extract_tables_from_sql(query_sql)
                join_relationships = self.sql_analyzer.extract_join_relationships(query_sql, tables)

                for join_rel in join_relationships:
                    source_table = join_rel.get('source_table')
                    target_table = join_rel.get('target_table')

                    if source_table and target_table:
                        source_id = self._find_or_create_table_component(source_table)
                        target_id = self._find_or_create_table_component(target_table)

                        if source_id and target_id and source_id != target_id:
                            self._insert_relationship(source_id, target_id, 'JOINS_WITH')
                            count += 1

            self.stats['table_join_relationships'] = count
            info(f"TABLE JOIN 관계 구축 완료: {count}개")

        except Exception as e:
            handle_error(e, "TABLE JOIN 관계 구축 실패")

    def _build_entity_table_relationships(self) -> None:
        """JPA ENTITY → TABLE 관계 구축"""
        try:
            count = 0

            for entity_data in self.collected_data['jpa_entities']:
                entity_name = entity_data.get('entity_name')
                table_name = entity_data.get('table_name')

                if not entity_name or not table_name:
                    continue

                # 1. ENTITY (CLASS) 컴포넌트 찾기
                entity_id = self._find_component_id(entity_name, 'CLASS')

                if not entity_id:
                    debug(f"ENTITY 컴포넌트를 찾을 수 없음: {entity_name}")
                    continue

                # 2. TABLE 컴포넌트 찾기 또는 생성
                table_id = self._find_or_create_table_component(table_name)

                if not table_id:
                    debug(f"TABLE 컴포넌트 생성 실패: {table_name}")
                    continue

                # 3. ENTITY → TABLE 관계 생성
                self._insert_relationship(entity_id, table_id, 'MAPS_TO_TABLE')
                count += 1

            self.stats['entity_table_relationships'] = count
            info(f"JPA ENTITY → TABLE 관계 구축 완료: {count}개")

        except Exception as e:
            handle_error(e, "JPA ENTITY → TABLE 관계 구축 실패")

    def _find_component_id(self, component_name: str, component_type: str) -> Optional[int]:
        """컴포넌트 ID 찾기"""
        try:
            query = """
                SELECT component_id FROM components
                WHERE project_id = ? AND component_name = ? AND component_type = ? AND del_yn = 'N'
                LIMIT 1
            """
            result = self.db_utils.execute_query(query, (self.project_id, component_name, component_type))
            return result[0]['component_id'] if result else None

        except Exception as e:
            handle_error(e, f"컴포넌트 ID 찾기 실패: {component_name}")
            return None

    def _find_query_component_id(self, query_id: str, namespace: str) -> Optional[int]:
        """QUERY 컴포넌트 ID 찾기 (네임스페이스 고려)"""
        try:
            # 1. namespace.query_id 형태로 찾기
            full_query_name = f"{namespace}.{query_id}" if namespace else query_id
            component_id = self._find_component_id(full_query_name, 'QUERY')

            if component_id:
                return component_id

            # 2. query_id만으로 찾기
            component_id = self._find_component_id(query_id, 'QUERY')
            return component_id

        except Exception as e:
            handle_error(e, f"QUERY 컴포넌트 ID 찾기 실패: {query_id}")
            return None

    def _find_or_create_table_component(self, table_name: str) -> Optional[int]:
        """TABLE 컴포넌트 찾기 또는 생성 - Oracle 키워드 필터링 추가"""
        try:
            # 1. 기존 테이블 컴포넌트 찾기
            table_id = self._find_component_id(table_name, 'TABLE')

            if table_id:
                return table_id

            # 2. Oracle 키워드 검증 (INFERRED 테이블 생성 시에만)
            if self._is_oracle_keyword(table_name):
                debug(f"Oracle 키워드 '{table_name}'이므로 inferred 테이블 생성 스킵")
                return None

            # 3. 테이블이 없으면 생성 (inferred)
            debug(f"TABLE 컴포넌트 생성: {table_name}")

            # inferred 컴포넌트용 file_id 찾기 (프로젝트의 첫 번째 파일 사용)
            inferred_file_id = self._get_inferred_file_id()
            if not inferred_file_id:
                error(f"inferred 컴포넌트용 file_id를 찾을 수 없음: {table_name}")
                return None

            # components 테이블에 추가
            component_data = {
                'project_id': self.project_id,
                'file_id': inferred_file_id,  # inferred 컴포넌트용 file_id 사용
                'component_type': 'TABLE',
                'component_name': table_name,
                'parent_id': None,
                'layer': 'TABLE',
                'hash_value': 'INFERRED',
                'del_yn': 'N'
            }

            # 디버그 로그 추가: components 테이블 삽입 전 데이터 확인
            debug(f"[RELATIONSHIP_BUILDER] inferred TABLE 컴포넌트 생성 시도: {table_name}")
            debug(f"[RELATIONSHIP_BUILDER] component_data: {component_data}")
            
            if component_data.get('file_id') is None:
                error(f"[RELATIONSHIP_BUILDER] FATAL: file_id가 NULL입니다! table_name={table_name}, inferred_file_id={inferred_file_id}")
                handle_error(Exception(f"file_id가 NULL입니다: {table_name}"), f"inferred TABLE 컴포넌트 생성 실패: {table_name}")
                return None

            component_id = self.db_utils.insert_or_replace('components', component_data)

            # tables 테이블에도 추가
            table_data = {
                'project_id': self.project_id,
                'table_name': table_name,
                'table_owner': 'INFERRED',
                'table_comments': 'Inferred from SQL analysis',
                'component_id': component_id,
                'hash_value': 'INFERRED',
                'del_yn': 'N'
            }

            self.db_utils.insert_or_replace('tables', table_data)

            return component_id

        except Exception as e:
            handle_error(e, f"TABLE 컴포넌트 찾기/생성 실패: {table_name}")
            return None

    def _get_inferred_file_id(self) -> Optional[int]:
        """
        inferred 컴포넌트용 file_id 찾기 (관계 분석 컨텍스트에 따라 결정)
        USER RULES: 공통함수 사용, 하드코딩 금지
        
        관계 분석에서 inferred 컴포넌트는 주로 다음 상황에서 생성됩니다:
        1. SQL 쿼리 분석에서 테이블명 추론 (XML/Java 파일에서)
        2. 관계 구축에서 누락된 테이블 발견 (분석된 파일들에서)
        
        Returns:
            file_id 또는 None
        """
        try:
            # 1. SQL 관련 파일 우선 조회 (inferred 테이블은 주로 SQL 분석에서 생성)
            sql_file_query = """
                SELECT file_id 
                FROM files 
                WHERE project_id = ? AND file_type IN ('XML', 'SQL') AND del_yn = 'N'
                ORDER BY file_type, file_id
                LIMIT 1
            """
            sql_result = self.db_utils.execute_query(sql_file_query, (self.project_id,))
            
            if sql_result and len(sql_result) > 0:
                file_id = sql_result[0]['file_id']
                debug(f"inferred 컴포넌트용 SQL 관련 file_id: {file_id}")
                return file_id
            
            # 2. Java 파일 조회 (StringBuilder SQL 분석에서도 inferred 생성 가능)
            java_file_query = """
                SELECT file_id 
                FROM files 
                WHERE project_id = ? AND file_type = 'JAVA' AND del_yn = 'N'
                ORDER BY file_id
                LIMIT 1
            """
            java_result = self.db_utils.execute_query(java_file_query, (self.project_id,))
            
            if java_result and len(java_result) > 0:
                file_id = java_result[0]['file_id']
                debug(f"inferred 컴포넌트용 Java file_id: {file_id}")
                return file_id
            
            # 3. 마지막으로 첫 번째 파일 사용 (fallback)
            first_file_query = "SELECT file_id FROM files WHERE project_id = ? AND del_yn = 'N' ORDER BY file_id LIMIT 1"
            first_file_result = self.db_utils.execute_query(first_file_query, (self.project_id,))
            first_file_id = first_file_result[0]['file_id'] if first_file_result else None
            
            if not first_file_id:
                # 시스템 에러: 프로젝트에 파일이 없는 것은 1단계에서 처리되지 않았음을 의미
                handle_error(f"프로젝트 {self.project_id}에 파일이 없습니다. 1단계 파일 스캔이 제대로 실행되지 않았습니다.")
                return None
                
            debug(f"inferred 컴포넌트용 첫 번째 file_id (fallback): {first_file_id}")
            return first_file_id
            
        except Exception as e:
            # 시스템 에러: 데이터베이스 연결 실패 등 - 프로그램 종료
            handle_error(e, f"inferred 컴포넌트용 file_id 조회 실패")
            return None

    def _find_table_by_entity(self, entity_name: str) -> Optional[str]:
        """Entity명으로 테이블명 찾기"""
        try:
            # JPA Entity 매핑에서 찾기
            for entity_data in self.collected_data['jpa_entities']:
                if entity_data.get('entity_name') == entity_name:
                    return entity_data.get('table_name')

            # 기본 규칙: CamelCase → SNAKE_CASE
            return self._camel_to_snake(entity_name).upper()

        except Exception as e:
            handle_error(e, f"Entity 테이블명 찾기 실패: {entity_name}")
            return None

    def _camel_to_snake(self, name: str) -> str:
        """CamelCase를 snake_case로 변환"""
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    def _insert_relationship(self, src_id: int, dst_id: int, rel_type: str) -> None:
        """관계 저장"""
        try:
            if not src_id or not dst_id:
                debug(f"관계 저장 건너뜀 - ID 없음: src={src_id}, dst={dst_id}")
                return

            relationship_data = {
                'src_id': src_id,
                'dst_id': dst_id,
                'rel_type': rel_type,
                'confidence': 1.0,
                'has_error': 'N',
                'del_yn': 'N'
            }

            # INSERT OR IGNORE로 중복 방지
            sql = """
                INSERT OR IGNORE INTO relationships (src_id, dst_id, rel_type, confidence, has_error, del_yn)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            self.db_utils.execute_update(sql, (src_id, dst_id, rel_type, 1.0, 'N', 'N'))

        except Exception as e:
            handle_error(e, f"관계 저장 실패: {src_id} → {dst_id} ({rel_type})")

    def _extract_namespace_from_xml(self, xml_file_path: str) -> str:
        """XML 파일 경로에서 네임스페이스 추출 (간단한 규칙)"""
        try:
            # UserMapper.xml → com.example.mapper.UserMapper 추정
            import os
            file_name = os.path.basename(xml_file_path)
            class_name = file_name.replace('.xml', '')

            # 기본 패키지 구조 가정
            return f"com.example.mapper.{class_name}"

        except Exception as e:
            handle_error(e, f"네임스페이스 추출 실패: {xml_file_path}")
            return ""

    def get_statistics(self) -> Dict[str, int]:
        """통계 반환"""
        return self.stats.copy()

    def add_frontend_analysis_result(self, frontend_result: Dict[str, Any]) -> None:
        """프론트엔드 분석 결과 추가"""
        try:
            if not frontend_result or frontend_result.get('error'):
                debug(f"프론트엔드 분석 결과 스킵 (에러): {frontend_result.get('file_path', 'unknown')}")
                return

            # 프론트엔드 파일 정보 추가
            file_info = {
                'file_path': frontend_result.get('file_path'),
                'file_type': frontend_result.get('file_type'),
                'component_name': frontend_result.get('component_name'),
                'api_call_count': frontend_result.get('api_call_count', 0)
            }
            self.collected_data['frontend_files'].append(file_info)

            # API 호출 정보 추가
            api_calls = frontend_result.get('api_calls', [])
            for api_call in api_calls:
                api_call_data = {
                    'file_path': frontend_result.get('file_path'),
                    'component_name': frontend_result.get('component_name'),
                    'api_url': api_call.get('api_url'),
                    'original_url': api_call.get('original_url'),
                    'http_method': api_call.get('http_method'),
                    'framework': api_call.get('framework'),
                    'line_number': api_call.get('line_number'),
                    'confidence': api_call.get('confidence', 0.5)
                }
                self.collected_data['api_calls'].append(api_call_data)

            info(f"프론트엔드 분석 결과 추가: {len(api_calls)}개 API 호출")

        except Exception as e:
            handle_error(e, f"프론트엔드 분석 결과 추가 실패: {frontend_result}")

    def add_controller_analysis_result(self, controller_result: Dict[str, Any]) -> None:
        """Spring Controller 분석 결과 추가"""
        try:
            if not controller_result or controller_result.get('error'):
                debug(f"Controller 분석 결과 스킵 (에러): {controller_result.get('file_path', 'unknown')}")
                return

            # Controller API 정보 추가
            api_mappings = controller_result.get('api_mappings', [])
            for api_mapping in api_mappings:
                controller_api_data = {
                    'file_path': controller_result.get('file_path'),
                    'class_name': controller_result.get('class_name'),
                    'method_name': api_mapping.get('method_name'),
                    'api_url': api_mapping.get('api_url'),
                    'http_method': api_mapping.get('http_method'),
                    'request_mapping': api_mapping.get('request_mapping'),
                    'confidence': api_mapping.get('confidence', 0.8)
                }
                self.collected_data['controller_apis'].append(controller_api_data)

            info(f"Controller 분석 결과 추가: {len(api_mappings)}개 API 매핑")

        except Exception as e:
            handle_error(e, f"Controller 분석 결과 추가 실패: {controller_result}")

    def _build_frontend_api_relationships(self) -> None:
        """프론트엔드 → API → METHOD 관계 구축"""
        try:
            frontend_api_count = 0
            api_method_count = 0

            # 1. 프론트엔드 → API 관계 구축
            for api_call in self.collected_data['api_calls']:
                component_name = api_call.get('component_name')
                api_url = api_call.get('api_url')
                http_method = api_call.get('http_method')

                if not component_name or not api_url:
                    continue

                # 프론트엔드 컴포넌트 찾기 (FRONTEND 타입으로 가정)
                frontend_id = self._find_component_id(component_name, 'FRONTEND')
                if not frontend_id:
                    # 프론트엔드 컴포넌트가 없으면 생성
                    frontend_id = self._create_frontend_component(component_name, api_call.get('file_path'))

                if frontend_id:
                    # API URL 컴포넌트 찾기 또는 생성
                    api_id = self._find_or_create_api_component(api_url, http_method)
                    if api_id:
                        self._insert_relationship(frontend_id, api_id, 'CALLS_API')
                        frontend_api_count += 1

            # 2. API → METHOD 관계 구축
            for api_call in self.collected_data['api_calls']:
                api_url = api_call.get('api_url')
                http_method = api_call.get('http_method')

                if not api_url:
                    continue

                # 매칭되는 Controller API 찾기
                matching_controller = self._find_matching_controller_api(api_url, http_method)
                if matching_controller:
                    # API 컴포넌트 찾기
                    api_id = self._find_or_create_api_component(api_url, http_method)

                    # Controller METHOD 찾기
                    method_full_name = f"{matching_controller['class_name']}.{matching_controller['method_name']}"
                    method_id = self._find_component_id(method_full_name, 'METHOD')

                    if api_id and method_id:
                        self._insert_relationship(api_id, method_id, 'IMPLEMENTS_API')
                        api_method_count += 1

            self.stats['frontend_api_relationships'] = frontend_api_count
            self.stats['api_method_relationships'] = api_method_count
            info(f"프론트엔드 → API 관계 구축 완료: {frontend_api_count}개")
            info(f"API → METHOD 관계 구축 완료: {api_method_count}개")

        except Exception as e:
            handle_error(e, "프론트엔드 → API → METHOD 관계 구축 실패")

    def _create_frontend_component(self, component_name: str, file_path: str) -> Optional[int]:
        """프론트엔드 컴포넌트 생성"""
        try:
            # 프론트엔드 파일의 file_id 찾기
            frontend_file_id = self._get_frontend_file_id(component_name)
            if not frontend_file_id:
                error(f"프론트엔드 파일의 file_id를 찾을 수 없음: {component_name}")
                return None

            component_data = {
                'project_id': self.project_id,
                'file_id': frontend_file_id,  # 프론트엔드 파일의 file_id 사용
                'component_type': 'FRONTEND',
                'component_name': component_name,
                'parent_id': None,
                'layer': 'FRONTEND',
                'hash_value': 'INFERRED',
                'del_yn': 'N'
            }

            component_id = self.db_utils.insert_or_replace('components', component_data)
            debug(f"프론트엔드 컴포넌트 생성: {component_name} (ID: {component_id}) file_id={frontend_file_id}")
            return component_id

        except Exception as e:
            handle_error(e, f"프론트엔드 컴포넌트 생성 실패: {component_name}")
            return None

    def _get_frontend_file_id(self, component_name: str) -> Optional[int]:
        """
        프론트엔드 파일의 file_id 찾기 (JSP, JSX, Vue, TypeScript 등 모든 프론트엔드 파일 지원)
        
        Args:
            component_name: 컴포넌트명 (예: error.jsp, App.jsx, Home.vue, index.ts)
            
        Returns:
            file_id 또는 None
        """
        try:
            # 프론트엔드 파일에서 해당 파일명으로 file_id 찾기
            # JSP, JSX, Vue, TypeScript, JavaScript, HTML 등 모든 프론트엔드 파일 타입 지원
            query = """
                SELECT file_id 
                FROM files 
                WHERE project_id = ? 
                  AND file_name = ? 
                  AND file_type IN ('JSP', 'JSX', 'VUE', 'TS', 'JS', 'HTML')
                  AND del_yn = 'N'
                LIMIT 1
            """
            result = self.db_utils.execute_query(query, (self.project_id, component_name))
            
            if result and len(result) > 0:
                file_id = result[0]['file_id']
                debug(f"프론트엔드 파일 찾음: {component_name} → file_id: {file_id}")
                return file_id
            
            # 파일을 찾지 못한 경우
            debug(f"프론트엔드 파일을 찾지 못함: {component_name}")
            return None
            
        except Exception as e:
            handle_error(e, f"프론트엔드 파일 file_id 조회 실패: {component_name}")
            return None

    def _find_or_create_api_component(self, api_url: str, http_method: str) -> Optional[int]:
        """API 컴포넌트 찾기 또는 생성"""
        try:
            # API 이름 생성: GET /api/users → GET_/api/users
            api_name = f"{http_method}_{api_url}"

            # 기존 API 컴포넌트 찾기
            api_id = self._find_component_id(api_name, 'API')
            if api_id:
                return api_id

            # API 컴포넌트용 file_id 찾기 (inferred 컴포넌트용)
            api_file_id = self._get_inferred_file_id()
            if not api_file_id:
                error(f"API 컴포넌트용 file_id를 찾을 수 없음: {api_name}")
                return None

            # API 컴포넌트 생성
            component_data = {
                'project_id': self.project_id,
                'file_id': api_file_id,  # inferred 컴포넌트용 file_id 사용
                'component_type': 'API',
                'component_name': api_name,
                'parent_id': None,
                'layer': 'API',
                'hash_value': 'INFERRED',
                'del_yn': 'N'
            }

            component_id = self.db_utils.insert_or_replace('components', component_data)
            debug(f"API 컴포넌트 생성: {api_name} (ID: {component_id}) file_id={api_file_id}")
            return component_id

        except Exception as e:
            handle_error(e, f"API 컴포넌트 찾기/생성 실패: {api_url}")
            return None

    def _find_matching_controller_api(self, api_url: str, http_method: str) -> Optional[Dict[str, Any]]:
        """프론트엔드 API 호출과 매칭되는 Controller API 찾기"""
        try:
            # 정확한 매칭 우선
            for controller_api in self.collected_data['controller_apis']:
                if (controller_api.get('api_url') == api_url and
                    controller_api.get('http_method') == http_method):
                    return controller_api

            # 패턴 매칭 (동적 경로 처리)
            normalized_frontend_url = self._normalize_api_url_for_matching(api_url)

            for controller_api in self.collected_data['controller_apis']:
                controller_url = controller_api.get('api_url', '')
                normalized_controller_url = self._normalize_api_url_for_matching(controller_url)

                if (normalized_controller_url == normalized_frontend_url and
                    controller_api.get('http_method') == http_method):
                    return controller_api

            return None

        except Exception as e:
            handle_error(e, f"Controller API 매칭 실패: {api_url}")
            return None

    def _normalize_api_url_for_matching(self, api_url: str) -> str:
        """API URL 매칭을 위한 정규화"""
        try:
            import re

            # 동적 파라미터 정규화
            # /api/users/123 → /api/users/{id}
            # /api/users/{userId} → /api/users/{id}
            normalized = api_url

            # 숫자 ID를 {id}로 치환
            normalized = re.sub(r'/\d+(?:/|$)', '/{id}/', normalized)

            # 기존 변수명을 {id}로 정규화
            normalized = re.sub(r'/\{[^}]+\}', '/{id}', normalized)

            # 끝의 / 제거
            normalized = normalized.rstrip('/')

            return normalized

        except Exception as e:
            handle_error(e, f"API URL 정규화 실패: {api_url}")
            return api_url

    def clear_collected_data(self) -> None:
        """수집된 데이터 초기화"""
        for key in self.collected_data:
            self.collected_data[key] = []

        for key in self.stats:
            self.stats[key] = 0
    
    def _is_oracle_keyword(self, name: str) -> bool:
        """
        Oracle SQL 키워드인지 확인

        Args:
            name: 확인할 이름

        Returns:
            Oracle 키워드이면 True
        """
        return self.oracle_keyword_manager.is_oracle_keyword(name)