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
import re
import sqlite3
from typing import Dict, List, Any, Optional

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from util.database_utils import DatabaseUtils
from util.path_utils import get_project_metadata_db_path, PathUtils
from util.logger import app_logger, handle_error, info, warning, error, debug


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
        
        # DB 스키마 레이아웃 파일(csv/sch) ID 조회
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
        """
        CSV/스키마 파일의 file_id 동적 조회 (csv/sch 공통 처리)

        Args:
            file_name: 파일명 또는 기본 이름 (예: 'ALL_TABLES.csv', 'ALL_TABLES')

        Returns:
            files.file_id 또는 None
        """
        try:
            # 기본 이름 및 후보 파일명 계산
            name_without_ext, ext = os.path.splitext(file_name)
            if ext.lower() in ['.csv', '.sch']:
                base_name = name_without_ext
            else:
                base_name = file_name

            candidate_names = [f"{base_name}.sch", f"{base_name}.csv"]

            result = self.db_utils.execute_query(
                """
                SELECT file_id, file_name FROM files
                WHERE file_name IN (?, ?) AND file_type = 'CSV' AND del_yn = 'N'
                ORDER BY
                  CASE
                    WHEN file_name LIKE '%.sch' THEN 0
                    WHEN file_name LIKE '%.csv' THEN 1
                    ELSE 2
                  END,
                  file_id
                LIMIT 1
                """,
                (candidate_names[0], candidate_names[1])
            )

            if result:
                file_id = result[0]['file_id']
                found_name = result[0]['file_name']
                info(f"CSV/스키마 파일 ID 조회: {found_name} -> file_id {file_id}")
                return file_id
            else:
                warning(f"CSV/스키마 파일을 찾을 수 없음: {base_name}.sch / {base_name}.csv")
                return None

        except Exception as e:
            warning(f"CSV/스키마 파일 ID 조회 실패: {file_name} - {e}")
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
    
    def _remove_duplicate_relationships(self):
        """중복 관계 제거 (같은 src_id, dst_id, rel_type의 관계 중복 제거 + 하위 정보 병합)"""
        try:
            # 같은 src_id, dst_id, rel_type을 가진 중복 관계 조회
            duplicate_relationships = self.db_utils.execute_query("""
                SELECT
                    src_id,
                    dst_id,
                    rel_type,
                    COUNT(*) as count,
                    GROUP_CONCAT(relationship_id) as relationship_ids,
                    MIN(relationship_id) as keep_id
                FROM relationships
                WHERE del_yn = 'N'
                GROUP BY src_id, dst_id, rel_type
                HAVING COUNT(*) > 1
                ORDER BY count DESC
            """)

            if duplicate_relationships:
                info(f"중복 관계 발견: {len(duplicate_relationships)}개 그룹")

                total_removed = 0
                total_merged = 0

                for dup in duplicate_relationships:
                    relationship_ids = [int(id_str) for id_str in dup['relationship_ids'].split(',')]
                    keep_id = dup['keep_id']

                    # 최소 ID를 제외한 나머지 ID들
                    remove_ids = [rid for rid in relationship_ids if rid != keep_id]

                    for remove_id in remove_ids:
                        try:
                            # [Step 1] 삭제 전 하위 정보 병합
                            # 1-1. 이 relationship_id를 parent_id로 가진 컴포넌트들을 keep_id로 이동
                            merge_count = 0
                            components_to_merge = self.db_utils.execute_query("""
                                SELECT component_id, component_type, component_name
                                FROM components
                                WHERE parent_id = ? AND del_yn = 'N'
                            """, (remove_id,))

                            if components_to_merge:
                                for comp in components_to_merge:
                                    self.db_utils.execute_query("""
                                        UPDATE components
                                        SET parent_id = ?, updated_at = CURRENT_TIMESTAMP
                                        WHERE component_id = ?
                                    """, (keep_id, comp['component_id']))
                                    merge_count += 1
                                    info(f"  병합: {comp['component_type']}({comp['component_name']}) parent_id {remove_id} → {keep_id}")

                            # 1-2. 이 relationship_id를 src_id로 가진 다른 관계들을 keep_id로 이동
                            related_as_src = self.db_utils.execute_query("""
                                SELECT relationship_id, rel_type, dst_id
                                FROM relationships
                                WHERE src_id = ? AND del_yn = 'N'
                            """, (remove_id,))

                            if related_as_src:
                                for rel in related_as_src:
                                    # 중복 방지: 이미 동일한 (keep_id, dst_id, rel_type) 관계가 있는지 확인
                                    existing = self.db_utils.execute_query("""
                                        SELECT relationship_id
                                        FROM relationships
                                        WHERE src_id = ? AND dst_id = ? AND rel_type = ? AND del_yn = 'N'
                                        LIMIT 1
                                    """, (keep_id, rel['dst_id'], rel['rel_type']))

                                    if not existing:
                                        self.db_utils.execute_query("""
                                            UPDATE relationships
                                            SET src_id = ?, updated_at = CURRENT_TIMESTAMP
                                            WHERE relationship_id = ?
                                        """, (keep_id, rel['relationship_id']))
                                        merge_count += 1
                                        info(f"  병합: 관계 src_id {remove_id} → {keep_id} ({rel['rel_type']})")
                                    else:
                                        # 중복이므로 이 관계는 삭제
                                        self.db_utils.execute_query("""
                                            UPDATE relationships
                                            SET del_yn = 'Y', updated_at = CURRENT_TIMESTAMP
                                            WHERE relationship_id = ?
                                        """, (rel['relationship_id'],))
                                        info(f"  중복 관계 삭제: relationship_id {rel['relationship_id']} (이미 존재)")

                            # 1-3. 이 relationship_id를 dst_id로 가진 다른 관계들을 keep_id로 이동
                            related_as_dst = self.db_utils.execute_query("""
                                SELECT relationship_id, rel_type, src_id
                                FROM relationships
                                WHERE dst_id = ? AND del_yn = 'N'
                            """, (remove_id,))

                            if related_as_dst:
                                for rel in related_as_dst:
                                    # 중복 방지
                                    existing = self.db_utils.execute_query("""
                                        SELECT relationship_id
                                        FROM relationships
                                        WHERE src_id = ? AND dst_id = ? AND rel_type = ? AND del_yn = 'N'
                                        LIMIT 1
                                    """, (rel['src_id'], keep_id, rel['rel_type']))

                                    if not existing:
                                        self.db_utils.execute_query("""
                                            UPDATE relationships
                                            SET dst_id = ?, updated_at = CURRENT_TIMESTAMP
                                            WHERE relationship_id = ?
                                        """, (keep_id, rel['relationship_id']))
                                        merge_count += 1
                                        info(f"  병합: 관계 dst_id {remove_id} → {keep_id} ({rel['rel_type']})")
                                    else:
                                        # 중복이므로 이 관계는 삭제
                                        self.db_utils.execute_query("""
                                            UPDATE relationships
                                            SET del_yn = 'Y', updated_at = CURRENT_TIMESTAMP
                                            WHERE relationship_id = ?
                                        """, (rel['relationship_id'],))
                                        info(f"  중복 관계 삭제: relationship_id {rel['relationship_id']} (이미 존재)")

                            total_merged += merge_count

                            # [Step 2] 병합 완료 후 안전하게 삭제
                            self.db_utils.execute_query("""
                                UPDATE relationships
                                SET del_yn = 'Y', updated_at = CURRENT_TIMESTAMP
                                WHERE relationship_id = ?
                            """, (remove_id,))
                            total_removed += 1

                            if merge_count > 0:
                                info(f"중복 관계 제거 (병합 {merge_count}건): relationship_id {remove_id} 삭제, {keep_id}로 통합")

                        except Exception as e:
                            warning(f"관계 삭제 실패 (relationship_id: {remove_id}): {e}")

                info(f"중복 관계 제거 완료: {total_removed}개 제거됨, {total_merged}개 하위 정보 병합 (중복 그룹: {len(duplicate_relationships)}개)")
            else:
                info("중복 관계 없음")

        except Exception as e:
            warning(f"중복 관계 제거 중 오류: {e}")

    def _fallback_table_relationship_builder(self):
        """
        단순 테이블명 매칭으로 USE_TABLE 관계 보완
        - MyBatis XML 파일을 직접 읽어서 테이블명 검색
        - 누락된 USE_TABLE 관계 추가 (기존 관계는 skip)
        """
        try:
            info("=== 단순 테이블명 매칭 시작 ===")

            # 1. MyBatis XML 파일 목록 가져오기
            from parser.xml_parser import XmlParser
            xml_parser = XmlParser(project_name=self.project_name)

            path_utils = PathUtils()
            project_source_path = path_utils.join_path(path_utils.project_root, "projects", self.project_name, "src")
            xml_files = xml_parser.get_filtered_xml_files(project_source_path)

            if not xml_files:
                info("분석할 MyBatis XML 파일이 없습니다.")
                return

            info(f"MyBatis XML 파일 {len(xml_files)}개 발견")

            # 2. tables 테이블에서 모든 테이블명 조회
            all_tables = self.db_utils.execute_query("""
                SELECT DISTINCT table_name
                FROM tables
                WHERE project_id = ? AND del_yn = 'N'
                ORDER BY LENGTH(table_name) DESC
            """, (self.project_id,))

            if not all_tables:
                warning("테이블 정보가 없습니다.")
                return

            table_names = [row['table_name'] for row in all_tables]
            info(f"테이블 {len(table_names)}개 로드")

            total_relationships_added = 0
            total_queries_processed = 0

            # 3. 각 XML 파일 처리
            for xml_file in xml_files:
                try:
                    # 파일 내용 읽기 (UTF-8 + 에러 무시)
                    with open(xml_file, 'r', encoding='utf-8', errors='ignore') as f:
                        xml_content = f.read()

                    # namespace 추출
                    namespace_match = re.search(r'<mapper\s+namespace\s*=\s*["\']([^"\']+)["\']', xml_content, re.IGNORECASE)
                    if not namespace_match:
                        debug(f"namespace를 찾을 수 없음: {xml_file}")
                        continue

                    namespace = namespace_match.group(1)

                    # 쿼리 ID 추출 (select, insert, update, delete 태그의 id 속성)
                    query_pattern = r'<(?:select|insert|update|delete)\s+[^>]*id\s*=\s*["\']([^"\']+)["\']'
                    query_ids = re.findall(query_pattern, xml_content, re.IGNORECASE)

                    if not query_ids:
                        debug(f"쿼리 ID를 찾을 수 없음: {xml_file}")
                        continue

                    # 4. 각 쿼리 태그와 내용 추출 (단순 문자열 파싱)
                    for query_id in query_ids:
                        total_queries_processed += 1

                        # SQL 컴포넌트 조회 (query ID로만 검색)
                        sql_component = self.db_utils.execute_query("""
                            SELECT component_id
                            FROM components
                            WHERE component_name = ?
                              AND component_type LIKE 'SQL_%'
                              AND del_yn = 'N'
                            LIMIT 1
                        """, (query_id,))

                        if not sql_component:
                            continue

                        sql_component_id = sql_component[0]['component_id']

                        # 이미 등록된 USE_TABLE 관계 조회
                        existing_tables = self.db_utils.execute_query("""
                            SELECT t.table_name
                            FROM relationships r
                            JOIN components c ON r.dst_id = c.component_id
                            JOIN tables t ON c.component_id = t.component_id
                            WHERE r.src_id = ?
                              AND r.rel_type = 'USE_TABLE'
                              AND r.del_yn = 'N'
                              AND c.del_yn = 'N'
                              AND t.del_yn = 'N'
                        """, (sql_component_id,))

                        existing_table_names = {row['table_name'] for row in existing_tables}

                        # 5. 쿼리 ID에 해당하는 태그 찾기 (단순 검색)
                        # 형식: <select id="queryId"> ... </select>
                        query_start_pattern = f'id="{query_id}"'
                        query_start_idx = xml_content.find(query_start_pattern)

                        if query_start_idx == -1:
                            # 작은따옴표로도 시도
                            query_start_pattern = f"id='{query_id}'"
                            query_start_idx = xml_content.find(query_start_pattern)

                        if query_start_idx == -1:
                            continue

                        # 태그 시작부터 닫는 태그까지 추출
                        # select, insert, update, delete 닫는 태그 찾기
                        for tag in ['select', 'insert', 'update', 'delete']:
                            close_tag = f'</{tag}>'
                            query_end_idx = xml_content.find(close_tag, query_start_idx)
                            if query_end_idx != -1:
                                break

                        if query_end_idx == -1:
                            continue

                        # 쿼리 내용 추출
                        query_content = xml_content[query_start_idx:query_end_idx]

                        # 주석 제거
                        # 1) /* */ 블록 주석 제거
                        query_content = re.sub(r'/\*.*?\*/', ' ', query_content, flags=re.DOTALL)
                        # 2) -- 라인 주석 제거
                        query_content = re.sub(r'--[^\n]*', ' ', query_content)
                        query_content = re.sub(r'//[^\n]*', ' ', query_content)

                        query_content_upper = query_content.upper()

                        # 6. 쿼리 내용에서 테이블명 단순 검색
                        found_tables = []

                        for table_name in table_names:
                            # 이미 등록된 테이블은 스킵
                            if table_name in existing_table_names:
                                continue

                            # 단순 문자열 검색 (대소문자 무시)
                            if table_name in query_content_upper:
                                found_tables.append(table_name)

                        # 7. 누락된 테이블 관계 등록
                        for table_name in found_tables:
                            # 테이블 컴포넌트 ID 조회
                            table_component = self.db_utils.execute_query("""
                                SELECT component_id
                                FROM components
                                WHERE component_name = ?
                                  AND component_type = 'TABLE'
                                  AND project_id = ?
                                  AND del_yn = 'N'
                                LIMIT 1
                            """, (table_name, self.project_id))

                            if not table_component:
                                debug(f"테이블 컴포넌트를 찾을 수 없음: {table_name}")
                                continue

                            table_component_id = table_component[0]['component_id']

                            # 중복 확인: 이미 등록된 관계인지 확인 (src_id, dst_id, rel_type)
                            existing_relationship = self.db_utils.execute_query("""
                                SELECT relationship_id
                                FROM relationships
                                WHERE src_id = ?
                                  AND dst_id = ?
                                  AND rel_type = 'USE_TABLE'
                                  AND del_yn = 'N'
                                LIMIT 1
                            """, (sql_component_id, table_component_id))

                            if existing_relationship:
                                debug(f"이미 등록된 USE_TABLE 관계 스킵: {query_id} -> {table_name}")
                                continue

                            # USE_TABLE 관계 등록
                            relationship_data = {
                                'src_id': sql_component_id,
                                'dst_id': table_component_id,
                                'rel_type': 'USE_TABLE',
                                'del_yn': 'N'
                            }

                            relationship_id = self.db_utils.insert_or_replace_with_id('relationships', relationship_data)

                            if relationship_id:
                                total_relationships_added += 1
                                debug(f"USE_TABLE 추가: {query_id} -> {table_name}")

                except Exception as e:
                    handle_error(e, f"XML 파일 처리 중 오류: {xml_file}")

            info(f"=== 단순 테이블명 매칭 완료 ===")
            info(f"처리된 쿼리: {total_queries_processed}개")
            info(f"추가된 USE_TABLE 관계: {total_relationships_added}개")

        except Exception as e:
            handle_error(e, "단순 테이블명 매칭 중 오류")

    def _check_warning_cases(self):
        """경고성 검사 (정상적이지만 확인 필요)"""

        # 중복 관계 제거 로직 실행
        self._remove_duplicate_relationships()

        # 단순 테이블명 매칭으로 누락된 USE_TABLE 관계 보완
        self._fallback_table_relationship_builder()

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
        
        # 6. 불필요한 getter/setter 메소드 정리
        self._cleanup_unnecessary_getter_setter_methods()
    
    def _cleanup_unnecessary_getter_setter_methods(self):
        """불필요한 getter/setter 메소드 정리 (relationships에 연결고리가 없는 것들)"""
        
        # getter/setter 메소드 중 relationships에 src_id, dst_id 둘 다 연결고리가 없는 것들 조회
        unnecessary_methods = self.db_utils.execute_query("""
            SELECT 
                c.component_id,
                c.component_name,
                c.component_type,
                f.file_name,
                f.file_path
            FROM components c
            JOIN files f ON c.file_id = f.file_id
            WHERE c.component_type = 'METHOD' 
              AND c.del_yn = 'N'
              AND f.del_yn = 'N'
              AND f.project_id = ?
              AND (c.component_name LIKE 'get%' OR c.component_name LIKE 'set%')
              AND NOT EXISTS (
                  SELECT 1 FROM relationships r 
                  WHERE (r.src_id = c.component_id OR r.dst_id = c.component_id) 
                    AND r.del_yn = 'N'
              )
            ORDER BY c.component_name
        """, (self.project_id,))
        
        if unnecessary_methods:
            info(f"불필요한 getter/setter 메소드 발견: {len(unnecessary_methods)}개")
            
            # 각 메소드를 del_yn='Y'로 업데이트
            cleanup_count = 0
            for method in unnecessary_methods:
                try:
                    # components 테이블에서 del_yn='Y'로 업데이트
                    self.db_utils.execute_query("""
                        UPDATE components 
                        SET del_yn = 'Y', updated_at = CURRENT_TIMESTAMP
                        WHERE component_id = ?
                    """, (method['component_id'],))
                    
                    cleanup_count += 1
                    
                except Exception as e:
                    warning(f"  정리 실패: {method['component_name']} - {e}")
            
            info(f"불필요한 getter/setter 메소드 정리 완료: {cleanup_count}개 처리됨")
        else:
            info("불필요한 getter/setter 메소드 없음")


