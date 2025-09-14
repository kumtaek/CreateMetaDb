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
from reports.report_templates import ReportTemplates


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
        
        # 메타데이터베이스 연결
        self.metadata_db_path = self.path_utils.get_project_metadata_db_path(project_name)
        self.db_utils = DatabaseUtils(self.metadata_db_path)
        
        if not self.db_utils.connect():
            handle_error(Exception("데이터베이스 연결 실패"), f"메타데이터베이스 연결 실패: {self.metadata_db_path}")
    
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
            
            # 4. 파일 저장
            output_file = self._save_report(html_content)
            
            app_logger.info(f"ERD Report 생성 완료: {output_file}")
            return True
            
        except Exception as e:
            handle_error(e, "ERD Report 생성 실패")
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
            
            app_logger.debug(f"ERD 통계 정보 조회 완료: {stats}")
            return stats
            
        except Exception as e:
            handle_error(e, "ERD 통계 정보 조회 실패")
            return {}
    
    def _get_erd_data(self) -> Dict[str, Any]:
        """ERD 데이터 조회 (N+1 쿼리 문제 해결)"""
        try:
            # 단일 쿼리로 모든 테이블과 컬럼 정보 조회
            query = """
                SELECT 
                    t.table_name,
                    c.column_name,
                    c.data_type,
                    c.position_pk,
                    c.nullable,
                    c.column_id
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
                    tables_data[table_name] = []
                
                tables_data[table_name].append({
                    'column_name': row['column_name'],
                    'data_type': row['data_type'],
                    'is_primary_key': bool(row['position_pk']),
                    'is_nullable': row['nullable'] == 'Y',
                    'column_order': row['column_id']
                })
            
            # 관계 정보 조회
            relationships = self._get_relationships()
            
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
    
    def _get_relationships(self) -> List[Dict[str, Any]]:
        """관계 정보 조회"""
        try:
            query = """
                SELECT 
                    r.rel_type,
                    src_table.table_name as src_table,
                    dst_table.table_name as dst_table,
                    src_col.column_name as src_column,
                    dst_col.column_name as dst_column
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
                ORDER BY src_table.table_name, dst_table.table_name
            """
            
            results = self.db_utils.execute_query(query, (self.project_name,))
            
            relationships = []
            for row in results:
                relationships.append({
                    'rel_type': row['rel_type'],
                    'src_table': row['src_table'],
                    'dst_table': row['dst_table'],
                    'src_column': row['src_column'],
                    'dst_column': row['dst_column']
                })
            
            app_logger.debug(f"관계 정보 조회 완료: {len(relationships)}개")
            return relationships
            
        except Exception as e:
            app_logger.warning(f"관계 정보 조회 실패: {str(e)}")
            return []
    
    def _generate_mermaid_erd(self, tables_data: Dict[str, List[Dict[str, Any]]], relationships: List[Dict[str, Any]]) -> str:
        """Mermaid ERD 코드 생성"""
        try:
            mermaid_lines = ["erDiagram"]
            
            # 테이블 정의
            for table_name, columns in tables_data.items():
                # 테이블명 정리 (Mermaid 호환)
                clean_table_name = table_name.replace(' ', '_').replace('-', '_')
                mermaid_lines.append(f"    {clean_table_name} {{")
                
                for column in columns:
                    # 데이터 타입 정규화
                    normalized_type = self._normalize_data_type(column['data_type'])
                    
                    # 컬럼 정의
                    column_def = f"        {normalized_type} {column['column_name']}"
                    
                    # Primary Key 표시 (Mermaid 문법에 맞게)
                    if column['is_primary_key']:
                        column_def += " PK"
                    
                    # NULL 허용 여부 표시
                    if not column['is_nullable']:
                        column_def += " \"NOT NULL\""
                    
                    mermaid_lines.append(column_def)
                
                mermaid_lines.append("    }")
            
            # 관계 정의
            for rel in relationships:
                src_table = rel['src_table'].replace(' ', '_').replace('-', '_')
                dst_table = rel['dst_table'].replace(' ', '_').replace('-', '_')
                rel_type = rel['rel_type']
                
                # 관계 유형별 Mermaid 문법 적용
                if rel_type == 'FK':
                    # Foreign Key 관계 (실선)
                    mermaid_lines.append(f"    {src_table} ||--o{{ {dst_table} : \"{rel['src_column']} -> {rel['dst_column']}\"")
                elif rel_type.startswith('JOIN_'):
                    # JOIN 관계 (점선)
                    mermaid_lines.append(f"    {src_table} }}o--o{{ {dst_table} : \"{rel['src_column']} -> {rel['dst_column']}\"")
                else:
                    # 기타 관계 (기본)
                    mermaid_lines.append(f"    {src_table} ||--o{{ {dst_table} : \"{rel['src_column']} -> {rel['dst_column']}\"")
            
            mermaid_code = '\n'.join(mermaid_lines)
            app_logger.debug("Mermaid ERD 코드 생성 완료")
            return mermaid_code
            
        except Exception as e:
            app_logger.warning(f"Mermaid ERD 코드 생성 실패: {str(e)}")
            return "erDiagram\n    EMPTY_TABLE {\n        string message\n    }"
    
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
            app_logger.warning(f"데이터 타입 정규화 실패: {data_type}, 오류: {str(e)}")
            return "string"
    
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
            filename = f"{self.project_name}_ERD_{timestamp}.html"
            output_path = os.path.join(self.output_dir, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            app_logger.info(f"ERD 리포트 파일 저장 완료: {output_path}")
            return output_path
            
        except Exception as e:
            handle_error(e, "ERD 리포트 파일 저장 실패")
            return ""


if __name__ == '__main__':
    # 테스트용 실행
    generator = ERDReportGenerator('sampleSrc', './temp')
    generator.generate_report()
