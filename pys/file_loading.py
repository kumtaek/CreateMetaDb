"""
파일 로딩 모듈
- 처리플로우 1단계: 파일 정보 저장 (프로젝트 전체 스캔)
- 처리플로우 2단계: 데이터베이스 구조 저장 및 컴포넌트 생성
"""

import os
from typing import Optional, List, Dict, Any
from util import (
    PathUtils, DatabaseUtils, FileUtils, HashUtils, ValidationUtils,
    app_logger, info, error, debug, warning, handle_error, safe_remove_file,
    get_project_source_path, get_project_metadata_db_path, get_database_schema_path,
    get_project_db_schema_path, validate_file_exists, validate_directory_exists, join_path
)
from util.base_loading_engine import BaseLoadingEngine


class FileLoadingEngine(BaseLoadingEngine):
    """파일 로딩 엔진 - 1-2단계 처리플로우 구현"""
    
    def __init__(self, project_name: str, conn: Optional[Any] = None):
        """
        파일 로딩 엔진 초기화
        
        Args:
            project_name: 프로젝트명
            conn: 외부에서 주입된 데이터베이스 연결 객체
        """
        super().__init__(project_name, conn)
        
        # 프로젝트 경로들 (부모에 없는 것만 추가)
        self.project_db_schema_path = get_project_db_schema_path(project_name)
        
        # 통계 정보
        self.stats = {
            'total_files': 0, 'scanned_files': 0, 'error_files': 0,
            'java_files': 0, 'xml_files': 0, 'jsp_files': 0, 'sql_files': 0, 'csv_files': 0,
            'jsx_files': 0, 'vue_files': 0, 'ts_files': 0, 'tsx_files': 0, 'js_files': 0, 'html_files': 0,
            'css_files': 0, 'scss_files': 0, 'sass_files': 0, 'less_files': 0, 'other_files': 0,
            'tables_loaded': 0, 'tables_with_errors': 0, 'columns_loaded': 0, 'columns_with_errors': 0,
            'components_created': 0, 'components_with_errors': 0, 'inferred_columns_created': 0
        }


    
    def scan_project_files(self) -> List[Dict[str, Any]]:
        """
        프로젝트 전체 파일 스캔 (처리플로우 1단계)
        
        Returns:
            스캔된 파일 정보 리스트
        """
        try:
            # info(f"프로젝트 파일 스캔 시작: {self.project_source_path}")  # 로그 제거
            
            # 프로젝트 존재 여부 확인
            if not validate_directory_exists(self.project_source_path):
                error(f"프로젝트 경로가 존재하지 않습니다: {self.project_source_path}")
                return []
            
            scanned_files = []
            
            # FileUtils.scan_directory()로 전체 디렉토리 스캔
            files = FileUtils.scan_directory(self.project_source_path, recursive=True)
            for file_info in files:
                file_path = file_info['file_path']
                
                try:
                    # 파일 필터링: 대상 파일만 포함
                    relative_path = self.path_utils.get_relative_path(file_path, self.project_source_path)
                    if not self._should_include_file(relative_path):
                        continue
                    
                    # 파일 정보 수집
                    detailed_file_info = self._get_file_info(file_path)
                    if detailed_file_info:
                        scanned_files.append(detailed_file_info)
                        self.stats['scanned_files'] += 1
                        
                        # 파일 타입별 통계
                        file_type = detailed_file_info.get('file_type', 'unknown').upper()
                        # 기본 파일 타입
                        if file_type in ['JAVA', 'XML', 'JSP', 'SQL', 'CSV']:
                            self.stats[f'{file_type.lower()}_files'] += 1
                        # 프론트엔드 파일 타입
                        elif file_type in ['JSX', 'VUE', 'TS', 'TSX', 'JS', 'HTML', 'CSS', 'SCSS', 'SASS', 'LESS']:
                            # TypeScript 파일 처리 (.ts -> ts_files, .tsx -> tsx_files)
                            if file_type == 'TS':
                                self.stats['ts_files'] += 1
                            elif file_type == 'TSX':
                                self.stats['tsx_files'] += 1
                            else:
                                self.stats[f'{file_type.lower()}_files'] += 1
                        else:
                            self.stats['other_files'] += 1
                    else:
                        self.stats['error_files'] += 1
                        
                except Exception as e:
                    handle_error(e, f"파일 스캔 오류: {file_path}")
            
            self.stats['total_files'] = len(scanned_files)
            # info(f"파일 스캔 완료: 총 {self.stats['total_files']}개 파일")  # 로그 제거
            
            return scanned_files
            
        except Exception as e:
            # 모든 예외는 handle_error()로 처리
            handle_error(e, "프로젝트 파일 스캔 실패")
            return []
    


    def _get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """수집 대상 파일의 메타데이터를 생성한다."""
        try:
            file_info = FileUtils.get_file_info(file_path)

            relative_path = self.path_utils.get_relative_path(file_path, self.project_source_path)
            unix_relative_path = self.path_utils.normalize_path_separator(relative_path, 'unix')
            relative_dir = os.path.dirname(unix_relative_path) if unix_relative_path else ''
            if relative_dir in ('', '.'):
                relative_dir = ''
            else:
                relative_dir = self.path_utils.normalize_path_separator(relative_dir, 'unix')

            components = self.path_utils.get_path_components(file_path)
            file_name = file_info.get('file_name') or components.get('filename') or components.get('file_name') or os.path.basename(file_path)

            if not file_info.get('exists', False):
                raw_file_type = FileUtils.get_file_type(file_path)
                file_type = raw_file_type.upper()
                debug(f"DEBUG: _get_file_info processing {file_name}: raw={raw_file_type}, upper={file_type}")
                return {
                    'file_path': relative_dir,
                    'file_name': file_name,
                    'file_type': file_type,
                    'hash_value': '-',
                    'line_count': 0,
                    'del_yn': 'N'
                }

            raw_file_type = file_info['file_type']
            file_type = raw_file_type.upper()
            debug(f"DEBUG: _get_file_info processing {file_name}: raw={raw_file_type}, upper={file_type}")
            return {
                'file_path': relative_dir,
                'file_name': file_name,
                'file_type': file_type,
                'hash_value': file_info['hash_value'],
                'line_count': file_info['line_count'],
                'del_yn': 'N'
            }

        except Exception as e:
            handle_error(e, f"파일 정보 수집 실패: {file_path}")
            try:
                relative_path = self.path_utils.get_relative_path(file_path, self.project_source_path)
                unix_relative_path = self.path_utils.normalize_path_separator(relative_path, 'unix')
                relative_dir = os.path.dirname(unix_relative_path) if unix_relative_path else ''
                if relative_dir in ('', '.'):
                    relative_dir = ''
                else:
                    relative_dir = self.path_utils.normalize_path_separator(relative_dir, 'unix')
                components = self.path_utils.get_path_components(file_path)
                file_name = components.get('filename') or components.get('file_name') or os.path.basename(file_path)
                file_type = FileUtils.get_file_type(file_path).upper()
                return {
                    'file_path': relative_dir,
                    'file_name': file_name,
                    'file_type': file_type,
                    'hash_value': '-',
                    'line_count': 0,
                    'del_yn': 'N'
                }
            except Exception as e2:
                handle_error(e2, f"파일 정보 수집 실패(보조 경로 계산 실패): {file_path}")
                return None
    def _should_include_file(self, relative_path: str) -> bool:
        """
        파일 포함 여부 확인 (대상 파일인지 확인)
        target_source_config.yaml의 include/exclude 설정 적용
        
        Args:
            relative_path: 프로젝트 기준 상대경로
            
        Returns:
            포함 여부 (True: 포함, False: 제외)
        """
        try:
            # 크로스플랫폼 경로 구분자 정규화 (Unix 스타일로 통일)
            normalized_path = self.path_utils.normalize_path_separator(relative_path, 'unix')
            
            # metadata.db 관련 파일들 제외
            if normalized_path in ['metadata.db', 'metadata.db-shm', 'metadata.db-wal']:
                return False
            
            # config/* 파일들 제외 (크로스플랫폼 대응)
            if normalized_path.startswith('config' + os.sep) or normalized_path.startswith('config/'):
                return False
            
            # db_schema의 스키마 파일만 포함 (ALL_TABLES/ALL_TAB_COLUMNS, 확장자 csv/sch 허용)
            if normalized_path.startswith('db_schema/'):
                filename = os.path.basename(normalized_path)
                name_without_ext, ext = os.path.splitext(filename)
                if name_without_ext in ['ALL_TABLES', 'ALL_TAB_COLUMNS'] and ext.lower() in ['.csv', '.sch']:
                    return True
                return False
            
            # src/ 하위 파일들은 target_source_config.yaml 설정 적용
            if normalized_path.startswith('src/'):
                return self._apply_file_filters(normalized_path)
            
            # 그 외 모든 파일 제외
            return False
            
        except Exception as e:
            # 모든 예외는 handle_error()로 처리
            handle_error(e, f"파일 포함 여부 확인 실패: {relative_path}")
            return False
    
    def _apply_file_filters(self, normalized_path: str) -> bool:
        """
        target_source_config.yaml의 include/exclude 설정을 적용하여 파일 포함 여부 결정
        
        Args:
            normalized_path: Unix 스타일로 정규화된 상대경로
            
        Returns:
            포함 여부 (True: 포함, False: 제외)
        """
        try:
            # target_source_config.yaml 설정 로드
            config = self._load_target_source_config()
            if not config:
                # 설정 파일이 없으면 기본적으로 포함
                return True
            
            # 제외 디렉토리 패턴 확인
            exclude_directories = config.get('exclude_directories', [])
            for pattern in exclude_directories:
                if self._match_pattern(normalized_path, pattern):
                    return False
            
            # 제외 파일 패턴 확인
            exclude_files = config.get('exclude_files', [])
            for pattern in exclude_files:
                if self._match_pattern(normalized_path, pattern):
                    return False
            
            # 포함 파일 패턴 확인
            include_patterns = config.get('include_patterns', [])
            if include_patterns:
                # include_patterns가 정의되어 있으면 매칭되는 것만 포함
                for pattern in include_patterns:
                    if self._match_pattern(normalized_path, pattern):
                        return True
                # 매칭되는 패턴이 없으면 제외
                return False
            
            # include_patterns가 없으면 기본적으로 포함
            return True
            
        except Exception as e:
            handle_error(e, f"파일 필터 적용 실패: {normalized_path}")
            return True
    
    def _load_target_source_config(self) -> Optional[Dict[str, Any]]:
        """
        target_source_config.yaml 설정 로드
        프로젝트별 설정 우선, 기본 설정 후순위
        
        Returns:
            설정 딕셔너리 또는 None
        """
        try:
            from util.config_utils import load_yaml_config
            
            # 1. 프로젝트별 설정 우선 적용 (크로스플랫폼 대응)
            project_config_path = self.path_utils.join_path(self.project_source_path, 'config', 'target_source_config.yaml')
            if os.path.exists(project_config_path):
                return load_yaml_config(project_config_path)
            
            # 2. 기본 설정 적용 (크로스플랫폼 대응)
            default_config_path = self.path_utils.get_config_path('target_source_config.yaml')
            if os.path.exists(default_config_path):
                return load_yaml_config(default_config_path)
            
            return None
            
        except Exception as e:
            handle_error(e, "target_source_config.yaml 로드 실패")
            return None
    
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """
        경로가 패턴과 매칭되는지 확인 (pathlib.Path.match 사용)
        '**' 패턴을 올바르게 지원합니다.
        
        Args:
            path: 확인할 경로
            pattern: 매칭 패턴
            
        Returns:
            매칭 여부 (True/False)
        """
        try:
            from pathlib import Path
            # 윈도우 경로 구분자를 POSIX 스타일로 변경하여 match 메서드가 올바르게 동작하도록 함
            # pathlib.Path.match는 POSIX 스타일 경로에서만 '**'를 올바르게 처리함
            normalized_path_for_match = path.replace('\\', '/')
            return Path(normalized_path_for_match).match(pattern)
                
        except Exception as e:
            handle_error(e, f"패턴 매칭 실패: {path}, {pattern}")
            return False
    
    def _parse_data_type(self, data_type_raw: str) -> tuple[str, Optional[int]]:
        """
        data_type에서 타입과 길이 정보 분리
        
        Args:
            data_type_raw: 원본 data_type (예: VARCHAR2(50), NUMBER(10,2))
            
        Returns:
            (data_type, data_length) 튜플
        """
        if not data_type_raw:
            return '', None
        
        # 괄호가 있는 경우 길이 정보 추출
        if '(' in data_type_raw and ')' in data_type_raw:
            # VARCHAR2(50) -> VARCHAR2, 50
            type_part = data_type_raw.split('(')[0].strip()
            length_part = data_type_raw.split('(')[1].split(')')[0].strip()
            
            # 길이가 숫자인지 확인
            try:
                # NUMBER(10,2) 같은 경우 첫 번째 숫자만 사용
                if ',' in length_part:
                    length_part = length_part.split(',')[0]
                data_length = int(length_part)
                return type_part, data_length
            except ValueError as ve:
                handle_error(ve, f"데이터 길이 파싱 실패: {length_part}")
                return type_part, None
        else:
            # 괄호가 없는 경우 (NUMBER, DATE 등)
            return data_type_raw.strip(), None
    
    def load_csv_file(self, csv_path: str) -> List[Dict[str, str]]:
        """
        CSV/스키마 파일을 읽어서 딕셔너리 리스트로 변환

        Args:
            csv_path: CSV 또는 SCH 파일 경로

        Returns:
            딕셔너리 리스트
        """
        import csv
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                return [row for row in reader]
        except UnicodeDecodeError:
            try:
                with open(csv_path, 'r', encoding='cp949') as file:
                    reader = csv.DictReader(file)
                    return [row for row in reader]
            except Exception as e:
                handle_error(e, f"CSV/SCH 파일 처리 실패 (cp949): {csv_path}")
                return []
        except FileNotFoundError:
            handle_error(Exception(f"CSV/SCH 파일을 찾을 수 없습니다: {csv_path}"), f"CSV/SCH 파일 읽기 실패: {csv_path}")
            return []
        except Exception as e:
            handle_error(e, f"CSV/SCH 파일 처리 실패: {csv_path}")
            return []

    def save_files_to_database(self, files: List[Dict[str, Any]]) -> bool:
        """
        스캔된 파일들을 files 테이블에 저장 (주입된 연결 사용)
        
        Args:
            files: 파일 정보 리스트
            
        Returns:
            저장 성공 여부
        """
        try:
            if not files:
                warning("저장할 파일이 없습니다")
                return True
            
            project_id = self.get_project_id()
            if not project_id:
                raise Exception("프로젝트 ID를 찾을 수 없습니다")

            # DB 스키마에 맞춰 files 테이블 컬럼만 남겨 저장
            allowed_cols = {
                'project_id', 'file_path', 'file_name', 'file_type',
                'hash_value', 'line_count', 'frameworks', 'del_yn'
            }
            file_data_list = []
            for f in files:
                base = {'project_id': project_id, **f}
                filtered = {k: v for k, v in base.items() if k in allowed_cols}
                file_data_list.append(filtered)
            
            processed_count = 0
            for file_data in file_data_list:
                if self.db_utils.upsert('files', file_data, ['file_name', 'file_path', 'project_id'], self.conn):
                    processed_count += 1
            
            if processed_count > 0:
                return True
            else:
                raise Exception("파일 정보 저장 실패")
                
        except Exception as e:
            handle_error(e, "파일 정보 저장 실패")
            return False

    # total_files 컬럼 제거에 따라 프로젝트 파일 수 업데이트는 수행하지 않음

    def save_tables_to_database(self, tables_data: List[Dict[str, str]]) -> bool:
        """테이블 정보를 tables 테이블에 저장 (주입된 연결 사용)"""
        try:
            if not tables_data:
                return True
            
            project_id = self.get_project_id()
            if not project_id:
                raise Exception("프로젝트 ID를 찾을 수 없습니다")

            all_tables_file_id = self._get_csv_file_id("ALL_TABLES.sch")
            if not all_tables_file_id:
                raise Exception("ALL_TABLES.sch 파일 ID를 찾을 수 없습니다")

            table_data_list = []
            for table_info in tables_data:
                table_name = table_info.get('TABLE_NAME', '')
                if not table_name: continue
                table_name = table_name.strip().upper()
                table_owner = (table_info.get('OWNER', '').strip() or 'UNKNOWN').upper()
                table_hash = HashUtils.generate_content_hash(f"{table_owner}{table_name}{table_info.get('COMMENTS', '')}")
                table_data_list.append({
                    'project_id': project_id, 'component_id': None,
                    'table_name': table_name, 'table_owner': table_owner,
                    'table_comments': table_info.get('COMMENTS', ''),
                    'hash_value': table_hash, 'del_yn': 'N'
                })

            processed_count = self.db_utils.batch_insert_or_replace('tables', table_data_list, conn=self.conn)
            if processed_count > 0:
                self.stats['tables_loaded'] = processed_count
                return True
            return False
        except Exception as e:
            handle_error(e, "테이블 정보 저장 실패")
            return False

    def save_columns_to_database(self, columns_data: List[Dict[str, str]]) -> bool:
        """컬럼 정보를 columns 테이블에 저장 (주입된 연결 사용)"""
        try:
            if not columns_data:
                return True

            column_data_list = []
            for col_info in columns_data:
                table_name = col_info.get('TABLE_NAME', '')
                column_name = col_info.get('COLUMN_NAME', '')
                if not table_name or not column_name: continue
                table_name = table_name.strip().upper()
                column_name = column_name.strip().upper()

                table_owner = (col_info.get('OWNER', '').strip() or 'UNKNOWN').upper()
                table_id = self._get_table_id(table_owner, table_name)
                data_type, data_length = self._parse_data_type(col_info.get('DATA_TYPE', ''))
                column_hash = HashUtils.generate_content_hash(f"{table_owner}{table_name}{column_name}{data_type}")
                
                column_data_list.append({
                    'table_id': table_id, 'column_name': column_name, 'data_type': data_type,
                    'data_length': data_length, 'nullable': 'Y' if col_info.get('NULLABLE', 'Y') == 'Y' else 'N',
                    'column_comments': col_info.get('COLUMN_COMMENTS', ''), 'position_pk': int(col_info.get('PK', '0')) if col_info.get('PK', '0').isdigit() else None,
                    'data_default': None, 'owner': table_owner,
                    'hash_value': column_hash, 'del_yn': 'N'
                })

            processed_count = self.db_utils.batch_insert_or_replace('columns', column_data_list, conn=self.conn)
            if processed_count > 0:
                self.stats['columns_loaded'] = processed_count
                return True
            return False
        except Exception as e:
            handle_error(e, "컬럼 정보 저장 실패")
            return False

    def create_table_components(self) -> bool:
        """tables 테이블의 모든 테이블을 components 테이블에 등록 (주입된 연결 사용)"""
        try:
            project_id = self.get_project_id()
            if not project_id:
                raise Exception("프로젝트 ID를 찾을 수 없습니다")

            all_tables_file_id = self._get_csv_file_id("ALL_TABLES.sch")
            if not all_tables_file_id:
                raise Exception("ALL_TABLES.sch/ALL_TABLES.csv 파일 ID를 찾을 수 없습니다")

            tables = self.db_utils.execute_query("SELECT table_id, table_name, hash_value FROM tables WHERE project_id = ? AND del_yn = 'N'", (project_id,), self.conn)
            if not tables:
                return True

            component_data = [{'project_id': project_id, 'file_id': all_tables_file_id, 'component_name': t['table_name'], 'component_type': 'TABLE', 'layer': 'TABLE', 'hash_value': t['hash_value'], 'del_yn': 'N'} for t in tables]
            
            processed_count = self.db_utils.batch_insert_or_replace('components', component_data, conn=self.conn)
            if processed_count > 0:
                self.stats['components_created'] = processed_count
                self._update_table_component_ids(project_id)
                return True
            return False
        except Exception as e:
            handle_error(e, "테이블 컴포넌트 생성 실패")
            return False

    def create_column_components(self) -> bool:
        """columns 테이블의 모든 컬럼을 components 테이블에 등록 (주입된 연결 사용)"""
        try:
            project_id = self.get_project_id()
            if not project_id:
                raise Exception("프로젝트 ID를 찾을 수 없습니다")

            all_columns_file_id = self._get_csv_file_id("ALL_TAB_COLUMNS.sch")
            if not all_columns_file_id:
                raise Exception("ALL_TAB_COLUMNS.sch/ALL_TAB_COLUMNS.csv 파일 ID를 찾을 수 없습니다")

            query = """SELECT c.column_name, c.hash_value, t.table_name, t.table_owner FROM columns c JOIN tables t ON c.table_id = t.table_id WHERE t.project_id = ? AND c.del_yn = 'N' AND t.del_yn = 'N'"""
            columns = self.db_utils.execute_query(query, (project_id,), self.conn)
            if not columns:
                return True

            component_data = []
            for col in columns:
                table_comp_id = self._get_table_component_id(col['table_name'], col.get('table_owner'))
                component_data.append({
                    'project_id': project_id, 'file_id': all_columns_file_id, 'component_name': col['column_name'],
                    'component_type': 'COLUMN', 'parent_id': table_comp_id, 'layer': 'TABLE',
                    'hash_value': col['hash_value'], 'del_yn': 'N'
                })

            processed_count = self.db_utils.batch_insert_or_replace('components', component_data, conn=self.conn)
            if processed_count > 0:
                self.stats['components_created'] += processed_count
                return True
            return False
        except Exception as e:
            handle_error(e, "컬럼 컴포넌트 생성 실패")
            return False

    def _get_csv_file_id(self, filename: str) -> Optional[int]:
        """
        CSV/스키마 파일의 file_id 조회 (주입된 연결 사용, csv/sch 공통 처리)

        Args:
            filename: 파일명 또는 기본 이름 (예: 'ALL_TABLES.sch', 'ALL_TABLES')

        Returns:
            files.file_id 또는 None
        """
        # 확장자를 분리하여 기본 이름 계산
        name_without_ext, ext = os.path.splitext(filename)
        if ext.lower() in ['.csv', '.sch']:
            base_name = name_without_ext
        else:
            base_name = filename

        # csv/sch 두 종류 모두 허용, sch를 우선 사용
        candidate_names = [f"{base_name}.sch", f"{base_name}.csv"]

        query = """
            SELECT f.file_id, f.file_name
            FROM files f
            JOIN projects p ON f.project_id = p.project_id
            WHERE p.project_name = ?
              AND f.file_name IN (?, ?)
              AND f.del_yn = 'N'
            ORDER BY
              CASE
                WHEN f.file_name LIKE '%.sch' THEN 0
                WHEN f.file_name LIKE '%.csv' THEN 1
                ELSE 2
              END,
              f.file_id
            LIMIT 1
        """
        results = self.db_utils.execute_query(
            query,
            (self.project_name, candidate_names[0], candidate_names[1]),
            self.conn
        )
        return results[0]['file_id'] if results else None

    def _get_table_id(self, owner: str, table_name: str) -> Optional[int]:
        """테이블 ID 조회 (주입된 연결 사용)"""
        query = "SELECT t.table_id FROM tables t JOIN projects p ON t.project_id = p.project_id WHERE p.project_name = ? AND t.table_owner = ? AND t.table_name = ? AND t.del_yn = 'N'"
        results = self.db_utils.execute_query(query, (self.project_name, owner.upper(), table_name.upper()), self.conn)
        return results[0]['table_id'] if results else None

    def _get_table_component_id(self, table_name: str, table_owner: Optional[str] = None) -> Optional[int]:
        """테이블 컴포넌트 ID 조회 (주입된 연결 사용)"""
        if table_owner:
            query = """SELECT c.component_id 
                       FROM components c
                       JOIN projects p ON c.project_id = p.project_id 
                       WHERE p.project_name = ? 
                       AND c.component_name = ? 
                       AND c.component_type = 'TABLE' 
                       AND c.del_yn = 'N'"""
            results = self.db_utils.execute_query(query, (self.project_name, table_name.upper()), self.conn)
        else:
            query = """SELECT c.component_id 
                       FROM components c
                       JOIN projects p ON c.project_id = p.project_id 
                       WHERE p.project_name = ? 
                       AND c.component_name = ? 
                       AND c.component_type = 'TABLE' 
                       AND c.del_yn = 'N'"""
            results = self.db_utils.execute_query(query, (self.project_name, table_name.upper()), self.conn)
        return results[0]['component_id'] if results else None

    def _update_table_component_ids(self, project_id: int):
        """tables 테이블의 component_id 업데이트 (주입된 연결 사용)"""
        query = """UPDATE tables SET component_id = (SELECT c.component_id FROM components c WHERE c.project_id = tables.project_id AND c.component_name = tables.table_name AND c.component_type = 'TABLE' AND c.del_yn = 'N') WHERE project_id = ? AND del_yn = 'N'"""
        self.db_utils.execute_update(query, (project_id,), conn=self.conn)

    def execute_file_scan(self, clear_metadb: bool = False) -> bool:
        """파일 스캔 실행: 파일 정보 저장 (외부 트랜잭션 내에서 실행)"""
        try:
            # DB 초기화 및 프로젝트 정보 저장은 main에서 트랜잭션 시작 전에 수행
            db_path = get_project_metadata_db_path(self.project_name)
            # SqlContent.db 경로 (메타와 함께 초기화해야 잔존 데이터로 오염되는 것을 방지)
            sql_content_db_path = self.path_utils.join_path("projects", self.project_name, "SqlContent.db")

            # 이미 열린 커넥션이 있는 상태에서 clear_metadb가 남아있다면 잘못된 실행 순서이므로 중단
            if clear_metadb and self.conn:
                handle_error(Exception("메타DB 초기화 시점 오류"), "clear_metadb는 DB 커넥션 생성 전에 완료되어야 합니다")
            
            if clear_metadb:
                if os.path.exists(db_path):
                    if safe_remove_file(db_path, max_retries=3, retry_delay=0.5):
                        info(f"기존 메타데이터베이스 삭제: {db_path}")
                # SqlContent.db도 함께 초기화 (과거 잔존 SQL 콘텐츠가 파일 매핑을 왜곡하는 문제 예방)
                if os.path.exists(sql_content_db_path):
                    if safe_remove_file(sql_content_db_path, max_retries=3, retry_delay=0.5):
                        info(f"기존 SQL 콘텐츠 DB 삭제: {sql_content_db_path}")
            
            # 스키마가 존재하지 않으면 생성
            if not os.path.exists(db_path):
                if not self.db_utils.connect():
                    handle_error(Exception("DB 초기화 실패"), "메타데이터베이스 스키마 생성 실패")
                schema_path = self.path_utils.join_path(self.path_utils.get_root_path(), 'database', 'create_table_script.sql')
                if not self.db_utils.create_schema(schema_path):
                    handle_error(Exception("DB 초기화 실패"), "메타데이터베이스 스키마 생성 실패")
                info(f"메타데이터베이스 스키마 생성 완료: {db_path}")
            
            project_path_normalized = self.path_utils.normalize_path(self.path_utils.join_path("projects", self.project_name))
            project_data = {'project_name': self.project_name, 'project_path': project_path_normalized, 'del_yn': 'N'}
            self.db_utils.upsert('projects', project_data, ['project_name', 'project_path'], self.conn)

            # 파일 스캔 및 저장
            scanned_files = self.scan_project_files()
            if not scanned_files:
                warning("스캔된 파일이 없습니다")
                return True # 오류는 아니므로 True 반환
            
            return self.save_files_to_database(scanned_files)

        except Exception as e:
            handle_error(e, "파일 스캔 실행 실패")
            return False

    def execute_db_loading(self) -> bool:
        """데이터베이스 로딩 실행 (외부 트랜잭션 내에서 실행)"""
        try:
            # 1. ALL_TABLES.* (sch/csv) 로드 및 저장
            all_tables_path = None
            for ext in ['.sch', '.csv']:
                candidate = os.path.join(self.project_db_schema_path, f"ALL_TABLES{ext}")
                if validate_file_exists(candidate):
                    all_tables_path = candidate
                    break
            if not all_tables_path:
                handle_error(Exception("DB 스키마 파일 없음"), "ALL_TABLES.sch/ALL_TABLES.csv 파일을 찾을 수 없습니다")
                return False

            tables_data = self.load_csv_file(all_tables_path)
            if not self.save_tables_to_database(tables_data):
                return False

            # 2. ALL_TAB_COLUMNS.* (sch/csv) 로드 및 저장
            all_columns_path = None
            for ext in ['.sch', '.csv']:
                candidate = os.path.join(self.project_db_schema_path, f"ALL_TAB_COLUMNS{ext}")
                if validate_file_exists(candidate):
                    all_columns_path = candidate
                    break
            if not all_columns_path:
                handle_error(Exception("DB 스키마 파일 없음"), "ALL_TAB_COLUMNS.sch/ALL_TAB_COLUMNS.csv 파일을 찾을 수 없습니다")
                return False

            columns_data = self.load_csv_file(all_columns_path)
            if not self.save_columns_to_database(columns_data):
                return False
            
            # 3. 테이블/컬럼 컴포넌트 생성
            if not self.create_table_components():
                return False
            if not self.create_column_components():
                return False

            return True
        except Exception as e:
            handle_error(e, "데이터베이스 로딩 실행 실패")
            return False
    
    def _print_statistics(self):
        """통계 정보 출력"""
        # info("=== 파일 스캔 통계 ===")  # 로그 제거
        # info(f"총 파일 수: {self.stats['total_files']}")  # 로그 제거
        # info(f"성공 스캔: {self.stats['scanned_files']}")  # 로그 제거
        # info(f"오류 파일: {self.stats['error_files']}")  # 로그 제거
        # info(f"Java 파일: {self.stats['java_files']}")  # 로그 제거
        # info(f"XML 파일: {self.stats['xml_files']}")  # 로그 제거
        # info(f"JSP 파일: {self.stats['jsp_files']}")  # 로그 제거
        # info(f"SQL 파일: {self.stats['sql_files']}")  # 로그 제거
        # info(f"CSV 파일: {self.stats['csv_files']}")  # 로그 제거
        # info(f"기타 파일: {self.stats['other_files']}")  # 로그 제거
    
    def _print_db_loading_statistics(self):
        """데이터베이스 로딩 통계 정보 출력"""
        # info("=== 데이터베이스 구조 저장 통계 ===")  # 로그 제거
        # info(f"테이블 로드: {self.stats['tables_loaded']} (오류: {self.stats['tables_with_errors']})")  # 로그 제거
        # info(f"컬럼 로드: {self.stats['columns_loaded']} (오류: {self.stats['columns_with_errors']})")  # 로그 제거
        # info(f"컴포넌트 생성: {self.stats['components_created']} (오류: {self.stats['components_with_errors']})")  # 로그 제거
        # info(f"inferred 컬럼 생성: {self.stats['inferred_columns_created']}")  # 로그 제거
        
        # 오류 요약
        total_errors = (self.stats['tables_with_errors'] + 
                       self.stats['columns_with_errors'] + 
                       self.stats['components_with_errors'])
        if total_errors > 0:
            warning(f"총 오류 발생: {total_errors}개")
        # else:
        #     info("오류 없이 완료")  # 로그 제거


# 편의 함수
def execute_file_scan(project_name: str, clear_metadb: bool = False) -> bool:
    """
    파일 스캔 실행 편의 함수
    
    Args:
        project_name: 프로젝트명
        clear_metadb: 메타데이터베이스 초기화 여부
        
    Returns:
        실행 성공 여부
    """
    engine = FileLoadingEngine(project_name)
    return engine.execute_file_scan(clear_metadb)


def execute_db_loading(project_name: str) -> bool:
    """
    데이터베이스 로딩 실행 편의 함수
    
    Args:
        project_name: 프로젝트명
        
    Returns:
        실행 성공 여부
    """
    engine = FileLoadingEngine(project_name)
    return engine.execute_db_loading()