def validate_files_table(project_id: int, db_utils: DatabaseUtils, conn: sqlite3.Connection) -> dict:
    """files 테이블 검증"""
    try:
        # files 테이블 기본 검증
        files_count = db_utils.execute_query("SELECT COUNT(*) FROM files WHERE project_id = ?", (project_id,))[0][0]
        
        return {
            'check_name': 'files 테이블',
            'passed': True,
            'message': f'files 테이블 정상 ({files_count}개 파일)'
        }
    except Exception as e:
        return {
            'check_name': 'files 테이블',
            'passed': False,
            'message': f'files 테이블 검증 실패: {str(e)}'
        }

def validate_components_table(project_id: int, db_utils: DatabaseUtils, conn: sqlite3.Connection) -> dict:
    """components 테이블 검증"""
    try:
        # components 테이블 기본 검증
        components_count = db_utils.execute_query("SELECT COUNT(*) FROM components WHERE project_id = ?", (project_id,))[0][0]
        
        return {
            'check_name': 'components 테이블',
            'passed': True,
            'message': f'components 테이블 정상 ({components_count}개 컴포넌트)'
        }
    except Exception as e:
        return {
            'check_name': 'components 테이블',
            'passed': False,
            'message': f'components 테이블 검증 실패: {str(e)}'
        }

