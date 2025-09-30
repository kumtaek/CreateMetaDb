"""
MapperIndexer - MyBatis XML에서 mapper namespace와 쿼리 id를 수집해
mapper_map(project_id, file_id, namespace, query_id, sql_component_id)에 저장.

정확 매칭 용도:
- Java 인터페이스/DAO의 FQN.method 와 mapper namespace.id 매칭으로
  METHOD → SQL_* (CALL_QUERY) 관계를 정밀하게 구성할 수 있도록 보조 데이터를 제공.
"""

import os
import re
import sqlite3
from typing import Optional
from util import DatabaseUtils, PathUtils, get_project_source_path, get_project_metadata_db_path, handle_error, info, warning, debug


class MapperIndexer:
    def __init__(self, project_name: str, conn: sqlite3.Connection):
        self.project_name = project_name
        self.conn = conn
        self.path_utils = PathUtils()
        self.project_src = get_project_source_path(project_name)
        self.db = DatabaseUtils(get_project_metadata_db_path(project_name))

    def run(self) -> int:
        try:
            count = 0
            for root, _, files in os.walk(self.project_src):
                for fn in files:
                    if not fn.lower().endswith('.xml'):
                        continue
                    full = os.path.join(root, fn)
                    try:
                        ns = self._extract_namespace(full)
                        if not ns:
                            continue
                        file_id = self._get_file_id(full)
                        if not file_id:
                            continue
                        for qid in self._extract_query_ids(full):
                            sql_comp_id = self._find_sql_component_id(file_id, qid)
                            if not sql_comp_id:
                                continue
                            self._upsert_mapper_map(file_id, ns, qid, sql_comp_id)
                            count += 1
                    except Exception as e:
                        handle_error(e, f"Mapper XML 처리 실패: {full}")
            info(f"mapper_map 저장: {count}건")
            return count
        except Exception as e:
            handle_error(e, "MapperIndexer 실행 실패")
            return 0

    def _get_file_id(self, full_path: str) -> Optional[int]:
        rel = self.path_utils.get_relative_path(full_path, self.project_src)
        rel_unix = self.path_utils.normalize_path_separator(rel, 'unix')
        dir_path = os.path.dirname(rel_unix) if rel_unix else ''
        if dir_path in ('', '.'):
            dir_path = ''
        file_name = os.path.basename(rel_unix)
        row = self.db.execute_query(
            "SELECT file_id FROM files WHERE project_id=(SELECT project_id FROM projects WHERE project_name=?) AND file_path=? AND file_name=? AND del_yn='N'",
            (self.project_name, dir_path, file_name),
            conn=self.conn,
        )
        return row[0]['file_id'] if row else None

    def _extract_namespace(self, full_path: str) -> Optional[str]:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        m = re.search(r'<\s*mapper\s+namespace\s*=\s*"([^"]+)"', content)
        return m.group(1).strip() if m else None

    def _extract_query_ids(self, full_path: str):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ids = set()
        for tag in ['select', 'insert', 'update', 'delete']:
            for m in re.finditer(rf'<\s*{tag}\s+id\s*=\s*"([^"]+)"', content, re.IGNORECASE):
                ids.add(m.group(1).strip())
        return ids

    def _find_sql_component_id(self, file_id: int, query_id: str) -> Optional[int]:
        row = self.db.execute_query(
            "SELECT component_id FROM components WHERE file_id=? AND component_name=? AND component_type LIKE 'SQL_%' AND del_yn='N' LIMIT 1",
            (file_id, query_id),
            conn=self.conn,
        )
        return row[0]['component_id'] if row else None

    def _upsert_mapper_map(self, file_id: int, namespace: str, query_id: str, sql_component_id: int) -> None:
        project_id = self.db.get_project_id(self.project_name, self.conn)
        data = {
            'project_id': project_id,
            'file_id': file_id,
            'namespace': namespace,
            'query_id': query_id,
            'sql_component_id': sql_component_id,
            'del_yn': 'N'
        }
        self.db.insert_or_replace_with_id('mapper_map', data, conn=self.conn)


def index_mappers(project_name: str, conn: sqlite3.Connection) -> int:
    return MapperIndexer(project_name, conn).run()

