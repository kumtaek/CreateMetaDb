"""
Java 로딩 모듈 - 새로운 구조
목표: Java 파일에서 클래스와 메서드를 추출하여 components 테이블에 등록
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional
from util import (
    DatabaseUtils, PathUtils, info, warning, debug, handle_error,
    get_project_source_path, get_project_metadata_db_path, HashUtils
)
from parser.java_parser import JavaParser


class JavaLoader:
    """Java 파일 로더 - 클래스와 메서드 추출"""

    def __init__(self, project_name: str, conn: sqlite3.Connection):
        """초기화"""
        self.project_name = project_name
        self.conn = conn
        self.project_source_path = get_project_source_path(project_name)
        
        self.path_utils = PathUtils()
        self.db_utils = DatabaseUtils(get_project_metadata_db_path(project_name))
        self.java_parser = JavaParser()
        
        self.stats = {
            'java_files_processed': 0,
            'classes_extracted': 0,
            'methods_extracted': 0,
            'errors': 0
        }

    def execute_java_loading(self, project_id: int) -> bool:
        """Java 파일 로딩 실행 (외부 트랜잭션 내에서)"""
        try:
            info("Java 파일 로딩 시작 (새로운 구조)")
            
            # Java 파일 목록 수집
            java_files = self._get_java_files()
            if not java_files:
                warning("분석할 Java 파일이 없습니다.")
                return True

            info(f"처리할 Java 파일 수: {len(java_files)}개")

            # 각 Java 파일 처리
            for java_file in java_files:
                try:
                    self._process_java_file(java_file, project_id)
                    self.stats['java_files_processed'] += 1
                except Exception as e:
                    handle_error(e, f"Java 파일 처리 실패: {java_file}")
                    self.stats['errors'] += 1

            info("=== Java 로딩 완료 ===")
            info(f"처리된 Java 파일: {self.stats['java_files_processed']}개")
            info(f"추출된 클래스: {self.stats['classes_extracted']}개")
            info(f"추출된 메서드: {self.stats['methods_extracted']}개")
            info(f"오류 발생: {self.stats['errors']}개")
            
            return True

        except Exception as e:
            handle_error(e, "Java 로딩 실행 실패")
            return False

    def _get_java_files(self) -> List[str]:
        """Java 파일 목록 수집"""
        java_files = []
        try:
            for root, _, files in os.walk(self.project_source_path):
                for file in files:
                    if file.endswith('.java'):
                        java_files.append(self.path_utils.join_path(root, file))
            return java_files
        except Exception as e:
            handle_error(e, "Java 파일 목록 수집 실패")
            return []

    def _process_java_file(self, java_file: str, project_id: int):
        """개별 Java 파일 처리"""
        file_id = self._get_file_id(java_file)
        if not file_id:
            debug(f"파일 ID를 찾을 수 없음: {java_file}")
            return

        try:
            debug(f"Java 파일 파싱: {java_file}")
            parse_result = self.java_parser.parse_java_file(java_file)
            
            if not parse_result.get('classes'):
                warning(f"클래스가 추출되지 않았습니다: {java_file}")
                return

            # 클래스 처리
            class_id_map = {}
            for cls in parse_result.get('classes', []):
                class_id = self._upsert_class(cls, project_id, file_id)
                if class_id:
                    class_id_map[cls['name']] = class_id
                    self.stats['classes_extracted'] += 1

            # 메서드 처리
            for method in parse_result.get('methods', []):
                parent_class_id = class_id_map.get(method['class'])
                if parent_class_id:
                    method_comp = {
                        'project_id': project_id,
                        'file_id': file_id,
                        'component_name': method['name'],
                        'component_type': 'METHOD',
                        'parent_id': parent_class_id,
                        'hash_value': HashUtils().generate_content_hash(method['name'])
                    }
                    if self._upsert_component(method_comp):
                        self.stats['methods_extracted'] += 1

        except Exception as e:
            handle_error(e, f"Java 파일 처리 실패: {java_file}")

    def _get_file_id(self, file_path: str) -> Optional[int]:
        """파일 경로로 file_id 조회"""
        try:
            # 파일 경로를 디렉토리와 파일명으로 분리
            file_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            
            # 프로젝트 루트 기준으로 상대 경로 계산
            relative_dir = os.path.relpath(file_dir, self.project_source_path)
            
            # 프로젝트 루트의 상위 디렉토리 기준 절대 경로 생성
            project_root_parent = os.path.dirname(os.path.dirname(self.project_source_path))
            absolute_dir = os.path.join(project_root_parent, relative_dir)
            
            # 크로스플랫폼 호환성을 위해 모든 경로 구분자를 /로 통일
            absolute_dir = absolute_dir.replace('\\', '/')
            
            # 절대 경로와 파일명으로 조회
            query = "SELECT file_id FROM files WHERE file_path = ? AND file_name = ? AND project_id = (SELECT project_id FROM projects WHERE project_name = ?)"
            result = self.db_utils.execute_query(query, (absolute_dir, file_name, self.project_name), conn=self.conn)
            return result[0]['file_id'] if result else None
        except Exception as e:
            handle_error(e, f"파일 ID 조회 실패: {file_path}")
            return None

    def _upsert_class(self, class_data: Dict[str, Any], project_id: int, file_id: int) -> Optional[int]:
        """클래스 컴포넌트 저장 또는 업데이트"""
        try:
            component_data = {
                'project_id': project_id,
                'file_id': file_id,
                'component_name': class_data['name'],
                'component_type': 'CLASS',
                'parent_id': None,
                'hash_value': HashUtils().generate_content_hash(class_data['name'])
            }
            
            component_id = self.db_utils.insert_or_replace('components', component_data)
            
            return component_id
            
        except Exception as e:
            handle_error(e, f"클래스 저장 실패: {class_data['name']}")
            return None

    def _upsert_component(self, component_data: Dict[str, Any]) -> Optional[int]:
        """컴포넌트 저장 또는 업데이트"""
        try:
            component_id = self.db_utils.insert_or_replace('components', component_data)
            return component_id
        except Exception as e:
            handle_error(e, f"컴포넌트 저장 실패: {component_data.get('component_name', 'Unknown')}")
            return None

    def get_statistics(self) -> Dict[str, int]:
        """통계 반환"""
        return self.stats.copy()
