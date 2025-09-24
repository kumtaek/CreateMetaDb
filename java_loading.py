"""
심플 Java 로딩 모듈 - 4단계 처리
목표: files → classes → methods 순서로 components 테이블에 등록
관계 도출이 핵심 목표
"""

import os
import time
from typing import List, Dict, Any, Optional
from util import (
    DatabaseUtils, info, warning, debug, handle_error,
    get_project_source_path, get_project_metadata_db_path
)
from parser.simple_java_parser import SimpleJavaParser
from parser.simple_query_analyzer import SimpleQueryAnalyzer

class SimpleJavaLoader:
    """심플한 Java 파일 로더"""

    def __init__(self, project_name: str):
        """초기화"""
        self.project_name = project_name
        self.project_source_path = get_project_source_path(project_name)
        self.metadata_db_path = get_project_metadata_db_path(project_name)

        self.db_utils = None
        self.java_parser = SimpleJavaParser()
        self.simple_query_analyzer = SimpleQueryAnalyzer(project_name, self.metadata_db_path)

        # 통계
        self.stats = {
            'classes_extracted': 0,
            'methods_extracted': 0,
            'sql_queries_extracted': 0,
            'errors': 0
        }

    def execute_java_loading(self, project_id: int) -> bool:
        """Java 파일 로딩 실행"""
        try:
            info("Java 파일 로딩 시작 (심플 버전)")

            # 데이터베이스 초기화
            self.db_utils = DatabaseUtils(self.metadata_db_path)

            # Java 파일 수집
            java_files = []
            for root, dirs, files in os.walk(self.project_source_path):
                for file in files:
                    if file.endswith('.java'):
                        java_files.append(os.path.join(root, file))

            if not java_files:
                handle_error(Exception("Java 파일이 없습니다"), "Java 파일 스캔 실패")

            info(f"처리할 Java 파일 수: {len(java_files)}개")

            # Java 파일별 처리
            for java_file in java_files:
                try:
                    self._process_java_file(java_file, project_id)
                except Exception as e:
                    warning(f"Java 파일 처리 실패: {java_file} - {e}")
                    self.stats['errors'] += 1
                    continue

            # 통계 출력
            info("=== Java 로딩 완료 ===")
            info(f"처리된 클래스: {self.stats['classes_extracted']}개")
            info(f"처리된 메서드: {self.stats['methods_extracted']}개")
            info(f"추출된 쿼리: {self.stats.get('sql_queries_extracted', 0)}개")
            info(f"오류: {self.stats['errors']}개")

            return True

        except Exception as e:
            handle_error(e, "Java 로딩 실행 실패")
            return False

    def _process_java_file(self, java_file: str, project_id: int):
        """개별 Java 파일 처리"""
        # 1. 파일 ID 조회
        file_id = self._get_file_id(java_file)
        if not file_id:
            debug(f"파일 ID를 찾을 수 없음: {java_file}")
            return

        # 2. Java 파일 파싱 (public/protected만)
        debug(f"Java 파일 파싱: {java_file}")
        parse_result = self.java_parser.parse_java_file(java_file)

        # 3. 클래스 컴포넌트 먼저 등록하고 class_id 수집
        class_id_map = {}  # class_name -> component_id 매핑

        for cls in parse_result['classes']:
            class_comp = {
                'project_id': project_id,
                'file_id': file_id,
                'component_name': cls['name'],
                'component_type': 'CLASS',
                'layer_type': 'UNKNOWN',
                'line_number': cls['line'],
                'has_error': 'N',
                'error_message': None,
                'parent_id': None
            }
            class_id = self._upsert_component(class_comp)
            if class_id:
                class_id_map[cls['name']] = class_id
                self.stats['classes_extracted'] += 1

        # 4. 메서드 컴포넌트를 parent_id와 함께 등록
        for method in parse_result['methods']:
            parent_class_id = class_id_map.get(method['class'])
            method_comp = {
                'project_id': project_id,
                'file_id': file_id,
                'component_name': f"{method['class']}.{method['name']}",
                'component_type': 'METHOD',
                'layer_type': 'UNKNOWN',
                'line_number': method['line'],
                'has_error': 'N',
                'error_message': None,
                'parent_id': parent_class_id
            }
            if self._upsert_component(method_comp):
                self.stats['methods_extracted'] += 1

        debug(f"컴포넌트 등록 완료: 클래스 {len(parse_result['classes'])}개, 메서드 {len(parse_result['methods'])}개")

        # 4. 쿼리 분석 (3단계 파이프라인)
        try:
            query_analysis = self.simple_query_analyzer.analyze_java_file(java_file, file_id)
            if query_analysis and query_analysis.get('queries'):
                self.stats['sql_queries_extracted'] += len(query_analysis['queries'])
        except Exception as e:
            debug(f"쿼리 분석 실패: {java_file} - {e}")

    def _get_file_id(self, file_path: str) -> Optional[int]:
        """파일 경로로 file_id 조회"""
        try:
            # 상대 경로로 변환
            relative_path = os.path.relpath(file_path, self.project_source_path)
            relative_path = relative_path.replace('\\', '/')  # Windows 경로 처리

            query = "SELECT file_id FROM files WHERE file_path = ?"
            result = self.db_utils.execute_query(query, (relative_path,))

            return result[0]['file_id'] if result else None

        except Exception as e:
            debug(f"파일 ID 조회 실패: {file_path} - {e}")
            return None

    def _upsert_component(self, comp_data: Dict) -> Optional[int]:
        """컴포넌트 UPSERT (있으면 업데이트, 없으면 생성) - component_id 반환"""
        try:
            # 기존 컴포넌트 확인
            check_query = """
                SELECT component_id FROM components
                WHERE project_id = ? AND file_id = ? AND component_name = ? AND component_type = ?
            """
            existing = self.db_utils.execute_query(check_query, (
                comp_data['project_id'],
                comp_data['file_id'],
                comp_data['component_name'],
                comp_data['component_type']
            ))

            if existing:
                # 업데이트 (parent_id 포함)
                update_query = """
                    UPDATE components
                    SET line_start = ?, layer = ?, has_error = ?, error_message = ?, parent_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE component_id = ?
                """
                self.db_utils.execute_query(update_query, (
                    comp_data['line_number'],
                    comp_data['layer_type'],
                    comp_data['has_error'],
                    comp_data['error_message'],
                    comp_data.get('parent_id'),
                    existing[0]['component_id']
                ))
                debug(f"컴포넌트 업데이트: {comp_data['component_name']}")
                return existing[0]['component_id']
            else:
                # 생성 (parent_id 포함)
                insert_query = """
                    INSERT INTO components (
                        project_id, file_id, component_name, component_type,
                        line_start, layer, has_error, error_message, parent_id, hash_value, created_at, updated_at, del_yn
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'N')
                """

                # 간단한 해시값 생성
                import hashlib
                hash_value = hashlib.md5(f"{comp_data['component_name']}{comp_data['component_type']}".encode()).hexdigest()

                self.db_utils.execute_query(insert_query, (
                    comp_data['project_id'],
                    comp_data['file_id'],
                    comp_data['component_name'],
                    comp_data['component_type'],
                    comp_data['line_number'],
                    comp_data['layer_type'],
                    comp_data['has_error'],
                    comp_data['error_message'],
                    comp_data.get('parent_id'),
                    hash_value
                ))
                debug(f"컴포넌트 생성: {comp_data['component_name']}")

                # 새로 생성된 component_id 조회
                new_component = self.db_utils.execute_query(check_query, (
                    comp_data['project_id'],
                    comp_data['file_id'],
                    comp_data['component_name'],
                    comp_data['component_type']
                ))
                return new_component[0]['component_id'] if new_component else None

        except Exception as e:
            warning(f"컴포넌트 UPSERT 실패: {comp_data.get('component_name', 'unknown')} - {e}")
            return None


# 편의 함수
def load_java_files_simple(project_name: str, project_id: int) -> bool:
    """심플한 Java 파일 로딩 실행"""
    loader = SimpleJavaLoader(project_name)
    return loader.execute_java_loading(project_id)