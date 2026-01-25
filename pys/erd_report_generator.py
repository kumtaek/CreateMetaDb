"""
ERD Report 생성기
- 테이블과 컬럼 정보를 활용한 Mermaid ERD 생성
- 테이블 간 관계 시각화
- 오프라인 환경 지원 (Mermaid.js 로컬화)
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# 크로스플랫폼 경로 처리는 PathUtils 공통함수 사용

from util.logger import app_logger, handle_error
from util.path_utils import PathUtils
from util.database_utils import DatabaseUtils
from util.report_utils import ReportUtils
from reports.report_templates import ReportTemplates
from reports.erd_metadata_service import ERDMetadataService
import json


class ERDReportGenerator:
    """ERD Report 생성기 클래스"""
    
    def __init__(self, project_name: str, output_dir: str, include_orphan_tables: bool = False):
        """
        초기화
        
        Args:
            project_name: 프로젝트명
            output_dir: 출력 디렉토리
            include_orphan_tables: 고아 테이블 포함 여부 (기본값: False)
        """
        self.project_name = project_name
        self.output_dir = output_dir
        self.include_orphan_tables = include_orphan_tables
        self.path_utils = PathUtils()
        self.templates = ReportTemplates()
        self.report_utils = ReportUtils(project_name, output_dir)
        
        # 메타데이터베이스 연결
        self.metadata_db_path = self.path_utils.get_project_metadata_db_path(project_name)
        self.db_utils = DatabaseUtils(self.metadata_db_path)
        
        if not self.db_utils.connect():
            handle_error(Exception("데이터베이스 연결 실패"), f"메타데이터베이스 연결 실패: {self.metadata_db_path}")
        
        # ERD 메타데이터 서비스 초기화
        self.metadata_service = ERDMetadataService(self.db_utils, project_name)
    
    def generate_report(self) -> bool:
        """
        ERD Report 생성
        
        Returns:
            생성 성공 여부 (True/False)
        """
        try:
            app_logger.info(f"ERD Report 생성 시작: {self.project_name}")
            
            # 1. 통계 정보 조회
            stats = self._get_statistics()
            
            # 2. ERD 데이터 조회 (N+1 쿼리 문제 해결)
            erd_data = self._get_erd_data()
            
            # 3. HTML 생성
            html_content = self._generate_html(stats, erd_data)
            
            # 4. CSS 및 JS 파일 복사
            self.report_utils.copy_assets()
            
            # 5. 파일 저장
            output_file = self._save_report(html_content)
            
            app_logger.info(f"ERD Report 생성 완료: {output_file}")  # 최종 완료는 info 유지
            return True
            
        except Exception as e:
            handle_error(e, "ERD Report 생성 실패")
            return False
        finally:
            self.db_utils.disconnect()
    
    def _get_statistics(self) -> Dict[str, int]:
        """통계 정보 조회 - 공용 서비스 사용"""
        return self.metadata_service.get_statistics()
    
    def _get_erd_data(self) -> Dict[str, Any]:
        """ERD 데이터 조회 - 공용 서비스 사용"""
        try:
            # 고아 테이블 포함 여부에 따라 다른 메서드 호출
            if self.include_orphan_tables:
                # 모든 테이블 조회 (고아 테이블 포함)
                tables_data = self.metadata_service.get_all_tables_with_columns()
                app_logger.info("고아 테이블을 포함하여 ERD 생성")
            else:
                # 관계가 있는 테이블만 조회 (기존 방식)
                tables_data = self.metadata_service.get_tables_with_columns()
                app_logger.info("관계가 있는 테이블만으로 ERD 생성")
            
            # 공용 서비스에서 관계 정보 조회
            relationships = self.metadata_service.get_relationships()
            
            # 데이터 유효성 검증 (빈 리포트 생성 방지)
            if not tables_data or not relationships:
                # 관계가 없거나 관계 기반 테이블 조회가 비어 있으면 include_orphan_tables=True일 때만 전체 테이블로 대체
                app_logger.warning(
                    f"관계/테이블 데이터 부족 "
                    f"(tables={len(tables_data) if tables_data else 0}, rel={len(relationships) if relationships else 0})"
                )
                if self.include_orphan_tables:
                    tables_data = self.metadata_service.get_all_tables_with_columns()
                else:
                    if not relationships:
                        tables_data = {}
                relationships = relationships or []
            
            if not tables_data:
                app_logger.error("ERD를 생성할 테이블 데이터가 없습니다.")
                raise Exception("ERD 생성 실패: 테이블 데이터 없음")
            
            # 필터 파일(ERD_REPORT_TABLES.cfg) 적용
            tables_data, relationships = self.metadata_service.apply_table_filter(tables_data, relationships)

            # 테이블 코멘트 조회 (Dagre 상세 메타데이터 재사용)
            detailed_tables = self.metadata_service.get_all_tables_with_columns_detailed()
            table_comments_map = {
                name: (info.get('table_comments') or '')
                for name, info in detailed_tables.items()
            }
            table_owner_map = {
                name: (info.get('table_owner') or '')
                for name, info in detailed_tables.items()
            }

            # Mermaid ERD 코드 생성
            mermaid_code = self._generate_mermaid_erd(
                tables_data,
                relationships,
                table_comments_map,
                table_owner_map,
            )
            
            erd_data = {
                'tables': tables_data,
                'relationships': relationships,
                'mermaid_code': mermaid_code
            }
            
            app_logger.debug(f"ERD 데이터 조회 완료: {len(tables_data)}개 테이블, {len(relationships)}개 관계")
            return erd_data
            
        except Exception as e:
            handle_error(e, "ERD 데이터 조회 실패")
            return {'tables': {}, 'relationships': [], 'mermaid_code': ''}
    
    
    def _extract_join_columns(self, condition_expression: str, src_table: str, dst_table: str) -> tuple:
        """조인 조건에서 소스와 대상 컬럼 추출"""
        try:
            if not condition_expression:
                # 조건이 없으면 메타데이터 기반으로 추출
                return self.metadata_service.get_join_columns_from_metadata(src_table, dst_table)
            
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
                    return self._guess_foreign_key_columns(src_table, dst_table)
            
            # 패턴 매칭 실패시 실제 데이터베이스 스키마 기반으로 추측
            return self._guess_foreign_key_columns(src_table, dst_table)
            
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
            
            result = self.db_utils.execute_query(query, (dst_table.upper(), src_table.upper(), self.project_name, src_column.upper(), dst_column.upper()))
            return result[0]['count'] > 0 if result else False
            
        except Exception as e:
            handle_error(e, f"컬럼 쌍 유효성 검증 실패: {src_table}.{src_column} -> {dst_table}.{dst_column}")
    
    
    def _generate_mermaid_erd(
        self,
        tables_data: Dict[str, List[Dict[str, Any]]],
        relationships: List[Dict[str, Any]],
        table_comments_map: Optional[Dict[str, str]] = None,
        table_owner_map: Optional[Dict[str, str]] = None,
    ) -> str:
        """Mermaid ERD 코드 생성"""
        try:
            table_comments_map = table_comments_map or {}
            table_owner_map = table_owner_map or {}
            mermaid_lines = ["erDiagram"]
            table_label_map: Dict[str, str] = {}
            target_table_hits = 0
            target_rel_hits = 0
            
            # 테이블 정의
            for table_name, columns in tables_data.items():
                upper_name = table_name.upper()
                base_name = upper_name[3:] if upper_name.startswith("[I]") else upper_name
                base_name = base_name.split(".")[-1] if "." in base_name else base_name
                if base_name == "PLAR_PAFF_BAS":
                    target_table_hits += 1
                    app_logger.info(
                        f"[ERD DEBUG][TABLE] name={table_name}, inferred_prefix={table_name.startswith('[I]')}, columns={len(columns)}"
                    )
                # 테이블 표시용 라벨 생성 (테이블명 30바이트, 코멘트 30바이트)
                label_table_name = self._build_table_label_for_mermaid(
                    table_name,
                    table_comments_map,
                    table_owner_map,
                )
                if not label_table_name:
                    app_logger.warning(f"Mermaid ERD에서 테이블명을 정규화할 수 없어 제외: {table_name}")
                    continue

                table_label_map[table_name] = label_table_name
                mermaid_lines.append(f'    "{label_table_name}" {{')

                # 컬럼 정의 - 데이터 타입, PK 여부, 컬럼 코멘트만 표시
                for column in columns:
                    try:
                        column_name = column.get('column_name')
                        if not column_name:
                            continue

                        # INFERRED 컬럼의 데이터 타입은 UNKNOWN으로 통일 (스키마에 없음)
                        data_type = column.get('data_type') or 'UNKNOWN'
                        if column.get('is_inferred'):
                            data_type = 'UNKNOWN'

                        is_pk = bool(column.get('is_primary_key'))
                        # NULL 여부는 표시하지 않고, 컬럼 코멘트를 사용
                        # (사용자 요구사항: NOT NULL 대신 코멘트 표시)
                        comment = column.get('column_comments') or ''

                        # INFERRED 컬럼은 코멘트 대신 조인 상대 테이블명을 "[I]상대테이블명" 형식으로 표시
                        if column.get('is_inferred') and not comment:
                            inferred_from = column.get('inferred_from')
                            if inferred_from:
                                comment = f"[I]{inferred_from}"

                        # 컬럼 코멘트 바이트 길이 제한 (30바이트)
                        if comment:
                            comment = self._truncate_by_bytes(str(comment), 30)

                        # 출력 순서: 컬럼명 → 데이터 타입 → PK → 코멘트
                        line_parts = [f"        {column_name}", data_type]
                        if is_pk:
                            line_parts.append("PK")
                        if comment:
                            safe_comment = self._escape_mermaid_text(str(comment))
                            line_parts.append(f'"{safe_comment}"')

                        mermaid_lines.append(" ".join(line_parts))
                    except Exception as col_e:
                        # 컬럼 하나에 문제가 생겨도 전체 ERD 생성은 계속 진행
                        app_logger.error(
                            f"Mermaid ERD 컬럼 처리 실패: {table_name}.{column.get('column_name')} - {col_e}"
                        )

                # 테이블 블록 종료
                mermaid_lines.append("    }")

            seen_relationships = set()
            relationship_count = 0
            
            for rel in relationships:
                    
                # 테이블 라벨 확인
                src_label = self._resolve_table_label_for_mermaid(rel['src_table'], table_label_map)
                dst_label = self._resolve_table_label_for_mermaid(rel['dst_table'], table_label_map)
                if not src_label or not dst_label:
                    src_base = self.metadata_service._normalize_table_name(rel.get('src_table'))
                    dst_base = self.metadata_service._normalize_table_name(rel.get('dst_table'))
                    if {src_base, dst_base} == {'CS_BAS', 'TEL_INF'}:
                        app_logger.info(
                            "[ERD DEBUG] 라벨 매핑 실패로 관계 스킵: "
                            f"src={rel.get('src_table')}, dst={rel.get('dst_table')}, "
                            f"src_label={src_label}, dst_label={dst_label}"
                        )
                    continue
                if not (self._is_valid_identifier(rel['src_column']) and self._is_valid_identifier(rel['dst_column'])):
                    src_base = self.metadata_service._normalize_table_name(rel.get('src_table'))
                    dst_base = self.metadata_service._normalize_table_name(rel.get('dst_table'))
                    if {src_base, dst_base} == {'CS_BAS', 'TEL_INF'}:
                        app_logger.info(
                            "[ERD DEBUG] 컬럼 식별자 불일치로 관계 스킵: "
                            f"src={rel.get('src_table')}.{rel.get('src_column')}, "
                            f"dst={rel.get('dst_table')}.{rel.get('dst_column')}"
                        )
                    continue
                def _normalize(name: str) -> str:
                    up = name.upper()
                    up = up[3:] if up.startswith("[I]") else up
                    return up.split(".")[-1] if "." in up else up

                if _normalize(rel['src_table']) == "PLAR_PAFF_BAS" or _normalize(rel['dst_table']) == "PLAR_PAFF_BAS":
                    target_rel_hits += 1
                    app_logger.info(
                        f"[ERD DEBUG][REL] {rel['src_table']}.{rel['src_column']} -> {rel['dst_table']}.{rel['dst_column']} "
                        f"label_src={src_label}, label_dst={dst_label}"
                    )

                # 중복 관계 제거 (방향성 고려하여 중복 제거)
                rel_key = f"{src_label}-{dst_label}"
                reverse_key = f"{dst_label}-{src_label}"
                if rel_key in seen_relationships or reverse_key in seen_relationships:
                    src_base = self.metadata_service._normalize_table_name(rel.get('src_table'))
                    dst_base = self.metadata_service._normalize_table_name(rel.get('dst_table'))
                    if {src_base, dst_base} == {'CS_BAS', 'TEL_INF'}:
                        app_logger.info(
                            f"[ERD DEBUG] 중복 관계로 스킵: {src_label} <-> {dst_label}"
                        )
                    continue
                seen_relationships.add(rel_key)
                
                # 관계 유형별 Mermaid 문법 적용
                # 동일한 키로 조인되는 경우 중복 표시 제거
                relationship_label = self._format_relationship_label(rel['src_table'], rel['src_column'], rel['dst_table'], rel['dst_column'])
                
                # 관계 정보 확인 (PK-FK 여부, nullable 여부)
                rel_info = self._get_relationship_info(rel['src_table'], rel['src_column'], rel['dst_table'], rel['dst_column'])
                is_pk_fk_relation = rel_info['is_pk_fk']
                src_nullable = rel_info['src_nullable']
                dst_nullable = rel_info['dst_nullable']
                
                # 관계 불명확한 경우 필터링 (PK-FK 관계가 아니고 신뢰도가 낮은 경우)
                if not is_pk_fk_relation and rel.get('confidence', 0.8) < 0.7:
                    src_base = self.metadata_service._normalize_table_name(rel.get('src_table'))
                    dst_base = self.metadata_service._normalize_table_name(rel.get('dst_table'))
                    if {src_base, dst_base} == {'CS_BAS', 'TEL_INF'}:
                        app_logger.info(
                            "[ERD DEBUG] 신뢰도 기준으로 관계 스킵: "
                            f"src={rel.get('src_table')}.{rel.get('src_column')}, "
                            f"dst={rel.get('dst_table')}.{rel.get('dst_column')}, "
                            f"confidence={rel.get('confidence', 0.8)}"
                        )
                    app_logger.debug(f"Mermaid ERD에서 관계 불명확하여 제외: {rel['src_table']}.{rel['src_column']} -> {rel['dst_table']}.{rel['dst_column']} (신뢰도: {rel.get('confidence', 0.8)})")
                    continue
                
                # ERD 관계 방향 결정: PK가 있는 쪽이 1(왼쪽), FK가 있는 쪽이 N(오른쪽)
                # Mermaid 문법: A ||--o{ B 는 A(1) : B(N) 관계를 의미
                if rel_info['src_is_pk'] and not rel_info['dst_is_pk']:
                    # src가 PK, dst가 FK → src(1) : dst(N)
                    one_side = src_label
                    many_side = dst_label
                elif not rel_info['src_is_pk'] and rel_info['dst_is_pk']:
                    # src가 FK, dst가 PK → dst(1) : src(N)
                    one_side = dst_label
                    many_side = src_label
                else:
                    # PK-FK 관계가 명확하지 않은 경우, 기본적으로 src → dst 방향 사용
                    one_side = src_label
                    many_side = dst_label

                # ERD는 단순 문법만 지원: A ||--o{ B : has 형태만 사용
                mermaid_lines.append(f'    "{one_side}" ||--o{{ "{many_side}" : {relationship_label}')

                relationship_count += 1
            
            mermaid_code = '\n'.join(mermaid_lines)
            if target_table_hits or target_rel_hits:
                app_logger.info(f"[ERD DEBUG] PLAR_PAFF_BAS 관련: 테이블 노드 {target_table_hits}건, 관계 {target_rel_hits}건")
            app_logger.debug("Mermaid ERD 코드 생성 완료")
            return mermaid_code
            
        except Exception as e:
            handle_error(e, "Mermaid ERD 코드 생성 실패")
            return ""
    
    def _get_relationship_info(self, src_table: str, src_column: str, dst_table: str, dst_column: str) -> dict:
        """관계 정보 확인 - 3단계 우선순위 로직으로 PK-FK 판단"""
        # [I] 접두어 제거 (INFERRED 테이블 처리)
        src_table_clean = src_table[3:] if src_table.startswith('[I]') else src_table
        dst_table_clean = dst_table[3:] if dst_table.startswith('[I]') else dst_table
        src_is_inferred = src_table.startswith('[I]')
        dst_is_inferred = dst_table.startswith('[I]')

        rel_info = self.metadata_service.get_relationship_info(src_table_clean, src_column, dst_table_clean, dst_column)

        # 우선순위 1: 조인 컬럼의 PK 여부 (이미 rel_info에서 확인됨)
        if not (rel_info['src_is_pk'] or rel_info['dst_is_pk']):
            # 우선순위 2: 조인 컬럼이 둘 다 PK가 아닌 경우 - 각 테이블의 다른 PK 존재 여부 확인
            src_other_pk = self._has_other_pk(src_table_clean, src_column)
            dst_other_pk = self._has_other_pk(dst_table_clean, dst_column)

            if src_other_pk and not dst_other_pk:
                # src 테이블에만 다른 PK 존재 → src는 N(many), dst는 1(one)
                rel_info['src_is_pk'] = False
                rel_info['dst_is_pk'] = True
            elif not src_other_pk and dst_other_pk:
                # dst 테이블에만 다른 PK 존재 → dst는 N(many), src는 1(one)
                rel_info['src_is_pk'] = True
                rel_info['dst_is_pk'] = False
            else:
                # 우선순위 3: 둘 다 다른 PK가 없거나 둘 다 있는 경우 - INFERRED 여부로 판단
                if src_is_inferred and not dst_is_inferred:
                    # src가 INFERRED → src는 1(one), dst는 N(many)
                    rel_info['src_is_pk'] = True
                    rel_info['dst_is_pk'] = False
                elif not src_is_inferred and dst_is_inferred:
                    # dst가 INFERRED → dst는 1(one), src는 N(many)
                    rel_info['src_is_pk'] = False
                    rel_info['dst_is_pk'] = True
                # 둘 다 INFERRED이거나 둘 다 실제 테이블이면 기본값 유지

        return {
            'is_pk_fk': (rel_info['src_is_pk'] and not rel_info['dst_is_pk']) or (not rel_info['src_is_pk'] and rel_info['dst_is_pk']),
            'src_nullable': rel_info['src_nullable'],
            'dst_nullable': rel_info['dst_nullable'],
            'src_is_pk': rel_info['src_is_pk'],
            'dst_is_pk': rel_info['dst_is_pk']
        }

    def _has_other_pk(self, table_name: str, exclude_column: str) -> bool:
        """테이블에 조인 컬럼이 아닌 다른 PK가 존재하는지 확인"""
        try:
            if not exclude_column:
                # 조인 컬럼 정보가 없으면 판단 불가
                return False
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
            return len(result) > 0 if result else False
        except Exception as e:
            app_logger.error(f"다른 PK 존재 여부 확인 실패: {table_name}, {str(e)}")
            return False

    def _is_pk_fk_relation(self, src_table: str, src_column: str, dst_table: str, dst_column: str) -> bool:
        """CSV에서 업로드된 PK 정보를 기반으로 PK-FK 관계인지 확인 (하위 호환성)"""
        rel_info = self._get_relationship_info(src_table, src_column, dst_table, dst_column)
        return rel_info['is_pk_fk']

    def _format_relationship_label(self, src_table: str, src_column: str, dst_table: str, dst_column: str) -> str:
        """
        관계 라벨 포맷팅 - Mermaid 호환성 고려
        동일 컬럼명: 컬럼명만 표시 (예: USER_ID)
        다른 컬럼명: 테이블.컬럼 형식으로 표시 (예: USERS.ID-USER_ROLES.USER_ID)
        """
        try:
            # HTML 태그 오인식 방지: <, > 문자를 &lt;, &gt;로 변환
            def escape_html_chars(text: str) -> str:
                return text.replace('<', '&lt;').replace('>', '&gt;')

            if not src_column or not dst_column:
                label = escape_html_chars("UNKNOWN")
                return f'"{label}"'

            # 복합키(결합키) 처리 - 콤마로 구분된 경우
            if ',' in src_column and ',' in dst_column:
                src_keys = [key.strip() for key in src_column.split(',')]
                dst_keys = [key.strip() for key in dst_column.split(',')]

                # 동일한 키로 조인되는 경우 하나만 표시
                if src_keys == dst_keys:
                    label = f"[{', '.join(src_keys)}]"
                else:
                    # 다른 경우 테이블.컬럼 형식으로 표시
                    src_part = ', '.join([f"{src_table}.{k}" for k in src_keys])
                    dst_part = ', '.join([f"{dst_table}.{k}" for k in dst_keys])
                    label = f"[{src_part}] = [{dst_part}]"
            else:
                # 단일 키 처리 - 라벨이 겹치지 않도록 짧게 유지
                if src_column == dst_column:
                    # 동일한 컬럼명은 컬럼명만 표시 (예: USER_ID)
                    label = src_column
                else:
                    # 다른 컬럼명은 컬럼명만 사용하여 양쪽을 표시 (예: ORDER_ID↔ORDER_REF)
                    label = f"{src_column}↔{dst_column}"

            # HTML 특수문자 이스케이프 처리
            label = escape_html_chars(label)

            # ERD 안정성을 위해 모든 라벨을 따옴표로 감싸기
            return f'"{label}"'

        except Exception as e:
            handle_error(e, f"관계 라벨 포맷팅 실패: {src_column} -> {dst_column}")
    
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

    def _truncate_by_bytes(self, text: str, max_bytes: int) -> str:
        """
        UTF-8 기준 바이트 단위로 문자열을 자르는 유틸리티.
        - 멀티바이트 문자를 중간에서 자르지 않도록 안전하게 처리.
        """
        try:
            if not text or max_bytes <= 0:
                return ""
            encoded = text.encode("utf-8")
            if len(encoded) <= max_bytes:
                return text

            truncated = encoded[:max_bytes]
            # 잘못 잘린 멀티바이트 문자를 제거하면서 디코딩
            while truncated:
                try:
                    return truncated.decode("utf-8")
                except UnicodeDecodeError:
                    truncated = truncated[:-1]
            return ""
        except Exception as e:
            handle_error(e, f"바이트 기준 문자열 자르기 실패: {text}")
            # 실패 시에는 안전하게 앞쪽 일부만 잘라서 반환
            return text[:max_bytes]

    def _build_table_label_for_mermaid(
        self,
        table_name: str,
        table_comments_map: Dict[str, str],
        table_owner_map: Dict[str, str],
    ) -> str:
        """
        Mermaid ERD용 테이블 라벨 생성
        - 테이블명: 30바이트 이내
        - 테이블 코멘트: 30바이트 이내, 괄호() 안에 표시
        - INFERRED([I]) 테이블은 코멘트 미표시 (추론 금지 원칙 준수)
        """
        try:
            if not table_name:
                return ""

            prefix_inferred = table_name.startswith("[I]")
            raw_table_name = table_name[3:] if prefix_inferred else table_name

            clean_table_name = self._sanitize_identifier(raw_table_name)
            if not clean_table_name:
                return ""

            owner_name = (table_owner_map.get(raw_table_name) or "").strip()
            owner_name = "" if owner_name.upper() == "UNKNOWN" else owner_name
            owner_clean = self._truncate_by_bytes(self._sanitize_identifier(owner_name), 30) if owner_name else ""

            short_name = self._truncate_by_bytes(clean_table_name, 30)
            display_name = f"{owner_clean}.{short_name}" if owner_clean else short_name

            # [I] 테이블은 테이블 코멘트 표시하지 않음 (메타DB에 명시된 경우만 사용)
            comment = ""
            if not prefix_inferred:
                comment = table_comments_map.get(raw_table_name, "") or ""
                if comment:
                    comment = self._truncate_by_bytes(str(comment), 30)

            if comment:
                label_core = f"{display_name}({comment})"
            else:
                label_core = display_name

            return f"[I]{label_core}" if prefix_inferred else label_core
        except Exception as e:
            handle_error(e, f"Mermaid 테이블 라벨 생성 실패: {table_name}")
            return self._sanitize_identifier(table_name or "")

    def _resolve_table_label_for_mermaid(
        self,
        table_name: str,
        table_label_map: Dict[str, str],
    ) -> Optional[str]:
        """
        관계 정의 시 동일한 라벨을 사용하기 위한 헬퍼.
        - 테이블명은 원본/[I] 접두어 여부에 따라 다양하므로 안전하게 매핑.
        """
        if not table_name:
            return None

        if table_name in table_label_map:
            return table_label_map[table_name]

        try:
            if table_name.startswith('[I]'):
                bare = table_name[3:]
                return table_label_map.get(table_name) or table_label_map.get(bare)
            else:
                inferred_key = f"[I]{table_name}"
                return table_label_map.get(table_name) or table_label_map.get(inferred_key)
        except Exception as e:
            handle_error(e, f"Mermaid 테이블 라벨 매핑 실패: {table_name}")
            return None

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
    
    def _generate_html(self, stats: Dict[str, int], erd_data: Dict[str, Any]) -> str:
        """HTML 생성"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # HTML 템플릿 생성
            html_content = self.templates.get_erd_template(
                project_name=self.project_name,
                timestamp=timestamp,
                stats=stats,
                erd_data=erd_data
            )
            
            app_logger.debug("ERD HTML 생성 완료")
            return html_content
            
        except Exception as e:
            handle_error(e, "ERD HTML 생성 실패")
            return ""
    
    def _save_report(self, html_content: str) -> str:
        """리포트 파일 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"[{self.project_name}]_ERD_{timestamp}.html"
            output_path = self.path_utils.join_path(self.output_dir, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            app_logger.debug(f"ERD 리포트 파일 저장 완료: {output_path}")
            return output_path
            
        except Exception as e:
            handle_error(e, "ERD 리포트 파일 저장 실패")
            return ""
    


if __name__ == '__main__':
    import sys
    from util.arg_utils import ArgUtils
    
    # 명령행 인자 파싱
    arg_utils = ArgUtils()
    parser = arg_utils.create_parser("ERD Report 생성기")
    parser.add_argument('--include-orphan', action='store_true', 
                       help='고아 테이블(관계가 없는 테이블)도 ERD에 포함')
    args = parser.parse_args()
    
    project_name = args.project_name
    include_orphan = args.include_orphan
    print(f"ERD Report 생성 시작: {project_name} (고아 테이블 포함: {include_orphan})")
    
    generator = ERDReportGenerator(project_name, './temp', include_orphan)
    result = generator.generate_report()
    
    if result:
        print(f"ERD Report 생성 완료: {project_name}")
    else:
        print(f"ERD Report 생성 실패: {project_name}")
