"""Relationship Builder

Clean, cross?몆latform safe relationship builder used by the pipeline.
Creates precise relationships first (controller_api_map, mapper_map), then
optionally runs lightweight fallbacks. Kept concise for reliability.
"""

from __future__ import annotations

from typing import Dict, Optional
import sqlite3

from util import (
    DatabaseUtils, PathUtils, app_logger, info, error, debug, warning, handle_error
)


class RelationshipBuilder:
    """Builds relationships among components for a given project."""

    def __init__(self, project_name: str, project_id: int, conn: sqlite3.Connection):
        self.project_name = project_name
        self.project_id = project_id
        self.conn = conn
        self.path_utils = PathUtils()
        # Use actual metadata DB path for utility queries (e.g., table_exists)
        self.db_utils = DatabaseUtils(self.path_utils.get_project_metadata_db_path(project_name))

        self.stats: Dict[str, int] = {
            'method_query_relationships': 0,
            'frontend_api_relationships': 0,
            'api_method_relationships': 0,
            'query_table_relationships': 0,
            'table_join_relationships': 0,
            'entity_table_relationships': 0,
            'total_relationships': 0,
        }

    def build_all_relationships(self) -> Dict[str, int]:
        """Run precise builders first, then fallbacks; return stats."""
        try:
            info("Relationship build start")

            # 0) Optional: index MyBatis mapper namespace/id map
            try:
                from util.mapper_indexer import index_mappers
                index_mappers(self.project_name, self.conn)
            except Exception:
                warning("mapper_map indexing warning: continue")

            # 1) Precise builders
            self._build_api_method_from_file_id()
            self._build_method_query_relationships_from_mapper_map()
            self._build_mybatis_fqmn_relationships()

            # 2) Conservative fallbacks
            self._build_frontend_api_relationships()
            self._build_method_query_by_name_fallback()

            # 3) Analyze SQL contents for tables/joins (SqlContent.db)
            try:
                from util.common_sql_processor import CommonSqlAnalyzer
                CommonSqlAnalyzer(self.project_name).analyze_all_queries()
            except Exception:
                warning("CommonSqlAnalyzer analyze_all_queries warning: continue")




            self.stats['total_relationships'] = sum(
                v for k, v in self.stats.items() if k != 'total_relationships'
            )
            info(f"Relationship build done: total={self.stats['total_relationships']}")
            return self.stats
        except Exception as e:
            handle_error(e, "Relationship build failed")
            return self.stats

    # ===== Precise builders =====

    def _build_api_method_from_file_id(self) -> None:
        """Create API_URL → METHOD (CALL_METHOD) using file_id based matching."""
        try:
            cur = self.conn.cursor()
            rows = cur.execute(
                """
                SELECT api.component_id AS api_id,
                       method.component_id AS method_id
                  FROM components api
                  JOIN components method
                    ON api.file_id = method.file_id
                 WHERE api.project_id = ?
                   AND api.component_type = 'API_URL'
                   AND method.component_type = 'METHOD'
                   AND api.del_yn = 'N'
                   AND method.del_yn = 'N'
                """,
                (self.project_id,),
            ).fetchall()

            created = 0
            for api_id, method_id in rows:
                self._insert_relationship(api_id, method_id, 'CALL_METHOD')
                created += 1

            self.stats['api_method_relationships'] += created
            info(f"API_URL→METHOD via file_id: {created}")
        except Exception as e:
            handle_error(e, "file_id based API→METHOD failed")

    def _build_method_query_relationships_from_mapper_map(self) -> None:
        """Create METHOD → SQL_* (CALL_QUERY) using mapper_map (namespace+id).
        Adds a fuzzy fallback when strict class_name match fails.
        """
        try:
            # mapper_map이 없는 스키마에서는 스킵
            if not self.db_utils.table_exists('mapper_map'):
                info("mapper_map 없음: METHOD→SQL 정밀 매칭 스킵")
                return
            cur = self.conn.cursor()
            rows = cur.execute(
                """
                SELECT mm.namespace, mm.query_id, mm.sql_component_id
                  FROM mapper_map mm
                  JOIN components sc ON sc.component_id = mm.sql_component_id
                 WHERE sc.component_type LIKE 'SQL_%'
                   AND mm.project_id = ?
                   AND mm.del_yn='N'
                """,
                (self.project_id,),
            ).fetchall()

            created = 0
            for namespace, query_id, sql_comp_id in rows:
                base_class = namespace.split('.')[-1]
                method_name = query_id

                # 1) strict match: class == namespace tail, method == id
                m = cur.execute(
                    """
                    SELECT c.component_id
                      FROM components c
                 LEFT JOIN classes cl ON cl.class_id = c.parent_id
                     WHERE c.component_type='METHOD'
                       AND c.component_name = ?
                       AND cl.class_name = ?
                       AND c.del_yn='N'
                     LIMIT 1
                    """,
                    (method_name, base_class),
                ).fetchone()

                # 2) fuzzy class: allow class names ending with base_class (e.g., UserMapperImpl)
                if not m:
                    m = cur.execute(
                        """
                        SELECT c.component_id
                          FROM components c
                     LEFT JOIN classes cl ON cl.class_id = c.parent_id
                         WHERE c.project_id = ?
                           AND c.component_type='METHOD'
                           AND c.component_name = ?
                           AND cl.class_name LIKE '%' || ?
                           AND c.del_yn='N'
                      ORDER BY CASE WHEN cl.class_name LIKE '%Repository%' THEN 0
                                    WHEN cl.class_name LIKE '%Dao%' THEN 1
                                    WHEN cl.class_name LIKE '%Mapper%' THEN 2
                                    ELSE 3 END,
                               c.component_id ASC
                         LIMIT 1
                        """,
                        (self.project_id, method_name, base_class),
                    ).fetchone()

                if not m:
                    continue
                self._insert_relationship(m[0], sql_comp_id, 'CALL_QUERY')
                created += 1

            self.stats['method_query_relationships'] += created
            info(f"MyBatis namespace METHOD?뭆QL: {created}")
        except Exception as e:
            handle_error(e, "mapper_map based METHOD?뭆QL failed")

    # ===== Fallback builders =====

    def _build_frontend_api_relationships(self) -> None:
        """Map API_URL→METHOD via conservative heuristics.
        - Only accept "HTTP:methodName" (skip URL:HTTP names).
        - Prefer classes with 'Controller' in name.
        """
        try:
            cur = self.conn.cursor()
            rows = cur.execute(
                """
                SELECT component_id, component_name
                  FROM components
                 WHERE project_id = ?
                   AND component_type = 'API_URL'
                   AND del_yn = 'N'
                """,
                (self.project_id,),
            ).fetchall()

            created = 0
            verbs = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'}
            for api_id, comp_name in rows:
                if ':' not in comp_name:
                    continue
                left, right = comp_name.split(':', 1)
                # Only consider HTTP:methodName pattern
                if left.upper() not in verbs:
                    continue
                method = right.strip()
                # basic sanity for method identifier (exclude likely URL parts or all-caps tokens)
                if not method or '/' in method or method.strip() == method.upper():
                    continue

                m = cur.execute(
                    """
                    SELECT c.component_id
                      FROM components c
                 LEFT JOIN classes cl ON cl.class_id = c.parent_id
                     WHERE c.project_id = ?
                       AND c.component_type='METHOD'
                       AND c.component_name = ?
                       AND c.del_yn='N'
                  ORDER BY CASE WHEN cl.class_name LIKE '%Controller%' THEN 0 ELSE 1 END,
                           c.component_id ASC
                     LIMIT 1
                    """,
                    (self.project_id, method),
                ).fetchone()
                if not m:
                    continue
                self._insert_relationship(api_id, m[0], 'CALL_METHOD')
                created += 1

            self.stats['frontend_api_relationships'] += created
            info(f"Frontend API fallback CALL_METHOD: {created}")
        except Exception as e:
            handle_error(e, "frontend API fallback failed")

    # ===== DB helpers =====

    def _insert_relationship(self, src_id: int, dst_id: int, rel_type: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO relationships
                (src_id, dst_id, rel_type, confidence, del_yn)
            VALUES (?, ?, ?, 1.0, 'N')
            """,
            (src_id, dst_id, rel_type),
        )
        self.conn.commit()


    def _build_mybatis_fqmn_relationships(self) -> None:
        """Map METHOD to SQL_* using MyBatis FQMN (Fully Qualified Method Name) matching.
        
        Java에서 파싱한 MyBatis FQMN과 SQL component_name을 매칭하여 CALL_QUERY 관계 생성
        """
        try:
            cur = self.conn.cursor()
            
            # 1. Java METHOD 조회
            java_methods = cur.execute(
                """
                SELECT c.component_id, c.component_name, c.file_id
                  FROM components c
                  JOIN classes cl ON cl.class_id = c.parent_id
                 WHERE c.project_id = ?
                   AND c.component_type = 'METHOD'
                   AND c.del_yn = 'N'
                """,
                (self.project_id,),
            ).fetchall()

            created = 0
            
            # 2. Java 파일별로 한 번씩만 파싱 (중복 제거)
            java_files = set(file_id for _, _, file_id in java_methods)
            debug(f"파싱할 Java 파일 수: {len(java_files)}")
            
            for file_id in java_files:
                # 3. 해당 Java 파일에서 메소드별 MyBatis FQMN 추출
                method_fqmn_map = self._extract_mybatis_calls_from_java_file(file_id)
                debug(f"File {file_id}에서 추출된 메소드별 FQMN: {method_fqmn_map}")
                
                # 4. 해당 파일의 METHOD들 조회
                file_methods = [m for m in java_methods if m[2] == file_id]
                
                for method_id, method_name, _ in file_methods:
                    # 5. 해당 메소드의 FQMN들 조회
                    if method_name in method_fqmn_map:
                        fqmn_list = method_fqmn_map[method_name]
                        
                        for fqmn in fqmn_list:
                            # 6. FQMN과 일치하는 SQL 컴포넌트 찾기
                            sql_component = cur.execute(
                                """
                                SELECT component_id
                                  FROM components
                                 WHERE project_id = ?
                                   AND component_type LIKE 'SQL_%'
                                   AND component_name = ?
                                   AND del_yn = 'N'
                                 LIMIT 1
                                """,
                                (self.project_id, fqmn),
                            ).fetchone()
                            
                            if sql_component:
                                self._insert_relationship(method_id, sql_component[0], 'CALL_QUERY')
                                created += 1
                                debug(f"정확한 MyBatis FQMN 매칭: {method_name} → {fqmn}")

            self.stats['method_query_relationships'] += created
            info(f"MyBatis FQMN CALL_QUERY: {created}")
        except Exception as e:
            handle_error(e, "MyBatis FQMN relationships failed")

    def _extract_mybatis_calls_from_java_file(self, file_id: int) -> Dict[str, List[str]]:
        """Java 파일에서 메소드별 MyBatis 호출 패턴 파싱하여 FQMN 추출
        
        Returns:
            Dict[str, List[str]]: {method_name: [fqmn1, fqmn2, ...]}
        """
        try:
            import re
            import os
            
            # 1. file_id로 실제 Java 파일 경로 조회
            cur = self.conn.cursor()
            file_info = cur.execute(
                """
                SELECT file_path, file_name 
                FROM files 
                WHERE file_id = ? AND del_yn = 'N'
                """,
                (file_id,)
            ).fetchone()
            
            if not file_info:
                debug(f"File not found for file_id: {file_id}")
                return {}
                
            file_path, file_name = file_info
            full_path = os.path.join(self.path_utils.get_project_src_path(self.project_name), file_path, file_name)
            
            if not os.path.exists(full_path):
                debug(f"Java file not found: {full_path}")
                return {}
            
            # 2. Java 파일 내용 읽기
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                java_content = f.read()
            
            # 3. 메소드별 MyBatis 호출 패턴 파싱
            method_fqmn_map = {}
            
            # 3-1. Import 문에서 Mapper 클래스 네임스페이스 추출
            mapper_namespaces = self._extract_mapper_namespaces(java_content)
            
            # 3-2. @Autowired로 주입된 Mapper 변수들 추출
            mapper_variables = self._extract_mapper_variables(java_content)
            
            # 3-3. 메소드별로 MyBatis 호출 추출
            method_calls = self._extract_method_mybatis_calls(java_content, mapper_variables)
            
            # 3-4. 메소드별 FQMN 조합 생성
            for method_name, calls in method_calls.items():
                fqmn_list = []
                for var_name, call_method in calls:
                    if var_name in mapper_variables:
                        # mapper_variables에서 클래스명을 가져와서 mapper_namespaces에서 실제 네임스페이스 조회
                        class_name = mapper_variables[var_name]
                        if class_name in mapper_namespaces:
                            namespace = mapper_namespaces[class_name]
                            fqmn = f"{namespace}.{call_method}"
                            fqmn_list.append(fqmn)
                            debug(f"Method {method_name}: {var_name}.{call_method} → {fqmn}")
                        else:
                            debug(f"Namespace not found for class: {class_name}")
                method_fqmn_map[method_name] = fqmn_list
            
            return method_fqmn_map
            
        except Exception as e:
            handle_error(e, f"MyBatis calls extraction failed for file_id: {file_id}")
            return {}
    
    def _extract_mapper_namespaces(self, java_content: str) -> Dict[str, str]:
        """Import 문에서 Mapper 클래스 네임스페이스 추출"""
        try:
            import re
            namespaces = {}
            
            # import com.example.mapper.UserMapper; 패턴
            import_pattern = r'import\s+([a-zA-Z0-9_.]+\.([A-Z][a-zA-Z0-9]*Mapper))\s*;'
            matches = re.findall(import_pattern, java_content)
            
            for full_namespace, class_name in matches:
                namespaces[class_name] = full_namespace
                debug(f"Mapper namespace: {class_name} → {full_namespace}")
            
            return namespaces
        except Exception as e:
            handle_error(e, "Mapper namespace extraction failed")
            return {}
    
    def _extract_mapper_variables(self, java_content: str) -> Dict[str, str]:
        """@Autowired로 주입된 Mapper 변수들 추출"""
        try:
            import re
            variables = {}
            
            # @Autowired private UserMapper userMapper; 패턴
            autowired_pattern = r'@Autowired\s+private\s+([A-Z][a-zA-Z0-9]*Mapper)\s+([a-zA-Z][a-zA-Z0-9]*)\s*;'
            matches = re.findall(autowired_pattern, java_content)
            
            for class_name, var_name in matches:
                variables[var_name] = class_name
                debug(f"Mapper variable: {var_name} → {class_name}")
            
            return variables
        except Exception as e:
            handle_error(e, "Mapper variable extraction failed")
            return {}
    
    def _extract_method_mybatis_calls(self, java_content: str, mapper_variables: Dict[str, str]) -> Dict[str, List[Tuple[str, str]]]:
        """메소드별 MyBatis 호출 패턴 추출"""
        try:
            import re
            method_calls = {}
            
            # 메소드 정의 패턴: public ReturnType methodName(...) {
            method_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*[a-zA-Z_<>?[\],\s]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{'
            
            # 메소드별로 내용 추출
            for match in re.finditer(method_pattern, java_content):
                method_name = match.group(1)
                method_start = match.start()
                
                # 메소드 끝 찾기 (중괄호 매칭)
                brace_count = 0
                method_end = method_start
                for i, char in enumerate(java_content[method_start:], method_start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            method_end = i + 1
                            break
                
                # 메소드 내용 추출
                method_content = java_content[method_start:method_end]
                
                # 해당 메소드에서 MyBatis 호출 추출
                calls = []
                for var_name in mapper_variables.keys():
                    call_pattern = rf'{var_name}\.([a-zA-Z][a-zA-Z0-9]*)\s*\('
                    matches = re.findall(call_pattern, method_content)
                    
                    for call_method in matches:
                        calls.append((var_name, call_method))
                        debug(f"Method {method_name}: {var_name}.{call_method}()")
                
                if calls:
                    method_calls[method_name] = calls
            
            return method_calls
        except Exception as e:
            handle_error(e, "Method MyBatis call extraction failed")
            return {}

    def _build_method_query_by_name_fallback(self) -> None:
        """Map METHOD to SQL_* by exact name match (safe heuristic).
        Uses common MyBatis id == method_name convention.
        """
        try:
            cur = self.conn.cursor()
            rows = cur.execute(
                """
                SELECT component_id, component_name
                  FROM components
                 WHERE project_id = ?
                   AND component_type = 'METHOD'
                   AND del_yn='N'
                """,
                (self.project_id,),
            ).fetchall()

            created = 0
            for method_id, method_name in rows:
                sc = cur.execute(
                    """
                    SELECT component_id
                      FROM components
                     WHERE project_id = ?
                       AND component_type LIKE 'SQL_%'
                       AND component_name = ?
                       AND del_yn='N'
                     LIMIT 1
                    """,
                    (self.project_id, method_name),
                ).fetchone()
                if not sc:
                    continue
                self._insert_relationship(method_id, sc[0], 'CALL_QUERY')
                created += 1

            self.stats['method_query_relationships'] += created
            info(f"Method→SQL name fallback CALL_QUERY: {created}")
        except Exception as e:
            handle_error(e, "method→SQL name fallback failed")


# ===== Backfill entry (kept for callers) =====

def execute_db_relationship_backfill(project_name: str, conn: sqlite3.Connection) -> Dict[str, int]:
    """Create relationships from existing DB data (backfill, lightweight)."""
    stats = {"CALL_API": 0, "CALL_METHOD": 0, "CALL_QUERY": 0, "USE_TABLE": 0}
    try:
        # Intentionally minimal: precise builders run in RelationshipBuilder.
        return stats
    except Exception as e:
        handle_error(e, "DB relationship backfill failed")
        return stats
