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
        """테이블과 컬럼 정보 조회 (기본 ERD용) - 관계가 있는 테이블만 포함"""
        try:
            # 1. 관계가 있는 테이블들만 조회
            tables_with_relationships = self._get_tables_with_relationships()
            
            # 2. 기본 테이블-컬럼 정보 조회 (관계가 있는 테이블만)
            if not tables_with_relationships:
                app_logger.warning("관계가 있는 테이블이 없습니다")
                return {}
            
            # IN 절을 위한 플레이스홀더 생성
            placeholders = ','.join(['?' for _ in tables_with_relationships])
            query = f"""
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
                  AND t.table_name IN ({placeholders})
                ORDER BY t.table_name, c.column_id
            """
            
            params = [self.project_name] + tables_with_relationships
            results = self.db_utils.execute_query(query, params)
            
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
            
            # 3. 컬럼이 없는 테이블들에 대해 조인 조건에서 컬럼 추가 (관계가 있는 테이블만)
            for table_name in tables_with_relationships:
                if table_name not in tables_data:
                    # 테이블은 존재하지만 컬럼이 없는 경우
                    tables_data[table_name] = []
                
                # 컬럼이 없는 경우 조인 관계에서 컬럼 추론 및 실제 DB에 저장
                if len(tables_data.get(table_name, [])) == 0:
                    join_columns = self._extract_columns_from_relationships(table_name)
                    if join_columns:
                        # 조인에서 사용된 컬럼들을 실제 COLUMNS 테이블에 저장
                        self._save_inferred_columns_to_database(table_name, join_columns)
                        
                        # 조인에서 사용된 컬럼들 추가 (추론된 컬럼)
                        for col_name in join_columns:
                            tables_data[table_name].append({
                                'column_name': col_name,
                                'data_type': 'VARCHAR2(50)',  # 기본 타입
                                'is_primary_key': col_name.upper().endswith('_ID') or col_name.upper() == 'ID',
                                'is_nullable': True,
                                'column_comments': f'조인에서 추론된 컬럼',
                                'data_length': 50,
                                'data_default': None
                            })
            
            app_logger.debug(f"관계가 있는 테이블 정보 조회 완료: {len(tables_data)}개 테이블 (고아 테이블 제외)")
            return tables_data
            
        except Exception as e:
            handle_error(e, "테이블 및 컬럼 정보 조회 실패")
            return {}

    def get_all_tables_with_columns(self) -> Dict[str, List[Dict[str, Any]]]:
        """모든 테이블과 컬럼 정보 조회 (고아 테이블 포함)"""
        try:
            query = """
                SELECT 
                    t.table_name,
                    t.table_owner,
                    t.table_comments,
                    c.column_name,
                    c.data_type,
                    c.data_length,
                    c.nullable,
                    c.column_comments,
                    CASE WHEN c.position_pk IS NOT NULL THEN 'Y' ELSE 'N' END as is_primary_key,
                    'N' as is_foreign_key,
                    c.data_default
                FROM tables t
                LEFT JOIN columns c ON t.table_id = c.table_id AND c.del_yn = 'N'
                JOIN projects p ON t.project_id = p.project_id
                WHERE p.project_name = ? AND t.del_yn = 'N'
                ORDER BY t.table_name, c.column_id
            """
            
            results = self.db_utils.execute_query(query, (self.project_name,))
            
            # 테이블별로 데이터 그룹화
            tables_data = {}
            for row in results:
                table_name = row['table_name']
                if table_name not in tables_data:
                    tables_data[table_name] = []
                
                # 컬럼이 있는 경우만 추가
                if row['column_name']:
                    tables_data[table_name].append({
                        'column_name': row['column_name'],
                        'data_type': row['data_type'],
                        'data_length': row['data_length'],
                        'is_nullable': row['nullable'] == 'Y',
                        'column_comments': row['column_comments'],
                        'is_primary_key': row['is_primary_key'] == 'Y',
                        'is_foreign_key': row['is_foreign_key'] == 'Y',
                        'data_default': row['data_default']
                    })
            
            # 컬럼이 없는 테이블들에 대해 조인 조건에서 컬럼 추가 (모든 테이블 대상)
            for table_name in tables_data.keys():
                if len(tables_data[table_name]) == 0:
                    join_columns = self._extract_columns_from_relationships(table_name)
                    if join_columns:
                        # 조인에서 사용된 컬럼들을 실제 COLUMNS 테이블에 저장
                        self._save_inferred_columns_to_database(table_name, join_columns)
                        
                        # 조인에서 사용된 컬럼들 추가 (추론된 컬럼)
                        for col_name in join_columns:
                            tables_data[table_name].append({
                                'column_name': col_name,
                                'data_type': 'VARCHAR2(50)',  # 기본 타입
                                'is_primary_key': col_name.upper().endswith('_ID') or col_name.upper() == 'ID',
                                'is_nullable': True,
                                'column_comments': f'조인에서 추론된 컬럼',
                                'data_length': 50,
                                'data_default': None
                            })
            
            app_logger.debug(f"모든 테이블 정보 조회 완료: {len(tables_data)}개 테이블 (고아 테이블 포함)")
            return tables_data
            
        except Exception as e:
            handle_error(e, "모든 테이블 및 컬럼 정보 조회 실패")
            return {}
    
    def _get_all_tables(self) -> List[str]:
        """모든 테이블 목록 조회 (CSV 등록 + 조인에서 추론된 테이블 모두 포함)"""
        try:
            query = """
                SELECT DISTINCT t.table_name
                FROM tables t
                JOIN projects p ON t.project_id = p.project_id
                WHERE p.project_name = ? AND t.del_yn = 'N'
                ORDER BY t.table_name
            """
            
            results = self.db_utils.execute_query(query, (self.project_name,))
            return [row['table_name'] for row in results]
            
        except Exception as e:
            app_logger.error(f"모든 테이블 목록 조회 실패: {str(e)}")
            return []
    
    def _get_tables_with_relationships(self) -> List[str]:
        """관계가 있는 테이블들만 조회 (고아 엔티티 제외)"""
        try:
            query = """
                SELECT DISTINCT
                    src.component_name as table_name
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                JOIN components dst ON r.dst_id = dst.component_id
                JOIN projects p ON src.project_id = p.project_id
                WHERE p.project_name = ?
                  AND r.rel_type IN ('JOIN_EXPLICIT', 'JOIN_IMPLICIT')
                  AND r.del_yn = 'N'
                  AND src.del_yn = 'N'
                  AND dst.del_yn = 'N'
                  AND src.component_type = 'TABLE'
                
                UNION
                
                SELECT DISTINCT
                    dst.component_name as table_name
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                JOIN components dst ON r.dst_id = dst.component_id
                JOIN projects p ON src.project_id = p.project_id
                WHERE p.project_name = ?
                  AND r.rel_type IN ('JOIN_EXPLICIT', 'JOIN_IMPLICIT')
                  AND r.del_yn = 'N'
                  AND src.del_yn = 'N'
                  AND dst.del_yn = 'N'
                  AND dst.component_type = 'TABLE'
                
                ORDER BY table_name
            """
            
            results = self.db_utils.execute_query(query, (self.project_name, self.project_name))
            table_names = [row['table_name'] for row in results]
            
            app_logger.debug(f"관계가 있는 테이블 조회 완료: {len(table_names)}개 테이블")
            return table_names
            
        except Exception as e:
            app_logger.error(f"관계가 있는 테이블 조회 실패: {str(e)}")
            return []
    
    def _get_empty_tables_with_relationships(self) -> Dict[str, set]:
        """빈 테이블들의 조인 조건에서 사용된 컬럼들 추출"""
        try:
            # 컬럼이 없는 테이블들 중에서 관계가 있는 테이블들 찾기
            query = """
                SELECT DISTINCT
                    t.table_name,
                    r.rel_type
                FROM tables t
                LEFT JOIN columns c ON t.table_id = c.table_id AND c.del_yn = 'N'
                JOIN components comp ON t.component_id = comp.component_id
                JOIN relationships r ON (comp.component_id = r.src_id OR comp.component_id = r.dst_id)
                JOIN projects p ON t.project_id = p.project_id
                WHERE p.project_name = ?
                  AND t.del_yn = 'N'
                  AND comp.del_yn = 'N'
                  AND r.del_yn = 'N'
                  AND r.rel_type IN ('JOIN_EXPLICIT', 'JOIN_IMPLICIT', 'USE_TABLE')
                GROUP BY t.table_name
                HAVING COUNT(c.column_id) = 0
            """
            
            results = self.db_utils.execute_query(query, (self.project_name,))
            
            empty_tables_with_joins = {}
            for row in results:
                table_name = row['table_name']
                
                # 이 테이블과 관련된 조인 조건에서 컬럼 추출
                join_columns = self._extract_columns_from_relationships(table_name)
                if join_columns:
                    empty_tables_with_joins[table_name] = join_columns
            
            return empty_tables_with_joins
            
        except Exception as e:
            app_logger.error(f"빈 테이블의 관계 컬럼 추출 실패: {str(e)}")
            return {}
    
    def _extract_columns_from_relationships(self, table_name: str) -> set:
        """특정 테이블의 관계에서 사용된 컬럼들 추출 (순환 참조 방지)"""
        try:
            columns = set()
            
            # 기본적으로 ID 컬럼 추가 (대부분의 테이블에 존재)
            if table_name.upper().endswith('S'):
                # 복수형 테이블명에서 단수형 ID 추출 (예: USERS -> USER_ID)
                singular = table_name[:-1]
                columns.add(f"{singular}_ID")
            else:
                columns.add(f"{table_name}_ID")
            
            # 일반적인 ID 컬럼도 추가
            columns.add("ID")
            
            # 조인 관계에서 직접 컬럼 정보 조회 (get_relationships 호출 방지)
            query = """
                SELECT DISTINCT
                    src.component_name as src_table,
                    dst.component_name as dst_table
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                JOIN components dst ON r.dst_id = dst.component_id
                JOIN projects p ON src.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND r.rel_type IN ('JOIN_EXPLICIT', 'JOIN_IMPLICIT')
                  AND r.del_yn = 'N'
                  AND src.del_yn = 'N'
                  AND dst.del_yn = 'N'
                  AND (src.component_name = ? OR dst.component_name = ?)
            """
            
            results = self.db_utils.execute_query(query, (self.project_name, table_name, table_name))
            
            # 관련된 테이블들로부터 FK 컬럼 추론
            for row in results:
                src_table = row['src_table']
                dst_table = row['dst_table']
                
                if src_table == table_name:
                    # 이 테이블이 소스인 경우, 대상 테이블의 ID를 FK로 추가
                    if dst_table.upper().endswith('S'):
                        singular = dst_table[:-1]
                        columns.add(f"{singular}_ID")
                    else:
                        columns.add(f"{dst_table}_ID")
                
                if dst_table == table_name:
                    # 이 테이블이 대상인 경우, 소스 테이블의 ID를 FK로 추가
                    if src_table.upper().endswith('S'):
                        singular = src_table[:-1]
                        columns.add(f"{singular}_ID")
                    else:
                        columns.add(f"{src_table}_ID")
            
            return columns
            
        except Exception as e:
            app_logger.error(f"테이블 {table_name}의 관계 컬럼 추출 실패: {str(e)}")
            return set()
    
    def get_tables_with_columns_detailed(self) -> Dict[str, Dict[str, Any]]:
        """테이블과 컬럼 정보 조회 (Dagre ERD용 - 관계가 있는 테이블만 포함)"""
        try:
            # 1. 관계가 있는 테이블들만 조회
            tables_with_relationships = self._get_tables_with_relationships()
            
            if not tables_with_relationships:
                app_logger.warning("관계가 있는 테이블이 없습니다")
                return {}
            
            # 2. 기본 테이블-컬럼 정보 조회 (관계가 있는 테이블만)
            placeholders = ','.join(['?' for _ in tables_with_relationships])
            query = f"""
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
                  AND t.table_name IN ({placeholders})
                ORDER BY t.table_name, c.column_id
            """
            
            params = [self.project_name] + tables_with_relationships
            results = self.db_utils.execute_query(query, params)
            
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
            
            # 3. 컬럼이 없는 테이블들에 대해 조인 조건에서 컬럼 추가 (관계가 있는 테이블만)
            for table_name in tables_with_relationships:
                if table_name not in tables_data:
                    # 테이블은 존재하지만 컬럼이 없는 경우
                    tables_data[table_name] = {
                        'table_owner': 'UNKNOWN',
                        'table_comments': f'{table_name} 테이블 (조인에서 추론)',
                        'columns': []
                    }
                
                # 컬럼이 없는 경우 조인 관계에서 컬럼 추론
                if len(tables_data[table_name]['columns']) == 0:
                    join_columns = self._extract_columns_from_relationships(table_name)
                    if join_columns:
                        # 조인에서 사용된 컬럼들 추가 (추론된 컬럼)
                        for col_name in join_columns:
                            tables_data[table_name]['columns'].append({
                                'column_name': col_name,
                                'data_type': 'VARCHAR2(50)',
                                'is_primary_key': col_name.upper().endswith('_ID') or col_name.upper() == 'ID',
                                'is_nullable': True,
                                'column_comments': '조인에서 추론된 컬럼',
                                'column_order': 1,
                                'data_length': 50,
                                'data_default': None
                            })
            
            app_logger.debug(f"관계가 있는 상세 테이블 데이터 조회 완료: {len(tables_data)}개 테이블 (고아 테이블 제외)")
            return tables_data
            
        except Exception as e:
            handle_error(e, "상세 테이블 데이터 조회 실패")
            return {}

    def get_all_tables_with_columns_detailed(self) -> Dict[str, Dict[str, Any]]:
        """모든 테이블과 컬럼 정보 조회 (Dagre ERD용 - 고아 테이블 포함)"""
        try:
            query = """
                SELECT 
                    t.table_name,
                    t.table_owner,
                    t.table_comments,
                    c.column_name,
                    c.data_type,
                    c.data_length,
                    c.nullable,
                    c.column_comments,
                    CASE WHEN c.position_pk IS NOT NULL THEN 'Y' ELSE 'N' END as is_primary_key,
                    'N' as is_foreign_key,
                    c.data_default
                FROM tables t
                LEFT JOIN columns c ON t.table_id = c.table_id AND c.del_yn = 'N'
                JOIN projects p ON t.project_id = p.project_id
                WHERE p.project_name = ? AND t.del_yn = 'N'
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
                
                # 컬럼이 있는 경우만 추가
                if row['column_name']:
                    tables_data[table_name]['columns'].append({
                        'column_name': row['column_name'],
                        'data_type': row['data_type'],
                        'data_length': row['data_length'],
                        'is_nullable': row['nullable'] == 'Y',
                        'column_comments': row['column_comments'],
                        'is_primary_key': row['is_primary_key'] == 'Y',
                        'is_foreign_key': row['is_foreign_key'] == 'Y',
                        'data_default': row['data_default']
                    })
            
            app_logger.debug(f"모든 상세 테이블 데이터 조회 완료: {len(tables_data)}개 테이블 (고아 테이블 포함)")
            return tables_data
            
        except Exception as e:
            handle_error(e, "모든 상세 테이블 데이터 조회 실패")
            return {}
    
    def get_relationships(self) -> List[Dict[str, Any]]:
        """관계 정보 조회 - 간단하고 직접적인 JOIN 관계 조회"""
        try:
            # 간단한 방법: 테이블 간 JOIN 관계를 직접 조회
            query = """
                SELECT DISTINCT
                    r.rel_type,
                    src.component_name as src_table,
                    dst.component_name as dst_table
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                JOIN components dst ON r.dst_id = dst.component_id
                JOIN projects p ON src.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND r.rel_type IN ('JOIN_EXPLICIT', 'JOIN_IMPLICIT')
                  AND r.del_yn = 'N'
                  AND src.del_yn = 'N'
                  AND dst.del_yn = 'N'
                  AND src.component_type = 'TABLE'
                  AND dst.component_type = 'TABLE'
                ORDER BY src.component_name, dst.component_name
            """
            
            results = self.db_utils.execute_query(query, (self.project_name,))
            
            relationships = []
            for row in results:
                # 메타데이터 기반으로 컬럼 정보 추출
                src_column, dst_column = self.get_join_columns_from_metadata(
                    row['src_table'], 
                    row['dst_table']
                )
                
                # 관계 정보 추가
                relationships.append({
                    'rel_type': row['rel_type'],
                    'src_table': row['src_table'],
                    'dst_table': row['dst_table'],
                    'src_column': src_column or 'id',  # 기본값 제공
                    'dst_column': dst_column or 'id',  # 기본값 제공
                    'confidence': 0.9,  # ERD Dagre용 기본 신뢰도
                    'frequency': 1,     # ERD Dagre용 기본 빈도
                    'src_owner': '',    # ERD Dagre용 기본값
                    'dst_owner': '',    # ERD Dagre용 기본값
                    'src_data_type': 'VARCHAR',  # ERD Dagre용 기본값
                    'dst_data_type': 'VARCHAR',  # ERD Dagre용 기본값
                    'join_condition': None,      # ERD Dagre용 기본값
                    'rel_comment': '',           # ERD Dagre용 기본값
                    'is_pk_fk': False            # ERD Dagre용 기본값 (나중에 계산)
                })
            
            app_logger.info(f"테이블 간 JOIN 관계 조회 완료: {len(relationships)}개")
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
    
    def _save_inferred_columns_to_database(self, table_name: str, join_columns: List[str]) -> None:
        """
        조인 관계에서 추론된 컬럼들을 실제 COLUMNS 테이블에 저장
        
        Args:
            table_name: 테이블명
            join_columns: 조인에서 사용된 컬럼명 리스트
        """
        try:
            # 프로젝트 ID 조회
            project_result = self.db_utils.execute_query(
                "SELECT project_id FROM projects WHERE project_name = ?",
                (self.project_name,)
            )
            
            if not project_result:
                app_logger.warning(f"프로젝트를 찾을 수 없습니다: {self.project_name}")
                return
            
            project_id = project_result[0]['project_id']
            
            # 테이블 ID 조회
            table_result = self.db_utils.execute_query(
                "SELECT table_id FROM tables WHERE project_id = ? AND table_name = ? AND del_yn = 'N'",
                (project_id, table_name)
            )
            
            if not table_result:
                app_logger.warning(f"테이블을 찾을 수 없습니다: {table_name}")
                return
            
            table_id = table_result[0]['table_id']
            
            # 각 컬럼에 대해 COLUMNS 테이블에 저장
            for col_name in join_columns:
                # 이미 존재하는 컬럼인지 확인
                existing_result = self.db_utils.execute_query(
                    "SELECT column_id FROM columns WHERE table_id = ? AND column_name = ? AND del_yn = 'N'",
                    (table_id, col_name.upper())
                )
                
                if existing_result:
                    # 이미 존재하는 컬럼은 건너뛰기
                    continue
                
                # inferred 컬럼 데이터 생성
                column_data = {
                    'table_id': table_id,
                    'column_name': col_name.upper(),
                    'data_type': 'VARCHAR2(50)',
                    'data_length': 50,
                    'nullable': 'Y',
                    'column_comments': 'Inferred from JOIN analysis',
                    'position_pk': 1 if col_name.upper().endswith('_ID') or col_name.upper() == 'ID' else None,
                    'data_default': None,
                    'owner': 'UNKNOWN',
                    'has_error': 'N',
                    'error_message': None,
                    'hash_value': 'INFERRED',
                    'del_yn': 'N'
                }
                
                # COLUMNS 테이블에 삽입
                self.db_utils.insert_or_replace('columns', column_data)
                app_logger.debug(f"inferred 컬럼 저장 완료: {table_name}.{col_name}")
                
        except Exception as e:
            app_logger.error(f"inferred 컬럼 저장 실패: {table_name}, {str(e)}")
