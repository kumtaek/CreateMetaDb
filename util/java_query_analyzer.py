"""
Java Method → Query 연결 분석기
- MyBatis Mapper 인터페이스 분석
- JPA Repository 분석
- 명명 규칙 기반 매핑
"""

import re
from typing import List, Dict, Any, Set, Tuple, Optional
from util import app_logger, info, error, debug, warning, handle_error


class JavaQueryAnalyzer:
    """Java Method → Query 연결 분석기"""

    def __init__(self):
        # MyBatis 패턴
        self.mybatis_indicators = [
            '@Mapper',
            'Mapper',
            'org.apache.ibatis',
            'selectOne', 'selectList', 'insert', 'update', 'delete'
        ]

        # JPA 패턴
        self.jpa_indicators = [
            '@Repository',
            'JpaRepository',
            'CrudRepository',
            '@Query',
            '@Modifying',
            'findBy', 'countBy', 'deleteBy', 'existsBy'
        ]

        # JPA 메서드명 패턴
        self.jpa_method_patterns = [
            r'(find|count|delete|exists)By([A-Z][a-zA-Z]*)',
            r'(find|count|delete)([A-Z][a-zA-Z]*)By([A-Z][a-zA-Z]*)',
            r'(find|count|delete)All',
            r'(find|count|delete)Top\d*By([A-Z][a-zA-Z]*)',
            r'(find|count|delete)First\d*By([A-Z][a-zA-Z]*)'
        ]

    def analyze_java_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Java 파일 분석 (MyBatis + JPA)

        Args:
            file_path: Java 파일 경로
            content: 파일 내용

        Returns:
            분석 결과 (method→query 매핑 포함)
        """
        try:
            result = {
                'file_path': file_path,
                'file_type': self._detect_file_type(content),
                'namespace': self._extract_namespace(content),
                'class_name': self._extract_class_name(content),
                'method_query_mappings': [],
                'entity_table_mappings': [],
                'query_table_mappings': []
            }

            if result['file_type'] == 'MYBATIS_MAPPER':
                result['method_query_mappings'] = self._analyze_mybatis_interface(content, result['namespace'], result['class_name'])
            elif result['file_type'] == 'JPA_REPOSITORY':
                result['method_query_mappings'] = self._analyze_jpa_repository(content, result['class_name'])
                result['entity_table_mappings'] = self._analyze_jpa_entity_mapping(content)
            elif result['file_type'] == 'JPA_ENTITY':
                result['entity_table_mappings'] = self._analyze_jpa_entity(content, result['class_name'])

            # 각 쿼리에서 테이블 정보 추출
            if result['method_query_mappings']:
                result['query_table_mappings'] = self._extract_tables_from_queries(result['method_query_mappings'])

            info(f"Java 파일 분석 완료 - 타입: {result['file_type']}, 매핑: {len(result['method_query_mappings'])}개")
            return result

        except Exception as e:
            handle_error(e, f"Java 파일 분석 실패: {file_path}")
            return {
                'file_path': file_path,
                'file_type': 'UNKNOWN',
                'error': str(e)
            }

    def _detect_file_type(self, content: str) -> str:
        """파일 타입 감지"""
        try:
            content_upper = content.upper()

            # MyBatis 체크
            if any(indicator.upper() in content_upper for indicator in self.mybatis_indicators):
                return 'MYBATIS_MAPPER'

            # JPA Repository 체크
            if any(indicator.upper() in content_upper for indicator in self.jpa_indicators):
                return 'JPA_REPOSITORY'

            # JPA Entity 체크
            if '@ENTITY' in content_upper or '@TABLE' in content_upper:
                return 'JPA_ENTITY'

            return 'JAVA_CLASS'

        except Exception as e:
            handle_error(e, "파일 타입 감지 실패")
            return 'UNKNOWN'

    def _extract_namespace(self, content: str) -> str:
        """네임스페이스(패키지) 추출"""
        try:
            package_match = re.search(r'package\s+([a-zA-Z0-9_.]+)\s*;', content)
            return package_match.group(1) if package_match else ""
        except Exception as e:
            handle_error(e, "네임스페이스 추출 실패")
            return ""

    def _extract_class_name(self, content: str) -> str:
        """클래스명 추출"""
        try:
            # interface 또는 class 선언에서 클래스명 추출
            class_match = re.search(r'(?:public\s+)?(?:interface|class)\s+([A-Za-z_][A-Za-z0-9_]*)', content)
            return class_match.group(1) if class_match else ""
        except Exception as e:
            handle_error(e, "클래스명 추출 실패")
            return ""

    def _analyze_mybatis_interface(self, content: str, namespace: str, class_name: str) -> List[Dict[str, Any]]:
        """MyBatis Mapper 인터페이스 분석"""
        try:
            mappings = []

            # 메서드 시그니처 패턴
            method_pattern = r'([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*;'
            methods = re.findall(method_pattern, content, re.MULTILINE)

            for return_type, method_name in methods:
                # 메서드명에서 쿼리 타입 추정
                query_type = self._infer_query_type_from_method_name(method_name)

                # XML에서 찾을 쿼리 ID (보통 메서드명과 일치)
                query_id = method_name

                # 관례적 매핑 (UserMapper → UserMapper.xml)
                xml_file_name = f"{class_name}.xml"

                mappings.append({
                    'method_name': method_name,
                    'return_type': return_type,
                    'query_id': query_id,
                    'query_type': query_type,
                    'xml_namespace': namespace,
                    'xml_file_name': xml_file_name,
                    'mapping_type': 'MYBATIS_CONVENTION',
                    'confidence': 0.8  # 관례적 연결
                })

            return mappings

        except Exception as e:
            handle_error(e, "MyBatis 인터페이스 분석 실패")
            return []

    def _analyze_jpa_repository(self, content: str, class_name: str) -> List[Dict[str, Any]]:
        """JPA Repository 분석"""
        try:
            mappings = []

            # 1. @Query 어노테이션이 있는 메서드 분석
            query_mappings = self._analyze_jpa_query_annotations(content)
            mappings.extend(query_mappings)

            # 2. 메서드명 기반 쿼리 분석 (Query by Method)
            method_mappings = self._analyze_jpa_method_queries(content, class_name)
            mappings.extend(method_mappings)

            return mappings

        except Exception as e:
            handle_error(e, "JPA Repository 분석 실패")
            return []

    def _analyze_jpa_query_annotations(self, content: str) -> List[Dict[str, Any]]:
        """@Query 어노테이션 분석"""
        try:
            mappings = []

            # @Query 패턴 (여러 줄 지원)
            query_pattern = r'@Query\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\'](?:\s*,\s*nativeQuery\s*=\s*(true|false))?\s*\)\s*(?:[^{};]*\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)'

            matches = re.findall(query_pattern, content, re.DOTALL | re.MULTILINE)

            for query_sql, native_query, method_name in matches:
                query_type = 'NATIVE_SQL' if native_query.lower() == 'true' else 'JPQL'

                mappings.append({
                    'method_name': method_name,
                    'query_sql': query_sql.strip(),
                    'query_type': query_type,
                    'mapping_type': 'JPA_ANNOTATION',
                    'confidence': 1.0  # 명시적 연결
                })

            return mappings

        except Exception as e:
            handle_error(e, "@Query 어노테이션 분석 실패")
            return []

    def _analyze_jpa_method_queries(self, content: str, class_name: str) -> List[Dict[str, Any]]:
        """JPA 메서드명 기반 쿼리 분석"""
        try:
            mappings = []

            # 메서드 시그니처 패턴
            method_pattern = r'([A-Za-z_<>?[\],\s]+)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*;'
            methods = re.findall(method_pattern, content, re.MULTILINE)

            for return_type, method_name in methods:
                # JPA 메서드명 패턴 매칭
                if self._is_jpa_query_method(method_name):
                    # 메서드명에서 엔티티명 추정
                    entity_name = self._extract_entity_from_repository(class_name)

                    # 생성될 쿼리 추정
                    estimated_query = self._generate_jpa_query_from_method(method_name, entity_name)

                    mappings.append({
                        'method_name': method_name,
                        'return_type': return_type.strip(),
                        'estimated_query': estimated_query,
                        'entity_name': entity_name,
                        'query_type': 'JPA_METHOD_QUERY',
                        'mapping_type': 'JPA_METHOD_CONVENTION',
                        'confidence': 0.7  # 추론적 연결
                    })

            return mappings

        except Exception as e:
            handle_error(e, "JPA 메서드 쿼리 분석 실패")
            return []

    def _analyze_jpa_entity(self, content: str, class_name: str) -> List[Dict[str, Any]]:
        """JPA Entity 분석"""
        try:
            mappings = []

            # @Table 어노테이션에서 테이블명 추출
            table_match = re.search(r'@Table\s*\(\s*name\s*=\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
            table_name = table_match.group(1) if table_match else self._camel_to_snake(class_name).upper()

            mappings.append({
                'entity_name': class_name,
                'table_name': table_name,
                'mapping_type': 'JPA_ENTITY_TABLE',
                'confidence': 1.0 if table_match else 0.8
            })

            # @Column 어노테이션 분석 (필드→컬럼 매핑)
            column_mappings = self._analyze_jpa_columns(content, table_name)
            mappings.extend(column_mappings)

            return mappings

        except Exception as e:
            handle_error(e, "JPA Entity 분석 실패")
            return []

    def _analyze_jpa_entity_mapping(self, content: str) -> List[Dict[str, Any]]:
        """JPA Repository에서 Entity 매핑 추출"""
        try:
            mappings = []

            # JpaRepository<Entity, ID> 패턴
            generic_pattern = r'extends\s+JpaRepository<\s*([A-Za-z_][A-Za-z0-9_]*)\s*,'
            match = re.search(generic_pattern, content)

            if match:
                entity_name = match.group(1)
                table_name = self._camel_to_snake(entity_name).upper()

                mappings.append({
                    'entity_name': entity_name,
                    'table_name': table_name,
                    'mapping_type': 'JPA_REPOSITORY_ENTITY',
                    'confidence': 0.7  # 추론적 연결
                })

            return mappings

        except Exception as e:
            handle_error(e, "JPA Entity 매핑 분석 실패")
            return []

    def _analyze_jpa_columns(self, content: str, table_name: str) -> List[Dict[str, Any]]:
        """JPA @Column 어노테이션 분석"""
        try:
            mappings = []

            # @Column 패턴
            column_pattern = r'@Column\s*\(\s*name\s*=\s*["\']([^"\']+)["\'][^)]*\)\s*(?:[^;]*\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*;'
            matches = re.findall(column_pattern, content, re.MULTILINE)

            for column_name, field_name in matches:
                mappings.append({
                    'entity_field': field_name,
                    'table_name': table_name,
                    'column_name': column_name,
                    'mapping_type': 'JPA_FIELD_COLUMN',
                    'confidence': 1.0  # 명시적 연결
                })

            return mappings

        except Exception as e:
            handle_error(e, "JPA 컬럼 분석 실패")
            return []

    def _infer_query_type_from_method_name(self, method_name: str) -> str:
        """메서드명에서 쿼리 타입 추정"""
        method_lower = method_name.lower()

        if method_lower.startswith(('select', 'find', 'get', 'list')):
            return 'SELECT'
        elif method_lower.startswith('insert'):
            return 'INSERT'
        elif method_lower.startswith('update'):
            return 'UPDATE'
        elif method_lower.startswith('delete'):
            return 'DELETE'
        elif method_lower.startswith('count'):
            return 'SELECT'  # COUNT 쿼리
        else:
            return 'UNKNOWN'

    def _is_jpa_query_method(self, method_name: str) -> bool:
        """JPA 쿼리 메서드인지 확인"""
        return any(re.match(pattern, method_name) for pattern in self.jpa_method_patterns)

    def _extract_entity_from_repository(self, repository_class_name: str) -> str:
        """Repository 클래스명에서 Entity명 추출"""
        # UserRepository → User
        if repository_class_name.endswith('Repository'):
            return repository_class_name[:-10]
        return repository_class_name

    def _generate_jpa_query_from_method(self, method_name: str, entity_name: str) -> str:
        """JPA 메서드명에서 쿼리 생성"""
        try:
            # 간단한 패턴만 처리
            if method_name.startswith('findBy'):
                field = method_name[6:]  # findBy 제거
                return f"SELECT e FROM {entity_name} e WHERE e.{self._camel_to_snake(field)} = ?"
            elif method_name.startswith('countBy'):
                field = method_name[7:]  # countBy 제거
                return f"SELECT COUNT(e) FROM {entity_name} e WHERE e.{self._camel_to_snake(field)} = ?"
            elif method_name.startswith('deleteBy'):
                field = method_name[8:]  # deleteBy 제거
                return f"DELETE FROM {entity_name} e WHERE e.{self._camel_to_snake(field)} = ?"
            elif method_name.startswith('findAll'):
                return f"SELECT e FROM {entity_name} e"
            else:
                return f"-- JPA method query: {method_name}"

        except Exception as e:
            handle_error(e, f"JPA 쿼리 생성 실패: {method_name}")
            return f"-- Error generating query for {method_name}"

    def _camel_to_snake(self, name: str) -> str:
        """CamelCase를 snake_case로 변환"""
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    def _extract_tables_from_queries(self, method_mappings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """매핑된 쿼리들에서 테이블 정보 추출"""
        try:
            from util.simple_relationship_analyzer import SimpleRelationshipAnalyzer

            analyzer = SimpleRelationshipAnalyzer()
            query_table_mappings = []

            for mapping in method_mappings:
                query_sql = mapping.get('query_sql') or mapping.get('estimated_query', '')

                if query_sql:
                    # 테이블 추출
                    tables = analyzer.extract_tables_from_sql(query_sql)

                    # 조인 관계 추출
                    join_relationships = analyzer.extract_join_relationships(query_sql, tables)

                    query_table_mappings.append({
                        'method_name': mapping['method_name'],
                        'query_sql': query_sql,
                        'tables': list(tables),
                        'join_relationships': join_relationships,
                        'mapping_type': mapping['mapping_type']
                    })

            return query_table_mappings

        except Exception as e:
            handle_error(e, "쿼리에서 테이블 추출 실패")
            return []