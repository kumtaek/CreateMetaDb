"""
ERD(Dagre) Report 생성기
- Cytoscape.js와 Dagre 레이아웃을 사용한 고도화 ERD 생성
- 테이블과 컬럼 정보를 활용한 인터랙티브 ERD 생성
- 오프라인 환경 지원 (로컬 라이브러리 사용)
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# 크로스플랫폼 경로 처리는 PathUtils 공통함수 사용
from util.logger import app_logger, handle_error
from util.path_utils import PathUtils
from util.database_utils import DatabaseUtils
from reports.erd_dagre_templates import ERDDagreTemplates
from reports.erd_metadata_service import ERDMetadataService


class ERDDagreReportGenerator:
    """ERD(Dagre) Report 생성기 클래스"""
    
    def __init__(self, project_name: str, output_dir: str, include_orphan_tables: bool = False,
                 show_attributes: bool = True):
        """
        초기화
        
        Args:
            project_name: 프로젝트명
            output_dir: 출력 디렉토리
            include_orphan_tables: 고아 테이블 포함 여부 (기본값: False)
            show_attributes: 컬럼(속성) 표시 여부
        """
        self.project_name = project_name
        self.output_dir = output_dir
        self.include_orphan_tables = include_orphan_tables
        self.show_attributes = show_attributes
        self.path_utils = PathUtils()
        self.templates = ERDDagreTemplates()
        
        # 메타데이터베이스 연결
        self.metadata_db_path = self.path_utils.get_project_metadata_db_path(project_name)
        self.db_utils = DatabaseUtils(self.metadata_db_path)
        
        if not self.db_utils.connect():
            handle_error(Exception("데이터베이스 연결 실패"), f"메타데이터베이스 연결 실패: {self.metadata_db_path}")
        
        # ERD 메타데이터 서비스 초기화
        self.metadata_service = ERDMetadataService(self.db_utils, project_name)
    
    def generate_report(self) -> bool:
        """
        ERD(Dagre) Report 생성
        
        Returns:
            생성 성공 여부 (True/False)
        """
        try:
            app_logger.info(f"ERD(Dagre) Report 생성 시작: {self.project_name} (컬럼 표시: {'Y' if self.show_attributes else 'N'})")
            
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
        """통계 정보 조회 - 공용 서비스 사용"""
        return self.metadata_service.get_statistics()
    
    def _get_cytoscape_data(self) -> Dict[str, Any]:
        """Cytoscape.js 형식의 ERD 데이터 조회 - 공용 서비스 사용"""
        try:
            # 고아 테이블 포함 여부에 따라 다른 메서드 호출
            if self.include_orphan_tables:
                # 모든 테이블 조회 (고아 테이블 포함)
                tables_data = self.metadata_service.get_all_tables_with_columns_detailed()
                app_logger.info("고아 테이블을 포함하여 ERD Dagre 생성")
            else:
                # 관계가 있는 테이블만 조회 (기존 방식)
                tables_data = self.metadata_service.get_tables_with_columns_detailed()
                app_logger.info("관계가 있는 테이블만으로 ERD Dagre 생성")
            
            # 공용 서비스에서 관계 정보 조회
            relationships_data = self.metadata_service.get_relationships()

            # ERD_REPORT_TABLES.cfg 기반 필터 적용
            tables_data, relationships_data = self.metadata_service.apply_table_filter(tables_data, relationships_data)
            
            # INFERRED 컬럼 대상 테이블 맵 생성 (컬럼명 [I]상대테이블명 표기를 위해)
            inferred_targets = self._build_inferred_column_targets(tables_data, relationships_data)
            
            # Cytoscape.js 노드 데이터 생성
            nodes = self._generate_cytoscape_nodes(tables_data, inferred_targets)
            
            # Cytoscape.js 엣지 데이터 생성 (노드 존재 여부 검증)
            edges = self._generate_cytoscape_edges(relationships_data, nodes)
            
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
    
    
    def _generate_cytoscape_nodes(self, tables_data: Dict[str, List[Dict[str, Any]]],
                                  inferred_targets: Optional[Dict[str, Dict[str, str]]]) -> List[Dict[str, Any]]:
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
                        'label': table_name,  # 검색 및 기본 라벨
                        'display_label': '',  # 컬럼 처리 후 설정
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
                column_meta_list = []
                for col in table_info['columns']:
                    inferred_target = None
                    if inferred_targets:
                        inferred_target = inferred_targets.get(table_name, {}).get(col['column_name'])
                    is_foreign_key = col.get('is_foreign_key', False) or bool(inferred_target)
                    column_data = {
                        'name': col['column_name'],
                        'column_name': col['column_name'],  # 라벨 생성 시 사용
                        'data_type': col['data_type'],
                        'nullable': 'Y' if col['is_nullable'] else 'N',
                        'is_pk': col['is_primary_key'],
                        'is_foreign_key': is_foreign_key,
                        'fk_references': inferred_target,
                        'comment': col['column_comments'] or '',
                        'data_length': col['data_length'],
                        'data_default': col['data_default'],
                        'is_inferred': col.get('is_inferred', False),
                        'inferred_from': col.get('inferred_from')
                    }
                    column_meta_list.append(column_data)
                
                node_data['data']['meta']['columns'] = column_meta_list
                
                # 컬럼 메타를 반영한 표시용 라벨 생성
                display_label = self._build_node_label(table_name, column_meta_list)
                node_data['data']['display_label'] = display_label
                
                nodes.append(node_data)
            
            app_logger.debug(f"Cytoscape 노드 생성 완료: {len(nodes)}개")
            return nodes
            
        except Exception as e:
            handle_error(e, "Cytoscape 노드 생성 실패")
            return []

    def _build_node_label(self, table_name: str, columns: List[Dict[str, Any]]) -> str:
        """
        테이블 노드 라벨 생성 (Mermaid ERD와 동일한 포맷)
        
        Args:
            table_name: 테이블명
            columns: 컬럼 정보 목록
        
        Returns:
            Cytoscape 노드 라벨 문자열
        """
        try:
            if not self.show_attributes:
                # 속성 비표시 모드에서는 테이블명만 사용
                return table_name

            # 엔티티 박스 헤더 (테이블명 + 구분선)
            separator = '-' * max(12, min(36, len(table_name) + 6))
            lines = [table_name, separator]

            for col in columns:
                raw_name = col.get('column_name') or col.get('name') or ''
                if not raw_name:
                    continue

                # 표시용 컬럼명: INFERRED 컬럼은 [I] 접두어 제거
                display_name = raw_name[3:] if raw_name.startswith('[I]') else raw_name

                fk_target = col.get('fk_references')
                is_pk = bool(col.get('is_pk') or col.get('is_primary_key'))
                comment = col.get('comment') or ''

                if fk_target:
                    # INFERRED 컬럼: "컬럼명 [I]상대테이블명" (주석 미표시)
                    line = f"{display_name} {fk_target}"
                else:
                    # 일반/PK 컬럼
                    name_part = f"{display_name}(PK)" if is_pk else display_name
                    line = f"{name_part} {comment}" if comment else name_part

                lines.append(line)

            return "\n".join(lines)
        except Exception as e:
            handle_error(e, f"노드 라벨 생성 실패: {table_name}")
            return table_name
    
    def _sanitize_identifier(self, name: str) -> str:
        """
        Mermaid 호환 식별자 생성
        - 공백/특수문자 제거, 숫자로 시작하면 접두어 추가
        """
        try:
            if not name:
                return ""
            sanitized = re.sub(r'[^A-Za-z0-9_]', '_', name)
            if sanitized and sanitized[0].isdigit():
                sanitized = f"_{sanitized}"
            return sanitized
        except Exception as e:
            handle_error(e, f"Mermaid 식별자 정규화 실패: {name}")
            return ""

    def _escape_mermaid_text(self, text: str) -> str:
        """Mermaid 문자열에서 따옴표 등 문제되는 문자를 이스케이프"""
        try:
            return (text or "").replace('"', "'")
        except Exception as e:
            handle_error(e, f"Mermaid 문자열 이스케이프 실패: {text}")
            return ""
    
    def _is_valid_identifier(self, name: str) -> bool:
        """Mermaid에서 허용하는 식별자 패턴 검증 (영문/언더스코어 시작, [I] 접두어 허용)"""
        try:
            if not name:
                return False
            # 리터럴 값은 유효한 식별자가 아님 (YAML 설정 기반)
            from util.oracle_keyword_manager import is_literal_value
            if is_literal_value(name):
                return False
            # [I] 접두어 제거 후 검증 (INFERRED 테이블 지원)
            check_name = name[3:] if name.startswith('[I]') else name
            return bool(re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', check_name))
        except Exception as e:
            handle_error(e, f"Mermaid 식별자 검증 실패: {name}")
            return False

    def _normalize_data_type(self, data_type: str) -> str:
        """데이터 타입 정규화 (길이 정보 보존)"""
        try:
            if not data_type:
                return "string"
            
            # 길이·정밀도 제거 후 타입만 추출
            data_type_clean = re.sub(r'\s+', '', str(data_type))
            data_type_clean = re.sub(r'\((.*?)\)', '', data_type_clean)
            data_type_upper = data_type_clean.upper()

            # VARCHAR, CHAR, TEXT 등 문자열 타입
            if data_type_upper.startswith(('VARCHAR', 'CHAR', 'TEXT')):
                return "string"
            
            # 숫자 타입
            elif data_type_upper.startswith(('INT', 'INTEGER', 'BIGINT', 'SMALLINT')):
                return "int"
            elif data_type_upper.startswith(('DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE')):
                return "float"
            
            # 날짜 타입
            elif data_type_upper.startswith(('DATE', 'TIMESTAMP', 'DATETIME')):
                return "date"
            
            # 기타
            else:
                return data_type
            
        except Exception as e:
            handle_error(e, f"데이터 타입 정규화 실패: {data_type}")
            return "string"
    
    def _generate_cytoscape_edges(self, relationships_data: List[Dict[str, Any]], nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Cytoscape.js 엣지 데이터 생성 - 노드 존재 여부 검증 및 중복 제거"""
        try:
            edges = []
            processed_pairs = set()  # 처리된 테이블 쌍을 추적 (Mermaid ERD와 동일 방향성 유지)
            
            # 존재하는 노드 ID 목록 생성
            existing_node_ids = {node['data']['id'] for node in nodes}
            
            for rel in relationships_data:
                # PK/FK 기준으로 방향 결정 (Mermaid ERD와 동일 로직 사용)
                orientation = self._decide_relationship_orientation(rel)
                if not orientation:
                    continue
                one_table, many_table, one_column, many_column, rel_info = orientation
                
                src_id = f"table:{one_table}"   # 1 측
                dst_id = f"table:{many_table}"  # N 측
                
                # 노드 존재 여부 검증
                if src_id not in existing_node_ids or dst_id not in existing_node_ids:
                    app_logger.debug(f"엣지 제외 (노드 없음): {src_id} -> {dst_id}")
                    continue
                
                # Mermaid ERD와 동일하게 원본 순서 기반으로 중복 제거
                relation_key = (rel['src_table'], rel['dst_table'])
                reverse_key = (rel['dst_table'], rel['src_table'])
                if relation_key in processed_pairs or reverse_key in processed_pairs:
                    continue
                processed_pairs.add(relation_key)
                
                # 엣지 데이터 생성 - 동일한 키로 조인되는 경우 중복 표시 제거
                relationship_label = self._format_relationship_label_deduplicated(one_column, many_column)
                
                # PK-FK 관계 여부: 메타데이터 판단값 사용
                is_pk_fk_relation = rel_info.get('is_pk_fk', False)
                
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
                            'confidence': rel.get('confidence'),
                            'frequency': rel.get('frequency'),
                            'src_table': one_table,        # 1 측 테이블
                            'dst_table': many_table,       # N 측 테이블
                            'src_column': one_column,      # 1 측 컬럼
                            'dst_column': many_column,     # N 측 컬럼
                            'src_data_type': rel.get('src_data_type'),
                            'dst_data_type': rel.get('dst_data_type'),
                            'join_condition': rel.get('join_condition'),
                            'rel_comment': rel.get('rel_comment'),
                            'is_pk_fk': is_pk_fk_relation
                        }
                    }
                }
                
                edges.append(edge_data)
            
            app_logger.debug(f"Cytoscape 엣지 생성 완료 (중복 제거 후): {len(edges)}개")
            return edges
            
        except Exception as e:
            handle_error(e, "Cytoscape 엣지 생성 실패")
            return []

    def _build_inferred_column_targets(
        self,
        tables_data: Dict[str, List[Dict[str, Any]]],
        relationships_data: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, str]]:
        """
        INFERRED 컬럼의 상대 테이블 매핑 생성
        - 예: [I]BRANDS.[I]BRAND_ID -> PRODUCTS  => BRAND_ID [I]PRODUCTS
        """
        inferred_map: Dict[str, Dict[str, str]] = {}

        if not relationships_data:
            return inferred_map

        # 테이블 이름 매핑 (원본 이름 ↔ [I]접두어 이름)
        table_keys = set(tables_data.keys())

        def resolve_table_key(table_name: str) -> Optional[str]:
            if table_name in table_keys:
                return table_name
            inferred_key = f"[I]{table_name}"
            if inferred_key in table_keys:
                return inferred_key
            return None

        for rel in relationships_data:
            for side in ("src", "dst"):
                tbl = rel.get(f"{side}_table")
                other = rel.get("dst_table") if side == "src" else rel.get("src_table")
                col = rel.get(f"{side}_column")

                if not tbl or not other or not col:
                    continue

                table_key = resolve_table_key(tbl)
                if not table_key or table_key not in tables_data:
                    continue

                # 대상 테이블의 INFERRED 컬럼들 중에서 컬럼명 매칭
                for col_meta in tables_data[table_key]["columns"]:
                    raw_name = col_meta.get("column_name") or ""
                    base_name = raw_name[3:] if raw_name.startswith("[I]") else raw_name
                    # INFERRED 컬럼 후보: 조인에서 추론된 컬럼 코멘트
                    if base_name == col and col_meta.get("column_comments") == "조인에서 추론된 컬럼":
                        inferred_map.setdefault(table_key, {})[raw_name] = f"[I]{other}"
                        break

        return inferred_map

    def _decide_relationship_orientation(self, rel: Dict[str, Any]) -> Optional[Tuple[str, str, str, str, Dict[str, Any]]]:
        """
        PK/FK 정보를 기반으로 1측(One)과 N측(Many)을 결정
        
        Returns:
            (one_table, many_table, one_column, many_column, rel_info)
        """
        try:
            raw_src_table = rel['src_table']
            raw_dst_table = rel['dst_table']
            src_column = rel['src_column']
            dst_column = rel['dst_column']
            
            rel_info = self._get_relationship_info_aligned(raw_src_table, src_column, raw_dst_table, dst_column)

            # 관계 신뢰도/PK-FK 판단 기반 필터링 (Mermaid ERD와 동일)
            if not rel_info.get('is_pk_fk', False) and rel.get('confidence', 0.8) < 0.7:
                app_logger.debug(f"Dagre ERD에서 관계 제외 (PK-FK 아님, 신뢰도 낮음): {raw_src_table}.{src_column} -> {raw_dst_table}.{dst_column}")
                return None

            # 방향 결정: PK가 있는 쪽을 1로 설정 (Mermaid와 동일)
            if rel_info.get('src_is_pk') and not rel_info.get('dst_is_pk'):
                one_table, many_table = raw_src_table, raw_dst_table
                one_column, many_column = src_column, dst_column
            elif not rel_info.get('src_is_pk') and rel_info.get('dst_is_pk'):
                one_table, many_table = raw_dst_table, raw_src_table
                one_column, many_column = dst_column, src_column
            else:
                # PK 판단이 모호하면 원본 방향 유지
                one_table, many_table = raw_src_table, raw_dst_table
                one_column, many_column = src_column, dst_column

            return one_table, many_table, one_column, many_column, rel_info
        except Exception as e:
            handle_error(e, f"Dagre 관계 방향 결정 실패: {rel}")
            return None

    def _get_relationship_info_aligned(self, src_table: str, src_column: str, dst_table: str, dst_column: str) -> Dict[str, Any]:
        """
        Mermaid ERD와 동일한 PK/FK 판단 로직 적용
        """
        # [I] 접두어 제거 (INFERRED 테이블 처리)
        src_clean = src_table[3:] if src_table.startswith('[I]') else src_table
        dst_clean = dst_table[3:] if dst_table.startswith('[I]') else dst_table

        rel_info = self.metadata_service.get_relationship_info(src_clean, src_column, dst_clean, dst_column)
        src_is_pk = rel_info.get('src_is_pk', False)
        dst_is_pk = rel_info.get('dst_is_pk', False)
        src_nullable = rel_info.get('src_nullable', True)
        dst_nullable = rel_info.get('dst_nullable', True)

        # 우선순위 1: PK가 한쪽에만 있는 경우 그대로 사용
        # 우선순위 2: 두 쪽 모두 PK 아니거나 둘 다 PK가 아닌 경우 다른 PK 존재 여부로 판단
        if not src_is_pk and not dst_is_pk:
            src_other_pk = self._has_other_pk(src_clean, src_column)
            dst_other_pk = self._has_other_pk(dst_clean, dst_column)
            src_inferred = src_table.startswith('[I]')
            dst_inferred = dst_table.startswith('[I]')

            if src_other_pk and not dst_other_pk:
                src_is_pk = False
                dst_is_pk = True
            elif not src_other_pk and dst_other_pk:
                src_is_pk = True
                dst_is_pk = False
            else:
                # 우선순위 3: INFERRED 여부로 판단
                if src_inferred and not dst_inferred:
                    src_is_pk = True
                    dst_is_pk = False
                elif not src_inferred and dst_inferred:
                    src_is_pk = False
                    dst_is_pk = True

        is_pk_fk = (src_is_pk and not dst_is_pk) or (dst_is_pk and not src_is_pk)

        return {
            'is_pk_fk': is_pk_fk,
            'src_nullable': src_nullable,
            'dst_nullable': dst_nullable,
            'src_is_pk': src_is_pk,
            'dst_is_pk': dst_is_pk
        }

    def _has_other_pk(self, table_name: str, exclude_column: str) -> bool:
        """테이블에 조인 컬럼이 아닌 다른 PK 존재 여부 확인 (Mermaid ERD 로직 정합성)"""
        try:
            query = """
                SELECT c.column_name
                FROM columns c
                JOIN tables t ON c.table_id = t.table_id
                JOIN projects p ON t.project_id = p.project_id
                WHERE t.table_name = ?
                  AND p.project_name = ?
                  AND c.position_pk IS NOT NULL
                  AND c.column_name != ?
                  AND t.del_yn = 'N'
                  AND c.del_yn = 'N'
                LIMIT 1
            """
            result = self.db_utils.execute_query(query, (table_name.upper(), self.project_name, exclude_column.upper()))
            return bool(result)
        except Exception as e:
            handle_error(e, f"다른 PK 존재 여부 확인 실패: {table_name}")
            return False

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
    
    def _format_relationship_label_deduplicated(self, src_column: str, dst_column: str) -> str:
        """관계 라벨 포맷팅 - 중복 제거된 버전"""
        try:
            # 복합키(결합키) 처리 - 콤마로 구분된 경우
            if ',' in src_column and ',' in dst_column:
                src_keys = [key.strip() for key in src_column.split(',')]
                dst_keys = [key.strip() for key in dst_column.split(',')]
                
                # 모든 키가 동일한 경우 하나만 표시
                if set(src_keys) == set(dst_keys):
                    return f"[{', '.join(sorted(src_keys))}]"
                else:
                    # 다른 경우 정렬해서 일관성 있게 표시
                    all_keys = sorted(list(set(src_keys + dst_keys)))
                    return f"[{', '.join(all_keys)}]"
            
            # 단일 키 처리
            elif src_column == dst_column:
                return src_column
            else:
                # 다른 컬럼명이면 정렬해서 일관성 있게 표시
                columns = sorted([src_column, dst_column])
                return f"{columns[0]}↔{columns[1]}"
                
        except Exception as e:
            handle_error(e, f"중복 제거 관계 라벨 포맷팅 실패: {src_column} -> {dst_column}")
            return f"{src_column}↔{dst_column}"
    
    def _generate_html(self, stats: Dict[str, int], erd_data: Dict[str, Any]) -> str:
        """HTML 생성"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # HTML 템플릿 생성
            html_content = self.templates.get_erd_dagre_template(
                project_name=self.project_name,
                timestamp=timestamp,
                stats=stats,
                erd_data=erd_data,
                show_attributes=self.show_attributes
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
    import sys
    from util.arg_utils import ArgUtils
    
    # 명령행 인자 파싱
    arg_utils = ArgUtils()
    parser = arg_utils.create_parser("ERD Dagre Report 생성기")
    parser.add_argument('--include-orphan', action='store_true', 
                       help='고아 테이블(관계가 없는 테이블)도 ERD에 포함')
    args = parser.parse_args()
    
    project_name = args.project_name
    include_orphan = args.include_orphan
    print(f"ERD Dagre Report 생성 시작: {project_name} (고아 테이블 포함: {include_orphan})")
    
    generator = ERDDagreReportGenerator(project_name, './temp', include_orphan)
    result = generator.generate_report()
    
    if result:
        print(f"ERD Dagre Report 생성 완료: {project_name}")
    else:
        print(f"ERD Dagre Report 생성 실패: {project_name}")
