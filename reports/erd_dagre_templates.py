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
