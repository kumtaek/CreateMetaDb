"""
리포트 HTML 템플릿 관리
- CallChain Report 템플릿
- ERD Report 템플릿
"""

from typing import Dict, List, Any
from util.logger import handle_error


class ReportTemplates:
    """리포트 템플릿 관리 클래스"""
    
    def get_callchain_template(self, project_name: str, timestamp: str, stats: Dict[str, int], 
                              chain_data: List[Dict[str, Any]], filter_options: Dict[str, List[str]]) -> str:
        """CallChain Report HTML 템플릿 생성"""
        
        # 통계 카드 HTML 생성
        stats_html = self._generate_stats_html(stats)
        
        # 연계 체인 테이블 HTML 생성
        table_html = self._generate_chain_table_html(chain_data)
        
        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CallChain Report - {project_name}</title>
    <link rel="stylesheet" href="css/woori.css">
</head>
<body class="callchain-body">
    <div class="callchain-container">
        <div class="callchain-header">
            <h1>CallChain Report</h1>
            <div class="subtitle">Method-Class-Method-XML-Query-Table 연계 정보</div>
            <div class="subtitle">프로젝트: {project_name} | 생성일시: {timestamp}</div>
        </div>
        {stats_html}
        <div class="callchain-content">
            <div class="callchain-section">
                <div class="callchain-table-container">
                    <table id="chainTable" class="callchain-table">
                        <thead>
                            <tr>
                                <th>Frontend</th>
                                <th>API_URL</th>
                                <th>클래스</th>
                                <th>메서드 (Layer)</th>
                                <th>XML파일</th>
                                <th>쿼리ID (Layer)</th>
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
        """통계 카드 HTML 생성 - 그리드 컬럼 순서와 동일하게 정렬"""
        return f"""
        <div class="callchain-stats">
            <div class="callchain-stat-card">
                <div class="callchain-stat-number">{stats.get('frontend_files', 0)}</div>
                <div class="callchain-stat-label">Frontend Files</div>
            </div>
            <div class="callchain-stat-card">
                <div class="callchain-stat-number">{stats.get('java_classes', 0)}</div>
                <div class="callchain-stat-label">Java 클래스</div>
            </div>
            <div class="callchain-stat-card">
                <div class="callchain-stat-number">{stats.get('xml_files', 0)}</div>
                <div class="callchain-stat-label">XML 파일</div>
            </div>
            <div class="callchain-stat-card">
                <div class="callchain-stat-number">{stats.get('database_tables', 0)}</div>
                <div class="callchain-stat-label">데이터베이스 테이블</div>
            </div>
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
            
            # 각 셀별로 NO-QUERY 여부를 개별적으로 판단
            xml_file_class = ' no-query' if data.get('xml_file') == 'NO-QUERY' else ''
            query_id_class = ' no-query' if data.get('query_id') == 'NO-QUERY' else ''
            query_type_class = ' no-query' if data.get('query_type') == 'NO-QUERY' else ''
            
            # 툴팁이 있는 경우와 없는 경우 분기
            if sql_content:
                query_type_html = f'<span class="callchain-badge query-type{query_type_class} tooltip" data-query="{escaped_sql}">{data["query_type"]}<span class="tooltiptext">{escaped_sql}</span></span>'
            else:
                query_type_html = f'<span class="callchain-badge query-type{query_type_class}">{data["query_type"]}</span>'
            
            # 관련테이블 표시 로직: NO-QUERY인 경우는 NO-QUERY, QUERY인 경우는 빈 값일 때 공란
            if data.get('query_type') == 'CALCULATION_ONLY' or data.get('query_id') == 'NO-QUERY':
                related_tables_display = 'NO-QUERY'
                related_tables_class = ' no-query'
            else:
                related_tables_display = data['related_tables'] if data['related_tables'] else ''
                related_tables_class = ''
            
            # Layer 정보를 포함한 메서드와 쿼리 표시
            method_layer = data.get('method_layer', 'APPLICATION')
            query_layer = data.get('query_layer', 'DATA')
            method_color = data.get('method_color', '#e1f5fe')
            query_color = data.get('query_color', '#f1f8e9')
            
            # 안전한 HTML 생성 (크로스플랫폼 호환) - Layer 정보 포함
            rows.append(f"""
                <tr>
                    <td><span class="callchain-badge">{data.get('jsp_file', '')}</span></td>
                    <td><span class="callchain-badge">{data.get('api_entry', '')}</span></td>
                    <td><span class="callchain-badge">{data['class_name']}</span></td>
                    <td>
                        <span class="callchain-badge" style="background-color: {method_color}; border: 1px solid #ccc;">
                            {data['method_name']}
                            <br><small style="color: #666;">({method_layer})</small>
                        </span>
                    </td>
                    <td><span class="callchain-badge{xml_file_class}">{data['xml_file']}</span></td>
                    <td>
                        <span class="callchain-badge{query_id_class}" style="background-color: {query_color}; border: 1px solid #ccc;">
                            {data['query_id']}
                            <br><small style="color: #666;">({query_layer})</small>
                        </span>
                    </td>
                    <td>{query_type_html}</td>
                    <td><span class="callchain-badge{related_tables_class}">{related_tables_display}</span></td>
                </tr>""")
        
        return '\n'.join(rows)
    
    def _get_callchain_css(self) -> str:
        """CallChain Report CSS 스타일"""
        return """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 2px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            width: 100%;
            max-width: 100%;
            margin: 0;
            background: white;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
            min-height: 100vh;
        }
        .header {
            background: var(--gradient-header);
            color: var(--text-on-primary);
            padding: 8px;
            text-align: center;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-light);
            margin-bottom: 3px;
            padding-bottom: 3px;
        }
        .header h1 {
            margin: 0;
            font-size: 1.4em;
            font-weight: 300;
            color: var(--text-on-primary);
        }
        .header .subtitle {
            margin: 2px 0 0 0;
            opacity: 0.9;
            font-size: 0.8em;
            color: var(--text-on-primary);
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 6px;
            padding: 6px;
            background: #f8f9fa;
            margin-bottom: 3px;
        }
        .stat-card {
            background: white;
            padding: 6px;
            border-radius: 4px;
            text-align: center;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-1px);
        }
        .stat-number {
            font-size: 1.0em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 1px;
        }
        .stat-label {
            color: #7f8c8d;
            font-size: 0.6em;
        }
        .content {
            padding: 4px;
        }
        .section {
            margin-bottom: 5px;
        }
        .section h2 {
            color: #2c3e50;
            border-bottom: 1px solid #3498db;
            padding-bottom: 2px;
            margin-bottom: 5px;
            font-size: 0.9em;
        }
        .table-container {
            overflow-x: auto;
            margin: 5px 0;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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
            padding: 4px 6px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
            font-size: 0.8em;
        }
        td {
            padding: 4px 6px;
            border-bottom: 1px solid #ecf0f1;
            vertical-align: top;
        }
        tr:hover {
            background-color: #f8f9fa;
        }
        .chain-id, .frontend, .api-url, .jsp-file, .class-name, .method-name, .xml-file, .query-id, .query-type, .tables, .frontend-api, .api-entry {
            background: #f8f9fa;
            color: #495057;
            padding: 2px 4px;
            border: 1px solid #dee2e6;
            border-radius: 2px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 0.8em;
            white-space: nowrap;
        }
        .filter-controls {
            background: #ecf0f1;
            padding: 4px;
            border-radius: 4px;
            margin-bottom: 5px;
        }
        .filter-controls input, .filter-controls select {
            margin: 2px;
            padding: 4px 6px;
            border: 1px solid #bdc3c7;
            border-radius: 3px;
            font-size: 0.8em;
        }
        .filter-controls button {
            background: #3498db;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 3px;
            cursor: pointer;
            margin: 2px;
            font-size: 0.8em;
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
        
        // 툴팁 기능 초기화
        document.addEventListener('DOMContentLoaded', function() {
            // query-type 툴팁 요소들을 찾아서 이벤트 리스너 추가
            const queryTypeElements = document.querySelectorAll('.query-type.tooltip');
            
            queryTypeElements.forEach(function(element) {
                element.addEventListener('mouseenter', function() {
                    const tooltip = this.querySelector('.tooltiptext');
                    if (tooltip) {
                        tooltip.style.visibility = 'visible';
                        tooltip.style.opacity = '1';
                        tooltip.style.zIndex = '1000';
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
            
            // CSS 호버 방식도 함께 활성화 (백업)
            const style = document.createElement('style');
            style.textContent = `
                .query-type.tooltip:hover .tooltiptext {
                    visibility: visible !important;
                    opacity: 1 !important;
                    z-index: 1000 !important;
                }
            `;
            document.head.appendChild(style);
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
    <link rel="stylesheet" href="css/woori.css">
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
                    <button onclick="exportPng()">PNG 내보내기</button>
                    <button onclick="exportSvg()">SVG 내보내기</button>
                    <div class="zoom-hint">
                        <span class="hint-icon">🔍</span>
                        <span class="hint-text">CTRL+휠: 확대/축소 | 드래그: 이동</span>
                    </div>
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
        <div id="mermaid-container" class="mermaid-container">
            <div id="zoom-indicator" class="zoom-indicator">100%</div>
            <div id="erd-diagram" class="mermaid">
                {mermaid_code}
            </div>
        </div>"""
    
    def _get_erd_css(self) -> str:
        """ERD Report CSS 스타일"""
        return """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 2px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            width: 100%;
            max-width: 100%;
            margin: 0;
            background: white;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
            min-height: 100vh;
        }
        .content {
            padding: 4px;
        }
        .section {
            margin-bottom: 5px;
        }
        .section h2 {
            color: #2c3e50;
            border-bottom: 1px solid #3498db;
            padding-bottom: 2px;
            margin-bottom: 5px;
            font-size: 0.9em;
        }
        .diagram-controls {
            margin-bottom: 5px;
        }
        .diagram-controls button {
            background: #3498db;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 3px;
            cursor: pointer;
            margin: 2px;
            font-size: 0.8em;
        }
        .diagram-controls button:hover {
            background: #2980b9;
        }
        .zoom-hint {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            border: 2px solid #2196f3;
            border-radius: 8px;
            padding: 8px 12px;
            margin-left: 8px;
            box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);
            animation: pulse 2s infinite;
        }
        .hint-icon {
            font-size: 16px;
            animation: bounce 1.5s infinite;
        }
        .hint-text {
            font-size: 12px;
            font-weight: 600;
            color: #1976d2;
            white-space: nowrap;
        }
        @keyframes pulse {
            0%, 100% { 
                box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);
                transform: scale(1);
            }
            50% { 
                box-shadow: 0 4px 16px rgba(33, 150, 243, 0.4);
                transform: scale(1.02);
            }
        }
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-3px); }
            60% { transform: translateY(-2px); }
        }
        .mermaid-container {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border: 1px solid #e9ecef;
            position: relative;
            overflow: auto;
            max-height: 80vh;
            width: 100%;
            box-sizing: border-box;
        }
        
        .mermaid {
            text-align: center;
            min-width: 100%;
            min-height: 400px;
            overflow: visible;
        }
        
        /* 스크롤바 스타일링 */
        .mermaid-container::-webkit-scrollbar {
            width: 12px;
            height: 12px;
        }
        
        .mermaid-container::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 6px;
        }
        
        .mermaid-container::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 6px;
        }
        
        .mermaid-container::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        
        /* 줌 상태 표시 */
        .zoom-indicator {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            z-index: 1000;
        }
        
        .controls {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 0 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s;
        }
        
        .btn:hover {
            background: #2980b9;
        }
        
        .btn.secondary {
            background: #95a5a6;
        }
        
        .btn.secondary:hover {
            background: #7f8c8d;
        }
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 10px;
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
            flowchart: {
                useMaxWidth: false,
                htmlLabels: true,
                curve: 'basis'
            },
            er: {
                useMaxWidth: false,
                htmlLabels: true
            }
        });
        
        // 줌 및 팬 컨트롤
        let currentZoom = 1;
        let isPanning = false;
        let startX, startY, scrollLeft, scrollTop;
        
        function zoomIn() {
            currentZoom = Math.min(currentZoom * 1.2, 3);
            applyZoom();
        }
        
        function zoomOut() {
            currentZoom = Math.max(currentZoom / 1.2, 0.3);
            applyZoom();
        }
        
        function resetZoom() {
            currentZoom = 1;
            applyZoom();
            // 스크롤도 초기화
            const container = document.getElementById('mermaid-container');
            if (container) {
                container.scrollTop = 0;
                container.scrollLeft = 0;
            }
        }
        
        function exportPng() {
            try {
                // Mermaid 다이어그램을 PNG로 내보내기
                const diagram = document.getElementById('erd-diagram');
                if (!diagram) {
                    alert('다이어그램을 찾을 수 없습니다.');
                    return;
                }
                
                // html2canvas 라이브러리 사용
                if (typeof html2canvas === 'undefined') {
                    // html2canvas 라이브러리 동적 로드
                    const script = document.createElement('script');
                    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
                    script.onload = () => performPngExport();
                    document.head.appendChild(script);
                } else {
                    performPngExport();
                }
                
                function performPngExport() {
                    // 전체 다이어그램을 캡처하기 위해 컨테이너 사용
                    const container = document.getElementById('mermaid-container');
                    if (!container) {
                        alert('다이어그램 컨테이너를 찾을 수 없습니다.');
                        return;
                    }
                    
                    html2canvas(container, {
                        backgroundColor: '#ffffff',
                        scale: 2,
                        useCORS: true,
                        allowTaint: true,
                        scrollX: 0,
                        scrollY: 0,
                        width: container.scrollWidth,
                        height: container.scrollHeight
                    }).then(canvas => {
                        const link = document.createElement('a');
                        link.download = 'erd_diagram_full.png';
                        link.href = canvas.toDataURL();
                        link.click();
                    }).catch(err => {
                        console.error('PNG 내보내기 실패:', err);
                        alert('PNG 내보내기에 실패했습니다.');
                    });
                }
            } catch (error) {
                console.error('PNG 내보내기 오류:', error);
                alert('PNG 내보내기 중 오류가 발생했습니다.');
            }
        }
        
        function exportSvg() {
            try {
                // Mermaid 다이어그램을 SVG로 내보내기
                const diagram = document.getElementById('erd-diagram');
                if (!diagram) {
                    alert('다이어그램을 찾을 수 없습니다.');
                    return;
                }
                
                // SVG 요소 찾기
                const svgElement = diagram.querySelector('svg');
                if (!svgElement) {
                    alert('SVG 요소를 찾을 수 없습니다.');
                    return;
                }
                
                // SVG의 전체 크기 정보 추가
                const svgClone = svgElement.cloneNode(true);
                const bbox = svgElement.getBBox();
                svgClone.setAttribute('width', bbox.width + 100);
                svgClone.setAttribute('height', bbox.height + 100);
                svgClone.setAttribute('viewBox', `${bbox.x - 50} ${bbox.y - 50} ${bbox.width + 100} ${bbox.height + 100}`);
                
                // SVG 내용을 문자열로 변환
                const svgData = new XMLSerializer().serializeToString(svgClone);
                const svgBlob = new Blob([svgData], {type: 'image/svg+xml;charset=utf-8'});
                const svgUrl = URL.createObjectURL(svgBlob);
                
                // 다운로드 링크 생성
                const link = document.createElement('a');
                link.href = svgUrl;
                link.download = 'erd_diagram_full.svg';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(svgUrl);
                
            } catch (error) {
                console.error('SVG 내보내기 오류:', error);
                alert('SVG 내보내기 중 오류가 발생했습니다.');
            }
        }
        
        function applyZoom() {
            const diagram = document.getElementById('erd-diagram');
            const indicator = document.getElementById('zoom-indicator');
            if (diagram) {
                diagram.style.transform = `scale(${currentZoom})`;
                diagram.style.transformOrigin = 'center top';
                diagram.style.transition = 'transform 0.2s ease';
            }
            if (indicator) {
                indicator.textContent = Math.round(currentZoom * 100) + '%';
            }
        }
        
        function downloadSVG() {
            const svg = document.querySelector('#erd-diagram svg');
            if (svg) {
                const svgData = new XMLSerializer().serializeToString(svg);
                const svgBlob = new Blob([svgData], {type: 'image/svg+xml;charset=utf-8'});
                const svgUrl = URL.createObjectURL(svgBlob);
                const downloadLink = document.createElement('a');
                downloadLink.href = svgUrl;
                downloadLink.download = 'sampleSrc_ERD.svg';
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
                URL.revokeObjectURL(svgUrl);
            }
        }
        
        // 드래그로 팬 기능 초기화
        function initPanAndZoom() {
            const container = document.getElementById('mermaid-container');
            if (!container) return;
            
            // 마우스 드래그로 팬
            container.addEventListener('mousedown', function(e) {
                if (e.button === 0) { // 왼쪽 마우스 버튼
                    isPanning = true;
                    startX = e.pageX - container.offsetLeft;
                    startY = e.pageY - container.offsetTop;
                    scrollLeft = container.scrollLeft;
                    scrollTop = container.scrollTop;
                    container.style.cursor = 'grabbing';
                    e.preventDefault();
                }
            });
            
            container.addEventListener('mouseleave', function() {
                isPanning = false;
                container.style.cursor = 'grab';
            });
            
            container.addEventListener('mouseup', function() {
                isPanning = false;
                container.style.cursor = 'grab';
            });
            
            container.addEventListener('mousemove', function(e) {
                if (!isPanning) return;
                e.preventDefault();
                const x = e.pageX - container.offsetLeft;
                const y = e.pageY - container.offsetTop;
                const walkX = (x - startX) * 2;
                const walkY = (y - startY) * 2;
                container.scrollLeft = scrollLeft - walkX;
                container.scrollTop = scrollTop - walkY;
            });
            
            // 마우스 휠로 줌 (Ctrl + 휠)
            container.addEventListener('wheel', function(e) {
                if (e.ctrlKey) {
                    e.preventDefault();
                    if (e.deltaY < 0) {
                        zoomIn();
                    } else {
                        zoomOut();
                    }
                }
            });
            
            // 기본 커서 설정
            container.style.cursor = 'grab';
        }
        
        // 키보드 단축키
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey) {
                switch(e.key) {
                    case '=':
                    case '+':
                        e.preventDefault();
                        zoomIn();
                        break;
                    case '-':
                        e.preventDefault();
                        zoomOut();
                        break;
                    case '0':
                        e.preventDefault();
                        resetZoom();
                        break;
                }
            }
        });
        
        // 페이지 로드 시 다이어그램 렌더링 및 기능 초기화
        window.addEventListener('load', function() {
            mermaid.init(undefined, '.mermaid').then(function() {
                // 렌더링 완료 후 팬/줌 기능 초기화
                setTimeout(initPanAndZoom, 500);
                // 초기 줌 표시 업데이트
                applyZoom();
            });
        });
        """

    def get_architecture_template(self, project_name: str, timestamp: str, stats: Dict[str, int], 
                                layer_data: Dict[str, List[Dict[str, Any]]], relationships: Dict[str, List[Dict[str, Any]]]) -> str:
        """Architecture Report HTML 템플릿 생성 (기존 리포트와 동일한 구조)"""
        
        # 통계 카드 HTML 생성
        stats_html = self._generate_architecture_stats_html(stats)
        
        # 아키텍처 다이어그램 HTML 생성 (기존 구조)
        diagram_html = self._generate_architecture_diagram_html(layer_data)
        
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
            <div class="diagram-header">
                <h2>아키텍처 구조 다이어그램</h2>
                <div class="diagram-controls">
                    <button onclick="exportLayerCSV()">레이어별 컴포넌트 CSV 다운로드</button>
                    <button onclick="exportDiagramSVG()">다이어그램 SVG 내보내기</button>
                    <button onclick="exportDiagramPNG()">다이어그램 PNG 내보내기</button>
                </div>
            </div>
            <div class="diagram-container" id="architecture-diagram-container">
                {diagram_html}
            </div>
        </div>
        
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
    
    def _generate_architecture_diagram_html(self, layer_data: Dict[str, List[Dict[str, Any]]]) -> str:
        """HTML 기반 아키텍처 다이어그램 생성 (기존 리포트와 동일한 구조, 기타 레이어 포함)"""
        try:
            # 레이어별 컴포넌트 수 계산
            controller_count = len(layer_data.get('controller', []))
            service_count = len(layer_data.get('service', []))
            mapper_count = len(layer_data.get('mapper', []))
            model_count = len(layer_data.get('model', []))
            etc_count = len(layer_data.get('etc', []))
            
            # HTML 다이어그램 생성
            diagram_html = f"""
            <div class="architecture-diagram">
                <div class="layer-container">
                    
        <div class="layer controller-layer" style="background-color: #e3f2fd; border-color: #1976d2;">
            <div class="layer-header">
                <h3>Controller Layer ({controller_count}개)</h3>
            </div>
            <div class="components-container">
                {self._generate_layer_components_html(layer_data.get('controller', []))}
            </div>
        </div>
        
                    <div class="layer-arrow">↓</div>
                    
        <div class="layer service-layer" style="background-color: #e1f5fe; border-color: #1565c0;">
            <div class="layer-header">
                <h3>Service Layer ({service_count}개)</h3>
            </div>
            <div class="components-container">
                {self._generate_layer_components_html(layer_data.get('service', []))}
            </div>
        </div>
        
                    <div class="layer-arrow">↓</div>
                    
        <div class="layer mapper-layer" style="background-color: #e8f5e8; border-color: #1b5e20;">
            <div class="layer-header">
                <h3>Mapper Layer ({mapper_count}개)</h3>
            </div>
            <div class="components-container">
                {self._generate_layer_components_html(layer_data.get('mapper', []))}
            </div>
        </div>
        
                    <div class="layer-arrow">↓</div>
                    
        <div class="layer model-layer" style="background-color: #f1f8ff; border-color: #0d47a1;">
            <div class="layer-header">
                <h3>Model Layer ({model_count}개)</h3>
            </div>
            <div class="components-container">
                {self._generate_layer_components_html(layer_data.get('model', []))}
            </div>
        </div>
        
                    <div class="layer-arrow">↓</div>
                    
        <div class="layer etc-layer" style="background-color: #fafafa; border-color: #757575;">
            <div class="layer-header">
                <h3>Etc Layer ({etc_count}개)</h3>
            </div>
            <div class="components-container">
                {self._generate_layer_components_html(layer_data.get('etc', []))}
            </div>
        </div>
        
                </div>
            </div>"""
            
            return diagram_html
            
        except Exception as e:
            handle_error(e, "HTML 다이어그램 생성 실패")
            return ""
    
    def _generate_layer_components_html(self, components: List[Dict[str, Any]]) -> str:
        """레이어별 컴포넌트 HTML 생성 (30개 이상 시 생략 표시)"""
        if not components:
            return '<div class="empty-layer">컴포넌트가 없습니다.</div>'
        
        max_display = 30
        if len(components) <= max_display:
            # 모든 컴포넌트 표시
            component_htmls = []
            for component in components:
                component_name = component.get('component_name', 'Unknown')
                component_htmls.append(f'<div class="component">{component_name}</div>')
            return ''.join(component_htmls)
        else:
            # 처음 30개만 표시하고 나머지는 생략
            component_htmls = []
            for component in components[:max_display]:
                component_name = component.get('component_name', 'Unknown')
                component_htmls.append(f'<div class="component">{component_name}</div>')
            
            remaining_count = len(components) - max_display
            component_htmls.append(f'<div class="component more-indicator">...외 {remaining_count}건</div>')
            return ''.join(component_htmls)
    
    
    def _get_architecture_css(self) -> str:
        """Architecture Report CSS 스타일 (크로스플랫폼 호환, 반응형 지원)"""
        return """
        
        :root {
            /* === 메인 컬러 === */
            --primary-blue: #1976d2;         /* 메인 브랜드 블루 */
            --primary-dark: #0d47a1;         /* 진한 블루 (강조용) */
            --primary-light: #42a5f5;        /* 밝은 블루 (액션 버튼) */
            --primary-pale: #e3f2fd;         /* 아주 연한 블루 (배경) */
            
            /* === 보조 컬러 === */
            --secondary-blue: #1565c0;       /* 보조 블루 */
            --accent-blue: #2196f3;          /* 액센트 블루 */
            --sky-blue: #81d4fa;             /* 하늘색 */
            --ice-blue: #f1f8ff;             /* 아이스 블루 (최상단 배경) */
            
            /* === 그라데이션 === */
            --gradient-main: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%);
            --gradient-subtle: linear-gradient(135deg, #e3f2fd 0%, #ffffff 100%);
            --gradient-header: linear-gradient(90deg, #0d47a1 0%, #1976d2 100%);
            
            /* === 중성 컬러 === */
            --gray-50: #fafafa;
            --gray-100: #f5f5f5;
            --gray-200: #eeeeee;
            --gray-300: #e0e0e0;
            --gray-400: #bdbdbd;
            --gray-500: #9e9e9e;
            --gray-600: #757575;
            --gray-700: #616161;
            --gray-800: #424242;
            --gray-900: #212121;
            
            /* === 텍스트 컬러 === */
            --text-primary: #212121;
            --text-secondary: #616161;
            --text-hint: #9e9e9e;
            --text-on-primary: #ffffff;
            
            /* === 상태 컬러 === */
            --success: #4caf50;
            --warning: #ff9800;
            --error: #f44336;
            --info: var(--primary-blue);
            
            /* === 쉐도우 === */
            --shadow-light: 0 2px 4px rgba(25, 118, 210, 0.12);
            --shadow-medium: 0 4px 8px rgba(25, 118, 210, 0.16);
            --shadow-heavy: 0 8px 16px rgba(25, 118, 210, 0.24);
            
            /* === 보더 === */
            --border-light: 1px solid rgba(25, 118, 210, 0.12);
            --border-medium: 1px solid rgba(25, 118, 210, 0.24);
            --border-radius: 8px;
            --border-radius-small: 4px;
            --border-radius-large: 12px;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 5px;
            background-color: var(--ice-blue);
            line-height: 1.4;
        }
        .container {
            max-width: 95%;
            margin: 0 auto;
            background: white;
            padding: 8px;
            border-radius: var(--border-radius-large);
            box-shadow: var(--shadow-medium);
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 8px;
            text-align: center;
            margin-bottom: 5px;
        }
        .header h1 {
            margin: 0;
            font-size: 1.5em;
            font-weight: 300;
            color: white;
        }
        .header .subtitle {
            margin: 3px 0 0 0;
            opacity: 0.8;
            font-size: 0.9em;
            color: white;
        }
        .section {
            margin: 2px 0;
            padding: 3px;
            border-left: 3px solid var(--primary-blue);
            background-color: var(--primary-pale);
        }
        .section h2 {
            color: var(--primary-blue);
            margin-top: 0;
            margin-bottom: 2px;
            font-size: 1.1em;
        }
        .diagram-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }
        .diagram-header h2 {
            margin: 0;
            flex: 1;
        }
        .diagram-controls {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 8px;
        }
        .diagram-controls button {
            background: #3498db;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.7em;
            transition: all 0.3s ease;
        }
        .diagram-controls button:hover {
            background: #2980b9;
            transform: translateY(-1px);
        }
        .diagram-container {
            background: white;
            padding: 2px;
            border-radius: var(--border-radius);
            margin: 2px 0;
            box-shadow: var(--shadow-light);
            width: 100%;
            box-sizing: border-box;
        }
        .stats-table {
            width: 100%;
            border-collapse: collapse;
            margin: 5px 0;
            background: white;
            border-radius: var(--border-radius);
            overflow: hidden;
            box-shadow: var(--shadow-light);
        }
        .stats-table th, .stats-table td {
            border: var(--border-light);
            padding: 4px;
            text-align: left;
        }
        .stats-table th {
            background-color: var(--primary-blue);
            color: var(--text-on-primary);
            font-weight: bold;
        }
        .stats-table tr:nth-child(even) {
            background-color: var(--gray-50);
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
            color: var(--text-secondary);
            font-size: 0.9em;
            margin-top: 30px;
            padding-top: 20px;
            border-top: var(--border-light);
        }
        
        /* 반응형 아키텍처 다이어그램 스타일 */
        .architecture-diagram {
            width: 100%;
            margin: 20px 0;
        }
        
        .layer-container {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .layer {
            border: 2px solid;
            border-radius: 8px;
            padding: 15px;
            /* 높이 자동 조정 - min-height 제거 */
        }
        
        .layer-header {
            margin-bottom: 15px;
        }
        
        .layer-header h3 {
            margin: 0;
            font-size: 1.1em;
            font-weight: bold;
        }
        
        .components-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }
        
        .component {
            background: white;
            border: 1px solid var(--primary-blue);
            border-radius: var(--border-radius-small);
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 500;
            min-width: 120px;
            text-align: center;
            box-shadow: var(--shadow-light);
            color: var(--text-primary);
            transition: all 0.2s ease;
        }
        .component:hover {
            background-color: var(--primary-pale);
            border-color: var(--primary-dark);
            box-shadow: var(--shadow-medium);
        }
        
        .layer-arrow {
            text-align: center;
            font-size: 24px;
            color: var(--primary-blue);
            margin: 10px 0;
            font-weight: bold;
        }
        
        .empty-layer {
            text-align: center;
            color: var(--text-hint);
            font-style: italic;
        }
        
        .more-indicator {
            background: var(--primary-pale) !important;
            border-color: var(--primary-blue) !important;
            color: var(--primary-blue) !important;
            font-weight: bold !important;
        }
        
        /* 반응형 브레이크포인트 */
        @media (max-width: 1200px) {
            .component {
                min-width: 110px;
                font-size: 11px;
                padding: 6px 10px;
            }
        }
        
        @media (max-width: 992px) {
            .component {
                min-width: 100px;
                font-size: 10px;
                padding: 5px 8px;
            }
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                padding: 15px;
            }
            .header h1 {
                font-size: 1.8em;
            }
            .component {
                min-width: 90px;
                font-size: 9px;
                padding: 4px 6px;
            }
            .layer {
                padding: 10px;
            }
            .relationship-grid {
                grid-template-columns: 1fr;
            }
            .diagram-controls {
                flex-direction: column;
                align-items: stretch;
            }
            .controls-right {
                justify-content: center;
            }
            .diagram-controls button {
                margin: 2px 0;
            }
        }
        
        @media (max-width: 576px) {
            .component {
                min-width: 80px;
                font-size: 8px;
                padding: 3px 5px;
            }
            .layer-header h3 {
                font-size: 1em;
            }
        }
        """
    
    def _get_architecture_javascript(self) -> str:
        """Architecture Report JavaScript (CSV, SVG, PNG 내보내기 기능 포함)"""
        return """
        // 오프라인 환경 지원을 위한 JavaScript
        // 외부 라이브러리 의존성 없이 순수 JavaScript로 구현
        
        // 레이어별 컴포넌트 데이터 (서버에서 주입)
        let layerComponentData = {};
        
        // 다이어그램 확대/축소 기능 (간단한 버전)
        function zoomDiagram(scale) {
            const diagram = document.querySelector('.architecture-diagram');
            if (diagram) {
                diagram.style.transform = `scale(${scale})`;
                diagram.style.transformOrigin = 'center center';
            }
        }
        
        // 레이어별 컴포넌트 CSV 내보내기
        function exportLayerCSV() {
            try {
                // 각 레이어별로 컴포넌트 수집
                const layers = ['controller', 'service', 'mapper', 'model'];
                let csvContent = 'Layer,Component_Name,Component_Type,File_Path\\n';
                
                layers.forEach(layerName => {
                    const layerDiv = document.querySelector(`.${layerName}-layer`);
                    if (layerDiv) {
                        const components = layerDiv.querySelectorAll('.component');
                        components.forEach(component => {
                            const componentName = component.textContent.trim();
                            // "...외 N건" 형태는 제외
                            if (!componentName.includes('...외') && !componentName.includes('컴포넌트가 없습니다')) {
                                csvContent += `${layerName.toUpperCase()},${componentName},CLASS,\\n`;
                            }
                        });
                    }
                });
                
                // CSV 파일 다운로드
                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                const url = URL.createObjectURL(blob);
                link.setAttribute('href', url);
                link.setAttribute('download', 'architecture_components_by_layer.csv');
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
                
                alert('레이어별 컴포넌트 CSV 파일이 다운로드되었습니다.');
            } catch (error) {
                console.error('CSV 내보내기 오류:', error);
                alert('CSV 내보내기 중 오류가 발생했습니다.');
            }
        }
        
        // 다이어그램 SVG 내보내기
        function exportDiagramSVG() {
            try {
                const diagramContainer = document.getElementById('architecture-diagram-container');
                if (!diagramContainer) {
                    alert('다이어그램을 찾을 수 없습니다.');
                    return;
                }
                
                // HTML을 SVG로 변환
                const svgContent = createSVGFromHTML(diagramContainer);
                const blob = new Blob([svgContent], { type: 'image/svg+xml;charset=utf-8;' });
                const link = document.createElement('a');
                const url = URL.createObjectURL(blob);
                link.setAttribute('href', url);
                link.setAttribute('download', 'architecture_diagram.svg');
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
                
                alert('다이어그램 SVG 파일이 다운로드되었습니다.');
            } catch (error) {
                console.error('SVG 내보내기 오류:', error);
                alert('SVG 내보내기 중 오류가 발생했습니다.');
            }
        }
        
        // 다이어그램 PNG 내보내기
        function exportDiagramPNG() {
            try {
                const diagramContainer = document.getElementById('architecture-diagram-container');
                if (!diagramContainer) {
                    alert('다이어그램을 찾을 수 없습니다.');
                    return;
                }
                
                // html2canvas 라이브러리 동적 로드 및 사용
                if (typeof html2canvas === 'undefined') {
                    const script = document.createElement('script');
                    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
                    script.onload = () => performPNGExport(diagramContainer);
                    script.onerror = () => {
                        // 오프라인 환경에서는 캔버스 기반 대안 사용
                        performCanvasPNGExport(diagramContainer);
                    };
                    document.head.appendChild(script);
                } else {
                    performPNGExport(diagramContainer);
                }
            } catch (error) {
                console.error('PNG 내보내기 오류:', error);
                alert('PNG 내보내기 중 오류가 발생했습니다.');
            }
        }
        
        // html2canvas를 사용한 PNG 내보내기
        function performPNGExport(container) {
            html2canvas(container, {
                backgroundColor: '#ffffff',
                scale: 2,
                useCORS: true,
                allowTaint: true,
                scrollX: 0,
                scrollY: 0,
                width: container.scrollWidth,
                height: container.scrollHeight
            }).then(canvas => {
                const link = document.createElement('a');
                link.download = 'architecture_diagram.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
                alert('다이어그램 PNG 파일이 다운로드되었습니다.');
            }).catch(err => {
                console.error('PNG 내보내기 실패:', err);
                alert('PNG 내보내기에 실패했습니다.');
            });
        }
        
        // 대안 캔버스 기반 PNG 내보내기 (오프라인 환경용)
        function performCanvasPNGExport(container) {
            // 간단한 캔버스 기반 렌더링 (텍스트만)
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = 1200;
            canvas.height = 800;
            
            // 배경 설정
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // 제목 그리기
            ctx.fillStyle = '#1976d2';
            ctx.font = 'bold 24px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('시스템 아키텍처 다이어그램', canvas.width / 2, 50);
            
            // 레이어별 컴포넌트 텍스트 렌더링
            let yPos = 100;
            const layers = ['controller', 'service', 'mapper', 'model'];
            const layerColors = ['#e3f2fd', '#e1f5fe', '#e8f5e8', '#f1f8ff'];
            
            layers.forEach((layerName, index) => {
                const layerDiv = document.querySelector(`.${layerName}-layer`);
                if (layerDiv) {
                    // 레이어 박스 그리기
                    ctx.fillStyle = layerColors[index];
                    ctx.fillRect(100, yPos, canvas.width - 200, 120);
                    ctx.strokeStyle = '#1976d2';
                    ctx.lineWidth = 2;
                    ctx.strokeRect(100, yPos, canvas.width - 200, 120);
                    
                    // 레이어 제목
                    ctx.fillStyle = '#1976d2';
                    ctx.font = 'bold 18px Arial';
                    ctx.textAlign = 'left';
                    ctx.fillText(`${layerName.toUpperCase()} LAYER`, 120, yPos + 25);
                    
                    // 컴포넌트 나열
                    const components = layerDiv.querySelectorAll('.component');
                    let componentText = '';
                    let count = 0;
                    components.forEach(component => {
                        const name = component.textContent.trim();
                        if (!name.includes('...외') && !name.includes('컴포넌트가 없습니다') && count < 10) {
                            componentText += name + ', ';
                            count++;
                        }
                    });
                    if (componentText) {
                        componentText = componentText.slice(0, -2); // 마지막 쉼표 제거
                        if (count >= 10) componentText += '...';
                    }
                    
                    ctx.fillStyle = '#424242';
                    ctx.font = '12px Arial';
                    ctx.textAlign = 'left';
                    const words = componentText.split(' ');
                    let line = '';
                    let lineY = yPos + 50;
                    
                    for (let n = 0; n < words.length; n++) {
                        const testLine = line + words[n] + ' ';
                        const metrics = ctx.measureText(testLine);
                        const testWidth = metrics.width;
                        if (testWidth > canvas.width - 240 && n > 0) {
                            ctx.fillText(line, 120, lineY);
                            line = words[n] + ' ';
                            lineY += 15;
                        } else {
                            line = testLine;
                        }
                    }
                    ctx.fillText(line, 120, lineY);
                    
                    yPos += 150;
                }
            });
            
            // PNG 다운로드
            const link = document.createElement('a');
            link.download = 'architecture_diagram.png';
            link.href = canvas.toDataURL('image/png');
            link.click();
            alert('다이어그램 PNG 파일이 다운로드되었습니다.');
        }
        
        // HTML을 SVG로 변환하는 함수
        function createSVGFromHTML(element) {
            const rect = element.getBoundingClientRect();
            const svgWidth = Math.max(rect.width, 1200);
            const svgHeight = Math.max(rect.height, 800);
            
            let svgContent = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${svgWidth}" height="${svgHeight}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <style>
            .layer-box { fill: #e3f2fd; stroke: #1976d2; stroke-width: 2; }
            .layer-text { font-family: Arial, sans-serif; font-size: 18px; font-weight: bold; fill: #1976d2; }
            .component-text { font-family: Arial, sans-serif; font-size: 12px; fill: #424242; }
        </style>
    </defs>
    <rect width="100%" height="100%" fill="white"/>
    <text x="${svgWidth/2}" y="30" text-anchor="middle" font-family="Arial" font-size="24" font-weight="bold" fill="#1976d2">시스템 아키텍처 다이어그램</text>
`;
            
            let yPos = 80;
            const layers = ['controller', 'service', 'mapper', 'model'];
            const layerColors = ['#e3f2fd', '#e1f5fe', '#e8f5e8', '#f1f8ff'];
            
            layers.forEach((layerName, index) => {
                const layerDiv = document.querySelector(`.${layerName}-layer`);
                if (layerDiv) {
                    // 레이어 박스
                    svgContent += `<rect x="50" y="${yPos}" width="${svgWidth-100}" height="120" fill="${layerColors[index]}" stroke="#1976d2" stroke-width="2"/>`;
                    
                    // 레이어 제목
                    svgContent += `<text x="70" y="${yPos + 25}" class="layer-text">${layerName.toUpperCase()} LAYER</text>`;
                    
                    // 컴포넌트 텍스트
                    const components = layerDiv.querySelectorAll('.component');
                    let componentText = '';
                    let count = 0;
                    components.forEach(component => {
                        const name = component.textContent.trim();
                        if (!name.includes('...외') && !name.includes('컴포넌트가 없습니다') && count < 15) {
                            componentText += name + ', ';
                            count++;
                        }
                    });
                    if (componentText) {
                        componentText = componentText.slice(0, -2);
                        if (count >= 15) componentText += '...';
                    }
                    
                    // 텍스트를 여러 줄로 분할
                    const words = componentText.split(' ');
                    let line = '';
                    let lineY = yPos + 50;
                    const maxWidth = svgWidth - 140;
                    
                    for (let n = 0; n < words.length; n++) {
                        const testLine = line + words[n] + ' ';
                        if (testLine.length * 7 > maxWidth && n > 0) { // 대략적인 문자 폭 계산
                            svgContent += `<text x="70" y="${lineY}" class="component-text">${line.trim()}</text>`;
                            line = words[n] + ' ';
                            lineY += 15;
                        } else {
                            line = testLine;
                        }
                    }
                    if (line.trim()) {
                        svgContent += `<text x="70" y="${lineY}" class="component-text">${line.trim()}</text>`;
                    }
                    
                    yPos += 150;
                }
            });
            
            svgContent += '</svg>';
            return svgContent;
        }
        
        // 다이어그램 초기화
        document.addEventListener('DOMContentLoaded', function() {
            // 반응형 처리
            const diagram = document.querySelector('.architecture-diagram');
            if (diagram) {
                diagram.style.maxWidth = '100%';
                diagram.style.height = 'auto';
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
    
    def get_erd_mg_template(self, project_name: str, timestamp: str, stats: Dict[str, int], 
                           erd_data: Dict[str, Any]) -> str:
        """ERD(MG) Report HTML 템플릿 생성 - Magic MCP 스타일"""
        
        # 통계 카드 HTML 생성
        stats_html = self._generate_erd_mg_stats_html(stats)
        
        # ERD 다이어그램 HTML 생성
        erd_diagram_html = self._generate_erd_mg_diagram_html(erd_data)
        
        # 테이블 상세 정보 HTML 생성
        table_details_html = self._generate_erd_mg_table_details_html(erd_data)
        
        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - Magic MCP 스타일 ERD</title>
    <style>
        {self._get_erd_mg_css()}
    </style>
</head>
<body>
    <div class="container">
        <div class="header fade-in-up">
            <h1>🗄️ {project_name} 데이터베이스 ERD</h1>
            <div class="subtitle">Magic MCP 스타일 고급 ERD 다이어그램</div>
            <div class="subtitle">생성일시: {timestamp}</div>
        </div>
        
        {stats_html}
        
        <div class="erd-container fade-in-up">
            <h2 class="erd-title">🔗 Magic MCP 스타일 ERD 다이어그램</h2>
            
            <div class="controls">
                <button class="control-btn" onclick="resetLayout()">🔍 레이아웃 초기화</button>
                <button class="control-btn" onclick="autoLayout()">📐 자동 배치</button>
                <button class="control-btn" onclick="toggleGlow()">✨ 글로우 효과</button>
                <button class="control-btn" onclick="exportSVG()">📷 SVG 저장</button>
                <button class="control-btn" onclick="toggleAnimation()">🎭 애니메이션</button>
            </div>
            
            <div class="erd-diagram" id="erdDiagram">
                {erd_diagram_html}
            </div>
        </div>
        
        {table_details_html}
        
        <div class="footer fade-in-up">
            <p>이 문서는 Magic MCP의 Database With REST API 컴포넌트 디자인을 적용하여 구현되었습니다.</p>
            <p>분석 시간: {timestamp}</p>
        </div>
    </div>
    
    <script>
        {self._get_erd_mg_javascript()}
    </script>
</body>
</html>"""
    
    def _generate_erd_mg_stats_html(self, stats: Dict[str, int]) -> str:
        """ERD(MG) 통계 카드 HTML 생성"""
        return f"""
        <div class="stats-grid fade-in-up">
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_tables', 0)}</div>
                <div class="stat-label">테이블</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_columns', 0)}</div>
                <div class="stat-label">컬럼</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('relationships', 0)}</div>
                <div class="stat-label">관계</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('avg_columns_per_table', 0)}</div>
                <div class="stat-label">평균 컬럼/테이블</div>
            </div>
        </div>"""
    
    def _generate_erd_mg_diagram_html(self, erd_data: Dict[str, Any]) -> str:
        """ERD(MG) 다이어그램 HTML 생성"""
        tables_data = erd_data.get('tables', {})
        relationships = erd_data.get('relationships', [])
        
        # 테이블 노드 HTML 생성
        table_nodes_html = []
        for i, (table_name, table_info) in enumerate(tables_data.items()):
            columns = table_info.get('columns', [])
            
            # 테이블 위치 계산 (그리드 레이아웃)
            row = i // 4
            col = i % 4
            left = col * 280 + 50
            top = row * 220 + 50
            
            # 컬럼 HTML 생성
            columns_html = []
            for column in columns:
                pk_badge = '<span class="pk-badge">PK</span>' if column.get('is_primary_key') else ''
                fk_badge = '<span class="fk-badge">FK</span>' if column.get('is_foreign_key') else ''
                
                columns_html.append(f"""
                    <li class="column-item">
                        {column['column_name']} ({column['data_type']})
                        {pk_badge}
                        {fk_badge}
                    </li>""")
            
            table_nodes_html.append(f"""
            <div class="table-node" data-table="{table_name}" style="left: {left}px; top: {top}px;">
                <div class="table-header">{table_name}</div>
                <ul class="column-list">
                    {''.join(columns_html)}
                </ul>
            </div>""")
        
        # 관계선 HTML 생성
        relationship_lines_html = []
        for rel in relationships:
            relationship_lines_html.append(f"""
                <div class="relationship-line" 
                     data-from="{rel['src_table']}" 
                     data-to="{rel['dst_table']}"
                     style="width: 200px; left: 0px; top: 0px; transform: rotate(0deg);">
                </div>""")
        
        return ''.join(table_nodes_html) + ''.join(relationship_lines_html)
    
    def _generate_erd_mg_table_details_html(self, erd_data: Dict[str, Any]) -> str:
        """ERD(MG) 테이블 상세 정보 HTML 생성"""
        tables_data = erd_data.get('tables', {})
        schema_groups = erd_data.get('schema_groups', {})
        
        details_html = []
        details_html.append('<div class="erd-container fade-in-up">')
        details_html.append('<h2 class="erd-title">📊 테이블 상세 정보</h2>')
        
        for schema, table_names in schema_groups.items():
            details_html.append(f'<h3>🎯 {schema} 스키마 ({len(table_names)}개 테이블)</h3>')
            
            for table_name in table_names:
                table_info = tables_data.get(table_name, {})
                columns = table_info.get('columns', [])
                table_comment = table_info.get('table_comment', f'{schema}.{table_name} 테이블')
                
                # 통계 계산
                pk_count = sum(1 for col in columns if col.get('is_primary_key'))
                fk_count = sum(1 for col in columns if col.get('is_foreign_key'))
                
                # 컬럼 상세 HTML 생성
                columns_detail_html = []
                for column in columns:
                    pk_badge = '<span class="pk-badge">PK</span>' if column.get('is_primary_key') else ''
                    fk_badge = '<span class="fk-badge">FK</span>' if column.get('is_foreign_key') else ''
                    comment = f'<br><small>{column["column_comment"]}</small>' if column.get('column_comment') else ''
                    
                    columns_detail_html.append(f"""
                        <li class="column-item">
                            <strong>{column['column_name']}</strong> ({column['data_type']})
                            {pk_badge}
                            {fk_badge}
                            {comment}
                        </li>""")
                
                details_html.append(f"""
                <div class="table-info">
                    <h3>📊 {table_name}</h3>
                    <p><strong>전체명:</strong> {schema}.{table_name}</p>
                    <p><strong>설명:</strong> {table_comment}</p>
                    
                    <div class="table-meta">
                        <div class="meta-item">
                            <div class="meta-number">{len(columns)}</div>
                            <div class="meta-label">컬럼</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-number">{pk_count}</div>
                            <div class="meta-label">기본키</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-number">{fk_count}</div>
                            <div class="meta-label">외래키</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-number">VALID</div>
                            <div class="meta-label">상태</div>
                        </div>
                    </div>
                    
                    <h4>📝 컬럼 목록</h4>
                    <ul class="column-list">
                        {''.join(columns_detail_html)}
                    </ul>
                </div>""")
        
        details_html.append('</div>')
        return ''.join(details_html)
    
    def _get_erd_mg_css(self) -> str:
        """ERD(MG) Report CSS 스타일 - Magic MCP 스타일"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0f0f23;
            min-height: 100vh;
            color: #ffffff;
            overflow-x: auto;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: var(--gradient-header);
            color: var(--text-on-primary);
            padding: 8px;
            border-radius: var(--border-radius);
            text-align: center;
            margin-bottom: 3px;
            padding-bottom: 3px;
            box-shadow: var(--shadow-light);
        }
        
        .header h1 {
            font-size: 1.4em;
            font-weight: 300;
            margin: 0;
            color: var(--text-on-primary);
        }
        
        .header .subtitle {
            opacity: 0.9;
            font-size: 0.8em;
            color: var(--text-on-primary);
            margin-top: 2px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 6px;
            padding: 6px;
            background: #f8f9fa;
            margin-bottom: 3px;
        }
        
        .stat-card {
            background: white;
            padding: 6px;
            border-radius: 4px;
            text-align: center;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            transition: left 0.5s;
        }
        
        .stat-card:hover::before {
            left: 100%;
        }
        
        .stat-card:hover {
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 25px 50px rgba(0,0,0,0.4);
            border-color: #00d4ff;
        }
        
        .stat-number {
            font-size: 1.2em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 2px;
        }
        
        .stat-label {
            color: #7f8c8d;
            font-size: 0.7em;
            font-weight: 500;
        }
        
        .erd-container {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 40px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.3);
            border: 1px solid #2d3748;
            overflow: hidden;
        }
        
        .erd-title {
            color: #ffffff;
            border-bottom: 3px solid #00d4ff;
            padding-bottom: 20px;
            margin-bottom: 30px;
            font-size: 2.2em;
            text-align: center;
        }
        
        .controls {
            background: rgba(45, 55, 72, 0.5);
            padding: 25px;
            text-align: center;
            border-bottom: 1px solid #2d3748;
            margin-bottom: 30px;
            border-radius: 15px;
        }
        
        .control-btn {
            background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            margin: 0 10px;
            border-radius: 12px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .control-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }
        
        .control-btn:hover::before {
            left: 100%;
        }
        
        .control-btn:hover {
            background: linear-gradient(135deg, #0099cc 0%, #006699 100%);
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(0, 212, 255, 0.4);
        }
        
        .control-btn:active {
            transform: translateY(-1px);
        }
        
        .erd-diagram {
            background: #0f0f23;
            border-radius: 15px;
            padding: 30px;
            border: 1px solid #2d3748;
            position: relative;
            min-height: 600px;
            overflow: hidden;
        }
        
        .table-node {
            position: absolute;
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            border: 2px solid #00d4ff;
            border-radius: 15px;
            padding: 20px;
            min-width: 200px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: move;
        }
        
        .table-node:hover {
            transform: scale(1.05);
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            border-color: #ff6b6b;
        }
        
        .table-header {
            background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
            color: white;
            padding: 10px 15px;
            border-radius: 10px;
            text-align: center;
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 15px;
        }
        
        .column-list {
            list-style: none;
        }
        
        .column-item {
            background: rgba(255,255,255,0.05);
            margin: 8px 0;
            padding: 10px 15px;
            border-radius: 8px;
            border-left: 3px solid #4a5568;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            transition: all 0.3s ease;
        }
        
        .column-item:hover {
            background: rgba(255,255,255,0.1);
            border-left-color: #00d4ff;
        }
        
        .pk-badge {
            background: #ff6b6b;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            margin-left: 10px;
            font-weight: bold;
        }
        
        .fk-badge {
            background: #00d4ff;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            margin-left: 10px;
            font-weight: bold;
        }
        
        .relationship-line {
            position: absolute;
            background: linear-gradient(90deg, #ff6b6b, #00d4ff);
            height: 3px;
            border-radius: 2px;
            transform-origin: left center;
            box-shadow: 0 0 10px rgba(255, 107, 107, 0.5);
            z-index: 1;
        }
        
        .relationship-line::after {
            content: '';
            position: absolute;
            right: -10px;
            top: -4px;
            width: 0;
            height: 0;
            border-left: 10px solid #00d4ff;
            border-top: 5px solid transparent;
            border-bottom: 5px solid transparent;
        }
        
        .table-info {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 15px;
            padding: 25px;
            margin: 25px 0;
            border: 1px solid #2d3748;
            transition: all 0.3s ease;
        }
        
        .table-info:hover {
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transform: translateX(5px);
            border-color: #00d4ff;
        }
        
        .table-info h3 {
            color: #00d4ff;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-bottom: 2px solid #2d3748;
            padding-bottom: 10px;
        }
        
        .table-meta {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        
        .meta-item {
            text-align: center;
            padding: 15px;
            background: rgba(45, 55, 72, 0.5);
            border-radius: 12px;
            border: 1px solid #2d3748;
            transition: all 0.3s ease;
        }
        
        .meta-item:hover {
            border-color: #00d4ff;
            background: rgba(45, 55, 72, 0.8);
        }
        
        .meta-number {
            font-size: 1.8em;
            font-weight: bold;
            color: #00d4ff;
            margin-bottom: 8px;
        }
        
        .meta-label {
            color: #a0aec0;
            font-size: 0.8em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .footer {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            text-align: center;
            padding: 30px;
            border-radius: 20px;
            font-size: 1em;
            border: 1px solid #2d3748;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            
            .header h1 {
                font-size: 2.2em;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .table-meta {
                grid-template-columns: 1fr;
            }
            
            .control-btn {
                margin: 5px;
                padding: 12px 20px;
                font-size: 14px;
            }
        }
        
        /* 애니메이션 */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(40px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .fade-in-up {
            animation: fadeInUp 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        @keyframes float {
            0%, 100% {
                transform: translateY(0px);
            }
            50% {
                transform: translateY(-10px);
            }
        }
        
        .float {
            animation: float 3s ease-in-out infinite;
        }
        
        @keyframes glow {
            0%, 100% {
                box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
            }
            50% {
                box-shadow: 0 0 30px rgba(0, 212, 255, 0.6);
            }
        }
        
        .glow {
            animation: glow 2s ease-in-out infinite;
        }
        """
    
    def _get_erd_mg_javascript(self) -> str:
        """ERD(MG) Report JavaScript - Magic MCP 스타일"""
        return """
        // 테이블 노드 드래그 기능
        let isDragging = false;
        let currentDragElement = null;
        let dragOffset = { x: 0, y: 0 };
        
        // 초기화
        document.addEventListener('DOMContentLoaded', function() {
            setupDragAndDrop();
            setupAnimations();
        });
        
        function setupDragAndDrop() {
            const tableNodes = document.querySelectorAll('.table-node');
            
            tableNodes.forEach(node => {
                node.addEventListener('mousedown', startDrag);
                node.addEventListener('touchstart', startDrag);
            });
            
            document.addEventListener('mousemove', drag);
            document.addEventListener('touchmove', drag);
            document.addEventListener('mouseup', endDrag);
            document.addEventListener('touchend', endDrag);
        }
        
        function startDrag(e) {
            e.preventDefault();
            isDragging = true;
            currentDragElement = e.target.closest('.table-node');
            
            const rect = currentDragElement.getBoundingClientRect();
            const clientX = e.type === 'mousedown' ? e.clientX : e.touches[0].clientX;
            const clientY = e.type === 'mousedown' ? e.clientY : e.touches[0].clientY;
            
            dragOffset.x = clientX - rect.left;
            dragOffset.y = clientY - rect.top;
            
            currentDragElement.style.zIndex = '1000';
        }
        
        function drag(e) {
            if (!isDragging || !currentDragElement) return;
            
            e.preventDefault();
            const clientX = e.type === 'mousemove' ? e.clientX : e.touches[0].clientX;
            const clientY = e.type === 'mousemove' ? e.clientY : e.touches[0].clientY;
            
            const newX = clientX - dragOffset.x;
            const newY = clientY - dragOffset.y;
            
            currentDragElement.style.left = newX + 'px';
            currentDragElement.style.top = newY + 'px';
            
            updateRelationshipLines();
        }
        
        function endDrag() {
            if (currentDragElement) {
                currentDragElement.style.zIndex = '1';
                currentDragElement = null;
            }
            isDragging = false;
        }
        
        function updateRelationshipLines() {
            const lines = document.querySelectorAll('.relationship-line');
            lines.forEach(line => {
                const fromTable = line.getAttribute('data-from');
                const toTable = line.getAttribute('data-to');
                
                const fromNode = document.querySelector(`[data-table="${fromTable}"]`);
                const toNode = document.querySelector(`[data-table="${toTable}"]`);
                
                if (fromNode && toNode) {
                    const fromRect = fromNode.getBoundingClientRect();
                    const toRect = toNode.getBoundingClientRect();
                    const diagramRect = document.getElementById('erdDiagram').getBoundingClientRect();
                    
                    const fromX = fromRect.left + fromRect.width / 2 - diagramRect.left;
                    const fromY = fromRect.top + fromRect.height / 2 - diagramRect.top;
                    const toX = toRect.left + toRect.width / 2 - diagramRect.left;
                    const toY = toRect.top + toRect.height / 2 - diagramRect.top;
                    
                    const length = Math.sqrt(Math.pow(toX - fromX, 2) + Math.pow(toY - fromY, 2));
                    const angle = Math.atan2(toY - fromY, toX - fromX) * 180 / Math.PI;
                    
                    line.style.width = length + 'px';
                    line.style.left = fromX + 'px';
                    line.style.top = fromY + 'px';
                    line.style.transform = `rotate(${angle}deg)`;
                }
            });
        }
        
        function setupAnimations() {
            const tableNodes = document.querySelectorAll('.table-node');
            tableNodes.forEach((node, index) => {
                node.style.animationDelay = (index * 0.1) + 's';
                node.classList.add('fade-in-up');
            });
        }
        
        // 컨트롤 함수들
        function resetLayout() {
            const tableNodes = document.querySelectorAll('.table-node');
            tableNodes.forEach((node, index) => {
                const row = Math.floor(index / 4);
                const col = index % 4;
                node.style.left = (col * 250 + 50) + 'px';
                node.style.top = (row * 200 + 50) + 'px';
            });
            updateRelationshipLines();
        }
        
        function autoLayout() {
            // 자동 레이아웃 알고리즘 (간단한 그리드)
            const tableNodes = document.querySelectorAll('.table-node');
            const cols = Math.ceil(Math.sqrt(tableNodes.length));
            
            tableNodes.forEach((node, index) => {
                const row = Math.floor(index / cols);
                const col = index % cols;
                node.style.left = (col * 280 + 50) + 'px';
                node.style.top = (row * 220 + 50) + 'px';
            });
            updateRelationshipLines();
        }
        
        function toggleGlow() {
            const tableNodes = document.querySelectorAll('.table-node');
            tableNodes.forEach(node => {
                node.classList.toggle('glow');
            });
        }
        
        function exportSVG() {
            // SVG 내보내기 기능 (간단한 구현)
            alert('SVG 내보내기 기능은 개발 중입니다.');
        }
        
        function toggleAnimation() {
            const tableNodes = document.querySelectorAll('.table-node');
            tableNodes.forEach(node => {
                node.classList.toggle('float');
            });
        }
        
        // 초기 레이아웃 설정
        setTimeout(() => {
            autoLayout();
        }, 100);
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

