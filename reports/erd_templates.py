"""
ERD Report HTML 템플릿 관리
"""

from typing import Dict, List, Any


class ERDTemplates:
    """ERD Report 템플릿 관리 클래스"""
    
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
