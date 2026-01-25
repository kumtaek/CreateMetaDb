import os
import sqlite3
import json
from typing import Dict, Any

BASE = os.path.join('projects', 'sampleSrc')
META_DB = os.path.join(BASE, 'metadata.db')
SQL_DB = os.path.join(BASE, 'SqlContent.db')


def query_one(conn: sqlite3.Connection, sql: str, params=()) -> int:
    cur = conn.execute(sql, params)
    row = cur.fetchone()
    return int(row[0] or 0)


def collect_metrics() -> Dict[str, Any]:
    metrics: Dict[str, Any] = {}
    if not os.path.exists(META_DB):
        raise SystemExit(f"Meta DB not found: {META_DB}")
    if not os.path.exists(SQL_DB):
        raise SystemExit(f"SqlContent DB not found: {SQL_DB}")

    with sqlite3.connect(META_DB) as mconn:
        mconn.row_factory = sqlite3.Row
        metrics['files'] = query_one(mconn, "SELECT COUNT(*) FROM files WHERE del_yn='N'")
        metrics['classes'] = query_one(mconn, "SELECT COUNT(*) FROM classes WHERE del_yn='N'")
        metrics['components'] = query_one(mconn, "SELECT COUNT(*) FROM components WHERE del_yn='N'")

        # Relationships
        rel_total = query_one(mconn, "SELECT COUNT(*) FROM relationships WHERE del_yn='N'")
        metrics['relationships_total'] = rel_total

        def rel_count(t: str) -> int:
            return query_one(mconn, "SELECT COUNT(*) FROM relationships WHERE del_yn='N' AND rel_type=?", (t,))

        metrics['rel_CALL_METHOD'] = rel_count('CALL_METHOD')
        metrics['rel_CALL_QUERY'] = rel_count('CALL_QUERY')
        metrics['rel_USE_TABLE'] = rel_count('USE_TABLE')
        metrics['rel_JOIN_EXPLICIT'] = rel_count('JOIN_EXPLICIT')
        metrics['rel_JOIN_EXPLICIT_OUTER'] = rel_count('JOIN_EXPLICIT_OUTER')
        metrics['rel_JOIN_EXPLICIT_FULL_OUTER'] = rel_count('JOIN_EXPLICIT_FULL_OUTER')
        metrics['rel_JOIN_IMPLICIT'] = rel_count('JOIN_IMPLICIT')
        metrics['rel_JOIN_IMPLICIT_OUTER'] = rel_count('JOIN_IMPLICIT_OUTER')
        metrics['rel_JOIN_MERGEON'] = rel_count('JOIN_MERGEON')
        metrics['rel_JOIN_MERGE'] = rel_count('JOIN_MERGE')
        metrics['rel_USE_COLUMN'] = rel_count('USE_COLUMN')

        # Component by type
        def comp_count(t: str) -> int:
            return query_one(mconn, "SELECT COUNT(*) FROM components WHERE del_yn='N' AND component_type=?", (t,))

        metrics['comp_API_URL'] = comp_count('API_URL')
        metrics['comp_METHOD'] = comp_count('METHOD')
        metrics['comp_TABLE'] = comp_count('TABLE')
        metrics['comp_COLUMN'] = comp_count('COLUMN')

    with sqlite3.connect(SQL_DB) as sconn:
        sconn.row_factory = sqlite3.Row
        metrics['sql_total'] = query_one(sconn, "SELECT COUNT(*) FROM sql_contents WHERE del_yn='N'")

    return metrics


def main():
    metrics = collect_metrics()
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