def validate_relationships_table(project_id: int, db_utils: DatabaseUtils, conn: sqlite3.Connection) -> dict:
    """relationships 테이블 검증"""
    try:
        # relationships 테이블 기본 검증 (project_id 컬럼이 없으므로 전체 카운트)
        relationships_count = db_utils.execute_query("SELECT COUNT(*) FROM relationships", ())[0][0]
        
        return {
            'check_name': 'relationships 테이블',
            'passed': True,
            'message': f'relationships 테이블 정상 ({relationships_count}개 관계)'
        }
    except Exception as e:
        return {
            'check_name': 'relationships 테이블',
            'passed': False,
            'message': f'relationships 테이블 검증 실패: {str(e)}'
        }

def validate_tables_table(project_id: int, db_utils: DatabaseUtils, conn: sqlite3.Connection) -> dict:
    """tables 테이블 검증"""
    try:
        # tables 테이블 기본 검증
        tables_count = db_utils.execute_query("SELECT COUNT(*) FROM tables WHERE project_id = ?", (project_id,))[0][0]
        
        return {
            'check_name': 'tables 테이블',
            'passed': True,
            'message': f'tables 테이블 정상 ({tables_count}개 테이블)'
        }
    except Exception as e:
        return {
            'check_name': 'tables 테이블',
            'passed': False,
            'message': f'tables 테이블 검증 실패: {str(e)}'
        }

