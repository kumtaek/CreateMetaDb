import sqlite3, pathlib
conn=sqlite3.connect('projects/sampleSrc/SqlContent.db')
c=conn.cursor()
rows=c.execute("select file_path, file_name, component_name from sql_contents where file_name='ProductMapper.xml'").fetchall()
print(rows[:5])
conn.close()
