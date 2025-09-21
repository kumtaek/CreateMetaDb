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
        """6개 핵심 Layer 순서 정의 (USER RULES: 동적 구성)"""
        return [
            'FRONTEND', 'CONTROLLER', 'SERVICE', 'MODEL', 'TABLE'
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
                    f.file_name as file_path,
                    (SELECT COUNT(*) FROM relationships r 
                     WHERE (r.src_id = c.component_id OR r.dst_id = c.component_id) 
                     AND r.del_yn = 'N') as relationship_count
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                WHERE c.del_yn = 'N' 
                  AND c.project_id = (SELECT project_id FROM projects WHERE project_name = ?)
                  AND c.component_type IN ('METHOD', 'TABLE', 'CLASS', 'API_URL', 'JSP', 'JS', 'HTML', 'CSS')
                  AND c.component_name IS NOT NULL
                  AND c.component_name != ''
                  AND NOT (c.component_name GLOB '[0-9]*' AND LENGTH(c.component_name) <= 3)
                  AND c.component_name GLOB '[a-zA-Z]*'
                ORDER BY c.layer, relationship_count DESC, c.component_name
            """
            
            component_results = self.db_utils.execute_query(components_query, (self.project_name,))
            
            # 중복 제거를 위한 컴포넌트 세트 (컴포넌트명 기준 완전 중복 제거)
            component_sets = {}
            
            for row in component_results:
                layer = row['layer'] if row['layer'] else 'NULL'
                comp_type = row['component_type']
                comp_name = row['component_name']
                comp_id = row['component_id']
                file_path = row['file_path'] if row['file_path'] else ''
                
                # 아키텍처 다이어그램용 완전 중복 제거: 컴포넌트명 + 타입 기준
                unique_key = f"{comp_name}::{comp_type}"
                
                if layer not in component_sets:
                    component_sets[layer] = {}
                
                # 중복 제거: 동일한 컴포넌트명+타입은 하나만 유지 (관계수가 많은 것 우선)
                if unique_key not in component_sets[layer]:
                    file_name = file_path.split('/')[-1] if file_path else 'unknown'
                    component_sets[layer][unique_key] = {
                        'id': comp_id,
                        'name': comp_name,
                        'type': comp_type,
                        'file_path': file_path,
                        'file_name': file_name,
                        'display_name': f"{comp_name} ({file_name})" if file_name != 'unknown' else comp_name,
                        'relationship_count': row.get('relationship_count', 0)
                    }
                else:
                    # 기존 것보다 관계수가 많으면 교체
                    existing = component_sets[layer][unique_key]
                    current_rel_count = row.get('relationship_count', 0)
                    if current_rel_count > existing['relationship_count']:
                        file_name = file_path.split('/')[-1] if file_path else 'unknown'
                        component_sets[layer][unique_key] = {
                            'id': comp_id,
                            'name': comp_name,
                            'type': comp_type,
                            'file_path': file_path,
                            'file_name': file_name,
                            'display_name': f"{comp_name} ({file_name})" if file_name != 'unknown' else comp_name,
                            'relationship_count': current_rel_count
                        }
            
            # 5개 핵심 레이어만 필터링 (REPOSITORY 제거, MODEL만 표시)
            target_layers = ['FRONTEND', 'CONTROLLER', 'SERVICE', 'MODEL', 'TABLE']
            
            # 레이어 매핑 로직 
            def map_to_target_layer(layer, comp_type, file_path):
                if comp_type in ['JSP', 'JS', 'HTML', 'CSS']:
                    return 'FRONTEND'
                elif comp_type == 'API_URL' or 'controller' in file_path.lower():
                    return 'CONTROLLER'
                elif 'service' in file_path.lower():
                    return 'SERVICE'
                elif layer == 'MODEL':  # 기존 REPOSITORY가 MODEL로 변경됨
                    return 'MODEL'
                elif comp_type == 'TABLE':
                    return 'TABLE'
                else:
                    return None
            
            # 컴포넌트를 타겟 레이어로 재분류
            target_component_sets = {}
            for layer, comp_set in component_sets.items():
                for unique_key, component in comp_set.items():
                    target_layer = map_to_target_layer(layer, component['type'], component['file_path'])
                    
                    if target_layer and target_layer in target_layers:
                        if target_layer not in target_component_sets:
                            target_component_sets[target_layer] = {}
                        target_component_sets[target_layer][unique_key] = component
            
            # 세트를 리스트로 변환 (전체 표시)
            for target_layer in target_layers:
                if target_layer not in analysis['layer_components']:
                    analysis['layer_components'][target_layer] = []
                
                if target_layer in target_component_sets:
                    comp_set = target_component_sets[target_layer]
                    # ABC 정렬 (컴포넌트명 기준)
                    sorted_components = sorted(comp_set.values(), key=lambda x: x['name'].lower())
                    
                    # 전체 컴포넌트 표시 (제한 없음)
                    analysis['layer_components'][target_layer].extend(sorted_components)
                
                    # 중복 제거된 컴포넌트 기반으로 분포 분석 (기존 분포 분석 대신)
                    if target_layer not in analysis['layer_distribution']:
                        analysis['layer_distribution'][target_layer] = {}
                    
                    for comp in sorted_components:
                        comp_type = comp['type']
                        if comp_type not in analysis['layer_distribution'][target_layer]:
                            analysis['layer_distribution'][target_layer][comp_type] = 0
                        analysis['layer_distribution'][target_layer][comp_type] += 1
            
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
            
            # 5. 전체 호출 체인 관계 데이터 조회 (CallChain 스타일)
            comp_rel_query = """
                -- Frontend → API → METHOD 관계
                SELECT 
                    frontend_file.file_name as src_comp,
                    'FRONTEND' as src_layer,
                    api_url.component_name as dst_comp,
                    'API_ENTRY' as dst_layer,
                    'CALL_API' as rel_type
                FROM components api_url
                JOIN files frontend_file ON api_url.file_id = frontend_file.file_id
                JOIN projects p ON api_url.project_id = p.project_id
                WHERE p.project_name = ?
                  AND api_url.component_type = 'API_URL'
                  AND frontend_file.file_type IN ('JSP', 'JSX', 'HTML')
                  AND api_url.del_yn = 'N'
                  AND frontend_file.del_yn = 'N'
                
                UNION ALL
                
                -- API → METHOD 관계
                SELECT 
                    api_url.component_name as src_comp,
                    'API_ENTRY' as src_layer,
                    method.component_name as dst_comp,
                    method.layer as dst_layer,
                    'CALL_METHOD' as rel_type
                FROM components api_url
                JOIN relationships r1 ON api_url.component_id = r1.src_id AND r1.rel_type = 'CALL_METHOD'
                JOIN components method ON r1.dst_id = method.component_id
                JOIN projects p ON api_url.project_id = p.project_id
                WHERE p.project_name = ?
                  AND api_url.component_type = 'API_URL'
                  AND method.component_type = 'METHOD'
                  AND r1.del_yn = 'N'
                  AND api_url.del_yn = 'N'
                  AND method.del_yn = 'N'
                
                UNION ALL
                
                -- METHOD → QUERY 관계
                SELECT 
                    method.component_name as src_comp,
                    method.layer as src_layer,
                    query.component_name as dst_comp,
                    'QUERY' as dst_layer,
                    'CALL_QUERY' as rel_type
                FROM components method
                JOIN relationships r2 ON method.component_id = r2.src_id AND r2.rel_type = 'CALL_QUERY'
                JOIN components query ON r2.dst_id = query.component_id
                JOIN projects p ON method.project_id = p.project_id
                WHERE p.project_name = ?
                  AND method.component_type = 'METHOD'
                  AND query.component_type LIKE 'SQL_%'
                  AND r2.del_yn = 'N'
                  AND method.del_yn = 'N'
                  AND query.del_yn = 'N'
                
                UNION ALL
                
                -- QUERY → TABLE 관계
                SELECT 
                    query.component_name as src_comp,
                    'QUERY' as src_layer,
                    table_comp.component_name as dst_comp,
                    'TABLE' as dst_layer,
                    'USE_TABLE' as rel_type
                FROM components query
                JOIN relationships r3 ON query.component_id = r3.src_id AND r3.rel_type = 'USE_TABLE'
                JOIN components table_comp ON r3.dst_id = table_comp.component_id
                JOIN projects p ON query.project_id = p.project_id
                WHERE p.project_name = ?
                  AND query.component_type LIKE 'SQL_%'
                  AND table_comp.component_type = 'TABLE'
                  AND r3.del_yn = 'N'
                  AND query.del_yn = 'N'
                  AND table_comp.del_yn = 'N'
                
                ORDER BY src_comp, dst_comp
                LIMIT 5000
            """
            
            comp_rel_results = self.db_utils.execute_query(comp_rel_query, (self.project_name, self.project_name, self.project_name, self.project_name))
            
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
                
                # 디버그: 관계 데이터 확인
                app_logger.debug(f"관계 추가: {src_comp} ({row['src_layer']}) -> {row['dst_comp']} ({row['dst_layer']})")
            
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
    <link rel="stylesheet" href="css/woori.css">
    <style>
        {css_styles}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>아키텍처 레이어 다이어그램</h1>
            <div class="subtitle">프로젝트: {project_name} | 생성일: {generation_time}</div>
        </div>
        
        <div class="content">
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
        </div>
        
        <div class="stats">
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
        """CSS 스타일 생성 - CallChain Report와 동일한 컴팩트 스타일 적용"""
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
        }
        .header {
            background: linear-gradient(90deg, #0d47a1 0%, #1976d2 100%);
            color: white;
            padding: 8px;
            text-align: center;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(25, 118, 210, 0.12);
            margin-bottom: 3px;
            padding-bottom: 3px;
        }
        .header h1 {
            margin: 0;
            font-size: 1.4em;
            font-weight: 300;
        }
        .header .subtitle {
            margin: 2px 0 0 0;
            opacity: 0.9;
            font-size: 0.8em;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 6px;
            padding: 6px;
            background: #f8f9fa;
            margin: 10px 0;
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
        .architecture-container {
            display: flex;
            flex-direction: row;
            width: 100%;
            padding: 10px;
            background: white;
            min-height: 400px;
            position: relative;
            box-sizing: border-box;
        }
        
        .layer-column {
            flex: 1;
            min-width: 0;
            background: #fafafa;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 6px;
            position: relative;
            height: 100%;
            overflow-y: auto;
            margin: 0 2px;
            display: flex;
            flex-direction: column;
        }
        
        .layer-header {
            text-align: center;
            font-weight: bold;
            font-size: 0.7em;
            padding: 3px;
            border-radius: 2px;
            margin-bottom: 4px;
            color: #333;
            flex-shrink: 0;
        }
        
        .layer-content {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }
        
        .component-item {
            background: white;
            border: 1px solid #ccc;
            border-radius: 2px;
            padding: 2px 4px;
            margin-bottom: 1px;
            font-size: 0.6em;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            order: 1;
        }
        
        .component-item:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            border-color: #007bff;
            z-index: 5;
        }
        
        .component-item.selected {
            background: #007bff !important;
            color: white !important;
            border-color: #0056b3 !important;
            border-width: 3px !important;
            box-shadow: 0 4px 12px rgba(0,123,255,0.4) !important;
            transform: translateY(-2px) scale(1.02) !important;
            z-index: 1000 !important;
            position: relative !important;
            order: 0 !important;
        }
        
        .component-item.related {
            background: #28a745 !important;
            color: white !important;
            border-color: #1e7e34 !important;
            border-width: 2px !important;
            box-shadow: 0 2px 8px rgba(40,167,69,0.3) !important;
            transform: translateY(-1px) !important;
            z-index: 500 !important;
            position: relative !important;
        }
        
        .component-item.dimmed {
            opacity: 0.3;
            background: #f8f9fa;
            border-color: #e9ecef;
        }
        
        .component-count {
            background: #666;
            color: white;
            border-radius: 8px;
            padding: 1px 4px;
            font-size: 0.5em;
            margin-left: 2px;
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
        
        .footer {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 8px;
            text-align: center;
            font-size: 12px;
            opacity: 0.8;
            margin-top: 10px;
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
                displayed_count = len(layer_components)  # 실제 표시되는 개수 (최대 100개)
                
                # 전체 건수 조회 (필터링 전)
                total_count = self._get_total_component_count_by_layer(layer)
                
                # 레이어 헤더 색상
                header_color = self.layer_colors.get(layer, '#e0e0e0')
                
                # 레이어 헤더 HTML
                header_html = f'''
                <div class="layer-header" style="background-color: {header_color};">
                    {layer} Layer<br>
                    <small>({total_count:,}개 컴포넌트)</small>
                </div>
                '''
                
                # 실제 컴포넌트 항목들 HTML (전체 표시)
                components_html = []
                
                for idx, component in enumerate(layer_components):
                    comp_id = component['id']
                    comp_name = component['name']
                    comp_type = component['type']
                    file_path = component['file_path']
                    
                    # 잘못된 컴포넌트 이름 필터링 (동적 검증)
                    if not self._is_valid_component_name(comp_name, comp_type):
                        continue
                    
                    # 컴포넌트명만 표시 (괄호 제거)
                    display_name = comp_name
                    if len(display_name) > 25:
                        display_name = display_name[:22] + "..."
                    
                    components_html.append(f'''
                    <div class="component-item" 
                         data-component-id="{comp_id}" 
                         data-layer="{layer}" 
                         data-type="{comp_type}"
                         data-name="{comp_name}"
                         data-file-path="{file_path}"
                         title="{comp_name} ({comp_type}) - {file_path}">
                        {display_name}
                    </div>
                    ''')
                
                # 전체 컬럼 HTML
                column_html = f'''
                <div class="layer-column" style="border-color: {header_color};" data-layer="{layer}">
                    {header_html}
                    <div class="layer-content" id="layer-content-{layer}">
                        {"".join(components_html)}
                    </div>
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
        let lastSelectedComponent = null;
        let relationshipData = {component_relationships_json};
        let layerRelationships = {traditional_relationships_json};
        
        console.log('관계 데이터 로드됨:', Object.keys(relationshipData).length + '개 컴포넌트');
        console.log('관계 데이터 상세:', relationshipData);
        console.log('레이어 관계:', layerRelationships);
        
        // 간단한 클릭 이벤트
        document.addEventListener('DOMContentLoaded', function() {{
            document.querySelectorAll('.component-item').forEach(function(item) {{
                item.addEventListener('click', function() {{
                    const name = this.dataset.name;
                    
                    // 동일한 컴포넌트 두 번째 클릭 시 토글 (전체 활성화)
                    if (lastSelectedComponent === name) {{
                        console.log('동일 컴포넌트 두 번째 클릭 - 전체 활성화:', name);
                        // 모든 상태 초기화 (전체 활성화)
                        document.querySelectorAll('.component-item').forEach(function(el) {{
                            el.style.opacity = '';
                            el.style.borderColor = '';
                            el.style.borderWidth = '';
                            el.style.zIndex = '';
                            el.style.position = '';
                            el.style.order = '';
                            el.classList.remove('selected', 'related', 'dimmed');
                        }});
                        lastSelectedComponent = null;
                        selectedComponent = null;
                        return;
                    }}
                    
                    // 기존 선택 해제 (모든 상태 초기화)
                    document.querySelectorAll('.component-item').forEach(function(el) {{
                        el.style.opacity = '';
                        el.style.borderColor = '';
                        el.style.borderWidth = '';
                        el.style.zIndex = '';
                        el.style.position = '';
                        el.style.order = '';
                        el.classList.remove('selected', 'related', 'dimmed');
                    }});
                    
                    // 현재 컴포넌트 선택 (해당 레이어 맨 위로 이동)
                    this.classList.add('selected');
                    this.style.borderColor = '#007bff';
                    this.style.zIndex = '1000';
                    this.style.position = 'relative';
                    
                    // 해당 레이어에서 맨 위로 이동
                    const currentLayer = this.dataset.layer;
                    const layerContent = document.getElementById('layer-content-' + currentLayer);
                    if (layerContent && this.parentNode === layerContent) {{
                        layerContent.insertBefore(this, layerContent.firstChild);
                    }}
                    
                    const layer = this.dataset.layer;
                    const type = this.dataset.type;
                    console.log('선택된 컴포넌트:', name, '레이어:', layer, '타입:', type);
                    console.log('해당 컴포넌트 관계 데이터:', relationshipData[name]);
                    
                    // 선택된 컴포넌트 기록
                    lastSelectedComponent = name;
                    selectedComponent = name;
                    
                    // 전체 호출 체인 추적 (CallChain 스타일)
                    const relatedComponents = new Set();
                    const visited = new Set();
                    
                    // 재귀적으로 연결고리 추적
                    function traceRelationships(compName, depth = 0, maxDepth = 5) {{
                        if (depth > maxDepth || visited.has(compName)) return;
                        visited.add(compName);
                        
                        // 직접 관계 추가
                        if (relationshipData[compName]) {{
                            relationshipData[compName].relationships.forEach(function(rel) {{
                                relatedComponents.add(rel.target);
                                console.log(`${{depth}}단계 관계:`, compName, '->', rel.target, `(${{rel.target_layer}})`);
                                // 재귀적으로 다음 단계 추적
                                traceRelationships(rel.target, depth + 1, maxDepth);
                            }});
                        }}
                        
                        // 역방향 관계 추가
                        Object.keys(relationshipData).forEach(function(srcName) {{
                            relationshipData[srcName].relationships.forEach(function(rel) {{
                                if (rel.target === compName) {{
                                    relatedComponents.add(srcName);
                                    console.log(`${{depth}}단계 역방향:`, srcName, '->', compName);
                                    // 재귀적으로 이전 단계 추적
                                    traceRelationships(srcName, depth + 1, maxDepth);
                                }}
                            }});
                        }});
                    }}
                    
                    // 선택된 컴포넌트부터 체인 추적 시작
                    traceRelationships(name, 0, 5);
                    
                    // 관련 컴포넌트들 하이라이트 (모든 레이어에서)
                    relatedComponents.forEach(function(targetName) {{
                        const targets = document.querySelectorAll('[data-name="' + targetName + '"]');
                        targets.forEach(function(target) {{
                            target.style.borderColor = '#28a745';
                            target.style.borderWidth = '2px';
                            target.style.opacity = '1';
                            target.style.zIndex = '500';
                            target.style.position = 'relative';
                            target.classList.add('related');
                        }});
                    }});
                    
                    console.log('총 관련 컴포넌트:', relatedComponents.size, '개');
                    
                    // 관련 없는 컴포넌트만 흐리게
                    document.querySelectorAll('.component-item:not(.selected):not(.related)').forEach(function(el) {{
                        el.style.opacity = '0.3';
                        el.classList.add('dimmed');
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
    
    def _is_valid_component_name(self, comp_name: str, comp_type: str) -> bool:
        """
        컴포넌트명 유효성 검증 (동적 검증)
        
        Args:
            comp_name: 컴포넌트명
            comp_type: 컴포넌트 타입
            
        Returns:
            유효성 여부 (True/False)
        """
        try:
            # 1. 기본 검증: 빈 값이나 공백만 있는 경우
            if not comp_name or not comp_name.strip():
                return False
            
            # 2. 숫자만으로 구성된 경우 (Java 파서 오류)
            if comp_name.isdigit():
                return False
            
            # 3. 길이가 너무 짧은 경우 (1글자 이하)
            if len(comp_name.strip()) <= 1:
                return False
            
            # 4. 타입별 추가 검증
            if comp_type == 'METHOD':
                # Java 메서드명 규칙: 영문자로 시작, 영문자/숫자/언더스코어 조합
                import re
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', comp_name):
                    return False
            
            elif comp_type == 'CLASS':
                # Java 클래스명 규칙: 대문자로 시작, 영문자/숫자 조합
                import re
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', comp_name):
                    return False
            
            # 5. 특수문자만으로 구성된 경우
            import re
            if re.match(r'^[^a-zA-Z0-9_]+$', comp_name):
                return False
            
            return True
            
        except Exception as e:
            # 검증 실패 시 안전하게 False 반환
            from util.logger import debug
            debug(f"컴포넌트명 검증 실패: {comp_name} - {e}")
            return False
    
    def _get_total_component_count_by_layer(self, layer: str) -> int:
        """
        레이어별 전체 컴포넌트 개수 조회 (필터링 전)
        
        Args:
            layer: 레이어명
            
        Returns:
            전체 컴포넌트 개수
        """
        try:
            query = """
                SELECT COUNT(*) as total_count
                FROM components c
                JOIN files f ON c.file_id = f.file_id
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? 
                AND c.layer = ?
                AND c.component_type IN ('METHOD', 'TABLE', 'CLASS', 'API_URL', 'JSP', 'JS', 'HTML', 'CSS')
                AND c.del_yn = 'N' 
                AND f.del_yn = 'N'
                AND c.component_name IS NOT NULL
                AND c.component_name != ''
                AND NOT (c.component_name GLOB '[0-9]*' AND LENGTH(c.component_name) <= 3)
                AND c.component_name GLOB '[a-zA-Z]*'
            """
            
            result = self.db_utils.execute_query(query, (self.project_name, layer))
            return result[0]['total_count'] if result else 0
            
        except Exception as e:
            from util.logger import debug
            debug(f"레이어별 전체 개수 조회 실패: {layer} - {e}")
            return 0


if __name__ == '__main__':
    import sys
    from util.arg_utils import ArgUtils
    
    # 명령행 인자 파싱
    arg_utils = ArgUtils()
    parser = arg_utils.create_parser("아키텍처 레이어 다이어그램 리포트 생성기")
    args = parser.parse_args()
    
    project_name = args.project_name
    
    print(f"아키텍처 레이어 다이어그램 리포트 생성 시작: {project_name}")
    
    generator = ArchitectureLayerReportGenerator(project_name, './temp')
    result = generator.generate_report()
    
    if result:
        print(f"아키텍처 레이어 다이어그램 리포트 생성 완료: {project_name}")
    else:
        print(f"아키텍처 레이어 다이어그램 리포트 생성 실패: {project_name}")
        sys.exit(1)
