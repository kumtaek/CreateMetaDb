"""
ERD(Dagre) Report HTML 템플릿 관리
"""

from typing import Dict, List, Any
import json


class ERDDagreTemplates:
    """ERD(Dagre) Report 템플릿 관리 클래스"""
    
    def get_erd_dagre_template(self, project_name: str, timestamp: str, stats: Dict[str, int], 
                              erd_data: Dict[str, Any], show_attributes: bool = True) -> str:
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
        {self._get_erd_dagre_javascript(project_name, show_attributes)}
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
    
    def _get_erd_dagre_javascript(self, project_name: str, show_attributes: bool) -> str:
        """ERD(Dagre) Report JavaScript - 프로젝트명 동적 처리"""
        return f"""
        // ERD Dagre 초기화 및 이벤트 처리
        let cy;
        let currentLayout = 'dagre';
        let tooltipTimeout;
        let edgeTooltipTimeout;
        let isTooltipVisible = false;
        let isEdgeTooltipVisible = false;
        const SHOW_ATTRIBUTES = {str(show_attributes).lower()};
        
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
                // 마우스 커서 위치 중심 줌 활성화
                zoomingEnabled: true,
                userZoomingEnabled: true,
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'background-color': '#f5f7ff',
                            'label': 'data(display_label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'color': '#0f172a',
                            'font-size': '13px',
                            'font-weight': '600',
                            'text-outline-width': 0,
                            'text-wrap': 'wrap',
                            'text-max-width': '260px',
                            'text-margin-y': 0,
                            'text-margin-x': 0,
                            'text-justification': 'center',
                            'width': 'label',
                            'height': 'label',
                            'min-width': '220px',
                            'min-height': '140px',
                            'border-width': 3,
                            'border-color': '#1e3a8a',
                            'shape': 'round-rectangle',
                            'padding': '18px',
                            'shadow-blur': 12,
                            'shadow-color': '#cbd5e1',
                            'shadow-opacity': 0.7
                        }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 3,
                            'line-color': '#5f6b7a',
                            'target-arrow-color': '#0f172a',
                            'target-arrow-shape': 'triangle',
                            'target-arrow-fill': 'filled',
                            'arrow-scale': 1.8,
                            'source-arrow-shape': 'none',
                            'source-endpoint': 'outside-to-node',
                            'target-endpoint': 'outside-to-node',
                            'curve-style': 'bezier',
                            'label': 'data(label)',
                            'font-size': '11px',
                            'font-weight': 'bold',
                            'color': '#1f2937',
                            'text-rotation': 'none',
                            'text-margin-y': -15,
                            'text-background-color': '#ffffff',
                            'text-background-opacity': 0.9,
                            'text-background-padding': '3px',
                            'text-background-shape': 'roundrectangle',
                            'text-border-color': '#ddd',
                            'text-border-width': 1,
                            'text-border-opacity': 0.8
                        }}
                    }}
                ],
                layout: {{
                    name: 'dagre',              // 초기 레이아웃: dagre (계층형)
                    animate: true,
                    animationDuration: 1000,
                    nodeSep: 150,               // 노드 간 간격 확대 (80 → 150) - 엔티티 겹침 방지
                    edgeSep: 100,               // 엣지 간 간격 확대 (50 → 100) - 관계선 분리
                    rankSep: 200,               // 계층 간 간격 확대 (120 → 200) - 수직 공간 확보
                    rankDir: 'TB',              // 위에서 아래로 배치
                    align: 'UL',                // 정렬 방식 변경 (DR → UL) - 좌상단 정렬로 겹침 최소화
                    ranker: 'network-simplex'   // 최적 계층 배치 알고리즘
                }}
            }});
            
            applyNodeLabels();
        }}
        
        function applyNodeLabels() {{
            cy.nodes().forEach((node) => {{
                const baseLabel = node.data('label');
                const displayLabel = node.data('display_label') || baseLabel;
                const finalLabel = SHOW_ATTRIBUTES ? displayLabel : baseLabel;
                node.data('display_label', finalLabel);
                node.style('label', finalLabel);
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
                    nodeRepulsion: 50000,       // 노드 간 반발력 극대화 (25000 → 50000) - 겹침 완전 방지
                    idealEdgeLength: 500,       // 이상적인 엣지 길이 증가 (400 → 500)
                    edgeElasticity: 0.1,        // 엣지 탄성력 최소화 (0.2 → 0.1)
                    nestingFactor: 0.01,        // 중첩 방지 극대화
                    gravity: 0.02,              // 중력 더욱 감소 (0.05 → 0.02) - 노드 분산
                    numIter: 5000,              // 반복 횟수 증가 (4000 → 5000)
                    tile: true,                 // 타일링 활성화
                    tilingPaddingVertical: 200, // 수직 패딩 증가 (150 → 200)
                    tilingPaddingHorizontal: 200, // 수평 패딩 증가 (150 → 200)
                    initialTemp: 500,           // 초기 온도 증가 (300 → 500)
                    coolingFactor: 0.99,        // 더욱 천천히 냉각 (0.98 → 0.99)
                    minTemp: 0.3,               // 최소 온도 감소 (0.5 → 0.3)
                    nodeSeparation: 200,        // 노드 최소 간격 추가
                    spacingFactor: 2.0,         // 전체 간격 배율 추가
                    avoidOverlap: true,         // 겹침 방지 활성화
                    avoidOverlapPadding: 50     // 겹침 방지 패딩
                }};
            }} else if (currentLayout === 'dagre') {{
                layoutOptions = {{
                    ...layoutOptions,
                    nodeSep: 150,               // 노드 간 간격 확대 (80 → 150)
                    edgeSep: 100,               // 엣지 간 간격 확대 (50 → 100)
                    rankSep: 200,               // 계층 간 간격 확대 (120 → 200)
                    rankDir: 'TB',              // 위에서 아래로 배치
                    align: 'UL',                // 좌상단 정렬
                    ranker: 'network-simplex'   // 최적 계층 배치
                }};
            }} else if (currentLayout === 'circle') {{
                layoutOptions = {{
                    ...layoutOptions,
                    radius: 600,                // 원의 반지름 더 확대
                    padding: 150,               // 원 주변 패딩 증가
                    startAngle: 0,              // 시작 각도
                    sweep: Math.PI * 2,         // 전체 원 (360도)
                    clockwise: true,            // 시계 방향
                    sort: function(a, b) {{     // 노드 정렬 (이름순)
                        return a.data('label').localeCompare(b.data('label'));
                    }},
                    spacingFactor: 1.5          // 노드 간 간격 조정
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
            
            // 마우스 휠 줌 이벤트 커스터마이징 (Ctrl + 휠)
            cy.container().addEventListener('wheel', function(e) {{
                if (e.ctrlKey) {{
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // 마우스 커서 위치를 기준으로 줌 중심점 계산
                    const rect = cy.container().getBoundingClientRect();
                    const mouseX = e.clientX - rect.left;
                    const mouseY = e.clientY - rect.top;
                    
                    // 현재 줌 레벨과 포지션 저장
                    const currentZoom = cy.zoom();
                    const currentPan = cy.pan();
                    
                    // 줌 비율 계산
                    const zoomFactor = 1.1;
                    let newZoom = currentZoom;
                    
                    if (e.deltaY < 0) {{
                        // 휠을 위로: 확대
                        newZoom = Math.min(currentZoom * zoomFactor, 3);
                    }} else {{
                        // 휠을 아래로: 축소
                        newZoom = Math.max(currentZoom / zoomFactor, 0.1);
                    }}
                    
                    // 줌 비율이 변경된 경우에만 적용
                    if (newZoom !== currentZoom) {{
                        // 마우스 커서 위치를 Cytoscape 좌표계로 변환
                        const mousePos = cy.renderer().projectIntoViewport(mouseX, mouseY);
                        
                        // 줌 중심점 계산
                        const zoomCenter = {{
                            x: mousePos.x,
                            y: mousePos.y
                        }};
                        
                        // 줌 적용 (마우스 커서 위치 중심)
                        cy.zoom({{
                            level: newZoom,
                            renderedPosition: zoomCenter
                        }});
                    }}
                }}
            }}, {{ passive: false }});
        }}
        """
