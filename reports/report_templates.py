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
            <div class="subtitle">JSP-Class-Method-XML-Query-Table 연계 정보</div>
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
                                <th>JSP파일</th>
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
            <input type="text" id="searchInput" placeholder="JSP파일, 클래스, 메서드, 테이블명으로 검색..." style="width: 300px;">
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
                    <td><span class="jsp-file">{data.get('jsp_file', '')}</span></td>
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
                    const tablesCell = cells[7];
                    if (tablesCell.textContent.indexOf(tableFilter) === -1) {
                        shouldShow = false;
                    }
                }
                
                // 쿼리 타입 필터
                if (queryTypeFilter && shouldShow) {
                    const queryTypeCell = cells[6];
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
            csv.push('연계ID,JSP파일,클래스,메서드,XML파일,쿼리ID,쿼리종류,정제된SQL내용,관련테이블들');
            
            for (let i = 1; i < rows.length; i++) {
                const cells = rows[i].getElementsByTagName('td');
                if (cells.length > 0 && rows[i].style.display !== 'none') {
                    let row = [];
                    for (let j = 0; j < cells.length; j++) {
                        let cellText = cells[j].textContent.replace(/"/g, '""');
                        
                        // 쿼리종류 컬럼(인덱스 6)의 경우 정제된 SQL 내용도 포함
                        if (j === 6) {
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
