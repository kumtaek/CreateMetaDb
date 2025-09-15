"""
리포트 HTML 템플릿 관리
- CallChain Report 템플릿
- ERD Report 템플릿
"""

from typing import Dict, List, Any


class ReportTemplates:
    """리포트 템플릿 관리 클래스"""
    
    def get_callchain_template(self, project_name: str, timestamp: str, stats: Dict[str, int], 
                              chain_data: List[Dict[str, Any]], filter_options: Dict[str, List[str]]) -> str:
        """CallChain Report HTML 템플릿 생성"""
        
        # 통계 카드 HTML 생성
        stats_html = self._generate_stats_html(stats)
        
        # 필터링 옵션 HTML 생성
        filter_html = self._generate_filter_html(filter_options)
        
        # 연계 체인 테이블 HTML 생성
        table_html = self._generate_chain_table_html(chain_data)
        
        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CallChain Report - {project_name}</title>
    <style>
        {self._get_callchain_css()}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>CallChain Report</h1>
            <div class="subtitle">Method-Class-Method-XML-Query-Table 연계 정보</div>
            <div class="subtitle">프로젝트: {project_name} | 생성일시: {timestamp}</div>
        </div>
        {stats_html}
        <div class="content">
            <div class="section">
                <h2>필터 및 검색</h2>
                {filter_html}
            </div>
            <div class="section">
                <h2>완전한 연계 경로</h2>
                <div class="table-container">
                    <table id="chainTable">
                        <thead>
                            <tr>
                                <th>연계ID</th>
                                <th>클래스</th>
                                <th>메서드</th>
                                <th>XML파일</th>
                                <th>쿼리ID</th>
                                <th>쿼리종류</th>
                                <th>관련테이블들</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        {self._get_callchain_javascript()}
    </script>
