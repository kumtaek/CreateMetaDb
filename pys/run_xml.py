import sys, os
sys.path.append(os.getcwd())
from parser.xml_parser import XmlParser
xp=XmlParser()
res=xp.extract_sql_queries_and_analyze_relationships('projects/sampleSrc/src/main/resources/mybatis/mapper/ProductMapper.xml')
for q in res['sql_queries']:
    if 'Advanced' in q['query_id']:
        print(q)
