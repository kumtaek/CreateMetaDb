"""
범용 프론트엔드 로딩 모듈
- JSP, JSX, Vue, TS, JS, HTML 파일에서 컴포넌트 추출 및 관계 분석
- 기존 JSP 로딩 엔진을 범용화하여 모든 프론트엔드 파일 타입 지원
- 메모리 최적화 (스트리밍 처리)
- 데이터베이스 저장 및 통계 관리

USER RULES:
- 하드코딩 금지: path_utils.get_parser_config_path("frontend") 사용 (크로스플랫폼 대응)
- 파싱 에러 처리: has_error='Y', error_message 저장 후 계속 실행
- 시스템 에러 처리: handle_error() 공통함수 사용
- 공통함수 사용: util 모듈 활용
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional
import time
import datetime
import datetime
from util import (
    DatabaseUtils, PathUtils, HashUtils, ValidationUtils,
    build_api_identity_key, format_api_component_name,
    app_logger, info, error, debug, warning, handle_error,
    get_project_source_path, get_project_metadata_db_path, get_log_file_path
)
from util.file_context import get_file_context_manager
from parser.frontend_parser import FrontendParser
from util.base_loading_engine import BaseLoadingEngine
from util.progress_utils import ProgressTracker


class FrontendLoadingEngine(BaseLoadingEngine):
    """범용 프론트엔드 로딩 엔진 - JSP, JSX, Vue, TS, JS, HTML 지원"""

    def __init__(self, project_name: str, conn: sqlite3.Connection):
        """
        프론트엔드 로딩 엔진 초기화

        Args:
            project_name: 프로젝트명
            conn: 외부에서 주입된 데이터베이스 연결 객체
        """
        super().__init__(project_name, conn)
        self.frontend_parser = FrontendParser(project_name=project_name)
        self.hash_utils = HashUtils()
        self.current_file_id = None
        self.file_context = get_file_context_manager()
        self.stats = {
            'total_files': 0, 'processed_files': 0, 'error_files': 0,
            'jsp_files': 0, 'jsx_files': 0, 'vue_files': 0, 'ts_files': 0, 'tsx_files': 0,
            'js_files': 0, 'html_files': 0, 'components_created': 0,
            'api_calls_found': 0, 'relationships_created': 0
        }
        self._debug_last_ts: Dict[str, float] = {}  # 디버그 로그 스로틀링(키별)
        self.supported_extensions = {'.jsp': 'JSP', '.jsx': 'JSX', '.vue': 'VUE', '.ts': 'TS', '.tsx': 'TSX', '.js': 'JS', '.html': 'HTML'}
        info(f"프론트엔드 로딩 엔진 초기화 완료: {project_name}")

    def _log_debug(self, key: str, message: str, interval: float = 1.0) -> None:
        """
        디버그 로그를 지정된 주기로만 콘솔/파일에 출력하고,
        스로틀된 경우에도 로그 파일에는 모두 기록되도록 처리합니다.
        """
        now = time.time()
        last_ts = self._debug_last_ts.get(key, 0.0)
        if now - last_ts >= interval:
            app_logger.info(message)  # 표준 핸들러(콘솔+파일)
            self._debug_last_ts[key] = now
        else:
            self._write_logfile_only(message)

    def _write_logfile_only(self, message: str) -> None:
        """스로틀된 로그를 파일에만 기록"""
        try:
            log_path = get_log_file_path()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"{timestamp} - INFO - {message}\n")
        except Exception:
            # 파일 기록 실패는 조용히 무시 (핵심 로직 영향 방지)
            pass

    def execute_frontend_loading(self) -> bool:
        """프론트엔드 파일 로딩 실행 (외부 트랜잭션 내에서)"""
        try:
            info("=== 프론트엔드 파일 로딩 시작 ===")
            project_id = self.get_project_id()
            if not project_id:
                raise Exception("프로젝트 ID를 찾을 수 없음")

            frontend_files = self._get_frontend_files(project_id)
            if not frontend_files:
                info("처리할 프론트엔드 파일이 없음")
                return True

            self.stats['total_files'] = len(frontend_files)
            info(f"총 {len(frontend_files)}개 프론트엔드 파일 발견")

            progress_tracker = ProgressTracker(
                total=len(frontend_files),
                desc="Frontend Loading",
                unit="file",
                log_interval_sec=1.0
            )
            start_time = time.time()
            try:
                for index, file_info in enumerate(frontend_files, start=1):
                    try:
                        self._process_frontend_file(file_info, project_id)
                        self.stats['processed_files'] += 1
                    except Exception as e:
                        self.stats['error_files'] += 1
                        handle_error(e, f"프론트엔드 파일 처리 실패: {full_file_path}")
                    elapsed = time.time() - start_time
                    progress_tracker.update(
                        current=index,
                        log_message=(
                            f"[FRONTEND FILE PROGRESS] {index}/{len(frontend_files)} "
                            f"file={file_info.get('file_name')} "
                            f"elapsed={elapsed:.1f}s"
                        )
                    )
            finally:
                progress_tracker.close()

            self._print_statistics()
            info("=== 프론트엔드 파일 로딩 완료 ===")
            return True
        except Exception as e:
            handle_error(e, "프론트엔드 파일 로딩 실행 실패")
            return False



    def _get_frontend_files(self, project_id: int) -> List[Dict[str, Any]]:
        """프론트엔드 파일 목록 조회"""
        frontend_types = list(self.supported_extensions.values())
        placeholders = ','.join(['?' for _ in frontend_types])
        query = f"SELECT file_id, file_name, file_path, file_type FROM files WHERE project_id = ? AND file_type IN ({placeholders}) AND del_yn = 'N' ORDER BY file_type, file_name"
        params = [project_id] + frontend_types
        return self.db_utils.execute_query(query, params, conn=self.conn)

    def _process_frontend_file(self, file_info: Dict[str, Any], project_id: int):
        """개별 프론트엔드 파일 처리"""
        self.current_file_id = file_info['file_id']
        path_parts = [self.project_source_path]
        if file_info.get('file_path'):
            path_parts.append(file_info['file_path'])
        path_parts.append(file_info['file_name'])
        full_file_path = os.path.join(*path_parts)
        if not os.path.exists(full_file_path):
            warning(f"파일이 존재하지 않음: {full_file_path}")
            return

        # 파일 컨텍스트 push (전역 추적)
        self.file_context.push(
            project_name=self.project_name,
            project_id=project_id,
            file_id=file_info['file_id'],
            file_path=file_info.get('file_path', ''),
            file_name=file_info.get('file_name', ''),
            file_type=file_info.get('file_type', ''),
            source_type='FRONTEND',
            stage='Frontend'
        )

        try:
            parse_result = self.frontend_parser.parse_frontend_file(full_file_path, file_info['file_type'])
            if parse_result.get('has_error') == 'Y':
                warning(f"파싱 에러: {file_info['file_name']} - {parse_result.get('error_message')}")
                return
        except Exception as e:
            handle_error(e, f"프론트엔드 파일 파싱 실패: {file_info['file_name']}")
            return

        try:
            if parse_result.get('components'):
                self._save_frontend_components_to_database(parse_result['components'], project_id, file_info['file_type'])
            
            if parse_result.get('api_calls'):
                self._save_api_call_relationships_to_database(parse_result['api_calls'], project_id)
        except Exception as e:
            handle_error(e, f"프론트엔드 데이터 저장 실패: {file_info['file_name']}")
        finally:
            # 컨텍스트 복원
            self.file_context.pop()

        self.stats['api_calls_found'] += len(parse_result.get('api_calls', []))
        self.stats['components_created'] += len(parse_result.get('components', []))

    def _save_frontend_components_to_database(self, components: List[Dict[str, Any]], project_id: int, file_type: str):
        """프론트엔드 컴포넌트를 데이터베이스에 저장"""
        try:
            for component in components:
                component_data = {
                    'project_id': project_id, 'file_id': self.current_file_id,
                    'component_name': component['component_name'], 'component_type': file_type.upper(),
                    'layer': 'FRONTEND', 'line_start': component.get('line_start', 1),
                    'line_end': component.get('line_end', 1), 'hash_value': component.get('hash_value', '-'),
                    'del_yn': 'N', 'has_error': 'N', 'error_message': None, 'parent_id': None
                }
                try:
                    self.db_utils.insert_or_replace('components', component_data)
                except Exception as e:
                    handle_error(e, f"컴포넌트 저장 실패: {component_data}")
                self.stats['components_created'] += 1
        except Exception as e:
            handle_error(e, f"프론트엔드 컴포넌트 저장 실패: {file_type}")

    def _save_api_call_relationships_to_database(self, api_calls: List[Dict[str, Any]], project_id: int):
        """API 호출 관계를 데이터베이스에 저장"""
        try:
            frameworks_in_file = {call.get('framework') for call in api_calls if call.get('framework')}

            for api_call in api_calls:
                try:
                    api_url_id = self._find_or_create_api_url_component(api_call, project_id)
                    if not api_url_id: continue

                    # 수정 필요: JSP만이 아닌 모든 프론트엔드 파일 타입 허용
                    file_type = api_call.get('file_type', '').upper()
                    self._log_debug("call_api_attempt", f"[DEBUG] CALL_API 관계 생성 시도: file_type={file_type}, file_name={api_call['file_name']}, api_url_id={api_url_id}")
                    if file_type in ['JSP', 'JSX', 'VUE', 'TS', 'TSX', 'JS', 'HTML']:
                        jsp_component_id = self._find_frontend_component_id(api_call['file_name'], project_id)
                        if jsp_component_id:
                            self._log_debug("call_api_created", f"[DEBUG] CALL_API 관계 생성: jsp_component_id={jsp_component_id} -> api_url_id={api_url_id}")
                            self._create_relationship(jsp_component_id, api_url_id, 'CALL_API')
                        else:
                            self._log_debug("call_api_missing", "[DEBUG] CALL_API 관계 생성 실패: jsp_component_id를 찾을 수 없음")
                    else:
                        self._log_debug("call_api_skip", f"[DEBUG] CALL_API 관계 생성 스킵: 지원하지 않는 파일 타입={file_type}")
                except Exception as e:
                    handle_error(e, f"API 호출 관계 저장 실패: {api_call}")

            if frameworks_in_file and self.current_file_id:
                try:
                    for framework in frameworks_in_file:
                        self.db_utils.update_file_frameworks(self.current_file_id, framework, conn=self.conn)
                except Exception as e:
                    handle_error(e, f"프레임워크 정보 업데이트 실패: {frameworks_in_file}")
        except Exception as e:
            handle_error(e, "API 호출 관계 저장 실패")

    def _find_or_create_api_url_component(self, api_call: Dict[str, Any], project_id: int) -> Optional[int]:
        """Find or create the API_URL component using the new naming convention."""
        api_url = (api_call.get('api_url') or '').strip()
        http_method = api_call.get('http_method')
        if not api_url:
            return None

        identity_key = build_api_identity_key(api_url, http_method)
        identity_hash = self.hash_utils.generate_content_hash(identity_key)

        existing = self.db_utils.get_component_by_hash(project_id, 'API_URL', identity_hash)
        self._log_debug("api_match", f"[DEBUG] API_URL 매칭 시도: identity_key={identity_key}, existing={existing is not None}")
        if existing:
            component_id = existing['component_id']
            # 프론트엔드에서 발견 시 file_id를 프론트 파일로 우선 갱신
            if self.current_file_id and existing.get('file_id') != self.current_file_id:
                try:
                    self.db_utils.update_component_file_id(component_id, self.current_file_id, conn=self.conn)
                except Exception as e:
                    handle_error(e, f"API_URL file_id 갱신 실패: {component_id}")
            self._log_debug("api_match", f"[DEBUG] API_URL 매칭 성공: component_id={component_id}, existing_file_id={existing.get('file_id')}, current_file_id={self.current_file_id}")
            return component_id

        component_name = format_api_component_name(http_method, api_url, api_url)
        if not component_name:
            return None

        component_data = {
            'project_id': project_id, 'file_id': self.current_file_id,
            'component_name': component_name, 'component_type': 'API_URL',
            'layer': 'API_ENTRY', 'line_start': api_call.get('line_number', 1),
            'line_end': api_call.get('line_number', 1), 'hash_value': identity_hash,
            'del_yn': 'N', 'has_error': 'N', 'error_message': None, 'parent_id': None
        }
        try:
            return self.db_utils.insert_or_replace_with_id('components', component_data, conn=self.conn)
        except Exception as e:
            handle_error(e, f"API_URL 컴포넌트 등록 실패: {component_data}")
            return None

    def _find_frontend_component_id(self, file_name: str, project_id: int) -> Optional[int]:
        """프론트엔드 컴포넌트 ID 찾기"""
        try:
            # 파일명에서 확장자 제거 (예: JpaApiService.js -> JpaApiService)
            base_name = file_name
            if '.' in file_name:
                base_name = file_name.rsplit('.', 1)[0]
            
            query = "SELECT component_id FROM components WHERE project_id = ? AND component_name = ? AND file_id = ? AND del_yn = 'N'"
            result = self.db_utils.execute_query(query, (project_id, base_name, self.current_file_id), conn=self.conn)
            component_id = result[0]['component_id'] if result else None
            self._log_debug("find_frontend_component", f"[DEBUG] _find_frontend_component_id: file_name={file_name}, base_name={base_name}, project_id={project_id}, current_file_id={self.current_file_id}, found_component_id={component_id}")
            return component_id
        except Exception as e:
            handle_error(e, f"프론트엔드 컴포넌트 ID 조회 실패: {file_name}")
            return None

    def _create_relationship(self, src_id: int, dst_id: int, rel_type: str):
        """관계 생성"""
        try:
            self._log_debug("create_relationship", f"[DEBUG] _create_relationship 시도: src_id={src_id}, dst_id={dst_id}, rel_type={rel_type}")
            if self.db_utils.insert_relationship(src_id, dst_id, rel_type):
                self.stats['relationships_created'] += 1
                self._log_debug("create_relationship", f"[DEBUG] _create_relationship 성공: src_id={src_id} -> dst_id={dst_id} ({rel_type})")
            else:
                self._log_debug("create_relationship", f"[DEBUG] _create_relationship 기존재 스킵: src_id={src_id} -> dst_id={dst_id} ({rel_type})")
        except Exception as e:
            handle_error(e, f"관계 생성 실패: {src_id} -> {dst_id} ({rel_type})")

    def _print_statistics(self) -> None:
        """통계 정보 출력"""
        info("=== 프론트엔드 파일 로딩 통계 ===")
        # ... (rest of the method is unchanged)

def execute_frontend_loading(project_name: str, conn: sqlite3.Connection) -> bool:
    """프론트엔드 파일 로딩 실행 함수"""
    try:
        engine = FrontendLoadingEngine(project_name, conn)
        return engine.execute_frontend_loading()
    except Exception as e:
        handle_error(e, "프론트엔드 로딩 실행 실패")
        return False