</body>
</html>"""
    
    def _generate_stats_html(self, stats: Dict[str, int]) -> str:
        """통계 카드 HTML 생성"""
        return f"""
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{stats.get('java_classes', 0)}</div>
                <div class="stat-label">Java 클래스</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('database_tables', 0)}</div>
                <div class="stat-label">데이터베이스 테이블</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('xml_files', 0)}</div>
                <div class="stat-label">XML 파일</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('jsp_files', 0)}</div>
                <div class="stat-label">JSP 파일</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('join_relations', 0)}</div>
                <div class="stat-label">JOIN 관계</div>
            </div>
        </div>"""
    
    def _generate_filter_html(self, filter_options: Dict[str, List[str]]) -> str:
        """필터링 옵션 HTML 생성"""
        # 테이블 옵션
        table_options = ''.join([f'<option value="{table}">{table}</option>' for table in filter_options.get('tables', [])])
        
        # 쿼리 타입 옵션
        query_type_options = ''.join([f'<option value="{qt}">{qt}</option>' for qt in filter_options.get('query_types', [])])
        
        return f"""
        <div class="filter-controls">
            <input type="text" id="searchInput" placeholder="클래스, 메서드, 테이블명으로 검색..." style="width: 300px;">
            <select id="tableFilter">
                <option value="">모든 테이블</option>
                {table_options}
            </select>
            <select id="queryTypeFilter">
                <option value="">모든 쿼리 타입</option>
                {query_type_options}
            </select>
            <button onclick="filterTable()">필터 적용</button>
            <button onclick="clearFilters()">필터 초기화</button>
            <button onclick="exportToCSV()">CSV 내보내기</button>
        </div>"""
    
    def _generate_chain_table_html(self, chain_data: List[Dict[str, Any]]) -> str:
        """연계 체인 테이블 HTML 생성 (툴팁 포함, 오프라인 지원)"""
        rows = []
        for data in chain_data:
            sql_content = data.get('sql_content', '')
            # HTML 특수문자 이스케이프 (크로스플랫폼 호환)
            escaped_sql = (sql_content.replace('&', '&amp;')
                          .replace('<', '&lt;')
                          .replace('>', '&gt;')
                          .replace('"', '&quot;')
                          .replace("'", '&#39;'))
            
            # 툴팁이 있는 경우와 없는 경우 분기
            if sql_content:
                query_type_html = f'<span class="query-type tooltip" data-query="{escaped_sql}">{data["query_type"]}<span class="tooltiptext">{escaped_sql}</span></span>'
            else:
                query_type_html = f'<span class="query-type">{data["query_type"]}</span>'
            
            # 안전한 HTML 생성 (크로스플랫폼 호환)
            rows.append(f"""
                <tr>
                    <td><span class="chain-id">{data['chain_id']}</span></td>
                    <td><span class="class-name">{data['class_name']}</span></td>
                    <td><span class="method-name">{data['method_name']}</span></td>
                    <td><span class="xml-file">{data['xml_file']}</span></td>
                    <td><span class="query-id">{data['query_id']}</span></td>
                    <td>{query_type_html}</td>
                    <td><span class="tables">{data['related_tables']}</span></td>
                </tr>""")
        
        return '\n'.join(rows)
    
    def _get_callchain_css(self) -> str:
        """CallChain Report CSS 스타일"""
        return """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            width: 100%;
            max-width: 100%;
            margin: 0;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header .subtitle {
            margin: 10px 0 0 0;
            opacity: 0.8;
            font-size: 1.1em;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 5px;
        }
        .stat-label {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .content {
            padding: 30px;
        }
        .section {
            margin-bottom: 40px;
        }
        .section h2 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .table-container {
            overflow-x: auto;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            font-size: 1.0em;
        }
        th {
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            padding: 15px 10px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        td {
            padding: 12px 10px;
            border-bottom: 1px solid #ecf0f1;
            vertical-align: top;
        }
        tr:hover {
            background-color: #f8f9fa;
        }
        .chain-id, .jsp-file, .class-name, .method-name, .xml-file, .query-id, .query-type, .tables {
            background: #f8f9fa;
            color: #495057;
            padding: 6px 10px;
            border: 1px solid #dee2e6;
            border-radius: 3px;
            font-family: monospace;
            font-size: 1.0em;
        }
        .filter-controls {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .filter-controls input, .filter-controls select {
            margin: 5px;
            padding: 8px 12px;
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            font-size: 0.9em;
        }
        .filter-controls button {
            background: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        .filter-controls button:hover {
            background: #2980b9;
        }
        .tooltip {
            position: relative;
            display: inline-block;
        }
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 500px;
            background-color: #2c3e50;
            color: #fff;
            text-align: left;
            border-radius: 6px;
            padding: 10px;
            position: absolute;
            z-index: 1000;
            bottom: 125%;
            left: 50%;
            margin-left: -250px;
            opacity: 0;
            transition: opacity 0.3s;
            font-family: monospace;
            font-size: 1.0em;
            white-space: pre-wrap;
            word-break: break-all;
            max-height: 300px;
            overflow-y: auto;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        .tooltip .tooltiptext::after {
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: #2c3e50 transparent transparent transparent;
        }
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 10px;
            }
            .header {
                padding: 20px;
            }
            .header h1 {
                font-size: 2em;
            }
            .content {
                padding: 20px;
            }
            table {
                font-size: 0.8em;
            }
            th, td {
                padding: 8px 5px;
            }
            .tooltip .tooltiptext {
                width: 300px;
                margin-left: -150px;
            }
        }
        """
    
    def _get_callchain_javascript(self) -> str:
        """CallChain Report JavaScript (오프라인 지원)"""
        return """
        // 오프라인 환경 지원을 위한 JavaScript
        // 외부 라이브러리 의존성 없이 순수 JavaScript로 구현
        
        // 검색 기능
        function filterTable() {
            const searchInput = document.getElementById('searchInput').value.toLowerCase();
            const tableFilter = document.getElementById('tableFilter').value;
            const queryTypeFilter = document.getElementById('queryTypeFilter').value;
            const table = document.getElementById('chainTable');
            const rows = table.getElementsByTagName('tr');
            
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const cells = row.getElementsByTagName('td');
                let shouldShow = true;
                
                // 텍스트 검색
                if (searchInput) {
                    let found = false;
                    for (let j = 0; j < cells.length; j++) {
                        if (cells[j].textContent.toLowerCase().indexOf(searchInput) !== -1) {
                            found = true;
                            break;
                        }
                    }
                    if (!found) shouldShow = false;
                }
                
                // 테이블 필터
                if (tableFilter && shouldShow) {
                    const tablesCell = cells[6];
                    if (tablesCell.textContent.indexOf(tableFilter) === -1) {
                        shouldShow = false;
                    }
                }
                
                // 쿼리 타입 필터
                if (queryTypeFilter && shouldShow) {
                    const queryTypeCell = cells[5];
                    if (queryTypeCell.textContent.indexOf(queryTypeFilter) === -1) {
                        shouldShow = false;
                    }
                }
                
                row.style.display = shouldShow ? '' : 'none';
            }
        }
        
        // 필터 초기화
        function clearFilters() {
            document.getElementById('searchInput').value = '';
            document.getElementById('tableFilter').value = '';
            document.getElementById('queryTypeFilter').value = '';
            const table = document.getElementById('chainTable');
            const rows = table.getElementsByTagName('tr');
            for (let i = 1; i < rows.length; i++) {
                rows[i].style.display = '';
            }
        }
        
        // CSV 내보내기 (정제된 SQL 내용 포함)
        function exportToCSV() {
            const table = document.getElementById('chainTable');
            const rows = table.getElementsByTagName('tr');
            let csv = [];
            
            // 헤더 추가
            csv.push('연계ID,클래스,메서드,XML파일,쿼리ID,쿼리종류,정제된SQL내용,관련테이블들');
            
            for (let i = 1; i < rows.length; i++) {
                const cells = rows[i].getElementsByTagName('td');
                if (cells.length > 0 && rows[i].style.display !== 'none') {
                    let row = [];
                    for (let j = 0; j < cells.length; j++) {
                        let cellText = cells[j].textContent.replace(/"/g, '""');
                        
                        // 쿼리종류 컬럼(인덱스 5)의 경우 정제된 SQL 내용도 포함
                        if (j === 5) {
                            const queryTypeSpan = cells[j].querySelector('.query-type');
                            if (queryTypeSpan && queryTypeSpan.classList.contains('tooltip')) {
                                const sqlContent = queryTypeSpan.getAttribute('data-query') || '';
                                row.push('"' + cellText + '"'); // 쿼리종류
                                row.push('"' + sqlContent.replace(/"/g, '""') + '"'); // 정제된 SQL 내용
                            } else {
                                row.push('"' + cellText + '"'); // 쿼리종류
                                row.push('""'); // 빈 정제된 SQL 내용
                            }
                        } else {
                            row.push('"' + cellText + '"');
                        }
                    }
                    csv.push(row.join(','));
                }
            }
            
            const csvContent = csv.join('\\n');
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', 'CallChainReport_' + new Date().toISOString().slice(0,19).replace(/:/g,'-') + '.csv');
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        
        // 이벤트 리스너 등록
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                filterTable();
            }
        });
        
        document.getElementById('searchInput').addEventListener('input', function() {
            filterTable();
        });
        
        document.getElementById('tableFilter').addEventListener('change', function() {
            filterTable();
        });
        
        document.getElementById('queryTypeFilter').addEventListener('change', function() {
            filterTable();
        });
        
        // 툴팁 기능 초기화
        document.addEventListener('DOMContentLoaded', function() {
            // query-type 요소에 툴팁 이벤트 리스너 추가
            const queryTypeElements = document.querySelectorAll('.query-type.tooltip');
            queryTypeElements.forEach(function(element) {
                element.addEventListener('mouseenter', function() {
                    const tooltip = this.querySelector('.tooltiptext');
                    if (tooltip) {
                        tooltip.style.visibility = 'visible';
                        tooltip.style.opacity = '1';
                    }
                });
                
                element.addEventListener('mouseleave', function() {
                    const tooltip = this.querySelector('.tooltiptext');
                    if (tooltip) {
                        tooltip.style.visibility = 'hidden';
                        tooltip.style.opacity = '0';
                    }
                });
            });
        });
        """

    def get_erd_template(self, project_name: str, timestamp: str, stats: Dict[str, int], 
                        erd_data: Dict[str, Any]) -> str:
        """ERD Report HTML 템플릿 생성"""
        
        # 통계 카드 HTML 생성
        stats_html = self._generate_erd_stats_html(stats)
        
        # Mermaid ERD 다이어그램 HTML 생성
        erd_diagram_html = self._generate_erd_diagram_html(erd_data)
        
        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ERD Report - {project_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
    <style>
        {self._get_erd_css()}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ERD Report</h1>
            <div class="subtitle">Entity Relationship Diagram</div>
            <div class="subtitle">프로젝트: {project_name} | 생성일시: {timestamp}</div>
        </div>
        {stats_html}
        <div class="content">
            <div class="section">
                <h2>데이터베이스 ERD</h2>
                <div class="diagram-controls">
                    <button onclick="zoomIn()">확대</button>
                    <button onclick="zoomOut()">축소</button>
                    <button onclick="resetZoom()">원래 크기</button>
                </div>
                <div class="diagram-container">
                    {erd_diagram_html}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        {self._get_erd_javascript()}
    </script>
</body>
</html>"""
    
    def _generate_erd_stats_html(self, stats: Dict[str, int]) -> str:
        """ERD 통계 카드 HTML 생성"""
        return f"""
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_tables', 0)}</div>
                <div class="stat-label">전체 테이블</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_columns', 0)}</div>
                <div class="stat-label">전체 컬럼</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('primary_keys', 0)}</div>
                <div class="stat-label">Primary Key</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('foreign_keys', 0)}</div>
                <div class="stat-label">Foreign Key</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('relationships', 0)}</div>
                <div class="stat-label">관계</div>
            </div>
        </div>"""
    
    def _generate_erd_diagram_html(self, erd_data: Dict[str, Any]) -> str:
        """Mermaid ERD 다이어그램 HTML 생성"""
        mermaid_code = erd_data.get('mermaid_code', '')
        return f"""
        <div class="mermaid">
            {mermaid_code}
        </div>"""
    
    def _get_erd_css(self) -> str:
        """ERD Report CSS 스타일"""
        return """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            width: 100%;
            max-width: 100%;
            margin: 0;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header .subtitle {
            margin: 10px 0 0 0;
            opacity: 0.8;
            font-size: 1.1em;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 5px;
        }
        .stat-label {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .content {
            padding: 30px;
        }
        .section {
            margin-bottom: 40px;
        }
        .section h2 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .diagram-controls {
            margin-bottom: 20px;
        }
        .diagram-controls button {
            background: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        .diagram-controls button:hover {
            background: #2980b9;
        }
        .diagram-container {
            overflow: auto;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            background: #fafafa;
            min-height: 600px;
        }
        .mermaid {
            text-align: center;
        }
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 10px;
            }
            .header {
                padding: 20px;
            }
            .header h1 {
                font-size: 2em;
            }
            .content {
                padding: 20px;
            }
        }
        """
    
    def _get_erd_javascript(self) -> str:
        """ERD Report JavaScript"""
        return """
        // Mermaid 초기화
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            er: {
                diagramPadding: 20
            }
        });
        
        // 확대 기능
        function zoomIn() {
            const diagram = document.querySelector('.mermaid');
            if (diagram) {
                const currentTransform = diagram.style.transform || 'scale(1)';
                const currentScale = parseFloat(currentTransform.match(/scale\\((\\d+(?:\\.\\d+)?)\\)/)?.[1] || '1');
                const newScale = Math.min(currentScale * 1.2, 3);
                diagram.style.transform = `scale(${newScale})`;
            }
        }
        
        // 축소 기능
        function zoomOut() {
            const diagram = document.querySelector('.mermaid');
            if (diagram) {
                const currentTransform = diagram.style.transform || 'scale(1)';
                const currentScale = parseFloat(currentTransform.match(/scale\\((\\d+(?:\\.\\d+)?)\\)/)?.[1] || '1');
                const newScale = Math.max(currentScale / 1.2, 0.5);
                diagram.style.transform = `scale(${newScale})`;
            }
        }
        
        // 원래 크기로 리셋
        function resetZoom() {
            const diagram = document.querySelector('.mermaid');
            if (diagram) {
                diagram.style.transform = 'scale(1)';
            }
        }
        """

    def get_architecture_template(self, project_name: str, timestamp: str, stats: Dict[str, int], 
                                layer_data: Dict[str, List[Dict[str, Any]]], relationships: Dict[str, List[Dict[str, Any]]]) -> str:
        """Architecture Report HTML 템플릿 생성 (오프라인 지원, SVG 기반)"""
        
        # 통계 카드 HTML 생성
        stats_html = self._generate_architecture_stats_html(stats)
        
        # 아키텍처 다이어그램 SVG 생성
        diagram_svg = self._generate_architecture_diagram_svg(layer_data)
        
        # 관계 분석 HTML 생성
        relationships_html = self._generate_relationships_html(relationships)
        
        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>시스템 아키텍처 분석 리포트 - {project_name}</title>
    <style>
        {self._get_architecture_css()}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>시스템 아키텍처 분석</h1>
            <div class="subtitle">System Architecture Analysis Report</div>
            <div class="subtitle">생성일시: {timestamp}</div>
        </div>
        
        <div class="section">
            <h2>아키텍처 구조 다이어그램</h2>
            <div class="diagram-container">
                {diagram_svg}
            </div>
        </div>
        
        {relationships_html}
        
        {stats_html}
        
        <div class="timestamp">
            Generated by SourceAnalyzer Architecture Reporter | {timestamp}
        </div>
    </div>
    
    <script>
        {self._get_architecture_javascript()}
    </script>
</body>
</html>"""
    
    def _generate_architecture_stats_html(self, stats: Dict[str, int]) -> str:
        """아키텍처 통계 카드 HTML 생성"""
        return f"""
        <div class="section">
            <h2>구성 요소 통계</h2>
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>컴포넌트 타입</th>
                        <th>수량</th>
                        <th>설명</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>클래스</td>
                        <td>{stats.get('total_classes', 0)}개</td>
                        <td>Java 클래스 파일</td>
                    </tr>
                    <tr>
                        <td>테이블</td>
                        <td>{stats.get('total_tables', 0)}개</td>
                        <td>데이터베이스 테이블</td>
                    </tr>
                    <tr style="font-weight:bold;background-color:#e3f2fd;">
                        <td>전체</td>
                        <td>{stats.get('total_classes', 0) + stats.get('total_tables', 0)}개</td>
                        <td>총 컴포넌트 수</td>
                    </tr>
                </tbody>
            </table>
        </div>"""
    
    def _generate_architecture_diagram_svg(self, layer_data: Dict[str, List[Dict[str, Any]]]) -> str:
        """SVG 기반 아키텍처 다이어그램 생성 (오프라인 지원)"""
        try:
            # 레이어별 컴포넌트 수 계산
            controller_count = len(layer_data.get('controller', []))
            service_count = len(layer_data.get('service', []))
            mapper_count = len(layer_data.get('mapper', []))
            model_count = len(layer_data.get('model', []))
            
            # SVG 다이어그램 생성
            svg_content = f"""<svg width="100%" height="500" viewBox="0 0 1000 500">
                <!-- Controller Layer -->
                <rect x="50" y="50" width="900" height="80" 
                      fill="#e1f5fe" stroke="#01579b" 
                      stroke-width="2" rx="10"/>
                <text x="500" y="70" text-anchor="middle" 
                      fill="#01579b" font-weight="bold" font-size="14">
                      Controller Layer</text>
                
                {self._generate_layer_components_svg(layer_data.get('controller', []), 80, 85, '#01579b')}
                
                <!-- Service Layer -->
                <rect x="50" y="150" width="900" height="80" 
                      fill="#f3e5f5" stroke="#4a148c" 
                      stroke-width="2" rx="10"/>
                <text x="500" y="170" text-anchor="middle" 
                      fill="#4a148c" font-weight="bold" font-size="14">
                      Service Layer</text>
                
                {self._generate_layer_components_svg(layer_data.get('service', []), 180, 185, '#4a148c')}
                
                <!-- Mapper Layer -->
                <rect x="50" y="250" width="900" height="80" 
                      fill="#e8f5e8" stroke="#1b5e20" 
                      stroke-width="2" rx="10"/>
                <text x="500" y="270" text-anchor="middle" 
                      fill="#1b5e20" font-weight="bold" font-size="14">
                      Mapper Layer</text>
                
                {self._generate_layer_components_svg(layer_data.get('mapper', []), 280, 285, '#1b5e20')}
                
                <!-- Model Layer -->
                <rect x="50" y="350" width="900" height="80" 
                      fill="#fff3e0" stroke="#e65100" 
                      stroke-width="2" rx="10"/>
                <text x="500" y="370" text-anchor="middle" 
                      fill="#e65100" font-weight="bold" font-size="14">
                      Model Layer</text>
                
                {self._generate_layer_components_svg(layer_data.get('model', []), 380, 385, '#e65100')}
                
                <!-- Layer Arrows -->
                <defs>
                    <marker id="layer-arrow" markerWidth="10" markerHeight="7" 
                            refX="10" refY="3.5" orient="auto">
                        <polygon points="0 0, 10 3.5, 0 7" fill="#333"/>
                    </marker>
                </defs>
                <line x1="500" y1="130" x2="500" y2="150" 
                      stroke="#333" stroke-width="2" marker-end="url(#layer-arrow)"/>
                <line x1="500" y1="230" x2="500" y2="250" 
                      stroke="#333" stroke-width="2" marker-end="url(#layer-arrow)"/>
                <line x1="500" y1="330" x2="500" y2="350" 
                      stroke="#333" stroke-width="2" marker-end="url(#layer-arrow)"/>
            </svg>"""
            
            return svg_content
            
        except Exception as e:
            app_logger.warning(f"SVG 다이어그램 생성 실패: {str(e)}")
            return """<svg width="100%" height="500" viewBox="0 0 1000 500">
                <rect x="50" y="50" width="900" height="400" fill="#f5f5f5" stroke="#ccc" stroke-width="2" rx="10"/>
                <text x="500" y="250" text-anchor="middle" fill="#666" font-size="16">다이어그램 생성 중 오류 발생</text>
            </svg>"""
    
    def _generate_layer_components_svg(self, components: List[Dict[str, Any]], layer_y: int, component_y: int, stroke_color: str) -> str:
        """레이어별 컴포넌트 SVG 생성"""
        if not components:
            return ""
        
        svg_elements = []
        max_components_per_row = 8
        component_width = 100
        component_height = 25
        start_x = 80
        spacing = 10
        
        for i, component in enumerate(components[:max_components_per_row]):
            x = start_x + i * (component_width + spacing)
            component_name = component.get('component_name', 'Unknown')
            
            # 컴포넌트명 길이 제한 (12자)
            display_name = component_name[:12] + '...' if len(component_name) > 12 else component_name
            
            svg_elements.append(f"""
                <rect x="{x}" y="{component_y}" width="{component_width}" height="{component_height}" 
                      fill="white" stroke="{stroke_color}" rx="3"/>
                <text x="{x + component_width//2}" y="{component_y + component_height//2 + 3}" text-anchor="middle" 
                      fill="#333" font-size="9">{display_name}</text>""")
        
        return ''.join(svg_elements)
    
    def _generate_relationships_html(self, relationships: Dict[str, List[Dict[str, Any]]]) -> str:
        """관계 분석 HTML 생성"""
        dependency_html = self._generate_relationship_card_html("의존성 관계", relationships.get('dependency', []))
        implementation_html = self._generate_relationship_card_html("구현 관계", relationships.get('implementation', []))
        call_html = self._generate_relationship_card_html("호출 관계", relationships.get('call', []))
        
        return f"""
        <div class="section">
            <h2>컴포넌트 관계 분석</h2>
            <div class="relationship-grid">
                {dependency_html}
                {implementation_html}
                {call_html}
            </div>
        </div>"""
    
    def _generate_relationship_card_html(self, title: str, relationships: List[Dict[str, Any]]) -> str:
        """관계 카드 HTML 생성"""
        relationship_items = []
        for rel in relationships:
            src = rel.get('src_component', 'Unknown')
            dst = rel.get('dst_component', 'Unknown')
            relationship_items.append(f'<div class="relationship-item">{src} ➜ {dst}</div>')
        
        return f"""
        <div class="relationship-card">
            <div class="relationship-header">{title} ({len(relationships)}개)</div>
            <div class="relationship-body">
                {''.join(relationship_items)}
            </div>
        </div>"""
    
    def _get_architecture_css(self) -> str:
        """Architecture Report CSS 스타일 (크로스플랫폼 호환)"""
        return """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 15px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }
        .container {
            max-width: 95%;
            margin: 0 auto;
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #007acc;
        }
        .header h1 {
            color: #007acc;
            margin: 0;
            font-size: 2.2em;
        }
        .header .subtitle {
            color: #666;
            font-size: 1.1em;
            margin-top: 10px;
        }
        .section {
            margin: 30px 0;
            padding: 20px;
            border-left: 4px solid #007acc;
            background-color: #f8f9fa;
        }
        .section h2 {
            color: #007acc;
            margin-top: 0;
            font-size: 1.6em;
        }
        .diagram-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        .stats-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .stats-table th, .stats-table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        .stats-table th {
            background-color: #007acc;
            color: white;
            font-weight: bold;
        }
        .stats-table tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .relationship-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .relationship-card {
            background: white;
            border: 2px solid #28a745;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .relationship-header {
            background: #28a745;
            color: white;
            padding: 15px;
            font-weight: bold;
            text-align: center;
        }
        .relationship-body {
            padding: 15px;
            max-height: 300px;
            overflow-y: auto;
        }
        .relationship-item {
            margin: 5px 0;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 0.9em;
        }
        .timestamp {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                padding: 15px;
            }
            .header h1 {
                font-size: 1.8em;
            }
            .relationship-grid {
                grid-template-columns: 1fr;
            }
        }
        """
    
    def _get_architecture_javascript(self) -> str:
        """Architecture Report JavaScript (오프라인 지원)"""
        return """
        // 오프라인 환경 지원을 위한 JavaScript
        // 외부 라이브러리 의존성 없이 순수 JavaScript로 구현
        
        // 다이어그램 확대/축소 기능
        function zoomDiagram(scale) {
            const svg = document.querySelector('svg');
            if (svg) {
                svg.style.transform = `scale(${scale})`;
                svg.style.transformOrigin = 'center center';
            }
        }
        
        // 다이어그램 초기화
        document.addEventListener('DOMContentLoaded', function() {
            // SVG 반응형 처리
            const svg = document.querySelector('svg');
            if (svg) {
                svg.style.maxWidth = '100%';
                svg.style.height = 'auto';
            }
        });
        
        // 키보드 단축키 지원
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case '=':
                    case '+':
                        e.preventDefault();
                        zoomDiagram(1.2);
                        break;
                    case '-':
                        e.preventDefault();
                        zoomDiagram(0.8);
                        break;
                    case '0':
                        e.preventDefault();
                        zoomDiagram(1);
                        break;
                }
            }
        });
        """

    def get_erd_dagre_template(self, project_name: str, timestamp: str, stats: Dict[str, int], 
                              erd_data: Dict[str, Any]) -> str:
        """ERD(Dagre) Report HTML 템플릿 생성"""
        
        # 통계 카드 HTML 생성
        stats_html = self._generate_erd_dagre_stats_html(stats)
        
        # Cytoscape.js 데이터 JSON 생성
        cytoscape_json = self._generate_cytoscape_json(erd_data)
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Source Analyzer - 고도화 ERD</title>
    <style>
        {self._get_erd_dagre_css()}
    </style>
    <!-- Offline assets -->
    <script src="./js/cytoscape.min.js"></script>
    <script src="./js/dagre.min.js"></script>
    <script src="./js/cytoscape-dagre.js"></script>
    <script src="./js/cytoscape-fcose.js"></script>
    <script>
        const DATA = {cytoscape_json};
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Source Analyzer - 고도화 ERD</h1>
            <div class="subtitle">프로젝트: {project_name} | 생성일시: {timestamp}</div>
        </div>
        {stats_html}
        <div id="toolbar">
            <button onclick="resetView()">초기화</button>
            <button onclick="toggleLayout()">레이아웃 전환</button>
            <button onclick="exportPng()">PNG 내보내기</button>
            <button onclick="exportSvg()">SVG 내보내기</button>
            <input type="text" id="search" placeholder="테이블명으로 검색..." />
            <span id="current-layout">fcose</span>
        </div>
        <div id="cy"></div>
        
        <!-- 툴팁 -->
        <div id="tooltip" class="tooltip">
            <div class="tooltip-header">
                <div class="tooltip-title"></div>
                <div class="tooltip-subtitle"></div>
            </div>
            <div class="tooltip-content">
                <ul class="columns-list"></ul>
            </div>
        </div>
        
        <!-- 관계선 툴팁 -->
        <div id="edge-tooltip" class="edge-tooltip">
            <div class="edge-tooltip-header">
                <span class="edge-tooltip-title"></span>
                <span class="edge-tooltip-type"></span>
            </div>
            <div class="edge-tooltip-content">
                <div class="join-condition"></div>
                <div class="relation-detail"></div>
                <div class="edge-metadata">
                    <span class="confidence-badge"></span>
                    <span class="frequency-info"></span>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        {self._get_erd_dagre_javascript()}
    </script>
</body>
</html>"""
    
    def _generate_erd_dagre_stats_html(self, stats: Dict[str, int]) -> str:
        """ERD(Dagre) 통계 카드 HTML 생성"""
        return f"""
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_tables', 0)}</div>
                <div class="stat-label">전체 테이블</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_columns', 0)}</div>
                <div class="stat-label">전체 컬럼</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('primary_keys', 0)}</div>
                <div class="stat-label">Primary Key</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('foreign_keys', 0)}</div>
                <div class="stat-label">Foreign Key</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('relationships', 0)}</div>
                <div class="stat-label">관계</div>
            </div>
        </div>"""
    
    def _generate_cytoscape_json(self, erd_data: Dict[str, Any]) -> str:
        """Cytoscape.js 데이터 JSON 생성"""
        import json
        
        # JSON 데이터 생성
        cytoscape_data = {
            'nodes': erd_data.get('nodes', []),
            'edges': erd_data.get('edges', [])
        }
        
        # JSON 문자열로 변환 (한글 지원)
        return json.dumps(cytoscape_data, ensure_ascii=False, indent=2)
    
    def _get_erd_dagre_css(self) -> str:
        """ERD(Dagre) Report CSS 스타일"""
        return """
        body, html { 
            margin: 0; 
            height: 100%; 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .container {
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2em;
            font-weight: 300;
        }
        .header .subtitle {
            margin: 10px 0 0 0;
            opacity: 0.8;
            font-size: 1em;
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 20px;
            padding: 15px;
            background: #f8f9fa;
            flex-wrap: wrap;
        }
        .stat-card {
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            min-width: 120px;
        }
        .stat-number {
            font-size: 1.8em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 5px;
        }
        .stat-label {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        #toolbar { 
            padding: 12px; 
            border-bottom: 1px solid #ddd; 
            background: #f8f9fa;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        #cy { 
            width: 100%; 
            height: calc(100vh - 200px); 
            flex: 1;
        }
        
        button {
            background: #007bff;
            border: none;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        button:hover {
            background: #0056b3;
        }
        
        #search {
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 14px;
            min-width: 200px;
        }
        
        /* 향상된 툴팁 스타일 */
        .tooltip {
            position: absolute;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 0;
            max-width: 400px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            display: none;
            z-index: 2000;
            font-size: 12px;
        }
        
        .tooltip-header {
            background: #f8f9fa;
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
            border-radius: 8px 8px 0 0;
        }
        
        .tooltip-title {
            font-weight: bold;
            font-size: 14px;
            color: #212529;
            margin-bottom: 4px;
        }
        
        .tooltip-subtitle {
            font-size: 11px;
            color: #6c757d;
        }
        
        .tooltip-content {
            padding: 0;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .columns-list {
            list-style: none;
            margin: 0;
            padding: 0;
        }
        
        .column-item {
            padding: 8px 12px;
            border-bottom: 1px solid #f1f3f4;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .column-item:last-child {
            border-bottom: none;
        }
        
        .column-name {
            font-weight: 500;
            color: #212529;
        }
        
        .column-type {
            font-size: 10px;
            color: #6c757d;
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 3px;
        }
        
        .column-pk {
            background: #d4edda;
            color: #155724;
        }
        
        .column-fk {
            background: #cce5ff;
            color: #004085;
        }
        
        .column-nullable {
            background: #fff3cd;
            color: #856404;
        }
        
        /* 관계선 툴팁 스타일 */
        .edge-tooltip {
            position: absolute;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border: 2px solid #007bff;
            border-radius: 8px;
            padding: 0;
            max-width: 380px;
            min-width: 200px;
            box-shadow: 0 8px 25px rgba(0,123,255,0.15), 0 3px 10px rgba(0,0,0,0.1);
            display: none;
            z-index: 2100;
            font-size: 12px;
            pointer-events: none;
            animation: fadeInTooltip 0.2s ease-out;
        }
        
        @keyframes fadeInTooltip {
            from { opacity: 0; transform: translateY(-5px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .edge-tooltip-header {
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            padding: 10px 12px;
            margin: 0;
            border-radius: 6px 6px 0 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-weight: 600;
            font-size: 13px;
        }
        
        .edge-tooltip-type {
            font-size: 10px;
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-weight: 500;
            border: 1px solid rgba(255,255,255,0.3);
        }
        
        .edge-tooltip-content {
            color: #495057;
            padding: 12px;
        }
        
        .join-condition {
            background: linear-gradient(135deg, #e8f4fd 0%, #f1f8ff 100%);
            border: 1px solid #b3d9ff;
            padding: 8px 12px;
            border-radius: 6px;
            margin: 8px 0;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            font-weight: 500;
            color: #0056b3;
            position: relative;
        }
        
        .join-condition::before {
            content: '🔗';
            position: absolute;
            left: -5px;
            top: 50%;
            transform: translateY(-50%);
            width: 10px;
            height: 10px;
        }
        
        .edge-metadata {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 10px;
            color: #6c757d;
            margin-top: 10px;
            padding: 8px 0;
            border-top: 1px solid #e9ecef;
        }
        
        .confidence-badge {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 4px rgba(40,167,69,0.3);
        }
        
        .frequency-info {
            color: #6c757d;
            font-size: 10px;
        }
        
        .relation-detail {
            margin: 4px 0;
            padding: 4px 8px;
            background: #f8f9fa;
            border-left: 3px solid #007bff;
            border-radius: 0 4px 4px 0;
            font-size: 11px;
        }
        
        .relation-detail strong {
            color: #495057;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.5em;
            }
            .stats {
                gap: 10px;
                padding: 10px;
            }
            .stat-card {
                padding: 10px 15px;
                min-width: 100px;
            }
            .stat-number {
                font-size: 1.5em;
            }
            #toolbar {
                padding: 8px;
                gap: 5px;
            }
            #search {
                min-width: 150px;
            }
        }
        """
    
    def _get_erd_dagre_javascript(self) -> str:
        """ERD(Dagre) Report JavaScript"""
        return """
        // Cytoscape.js 초기화
        let cy;
        let currentLayout = 'fcose';
        let tooltipTimeout;
        let edgeTooltipTimeout;
        let isTooltipVisible = false;
        let isEdgeTooltipVisible = false;
        
        // 레이아웃 옵션
        const layoutOptions = {
            fcose: {
                name: 'fcose',
                quality: 'default',
                randomize: false,
                animate: true,
                animationDuration: 1000,
                fit: true,
                padding: 30,
                nodeDimensionsIncludeLabels: true,
                uniformNodeDimensions: false,
                packComponents: true,
                step: 'all',
                samplingType: false,
                sampleSize: 25,
                nodeSeparation: 75,
                piTol: 0.0000001,
                nodeRepulsion: function( node ){ return 400000; },
                idealEdgeLength: function( edge ){ return 10; },
                edgeElasticity: function( edge ){ return 100; },
                nestingFactor: 0.1,
                gravity: 0.25,
                numIter: 2500,
                tile: true,
                tilingPaddingVertical: 10,
                tilingPaddingHorizontal: 10,
                gravityRangeCompound: 1.5,
                gravityCompound: 1.0,
                gravityRange: 3.8,
                initialEnergyOnIncremental: 0.3
            },
            dagre: {
                name: 'dagre',
                rankDir: 'TB',
                rankSep: 100,
                nodeSep: 50,
                edgeSep: 10,
                ranker: 'tight-tree'
            }
        };
        
        // Cytoscape 초기화
        function initCytoscape() {
            cy = cytoscape({
                container: document.getElementById('cy'),
                elements: DATA,
                style: [
                    {
                        selector: 'node',
                        style: {
                            'background-color': '#3498db',
                            'label': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'color': 'white',
                            'font-size': '12px',
                            'font-weight': 'bold',
                            'text-outline-width': 2,
                            'text-outline-color': '#2c3e50',
                            'width': '120px',
                            'height': '60px',
                            'border-width': 2,
                            'border-color': '#2c3e50',
                            'border-style': 'solid'
                        }
                    },
                    {
                        selector: 'node[type="table"]',
                        style: {
                            'background-color': '#e74c3c',
                            'shape': 'roundrectangle'
                        }
                    },
                    {
                        selector: 'edge',
                        style: {
                            'width': 2,
                            'line-color': '#7f8c8d',
                            'target-arrow-color': '#7f8c8d',
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier',
                            'label': 'data(label)',
                            'font-size': '10px',
                            'text-rotation': 'autorotate',
                            'text-margin-y': -10
                        }
                    },
                    {
                        selector: 'edge[type="FK"]',
                        style: {
                            'line-color': '#e74c3c',
                            'target-arrow-color': '#e74c3c',
                            'line-style': 'solid'
                        }
                    },
                    {
                        selector: 'edge[type*="JOIN"]',
                        style: {
                            'line-color': '#f39c12',
                            'target-arrow-color': '#f39c12',
                            'line-style': 'dashed'
                        }
                    },
                    {
                        selector: 'node:selected',
                        style: {
                            'background-color': '#f39c12',
                            'border-color': '#e67e22',
                            'border-width': 3
                        }
                    },
                    {
                        selector: 'edge:selected',
                        style: {
                            'line-color': '#f39c12',
                            'target-arrow-color': '#f39c12',
                            'width': 3
                        }
                    }
                ],
                layout: layoutOptions[currentLayout]
            });
            
            // 이벤트 리스너 등록
            setupEventListeners();
        }
        
        // 이벤트 리스너 설정
        function setupEventListeners() {
            // 검색 기능
            const searchInput = document.getElementById('search');
            searchInput.addEventListener('input', function() {
                const query = this.value.toLowerCase();
                if (query === '') {
                    cy.elements().style('opacity', 1);
                } else {
                    cy.elements().style('opacity', 0.3);
                    cy.elements().filter(function(ele) {
                        return ele.data('label').toLowerCase().includes(query);
                    }).style('opacity', 1);
                }
            });
            
            // 툴팁 이벤트
            setupTooltipEvents();
        }
        
        // 툴팁 이벤트 설정
        function setupTooltipEvents() {
            const tooltip = document.getElementById('tooltip');
            const edgeTooltip = document.getElementById('edge-tooltip');
            
            // 노드 툴팁
            cy.on('mouseover', 'node', function(event) {
                const node = event.target;
                clearTimeout(tooltipTimeout);
                hideEdgeTooltip();
                
                tooltipTimeout = setTimeout(() => {
                    const renderedPosition = event.renderedPosition;
                    showTooltip(node, renderedPosition.x, renderedPosition.y);
                }, 500);
            });
            
            cy.on('mouseout', 'node', function(event) {
                clearTimeout(tooltipTimeout);
                setTimeout(() => {
                    if (!isTooltipVisible) return;
                    hideTooltip();
                }, 100);
            });
            
            // 엣지 툴팁
            cy.on('mouseover', 'edge', function(event) {
                const edge = event.target;
                clearTimeout(edgeTooltipTimeout);
                hideTooltip();
                
                edgeTooltipTimeout = setTimeout(() => {
                    const renderedPosition = event.renderedPosition;
                    showEdgeTooltip(edge, renderedPosition.x, renderedPosition.y);
                }, 300);
            });
            
            cy.on('mouseout', 'edge', function(event) {
                clearTimeout(edgeTooltipTimeout);
                setTimeout(() => {
                    if (!isEdgeTooltipVisible) return;
                    hideEdgeTooltip();
                }, 100);
            });
            
            // 캔버스 클릭 시 툴팁 숨김
            cy.on('tap', function(event) {
                if (event.target === cy) {
                    hideTooltip();
                    hideEdgeTooltip();
                }
            });
        }
        
        // 노드 툴팁 표시
        function showTooltip(node, x, y) {
            const tooltip = document.getElementById('tooltip');
            const meta = node.data('meta');
            
            if (!meta) return;
            
            document.getElementById('tooltip').querySelector('.tooltip-title').textContent = meta.table_name;
            document.getElementById('tooltip').querySelector('.tooltip-subtitle').textContent = 
                `${meta.owner} | ${meta.columns.length}개 컬럼`;
            
            const columnsList = document.getElementById('tooltip').querySelector('.columns-list');
            columnsList.innerHTML = '';
            
            meta.columns.forEach(col => {
                const li = document.createElement('li');
                li.className = 'column-item';
                
                const nameSpan = document.createElement('span');
                nameSpan.className = 'column-name';
                nameSpan.textContent = col.name;
                
                const typeSpan = document.createElement('span');
                typeSpan.className = 'column-type';
                typeSpan.textContent = col.data_type;
                
                if (col.is_pk) {
                    typeSpan.classList.add('column-pk');
                    typeSpan.textContent += ' PK';
                }
                if (col.is_foreign_key) {
                    typeSpan.classList.add('column-fk');
                    typeSpan.textContent += ' FK';
                }
                if (col.nullable === 'Y') {
                    typeSpan.classList.add('column-nullable');
                }
                
                li.appendChild(nameSpan);
                li.appendChild(typeSpan);
                columnsList.appendChild(li);
            });
            
            tooltip.style.left = Math.min(x + 10, window.innerWidth - 420) + 'px';
            tooltip.style.top = Math.max(y - 10, 10) + 'px';
            tooltip.style.display = 'block';
            isTooltipVisible = true;
        }
        
        // 노드 툴팁 숨김
        function hideTooltip() {
            document.getElementById('tooltip').style.display = 'none';
            isTooltipVisible = false;
        }
        
        // 엣지 툴팁 표시
        function showEdgeTooltip(edge, x, y) {
            const edgeTooltip = document.getElementById('edge-tooltip');
            const meta = edge.data('meta');
            
            if (!meta) return;
            
            document.getElementById('edge-tooltip').querySelector('.edge-tooltip-title').textContent = 
                `${meta.src_table}.${meta.src_column} → ${meta.dst_table}.${meta.dst_column}`;
            document.getElementById('edge-tooltip').querySelector('.edge-tooltip-type').textContent = meta.rel_type;
            
            const joinCondition = document.getElementById('edge-tooltip').querySelector('.join-condition');
            if (meta.join_condition) {
                joinCondition.textContent = meta.join_condition;
                joinCondition.style.display = 'block';
            } else {
                joinCondition.style.display = 'none';
            }
            
            const relationDetail = document.getElementById('edge-tooltip').querySelector('.relation-detail');
            relationDetail.innerHTML = `
                <strong>소스:</strong> ${meta.src_table}.${meta.src_column} (${meta.src_data_type})<br>
                <strong>타겟:</strong> ${meta.dst_table}.${meta.dst_column} (${meta.dst_data_type})
            `;
            
            document.getElementById('edge-tooltip').querySelector('.confidence-badge').textContent = 
                `신뢰도 ${Math.round(meta.confidence * 100)}%`;
            document.getElementById('edge-tooltip').querySelector('.frequency-info').textContent = 
                `빈도: ${meta.frequency}회`;
            
            edgeTooltip.style.left = Math.min(x + 10, window.innerWidth - 390) + 'px';
            edgeTooltip.style.top = Math.max(y - 10, 10) + 'px';
            edgeTooltip.style.display = 'block';
            isEdgeTooltipVisible = true;
        }
        
        // 엣지 툴팁 숨김
        function hideEdgeTooltip() {
            document.getElementById('edge-tooltip').style.display = 'none';
            isEdgeTooltipVisible = false;
        }
        
        // 툴바 함수들
        function resetView() {
            cy.layout(layoutOptions[currentLayout]).run();
            cy.fit();
        }
        
        function toggleLayout() {
            currentLayout = currentLayout === 'fcose' ? 'dagre' : 'fcose';
            document.getElementById('current-layout').textContent = currentLayout;
            resetView();
        }
        
        function exportPng() {
            const png = cy.png({
                scale: 2,
                full: true,
                bg: 'white'
            });
            
            const link = document.createElement('a');
            link.download = 'ERD_Dagre_' + new Date().toISOString().slice(0,19).replace(/:/g,'-') + '.png';
            link.href = png;
            link.click();
        }
        
        function exportSvg() {
            const svg = cy.svg({
                full: true,
                bg: 'white'
            });
            
            const blob = new Blob([svg], { type: 'image/svg+xml' });
            const url = URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.download = 'ERD_Dagre_' + new Date().toISOString().slice(0,19).replace(/:/g,'-') + '.svg';
            link.href = url;
            link.click();
            
            URL.revokeObjectURL(url);
        }
        
        // 페이지 로드 시 초기화
        document.addEventListener('DOMContentLoaded', function() {
            initCytoscape();
        });
        """


if __name__ == '__main__':
    # 테스트용 실행
    templates = ReportTemplates()
    html = templates.get_callchain_template(
        project_name='test',
        timestamp='2025-01-14 14:30:00',
        stats={'java_classes': 10, 'database_tables': 5, 'xml_files': 3, 'jsp_files': 2, 'join_relations': 8},
        chain_data=[],
        filter_options={'tables': ['USERS', 'PRODUCTS'], 'query_types': ['SELECT', 'INSERT']}
    )
    print(html[:500] + '...')

