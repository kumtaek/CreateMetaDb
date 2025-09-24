"""
심플 쿼리 분석기 - 3단계 파이프라인
목표: 메소드→쿼리→테이블→조인조건 도출

1단계: 쿼리 추출 (JAVA/XML/JPA) → 딕셔너리 생성
2단계: 테이블 추출 (공통) → 테이블명과 별칭 딕셔너리
3단계: 조인관계 추출 (공통) → relationships 테이블 저장
"""

import re
import os
import zlib
import json
from typing import Dict, List, Set, Tuple, Any, Optional
from util import (
    info, error, warning, debug, handle_error,
    DatabaseUtils, ConfigUtils, PathUtils, HashUtils
)


class SimpleQueryAnalyzer:
    """심플 쿼리 분석기 - 3단계 파이프라인 구현"""

    def __init__(self, project_name: str, db_path: str):
        """초기화"""
        try:
            self.project_name = project_name
            self.db_utils = DatabaseUtils(db_path)
            self.config_utils = ConfigUtils()
            self.path_utils = PathUtils()
            self.hash_utils = HashUtils()

            # 오라클 키워드 로드
            self.oracle_keywords = self._load_oracle_keywords()

            # SQL 키워드 패턴 (대소문자 무관)
            self.sql_start_patterns = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'MERGE']

            info("심플 쿼리 분석기 초기화 완료")

        except Exception as e:
            handle_error(e, "심플 쿼리 분석기 초기화 실패")

    def _load_oracle_keywords(self) -> Set[str]:
        """오라클 키워드 로드 - YAML 파일에서 로드 (다른 파서와 통일)"""
        try:
            # USER RULES: 공통함수 사용, 하드코딩 금지
            config_path = self.path_utils.get_parser_config_path("oracle_sql")

            if not os.path.exists(config_path):
                handle_error(Exception(f"오라클 키워드 설정 파일 없음: {config_path}"), "오라클 키워드 파일 없음 - 2,3단계 키워드 체크 불가")
                return set()

            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            keywords = set()
            if isinstance(config, dict):
                # oracle_sql_keywords 하위의 모든 키워드들 수집
                for key, value in config.items():
                    if key.endswith('_keywords') or key.endswith('_functions'):
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                if isinstance(sub_value, list):
                                    keywords.update([kw.upper() for kw in sub_value])
                        elif isinstance(value, list):
                             keywords.update([kw.upper() for kw in value])

            debug(f"오라클 키워드 {len(keywords)}개 로드")
            return keywords

        except Exception as e:
            handle_error(e, f"오라클 키워드 로드 실패")
            return set()

    # ========== 1단계: 쿼리 추출 ==========

    def analyze_java_file(self, file_path: str, file_id: int) -> Dict[str, List[Dict]]:
        """Java 파일 분석 - 1단계 쿼리 추출"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            results = {
                'java_queries': [],
                'jpa_queries': [],
                'methods': []
            }

            # 메소드 추출
            methods = self._extract_java_methods(content)
            results['methods'] = methods

            # 각 메소드별 쿼리 추출
            for method in methods:
                method_name = method['name']
                method_content = method['content']

                # 1-1. Java 동적 쿼리 추출
                java_queries = self._extract_java_queries(method_content, method_name)
                results['java_queries'].extend(java_queries)

                # 1-2. JPA 쿼리 추출
                jpa_queries = self._extract_jpa_queries(method_content, method_name)
                results['jpa_queries'].extend(jpa_queries)

            info(f"Java 분석 완료: {file_path}, 메소드={len(methods)}, Java쿼리={len(results['java_queries'])}, JPA쿼리={len(results['jpa_queries'])}")
            return results

        except Exception as e:
            handle_error(e, f"Java 파일 분석 실패: {file_path}")
            return {'java_queries': [], 'jpa_queries': [], 'methods': []}

    def _extract_java_methods(self, content: str) -> List[Dict]:
        """Java 메소드 추출"""
        try:
            methods = []
            # 메소드 패턴: public/private/protected + 리턴타입 + 메소드명(파라미터) { ... }
            pattern = r'(public|private|protected)\s+[^{]+?(\w+)\s*\([^)]*\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'

            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                method_name = match.group(2)
                method_content = match.group(3)

                methods.append({
                    'name': method_name,
                    'content': method_content
                })

            return methods

        except Exception as e:
            handle_error(e, f"Java 메소드 추출 실패")
            return []

    def _extract_java_queries(self, method_content: str, method_name: str) -> List[Dict]:
        """Java 동적 쿼리 추출 - 문자열 변수 concatenation 분석"""
        try:
            queries = []

            # 문자열 변수 딕셔너리 구성
            string_vars = {}

            # 1. 문자열 상수 추출 (임의 변수명으로 저장)
            string_constants = re.findall(r'"([^"]*)"', method_content)
            for i, const in enumerate(string_constants):
                var_name = f"STRING_CONST_{i}"
                string_vars[var_name] = const.strip()

            # 2. 문자열 변수 할당 추출 (String var = "...";)
            var_pattern = r'String\s+(\w+)\s*=\s*"([^"]*)"'
            matches = re.finditer(var_pattern, method_content, re.IGNORECASE)
            for match in matches:
                var_name = match.group(1)
                var_value = match.group(2).strip()
                string_vars[var_name] = var_value

            # 3. 문자열 concatenation 추출 (var += "..."; var = var + "...";)
            concat_patterns = [
                r'(\w+)\s*\+=\s*"([^"]*)"',  # var += "..."
                r'(\w+)\s*=\s*\w+\s*\+\s*"([^"]*)"',  # var = var + "..."
            ]

            for pattern in concat_patterns:
                matches = re.finditer(pattern, method_content, re.IGNORECASE)
                for match in matches:
                    var_name = match.group(1)
                    append_value = match.group(2).strip()

                    if var_name in string_vars:
                        string_vars[var_name] += " " + append_value
                    else:
                        string_vars[var_name] = append_value

            # 4. StringBuilder 처리
            sb_pattern = r'StringBuilder\s+(\w+).*?\.append\("([^"]*)"\)'
            matches = re.finditer(sb_pattern, method_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                var_name = match.group(1)
                append_value = match.group(2).strip()

                if var_name in string_vars:
                    string_vars[var_name] += " " + append_value
                else:
                    string_vars[var_name] = append_value

            # 5. 쿼리 변수만 필터링 (SQL 키워드로 시작하는 것들)
            for var_name, var_content in string_vars.items():
                cleaned_content = var_content.strip()
                if self._is_sql_query(cleaned_content):
                    query_type = self._detect_query_type(cleaned_content)

                    queries.append({
                        'query_id': f"{method_name}_{var_name}",
                        'method_name': method_name,
                        'variable_name': var_name,
                        'sql_content': cleaned_content,
                        'query_type': query_type
                    })

            return queries

        except Exception as e:
            handle_error(e, f"Java 쿼리 추출 실패: {method_name}")
            return []

    def _extract_jpa_queries(self, method_content: str, method_name: str) -> List[Dict]:
        """JPA 쿼리 추출 - @Query(...) 괄호 안 쌍따옴표 문자열만 심플 추출"""
        try:
            queries = []

            # @Query(...) 패턴 찾기 - 괄호 안 모든 내용 추출 (멀티라인 포함)
            query_pattern = r'@Query\s*\(\s*([^)]+?)\s*\)'
            matches = re.finditer(query_pattern, method_content, re.DOTALL | re.IGNORECASE)

            for match in matches:
                query_annotation = match.group(1)

                # 심플 로직: 쌍따옴표 안 문자열만 추출, 나머지는 모두 제거
                string_parts = re.findall(r'"([^"]*)"', query_annotation, re.DOTALL)

                if string_parts:
                    # 모든 쌍따옴표 문자열을 공백으로 연결 (+ 연산 시뮬레이션)
                    full_query = ' '.join(part.strip() for part in string_parts).strip()

                    # 개행문자 정리
                    full_query = re.sub(r'\s+', ' ', full_query)

                    if self._is_sql_query(full_query):
                        query_type = self._detect_query_type(full_query)

                        queries.append({
                            'query_id': method_name,  # 더 심플하게 메소드명 그대로
                            'method_name': method_name,
                            'variable_name': method_name,
                            'sql_content': full_query,
                            'query_type': query_type
                        })

            return queries

        except Exception as e:
            handle_error(e, f"JPA 쿼리 추출 실패: {method_name}")
            return []

    def analyze_xml_file(self, file_path: str, file_id: int) -> Dict[str, List[Dict]]:
        """XML(MyBatis) 파일 분석 - 1단계 쿼리 추출"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            queries = []

            # MyBatis 쿼리 태그 패턴
            tag_patterns = [
                r'<select\s+id="([^"]+)"[^>]*>(.*?)</select>',
                r'<insert\s+id="([^"]+)"[^>]*>(.*?)</insert>',
                r'<update\s+id="([^"]+)"[^>]*>(.*?)</update>',
                r'<delete\s+id="([^"]+)"[^>]*>(.*?)</delete>',
            ]

            for pattern in tag_patterns:
                matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    query_id = match.group(1)
                    raw_content = match.group(2)

                    # 태그 제거 후 쿼리만 추출
                    sql_content = self._remove_mybatis_tags(raw_content)

                    if self._is_sql_query(sql_content):
                        query_type = self._detect_query_type(sql_content)

                        # MERGE 처리: insert/update 태그도 MERGE 쿼리가 될 수 있음
                        if 'MERGE' in sql_content.upper():
                            query_type = 'SQL_MERGE'

                        queries.append({
                            'query_id': query_id,
                            'method_name': query_id,  # XML에서는 query_id가 메소드명 역할
                            'variable_name': query_id,
                            'sql_content': sql_content,
                            'query_type': query_type
                        })

            info(f"XML 분석 완료: {file_path}, 쿼리={len(queries)}")
            return {'xml_queries': queries}

        except Exception as e:
            handle_error(e, f"XML 파일 분석 실패: {file_path}")
            return {'xml_queries': []}

    def _remove_mybatis_tags(self, content: str) -> str:
        """MyBatis 태그 제거 - 심플한 방식"""
        try:
            # 모든 XML 태그 제거 (주석도 제거)
            content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
            content = re.sub(r'<[^>]+>', ' ', content)

            # 여러 공백을 하나로 정리
            content = re.sub(r'\s+', ' ', content)

            return content.strip()

        except Exception as e:
            handle_error(e, f"MyBatis 태그 제거 실패")
            return content

    def _is_sql_query(self, content: str) -> bool:
        """SQL 쿼리인지 확인"""
        try:
            cleaned = content.strip().upper()
            return any(cleaned.startswith(keyword) for keyword in self.sql_start_patterns)
        except:
            return False

    def _detect_query_type(self, content: str) -> str:
        """쿼리 타입 감지"""
        try:
            cleaned = content.strip().upper()

            if cleaned.startswith('SELECT'):
                return 'SQL_SELECT'
            elif cleaned.startswith('INSERT'):
                return 'SQL_INSERT'
            elif cleaned.startswith('UPDATE'):
                return 'SQL_UPDATE'
            elif cleaned.startswith('DELETE'):
                return 'SQL_DELETE'
            elif cleaned.startswith('MERGE'):
                return 'SQL_MERGE'
            else:
                return 'SQL_SELECT'  # 기본값

        except:
            return 'SQL_SELECT'

    # ========== 공통 2,3단계 처리 ==========

    def process_query_common_stages(self, query_info: Dict, file_id: int) -> Dict:
        """공통 2,3단계 처리: 테이블 추출 → 조인관계 분석"""
        try:
            result = {
                'tables': [],
                'join_relationships': [],
                'use_table_relationships': []
            }

            sql_content = query_info['sql_content']
            query_id = query_info['query_id']

            # 2단계: 테이블 추출
            tables_and_aliases = self._extract_tables_stage2(sql_content)

            # 테이블 컴포넌트 등록 및 USE_TABLE 관계 생성
            for table_name, alias in tables_and_aliases.items():
                if not self._is_oracle_keyword(table_name):
                    # 테이블 컴포넌트 등록
                    table_id = self._register_table_component(table_name, file_id)

                    # USE_TABLE 관계 생성 (쿼리 → 테이블)
                    result['use_table_relationships'].append({
                        'src_name': query_id,
                        'dst_name': table_name,
                        'relationship_type': 'USE_TABLE',
                        'src_type': query_info['query_type'],
                        'dst_type': 'TABLE'
                    })

            # 3단계: 조인관계 추출
            join_relations = self._extract_joins_stage3(sql_content, tables_and_aliases)
            result['join_relationships'] = join_relations

            result['tables'] = list(tables_and_aliases.keys())

            return result

        except Exception as e:
            handle_error(e, f"공통 2,3단계 처리 실패: {query_info.get('query_id', 'UNKNOWN')}")
            return {'tables': [], 'join_relationships': [], 'use_table_relationships': []}

    def _extract_tables_stage2(self, sql_content: str) -> Dict[str, str]:
        """2단계: 테이블 추출 - 정규식 패턴 기반"""
        try:
            tables_and_aliases = {}

            # 주석 제거
            sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
            sql_content = re.sub(r'--.*', '', sql_content)

            # 테이블 추출 패턴들
            patterns = [
                r'FROM\s+([^,\s]+(?:\s+\w+)?)\s*(?:WHERE|GROUP|ORDER|UNION|HAVING|LIMIT|FETCH|FOR|INTERSECT|MINUS|EXCEPT|$)',
                r'FROM\s+([^,\s]+(?:\s+\w+)?)\s*,',
                r'UPDATE\s+([^,\s]+(?:\s+\w+)?)\s+SET',
                r'DELETE\s+FROM\s+([^,\s]+(?:\s+\w+)?)\s*(?:WHERE|$)',
                r'INSERT\s+INTO\s+([^,\s]+(?:\s+\w+)?)\s*[\(\s]',
                r'MERGE\s+INTO\s+([^,\s]+(?:\s+\w+)?)\s+USING',
                r'JOIN\s+([^,\s]+(?:\s+\w+)?)\s+ON',
                r'USING\s+([^,\s]+(?:\s+\w+)?)\s+ON',
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, sql_content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    table_part = match.group(1).strip()

                    # 테이블명과 별칭 분리
                    parts = table_part.split()
                    if len(parts) >= 2:
                        table_name = parts[0].strip()
                        alias = parts[1].strip()
                    else:
                        table_name = parts[0].strip()
                        alias = table_name

                    # 특수문자 제거
                    table_name = re.sub(r'[^\w]', '', table_name).upper()
                    alias = re.sub(r'[^\w]', '', alias).upper()

                    if table_name and not self._is_oracle_keyword(table_name):
                        tables_and_aliases[table_name] = alias

            return tables_and_aliases

        except Exception as e:
            handle_error(e, f"테이블 추출 실패")
            return {}

    def _extract_joins_stage3(self, sql_content: str, tables_and_aliases: Dict[str, str]) -> List[Dict]:
        """3단계: 조인관계 추출"""
        try:
            join_relationships = []

            # 조인 분석 패턴
            join_patterns = [
                # WHERE 절 암시적 조인
                (r'WHERE\s+.*?(\w+\.\w+)\s*=\s*(\w+\.\w+)', 'JOIN_IMPLICIT'),
                # JOIN ... ON 명시적 조인
                (r'JOIN\s+\w+\s+ON\s+(\w+\.\w+)\s*=\s*(\w+\.\w+)', 'JOIN_EXPLICIT'),
                # MERGE ... ON 조인
                (r'MERGE\s+.*?ON\s+\(([^)]+)\)', 'JOIN_MERGEON'),
            ]

            for pattern, join_type in join_patterns:
                matches = re.finditer(pattern, sql_content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    if join_type == 'JOIN_MERGEON':
                        # MERGE ON 절의 복잡한 조건 처리
                        join_condition = match.group(1)
                        join_parts = self._parse_merge_join_condition(join_condition)
                    else:
                        # 일반 조인 조건
                        left_col = match.group(1)
                        right_col = match.group(2)
                        join_parts = [(left_col, right_col)]

                    # 조인 관계 생성
                    for left, right in join_parts:
                        left_table, left_column = self._parse_column_reference(left, tables_and_aliases)
                        right_table, right_column = self._parse_column_reference(right, tables_and_aliases)

                        if left_table and right_table and left_column and right_column:
                            # 컬럼 컴포넌트 등록
                            left_col_id = self._register_column_component(left_table, left_column)
                            right_col_id = self._register_column_component(right_table, right_column)

                            if left_col_id and right_col_id:
                                join_relationships.append({
                                    'src_name': f"{left_table}.{left_column}",
                                    'dst_name': f"{right_table}.{right_column}",
                                    'relationship_type': join_type,
                                    'src_type': 'COLUMN',
                                    'dst_type': 'COLUMN'
                                })

            return join_relationships

        except Exception as e:
            handle_error(e, f"조인관계 추출 실패")
            return []

    def _parse_merge_join_condition(self, condition: str) -> List[Tuple[str, str]]:
        """MERGE JOIN 조건 파싱"""
        try:
            join_parts = []
            # 간단한 = 조건들만 추출
            eq_conditions = re.findall(r'(\w+\.\w+)\s*=\s*(\w+\.\w+)', condition)
            join_parts.extend(eq_conditions)
            return join_parts
        except:
            return []

    def _parse_column_reference(self, col_ref: str, aliases: Dict[str, str]) -> Tuple[str, str]:
        """컬럼 참조 파싱 (테이블.컬럼 또는 별칭.컬럼)"""
        try:
            if '.' in col_ref:
                parts = col_ref.split('.')
                table_or_alias = parts[0].strip().upper()
                column = parts[1].strip().upper()

                # 별칭을 실제 테이블명으로 변환
                actual_table = None
                for table_name, alias in aliases.items():
                    if alias == table_or_alias or table_name == table_or_alias:
                        actual_table = table_name
                        break

                return actual_table, column

            return None, None

        except:
            return None, None

    # ========== 데이터베이스 조작 ==========

    def _register_table_component(self, table_name: str, file_id: int) -> Optional[int]:
        """테이블 컴포넌트 등록 (INFERRED)"""
        try:
            # 기존 테이블 존재 확인
            existing = self.db_utils.execute_query(
                "SELECT component_id FROM components WHERE component_name = ? AND component_type = 'TABLE'",
                (table_name,)
            )

            if existing:
                return existing[0]['component_id']

            # INFERRED 테이블 등록
            component_id = self.db_utils.execute_query(
                """INSERT INTO components
                   (project_id, file_id, component_name, component_type, layer, hash_value)
                   VALUES (1, ?, ?, 'TABLE', 'DATABASE', ?)""",
                (file_id, table_name, 'INFERRED_TABLE'),
                return_id=True
            )

            debug(f"INFERRED 테이블 등록: {table_name}")
            return component_id

        except Exception as e:
            handle_error(e, f"테이블 컴포넌트 등록 실패: {table_name}")
            return None

    def _register_column_component(self, table_name: str, column_name: str) -> Optional[int]:
        """컬럼 컴포넌트 등록 (INFERRED)"""
        try:
            # 테이블 컴포넌트 ID 찾기
            table_result = self.db_utils.execute_query(
                "SELECT component_id FROM components WHERE component_name = ? AND component_type = 'TABLE'",
                (table_name,)
            )

            if not table_result:
                return None

            table_id = table_result[0]['component_id']

            # 기존 컬럼 존재 확인
            existing = self.db_utils.execute_query(
                "SELECT component_id FROM components WHERE component_name = ? AND component_type = 'COLUMN' AND parent_id = ?",
                (column_name, table_id)
            )

            if existing:
                return existing[0]['component_id']

            # INFERRED 컬럼 등록
            component_id = self.db_utils.execute_query(
                """INSERT INTO components
                   (project_id, file_id, component_name, component_type, parent_id, layer, hash_value)
                   VALUES (1, 1, ?, 'COLUMN', ?, 'DATABASE', ?)""",
                (column_name, table_id, 'INFERRED_COLUMN'),
                return_id=True
            )

            debug(f"INFERRED 컬럼 등록: {table_name}.{column_name}")
            return component_id

        except Exception as e:
            handle_error(e, f"컬럼 컴포넌트 등록 실패: {table_name}.{column_name}")
            return None

    def get_query_analysis_results(self, query_info: Dict) -> Dict:
        """쿼리 분석 결과 반환 - 데이터베이스 저장은 호출자에서 처리"""
        try:
            # 2,3단계 분석 실행
            analysis_result = self.process_query_common_stages(query_info)

            # 쿼리 정보와 분석 결과를 합쳐서 반환
            result = {
                'query_id': query_info['query_id'],
                'method_name': query_info['method_name'],
                'variable_name': query_info['variable_name'],
                'sql_content': query_info['sql_content'],
                'query_type': query_info['query_type'],
                'hash_value': self._calculate_hash(query_info['sql_content']),
                'tables': analysis_result['tables'],
                'join_relationships': analysis_result['join_relationships'],
                'use_table_relationships': analysis_result['use_table_relationships']
            }

            debug(f"쿼리 분석 완료: {query_info['query_id']}")
            return result

        except Exception as e:
            handle_error(e, f"쿼리 분석 실패: {query_info.get('query_id', 'UNKNOWN')}")
            return {}

    def save_relationships(self, relationships: List[Dict]) -> bool:
        """관계 데이터 저장"""
        try:
            for rel in relationships:
                # 컴포넌트 ID 찾기
                src_id = self._find_component_id(rel['src_name'], rel['src_type'])
                dst_id = self._find_component_id(rel['dst_name'], rel['dst_type'])

                if src_id and dst_id:
                    # 관계 중복 확인
                    existing = self.db_utils.execute_query(
                        "SELECT COUNT(*) as count FROM relationships WHERE src_id = ? AND dst_id = ? AND rel_type = ?",
                        (src_id, dst_id, rel['relationship_type'])
                    )

                    if existing[0]['count'] == 0:
                        self.db_utils.execute_query(
                            "INSERT INTO relationships (src_id, dst_id, rel_type, confidence) VALUES (?, ?, ?, 1.0)",
                            (src_id, dst_id, rel['relationship_type'])
                        )
                        debug(f"관계 저장: {rel['src_name']} -> {rel['dst_name']} ({rel['relationship_type']})")

            return True

        except Exception as e:
            handle_error(e, "관계 저장 실패")
            return False

    def _find_component_id(self, component_name: str, component_type: str) -> Optional[int]:
        """컴포넌트 ID 찾기"""
        try:
            result = self.db_utils.execute_query(
                "SELECT component_id FROM components WHERE component_name = ? AND component_type = ? LIMIT 1",
                (component_name, component_type)
            )
            return result[0]['component_id'] if result else None
        except:
            return None

    def _is_oracle_keyword(self, word: str) -> bool:
        """오라클 키워드 확인"""
        return word.upper() in self.oracle_keywords

    def _calculate_hash(self, content: str) -> str:
        """해시 계산 - USER RULES: 공통함수 사용"""
        return self.hash_utils.generate_content_hash(content)

    # ========== 메인 분석 함수 ==========

    def analyze_file(self, file_path: str, file_type: str, file_id: int) -> Dict:
        """파일 분석 - 3단계 파이프라인 실행"""
        try:
            info(f"파일 분석 시작: {file_path} ({file_type})")

            results = {
                'queries_processed': 0,
                'tables_found': 0,
                'relationships_created': 0
            }

            # 1단계: 파일 타입별 쿼리 추출
            if file_type.lower() == 'java':
                query_results = self.analyze_java_file(file_path, file_id)
                all_queries = query_results['java_queries'] + query_results['jpa_queries']
            elif file_type.lower() == 'xml':
                query_results = self.analyze_xml_file(file_path, file_id)
                all_queries = query_results['xml_queries']
            else:
                info(f"지원하지 않는 파일 타입: {file_type}")
                return results

            # 각 쿼리별로 2,3단계 공통 처리
            all_relationships = []

            for query_info in all_queries:
                # SqlContent에 쿼리 저장
                self.save_query_to_sqlcontent(query_info, file_id)

                # 2,3단계 공통 처리
                stage_results = self.process_query_common_stages(query_info, file_id)

                # 관계 수집
                all_relationships.extend(stage_results['use_table_relationships'])
                all_relationships.extend(stage_results['join_relationships'])

                results['queries_processed'] += 1
                results['tables_found'] += len(stage_results['tables'])

            # 관계 저장
            if all_relationships:
                self.save_relationships(all_relationships)
                results['relationships_created'] = len(all_relationships)

            info(f"파일 분석 완료: {file_path}, 쿼리={results['queries_processed']}, 관계={results['relationships_created']}")
            return results

        except Exception as e:
            handle_error(e, f"파일 분석 실패: {file_path}")
            return {'queries_processed': 0, 'tables_found': 0, 'relationships_created': 0}