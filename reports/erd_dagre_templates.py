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
            padding: 2px;
        }
        .container {
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 4px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 1.0em;
            font-weight: 300;
        }
        .header .subtitle {
            margin: 1px 0 0 0;
            opacity: 0.8;
            font-size: 0.6em;
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 2px;
            padding: 4px;
            background: #f8f9fa;
            flex-wrap: wrap;
        }
        .stat-card {
            background: white;
            padding: 3px;
            border-radius: 3px;
            text-align: center;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            min-width: 60px;
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
            flex: 1;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 25%, #cbd5e1 50%, #94a3b8 75%, #64748b 100%);
            background-size: 400% 400%;
            animation: gradientShift 15s ease infinite;
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
                padding: 50,  // 패딩 증가로 고아 엔티티 간격 확대
                nodeDimensionsIncludeLabels: true,
                uniformNodeDimensions: false,
                packComponents: false,  // 컴포넌트 패킹 비활성화로 고아 엔티티 분산
                step: 'all',
                samplingType: false,
                sampleSize: 25,
                nodeSeparation: 200,  // 노드 간격 대폭 증가 (더 넓게)
                piTol: 0.0000001,
                nodeRepulsion: function( node ){ 
                    // 고아 노드(연결이 적은 노드)에 더 강한 반발력 적용
                    const degree = node.degree();
                    return degree < 2 ? 400000 : 200000;  // 고아 노드에 2배 반발력
                },
                idealEdgeLength: function( edge ){ 
                    // 관계선 길이를 동적으로 조정
                    const sourceDegree = edge.source().degree();
                    const targetDegree = edge.target().degree();
                    const avgDegree = (sourceDegree + targetDegree) / 2;
                    return avgDegree > 5 ? 120 : 100;  // 연결이 많은 노드는 더 긴 거리
                },
                edgeElasticity: function( edge ){ 
                    // 관계선 탄성도 동적 조정
                    const sourceDegree = edge.source().degree();
                    const targetDegree = edge.target().degree();
                    return Math.max(30, 100 - (sourceDegree + targetDegree) * 5);  // 연결이 많을수록 탄성도 감소
                },
                nestingFactor: 0.1,
                gravity: 0.15,  // 중력 감소로 고아 엔티티가 더 분산되도록
                numIter: 3000,  // 반복 횟수 증가로 더 나은 배치
                tile: true,
                tilingPaddingVertical: 20,  // 타일링 패딩 증가
                tilingPaddingHorizontal: 20,
                gravityRangeCompound: 1.5,
                gravityCompound: 1.0,
                gravityRange: 4.5,  // 중력 범위 증가
                initialEnergyOnIncremental: 0.3
            },
            dagre: {
                name: 'dagre',
                rankDir: 'TB',
                rankSep: 200,  // 랭크 간격 대폭 증가
                nodeSep: 120,  // 노드 간격 대폭 증가
                edgeSep: 30,   // 엣지 간격 증가
                ranker: 'tight-tree'
            }
        };
        
        // Cytoscape 초기화
        function initCytoscape() {
            cy = cytoscape({
                container: document.getElementById('cy'),
                elements: DATA,
                minZoom: 0.1,
                maxZoom: 3,
                wheelSensitivity: 0.1,  // 휠 줌 감도 줄이기
                style: [
                    {
                        selector: 'node',
                        style: {
                            'background-color': '#1e3a8a',  // 남색으로 변경
                            'background-gradient-stop-colors': '#1e3a8a #1e40af #1d4ed8',
                            'background-gradient-direction': 'to-bottom-right',
                            'label': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'color': 'white',
                            'font-size': '12px',
                            'font-weight': 'bold',
                            'text-outline-width': 2,
                            'text-outline-color': '#1e40af',
                            'width': '120px',
                            'height': '60px',
                            'border-width': 3,
                            'border-color': '#1e40af',
                            'border-style': 'solid',
                            'border-opacity': 0.8,
                            'overlay-opacity': 0,
                            'transition-property': 'background-color, border-color',
                            'transition-duration': '0.3s',
                            'transition-timing-function': 'ease-in-out'
                        }
                    },
                    {
                        selector: 'node[type="table"]',
                        style: {
                            'background-color': '#1e3a8a',  // 남색으로 변경
                            'background-gradient-stop-colors': '#1e3a8a #1e40af #1d4ed8',
                            'background-gradient-direction': 'to-bottom-right',
                            'shape': 'roundrectangle',
                            'border-width': 3,
                            'border-color': '#1e40af',
                            'border-opacity': 0.8,
                            'transition-property': 'background-color, border-color',
                            'transition-duration': '0.3s',
                            'transition-timing-function': 'ease-in-out'
                        }
                    },
                    {
                        selector: 'edge',
                        style: {
                            'width': 3,
                            'line-color': '#7f8c8d',
                            'target-arrow-color': '#7f8c8d',
                            'target-arrow-shape': 'triangle',
                            'target-arrow-size': 8,
                            'curve-style': 'straight',  // 깔끔한 직선 스타일
                            'label': 'data(label)',
                            'font-size': '10px',
                            'text-rotation': 'autorotate',
                            'text-margin-y': -10,
                            'line-opacity': 0.8,
                            'overlay-opacity': 0,
                            'transition-property': 'line-color, target-arrow-color, width',
                            'transition-duration': '0.3s',
                            'transition-timing-function': 'ease-in-out'
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
            
            // 노드 간격 최적화로 관계선 겹침 방지
            optimizeNodeSpacing();
        }
        
        // 노드 간격을 더 넓게 하여 관계선 겹침 방지
        function optimizeNodeSpacing() {
            const nodes = cy.nodes();
            const edges = cy.edges();
            
            // 고아 노드들(연결이 적은 노드)을 더 넓게 분산
            nodes.forEach(node => {
                const degree = node.degree();
                if (degree <= 1) {
                    // 고아 노드의 경우 더 큰 크기로 설정
                    node.style({
                        'width': '140px',
                        'height': '80px'
                    });
                }
            });
            
            // 엣지 라벨 위치 최적화
            edges.forEach(edge => {
                const sourcePos = edge.source().position();
                const targetPos = edge.target().position();
                const midX = (sourcePos.x + targetPos.x) / 2;
                const midY = (sourcePos.y + targetPos.y) / 2;
                
                // 라벨을 엣지 중앙에서 약간 오프셋
                edge.style({
                    'text-margin-y': -15,
                    'text-margin-x': 10
                });
            });
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
                
                // 호버 효과: 그림자 강화 및 크기 증가
                node.style({
                    'width': '130px',
                    'height': '70px',
                    'border-width': 4,
                    'border-color': '#3b82f6'
                });
                
                tooltipTimeout = setTimeout(() => {
                    const renderedPosition = event.renderedPosition;
                    showTooltip(node, renderedPosition.x, renderedPosition.y);
                }, 500);
            });
            
            cy.on('mouseout', 'node', function(event) {
                const node = event.target;
                clearTimeout(tooltipTimeout);
                
                // 호버 효과 복원: 원래 스타일로 되돌리기
                node.style({
                    'width': '120px',
                    'height': '60px',
                    'border-width': 3,
                    'border-color': '#1e40af'
                });
                
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
                
                // 엣지 호버 효과: 두께 증가 및 그림자 강화
                edge.style({
                    'width': 5,
                    'line-color': '#4a5568',
                    'target-arrow-color': '#4a5568'
                });
                
                edgeTooltipTimeout = setTimeout(() => {
                    const renderedPosition = event.renderedPosition;
                    showEdgeTooltip(edge, renderedPosition.x, renderedPosition.y);
                }, 300);
            });
            
            cy.on('mouseout', 'edge', function(event) {
                const edge = event.target;
                clearTimeout(edgeTooltipTimeout);
                
                // 엣지 호버 효과 복원: 원래 스타일로 되돌리기
                edge.style({
                    'width': 3,
                    'line-color': '#7f8c8d',
                    'target-arrow-color': '#7f8c8d'
                });
                
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
            tooltip.style.top = Math.min(y + 20, window.innerHeight - 300) + 'px';  // 아래쪽으로 변경
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
            edgeTooltip.style.top = Math.min(y + 20, window.innerHeight - 200) + 'px';  // 아래쪽으로 변경
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
            
            // 레이아웃 변경 후 노드 간격 최적화 재적용
            cy.layout(layoutOptions[currentLayout]).run().promiseOn('layoutstop').then(() => {
                optimizeNodeSpacing();
                resetView();
            });
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
            try {
                // Cytoscape.js 컨테이너에서 SVG 요소 직접 추출
                const container = document.getElementById('cy');
                const svgElement = container.querySelector('svg');
                
                if (!svgElement) {
                    throw new Error('SVG 요소를 찾을 수 없습니다.');
                }
                
                // SVG 내용을 문자열로 변환
                const svgData = new XMLSerializer().serializeToString(svgElement);
                const svgBlob = new Blob([svgData], {type: 'image/svg+xml;charset=utf-8'});
                const svgUrl = URL.createObjectURL(svgBlob);
                
                // 다운로드 링크 생성
                const link = document.createElement('a');
                link.href = svgUrl;
                link.download = 'ERD_Dagre_' + new Date().toISOString().slice(0,19).replace(/:/g,'-') + '.svg';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(svgUrl);
                
            } catch (error) {
                console.error('SVG 내보내기 오류:', error);
                alert('SVG 내보내기 중 오류가 발생했습니다: ' + error.message);
            }
        }
        
        // 페이지 로드 시 초기화
        document.addEventListener('DOMContentLoaded', function() {
            initCytoscape();
        });
        """
