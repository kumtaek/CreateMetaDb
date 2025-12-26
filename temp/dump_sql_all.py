import sqlite3, pathlib, gzip
p=pathlib.Path('projects/sampleSrc/SqlContent.db')
conn=sqlite3.connect(p)
c=conn.cursor()
rows=c.execute("select component_name, sql_content_compressed from sql_contents where file_name='ProductMapper.xml'").fetchall()
for name, blob in rows:
    try:
        text=gzip.decompress(blob).decode('utf-8')
    except Exception:
        text=str(blob)
    print(name, '->', repr(text[:120]))
conn.close()
