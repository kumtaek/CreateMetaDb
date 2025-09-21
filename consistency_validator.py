"""
메타데이터베이스 일관성 검증기 (최종판)
실제 비일관성만 검출, 정상 케이스 제외

치명적 비일관성 (ERROR + EXIT):
1. 외래키 무결성 위반
2. 파일 중복 (UNIQUE 제약조건 우회)  
3. API_URL 중복 (백엔드에서 하나의 API_URL이 여러 METHOD에 매핑)
4. 관계 무결성 위반
5. parent_id 타입 불일치

경고성 (WARNING 로그만):
- 정상적이지만 확인 필요한 케이스들
"""

import sys
import os
from typing import Dict, List, Any, Optional

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from util.database_utils import DatabaseUtils
from util.path_utils import get_project_metadata_db_path
from util.logger import app_logger, handle_error, info, warning, error


class ConsistencyValidator:
    """메타데이터베이스 일관성 검증 클래스"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.metadata_db_path = get_project_metadata_db_path(project_name)
        self.db_utils = DatabaseUtils(self.metadata_db_path)
        
        if not self.db_utils.connect():
            handle_error(Exception("데이터베이스 연결 실패"), f"메타데이터베이스 연결 실패: {self.metadata_db_path}")
        
        self.critical_violations = []
        
        # 현재 프로젝트 ID 조회
        self.project_id = self._get_project_id()
        if not self.project_id:
            handle_error(Exception("프로젝트 ID 조회 실패"), f"프로젝트 '{project_name}'을 찾을 수 없습니다")
        
        # CSV 파일 ID 동적 조회
        self.all_tables_file_id = self._get_csv_file_id('ALL_TABLES.csv')
        self.all_columns_file_id = self._get_csv_file_id('ALL_TAB_COLUMNS.csv')
    
    def _get_project_id(self) -> Optional[int]:
        """현재 프로젝트의 project_id 조회"""
        try:
            result = self.db_utils.execute_query("""
                SELECT project_id FROM projects 
                WHERE project_name = ? AND del_yn = 'N'
                LIMIT 1
            """, (self.project_name,))
            
            if result:
                project_id = result[0]['project_id']
                info(f"프로젝트 ID 조회: {self.project_name} -> project_id {project_id}")
                return project_id
            else:
                warning(f"프로젝트를 찾을 수 없음: {self.project_name}")
                return None
                
        except Exception as e:
            warning(f"프로젝트 ID 조회 실패: {self.project_name} - {e}")
            return None
    
    def _get_csv_file_id(self, file_name: str) -> Optional[int]:
        """CSV 파일의 file_id 동적 조회"""
        try:
            result = self.db_utils.execute_query("""
                SELECT file_id FROM files 
                WHERE file_name = ? AND file_type = 'CSV' AND del_yn = 'N'
                LIMIT 1
            """, (file_name,))
            
            if result:
                file_id = result[0]['file_id']
                info(f"CSV 파일 ID 조회: {file_name} -> file_id {file_id}")
                return file_id
            else:
                warning(f"CSV 파일을 찾을 수 없음: {file_name}")
                return None
                
        except Exception as e:
            warning(f"CSV 파일 ID 조회 실패: {file_name} - {e}")
            return None
    
    def close(self):
        if self.db_utils:
            self.db_utils.disconnect()
    
    def validate_all(self) -> bool:
        """
        전체 일관성 검증 실행
        
        Returns:
            검증 성공 여부 (치명적 문제 없으면 True)
        """
        try:
            info("메타데이터베이스 일관성 검증 시작")
            
            # 치명적 비일관성 검사
            self._check_foreign_key_violations()
            self._check_file_duplicates()
            self._check_method_duplicates()  # 추가: 메서드 중복 검사
            self._check_api_url_duplicates()
            self._check_relationship_violations()
            self._check_parent_id_violations()
            # self._check_table_column_file_id_violations()  # 제거: inferred 컴포넌트는 다양한 파일에서 생성 가능
            
            # 경고성 검사
            self._check_warning_cases()
            
            # 치명적 문제 처리
            if self.critical_violations:
                error(f"치명적 일관성 위반 {len(self.critical_violations)}개 발견:")
                for i, violation in enumerate(self.critical_violations, 1):
                    error(f"  {i}. {violation['type']}: {violation['description']}")
                
                handle_error(Exception("메타데이터베이스 일관성 위반"), "치명적 일관성 문제로 인한 종료")
                return False
            else:
                info("메타데이터베이스 일관성 검증 통과")
                return True
                
        except Exception as e:
            handle_error(e, "일관성 검증 실행 실패")
            return False
    
    def _check_foreign_key_violations(self):
        """치명적: 외래키 무결성 위반"""
        
        # 1. files.project_id → projects.project_id
        orphaned_files = self.db_utils.execute_query("""
            SELECT f.file_id, f.file_name, f.project_id
            FROM files f
            WHERE f.del_yn = 'N'
              AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = f.project_id)
        """)
        
        for orphan in orphaned_files:
            self.critical_violations.append({
                'type': 'FK_VIOLATION_FILES_PROJECT',
                'description': f"파일 '{orphan['file_name']}'이 존재하지 않는 프로젝트 ID {orphan['project_id']}를 참조"
            })
        
        # 2. components.file_id → files.file_id
        orphaned_components = self.db_utils.execute_query("""
            SELECT c.component_id, c.component_name, c.file_id
            FROM components c
            WHERE c.del_yn = 'N'
              AND NOT EXISTS (SELECT 1 FROM files f WHERE f.file_id = c.file_id AND f.del_yn = 'N')
        """)
        
        for orphan in orphaned_components:
            self.critical_violations.append({
                'type': 'FK_VIOLATION_COMPONENTS_FILE',
                'description': f"컴포넌트 '{orphan['component_name']}'이 존재하지 않는 파일 ID {orphan['file_id']}를 참조"
            })
        
        # 3. classes.parent_class_id → classes.class_id
        orphaned_inheritance = self.db_utils.execute_query("""
            SELECT c.class_id, c.class_name, c.parent_class_id
            FROM classes c
            WHERE c.del_yn = 'N' AND c.parent_class_id IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM classes p WHERE p.class_id = c.parent_class_id AND p.del_yn = 'N')
        """)
        
        for orphan in orphaned_inheritance:
            self.critical_violations.append({
                'type': 'FK_VIOLATION_CLASS_PARENT',
                'description': f"클래스 '{orphan['class_name']}'이 존재하지 않는 부모 클래스 ID {orphan['parent_class_id']}를 참조"
            })
        
        # 4. relationships.src_id, dst_id → components.component_id
        broken_relationships = self.db_utils.execute_query("""
            SELECT r.relationship_id, r.src_id, r.dst_id, r.rel_type
            FROM relationships r
            WHERE r.del_yn = 'N'
              AND (NOT EXISTS (SELECT 1 FROM components c WHERE c.component_id = r.src_id AND c.del_yn = 'N')
                   OR NOT EXISTS (SELECT 1 FROM components c WHERE c.component_id = r.dst_id AND c.del_yn = 'N'))
        """)
        
        for broken in broken_relationships:
            self.critical_violations.append({
                'type': 'FK_VIOLATION_RELATIONSHIPS',
                'description': f"관계 ID {broken['relationship_id']}이 존재하지 않는 컴포넌트를 참조 ({broken['src_id']} → {broken['dst_id']})"
            })
    
    def _check_file_duplicates(self):
        """치명적: 파일 중복 (UNIQUE 제약조건 우회)"""
        
        # ix_files_01: (file_name, file_path, project_id) UNIQUE 제약조건 위반
        file_duplicates = self.db_utils.execute_query("""
            SELECT 
                file_name,
                file_path,
                project_id,
                COUNT(*) as count,
                GROUP_CONCAT(file_id) as file_ids
            FROM files 
            WHERE del_yn = 'N'
            GROUP BY file_name, file_path, project_id
            HAVING COUNT(*) > 1
        """)
        
        for dup in file_duplicates:
            self.critical_violations.append({
                'type': 'FILE_UNIQUE_VIOLATION',
                'description': f"파일 '{dup['file_name']}' ({dup['file_path']})이 {dup['count']}개 중복 등록됨 - UNIQUE 제약조건 위반"
            })
    
    def _check_method_duplicates(self):
        """치명적: 메서드 중복 저장 (같은 파일에서 같은 메서드가 여러 번 추출)"""
        
        method_duplicates = self.db_utils.execute_query("""
            SELECT 
                c.component_name,
                f.file_id,
                f.file_name,
                f.file_path,
                COUNT(*) as count,
                GROUP_CONCAT(c.component_id) as component_ids,
                GROUP_CONCAT(c.hash_value) as hash_values
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            WHERE c.component_type = 'METHOD' 
              AND c.del_yn = 'N'
              AND f.del_yn = 'N'
            GROUP BY c.component_name, f.file_id
            HAVING COUNT(*) > 1
            ORDER BY count DESC, c.component_name
        """)
        
        for dup in method_duplicates:
            component_ids = dup['component_ids'].split(',')
            hash_values = dup['hash_values'].split(',')
            unique_hashes = len(set(hash_values))
            
            self.critical_violations.append({
                'type': 'METHOD_DUPLICATE',
                'description': f"파일 '{dup['file_name']}'에서 메서드 '{dup['component_name']}'이 {dup['count']}개 중복 저장됨 (해시값 {unique_hashes}개) - component_ids: {', '.join(component_ids[:3])}"
            })
        
        info(f"메서드 중복 검증 완료: {len(method_duplicates)}개 중복 발견")
    
    def _check_api_url_duplicates(self):
        """치명적: API_URL 중복 검증"""
        
        # 1. 백엔드: 하나의 API_URL이 여러 METHOD와 관계를 맺는 경우
        backend_multi_method_apis = self.db_utils.execute_query("""
            SELECT 
                api.component_name as api_name,
                COUNT(r.dst_id) as method_count,
                GROUP_CONCAT(method.component_name) as method_names,
                GROUP_CONCAT(f.file_name) as file_names
            FROM components api
            JOIN relationships r ON api.component_id = r.src_id
            JOIN components method ON r.dst_id = method.component_id
            JOIN files f ON api.file_id = f.file_id
            WHERE api.component_type = 'API_URL' 
              AND r.rel_type = 'CALL_METHOD'
              AND f.file_type = 'JAVA'
              AND f.project_id = ?
              AND api.del_yn = 'N'
              AND r.del_yn = 'N'
              AND method.del_yn = 'N'
              AND f.del_yn = 'N'
            GROUP BY api.component_name
            HAVING COUNT(r.dst_id) > 1
        """, (self.project_id,))
        
        for dup in backend_multi_method_apis:
            method_names = dup['method_names'].split(',')[:5]  # 처음 5개만
            self.critical_violations.append({
                'type': 'BACKEND_API_MULTI_METHOD',
                'description': f"백엔드 API '{dup['api_name']}'이 {dup['method_count']}개 METHOD와 연결됨 (1:1 매핑 위반) - METHOD: {', '.join(method_names)}"
            })
        
        # 2. 프론트엔드: 하나의 파일에서 같은 API_URL이 여러 개 생성된 경우
        frontend_file_duplicates = self.db_utils.execute_query("""
            SELECT 
                c.component_name,
                f.file_id,
                f.file_name,
                f.file_path,
                COUNT(*) as count
            FROM components c 
            JOIN files f ON c.file_id = f.file_id
            WHERE c.component_type = 'API_URL' 
              AND f.file_type IN ('JSP', 'JS', 'VUE', 'JSX', 'HTML')
              AND c.del_yn = 'N' 
              AND f.del_yn = 'N'
            GROUP BY c.component_name, f.file_id
            HAVING COUNT(*) > 1
        """)
        
        for dup in frontend_file_duplicates:
            self.critical_violations.append({
                'type': 'FRONTEND_API_FILE_DUPLICATE',
                'description': f"프론트엔드 파일 '{dup['file_name']}'에서 API '{dup['component_name']}'이 {dup['count']}개 중복 생성됨"
            })
        
        info(f"API_URL 중복 검증 완료: 백엔드 {len(backend_multi_method_apis)}개, 프론트엔드 {len(frontend_file_duplicates)}개 위반 발견")
    
    def _check_relationship_violations(self):
        """치명적: 관계 무결성 위반"""
        
        # relationships 테이블의 외래키 위반은 이미 _check_foreign_key_violations에서 처리됨
        # 여기서는 추가적인 관계 논리 검사만 수행
        
        # 자기 자신을 참조하는 관계 (CHECK 제약조건 위반)
        self_references = self.db_utils.execute_query("""
            SELECT r.relationship_id, r.src_id, r.rel_type, c.component_name
            FROM relationships r
            JOIN components c ON r.src_id = c.component_id
            WHERE r.src_id = r.dst_id AND r.del_yn = 'N'
        """)
        
        for self_ref in self_references:
            self.critical_violations.append({
                'type': 'SELF_REFERENCE_VIOLATION',
                'description': f"자기 자신을 참조하는 관계: {self_ref['component_name']} ({self_ref['rel_type']}) - CHECK 제약조건 위반"
            })
    
    def _check_parent_id_violations(self):
        """치명적: parent_id 타입 불일치"""
        
        # METHOD의 parent_id는 classes.class_id여야 함
        method_parent_violations = self.db_utils.execute_query("""
            SELECT c.component_id, c.component_name, c.parent_id
            FROM components c
            WHERE c.component_type = 'METHOD' AND c.parent_id IS NOT NULL AND c.del_yn = 'N'
              AND NOT EXISTS (SELECT 1 FROM classes cl WHERE cl.class_id = c.parent_id AND cl.del_yn = 'N')
        """)
        
        for violation in method_parent_violations:
            self.critical_violations.append({
                'type': 'METHOD_PARENT_TYPE_VIOLATION',
                'description': f"METHOD '{violation['component_name']}'의 parent_id {violation['parent_id']}가 존재하지 않는 클래스를 참조"
            })
        
        # COLUMN의 parent_id는 components.component_id (TABLE 타입)여야 함
        column_parent_violations = self.db_utils.execute_query("""
            SELECT c.component_id, c.component_name, c.parent_id
            FROM components c
            WHERE c.component_type = 'COLUMN' AND c.parent_id IS NOT NULL AND c.del_yn = 'N'
              AND NOT EXISTS (
                  SELECT 1 FROM components p 
                  WHERE p.component_id = c.parent_id AND p.component_type = 'TABLE' AND p.del_yn = 'N'
              )
        """)
        
        for violation in column_parent_violations:
            self.critical_violations.append({
                'type': 'COLUMN_PARENT_TYPE_VIOLATION',
                'description': f"COLUMN '{violation['component_name']}'의 parent_id {violation['parent_id']}가 TABLE 컴포넌트가 아님"
            })
    
    def _check_table_column_file_id_violations(self):
        """치명적: TABLE/COLUMN 컴포넌트의 file_id 검증"""
        
        # TABLE 컴포넌트는 ALL_TABLES.csv file_id를 가져야 함 (inferred TABLE 제외)
        if self.all_tables_file_id:
            wrong_table_file_ids = self.db_utils.execute_query("""
                SELECT component_id, component_name, file_id, hash_value
                FROM components
                WHERE component_type = 'TABLE' AND del_yn = 'N'
                  AND file_id != ?
                  AND hash_value != 'INFERRED'  -- inferred TABLE은 제외
            """, (self.all_tables_file_id,))
            
            for violation in wrong_table_file_ids:
                self.critical_violations.append({
                    'type': 'TABLE_WRONG_FILE_ID',
                    'description': f"TABLE 컴포넌트 '{violation['component_name']}'의 file_id가 ALL_TABLES.csv({self.all_tables_file_id})가 아님 (현재: {violation['file_id']})"
                })
        
        # COLUMN 컴포넌트는 ALL_TAB_COLUMNS.csv file_id를 가져야 함 (inferred COLUMN 제외)
        if self.all_columns_file_id:
            wrong_column_file_ids = self.db_utils.execute_query("""
                SELECT component_id, component_name, file_id, hash_value
                FROM components
                WHERE component_type = 'COLUMN' AND del_yn = 'N'
                  AND file_id != ?
                  AND hash_value != 'INFERRED'  -- inferred COLUMN은 제외
            """, (self.all_columns_file_id,))
            
            for violation in wrong_column_file_ids:
                self.critical_violations.append({
                    'type': 'COLUMN_WRONG_FILE_ID',
                    'description': f"COLUMN 컴포넌트 '{violation['component_name']}'의 file_id가 ALL_TAB_COLUMNS.csv({self.all_columns_file_id})가 아님 (현재: {violation['file_id']})"
                })
    
    def _check_warning_cases(self):
        """경고성 검사 (정상적이지만 확인 필요)"""
        
        # 1. 프론트엔드 API 크로스 파일 사용량 (정보성)
        frontend_cross_file_apis = self.db_utils.execute_query("""
            SELECT 
                c.component_name as api_name,
                COUNT(DISTINCT f.file_id) as file_count,
                GROUP_CONCAT(DISTINCT f.file_name) as file_names
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            WHERE c.component_type = 'API_URL' 
              AND f.file_type IN ('JSP', 'JS', 'VUE', 'JSX', 'HTML')
              AND c.del_yn = 'N'
              AND f.del_yn = 'N'
            GROUP BY c.component_name
            HAVING COUNT(DISTINCT f.file_id) > 5
            ORDER BY file_count DESC
            LIMIT 10
        """)
        
        for multi in frontend_cross_file_apis:
            files = multi['file_names'].split(',')[:3]  # 처음 3개만
            info(f"프론트엔드 API 다중 사용: {multi['api_name']} -> {multi['file_count']}개 파일에서 사용 (예: {', '.join(files)})")
        
        # 2. 백엔드 연결 없는 API (프론트엔드 전용 API일 수 있음)
        orphaned_apis = self.db_utils.execute_query("""
            SELECT c.component_name, f.file_name, f.file_type
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            WHERE c.component_type = 'API_URL' AND c.del_yn = 'N'
              AND NOT EXISTS (
                  SELECT 1 FROM relationships r 
                  WHERE r.src_id = c.component_id AND r.rel_type = 'CALL_METHOD' AND r.del_yn = 'N'
              )
        """)
        
        if orphaned_apis:
            warning(f"백엔드 연결이 없는 API: {len(orphaned_apis)}개 (프론트엔드 전용 또는 JPA 자동 생성 API일 수 있음)")
            for api in orphaned_apis[:5]:
                warning(f"  - {api['component_name']} (파일: {api['file_name']})")
        
        # 3. SQL 연결이 없는 DAO 메서드 (계산 전용 메서드일 수 있음)
        dao_without_sql = self.db_utils.execute_query("""
            SELECT c.component_name, c.layer
            FROM components c
            WHERE c.component_type = 'METHOD' 
              AND c.layer IN ('REPOSITORY', 'DAO', 'MAPPER')
              AND c.del_yn = 'N'
              AND NOT EXISTS (
                  SELECT 1 FROM relationships r 
                  WHERE r.src_id = c.component_id AND r.rel_type = 'CALL_QUERY' AND r.del_yn = 'N'
              )
        """)
        
        if dao_without_sql:
            warning(f"SQL 연결이 없는 DAO/Repository 메서드: {len(dao_without_sql)}개 (계산 전용 메서드일 수 있음)")
            for method in dao_without_sql[:3]:
                warning(f"  - {method['component_name']} ({method['layer']})")
        
        # 4. 테이블 연결이 없는 SQL (시스템 함수 호출일 수 있음)
        sql_without_table = self.db_utils.execute_query("""
            SELECT c.component_name, c.component_type
            FROM components c
            WHERE c.component_type LIKE 'SQL_%' AND c.del_yn = 'N'
              AND NOT EXISTS (
                  SELECT 1 FROM relationships r 
                  WHERE r.src_id = c.component_id AND r.rel_type = 'USE_TABLE' AND r.del_yn = 'N'
              )
        """)
        
        if sql_without_table:
            warning(f"테이블 연결이 없는 SQL: {len(sql_without_table)}개 (시스템 함수 또는 DUAL 테이블 사용일 수 있음)")
            for sql in sql_without_table[:3]:
                warning(f"  - {sql['component_name']} ({sql['component_type']})")
        
        # 5. 같은 파일에서 같은 쿼리명 중복 (비정상 - 실제 중복)
        sql_file_duplicates = self.db_utils.execute_query("""
            SELECT 
                c.component_name,
                c.component_type,
                c.file_id,
                f.file_name,
                COUNT(*) as count
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            WHERE c.component_type LIKE 'SQL_%' 
              AND c.del_yn = 'N'
              AND f.project_id = ?
            GROUP BY c.project_id, c.file_id, c.component_name
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """, (self.project_id,))
        
        if sql_file_duplicates:
            warning(f"같은 파일에서 중복된 SQL 쿼리: {len(sql_file_duplicates)}개 (파일 내 실제 중복)")
            for dup in sql_file_duplicates[:3]:
                warning(f"  - {dup['component_name']} ({dup['component_type']}) in {dup['file_name']}: {dup['count']}개")


def execute_consistency_validation(project_name: str) -> bool:
    """
    일관성 검증 실행 (main.py에서 호출용)
    
    Args:
        project_name: 프로젝트명
        
    Returns:
        검증 성공 여부 (치명적 문제 없으면 True)
    """
    try:
        validator = ConsistencyValidator(project_name)
        
        try:
            return validator.validate_all()
        finally:
            validator.close()
            
    except Exception as e:
        handle_error(e, "일관성 검증 실행 실패")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: py consistency_validator.py <project_name>")
        print("예: py consistency_validator.py SampleSrc")
        sys.exit(1)
    
    project_name = sys.argv[1]
    success = execute_consistency_validation(project_name)
    sys.exit(0 if success else 1)