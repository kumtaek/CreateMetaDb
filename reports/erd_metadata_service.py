"""
ERD 메타데이터 조회 서비스
- ERD 리포트 생성에 필요한 공통 메타데이터 조회 기능 제공
- ERDReportGenerator와 ERDDagreReportGenerator에서 공용으로 사용
"""

from typing import List, Dict, Any, Tuple
from util.logger import app_logger, handle_error
from util.database_utils import DatabaseUtils


class ERDMetadataService:
    """ERD 메타데이터 조회 서비스 클래스"""
    
    def __init__(self, db_utils: DatabaseUtils, project_name: str):
        """
        초기화
        
        Args:
            db_utils: 데이터베이스 유틸리티 인스턴스
            project_name: 프로젝트명
        """
        self.db_utils = db_utils
        self.project_name = project_name
    
    def get_statistics(self) -> Dict[str, int]:
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
                WHERE p.project_name = ? 
                  AND c.position_pk IS NOT NULL 
                  AND c.del_yn = 'N' 
                  AND t.del_yn = 'N'
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['primary_keys'] = result[0]['count'] if result else 0
            
            # 관계 수 (JOIN 관계만)
            query = """
                SELECT COUNT(*) as count
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                JOIN projects p ON src.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND r.rel_type IN ('JOIN_EXPLICIT', 'JOIN_IMPLICIT')
                  AND r.del_yn = 'N'
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['relationships'] = result[0]['count'] if result else 0
            
            app_logger.debug(f"ERD 통계 정보 조회 완료: {stats}")
            return stats
            
        except Exception as e:
            handle_error(e, "ERD 통계 정보 조회 실패")
            return {}
    
    def get_tables_with_columns(self) -> Dict[str, List[Dict[str, Any]]]:
        """테이블과 컬럼 정보 조회 (기본 ERD용)"""
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
                    c.data_length,
                    c.data_default,
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
                    'column_comments': row['column_comments'],
                    'data_length': row['data_length'],
                    'data_default': row['data_default']
                })
            
            app_logger.debug(f"테이블 및 컬럼 정보 조회 완료: {len(tables_data)}개 테이블")
            return tables_data
            
        except Exception as e:
            handle_error(e, "테이블 및 컬럼 정보 조회 실패")
            return {}
    
    def get_tables_with_columns_detailed(self) -> Dict[str, Dict[str, Any]]:
        """테이블과 컬럼 정보 조회 (Dagre ERD용 - 상세 정보 포함)"""
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
            
            # 테이블별로 데이터 그룹화 (Dagre용 구조)
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
            
            app_logger.debug(f"상세 테이블 데이터 조회 완료: {len(tables_data)}개 테이블")
            return tables_data
            
        except Exception as e:
            handle_error(e, "상세 테이블 데이터 조회 실패")
            return {}
    
    def get_relationships(self) -> List[Dict[str, Any]]:
        """관계 정보 조회 - 메타데이터에서 분석된 JOIN 관계 직접 활용"""
        try:
            # 메타데이터에서 이미 분석된 테이블 간 JOIN 관계를 직접 조회
            query = """
                SELECT DISTINCT
                    r.rel_type,
                    src_table.table_name as src_table,
                    dst_table.table_name as dst_table
                FROM relationships r
                JOIN components src_sql ON r.src_id = src_sql.component_id
                JOIN components dst_table_comp ON r.dst_id = dst_table_comp.component_id
                JOIN tables dst_table ON dst_table_comp.component_id = dst_table.component_id
                JOIN relationships r2 ON src_sql.component_id = r2.src_id
                JOIN components src_table_comp ON r2.dst_id = src_table_comp.component_id
                JOIN tables src_table ON src_table_comp.component_id = src_table.component_id
                JOIN projects p ON src_sql.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND r.rel_type IN ('JOIN_EXPLICIT', 'JOIN_IMPLICIT')
                  AND r2.rel_type = 'USE_TABLE'
                  AND r.del_yn = 'N'
                  AND r2.del_yn = 'N'
                  AND src_sql.del_yn = 'N'
                  AND dst_table_comp.del_yn = 'N'
                  AND src_table_comp.del_yn = 'N'
                  AND src_table.del_yn = 'N'
                  AND dst_table.del_yn = 'N'
                ORDER BY src_table.table_name, dst_table.table_name
            """
            
            results = self.db_utils.execute_query(query, (self.project_name,))
            
            relationships = []
            for row in results:
                # 메타데이터 기반으로 컬럼 정보 추출
                src_column, dst_column = self.get_join_columns_from_metadata(
                    row['src_table'], 
                    row['dst_table']
                )
                
                # 컬럼 정보가 없어도 관계는 유지 (테이블 레벨 관계)
                relationships.append({
                    'rel_type': row['rel_type'],
                    'src_table': row['src_table'],
                    'dst_table': row['dst_table'],
                    'src_column': src_column or 'id',  # 기본값 제공
                    'dst_column': dst_column or 'id'   # 기본값 제공
                })
            
            app_logger.info(f"메타데이터 기반 관계 정보 조회 완료: {len(relationships)}개")
            return relationships
            
        except Exception as e:
            handle_error(e, "관계 정보 조회 실패")
            return []
    
    def get_join_columns_from_metadata(self, src_table: str, dst_table: str) -> Tuple[str, str]:
        """메타데이터에서 실제 JOIN 조건을 기반으로 컬럼 정보 추출"""
        try:
            # 1. 동일한 컬럼명을 가진 컬럼들 중에서 PK 우선 매칭
            query = """
                SELECT 
                    src_col.column_name as src_column,
                    dst_col.column_name as dst_column,
                    CASE 
                        WHEN src_col.position_pk IS NOT NULL THEN 3
                        WHEN dst_col.position_pk IS NOT NULL THEN 2
                        ELSE 1
                    END as priority
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
                ORDER BY priority DESC, src_col.column_name
                LIMIT 1
            """
            
            result = self.db_utils.execute_query(query, (dst_table.upper(), src_table.upper(), self.project_name))
            
            if result:
                return result[0]['src_column'], result[0]['dst_column']
            
            # 2. 매칭되는 컬럼이 없으면 각 테이블의 첫 번째 컬럼 반환
            src_col_query = """
                SELECT column_name 
                FROM columns c
                JOIN tables t ON c.table_id = t.table_id
                JOIN projects p ON t.project_id = p.project_id
                WHERE t.table_name = ? AND p.project_name = ?
                  AND t.del_yn = 'N' AND c.del_yn = 'N'
                ORDER BY c.column_id
                LIMIT 1
            """
            
            src_result = self.db_utils.execute_query(src_col_query, (src_table.upper(), self.project_name))
            dst_result = self.db_utils.execute_query(src_col_query, (dst_table.upper(), self.project_name))
            
            src_column = src_result[0]['column_name'] if src_result else src_table.lower() + '_id'
            dst_column = dst_result[0]['column_name'] if dst_result else dst_table.lower() + '_id'
            
            app_logger.debug(f"JOIN 컬럼 추출: {src_table}.{src_column} -> {dst_table}.{dst_column}")
            return src_column, dst_column
            
        except Exception as e:
            app_logger.error(f"메타데이터 기반 JOIN 컬럼 추출 중 오류: {str(e)}")
            # 오류 시 기본값 반환
            return src_table.lower() + '_id', dst_table.lower() + '_id'
    
    def get_relationship_info(self, src_table: str, src_column: str, dst_table: str, dst_column: str) -> Dict[str, Any]:
        """관계 정보 상세 조회 (PK-FK 여부, nullable 여부 등)"""
        try:
            # 소스 컬럼과 대상 컬럼의 PK 여부와 nullable 여부 확인
            query = """
                SELECT 
                    src_col.position_pk as src_is_pk,
                    src_col.nullable as src_nullable,
                    dst_col.position_pk as dst_is_pk,
                    dst_col.nullable as dst_nullable,
                    src_col.data_type as src_data_type,
                    dst_col.data_type as dst_data_type
                FROM tables src_t
                JOIN columns src_col ON src_t.table_id = src_col.table_id
                JOIN tables dst_t ON dst_t.table_name = ?
                JOIN columns dst_col ON dst_t.table_id = dst_col.table_id
                JOIN projects p ON src_t.project_id = p.project_id
                WHERE src_t.table_name = ? 
                  AND p.project_name = ?
                  AND src_col.column_name = ?
                  AND dst_col.column_name = ?
                  AND src_t.del_yn = 'N' 
                  AND dst_t.del_yn = 'N'
                  AND src_col.del_yn = 'N'
                  AND dst_col.del_yn = 'N'
            """
            
            result = self.db_utils.execute_query(query, (
                dst_table.upper(), src_table.upper(), self.project_name, 
                src_column.upper(), dst_column.upper()
            ))
            
            if result:
                row = result[0]
                return {
                    'src_is_pk': bool(row['src_is_pk']),
                    'src_nullable': row['src_nullable'] == 'Y',
                    'dst_is_pk': bool(row['dst_is_pk']),
                    'dst_nullable': row['dst_nullable'] == 'Y',
                    'src_data_type': row['src_data_type'],
                    'dst_data_type': row['dst_data_type']
                }
            else:
                # 기본값 반환
                return {
                    'src_is_pk': False,
                    'src_nullable': True,
                    'dst_is_pk': False,
                    'dst_nullable': True,
                    'src_data_type': 'VARCHAR',
                    'dst_data_type': 'VARCHAR'
                }
                
        except Exception as e:
            app_logger.error(f"관계 정보 상세 조회 실패: {str(e)}")
            return {
                'src_is_pk': False,
                'src_nullable': True,
                'dst_is_pk': False,
                'dst_nullable': True,
                'src_data_type': 'VARCHAR',
                'dst_data_type': 'VARCHAR'
            }
