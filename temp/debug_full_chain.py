import sqlite3

conn = sqlite3.connect('projects/sampleSrc/metadata.db')
cursor = conn.cursor()

print("=== 7. METHOD → SQL 관계 확인 ===")
cursor.execute("""
    SELECT 
        method.component_name as method_name,
        sql.component_name as sql_name,
        sql.component_type as sql_type
    FROM components method
    JOIN relationships r ON method.component_id = r.src_id AND r.rel_type = 'CALL_QUERY'
    JOIN components sql ON r.dst_id = sql.component_id
    WHERE method.component_type = 'METHOD'
    LIMIT 5
""")
method_sqls = cursor.fetchall()
for ms in method_sqls:
    print(f" METHOD: {ms[0]} → SQL: {ms[1]} ({ms[2]})")

print("\n=== 8. SQL → TABLE 관계 확인 ===")
cursor.execute("""
    SELECT 
        sql.component_name as sql_name,
        t.table_name
    FROM components sql
    JOIN relationships r ON sql.component_id = r.src_id AND r.rel_type = 'USE_TABLE'
    JOIN tables t ON r.dst_id = t.component_id
    WHERE sql.component_type LIKE 'SQL_%'
    LIMIT 5
""")
sql_tables = cursor.fetchall()
for st in sql_tables:
    print(f" SQL: {st[0]} → TABLE: {st[1]}")

print("\n=== 9. 완전한 체인 테스트 ===")
cursor.execute("""
    SELECT 
        api_url.component_name as api_name,
        method.component_name as method_name,
        sql.component_name as sql_name,
        t.table_name
    FROM components api_url
    JOIN relationships r1 ON api_url.component_id = r1.src_id AND r1.rel_type = 'CALL_METHOD'
    JOIN components method ON r1.dst_id = method.component_id
    JOIN relationships r2 ON method.component_id = r2.src_id AND r2.rel_type = 'CALL_QUERY'
    JOIN components sql ON r2.dst_id = sql.component_id
    LEFT JOIN relationships r3 ON sql.component_id = r3.src_id AND r3.rel_type = 'USE_TABLE'
    LEFT JOIN tables t ON r3.dst_id = t.component_id
    WHERE api_url.component_type = 'API_URL'
    LIMIT 3
""")
full_chains = cursor.fetchall()
for fc in full_chains:
    print(f" API: {fc[0]} → METHOD: {fc[1]} → SQL: {fc[2]} → TABLE: {fc[3] or 'None'}")

print("\n=== 10. JSP 파일 목록 ===")
cursor.execute('SELECT file_id, file_name FROM files WHERE file_type = "JSP"')
jsp_files = cursor.fetchall()
for jsp in jsp_files:
    print(f" JSP: {jsp[1]}, ID: {jsp[0]}")

conn.close()
