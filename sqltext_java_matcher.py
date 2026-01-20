"""
FramePlus Java 파일에서 sqltext SQL ID 문자열을 검색해 CALL_QUERY 관계를 생성하는 모듈.
- component_type LIKE 'SQL%' AND layer='SQL_FROM_SQLTEXT'인 컴포넌트 대상.
- 단순 문자열 매칭(대소문자 구분)으로 누락을 최소화한다.
"""

import os
import time
import re
from typing import List, Dict, Optional

from util import (
    DatabaseUtils, FileUtils, PathUtils, HashUtils,
    app_logger, info, debug, warning, handle_error,
    get_project_source_path
)
from util.progress_utils import ProgressTracker


class SqlTextJavaMatcher:
    """sqltext SQL ID를 Java 파일에서 검색해 CALL_QUERY 관계를 생성한다."""

    def __init__(self, project_name: str, conn):
        self.project_name = project_name
        self.conn = conn
        self.path_utils = PathUtils()
        self.db_utils = DatabaseUtils(self.path_utils.get_project_metadata_db_path(project_name))
        self.project_src_root = get_project_source_path(project_name)
        self._warn_counters = {"method_missing": 0}
        self._last_warn_ts = {}
        self._sqltext_scan_tracker = None
        self._sqltext_scan_total = 0
        self._sqltext_scan_done = 0
        self._sqltext_total_matched = 0

    def execute(self) -> bool:
        """매칭 실행"""
        try:
            project_id = self.db_utils.get_project_id(self.project_name, self.conn)
            if not project_id:
                handle_error(Exception("프로젝트 ID 조회 실패"), f"프로젝트 ID를 찾을 수 없습니다: {self.project_name}")
                return False

            sql_components = self._load_sqltext_components(project_id)
            if not sql_components:
                info("SQLTEXT 컴포넌트가 없어 추가 매칭 대상이 없습니다")
                return True

            java_files = self._load_java_files(project_id)
            if not java_files:
                info("Java 파일이 없어 sqltext 매칭 대상이 없습니다")
                return True

            total_matches = 0
            total_relationships = 0
            self._sqltext_scan_total = len(java_files) * len(sql_components)
            self._sqltext_scan_done = 0
            self._sqltext_total_matched = 0
            if self._sqltext_scan_total > 0:
                self._sqltext_scan_tracker = ProgressTracker(
                    total=self._sqltext_scan_total,
                    desc="SQLTEXT MATCH SCAN",
                    unit="scan",
                    log_interval_sec=3.0,
                    leave=True
                )

            progress_tracker = ProgressTracker(
                total=len(java_files),
                desc="SQLTEXT-JAVA",
                unit="file",
                log_interval_sec=3.0,
                leave=True
            )
            try:
                for index, file_info in enumerate(java_files, start=1):
                    matched = self._process_java_file(file_info, sql_components, project_id)
                    total_matches += matched['matched_sql']
                    self._sqltext_total_matched = total_matches
                    total_relationships += matched['relationships_created']
                    progress_tracker.update(
                        current=index,
                        log_message=None
                    )
            finally:
                progress_tracker.close()
                if self._sqltext_scan_tracker:
                    self._sqltext_scan_tracker.update(
                        current=self._sqltext_scan_done,
                        log_message=(
                            f"[SQLTEXT MATCH BATCH] scanned={self._sqltext_scan_done}/{self._sqltext_scan_total} "
                            f"matched={self._sqltext_total_matched}"
                        ),
                        force_log=True
                    )
                    self._sqltext_scan_tracker.close()
                    self._sqltext_scan_tracker = None

            info(f"sqltext-Java 매칭 완료: 파일 {len(java_files)}개, 매칭된 SQL ID {total_matches}개, 생성/유지된 관계 {total_relationships}개")
            if self._warn_counters.get("method_missing"):
                info(f"sqltext 매칭 스킵(메서드 없음): {self._warn_counters['method_missing']}건")
            return True
        except Exception as e:
            handle_error(e, "sqltext-Java 매칭 실행 실패")
            return False

    def _load_sqltext_components(self, project_id: int) -> List[Dict]:
        """FramePlus sqltext에서 생성된 SQL_QUERY 컴포넌트 목록 로드"""
        try:
            query = """
                SELECT component_id, component_name
                FROM components
                WHERE project_id = ?
                  AND component_type LIKE 'SQL%'
                  AND layer IN ('SQL_FROM_SQLTEXT', 'QUERY_FROM_SQLTEXT')
                  AND del_yn = 'N'
            """
            rows = self.db_utils.execute_query(query, (project_id,), conn=self.conn)
            return rows or []
        except Exception as e:
            handle_error(e, "SQLTEXT 컴포넌트 로드 실패")
            return []

    def _load_java_files(self, project_id: int) -> List[Dict]:
        """files 테이블에서 Java 파일 목록 로드"""
        try:
            query = """
                SELECT file_id, file_name, file_path
                FROM files
                WHERE project_id = ?
                  AND file_type = 'JAVA'
                  AND del_yn = 'N'
            """
            return self.db_utils.execute_query(query, (project_id,), conn=self.conn)
        except Exception as e:
            handle_error(e, "Java 파일 목록 로드 실패")
            return []

    def _process_java_file(self, file_info: Dict, sql_components: List[Dict], project_id: int) -> Dict[str, int]:
        """단일 Java 파일을 처리하여 CALL_QUERY 관계를 생성"""
        matched_sql = 0
        relationships_created = 0
        file_path_parts = [self.project_src_root]
        if file_info.get('file_path'):
            file_path_parts.append(file_info['file_path'])
        file_path_parts.append(file_info['file_name'])
        full_path = os.path.join(*file_path_parts)
        file_stem = os.path.splitext(file_info['file_name'])[0]

        if not os.path.exists(full_path):
            handle_error(Exception("Java 파일 미존재"), f"Java 파일이 존재하지 않습니다: {full_path}")
            return {'matched_sql': 0, 'relationships_created': 0}

        content = FileUtils.read_file(full_path)
        if content is None:
            handle_error(Exception("Java 파일 읽기 실패"), f"Java 파일을 읽을 수 없습니다: {full_path}")
            return {'matched_sql': 0, 'relationships_created': 0}
        # 주석 제거 후 대소문자 구분 매칭을 위해 원문 그대로 사용
        content = self._remove_java_comments(content)

        # execute/executeBatch 호출 흔적이 없으면 스킵 (공백 제거 후 확인)
        compact = self._remove_whitespace(content)
        has_execute = ".execute(" in compact or ".executeBatch(" in compact

        # 파일 내 METHOD 컴포넌트 조회
        method_component_map = self._get_method_component_map(project_id, file_info['file_id'])
        if not method_component_map:
            self._log_method_missing(full_path)

        sql_id_set = {comp['component_name'] for comp in sql_components if comp.get('component_name')}
        sql_comp_map = {comp['component_name']: comp['component_id'] for comp in sql_components if comp.get('component_name')}
        matched_sql_ids = set()

        # 1) 메서드 단위 매칭 (execute/executeBatch 인자 추적)
        if has_execute:
            const_map = self._extract_constant_string_map(content, sql_id_set)
            method_blocks = self._extract_method_blocks(content)
            for method in method_blocks:
                method_name = method['name']
                method_body = method['body']
                compact_body = self._remove_whitespace(method_body)
                if ".execute(" not in compact_body and ".executeBatch(" not in compact_body:
                    continue
                local_map = self._extract_local_string_map(method_body, sql_id_set)
                method_sql_ids = self._extract_sql_ids_from_execute_calls(method_body, local_map, const_map, sql_id_set)
                if not method_sql_ids:
                    continue

                method_id = method_component_map.get(method_name)
                if method_id is None:
                    class_id = self._ensure_class_record(project_id, file_info['file_id'], file_stem)
                    method_id = self._ensure_method_component(project_id, file_info['file_id'], method_name, class_id)
                    if method_id:
                        method_component_map[method_name] = method_id
                if not method_id:
                    continue

                for sql_id in method_sql_ids:
                    sql_comp_id = sql_comp_map.get(sql_id)
                    if not sql_comp_id:
                        continue
                    if sql_id not in matched_sql_ids:
                        matched_sql += 1
                        matched_sql_ids.add(sql_id)
                    if self._insert_call_query_relationship(method_id, sql_comp_id):
                        relationships_created += 1
                debug(f"sqltext 매칭(메서드): {file_info['file_name']} {method_name} -> {sorted(list(method_sql_ids))}")

        # 2) 보조 매칭: 메서드 기반 SQL ID 인식이 없을 때만 단순 문자열 매칭 수행
        if not matched_sql_ids:
            total_sql = len(sql_components)
            scanned_sql = 0
            for sql_comp in sql_components:
                scanned_sql += 1
                if self._sqltext_scan_tracker:
                    self._sqltext_scan_done += 1
                    self._sqltext_scan_tracker.update(
                        current=self._sqltext_scan_done,
                        log_message=(
                            f"[SQLTEXT MATCH BATCH] scanned={self._sqltext_scan_done}/{self._sqltext_scan_total} "
                            f"matched={self._sqltext_total_matched}"
                        )
                    )
                sql_id = sql_comp['component_name']
                if not sql_id or sql_id in matched_sql_ids:
                    continue
                if sql_id and sql_id in content:
                    fallback_method_name = file_stem
                    class_id = self._ensure_class_record(project_id, file_info['file_id'], file_stem)
                    fallback_method_id = self._ensure_method_component(
                        project_id,
                        file_info['file_id'],
                        fallback_method_name,
                        class_id
                    )
                    if not fallback_method_id:
                        continue
                    matched_sql += 1
                    matched_sql_ids.add(sql_id)
                    if self._insert_call_query_relationship(fallback_method_id, sql_comp['component_id']):
                        relationships_created += 1
                    debug(f"sqltext 매칭(보조): {file_info['file_name']} SQL_ID={sql_id} -> METHOD={fallback_method_name}")

        return {'matched_sql': matched_sql, 'relationships_created': relationships_created}

    def _extract_method_blocks(self, content: str) -> List[Dict[str, str]]:
        """
        Java 파일에서 메서드 블록을 추출한다.

        Returns:
            [{'name': 메서드명, 'body': 메서드본문}, ...]
        """
        results: List[Dict[str, str]] = []
        try:
            pattern = re.compile(
                r'^[ \t]*(?:@\w[^\n]*\n\s*)*'
                r'(?:public|protected|private)?\s*'
                r'(?:static\s+|final\s+|synchronized\s+|abstract\s+|native\s+|strictfp\s+)*'
                r'[\w\<\>\[\]]+\s+(\w+)\s*\([^;{]*\)\s*\{',
                re.MULTILINE
            )
            last_end = -1
            for m in pattern.finditer(content):
                name = m.group(1)
                brace_start = content.find('{', m.end() - 1)
                if brace_start == -1 or brace_start <= last_end:
                    continue
                body, brace_end = self._extract_brace_block(content, brace_start)
                if body is None:
                    continue
                results.append({'name': name, 'body': body})
                last_end = brace_end
        except Exception:
            return results
        return results

    def _extract_brace_block(self, content: str, start_idx: int) -> (Optional[str], int):
        """
        중괄호 블록을 추출한다.

        Args:
            content: 원본 내용
            start_idx: '{' 위치

        Returns:
            (본문, 종료 인덱스) 또는 (None, start_idx)
        """
        depth = 0
        for idx in range(start_idx, len(content)):
            ch = content[idx]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return content[start_idx + 1:idx], idx
        return None, start_idx

    def _extract_constant_string_map(self, content: str, sql_id_set: set) -> Dict[str, str]:
        """
        클래스/전역 상수 문자열 매핑을 추출한다.
        """
        const_map: Dict[str, str] = {}
        try:
            pattern = re.compile(
                r'\b(?:public|protected|private)?\s*(?:static\s+)?(?:final\s+)?String\s+(\w+)\s*=\s*"([^"\\]*(?:\\.[^"\\]*)*)"',
                re.MULTILINE
            )
            for var_name, literal in pattern.findall(content):
                if literal in sql_id_set:
                    const_map[var_name] = literal
        except Exception:
            return const_map
        return const_map

    def _extract_local_string_map(self, method_body: str, sql_id_set: set) -> Dict[str, str]:
        """
        메서드 내 로컬 문자열 매핑을 추출한다.
        """
        local_map: Dict[str, str] = {}
        try:
            pattern = re.compile(
                r'\b(?:final\s+)?String\s+(\w+)\s*=\s*"([^"\\]*(?:\\.[^"\\]*)*)"',
                re.MULTILINE
            )
            for var_name, literal in pattern.findall(method_body):
                if literal in sql_id_set:
                    local_map[var_name] = literal
        except Exception:
            return local_map
        return local_map

    def _extract_sql_ids_from_execute_calls(
        self,
        method_body: str,
        local_map: Dict[str, str],
        const_map: Dict[str, str],
        sql_id_set: set
    ) -> set:
        """
        execute/executeBatch 호출 인자에서 SQL ID를 추출한다.
        """
        sql_ids = set()
        try:
            call_pattern = re.compile(r'\.execute(?:Batch)?\s*\((.*?)\)', re.DOTALL)
            for args in call_pattern.findall(method_body):
                first_arg = args.split(',', 1)[0].strip()
                if not first_arg:
                    continue
                # 형변환 제거
                first_arg = re.sub(r'^\([^)]+\)\s*', '', first_arg)
                if first_arg.startswith('"'):
                    m = re.match(r'^"([^"\\]*(?:\\.[^"\\]*)*)"', first_arg)
                    if m and m.group(1) in sql_id_set:
                        sql_ids.add(m.group(1))
                        continue
                token_match = re.match(r'^([A-Za-z_][A-Za-z0-9_\.]*)', first_arg)
                if not token_match:
                    continue
                token = token_match.group(1)
                base_name = token.split('.')[-1]
                if base_name in local_map:
                    sql_ids.add(local_map[base_name])
                elif base_name in const_map:
                    sql_ids.add(const_map[base_name])
        except Exception:
            return sql_ids
        return sql_ids

    def _get_method_component_map(self, project_id: int, file_id: int) -> Dict[str, int]:
        """
        파일 내 METHOD 컴포넌트 이름 -> ID 매핑 반환
        """
        try:
            query = """
                SELECT component_id, component_name
                FROM components
                WHERE project_id = ?
                  AND file_id = ?
                  AND component_type = 'METHOD'
                  AND del_yn = 'N'
            """
            rows = self.db_utils.execute_query(query, (project_id, file_id), conn=self.conn)
            return {row['component_name']: row['component_id'] for row in rows} if rows else {}
        except Exception:
            return {}

    def _ensure_method_component(
        self,
        project_id: int,
        file_id: int,
        method_name: str,
        parent_id: Optional[int] = None
    ) -> Optional[int]:
        """
        METHOD 컴포넌트가 없으면 생성하고 component_id를 반환한다.
        """
        try:
            if not method_name:
                return None
            existing = self.db_utils.execute_query(
                """
                SELECT component_id, parent_id
                FROM components
                WHERE project_id = ? AND file_id = ? AND component_type = 'METHOD' AND component_name = ? AND del_yn = 'N'
                LIMIT 1
                """,
                (project_id, file_id, method_name),
                conn=self.conn
            )
            if existing:
                if parent_id and existing[0].get('parent_id') is None:
                    self.db_utils.execute_update(
                        """
                        UPDATE components
                        SET parent_id = ?
                        WHERE component_id = ? AND del_yn = 'N'
                        """,
                        (parent_id, existing[0]['component_id']),
                        conn=self.conn
                    )
                return existing[0]['component_id']
            comp_data = {
                'project_id': project_id,
                'file_id': file_id,
                'component_name': method_name,
                'component_type': 'METHOD',
                'parent_id': parent_id,
                'hash_value': HashUtils.generate_content_hash(method_name),
                'del_yn': 'N'
            }
            self.db_utils.insert_or_replace('components', comp_data)
            created = self.db_utils.execute_query(
                """
                SELECT component_id
                FROM components
                WHERE project_id = ? AND file_id = ? AND component_type = 'METHOD' AND component_name = ? AND del_yn = 'N'
                LIMIT 1
                """,
                (project_id, file_id, method_name),
                conn=self.conn
            )
            return created[0]['component_id'] if created else None
        except Exception as e:
            handle_error(e, f"METHOD 컴포넌트 생성 실패: {method_name}")
            return None

    def _ensure_class_record(self, project_id: int, file_id: int, class_name: str) -> Optional[int]:
        """
        Java 파일 기준 클래스 레코드를 확보하고 class_id를 반환한다.
        """
        try:
            if not class_name:
                return None
            existing = self.db_utils.execute_query(
                """
                SELECT class_id
                FROM classes
                WHERE project_id = ? AND file_id = ? AND class_name = ? AND del_yn = 'N'
                LIMIT 1
                """,
                (project_id, file_id, class_name),
                conn=self.conn
            )
            if existing:
                return existing[0]['class_id']

            class_data = {
                'project_id': project_id,
                'file_id': file_id,
                'class_name': class_name,
                'hash_value': HashUtils.generate_content_hash(class_name),
                'del_yn': 'N'
            }
            self.db_utils.insert_or_replace('classes', class_data)

            created = self.db_utils.execute_query(
                """
                SELECT class_id
                FROM classes
                WHERE project_id = ? AND file_id = ? AND class_name = ? AND del_yn = 'N'
                LIMIT 1
                """,
                (project_id, file_id, class_name),
                conn=self.conn
            )
            return created[0]['class_id'] if created else None
        except Exception as e:
            handle_error(e, f"CLASS 레코드 생성 실패: {class_name}")
            return None

    def _insert_call_query_relationship(self, method_id: int, sql_comp_id: int) -> bool:
        """
        METHOD -> SQLTEXT 쿼리 CALL_QUERY 관계 생성
        """
        try:
            rel_data = {
                'src_id': method_id,
                'dst_id': sql_comp_id,
                'rel_type': 'CALL_QUERY',
                'del_yn': 'N'
            }
            return bool(self.db_utils.insert_or_replace('relationships', rel_data))
        except Exception:
            return False

    def _remove_java_comments(self, content: str) -> str:
        """
        Java 주석을 제거한다.
        - // 라인 주석, /* */ 블록 주석 제거
        """
        try:
            content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            return content
        except Exception:
            return content

    def _remove_whitespace(self, content: str) -> str:
        """공백/개행 제거 (호출 패턴 빠른 검사 용도)"""
        try:
            return re.sub(r'\s+', '', content)
        except Exception:
            return content

    def _throttled_warning(self, key: str, message: str, interval: float = 1.0) -> None:
        """동일 유형 반복 로그는 interval 초 이내 중복 출력 방지 (콘솔 스팸 최소화)"""
        now = time.time()
        last = self._last_warn_ts.get(key, 0)
        if now - last >= interval:
            warning(message)
            self._last_warn_ts[key] = now

    def _log_method_missing(self, full_path: str) -> None:
        self._warn_counters["method_missing"] += 1
        self._throttled_warning("method_missing", f"METHOD 컴포넌트 없음: {full_path} (sqltext 매칭 스킵)")


    def _get_method_components(self, project_id: int, file_id: int) -> List[int]:
        """해당 Java 파일의 METHOD 컴포넌트 ID 리스트 반환"""
        try:
            query = """
                SELECT component_id
                FROM components
                WHERE project_id = ?
                  AND file_id = ?
                  AND component_type = 'METHOD'
                  AND del_yn = 'N'
            """
            rows = self.db_utils.execute_query(query, (project_id, file_id), conn=self.conn)
            return [row['component_id'] for row in rows] if rows else []
        except Exception as e:
            handle_error(e, "Java 컴포넌트 조회 실패")
            return []


def execute_sqltext_java_matching(project_name: str, conn) -> bool:
    """편의 함수"""
    matcher = SqlTextJavaMatcher(project_name, conn)
    return matcher.execute()
