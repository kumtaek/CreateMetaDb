"""
ERD 메타데이터 조회 서비스
- ERD 리포트 생성에 필요한 공통 메타데이터 조회 기능 제공
- ERDReportGenerator와 ERDDagreReportGenerator에서 공용으로 사용
"""

import os
from typing import List, Dict, Any, Tuple
from util.logger import app_logger, handle_error
from util.database_utils import DatabaseUtils
from util.path_utils import PathUtils


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
        self.path_utils = PathUtils()
        self.erd_filter_tables = self._load_erd_filter_tables()
    
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
            # 1. 관계가 있는 테이블들만 조회 (INFERRED 테이블은 [I] 접두어 포함)
            tables_with_relationships = self._get_tables_with_relationships()

            # 2. 기본 테이블-컬럼 정보 조회 (관계가 있는 테이블만)
            if not tables_with_relationships:
                app_logger.warning("관계가 있는 테이블이 없습니다")
                return {}

            # [I] 접두어를 제거한 실제 테이블명 목록 생성 (DB 조회용)
            raw_table_names = [t[3:] if t.startswith('[I]') else t for t in tables_with_relationships]
            # 테이블명 -> [I] 접두어 여부 매핑
            inferred_table_map = {(t[3:] if t.startswith('[I]') else t): t.startswith('[I]') for t in tables_with_relationships}
            # 관계 기준 테이블명 로그 (디버깅용)
            app_logger.info(f"[ERD DEBUG] 관계 기준 테이블 목록 (raw): {raw_table_names}")
            # PLAR/PLAF/SM.PLAR 패턴 필터링 로그
            for nm in raw_table_names:
                up_nm = (nm or '').upper()
                if up_nm in ('PLAR_PAFF_BAS', 'PLAF_PAFF_BAS', 'SM.PLAR_PAFF_BAS', 'SM_PLAR_PAFF_BAS'):
                    app_logger.info(f"[ERD DEBUG][REL-RAW] table={nm}, inferred_prefix={inferred_table_map.get(nm, False)}")

            # IN 절을 위한 플레이스홀더 생성
            placeholders = ','.join(['?' for _ in raw_table_names])
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

            params = [self.project_name] + raw_table_names
            results = self.db_utils.execute_query(query, params)

            # 조회 결과 기준 누락 테이블 로그 (테이블 메타 없음)
            returned_names = {row['table_name'] for row in (results or [])}
            missing_tables = [name for name in raw_table_names if name not in returned_names]
            if missing_tables:
                app_logger.info(f"[ERD DEBUG] 테이블 메타 누락 감지: {missing_tables}")
                # PLAR/PLAF 패턴 특화 로그
                for mt in missing_tables:
                    upper_mt = (mt or '').upper()
                    if upper_mt in ('PLAR_PAFF_BAS', 'PLAF_PAFF_BAS', 'SM.PLAR_PAFF_BAS', 'SM_PLAR_PAFF_BAS'):
                        app_logger.info(f"[ERD DEBUG] PLAR/PLAF/PAFF 관련 누락 테이블: {mt} (inferred={inferred_table_map.get(mt, False)})")

            # 테이블별로 데이터 그룹화 (INFERRED 테이블은 [I] 접두어 추가)
            tables_data = {}
            for row in results:
                raw_table_name = row['table_name']
                # INFERRED 테이블이면 [I] 접두어 추가
                table_name = f"[I]{raw_table_name}" if inferred_table_map.get(raw_table_name, False) else raw_table_name
                if table_name not in tables_data:
                    tables_data[table_name] = []

                tables_data[table_name].append({
                    'column_name': row['column_name'],
                    'data_type': row['data_type'],
                    'is_primary_key': bool(row['position_pk']),
                    'is_nullable': row['nullable'] == 'Y',
                    'column_comments': row['column_comments'],
                    'data_length': row['data_length'],
                    'data_default': row['data_default'],
                    'is_inferred': False
                })

            # 3. 컬럼이 없는 테이블들에 대해 조인 조건에서 컬럼 추가 (관계가 있는 테이블만)
            for table_name in tables_with_relationships:
                if table_name not in tables_data:
                    # INFERRED 테이블은 [I] 접두어가 이미 포함되어 있음
                    tables_data[table_name] = []

            # 4. 관계 기반 추론 컬럼(INFERRED) 추가
            self._add_inferred_columns(tables_data)

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
                    f.file_type,
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
                LEFT JOIN components comp ON comp.component_type = 'TABLE' 
                    AND comp.component_name = t.table_name 
                    AND comp.project_id = t.project_id 
                    AND comp.del_yn = 'N'
                LEFT JOIN files f ON comp.file_id = f.file_id AND f.del_yn = 'N'
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
                        'data_default': row['data_default'],
                        'is_inferred': False
                    })
            

            
            # 관계 기반 추론 컬럼(INFERRED) 추가
            self._add_inferred_columns(tables_data)
            
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
            # INFERRED 테이블 정보와 함께 조회 (file_type != 'CSV'이면 INFERRED)
            query = """
                SELECT DISTINCT
                    src.component_name as table_name,
                    CASE WHEN f.file_type IS NOT NULL AND f.file_type != 'CSV' THEN 1 ELSE 0 END as is_inferred,
                    COALESCE(f.file_type, '') as file_type
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                JOIN components dst ON r.dst_id = dst.component_id
                JOIN projects p ON src.project_id = p.project_id
                LEFT JOIN files f ON src.file_id = f.file_id
                WHERE p.project_name = ?
                  AND r.rel_type IN ('JOIN_EXPLICIT', 'JOIN_IMPLICIT')
                  AND r.del_yn = 'N'
                  AND src.del_yn = 'N'
                  AND dst.del_yn = 'N'
                  AND src.component_type = 'TABLE'

                UNION

                SELECT DISTINCT
                    dst.component_name as table_name,
                    CASE WHEN f.file_type IS NOT NULL AND f.file_type != 'CSV' THEN 1 ELSE 0 END as is_inferred,
                    COALESCE(f.file_type, '') as file_type
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                JOIN components dst ON r.dst_id = dst.component_id
                JOIN projects p ON src.project_id = p.project_id
                LEFT JOIN files f ON dst.file_id = f.file_id
                WHERE p.project_name = ?
                  AND r.rel_type IN ('JOIN_EXPLICIT', 'JOIN_IMPLICIT')
                  AND r.del_yn = 'N'
                  AND src.del_yn = 'N'
                  AND dst.del_yn = 'N'
                  AND dst.component_type = 'TABLE'

                ORDER BY table_name
            """

            results = self.db_utils.execute_query(query, (self.project_name, self.project_name))
            # INFERRED 테이블은 [I] 접두어를 붙여서 반환
            table_names = []
            for row in results:
                table_name = row['table_name']
                file_type = row.get('file_type')
                upper_name = (table_name or '').upper()
                if upper_name in ('PLAR_PAFF_BAS', 'PLAF_PAFF_BAS', 'SM.PLAR_PAFF_BAS', 'SM_PLAR_PAFF_BAS'):
                    app_logger.info(
                        f"[ERD DEBUG][REL-TABLE] name={table_name}, file_type={file_type}, inferred_flag={row['is_inferred']}"
                    )
                if row['is_inferred']:
                    table_name = f"[I]{table_name}"
                table_names.append(table_name)

            app_logger.debug(f"관계가 있는 테이블 조회 완료: {len(table_names)}개 테이블")
            return table_names

        except Exception as e:
            app_logger.error(f"관계가 있는 테이블 조회 실패: {str(e)}")
            return []

    def _add_inferred_columns(self, tables_data: Dict[str, List[Dict[str, Any]]]) -> None:
        """조인 관계에서 추론된 컬럼을 테이블에 추가 (INFERRED 표시).
        스키마에 없는 컬럼이라도 쿼리에 명시된 경우 표시하여 추론 근거를 남긴다.
        """
        try:
            query = """
                SELECT 
                    src.component_name AS src_table,
                    dst.component_name AS dst_table,
                    r.src_column,
                    r.dst_column
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                JOIN components dst ON r.dst_id = dst.component_id
                JOIN projects p ON src.project_id = p.project_id
                WHERE p.project_name = ?
                  AND r.rel_type IN ('JOIN_EXPLICIT', 'JOIN_IMPLICIT')
                  AND r.del_yn = 'N'
                  AND src.del_yn = 'N'
                  AND dst.del_yn = 'N'
            """
            rel_rows = self.db_utils.execute_query(query, (self.project_name,))

            def get_effective_table_name(table_name: str) -> str:
                """주어진 테이블명에 [I] 접두어가 붙어있거나, tables_data에 [I] 접두어 형태로 존재하면 해당 이름 반환"""
                if table_name.startswith('[I]'):
                    return table_name
                # tables_data에 [I] 접두어 형태로 존재하는지 확인
                for key in tables_data.keys():
                    if key.startswith('[I]') and key[3:] == table_name:
                        return key
                return table_name

            def add_if_missing(table_name: str, col_name: str, inferred_from: str = None):
                if not table_name or not col_name:
                    return
                # 리터럴 값은 INFERRED 컬럼으로 추가하지 않음 (숫자, SYSDATE, TRUE/FALSE 등)
                from util.oracle_keyword_manager import is_literal_value
                if is_literal_value(col_name):
                    return
                
                effective_table_name = get_effective_table_name(table_name)

                if effective_table_name not in tables_data:
                    tables_data[effective_table_name] = []
                
                existing = {c['column_name'] for c in tables_data[effective_table_name]}
                if col_name in existing:
                    return
                inferred_label = inferred_from or col_name
                tables_data[effective_table_name].append({
                    'column_name': col_name,
                    'data_type': 'INFERRED',
                    'data_length': None,
                    'is_nullable': True,
                    'column_comments': None,
                    'is_primary_key': False,
                    'is_foreign_key': False,
                    'data_default': None,
                    'is_inferred': True,
                    'inferred_from': inferred_from
                })

            for row in rel_rows:
                add_if_missing(row['src_table'], row['src_column'], row['dst_table'])
                add_if_missing(row['dst_table'], row['dst_column'], row['src_table'])
                
                # 테이블 자체가 스키마에 없으면 INFERRED 테이블로 추가 (컬럼명에 [I]테이블명)
                # 이 로직은 `get_tables_with_columns`에서 이미 [I] 접두어를 붙여 처리하고 있으므로,
                # 중복 생성을 방지하기 위해 `get_effective_table_name`을 사용하여 한 번 더 확인합니다.
                for tbl in (row['src_table'], row['dst_table']):
                    if tbl and get_effective_table_name(tbl) not in tables_data: # 이미 처리된 테이블인지 확인
                        effective_tbl_name_for_new_entry = f"[I]{tbl}" # 새로 추가될 때는 [I] 접두어를 붙여서 추가
                        tables_data[effective_tbl_name_for_new_entry] = [{
                            'column_name': f"[I]{tbl}",
                            'data_type': 'INFERRED',
                            'data_length': None,
                            'is_nullable': True,
                            'column_comments': None,
                            'is_primary_key': False,
                            'is_foreign_key': False,
                            'data_default': None,
                            'is_inferred': True,
                            'inferred_from': tbl
                        }]

        except Exception as e:
            app_logger.error(f"관계 기반 추론 컬럼 추가 실패: {str(e)}")
    
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
                JOIN components comp 
                    ON comp.component_type = 'TABLE'
                    AND comp.component_name = t.table_name
                    AND comp.project_id = t.project_id
                    AND comp.del_yn = 'N'
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

    def apply_table_filter(
        self,
        tables_data: Dict[str, Any],
        relationships: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        ERD_REPORT_TABLES.cfg 기반 테이블/관계 필터링
        - 지정된 테이블 + 그 테이블과 직접 조인되는 1단계 인접 테이블만 남긴다.
        - 필터 설정이 없거나 비어 있으면 원본 데이터를 그대로 반환.
        """
        if not self.erd_filter_tables:
            return tables_data, relationships
        if not tables_data:
            return tables_data, relationships

        base_set = self.erd_filter_tables
        allowed_tables = set()

        for table_name in tables_data.keys():
            if self._normalize_table_name(table_name) in base_set:
                allowed_tables.add(table_name)

        filtered_relationships = []
        for rel in relationships or []:
            src_table = rel.get('src_table')
            dst_table = rel.get('dst_table')
            if not src_table or not dst_table:
                continue

            src_base = self._normalize_table_name(src_table)
            dst_base = self._normalize_table_name(dst_table)

            # CFG에 지정된 테이블과 직접 연결된 관계만 남김
            if src_base in base_set or dst_base in base_set:
                filtered_relationships.append(rel)
                allowed_tables.add(src_table)
                allowed_tables.add(dst_table)

        # 관계가 하나도 없으면 필터링 결과를 비워서 고아 출력 방지
        if not filtered_relationships:
            app_logger.info("[ERD DEBUG] 필터링 결과 관계가 없어 테이블/관계를 비웁니다.")
            return {}, []

        filtered_tables = {
            name: data
            for name, data in tables_data.items()
            if name in allowed_tables
        }

        allowed_keys = set(filtered_tables.keys())
        filtered_relationships = [
            rel for rel in filtered_relationships
            if rel.get('src_table') in allowed_keys and rel.get('dst_table') in allowed_keys
        ]

        return filtered_tables, filtered_relationships

    def _normalize_table_name(self, table_name: str) -> str:
        if not table_name:
            return ''
        name = table_name[3:] if table_name.startswith('[I]') else table_name
        return name.upper()

    def _load_erd_filter_tables(self) -> set:
        """ERD_REPORT_TABLES.cfg에서 필터 테이블 목록을 로드"""
        try:
            cfg_path = self.path_utils.join_path(
                'projects',
                self.project_name,
                'db_schema',
                'ERD_REPORT_TABLES.cfg'
            )
            if not os.path.exists(cfg_path):
                return set()

            tables = set()
            with open(cfg_path, 'r', encoding='utf-8') as cfg_file:
                for line in cfg_file:
                    cleaned = line.split('#', 1)[0].strip()
                    if cleaned:
                        tables.add(cleaned.upper())

            if tables:
                app_logger.info(f"ERD 테이블 필터 적용: {len(tables)}개 기준 테이블")
            return tables
        except Exception as e:
            app_logger.error(f"ERD 필터 테이블 로드 실패: {str(e)}")
            return set()

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
                    f.file_type,
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
                LEFT JOIN components comp 
                    ON comp.component_type = 'TABLE'
                    AND comp.component_name = t.table_name
                    AND comp.project_id = t.project_id
                    AND comp.del_yn = 'N'
                LEFT JOIN files f ON comp.file_id = f.file_id AND f.del_yn = 'N'
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
                        'columns': [],
                        'is_inferred': (row.get('file_type') == 'INFERRED') or table_name.startswith('[I]')
                    }
                
                tables_data[table_name]['columns'].append({
                    'column_name': row['column_name'],
                    'data_type': row['data_type'],
                    'is_primary_key': bool(row['position_pk']),
                    'is_nullable': row['nullable'] == 'Y',
                    'column_comments': row['column_comments'],
                    'column_order': row['column_id'],
                    'data_length': row['data_length'],
                    'data_default': row['data_default'],
                    'is_inferred': False,
                    'inferred_from': None
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
                                'data_default': None,
                                'is_inferred': True,
                                'inferred_from': table_name
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
                        'columns': [],
                        'is_inferred': (row.get('file_type') == 'INFERRED') or table_name.startswith('[I]')
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
                        'data_default': row['data_default'],
                        'is_inferred': False,
                        'inferred_from': None
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
                    dst.component_name as dst_table,
                    r.src_column,
                    r.dst_column,
                    r.join_condition,
                    fs.file_type AS src_file_type,
                    fd.file_type AS dst_file_type
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                JOIN components dst ON r.dst_id = dst.component_id
                JOIN projects p ON src.project_id = p.project_id
                LEFT JOIN files fs ON src.file_id = fs.file_id AND fs.del_yn = 'N'
                LEFT JOIN files fd ON dst.file_id = fd.file_id AND fd.del_yn = 'N'
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
                # INFERRED 테이블 여부 판단 (file_type != 'CSV'이면 INFERRED)
                src_is_inferred = row.get('src_file_type') != 'CSV'
                dst_is_inferred = row.get('dst_file_type') != 'CSV'
                # INFERRED 테이블은 [I] 접두어 추가
                src_table = f"[I]{row['src_table']}" if src_is_inferred else row['src_table']
                dst_table = f"[I]{row['dst_table']}" if dst_is_inferred else row['dst_table']

                # 메타데이터 기반으로 컬럼 정보 추출 (저장된 조인 컬럼 우선, 스키마 불일치 시에도 INFERRED로 사용)
                src_column = row.get('src_column')
                dst_column = row.get('dst_column')
                if not src_column or not dst_column:
                    src_column, dst_column = self.get_join_columns_from_metadata(
                        row['src_table'],
                        row['dst_table']
                    )
                join_condition = row.get('join_condition') or f"{src_table}.{src_column or 'ID'} = {dst_table}.{dst_column or 'ID'}"

                # 관계 정보 추가
                relationships.append({
                    'rel_type': row['rel_type'],
                    'src_table': src_table,
                    'dst_table': dst_table,
                    'src_column': src_column,
                    'dst_column': dst_column,
                    'src_is_inferred': src_is_inferred,
                    'dst_is_inferred': dst_is_inferred,
                    'confidence': 0.9,
                    'frequency': 1,     # ERD Dagre용 기본 빈도
                    'src_owner': '',    # ERD Dagre용 기본값
                    'dst_owner': '',    # ERD Dagre용 기본값
                    'src_data_type': 'VARCHAR',  # ERD Dagre용 기본값
                    'dst_data_type': 'VARCHAR',  # ERD Dagre용 기본값
                    'join_condition': join_condition,      # ERD Dagre용 기본값
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
            
            # 2. PK ↔ FK 패턴 매칭 (예: USERS.ID → USER_PROFILES.USER_ID)
            pk_query = """
                SELECT 
                    c.column_name
                FROM columns c
                JOIN tables t ON c.table_id = t.table_id
                JOIN projects p ON t.project_id = p.project_id
                WHERE t.table_name = ?
                  AND p.project_name = ?
                  AND t.del_yn = 'N'
                  AND c.del_yn = 'N'
                  AND c.position_pk IS NOT NULL
                ORDER BY c.position_pk
                LIMIT 1
            """
            src_pk_row = self.db_utils.execute_query(pk_query, (src_table.upper(), self.project_name))
            src_pk = src_pk_row[0]['column_name'] if src_pk_row else None

            fk_query = """
                SELECT column_name 
                FROM columns c
                JOIN tables t ON c.table_id = t.table_id
                JOIN projects p ON t.project_id = p.project_id
                WHERE t.table_name = ? 
                  AND p.project_name = ?
                  AND t.del_yn = 'N' AND c.del_yn = 'N'
            """
            dst_cols = self.db_utils.execute_query(fk_query, (dst_table.upper(), self.project_name))
            dst_col_names = {row['column_name'] for row in dst_cols} if dst_cols else set()

            fk_candidates = []
            if src_pk:
                fk_base = f"{src_table[:-1] if src_table.upper().endswith('S') else src_table}_ID".upper()
                fk_candidates.extend([src_pk, fk_base])

            matched_fk = None
            for cand in fk_candidates:
                if cand in dst_col_names:
                    matched_fk = cand
                    break

            if matched_fk and src_pk:
                return src_pk, matched_fk
            
            # 3. 매칭 실패 시 None 반환하여 이후 표시 단계에서 필터링
            app_logger.debug(f"JOIN 컬럼 추출 실패: {src_table} ↔ {dst_table}, fallback 없음") 
            return None, None
            
        except Exception as e:
            app_logger.error(f"메타데이터 기반 JOIN 컬럼 추출 중 오류: {str(e)}")
            # 오류 시 기본값 반환
            return src_table.lower() + '_id', dst_table.lower() + '_id'
    
    def get_relationship_info(self, src_table: str, src_column: str, dst_table: str, dst_column: str) -> Dict[str, Any]:
        """관계 정보 상세 조회 (PK-FK 여부, nullable 여부 등) - 각 컬럼 별도 조회"""
        try:
            # 소스 컬럼 정보 조회
            src_query = """
                SELECT
                    c.position_pk as is_pk,
                    c.nullable,
                    c.data_type
                FROM tables t
                JOIN columns c ON t.table_id = c.table_id
                JOIN projects p ON t.project_id = p.project_id
                WHERE t.table_name = ?
                  AND p.project_name = ?
                  AND c.column_name = ?
                  AND t.del_yn = 'N'
                  AND c.del_yn = 'N'
            """

            src_result = self.db_utils.execute_query(src_query, (src_table.upper(), self.project_name, src_column.upper()))

            # 대상 컬럼 정보 조회
            dst_query = """
                SELECT
                    c.position_pk as is_pk,
                    c.nullable,
                    c.data_type
                FROM tables t
                JOIN columns c ON t.table_id = c.table_id
                JOIN projects p ON t.project_id = p.project_id
                WHERE t.table_name = ?
                  AND p.project_name = ?
                  AND c.column_name = ?
                  AND t.del_yn = 'N'
                  AND c.del_yn = 'N'
            """

            dst_result = self.db_utils.execute_query(dst_query, (dst_table.upper(), self.project_name, dst_column.upper()))

            # 결과 조합
            src_info = src_result[0] if src_result else None
            dst_info = dst_result[0] if dst_result else None

            return {
                'src_is_pk': bool(src_info['is_pk']) if src_info else False,
                'src_nullable': (src_info['nullable'] == 'Y') if src_info else True,
                'dst_is_pk': bool(dst_info['is_pk']) if dst_info else False,
                'dst_nullable': (dst_info['nullable'] == 'Y') if dst_info else True,
                'src_data_type': src_info['data_type'] if src_info else 'VARCHAR',
                'dst_data_type': dst_info['data_type'] if dst_info else 'VARCHAR'
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
    
    
