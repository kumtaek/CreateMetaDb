"""
ERD(Dagre) Report 생성기
- Cytoscape.js와 Dagre 레이아웃을 사용한 고도화 ERD 생성
- 테이블과 컬럼 정보를 활용한 인터랙티브 ERD 생성
- 오프라인 환경 지원 (로컬 라이브러리 사용)
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# 크로스플랫폼 경로 처리
if sys.platform.startswith('win'):
    import ntpath
    path_module = ntpath
else:
    import posixpath
    path_module = posixpath

from util.logger import app_logger, handle_error
from util.path_utils import PathUtils
from util.database_utils import DatabaseUtils
from reports.erd_dagre_templates import ERDDagreTemplates


class ERDDagreReportGenerator:
    """ERD(Dagre) Report 생성기 클래스"""
    
    def __init__(self, project_name: str, output_dir: str):
        """
        초기화
        
        Args:
            project_name: 프로젝트명
            output_dir: 출력 디렉토리
        """
        self.project_name = project_name
        self.output_dir = output_dir
        self.path_utils = PathUtils()
        self.templates = ERDDagreTemplates()
        
        # 메타데이터베이스 연결
        self.metadata_db_path = self.path_utils.get_project_metadata_db_path(project_name)
        self.db_utils = DatabaseUtils(self.metadata_db_path)
        
        if not self.db_utils.connect():
            handle_error(Exception("데이터베이스 연결 실패"), f"메타데이터베이스 연결 실패: {self.metadata_db_path}")
    
    def generate_report(self) -> bool:
        """
        ERD(Dagre) Report 생성
        
        Returns:
            생성 성공 여부 (True/False)
        """
        try:
            app_logger.info(f"ERD(Dagre) Report 생성 시작: {self.project_name}")
            
            # 1. 통계 정보 조회
            stats = self._get_statistics()
            
            # 2. ERD 데이터 조회 (Cytoscape.js 형식)
            erd_data = self._get_cytoscape_data()
            
            # 3. HTML 생성
            html_content = self._generate_html(stats, erd_data)
            
            # 4. 파일 저장
            output_file = self._save_report(html_content)
            
            app_logger.info(f"ERD(Dagre) Report 생성 완료: {output_file}")
            return True
            
        except Exception as e:
            handle_error(e, "ERD(Dagre) Report 생성 실패")
            return False
        finally:
            self.db_utils.disconnect()
    
    def _get_statistics(self) -> Dict[str, int]:
        """통계 정보 조회"""
        try:
            stats = {}
            
            # 전체 테이블 수
            query = """
                SELECT COUNT(*) as count
                FROM (
                    SELECT DISTINCT t.table_name
                    FROM tables t
                    JOIN projects p ON t.project_id = p.project_id
                    WHERE p.project_name = ? AND t.del_yn = 'N'
                )
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['total_tables'] = result[0]['count'] if result else 0
            
            # 전체 컬럼 수
            query = """
                SELECT COUNT(*) as count
                FROM columns c
                JOIN tables t ON c.table_id = t.table_id
                JOIN projects p ON t.project_id = p.project_id
                WHERE p.project_name = ? AND c.del_yn = 'N' AND t.del_yn = 'N'
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['total_columns'] = result[0]['count'] if result else 0
            
            # Primary Key 수
            query = """
                SELECT COUNT(*) as count
                FROM columns c
                JOIN tables t ON c.table_id = t.table_id
                JOIN projects p ON t.project_id = p.project_id
                WHERE p.project_name = ? AND c.position_pk > 0 AND c.del_yn = 'N' AND t.del_yn = 'N'
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['primary_keys'] = result[0]['count'] if result else 0
            
            # Foreign Key 수
            query = """
                SELECT COUNT(*) as count
                FROM relationships r
                JOIN components src_comp ON r.src_id = src_comp.component_id
                JOIN projects p ON src_comp.project_id = p.project_id
                WHERE p.project_name = ? AND r.rel_type = 'FK' AND r.del_yn = 'N'
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['foreign_keys'] = result[0]['count'] if result else 0
            
            # 전체 관계 수
            query = """
                SELECT COUNT(*) as count
                FROM relationships r
                JOIN components src_comp ON r.src_id = src_comp.component_id
                JOIN projects p ON src_comp.project_id = p.project_id
                WHERE p.project_name = ? AND r.del_yn = 'N'
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['relationships'] = result[0]['count'] if result else 0
            
            app_logger.debug(f"ERD(Dagre) 통계 정보 조회 완료: {stats}")
            return stats
            
        except Exception as e:
            handle_error(e, "ERD(Dagre) 통계 정보 조회 실패")
            return {}
    
    def _get_cytoscape_data(self) -> Dict[str, Any]:
        """Cytoscape.js 형식의 ERD 데이터 조회"""
        try:
            # 테이블과 컬럼 정보 조회
            tables_data = self._get_tables_with_columns()
            
            # 관계 정보 조회
            relationships_data = self._get_relationships_detailed()
            
            # Cytoscape.js 노드 데이터 생성
            nodes = self._generate_cytoscape_nodes(tables_data)
            
            # Cytoscape.js 엣지 데이터 생성
            edges = self._generate_cytoscape_edges(relationships_data)
            
            cytoscape_data = {
                'nodes': nodes,
                'edges': edges,
                'tables_count': len(tables_data),
                'relationships_count': len(relationships_data)
            }
            
            app_logger.debug(f"Cytoscape 데이터 생성 완료: {len(nodes)}개 노드, {len(edges)}개 엣지")
            return cytoscape_data
            
        except Exception as e:
            handle_error(e, "Cytoscape 데이터 생성 실패")
            return {'nodes': [], 'edges': [], 'tables_count': 0, 'relationships_count': 0}
    
    def _get_tables_with_columns(self) -> Dict[str, List[Dict[str, Any]]]:
        """테이블과 컬럼 정보 조회"""
        try:
            query = """
                SELECT 
                    t.table_name,
                    t.table_owner,
                    t.table_comments,
                    c.column_name,
                    c.data_type,
                    c.position_pk,
                    c.nullable,
                    c.column_comments,
                    c.column_id,
                    c.data_length,
                    c.data_default
                FROM tables t
                JOIN columns c ON t.table_id = c.table_id
                JOIN projects p ON t.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND t.del_yn = 'N' 
                  AND c.del_yn = 'N'
                ORDER BY t.table_name, c.column_id
            """
            
            results = self.db_utils.execute_query(query, (self.project_name,))
            
            # 테이블별로 데이터 그룹화
            tables_data = {}
            for row in results:
                table_name = row['table_name']
                if table_name not in tables_data:
                    tables_data[table_name] = {
                        'table_owner': row['table_owner'],
                        'table_comments': row['table_comments'],
                        'columns': []
                    }
                
                tables_data[table_name]['columns'].append({
                    'column_name': row['column_name'],
                    'data_type': row['data_type'],
                    'is_primary_key': bool(row['position_pk']),
                    'is_nullable': row['nullable'] == 'Y',
                    'column_comments': row['column_comments'],
                    'column_order': row['column_id'],
                    'data_length': row['data_length'],
                    'data_default': row['data_default']
                })
            
            app_logger.debug(f"테이블 데이터 조회 완료: {len(tables_data)}개 테이블")
            return tables_data
            
        except Exception as e:
            handle_error(e, "테이블 데이터 조회 실패")
            return {}
    
    def _get_relationships_detailed(self) -> List[Dict[str, Any]]:
        """상세 관계 정보 조회"""
        try:
            query = """
                SELECT 
                    r.rel_type,
                    r.confidence,
                    r.condition_expression,
                    src_table.table_name as src_table,
                    src_table.table_owner as src_owner,
                    dst_table.table_name as dst_table,
                    dst_table.table_owner as dst_owner,
                    src_col.column_name as src_column,
                    dst_col.column_name as dst_column,
                    src_col.data_type as src_data_type,
                    dst_col.data_type as dst_data_type
                FROM relationships r
                JOIN components src_comp ON r.src_id = src_comp.component_id
                JOIN components dst_comp ON r.dst_id = dst_comp.component_id
                JOIN tables src_table ON src_comp.component_id = src_table.component_id
                JOIN tables dst_table ON dst_comp.component_id = dst_table.component_id
                JOIN columns src_col ON src_table.table_id = src_col.table_id AND src_col.position_pk > 0
                JOIN columns dst_col ON dst_table.table_id = dst_col.table_id
                JOIN projects p ON src_comp.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND r.del_yn = 'N'
                  AND src_comp.del_yn = 'N'
                  AND dst_comp.del_yn = 'N'
                  AND src_table.del_yn = 'N'
                  AND dst_table.del_yn = 'N'
                  AND r.rel_type LIKE '%JOIN%'
                ORDER BY src_table.table_name, dst_table.table_name
            """
            
            results = self.db_utils.execute_query(query, (self.project_name,))
            
            relationships = []
            for row in results:
                relationships.append({
                    'rel_type': row['rel_type'],
                    'confidence': row['confidence'] or 0.8,
                    'frequency': 1,  # 기본값
                    'src_table': row['src_table'],
                    'src_owner': row['src_owner'],
                    'dst_table': row['dst_table'],
                    'dst_owner': row['dst_owner'],
                    'src_column': row['src_column'],
                    'dst_column': row['dst_column'],
                    'src_data_type': row['src_data_type'],
                    'dst_data_type': row['dst_data_type'],
                    'join_condition': row['condition_expression'],
                    'rel_comment': ''
                })
            
            app_logger.debug(f"관계 정보 조회 완료: {len(relationships)}개")
            return relationships
            
        except Exception as e:
            app_logger.warning(f"관계 정보 조회 실패: {str(e)}")
            return []
    
    def _generate_cytoscape_nodes(self, tables_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Cytoscape.js 노드 데이터 생성"""
        try:
            nodes = []
            
            for table_name, table_info in tables_data.items():
                # Primary Key 컬럼들 추출
                pk_columns = [col for col in table_info['columns'] if col['is_primary_key']]
                pk_column_names = [col['column_name'] for col in pk_columns]
                
                # 노드 데이터 생성 (owner 제거)
                node_data = {
                    'data': {
                        'id': f"table:{table_name}",
                        'type': 'table',
                        'label': table_name,
                        'meta': {
                            'table_name': table_name,
                            'status': 'VALID',
                            'pk_columns': pk_column_names,
                            'comment': table_info['table_comments'] or '',
                            'columns': []
                        }
                    }
                }
                
                # 컬럼 정보 추가
                for col in table_info['columns']:
                    column_data = {
                        'name': col['column_name'],
                        'data_type': col['data_type'],
                        'nullable': 'Y' if col['is_nullable'] else 'N',
                        'is_pk': col['is_primary_key'],
                        'is_foreign_key': False,  # FK 정보는 별도 처리
                        'fk_references': None,
                        'comment': col['column_comments'] or '',
                        'data_length': col['data_length'],
                        'data_default': col['data_default']
                    }
                    node_data['data']['meta']['columns'].append(column_data)
                
                nodes.append(node_data)
            
            app_logger.debug(f"Cytoscape 노드 생성 완료: {len(nodes)}개")
            return nodes
            
        except Exception as e:
            handle_error(e, "Cytoscape 노드 생성 실패")
            return []
    
    def _generate_cytoscape_edges(self, relationships_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Cytoscape.js 엣지 데이터 생성"""
        try:
            edges = []
            
            for rel in relationships_data:
                # 소스와 타겟 노드 ID 생성 (owner 제거)
                src_id = f"table:{rel['src_table']}"
                dst_id = f"table:{rel['dst_table']}"
                
                # 엣지 데이터 생성
                edge_data = {
                    'data': {
                        'id': f"edge:{src_id}->{dst_id}",
                        'source': src_id,
                        'target': dst_id,
                        'type': rel['rel_type'],
                        'label': f"{rel['src_column']} -> {rel['dst_column']}",
                        'meta': {
                            'rel_type': rel['rel_type'],
                            'confidence': rel['confidence'],
                            'frequency': rel['frequency'],
                            'src_table': rel['src_table'],
                            'dst_table': rel['dst_table'],
                            'src_column': rel['src_column'],
                            'dst_column': rel['dst_column'],
                            'src_data_type': rel['src_data_type'],
                            'dst_data_type': rel['dst_data_type'],
                            'join_condition': rel['join_condition'],
                            'rel_comment': rel['rel_comment']
                        }
                    }
                }
                
                edges.append(edge_data)
            
            app_logger.debug(f"Cytoscape 엣지 생성 완료: {len(edges)}개")
            return edges
            
        except Exception as e:
            handle_error(e, "Cytoscape 엣지 생성 실패")
            return []
    
    def _generate_html(self, stats: Dict[str, int], erd_data: Dict[str, Any]) -> str:
        """HTML 생성"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # HTML 템플릿 생성
            html_content = self.templates.get_erd_dagre_template(
                project_name=self.project_name,
                timestamp=timestamp,
                stats=stats,
                erd_data=erd_data
            )
            
            app_logger.debug("ERD(Dagre) HTML 생성 완료")
            return html_content
            
        except Exception as e:
            handle_error(e, "ERD(Dagre) HTML 생성 실패")
            return ""
    
    def _save_report(self, html_content: str) -> str:
        """리포트 파일 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.project_name}_ERD_Dagre_{timestamp}.html"
            output_path = os.path.join(self.output_dir, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            app_logger.info(f"ERD(Dagre) 리포트 파일 저장 완료: {output_path}")
            return output_path
            
        except Exception as e:
            handle_error(e, "ERD(Dagre) 리포트 파일 저장 실패")
            return ""


if __name__ == '__main__':
    # 테스트용 실행
    generator = ERDDagreReportGenerator('sampleSrc', './temp')
    generator.generate_report()
