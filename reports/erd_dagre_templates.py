"""
ERD(Dagre) Report HTML 템플릿 관리
"""

from typing import Dict, List, Any
import json


class ERDDagreTemplates:
    """ERD(Dagre) Report 템플릿 관리 클래스"""
    
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
    <title>ERD Dagre Report - {project_name}</title>
    <link rel="stylesheet" href="css/woori.css">
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
<body class="erd-dagre-body">
    <div class="erd-dagre-container">
        <div class="erd-dagre-header">
            <h1>ERD Dagre Report</h1>
            <div class="subtitle">프로젝트: {project_name} | 생성일시: {timestamp}</div>
            <div id="toolbar">
                <button onclick="resetView()">초기화</button>
                <button onclick="toggleLayout()">레이아웃 전환</button>
                <button onclick="exportPng()">PNG 내보내기</button>
                <button onclick="exportSvg()">SVG 내보내기</button>
                <input type="text" id="search" placeholder="테이블명으로 검색..." />
                <span id="current-layout">dagre</span>
            </div>
        </div>
        <div class="erd-dagre-content">
            <div id="cy"></div>
        </div>
        
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
        {stats_html}
    </div>
    
    <script>
        {self._get_erd_dagre_javascript(project_name)}
    </script>
</body>
</html>"""
    
    def _generate_erd_dagre_stats_html(self, stats: Dict[str, int]) -> str:
        """ERD(Dagre) 통계 카드 HTML 생성 - 콜체인리포트와 동일한 구조"""
        return f"""
        <div class="erd-dagre-stats">
            <div class="erd-dagre-stat-card">
                <div class="erd-dagre-stat-number">{stats.get('total_tables', 0)}</div>
                <div class="erd-dagre-stat-label">전체 테이블</div>
            </div>
            <div class="erd-dagre-stat-card">
                <div class="erd-dagre-stat-number">{stats.get('total_columns', 0)}</div>
                <div class="erd-dagre-stat-label">전체 컬럼</div>
            </div>
            <div class="erd-dagre-stat-card">
                <div class="erd-dagre-stat-number">{stats.get('primary_keys', 0)}</div>
                <div class="erd-dagre-stat-label">Primary Key</div>
            </div>
            <div class="erd-dagre-stat-card">
                <div class="erd-dagre-stat-number">{stats.get('foreign_keys', 0)}</div>
                <div class="erd-dagre-stat-label">Foreign Key</div>
            </div>
            <div class="erd-dagre-stat-card">
                <div class="erd-dagre-stat-number">{stats.get('relationships', 0)}</div>
                <div class="erd-dagre-stat-label">관계</div>
            </div>
        </div>"""
    
    def _generate_cytoscape_json(self, erd_data: Dict[str, Any]) -> str:
        """Cytoscape.js 데이터 JSON 생성"""
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
        body.erd-dagre-body { 
            margin: 0; 
            height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 0;
            background: white;
            overflow: hidden;
        }
        .erd-dagre-container {
            height: 100vh;
            display: flex;
            flex-direction: column;
            background: white;
            overflow: hidden;
        }
        .erd-dagre-header {
            background: linear-gradient(90deg, #0d47a1 0%, #1976d2 100%);
            color: white;
            padding: 8px;
            text-align: center;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(25, 118, 210, 0.12);
            margin-bottom: 3px;
            padding-bottom: 3px;
            flex-shrink: 0;
        }
        .erd-dagre-header h1 {
            margin: 0;
            font-size: 1.4em;
            font-weight: 300;
        }
        .erd-dagre-header .subtitle {
            margin: 2px 0 0 0;
            opacity: 0.9;
            font-size: 0.8em;
        }
        .erd-dagre-stats {
            display: flex;
            justify-content: space-around;
            align-items: center;
            gap: 4px;
            padding: 2px 4px;
            background: #f8f9fa;
            margin: 0;
            flex-shrink: 0;
            height: 24px;
            min-height: 24px;
        }
        .erd-dagre-stat-card {
            background: white;
            padding: 2px 6px;
            border-radius: 2px;
            text-align: center;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
            display: flex;
            align-items: center;
            gap: 2px;
            white-space: nowrap;
        }
        .erd-dagre-stat-card:hover {
            transform: translateY(-1px);
        }
        .erd-dagre-stat-number {
            font-size: 0.9em;
            font-weight: bold;
            color: #3498db;
            margin: 0;
        }
        .erd-dagre-stat-label {
            color: #7f8c8d;
            font-size: 0.6em;
        }
        .erd-dagre-content {
            flex: 1;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        #toolbar { 
            padding: 4px; 
            border-bottom: 1px solid #ddd; 
            background: #f8f9fa;
            display: flex;
            align-items: center;
            gap: 2px;
            flex-wrap: wrap;
        }
        #cy { 
            width: 100%; 
            height: calc(100vh - 120px);
            background: white;
            overflow: hidden;
        }
        
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        button {
            background: #007bff;
            border: none;
            color: white;
            padding: 4px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 0.8em;
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
        
        .zoom-hint {
            display: flex;
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
            #toolbar {
                padding: 8px;
                gap: 5px;
            }
            #search {
                min-width: 150px;
            }
        }
        """
    
    def _get_erd_dagre_javascript(self, project_name: str) -> str:
        """ERD(Dagre) Report JavaScript - 프로젝트명 동적 처리"""
        return f"""
        // ERD Dagre 초기화 및 이벤트 처리
        let cy;
        let currentLayout = 'dagre';
        let tooltipTimeout;
        let edgeTooltipTimeout;
        let isTooltipVisible = false;
        let isEdgeTooltipVisible = false;
        
        document.addEventListener('DOMContentLoaded', function() {{
            initCytoscape();
            setupEventListeners();
        }});
        
        function initCytoscape() {{
            cy = cytoscape({{
                container: document.getElementById('cy'),
                elements: DATA,
                minZoom: 0.1,
                maxZoom: 3,
                wheelSensitivity: 0.1,  // 마우스 휠 줌 민감도를 0.1으로 설정 (더 둔감하게 조정)
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'background-color': '#4a90e2',
                            'label': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'color': 'white',
                            'font-size': '14px',
                            'font-weight': 'bold',
                            'width': '160px',
                            'height': '80px',
                            'border-width': 3,
                            'border-color': '#1e40af',
                            'shape': 'round-rectangle'
                        }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 3,
                            'line-color': '#7f8c8d',
                            'target-arrow-color': '#7f8c8d',
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier',
                            'label': 'data(label)',
                            'font-size': '10px',
                            'text-rotation': 'autorotate',
                            'text-margin-y': -10
                        }}
                    }}
                ],
                layout: {{
                    name: 'dagre',              // 초기 레이아웃을 dagre로 변경 (하단 레이아웃)
                    animate: true,
                    animationDuration: 1000,
                    nodeSep: 80,                // 노드 간 간격 축소 (200 → 80)
                    edgeSep: 50,                // 엣지 간 간격 축소 (120 → 50)
                    rankSep: 120,               // 계층 간 간격 축소 (300 → 120)
                    rankDir: 'TB',              // 위에서 아래로 배치
                    align: 'DR'                 // 정렬 방식
                }}
            }});
        }}
        
        function resetView() {{
            cy.fit();
            cy.center();
        }}
        
        function toggleLayout() {{
            const layouts = ['fcose', 'dagre', 'circle', 'grid'];
            const currentIndex = layouts.indexOf(currentLayout);
            const nextIndex = (currentIndex + 1) % layouts.length;
            currentLayout = layouts[nextIndex];
            
            document.getElementById('current-layout').textContent = currentLayout;
            
            // 레이아웃별 상세 설정 (더 넓게 퍼지도록)
            let layoutOptions = {{
                name: currentLayout,
                animate: true,
                animationDuration: 1000
            }};
            
            if (currentLayout === 'fcose') {{
                layoutOptions = {{
                    ...layoutOptions,
                    nodeRepulsion: 25000,       // 노드 간 반발력 극대화 (15000 → 25000)
                    idealEdgeLength: 400,       // 이상적인 엣지 길이 더 증가 (300 → 400)
                    edgeElasticity: 0.2,        // 엣지 탄성력 더 감소
                    nestingFactor: 0.01,        // 중첩 방지 극대화
                    gravity: 0.05,              // 중력 극소화 (0.1 → 0.05)
                    numIter: 4000,              // 반복 횟수 더 증가
                    tile: true,                 // 타일링 활성화
                    tilingPaddingVertical: 150, // 수직 패딩 더 증가 (100 → 150)
                    tilingPaddingHorizontal: 150, // 수평 패딩 더 증가 (100 → 150)
                    initialTemp: 300,           // 초기 온도 더 증가
                    coolingFactor: 0.98,        // 더 천천히 냉각
                    minTemp: 0.5                // 최소 온도 감소
                }};
            }} else if (currentLayout === 'dagre') {{
                layoutOptions = {{
                    ...layoutOptions,
                    nodeSep: 80,                // 노드 간 간격 축소 (200 → 80)
                    edgeSep: 50,                // 엣지 간 간격 축소 (120 → 50)
                    rankSep: 120,               // 계층 간 간격 축소 (300 → 120)
                    rankDir: 'TB',              // 위에서 아래로 배치
                    align: 'DR'                 // 정렬 방식
                }};
            }} else if (currentLayout === 'circle') {{
                layoutOptions = {{
                    ...layoutOptions,
                    radius: 400,                // 원의 반지름 확대 (기본값보다 크게)
                    padding: 100,               // 원 주변 패딩
                    startAngle: 0,              // 시작 각도
                    sweep: Math.PI * 2,         // 전체 원 (360도)
                    clockwise: true,            // 시계 방향
                    sort: function(a, b) {{     // 노드 정렬 (이름순)
                        return a.data('label').localeCompare(b.data('label'));
                    }}
                }};
            }} else if (currentLayout === 'grid') {{
                layoutOptions = {{
                    ...layoutOptions,
                    rows: 5,                    // 5행
                    cols: 5,                    // 5열
                    padding: 100                // 그리드 패딩 증가
                }};
            }}
            
            cy.layout(layoutOptions).run();
        }}
        
        function exportPng() {{
            const png = cy.png({{
                scale: 2,
                full: true,
                bg: 'white'
            }});
            
            const link = document.createElement('a');
            link.download = '{project_name}_ERD_Dagre_' + new Date().toISOString().slice(0,19).replace(/:/g,'-') + '.png';
            link.href = png;
            link.click();
        }}
        
        function exportSvg() {{
            try {{
                const svgData = cy.svg({{
                    full: true,
                    scale: 1,
                    quality: 1
                }});
                
                if (svgData) {{
                    const svgBlob = new Blob([svgData], {{type: 'image/svg+xml;charset=utf-8'}});
                    const svgUrl = URL.createObjectURL(svgBlob);
                    
                    const link = document.createElement('a');
                    link.href = svgUrl;
                    link.download = '{project_name}_ERD_Dagre_' + new Date().toISOString().slice(0,19).replace(/:/g,'-') + '.svg';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    URL.revokeObjectURL(svgUrl);
                }} else {{
                    alert('SVG 내보내기에 실패했습니다.');
                }}
            }} catch (error) {{
                console.error('SVG 내보내기 오류:', error);
                alert('SVG 내보내기 중 오류가 발생했습니다.');
            }}
        }}
        
        function setupEventListeners() {{
            // 검색 기능
            const searchInput = document.getElementById('search');
            searchInput.addEventListener('input', function() {{
                const query = this.value.toLowerCase();
                if (query === '') {{
                    cy.elements().style('opacity', 1);
                }} else {{
                    cy.elements().style('opacity', 0.3);
                    cy.elements().filter(function(ele) {{
                        return ele.data('label').toLowerCase().includes(query);
                    }}).style('opacity', 1);
                }}
            }});
        }}
        """
