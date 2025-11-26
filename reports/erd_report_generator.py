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
                # 관계가 없거나 관계 기반 테이블 조회가 비어 있으면 전체 테이블로 대체
                app_logger.warning("관계 데이터가 없거나 테이블 조회 결과가 비어 전체 테이블로 ERD를 생성합니다.")
                tables_data = self.metadata_service.get_all_tables_with_columns()
                relationships = relationships or []
            
            if not tables_data:
                app_logger.error("ERD를 생성할 테이블 데이터가 없습니다.")
                raise Exception("ERD 생성 실패: 테이블 데이터 없음")
            
            # Mermaid ERD 코드 생성
            mermaid_code = self._generate_mermaid_erd(tables_data, relationships)
            
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
    
    
    def _generate_mermaid_erd(self, tables_data: Dict[str, List[Dict[str, Any]]], relationships: List[Dict[str, Any]]) -> str:
        """Mermaid ERD 코드 생성"""
        try:
            # === 디버깅 코드 추가 ===
            try:
                with open('temp/debug_tables_data.json', 'w', encoding='utf-8') as f:
                    json.dump(tables_data, f, ensure_ascii=False, indent=4)
            except Exception as debug_e:
                app_logger.error(f"디버깅 파일 저장 실패: {debug_e}")
            # === 디버깅 코드 추가 끝 ===

            mermaid_lines = ["erDiagram"]
            
            # 테이블 정의
            for table_name, columns in tables_data.items():
                # 테이블명 정리 (Mermaid 호환)
                prefix_inferred = table_name.startswith("[I]")
                raw_table_name = table_name[3:] if prefix_inferred else table_name
                clean_table_name = self._sanitize_identifier(raw_table_name)
                if not clean_table_name:
                    app_logger.warning(f"Mermaid ERD에서 테이블명을 정규화할 수 없어 제외: {table_name}")
                    continue
                label_table_name = f"[I]{clean_table_name}" if prefix_inferred else clean_table_name
                mermaid_lines.append(f'    "{label_table_name}" {{')
                
                for column in columns:
                    is_inferred = column.get('is_inferred')
                    col_name_for_id = column['column_name']
                    if is_inferred and col_name_for_id.startswith('[I]'):
                        # 식별자는 안전하게 정규화
                        col_name_for_id = self._sanitize_identifier(col_name_for_id.replace('[', '').replace(']', ''))
                    if not is_inferred and not self._is_valid_identifier(col_name_for_id):
                        app_logger.warning(f"Mermaid ERD에서 허용되지 않는 컬럼명으로 제외: {table_name}.{column['column_name']}")
                        continue
                    # 데이터 타입 정규화
                    normalized_type = self._normalize_data_type(column['data_type'])
                    mermaid_type = self._sanitize_identifier(normalized_type)
                    
                    # 컬럼명 정리 (Mermaid 호환)
                    clean_column_name = self._sanitize_identifier(col_name_for_id)
                    if not clean_column_name:
                        app_logger.warning(f"Mermaid ERD에서 컬럼명을 정규화할 수 없어 제외: {column['column_name']}")
                        continue
                    
                    # 컬럼 정의 (PK 표시 포함)
                    column_def = f"        {mermaid_type or 'string'} {clean_column_name}"
                    
                    # Primary Key 표시 (Mermaid ERD 문법에 맞게)
                    if column['is_primary_key']:
                        column_def += " PK"
                    
                    # 컬럼 주석/제약을 하나의 어노테이션으로 묶어 Mermaid 파서 오류 방지
                    annotations: List[str] = []
                    if column.get('is_inferred'):
                        inferred_from = column.get('inferred_from') or column['column_name']
                        annotations.append(f"[I]{self._escape_mermaid_text(str(inferred_from))}")
                    if not column['is_nullable']:
                        annotations.append("NOT NULL")
                    if clean_column_name != column['column_name']:
                        annotations.append(self._escape_mermaid_text(column['column_name']))
                    if column.get('column_comments'):
                        annotations.append(self._escape_mermaid_text(column['column_comments']))
                    if column.get('data_default'):
                        annotations.append(self._escape_mermaid_text(str(column['data_default'])))
                    if annotations:
                        column_def += f' "{" | ".join(annotations)}"'
                    
                    mermaid_lines.append(column_def)
                
                mermaid_lines.append("    }")
                mermaid_lines.append("") # 테이블 정의 블록 사이에 빈 줄 추가
            
            # 관계 정의 (중복 제거 및 수 제한)
            seen_relationships = set()
            relationship_count = 0
            max_relationships = 50  # Mermaid ERD 렌더링 한계 고려
            
            for rel in relationships:
                if relationship_count >= max_relationships:
                    break
                    
                # Validate identifiers (allowing [I] prefix)
                if not (self._is_valid_identifier(rel['src_table']) and self._is_valid_identifier(rel['dst_table'])):
                    continue
                if not (self._is_valid_identifier(rel['src_column']) and self._is_valid_identifier(rel['dst_column'])):
                    continue

                # Preserve [I] prefix for inferred tables while sanitizing the raw name
                raw_src_table = rel['src_table']
                raw_dst_table = rel['dst_table']
                src_prefix = raw_src_table.startswith('[I]')
                dst_prefix = raw_dst_table.startswith('[I]')
                clean_src = raw_src_table[3:] if src_prefix else raw_src_table
                clean_dst = raw_dst_table[3:] if dst_prefix else raw_dst_table
                sanitized_src = self._sanitize_identifier(clean_src)
                sanitized_dst = self._sanitize_identifier(clean_dst)
                src_table = f"[I]{sanitized_src}" if src_prefix else sanitized_src
                dst_table = f"[I]{sanitized_dst}" if dst_prefix else sanitized_dst
                rel_type = rel['rel_type']
                
                # 중복 관계 제거 (방향성 고려하여 중복 제거)
                rel_key = f"{src_table}-{dst_table}"
                reverse_key = f"{dst_table}-{src_table}"
                if rel_key in seen_relationships or reverse_key in seen_relationships:
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
                    app_logger.debug(f"Mermaid ERD에서 관계 불명확하여 제외: {rel['src_table']}.{rel['src_column']} -> {rel['dst_table']}.{rel['dst_column']} (신뢰도: {rel.get('confidence', 0.8)})")
                    continue
                
                # ERD 관계 방향 결정: PK가 있는 쪽이 1(왼쪽), FK가 있는 쪽이 N(오른쪽)
                # Mermaid 문법: A ||--o{ B 는 A(1) : B(N) 관계를 의미
                if rel_info['src_is_pk'] and not rel_info['dst_is_pk']:
                    # src가 PK, dst가 FK → src(1) : dst(N)
                    one_side = src_table
                    many_side = dst_table
                elif not rel_info['src_is_pk'] and rel_info['dst_is_pk']:
                    # src가 FK, dst가 PK → dst(1) : src(N)
                    one_side = dst_table
                    many_side = src_table
                else:
                    # PK-FK 관계가 명확하지 않은 경우, 기본적으로 src → dst 방향 사용
                    one_side = src_table
                    many_side = dst_table

                # ERD는 단순 문법만 지원: A ||--o{ B : has 형태만 사용
                mermaid_lines.append(f'    "{one_side}" ||--o{{ "{many_side}" : {relationship_label}')

                relationship_count += 1
            
            mermaid_code = '\n'.join(mermaid_lines)
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
                # 단일 키 처리
                if src_column == dst_column:
                    # 동일한 컬럼명은 컬럼명만 표시
                    label = src_column
                else:
                    # 다른 컬럼명은 테이블.컬럼 형식으로 표시
                    label = f"{src_table}.{src_column} = {dst_table}.{dst_column}"

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
