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
        self.db_utils = DatabaseUtils(None)

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
            self._build_api_method_from_controller_map()
            self._build_method_query_relationships_from_mapper_map()

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

    def _build_api_method_from_controller_map(self) -> None:
        """Create API_URL ??METHOD (CALL_METHOD) using controller_api_map."""
        try:
            cur = self.conn.cursor()
            rows = cur.execute(
                """
                SELECT api.component_id AS api_id,
                       m.component_id   AS method_id
                  FROM controller_api_map cam
                  JOIN components api
                    ON api.component_type = 'API_URL'
                   AND api.hash_value = cam.identity_hash
                   AND api.del_yn = 'N'
                  JOIN components m
                    ON m.component_type = 'METHOD'
                   AND m.del_yn = 'N'
                  JOIN classes cl
                    ON cl.class_id = m.parent_id
                 WHERE cam.project_id = ?
                   AND cam.del_yn = 'N'
                   AND cl.class_name = cam.class_name
                   AND m.component_name = cam.method_name
                """,
                (self.project_id,),
            ).fetchall()

            created = 0
            for api_id, method_id in rows:
                self._insert_relationship(api_id, method_id, 'CALL_METHOD')
                created += 1

            self.stats['api_method_relationships'] += created
            info(f"API_URL?묺ETHOD via controller_api_map: {created}")
        except Exception as e:
            handle_error(e, "controller_api_map based API?묺ETHOD failed")

    def _build_method_query_relationships_from_mapper_map(self) -> None:
        """Create METHOD → SQL_* (CALL_QUERY) using mapper_map (namespace+id).
        Adds a fuzzy fallback when strict class_name match fails.
        """
        try:
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
                (src_id, dst_id, rel_type, confidence, has_error, error_message, del_yn)
            VALUES (?, ?, ?, 1.0, 'N', NULL, 'N')
            """,
            (src_id, dst_id, rel_type),
        )
        self.conn.commit()

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
