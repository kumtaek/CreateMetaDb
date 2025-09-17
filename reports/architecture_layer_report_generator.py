"""
새로운 아키텍처 레이어 다이어그램 리포트 생성기
- 가로 방향 레이어 배치
- Layer별 컴포넌트 시각화
- 관계 화살표 표시
- 인터랙티브 기능

USER RULES 준수:
- 공통함수 사용 지향
- handle_error()로 예외 처리
- 크로스플랫폼 대응
- 보편적 동적 로직 구현
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# USER RULES: 공통함수 사용 (기존 리포트 생성기와 동일한 구조)
from util.logger import app_logger, handle_error
from util.path_utils import PathUtils
from util.database_utils import DatabaseUtils
from util.report_utils import ReportUtils
from reports.report_templates import ReportTemplates


class ArchitectureLayerReportGenerator:
    """새로운 아키텍처 레이어 다이어그램 리포트 생성기"""
    
    def __init__(self, project_name: str, output_dir: str):
        """
        초기화
        
        Args:
            project_name: 프로젝트명 (USER RULES: 하드코딩 금지, 동적 처리)
            output_dir: 출력 디렉토리
        """
        self.project_name = project_name
        self.output_dir = output_dir
        
        # USER RULES: 공통함수 사용 (기존 리포트 생성기와 동일한 구조)
        self.path_utils = PathUtils()
        self.report_utils = ReportUtils(project_name, output_dir)
        
        # 메타데이터베이스 연결 (USER RULES: 공통함수 사용)
        self.metadata_db_path = self.path_utils.get_project_metadata_db_path(project_name)
        self.db_utils = DatabaseUtils(self.metadata_db_path)
        
        if not self.db_utils.connect():
            # USER RULES: handle_error()로 예외 처리 및 Exit
            handle_error(Exception("데이터베이스 연결 실패"), f"메타데이터베이스 연결 실패: {self.metadata_db_path}")
        
        # Layer별 색상 정의 (USER RULES: 보편적 로직, 하드코딩 최소화)
        self.layer_colors = self._get_layer_colors()
        
        # Layer 순서 정의 (USER RULES: 동적 구성 가능)
        self.layer_order = self._get_layer_order()
    
    def _get_layer_colors(self) -> Dict[str, str]:
        """Layer별 색상 매핑 반환 (USER RULES: 보편적 로직)"""
        return {
            'FRONTEND': '#e3f2fd',      # 파란색
            'API_ENTRY': '#f3e5f5',     # 보라색  
            'CONTROLLER': '#e8f5e8',    # 초록색
            'SERVICE': '#fff3e0',       # 노란색
            'REPOSITORY': '#ffcc80',    # 주황색
            'MODEL': '#f8bbd9',         # 분홍색
            'UTIL': '#e1f5fe',          # 하늘색
            'QUERY': '#ffcdd2',         # 빨간색
            'TABLE': '#f5f5f5',         # 회색
            'APPLICATION': '#e0e0e0',   # 연회색
            'DATA': '#f1f8e9',          # 연두색
            'DB': '#fff8e1'             # 연노랑색
        }
    
    def _get_layer_order(self) -> List[str]:
        """Layer 순서 정의 (USER RULES: 동적 구성)"""
        return [
            'FRONTEND', 'API_ENTRY', 'CONTROLLER', 'SERVICE', 
            'REPOSITORY', 'MODEL', 'QUERY', 'TABLE', 'UTIL', 
            'APPLICATION', 'DATA', 'DB'
        ]
    
    def generate_report(self) -> bool:
        """
        새로운 아키텍처 레이어 다이어그램 리포트 생성
        
        Returns:
            생성 성공 여부
        """
        try:
            app_logger.info(f"새로운 아키텍처 레이어 다이어그램 리포트 생성 시작: {self.project_name}")
            
            # 1. 데이터 분석 (USER RULES: 공통함수 사용)
            analysis_data = self._analyze_architecture_data()
            if not analysis_data:
                # USER RULES: warning 후 계속 실행하면 안됨, handle_error()로 Exit
                handle_error(Exception("분석할 아키텍처 데이터가 없습니다"), f"아키텍처 데이터 분석 실패: {self.project_name}")
                return False
            
            # 2. HTML 리포트 생성
            html_content = self._generate_layer_diagram_html(analysis_data)
            
            # 3. 파일 저장 (USER RULES: 공통함수 사용)
            output_file = self._save_report(html_content)
            
            app_logger.info(f"새로운 아키텍처 레이어 다이어그램 리포트 생성 완료: {output_file}")
            return True
            
        except Exception as e:
            # USER RULES: handle_error()로 예외 처리 및 Exit
            handle_error(e, f"새로운 아키텍처 레이어 다이어그램 리포트 생성 실패: {self.project_name}")
            return False
    
    def _analyze_architecture_data(self) -> Optional[Dict[str, Any]]:
        """
        아키텍처 데이터 분석 - 실제 컴포넌트 리스트 포함
        
        Returns:
            분석된 아키텍처 데이터
        """
        try:
            analysis = {
                'layer_distribution': {},
                'component_counts': {},
                'relationships': {},
                'layer_relationships': {},
                'component_relationships': {},  # 컴포넌트별 관계 데이터
                'traditional_layer_relationships': {},  # 전통적 레이어 간 관계
                'layer_components': {}  # 실제 컴포넌트 리스트
            }
            
            # 1. Layer별 실제 컴포넌트 리스트 조회 (USER RULES: 동적 쿼리)
            components_query = """
                SELECT 
                    c.layer, 
                    c.component_type, 
                    c.component_name,
                    c.component_id,
                    f.file_name as file_path
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                WHERE c.del_yn = 'N' AND c.project_id = (
                    SELECT project_id FROM projects WHERE project_name = ?
                )
                ORDER BY c.layer, c.component_type, c.component_name
            """
            
            component_results = self.db_utils.execute_query(components_query, (self.project_name,))
            
            for row in component_results:
                layer = row['layer'] if row['layer'] else 'NULL'
                comp_type = row['component_type']
                comp_name = row['component_name']
                comp_id = row['component_id']
                file_path = row['file_path'] if row['file_path'] else ''
                
                if layer not in analysis['layer_components']:
                    analysis['layer_components'][layer] = []
                
                analysis['layer_components'][layer].append({
                    'id': comp_id,
                    'name': comp_name,
                    'type': comp_type,
                    'file_path': file_path
                })
                
                # 기존 분포 분석도 유지
                if layer not in analysis['layer_distribution']:
                    analysis['layer_distribution'][layer] = {}
                if comp_type not in analysis['layer_distribution'][layer]:
                    analysis['layer_distribution'][layer][comp_type] = 0
                analysis['layer_distribution'][layer][comp_type] += 1
            
            # 2. 전체 컴포넌트 수 분석
            comp_query = """
                SELECT component_type, COUNT(*) as count 
                FROM components 
                WHERE del_yn = 'N' AND project_id = (
                    SELECT project_id FROM projects WHERE project_name = ?
                )
                GROUP BY component_type 
                ORDER BY count DESC
            """
            
            comp_results = self.db_utils.execute_query(comp_query, (self.project_name,))
            
            for row in comp_results:
                analysis['component_counts'][row['component_type']] = row['count']
            
            # 3. 관계 분석 (USER RULES: 설계문서 따라 올바른 쿼리 작성)
            rel_query = """
                SELECT r.rel_type, COUNT(*) as count 
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                WHERE r.del_yn = 'N' 
                  AND src.del_yn = 'N'
                  AND src.project_id = (
                      SELECT project_id FROM projects WHERE project_name = ?
                  )
                GROUP BY r.rel_type 
                ORDER BY count DESC
            """
            
            rel_results = self.db_utils.execute_query(rel_query, (self.project_name,))
            
            for row in rel_results:
                analysis['relationships'][row['rel_type']] = row['count']
            
            # 4. Layer간 관계 분석 (USER RULES: relationships 테이블에 project_id 없음, 수정된 쿼리)
            layer_rel_query = """
                SELECT 
                    src.layer as src_layer,
                    dst.layer as dst_layer,
                    r.rel_type,
                    COUNT(*) as count
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                JOIN components dst ON r.dst_id = dst.component_id
                WHERE r.del_yn = 'N' 
                  AND src.del_yn = 'N' 
                  AND dst.del_yn = 'N'
                  AND src.layer IS NOT NULL 
                  AND dst.layer IS NOT NULL
                  AND src.project_id = (
                      SELECT project_id FROM projects WHERE project_name = ?
                  )
                  AND dst.project_id = (
                      SELECT project_id FROM projects WHERE project_name = ?
                  )
                GROUP BY src.layer, dst.layer, r.rel_type
                ORDER BY count DESC
            """
            
            layer_rel_results = self.db_utils.execute_query(layer_rel_query, (self.project_name, self.project_name))
            
            for row in layer_rel_results:
                key = f"{row['src_layer']} -> {row['dst_layer']} ({row['rel_type']})"
                analysis['layer_relationships'][key] = row['count']
            
            # 5. 컴포넌트별 관계 데이터 조회 (인터랙티브 기능용)
            comp_rel_query = """
                SELECT 
                    src.component_name as src_comp,
                    src.layer as src_layer,
                    dst.component_name as dst_comp,
                    dst.layer as dst_layer,
                    r.rel_type
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                JOIN components dst ON r.dst_id = dst.component_id
                WHERE r.del_yn = 'N' 
                  AND src.del_yn = 'N' 
                  AND dst.del_yn = 'N'
                  AND src.layer IS NOT NULL 
                  AND dst.layer IS NOT NULL
                  AND src.component_type = 'METHOD'
                  AND dst.component_type = 'METHOD'
                  AND src.project_id = (
                      SELECT project_id FROM projects WHERE project_name = ?
                  )
                ORDER BY src.component_name
                LIMIT 1000
            """
            
            comp_rel_results = self.db_utils.execute_query(comp_rel_query, (self.project_name,))
            
            for row in comp_rel_results:
                src_comp = row['src_comp']
                if src_comp not in analysis['component_relationships']:
                    analysis['component_relationships'][src_comp] = {
                        'layer': row['src_layer'],
                        'relationships': []
                    }
                analysis['component_relationships'][src_comp]['relationships'].append({
                    'target': row['dst_comp'],
                    'target_layer': row['dst_layer'],
                    'type': row['rel_type']
                })
            
            # 6. 전통적 레이어 간 관계 매핑
            traditional_mapping = {
                'controller': ['CONTROLLER', 'API_ENTRY'],
                'service': ['SERVICE', 'APPLICATION'], 
                'mapper': ['REPOSITORY'],
                'model': ['MODEL', 'DATA']
            }
            
            for trad_src, meta_src_list in traditional_mapping.items():
                for trad_dst, meta_dst_list in traditional_mapping.items():
                    if trad_src != trad_dst:
                        src_placeholders = ','.join('?' * len(meta_src_list))
                        dst_placeholders = ','.join('?' * len(meta_dst_list))
                        
                        trad_rel_query = f"""
                            SELECT COUNT(*) as count
                            FROM relationships r
                            JOIN components src ON r.src_id = src.component_id
                            JOIN components dst ON r.dst_id = dst.component_id
                            WHERE r.del_yn = 'N' 
                              AND src.del_yn = 'N' 
                              AND dst.del_yn = 'N'
                              AND src.layer IN ({src_placeholders})
                              AND dst.layer IN ({dst_placeholders})
                              AND src.project_id = (
                                  SELECT project_id FROM projects WHERE project_name = ?
                              )
                        """
                        
                        params = meta_src_list + meta_dst_list + [self.project_name]
                        trad_rel_result = self.db_utils.execute_query(trad_rel_query, params)
                        
                        count = trad_rel_result[0]['count'] if trad_rel_result else 0
                        if count > 0:
                            key = f"{trad_src}->{trad_dst}"
                            analysis['traditional_layer_relationships'][key] = count
            
            app_logger.debug(f"아키텍처 데이터 분석 완료: Layer {len(analysis['layer_distribution'])}개, 관계 {len(analysis['relationships'])}개, 컴포넌트 관계 {len(analysis['component_relationships'])}개")
            return analysis
            
        except Exception as e:
            # USER RULES: exception 발생시 handle_error()로 로그남기고 Exit
            handle_error(e, f"아키텍처 데이터 분석 실패: {self.project_name}")
            return None
    
    def _generate_layer_diagram_html(self, analysis: Dict[str, Any]) -> str:
        """
        가로 방향 레이어 다이어그램 HTML 생성
        
        Args:
            analysis: 분석된 아키텍처 데이터
            
        Returns:
            생성된 HTML 콘텐츠
        """
        try:
            # HTML 템플릿 생성
            html_template = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>아키텍처 레이어 다이어그램 - {project_name}</title>
    <style>
        {css_styles}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>아키텍처 레이어 다이어그램</h1>
            <div class="subtitle">프로젝트: {project_name} | 생성일: {generation_time}<br>
            가로 방향 레이어 배치 및 컴포넌트 시각화</div>
        </div>
        
        <div class="architecture-container" id="architectureContainer">
            <svg class="relationship-arrows" id="relationshipArrows">
                <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                            refX="9" refY="3.5" orient="auto">
                        <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
                    </marker>
                </defs>
            </svg>
            {layer_columns}
        </div>
        
        <div class="statistics">
            <div class="stats-grid">
                {statistics}
            </div>
        </div>
        
        <div class="footer">
            아키텍처 분석 완료 - 컴포넌트를 클릭하여 관련 요소를 확인하세요
        </div>
    </div>
    
    <script>
        {javascript_code}
    </script>
</body>
</html>
            """
            
            # 각 섹션 생성
            css_styles = self._generate_css_styles()
            layer_columns = self._generate_layer_columns_html(analysis)
            statistics = self._generate_statistics_html(analysis)
            javascript_code = self._generate_javascript_code(analysis)
            
            # 최종 HTML 조합
            html_content = html_template.format(
                project_name=self.project_name,
                generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                css_styles=css_styles,
                layer_columns=layer_columns,
                statistics=statistics,
                javascript_code=javascript_code
            )
            
            return html_content
            
        except Exception as e:
            app_logger.error(f"레이어 다이어그램 HTML 생성 실패: {e}")
            raise
    
    def _generate_css_styles(self) -> str:
        """CSS 스타일 생성 - 다른 리포트와 동일한 헤더 스타일 적용"""
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
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 8px;
            text-align: center;
        }
        
        .header h1 {
            margin: 0;
            font-size: 1.5em;
            font-weight: 300;
        }
        
        .header .subtitle {
            margin: 3px 0 0 0;
            opacity: 0.8;
            font-size: 0.9em;
        }
        
        .architecture-container {
            display: flex;
            flex-direction: row;
            gap: 10px;
            overflow-x: auto;
            padding: 10px;
            background: white;
            height: calc(100vh - 120px);
            position: relative;
            justify-content: flex-start;
            align-items: flex-start;
        }
        
        .layer-column {
            flex: 1;
            min-width: 150px;
            max-width: none;
            background: #fafafa;
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 12px;
            position: relative;
            height: calc(100vh - 160px);
            overflow-y: auto;
            margin-bottom: 10px;
        }
        
        .layer-header {
            text-align: center;
            font-weight: bold;
            font-size: 13px;
            padding: 8px;
            border-radius: 5px;
            margin-bottom: 10px;
            color: #333;
        }
        
        .component-item {
            background: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 6px 8px;
            margin-bottom: 3px;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .component-item:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            border-color: #007bff;
            z-index: 5;
        }
        
        .component-item.selected {
            background: #007bff;
            color: white;
            border-color: #0056b3;
            box-shadow: 0 3px 8px rgba(0,123,255,0.3);
        }
        
        .component-item.dimmed {
            opacity: 0.3;
            background: #f8f9fa;
            border-color: #e9ecef;
        }
        
        .component-count {
            background: #666;
            color: white;
            border-radius: 10px;
            padding: 1px 6px;
            font-size: 9px;
            margin-left: 4px;
            float: right;
        }
        
        .relationship-arrows {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 10;
        }
        
        .arrow {
            stroke: #666;
            stroke-width: 2;
            fill: none;
            marker-end: url(#arrowhead);
        }
        
        .arrow.highlighted {
            stroke: #007bff;
            stroke-width: 3;
        }
        
        .statistics {
            padding: 6px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
            position: fixed;
            bottom: 20px;
            left: 0;
            right: 0;
            z-index: 1000;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 8px;
        }
        
        .stat-item {
            background: white;
            padding: 8px;
            border-radius: 4px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .stat-number {
            font-size: 16px;
            font-weight: bold;
            color: #007bff;
        }
        
        .stat-label {
            font-size: 10px;
            color: #666;
            margin-top: 2px;
        }
        
        .footer {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 2px;
            text-align: center;
            font-size: 9px;
            opacity: 0.8;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 1001;
        }
        
        /* 반응형 디자인 */
        @media (max-width: 1200px) {
            .layer-column {
                min-width: 140px;
                padding: 8px;
            }
            .component-item {
                font-size: 10px;
                padding: 4px 6px;
            }
        }
        
        @media (max-width: 768px) {
            .architecture-container {
                gap: 5px;
                padding: 5px;
            }
            .layer-column {
                min-width: 120px;
                padding: 6px;
            }
            .layer-header {
                font-size: 11px;
                padding: 6px;
            }
            .component-item {
                font-size: 9px;
                padding: 3px 5px;
                margin-bottom: 2px;
            }
        }
        """
    
    def _generate_layer_columns_html(self, analysis: Dict[str, Any]) -> str:
        """레이어 컬럼 HTML 생성 - 실제 컴포넌트 개별 표시"""
        columns_html = []
        
        # USER RULES: 동적 레이어 순서 처리
        for layer in self.layer_order:
            if layer in analysis['layer_components']:
                layer_components = analysis['layer_components'][layer]
                total_components = len(layer_components)
                
                # 레이어 헤더 색상
                header_color = self.layer_colors.get(layer, '#e0e0e0')
                
                # 레이어 헤더 HTML
                header_html = f'''
                <div class="layer-header" style="background-color: {header_color};">
                    {layer} Layer<br>
                    <small>({total_components:,}개 컴포넌트)</small>
                </div>
                '''
                
                # 실제 컴포넌트 항목들 HTML
                components_html = []
                for idx, component in enumerate(layer_components):
                    comp_id = component['id']
                    comp_name = component['name']
                    comp_type = component['type']
                    file_path = component['file_path']
                    
                    # 잘못된 컴포넌트 이름 필터링 (숫자만 있거나 빈 이름)
                    if not comp_name or comp_name.strip() == '' or comp_name.isdigit():
                        continue
                    
                    # 컴포넌트 이름 축약 (너무 길면)
                    display_name = comp_name
                    if len(display_name) > 20:
                        display_name = display_name[:17] + "..."
                    
                    components_html.append(f'''
                    <div class="component-item" 
                         data-component-id="{comp_id}" 
                         data-layer="{layer}" 
                         data-type="{comp_type}"
                         data-name="{comp_name}"
                         data-file-path="{file_path}"
                         title="{comp_name} ({comp_type}) - {file_path}">
                        {display_name}
                        <span class="component-count">{comp_type[:3]}</span>
                    </div>
                    ''')
                
                # 전체 컬럼 HTML
                column_html = f'''
                <div class="layer-column" style="border-color: {header_color};" data-layer="{layer}">
                    {header_html}
                    {"".join(components_html)}
                </div>
                '''
                
                columns_html.append(column_html)
        
        return "".join(columns_html)
    
    def _generate_statistics_html(self, analysis: Dict[str, Any]) -> str:
        """통계 HTML 생성"""
        total_components = sum(analysis['component_counts'].values())
        total_relationships = sum(analysis['relationships'].values())
        total_layers = len([layer for layer in analysis['layer_distribution'] if layer != 'NULL'])
        total_layer_relationships = len(analysis['layer_relationships'])
        
        stats = [
            ('총 컴포넌트', total_components),
            ('총 관계', total_relationships),
            ('활성 레이어', total_layers),
            ('레이어간 관계', total_layer_relationships)
        ]
        
        stats_html = []
        for label, value in stats:
            stats_html.append(f'''
            <div class="stat-item">
                <div class="stat-number">{value:,}</div>
                <div class="stat-label">{label}</div>
            </div>
            ''')
        
        return "".join(stats_html)
    
    def _generate_javascript_code(self, analysis: Dict[str, Any] = None) -> str:
        """JavaScript 코드 생성 - 향상된 인터랙션 기능"""
        
        import json
        # 관계 데이터를 JavaScript에서 사용할 수 있도록 JSON으로 변환
        if analysis:
            component_relationships_json = json.dumps(analysis.get('component_relationships', {}), ensure_ascii=False)
            traditional_relationships_json = json.dumps(analysis.get('traditional_layer_relationships', {}), ensure_ascii=False)
        else:
            component_relationships_json = "{}"
            traditional_relationships_json = "{}"
        
        return f"""
        let selectedComponent = null;
        let relationshipData = {component_relationships_json};
        let layerRelationships = {traditional_relationships_json};
        
        console.log('관계 데이터 로드됨:', Object.keys(relationshipData).length + '개 컴포넌트');
        console.log('레이어 관계:', layerRelationships);
        
        // 간단한 클릭 이벤트
        document.addEventListener('DOMContentLoaded', function() {{
            document.querySelectorAll('.component-item').forEach(function(item) {{
                item.addEventListener('click', function() {{
                    // 기존 선택 해제
                    document.querySelectorAll('.component-item').forEach(function(el) {{
                        el.style.opacity = '';
                        el.style.borderColor = '';
                        el.classList.remove('selected');
                    }});
                    
                    // 현재 컴포넌트 선택
                    this.classList.add('selected');
                    this.style.borderColor = '#007bff';
                    
                    const name = this.dataset.name;
                    console.log('선택된 컴포넌트:', name);
                    
                    // 관련 컴포넌트 하이라이트
                    if (relationshipData[name]) {{
                        relationshipData[name].relationships.forEach(function(rel) {{
                            const targets = document.querySelectorAll('[data-name="' + rel.target + '"]');
                            targets.forEach(function(target) {{
                                target.style.borderColor = '#28a745';
                                target.style.borderWidth = '2px';
                            }});
                        }});
                    }}
                    
                    // 나머지 흐리게
                    document.querySelectorAll('.component-item:not(.selected)').forEach(function(el) {{
                        if (el.style.borderColor !== 'rgb(40, 167, 69)') {{
                            el.style.opacity = '0.4';
                        }}
                    }});
                }});
            }});
        }});"""
    
    def _save_report(self, html_content: str) -> str:
        """
        리포트 파일 저장 (USER RULES: 기존 구조와 동일한 공통함수 사용)
        
        Args:
            html_content: HTML 콘텐츠
            
        Returns:
            저장된 파일 경로
        """
        try:
            # USER RULES: 기존 리포트 생성기와 동일한 방식으로 저장
            output_file = self.report_utils.save_report(html_content, "ArchitectureLayerDiagram")
            return output_file
            
        except Exception as e:
            app_logger.error(f"리포트 파일 저장 실패: {e}")
            raise
