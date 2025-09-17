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

# 크로스플랫폼 경로 처리는 PathUtils 공통함수 사용

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
            
            # 5. js 폴더 복사
            self._copy_js_folder()
            
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
            
            # Primary Key 수 (실제 쿼리에서 사용된 컬럼 기준)
            query = """
                SELECT COUNT(DISTINCT c.column_name) as count
                FROM columns c
                JOIN tables t ON c.table_id = t.table_id
                JOIN projects p ON t.project_id = p.project_id
                WHERE p.project_name = ? AND c.del_yn = 'N' AND t.del_yn = 'N'
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
            # 먼저 테이블 간 관계만 조회 (컬럼 정보는 별도 처리)
            query = """
                SELECT 
                    r.rel_type,
                    r.confidence,
                    src_table.table_name as src_table,
                    src_table.table_owner as src_owner,
                    dst_table.table_name as dst_table,
                    dst_table.table_owner as dst_owner
                FROM relationships r
                JOIN components src_comp ON r.src_id = src_comp.component_id
                JOIN components dst_comp ON r.dst_id = dst_comp.component_id
                JOIN tables src_table ON src_comp.component_id = src_table.component_id
                JOIN tables dst_table ON dst_comp.component_id = dst_table.component_id
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
                # 조인 조건에서 컬럼 정보 추출 (condition_expression 컬럼이 없으므로 기본값 사용)
                src_column, dst_column = self._extract_join_columns(
                    None, 
                    row['src_table'], 
                    row['dst_table']
                )
                
                if src_column and dst_column:
                    # 컬럼 데이터 타입 조회
                    src_data_type, dst_data_type = self._get_column_data_types(
                        row['src_table'], src_column, 
                        row['dst_table'], dst_column
                    )
                    
                    # PK-FK 관계 여부 확인
                    is_pk_fk_relation = self._is_pk_fk_relation(
                        row['src_table'], src_column, 
                        row['dst_table'], dst_column
                    )
                    
                    # 관계 불명확한 경우 필터링 (PK-FK 관계가 아니고 신뢰도가 낮은 경우)
                    if not is_pk_fk_relation and (row['confidence'] or 0.8) < 0.7:
                        app_logger.debug(f"관계 불명확하여 제외: {row['src_table']}.{src_column} -> {row['dst_table']}.{dst_column} (신뢰도: {row['confidence'] or 0.8})")
                        continue
                    
                    relationships.append({
                        'rel_type': row['rel_type'],
                        'confidence': row['confidence'] or 0.8,
                        'frequency': 1,  # 기본값
                        'src_table': row['src_table'],
                        'src_owner': row['src_owner'],
                        'dst_table': row['dst_table'],
                        'dst_owner': row['dst_owner'],
                        'src_column': src_column,
                        'dst_column': dst_column,
                        'src_data_type': src_data_type,
                        'dst_data_type': dst_data_type,
                        'join_condition': None,  # condition_expression 컬럼이 존재하지 않음
                        'rel_comment': '',
                        'is_pk_fk': is_pk_fk_relation
                    })
            
            app_logger.debug(f"관계 정보 조회 완료: {len(relationships)}개")
            return relationships
            
        except Exception as e:
            handle_error(e, "관계 정보 조회 실패")
    
    def _extract_join_columns(self, condition_expression: str, src_table: str, dst_table: str) -> tuple:
        """조인 조건에서 소스와 대상 컬럼 추출"""
        try:
            if not condition_expression:
                # 조건이 없으면 실제 데이터베이스 스키마 기반으로 추측
                return self._find_foreign_key_columns(src_table, dst_table)
            
            # 조건에서 컬럼 추출 (예: "p.brand_id = b.brand_id")
            import re
            
            # 테이블별칭.컬럼명 = 테이블별칭.컬럼명 패턴 매칭
            pattern = r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)'
            match = re.search(pattern, condition_expression, re.IGNORECASE)
            
            if match:
                left_table_alias, left_column, right_table_alias, right_column = match.groups()
                
                # 실제 데이터베이스 스키마를 기반으로 컬럼 유효성 검증
                if self._is_valid_column_pair(src_table, left_column, dst_table, right_column):
                    return left_column, right_column
                elif self._is_valid_column_pair(src_table, right_column, dst_table, left_column):
                    return right_column, left_column
                else:
                    # 유효한 컬럼 쌍이 없으면 스키마 기반 추측
                    return self._find_foreign_key_columns(src_table, dst_table)
            
            # 패턴 매칭 실패시 실제 데이터베이스 스키마 기반으로 추측
            return self._find_foreign_key_columns(src_table, dst_table)
            
        except Exception as e:
            handle_error(e, f"조인 컬럼 추출 실패: {condition_expression}")
    
    def _is_valid_column_pair(self, src_table: str, src_column: str, dst_table: str, dst_column: str) -> bool:
        """실제 데이터베이스 스키마를 기반으로 컬럼 쌍의 유효성 검증"""
        try:
            query = """
                SELECT COUNT(*) as count
                FROM tables src_t
                JOIN columns src_col ON src_t.table_id = src_col.table_id
                JOIN tables dst_t ON dst_t.table_name = ?
                JOIN columns dst_col ON dst_t.table_id = dst_col.table_id
                JOIN projects p ON src_t.project_id = p.project_id
                WHERE src_t.table_name = ? 
                  AND p.project_name = ?
                  AND src_t.del_yn = 'N' 
                  AND dst_t.del_yn = 'N'
                  AND src_col.del_yn = 'N'
                  AND dst_col.del_yn = 'N'
                  AND src_col.column_name = ?
                  AND dst_col.column_name = ?
            """
            
            result = self.db_utils.execute_query(query, (dst_table, src_table, self.project_name, src_column, dst_column))
            return result[0]['count'] > 0 if result else False
            
        except Exception as e:
            handle_error(e, f"컬럼 쌍 유효성 검증 실패: {src_table}.{src_column} -> {dst_table}.{dst_column}")
    
    def _find_foreign_key_columns(self, src_table: str, dst_table: str) -> tuple:
        """CSV에서 업로드된 정확한 PK 정보를 기반으로 외래키 컬럼 찾기"""
        try:
            # 1. 먼저 PK-PK 매칭 시도 (동일한 PK 컬럼명)
            query = """
                SELECT 
                    src_col.column_name as src_column,
                    dst_col.column_name as dst_column
                FROM tables src_t
                JOIN columns src_col ON src_t.table_id = src_col.table_id
                JOIN tables dst_t ON dst_t.table_name = ?
                JOIN columns dst_col ON dst_t.table_id = dst_col.table_id
                JOIN projects p ON src_t.project_id = p.project_id
                WHERE src_t.table_name = ? 
                  AND p.project_name = ?
                  AND src_t.del_yn = 'N' 
                  AND dst_t.del_yn = 'N'
                  AND src_col.del_yn = 'N'
                  AND dst_col.del_yn = 'N'
                  AND src_col.column_name = dst_col.column_name
                  AND src_col.position_pk IS NOT NULL
                  AND dst_col.position_pk IS NOT NULL
                LIMIT 1
            """
            
            result = self.db_utils.execute_query(query, (dst_table, src_table, self.project_name))
            
            if result:
                column_name = result[0]['src_column']
                return column_name, column_name
            
            # 2. FK-PK 매칭 시도 (소스는 PK가 아니고, 대상은 PK)
            query = """
                SELECT 
                    src_col.column_name as src_column,
                    dst_col.column_name as dst_column
                FROM tables src_t
                JOIN columns src_col ON src_t.table_id = src_col.table_id
                JOIN tables dst_t ON dst_t.table_name = ?
                JOIN columns dst_col ON dst_t.table_id = dst_col.table_id
                JOIN projects p ON src_t.project_id = p.project_id
                WHERE src_t.table_name = ? 
                  AND p.project_name = ?
                  AND src_t.del_yn = 'N' 
                  AND dst_t.del_yn = 'N'
                  AND src_col.del_yn = 'N'
                  AND dst_col.del_yn = 'N'
                  AND src_col.column_name = dst_col.column_name
                  AND src_col.position_pk IS NULL
                  AND dst_col.position_pk IS NOT NULL
                LIMIT 1
            """
            
            result = self.db_utils.execute_query(query, (dst_table, src_table, self.project_name))
            
            if result:
                column_name = result[0]['src_column']
                return column_name, column_name
            
            # 3. 일반적인 컬럼명 매칭 시도 (ID로 끝나는 컬럼)
            query = """
                SELECT 
                    src_col.column_name as src_column,
                    dst_col.column_name as dst_column
                FROM tables src_t
                JOIN columns src_col ON src_t.table_id = src_col.table_id
                JOIN tables dst_t ON dst_t.table_name = ?
                JOIN columns dst_col ON dst_t.table_id = dst_col.table_id
                JOIN projects p ON src_t.project_id = p.project_id
                WHERE src_t.table_name = ? 
                  AND p.project_name = ?
                  AND src_t.del_yn = 'N' 
                  AND dst_t.del_yn = 'N'
                  AND src_col.del_yn = 'N'
                  AND dst_col.del_yn = 'N'
                  AND src_col.column_name = dst_col.column_name
                  AND src_col.column_name LIKE '%_ID'
                LIMIT 1
            """
            
            result = self.db_utils.execute_query(query, (dst_table, src_table, self.project_name))
            
            if result:
                column_name = result[0]['src_column']
                return column_name, column_name
            
            # 매칭되는 컬럼이 없으면 None 반환 (관계 제외)
            app_logger.debug(f"외래키 컬럼 매칭 실패: {src_table} -> {dst_table}")
            return None, None
                
        except Exception as e:
            handle_error(e, f"외래키 컬럼 추측 실패: {src_table} -> {dst_table}")
    
    def _get_column_data_types(self, src_table: str, src_column: str, dst_table: str, dst_column: str) -> tuple:
        """컬럼의 데이터 타입 조회"""
        try:
            query = """
                SELECT 
                    c1.data_type as src_data_type,
                    c2.data_type as dst_data_type
                FROM tables t1
                JOIN columns c1 ON t1.table_id = c1.table_id
                JOIN tables t2 ON t2.table_name = ?
                JOIN columns c2 ON t2.table_id = c2.table_id
                JOIN projects p ON t1.project_id = p.project_id
                WHERE t1.table_name = ? 
                  AND c1.column_name = ?
                  AND c2.column_name = ?
                  AND p.project_name = ?
                  AND t1.del_yn = 'N' 
                  AND t2.del_yn = 'N'
                  AND c1.del_yn = 'N'
                  AND c2.del_yn = 'N'
            """
            
            result = self.db_utils.execute_query(query, (dst_table, src_table, src_column, dst_column, self.project_name))
            
            if result:
                return result[0]['src_data_type'], result[0]['dst_data_type']
            else:
                return 'VARCHAR2', 'VARCHAR2'  # 기본값
                
        except Exception as e:
            handle_error(e, f"컬럼 데이터 타입 조회 실패: {src_table}.{src_column} -> {dst_table}.{dst_column}")
    
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
                
                # 엣지 데이터 생성 - 동일한 키로 조인되는 경우 중복 표시 제거
                relationship_label = self._format_relationship_label(rel['src_column'], rel['dst_column'])
                
                # PK-FK 관계 여부는 이미 관계 정보에서 가져옴
                is_pk_fk_relation = rel.get('is_pk_fk', False)
                
                edge_data = {
                    'data': {
                        'id': f"edge:{src_id}->{dst_id}",
                        'source': src_id,
                        'target': dst_id,
                        'type': rel['rel_type'],
                        'label': relationship_label,
                        'is_pk_fk': is_pk_fk_relation,  # PK-FK 관계 여부 추가
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
                            'rel_comment': rel['rel_comment'],
                            'is_pk_fk': is_pk_fk_relation
                        }
                    }
                }
                
                edges.append(edge_data)
            
            app_logger.debug(f"Cytoscape 엣지 생성 완료: {len(edges)}개")
            return edges
            
        except Exception as e:
            handle_error(e, "Cytoscape 엣지 생성 실패")
            return []
    
    def _is_pk_fk_relation(self, src_table: str, src_column: str, dst_table: str, dst_column: str) -> bool:
        """CSV에서 업로드된 PK 정보를 기반으로 PK-FK 관계인지 확인"""
        try:
            # 소스 컬럼과 대상 컬럼의 PK 여부 확인
            query = """
                SELECT 
                    src_col.position_pk as src_is_pk,
                    dst_col.position_pk as dst_is_pk
                FROM tables src_t
                JOIN columns src_col ON src_t.table_id = src_col.table_id
                JOIN tables dst_t ON dst_t.table_name = ?
                JOIN columns dst_col ON dst_t.table_id = dst_col.table_id
                JOIN projects p ON src_t.project_id = p.project_id
                WHERE src_t.table_name = ? 
                  AND p.project_name = ?
                  AND src_t.del_yn = 'N' 
                  AND dst_t.del_yn = 'N'
                  AND src_col.del_yn = 'N'
                  AND dst_col.del_yn = 'N'
                  AND src_col.column_name = ?
                  AND dst_col.column_name = ?
            """
            
            result = self.db_utils.execute_query(query, (dst_table, src_table, self.project_name, src_column, dst_column))
            
            if result:
                src_is_pk = result[0]['src_is_pk'] is not None
                dst_is_pk = result[0]['dst_is_pk'] is not None
                
                # PK-FK 관계 판단: 한쪽은 PK이고 다른 쪽은 PK가 아닌 경우
                # 1. 소스가 PK이고 대상이 PK가 아닌 경우 (PK -> FK)
                # 2. 소스가 PK가 아니고 대상이 PK인 경우 (FK -> PK)
                return (src_is_pk and not dst_is_pk) or (not src_is_pk and dst_is_pk)
            
            return False
                
        except Exception as e:
            handle_error(e, f"PK-FK 관계 확인 실패: {src_table}.{src_column} -> {dst_table}.{dst_column}")

    def _format_relationship_label(self, src_column: str, dst_column: str) -> str:
        """관계 라벨 포맷팅 - 양방향 관계에서 글자 겹침 방지"""
        try:
            # 복합키(결합키) 처리 - 콤마로 구분된 경우
            if ',' in src_column and ',' in dst_column:
                src_keys = [key.strip() for key in src_column.split(',')]
                dst_keys = [key.strip() for key in dst_column.split(',')]
                
                # 동일한 키로 조인되는 경우 하나만 표시
                if src_keys == dst_keys:
                    return f"[{', '.join(src_keys)}]"
                else:
                    # 다른 경우 하이픈으로 연결
                    return f"[{', '.join(src_keys)}]-[{', '.join(dst_keys)}]"
            
            # 단일 키 처리
            elif src_column == dst_column:
                return src_column
            else:
                # 다른 경우 하이픈으로 연결
                return f"{src_column}-{dst_column}"
                
        except Exception as e:
            handle_error(e, f"관계 라벨 포맷팅 실패: {src_column} -> {dst_column}")
    
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
            filename = f"[{self.project_name}]_ERD_Dagre_{timestamp}.html"
            output_path = self.path_utils.join_path(self.output_dir, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            app_logger.info(f"ERD(Dagre) 리포트 파일 저장 완료: {output_path}")
            return output_path
            
        except Exception as e:
            handle_error(e, "ERD(Dagre) 리포트 파일 저장 실패")
    
    def _copy_js_folder(self) -> bool:
        """js 폴더를 출력 디렉토리로 복사 (권한 오류 방지)"""
        try:
            import shutil
            import time
            
            # JS 디렉토리 생성
            js_dir = self.path_utils.join_path(self.output_dir, "js")
            if not os.path.exists(js_dir):
                os.makedirs(js_dir)
            
            # 올바른 JS 파일들 복사 (재시도 로직 포함)
            # reports 폴더에서 찾기
            reports_path = self.path_utils.get_reports_path()
            source_js_dir = self.path_utils.join_path(reports_path, "js")
            
            if os.path.exists(source_js_dir):
                for js_file in os.listdir(source_js_dir):
                    if js_file.endswith('.js'):
                        source_js = self.path_utils.join_path(source_js_dir, js_file)
                        dest_js = self.path_utils.join_path(js_dir, js_file)
                        self._safe_copy_file(source_js, dest_js, f"JS ({js_file})")
                return True
            else:
                handle_error(Exception(f"소스 JS 디렉토리가 존재하지 않습니다: {source_js_dir}"), "JS 디렉토리 부재")
            
        except Exception as e:
            from util.logger import handle_error
            handle_error(e, "JS 폴더 복사 실패")
    
    def _safe_copy_file(self, source: str, dest: str, file_type: str, max_retries: int = 3):
        """파일 복사 (권한 오류 방지를 위한 재시도 로직)"""
        import shutil
        import time
        
        for attempt in range(max_retries):
            try:
                # 대상 파일이 이미 존재하고 사용 중인 경우 삭제 시도
                if os.path.exists(dest):
                    try:
                        os.remove(dest)
                    except PermissionError:
                        # 삭제 실패 시 잠시 대기 후 재시도
                        time.sleep(0.1)
                        continue
                
                # 파일 복사
                shutil.copy2(source, dest)
                app_logger.debug(f"{file_type} 파일 복사 완료: {dest}")
                return True
                
            except PermissionError as e:
                if attempt < max_retries - 1:
                    time.sleep(0.2)  # 200ms 대기
                else:
                    handle_error(e, f"{file_type} 파일 복사 실패 (최대 재시도 횟수 초과): {source} -> {dest}")
            except Exception as e:
                handle_error(e, f"{file_type} 파일 복사 실패")
        
        return False


if __name__ == '__main__':
    # 테스트용 실행
    generator = ERDDagreReportGenerator('sampleSrc', './temp')
    generator.generate_report()
