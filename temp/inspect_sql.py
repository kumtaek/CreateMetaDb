import sys, os, re, html
sys.path.append(os.getcwd())
from parser.xml_parser import XmlParser
xp=XmlParser()
xml_file='projects/sampleSrc/src/main/resources/mybatis/mapper/ProductMapper.xml'
with open(xml_file, 'r', encoding='utf-8', errors='ignore') as f:
    xml_content=f.read()
pattern = re.compile(r'<(select|insert|update|delete|merge)\s+id="([^\"]+)"[^>]*>(.*?)</\1>', re.DOTALL | re.IGNORECASE)
for match in pattern.finditer(xml_content):
    tag=match.group(1).lower(); qid=match.group(2); inner=match.group(3)
    if 'Advanced' in qid:
        print('qid', qid)
        print('inner length', len(inner))
        print('inner snippet', inner[:200])
        inner2 = xp._approximate_mybatis_dynamic_tags(inner)
        print('after approx length', len(inner2), 'snippet', inner2[:200])
        cleaned = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', inner2, flags=re.DOTALL)
        cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
        cleaned = html.unescape(cleaned)
        sql_content = ' '.join(cleaned.split())
        print('sql_content repr', repr(sql_content), 'len', len(sql_content))