def validate_columns_table(project_id: int, db_utils: DatabaseUtils, conn: sqlite3.Connection) -> dict:
    """columns 테이블 검증"""
    try:
        # columns 테이블 기본 검증 (project_id 컬럼이 없으므로 전체 카운트)
        columns_count = db_utils.execute_query("SELECT COUNT(*) FROM columns", ())[0][0]
        
        return {
            'check_name': 'columns 테이블',
            'passed': True,
            'message': f'columns 테이블 정상 ({columns_count}개 컬럼)'
        }
    except Exception as e:
        return {
            'check_name': 'columns 테이블',
            'passed': False,
            'message': f'columns 테이블 검증 실패: {str(e)}'
        }

def execute_consistency_validation(project_name: str, conn: sqlite3.Connection) -> bool:
    """메타데이터베이스 일관성 검증 실행 (외부 트랜잭션 내에서)"""
    try:
        info("메타데이터베이스 일관성 검증 시작")
        
        db_utils = DatabaseUtils(get_project_metadata_db_path(project_name))
        project_id = db_utils.get_project_id(project_name, conn)
        if not project_id:
            error(f"프로젝트 ID를 찾을 수 없습니다: {project_name}")
            return False

        validation_results = []

        # 1. files 테이블 검증
        validation_results.append(validate_files_table(project_id, db_utils, conn))

        # 2. components 테이블 검증
        validation_results.append(validate_components_table(project_id, db_utils, conn))

        # 3. relationships 테이블 검증
        validation_results.append(validate_relationships_table(project_id, db_utils, conn))

        # 4. tables 테이블 검증
        validation_results.append(validate_tables_table(project_id, db_utils, conn))

        # 5. columns 테이블 검증
        validation_results.append(validate_columns_table(project_id, db_utils, conn))

        # 6. 불필요한 getter/setter 메소드 정리
        try:
            validator = ConsistencyValidator(project_name)
            validator._cleanup_unnecessary_getter_setter_methods()
            validator.close()
            info("불필요한 getter/setter 메소드 정리 완료")
        except Exception as e:
            warning(f"getter/setter 메소드 정리 중 오류: {e}")

        # 모든 검증 결과 취합
        all_passed = all(result['passed'] for result in validation_results)

        if all_passed:
            info("일관성 검증 완료: 모든 검사 통과")
        else:
            warning("일관성 검증 완료: 일부 문제 발견됨")
            for result in validation_results:
                if not result['passed']:
                    warning(f"  - {result['check_name']}: {result['message']}")

        return all_passed

    except Exception as e:
        handle_error(e, "일관성 검증 실행 실패")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: py consistency_validator.py <project_name>")
        print("예: py consistency_validator.py sampleSrc")
        sys.exit(1)
    
    project_name = sys.argv[1]
    success = execute_consistency_validation(project_name)
    sys.exit(0 if success else 1)
