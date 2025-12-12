import sys, os, inspect, textwrap
sys.path.append(os.getcwd())
import parser.xml_parser as xp
print(textwrap.dedent(inspect.getsource(xp.XmlParser.extract_sql_queries_and_analyze_relationships)))
