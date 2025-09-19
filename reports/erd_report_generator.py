"""
ERD Report 생성기
- 테이블과 컬럼 정보를 활용한 Mermaid ERD 생성
- 테이블 간 관계 시각화
- 오프라인 환경 지원 (Mermaid.js 로컬화)
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
from util.report_utils import ReportUtils
from reports.report_templates import ReportTemplates
from reports.erd_metadata_service import ERDMetadataService


class ERDReportGenerator:
    """ERD Report 생성기 클래스"""
    
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
            # 공용 서비스에서 테이블과 컬럼 정보 조회
            tables_data = self.metadata_service.get_tables_with_columns()
            
            # 공용 서비스에서 관계 정보 조회
            relationships = self.metadata_service.get_relationships()
            
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
            mermaid_lines = ["erDiagram"]
            
            # 테이블 정의
            for table_name, columns in tables_data.items():
                # 테이블명 정리 (Mermaid 호환) - 특수문자 제거
                clean_table_name = table_name.replace(' ', '_').replace('-', '_').replace('<', '').replace('>', '').replace('{', '').replace('}', '').replace('[', '').replace(']', '').replace('(', '').replace(')', '')
                mermaid_lines.append(f"    {clean_table_name} {{")
                
                for column in columns:
                    # 데이터 타입 정규화
                    normalized_type = self._normalize_data_type(column['data_type'])
                    
                    # 컬럼명 정리 (특수문자 제거)
                    clean_column_name = column['column_name'].replace('<', '').replace('>', '').replace('{', '').replace('}', '').replace('[', '').replace(']', '').replace('(', '').replace(')', '')
                    
                    # 컬럼 정의 (PK 표시 포함)
                    column_def = f"        {normalized_type} {clean_column_name}"
                    
                    # Primary Key 표시 (Mermaid ERD 문법에 맞게)
                    if column['is_primary_key']:
                        column_def += " PK"
                    
                    # NULL 허용 여부 표시
                    if not column['is_nullable']:
                        column_def += " \"NOT NULL\""
                    
                    mermaid_lines.append(column_def)
                
                mermaid_lines.append("    }")
            
            # 관계 정의 (중복 제거 및 수 제한)
            seen_relationships = set()
            relationship_count = 0
            max_relationships = 50  # Mermaid ERD 렌더링 한계 고려
            
            for rel in relationships:
                if relationship_count >= max_relationships:
                    break
                    
                src_table = rel['src_table'].replace(' ', '_').replace('-', '_').replace('<', '').replace('>', '').replace('{', '').replace('}', '').replace('[', '').replace(']', '').replace('(', '').replace(')', '')
                dst_table = rel['dst_table'].replace(' ', '_').replace('-', '_').replace('<', '').replace('>', '').replace('{', '').replace('}', '').replace('[', '').replace(']', '').replace('(', '').replace(')', '')
                rel_type = rel['rel_type']
                
                # 중복 관계 제거 (방향성 고려하여 중복 제거)
                rel_key = f"{src_table}-{dst_table}"
                reverse_key = f"{dst_table}-{src_table}"
                if rel_key in seen_relationships or reverse_key in seen_relationships:
                    continue
                seen_relationships.add(rel_key)
                
                # 관계 유형별 Mermaid 문법 적용
                # 동일한 키로 조인되는 경우 중복 표시 제거
                relationship_label = self._format_relationship_label(rel['src_column'], rel['dst_column'])
                
                # 관계 정보 확인 (PK-FK 여부, nullable 여부)
                rel_info = self._get_relationship_info(rel['src_table'], rel['src_column'], rel['dst_table'], rel['dst_column'])
                is_pk_fk_relation = rel_info['is_pk_fk']
                src_nullable = rel_info['src_nullable']
                dst_nullable = rel_info['dst_nullable']
                
                # 관계 불명확한 경우 필터링 (PK-FK 관계가 아니고 신뢰도가 낮은 경우)
                if not is_pk_fk_relation and rel.get('confidence', 0.8) < 0.7:
                    app_logger.debug(f"Mermaid ERD에서 관계 불명확하여 제외: {rel['src_table']}.{rel['src_column']} -> {rel['dst_table']}.{rel['dst_column']} (신뢰도: {rel.get('confidence', 0.8)})")
                    continue
                
                # ERD는 단순 문법만 지원: A ||--o{ B : has 형태만 사용
                # PK-FK 관계든 JOIN 관계든 동일한 문법 사용
                mermaid_lines.append(f"    {src_table} ||--o{{ {dst_table} : {relationship_label}")
                
                relationship_count += 1
            
            mermaid_code = '\n'.join(mermaid_lines)
            app_logger.debug("Mermaid ERD 코드 생성 완료")
            return mermaid_code
            
        except Exception as e:
            handle_error(e, "Mermaid ERD 코드 생성 실패")
            return ""
    
    def _get_relationship_info(self, src_table: str, src_column: str, dst_table: str, dst_column: str) -> dict:
        """관계 정보 확인 - 공용 서비스 사용"""
        rel_info = self.metadata_service.get_relationship_info(src_table, src_column, dst_table, dst_column)
        return {
            'is_pk_fk': (rel_info['src_is_pk'] and not rel_info['dst_is_pk']) or (not rel_info['src_is_pk'] and rel_info['dst_is_pk']),
            'src_nullable': rel_info['src_nullable'],
            'dst_nullable': rel_info['dst_nullable']
        }

    def _is_pk_fk_relation(self, src_table: str, src_column: str, dst_table: str, dst_column: str) -> bool:
        """CSV에서 업로드된 PK 정보를 기반으로 PK-FK 관계인지 확인 (하위 호환성)"""
        rel_info = self._get_relationship_info(src_table, src_column, dst_table, dst_column)
        return rel_info['is_pk_fk']

    def _format_relationship_label(self, src_column: str, dst_column: str) -> str:
        """관계 라벨 포맷팅 - Mermaid 호환성 고려"""
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
                    # 다른 경우 하이픈으로 연결
                    label = f"[{', '.join(src_keys)}]-[{', '.join(dst_keys)}]"
            else:
                # 단일 키 처리
                if src_column == dst_column:
                    label = src_column
                else:
                    # 다른 경우 하이픈으로 연결
                    label = f"{src_column}-{dst_column}"
            
            # HTML 특수문자 이스케이프 처리
            label = escape_html_chars(label)
            
            # ERD 안정성을 위해 모든 라벨을 따옴표로 감싸기
            return f'"{label}"'
                
        except Exception as e:
            handle_error(e, f"관계 라벨 포맷팅 실패: {src_column} -> {dst_column}")
    
    def _normalize_data_type(self, data_type: str) -> str:
        """데이터 타입 정규화 (길이 정보 보존)"""
        try:
            if not data_type:
                return "string"
            
            data_type_upper = data_type.upper()
            
            # VARCHAR, CHAR, TEXT 등 문자열 타입
            if data_type_upper.startswith(('VARCHAR', 'CHAR', 'TEXT')):
                return data_type  # 길이 정보 보존
            
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
    args = parser.parse_args()
    
    project_name = args.project_name
    print(f"ERD Report 생성 시작: {project_name}")
    
    generator = ERDReportGenerator(project_name, './temp')
    result = generator.generate_report()
    
    if result:
        print(f"ERD Report 생성 완료: {project_name}")
    else:
        print(f"ERD Report 생성 실패: {project_name}")
