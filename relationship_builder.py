"""
RelationshipBuilder - Parser-Builder 패턴 구현
- 모든 파서의 결과를 종합하여 최종 연관관계 설정
- 단서 수집 → 관계 설정 분리
- relationships 테이블 완성이 목표
"""

from typing import List, Dict, Any, Set, Optional
import sqlite3
from util import (
    DatabaseUtils, PathUtils, app_logger, info, error, debug, warning, handle_error
)
from util.oracle_keyword_manager import get_oracle_keyword_manager
from util.simple_relationship_analyzer import SimpleRelationshipAnalyzer
from util.frontend_api_analyzer import FrontendApiAnalyzer


class RelationshipBuilder:
    """연관관계 빌더 - 모든 파서 결과를 종합하여 최종 관계 설정"""

    def __init__(self, project_name: str, project_id: int, conn: sqlite3.Connection):
        """
        RelationshipBuilder 초기화

        Args:
            project_name: 프로젝트명
            project_id: 프로젝트 ID
            conn: 외부에서 주입된 데이터베이스 연결 객체
        """
        self.project_name = project_name
        self.project_id = project_id
        self.conn = conn

        self.path_utils = PathUtils()
        self.db_utils = DatabaseUtils(None)  # 연결은 외부에서 주입받으므로 경로는 None
        self.sql_analyzer = SimpleRelationshipAnalyzer() # 이 클래스도 conn을 받도록 수정 필요
        self.frontend_analyzer = FrontendApiAnalyzer() # 이 클래스도 conn을 받도록 수정 필요

        self.oracle_keyword_manager = get_oracle_keyword_manager()
        self.collected_data = {k: [] for k in ['xml_queries', 'java_methods', 'jpa_entities', 'api_calls', 'api_implementations', 'frontend_files', 'controller_apis']}
        self.stats = {k: 0 for k in ['method_query_relationships', 'query_table_relationships', 'table_join_relationships', 'entity_table_relationships', 'frontend_api_relationships', 'api_method_relationships', 'total_relationships']}

    def build_all_relationships(self) -> Dict[str, int]:
        """모든 연관관계 구축 (외부 트랜잭션 내에서 실행)"""
        try:
            info("연관관계 구축 시작")

            # 데이터베이스에서 직접 데이터 수집
            self._collect_xml_queries_from_db()
            self._collect_java_methods_from_db()
            self._collect_jpa_entities_from_db()
            self._collect_api_calls_from_db()

            self._build_mybatis_method_query_relationships()
            self._build_jpa_method_entity_relationships()
            self._build_query_table_relationships()
            self._build_table_join_relationships()
            self._build_entity_table_relationships()
            self._build_frontend_api_relationships()
            self._build_call_method_relationships()

            self.stats['total_relationships'] = sum(self.stats.values())
            info(f"연관관계 구축 완료: 총 {self.stats['total_relationships']}개 관계 생성")
            return self.stats

        except Exception as e:
            handle_error(e, "연관관계 구축 실패")
            return self.stats

    def _collect_xml_queries_from_db(self) -> None:
        """데이터베이스에서 XML 쿼리 데이터 수집"""
        try:
            # SQL 컴포넌트에서 XML 쿼리 정보 수집 (sql_contents 테이블 없이)
            query = """
                SELECT c.component_id, c.component_name, c.component_type, c.file_id,
                       f.file_path
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND c.component_type IN ('SQL_SELECT', 'SQL_INSERT', 'SQL_UPDATE', 'SQL_DELETE', 'SQL_MERGE')
                  AND c.del_yn = 'N'
                  AND f.del_yn = 'N'
            """
            results = self.db_utils.execute_query(query, (self.project_name,), conn=self.conn)
            
            for row in results:
                # SqlContent.db에서 SQL 내용 조회 시도
                sql_content = self._get_sql_content_from_sqlcontent_db(row['component_id'])
                
                self.collected_data['xml_queries'].append({
                    'component_id': row['component_id'],
                    'component_name': row['component_name'],
                    'component_type': row['component_type'],
                    'file_id': row['file_id'],
                    'file_path': row['file_path'],
                    'sql_content': sql_content or ''
                })
            
            info(f"XML 쿼리 데이터 수집 완료: {len(self.collected_data['xml_queries'])}개")
            
        except Exception as e:
            handle_error(e, "XML 쿼리 데이터 수집 실패")

    def _collect_java_methods_from_db(self) -> None:
        """데이터베이스에서 Java 메서드 데이터 수집"""
        try:
            # METHOD 컴포넌트에서 Java 메서드 정보 수집
            query = """
                SELECT c.component_id, c.component_name, c.component_type, c.file_id,
                       f.file_path, f.file_name
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND c.component_type = 'METHOD'
                  AND c.del_yn = 'N'
                  AND f.del_yn = 'N'
            """
            results = self.db_utils.execute_query(query, (self.project_name,), conn=self.conn)
            
            for row in results:
                # 클래스명과 메서드명 분리
                full_name = row['component_name']
                if '.' in full_name:
                    class_name, method_name = full_name.rsplit('.', 1)
                else:
                    class_name = 'Unknown'
                    method_name = full_name
                
                self.collected_data['java_methods'].append({
                    'component_id': row['component_id'],
                    'component_name': row['component_name'],
                    'class_name': class_name,
                    'method_name': method_name,
                    'file_id': row['file_id'],
                    'file_path': row['file_path'],
                    'file_name': row['file_name']
                })
            
            info(f"Java 메서드 데이터 수집 완료: {len(self.collected_data['java_methods'])}개")
            
        except Exception as e:
            handle_error(e, "Java 메서드 데이터 수집 실패")

    def _collect_jpa_entities_from_db(self) -> None:
        """데이터베이스에서 JPA 엔티티 데이터 수집"""
        try:
            # JPA 관련 컴포넌트 수집
            query = """
                SELECT c.component_id, c.component_name, c.component_type, c.file_id,
                       f.file_path, f.file_name
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND c.component_type IN ('ENTITY', 'REPOSITORY', 'SERVICE')
                  AND c.del_yn = 'N'
                  AND f.del_yn = 'N'
            """
            results = self.db_utils.execute_query(query, (self.project_name,), conn=self.conn)
            
            for row in results:
                self.collected_data['jpa_entities'].append({
                    'component_id': row['component_id'],
                    'component_name': row['component_name'],
                    'component_type': row['component_type'],
                    'file_id': row['file_id'],
                    'file_path': row['file_path'],
                    'file_name': row['file_name']
                })
            
            info(f"JPA 엔티티 데이터 수집 완료: {len(self.collected_data['jpa_entities'])}개")
            
        except Exception as e:
            handle_error(e, "JPA 엔티티 데이터 수집 실패")

    def _collect_api_calls_from_db(self) -> None:
        """데이터베이스에서 API 호출 데이터 수집"""
        try:
            # API_URL 컴포넌트 수집
            query = """
                SELECT c.component_id, c.component_name, c.component_type, c.file_id,
                       f.file_path, f.file_name
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND c.component_type = 'API_URL'
                  AND c.del_yn = 'N'
                  AND f.del_yn = 'N'
            """
            results = self.db_utils.execute_query(query, (self.project_name,), conn=self.conn)
            
            for row in results:
                self.collected_data['api_calls'].append({
                    'component_id': row['component_id'],
                    'component_name': row['component_name'],
                    'file_id': row['file_id'],
                    'file_path': row['file_path'],
                    'file_name': row['file_name']
                })
            
            info(f"API 호출 데이터 수집 완료: {len(self.collected_data['api_calls'])}개")
            
        except Exception as e:
            handle_error(e, "API 호출 데이터 수집 실패")

    def _get_sql_content_from_sqlcontent_db(self, component_id: int) -> Optional[str]:
        """SqlContent.db에서 SQL 내용 조회"""
        try:
            import os
            sqlcontent_db_path = os.path.join('projects', self.project_name, 'SqlContent.db')
            
            if not os.path.exists(sqlcontent_db_path):
                debug(f"SqlContent.db 파일이 없습니다: {sqlcontent_db_path}")
                return None
            
            # SqlContent.db 연결
            import sqlite3
            sqlcontent_conn = sqlite3.connect(sqlcontent_db_path)
            sqlcontent_conn.row_factory = sqlite3.Row
            
            # sql_contents 테이블에서 SQL 내용 조회
            query = """
                SELECT sql_content_compressed, file_path, file_name
                FROM sql_contents 
                WHERE component_id = ? AND del_yn = 'N'
            """
            cursor = sqlcontent_conn.cursor()
            cursor.execute(query, (component_id,))
            result = cursor.fetchone()
            
            if result and result['sql_content_compressed']:
                # gzip 압축 해제
                import gzip
                try:
                    decompressed_content = gzip.decompress(result['sql_content_compressed']).decode('utf-8')
                    return decompressed_content
                except Exception as e:
                    debug(f"SQL 내용 압축 해제 실패: {e}")
                    return None
            
            sqlcontent_conn.close()
            return None
            
        except Exception as e:
            debug(f"SqlContent.db에서 SQL 내용 조회 실패: {e}")
            return None

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

                # 1. QUERY 컴포넌트 ID 사용
                query_id = query_data.get('component_id')
                if not query_id:
                    debug(f"QUERY 컴포넌트 ID를 찾을 수 없음: {query_data.get('component_name', 'Unknown')}")
                    continue

                # 2. SQL에서 테이블 추출
                tables = self._extract_tables_from_sql(sql_content)
                if not tables:
                    continue

                # 3. QUERY → TABLE 관계 생성
                for table_name in tables:
                    table_id = self._find_table_component_id(table_name)
                    if table_id and query_id != table_id:
                        self._insert_relationship(query_id, table_id, 'USE_TABLE')
                        count += 1

            # Java 메서드에서 SQL 쿼리 분석
            for method_data in self.collected_data['java_methods']:
                # SQL 쿼리가 포함된 메서드 찾기
                if 'sql_content' in method_data:
                    sql_content = method_data['sql_content']
                    if not sql_content:
                        continue
                    
                    method_id = method_data.get('component_id')
                    if not method_id:
                        continue
                    
                    tables = self._extract_tables_from_sql(sql_content)
                    for table_name in tables:
                        table_id = self._find_table_component_id(table_name)
                        if table_id and method_id != table_id:
                            self._insert_relationship(method_id, table_id, 'USE_TABLE')
                            count += 1
                        count += 1

            # JPA 쿼리 분석
            for method_data in self.collected_data['java_methods']:
                if method_data.get('mapping_type') != 'JPA_METHOD':
                    continue

                query_sql = method_data.get('query_sql', '')
                if not query_sql or query_sql.startswith('--'):
                    continue

                method_full_name = f"{method_data['class_name']}.{method_data['method_name']}"
                method_id = self._find_component_id(method_full_name, 'METHOD')

                if not method_id:
                    continue

                from parser.sql_parser import SqlParser
                sql_parser = SqlParser()
                tables = sql_parser.extract_table_names(query_sql)

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

                # SQL에서 테이블 추출
                tables = self._extract_tables_from_sql(sql_content)
                if len(tables) < 2:
                    continue

                # 테이블 간 조인 관계 생성
                for i, source_table in enumerate(tables):
                    for target_table in tables[i+1:]:
                        if source_table != target_table:
                            source_id = self._find_table_component_id(source_table)
                            target_id = self._find_table_component_id(target_table)
                            
                            if source_id and target_id:
                                # 명시적 조인 확인
                                if self._has_explicit_join(sql_content, source_table, target_table):
                                    self._insert_relationship(source_id, target_id, 'JOIN_EXPLICIT')
                                    count += 1
                                else:
                                    self._insert_relationship(source_id, target_id, 'JOIN_IMPLICIT')
                                    count += 1

            # 기존 relationships에서 조인 관계 확인
            existing_joins = self._get_existing_join_relationships()
            count += len(existing_joins)
            
            self.stats['table_join_relationships'] = count
            info(f"TABLE JOIN 관계 구축 완료: {count}개")

        except Exception as e:
            handle_error(e, "TABLE JOIN 관계 구축 실패")

    def _extract_tables_from_sql(self, sql_content: str) -> List[str]:
        """SQL에서 테이블명 추출"""
        try:
            import re
            tables = []
            
            # FROM 절에서 테이블 추출
            from_pattern = r'FROM\s+(\w+)'
            from_matches = re.findall(from_pattern, sql_content, re.IGNORECASE)
            tables.extend(from_matches)
            
            # JOIN 절에서 테이블 추출
            join_pattern = r'JOIN\s+(\w+)'
            join_matches = re.findall(join_pattern, sql_content, re.IGNORECASE)
            tables.extend(join_matches)
            
            # 중복 제거 및 정리
            unique_tables = list(set([t.upper() for t in tables if t]))
            return unique_tables
            
        except Exception as e:
            debug(f"테이블 추출 실패: {e}")
            return []

    def _find_table_component_id(self, table_name: str) -> Optional[int]:
        """테이블 컴포넌트 ID 찾기"""
        try:
            query = """
                SELECT c.component_id 
                FROM components c
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND c.component_name = ?
                  AND c.component_type = 'TABLE'
                  AND c.del_yn = 'N'
            """
            results = self.db_utils.execute_query(query, (self.project_name, table_name), conn=self.conn)
            return results[0]['component_id'] if results else None
            
        except Exception as e:
            debug(f"테이블 컴포넌트 ID 찾기 실패: {table_name} - {e}")
            return None

    def _has_explicit_join(self, sql_content: str, table1: str, table2: str) -> bool:
        """명시적 조인 여부 확인"""
        try:
            import re
            # JOIN 키워드가 있는지 확인
            join_pattern = r'JOIN\s+\w+'
            return bool(re.search(join_pattern, sql_content, re.IGNORECASE))
        except:
            return False

    def _get_existing_join_relationships(self) -> List[Dict]:
        """기존 조인 관계 조회"""
        try:
            query = """
                SELECT r.src_id, r.dst_id, r.rel_type
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                JOIN components dst ON r.dst_id = dst.component_id
                JOIN projects p ON src.project_id = p.project_id
                WHERE p.project_name = ?
                  AND r.rel_type IN ('JOIN_EXPLICIT', 'JOIN_IMPLICIT')
                  AND r.del_yn = 'N'
            """
            results = self.db_utils.execute_query(query, (self.project_name,), conn=self.conn)
            return results
        except Exception as e:
            debug(f"기존 조인 관계 조회 실패: {e}")
            return []

    def _build_call_method_relationships(self) -> None:
        """CALL_METHOD 관계 구축 - 실제 호출 관계만 생성"""
        try:
            count = 0

            # API_URL → METHOD 관계 생성 (실제 매핑된 메서드만)
            for api_data in self.collected_data['api_calls']:
                api_id = api_data.get('component_id')
                if not api_id:
                    continue
                
                # API_URL에 실제 매핑된 METHOD 찾기 (Spring @RequestMapping 등)
                # 현재는 간단히 같은 파일의 첫 번째 METHOD만 매핑
                file_id = api_data.get('file_id')
                if not file_id:
                    continue
                
                # 같은 파일의 첫 번째 METHOD 컴포넌트만 조회
                query = """
                    SELECT c.component_id, c.component_name
                    FROM components c
                    WHERE c.file_id = ? AND c.component_type = 'METHOD' AND c.del_yn = 'N'
                    ORDER BY c.component_id
                    LIMIT 1
                """
                methods = self.db_utils.execute_query(query, (file_id,), conn=self.conn)
                
                for method in methods:
                    method_id = method['component_id']
                    if method_id != api_id:
                        self._insert_relationship(api_id, method_id, 'CALL_METHOD')
                        count += 1

            # METHOD → METHOD 관계 생성 (실제 호출 관계만)
            # 현재는 실제 호출 분석이 없으므로 관계 생성하지 않음
            # TODO: 실제 메서드 호출 분석 로직 구현 필요

            self.stats['api_method_relationships'] = count
            info(f"CALL_METHOD 관계 구축 완료: {count}개")

        except Exception as e:
            handle_error(e, "CALL_METHOD 관계 구축 실패")

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
            # 1. 정확한 매칭 시도
            query = """
                SELECT c.component_id FROM components c
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? AND c.component_name = ? AND c.component_type = ? AND c.del_yn = 'N'
                LIMIT 1
            """
            result = self.db_utils.execute_query(query, (self.project_name, component_name, component_type), conn=self.conn)
            if result:
                return result[0]['component_id']
            
            # 2. 부분 매칭 시도 (클래스명만으로)
            if '.' in component_name:
                class_name = component_name.split('.')[0]
                query = """
                    SELECT c.component_id FROM components c
                    JOIN projects p ON c.project_id = p.project_id
                    WHERE p.project_name = ? AND c.component_name LIKE ? AND c.component_type = ? AND c.del_yn = 'N'
                    LIMIT 1
                """
                result = self.db_utils.execute_query(query, (self.project_name, f"{class_name}.%", component_type), conn=self.conn)
                if result:
                    return result[0]['component_id']
            
            # 3. 대소문자 무시 매칭
            query = """
                SELECT c.component_id FROM components c
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? AND UPPER(c.component_name) = UPPER(?) AND c.component_type = ? AND c.del_yn = 'N'
                LIMIT 1
            """
            result = self.db_utils.execute_query(query, (self.project_name, component_name, component_type), conn=self.conn)
            return result[0]['component_id'] if result else None

        except Exception as e:
            debug(f"컴포넌트 ID 찾기 실패: {component_name} ({component_type}) - {e}")
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
            return self._find_component_id(query_id, 'QUERY')

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

            # INSERT OR IGNORE로 중복 방지
            sql = """
                INSERT OR IGNORE INTO relationships (src_id, dst_id, rel_type, confidence, has_error, del_yn)
                VALUES (?, ?, ?, 1.0, 'N', 'N')
            """
            self.db_utils.execute_update(sql, (src_id, dst_id, rel_type), conn=self.conn)

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

    def _build_frontend_api_relationships(self, conn=None) -> None:
        """프론트엔드 → API → METHOD 관계 구축 (단일 연결 지원)"""
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