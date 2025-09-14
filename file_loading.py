"""
파일 로딩 모듈
- 처리플로우 1단계: 파일 정보 저장 (프로젝트 전체 스캔)
- 처리플로우 2단계: 데이터베이스 구조 저장 및 컴포넌트 생성
"""

import os
from typing import Optional, List, Dict, Any
from util import (
    PathUtils, DatabaseUtils, FileUtils, HashUtils, ValidationUtils,
    app_logger, info, error, debug, warning, handle_error,
    get_project_source_path, get_project_metadata_db_path, get_database_schema_path,
    get_project_db_schema_path, validate_file_exists, validate_directory_exists, join_path
)


class FileLoadingEngine:
    """파일 로딩 엔진 - 1-2단계 처리플로우 구현"""
    
    def __init__(self, project_name: str):
        """
        파일 로딩 엔진 초기화
        
        Args:
            project_name: 프로젝트명
        """
        self.project_name = project_name
        self.path_utils = PathUtils()
        
        # 프로젝트 경로들
        self.project_source_path = get_project_source_path(project_name)
        self.metadata_db_path = get_project_metadata_db_path(project_name)
        self.database_schema_path = get_database_schema_path()
        self.project_db_schema_path = get_project_db_schema_path(project_name)
        
        # 데이터베이스 연결
        self.db_utils = None
        
        # 통계 정보
        self.stats = {
            'total_files': 0,
            'scanned_files': 0,
            'error_files': 0,
            'java_files': 0,
            'xml_files': 0,
            'jsp_files': 0,
            'sql_files': 0,
            'csv_files': 0,
            'other_files': 0,
            'tables_loaded': 0,
            'tables_with_errors': 0,
            'columns_loaded': 0,
            'columns_with_errors': 0,
            'components_created': 0,
            'components_with_errors': 0,
            'inferred_columns_created': 0
        }
    
    def initialize_database(self, clear_metadb: bool = False) -> bool:
        """
        메타데이터베이스 초기화
        
        Args:
            clear_metadb: 기존 메타데이터베이스 삭제 여부
            
        Returns:
            초기화 성공 여부
        """
        try:
            # 기존 DB 삭제 (옵션)
            if clear_metadb and os.path.exists(self.metadata_db_path):
                os.remove(self.metadata_db_path)
                info(f"기존 메타데이터베이스 삭제: {self.metadata_db_path}")
            
            # 데이터베이스 연결
            self.db_utils = DatabaseUtils(self.metadata_db_path)
            if not self.db_utils.connect():
                error("메타데이터베이스 연결 실패")
                return False
            
            # 스키마 생성
            if not self.db_utils.create_schema(self.database_schema_path):
                error("메타데이터베이스 스키마 생성 실패")
                return False
            
            info(f"메타데이터베이스 초기화 완료: {self.metadata_db_path}")
            return True
            
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, "메타데이터베이스 초기화 실패")
            return False
    
    def add_project_info(self) -> bool:
        """
        프로젝트 정보를 projects 테이블에 추가 (기존 프로젝트가 있으면 업데이트)
        
        Returns:
            추가 성공 여부
        """
        try:
            # 프로젝트 해시값 (하드코딩)
            project_hash = '-'
            
            project_data = {
                'project_name': self.project_name,
                'project_path': f"projects/{self.project_name}",  # 상대경로로 직접 설정
                'hash_value': project_hash,
                'del_yn': 'N',
                'total_files': 0  # 나중에 업데이트
            }
            
            # UPSERT 방식으로 프로젝트 정보 저장 (변경사항 반영)
            success = self.db_utils.upsert('projects', project_data, ['project_name', 'project_path'])
            if success:
                debug(f"프로젝트 정보 저장/업데이트 완료: {self.project_name}")
            else:
                error(f"프로젝트 정보 저장/업데이트 실패: {self.project_name}")
            
            return success
            
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, "프로젝트 정보 추가 실패")
            return False
    
    def get_project_id(self) -> Optional[int]:
        """
        프로젝트 ID 조회
        
        Returns:
            프로젝트 ID 또는 None
        """
        return self.db_utils.get_project_id(self.project_name)
    
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
                        file_type = detailed_file_info.get('file_type', 'unknown')
                        if file_type in ['JAVA', 'XML', 'JSP', 'SQL', 'CSV']:
                            self.stats[f'{file_type.lower()}_files'] += 1
                        else:
                            self.stats['other_files'] += 1
                    else:
                        self.stats['error_files'] += 1
                        
                except Exception as e:
                    warning(f"파일 스캔 오류: {file_path}, 오류: {str(e)}")
                    self.stats['error_files'] += 1
                    continue
            
            self.stats['total_files'] = len(scanned_files)
            # info(f"파일 스캔 완료: 총 {self.stats['total_files']}개 파일")  # 로그 제거
            
            return scanned_files
            
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, "프로젝트 파일 스캔 실패")
            return []
    
    def _get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        개별 파일 정보 수집
        
        Args:
            file_path: 파일 경로
            
        Returns:
            파일 정보 딕셔너리 또는 None
        """
        try:
            # 파일 기본 정보
            file_info = FileUtils.get_file_info(file_path)
            if not file_info.get('exists', False):
                # 파일이 존재하지 않는 경우 오류로 처리
                relative_path = self.path_utils.get_relative_path(file_path, self.project_source_path)
                file_name = os.path.basename(file_path)
                # 파일명에서 확장자 추출
                file_type = FileUtils.get_file_type(file_path).upper()
                return {
                    'file_path': os.path.dirname(relative_path),  # 디렉토리 경로만
                    'file_name': file_name,
                    'file_type': file_type,
                    'hash_value': '-',
                    'line_count': 0,
                    'has_error': 'Y',
                    'error_message': '파일이 존재하지 않습니다',
                    'del_yn': 'N'
                }
            
            # 프로젝트 기준 상대경로
            relative_path = self.path_utils.get_relative_path(file_path, self.project_source_path)
            
            # 파일 정보 구성 (file_path는 디렉토리 경로만)
            return {
                'file_path': os.path.dirname(relative_path),  # 디렉토리 경로만
                'file_name': file_info['file_name'],
                'file_type': file_info['file_type'].upper(),  # 대문자로 변경
                'hash_value': file_info['hash_value'],
                'line_count': file_info['line_count'],
                'has_error': 'N',
                'error_message': None,
                'del_yn': 'N'
            }
            
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            # 파일 정보 수집 실패 시 오류로 처리
            handle_error(e, f"파일 정보 수집 실패: {file_path}")
            try:
                relative_path = self.path_utils.get_relative_path(file_path, self.project_source_path)
                file_name = os.path.basename(file_path)
                # 파일명에서 확장자 추출
                file_type = FileUtils.get_file_type(file_path).upper()
                return {
                    'file_path': os.path.dirname(relative_path),  # 디렉토리 경로만
                    'file_name': file_name,
                    'file_type': file_type,
                    'hash_value': '-',
                    'line_count': 0,
                    'has_error': 'Y',
                    'error_message': f'파일 정보 수집 실패: {str(e)}',
                    'del_yn': 'N'
                }
            except:
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
            
            # db_schema의 특정 CSV 파일만 포함 (하드코딩)
            if normalized_path.startswith('db_schema/'):
                if normalized_path in ['db_schema/ALL_TABLES.csv', 'db_schema/ALL_TAB_COLUMNS.csv']:
                    return True
                else:
                    return False
            
            # src/ 하위 파일들은 target_source_config.yaml 설정 적용
            if normalized_path.startswith('src/'):
                return self._apply_file_filters(normalized_path)
            
            # 그 외 모든 파일 제외
            return False
            
        except Exception as e:
            # 오류 발생 시 안전하게 제외
            warning(f"파일 포함 여부 확인 실패: {relative_path}, 오류: {str(e)}")
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
            warning(f"파일 필터 적용 실패: {normalized_path}, 오류: {str(e)}")
            # 오류 발생 시 안전하게 포함
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
            warning(f"target_source_config.yaml 로드 실패: {str(e)}")
            return None
    
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """
        경로가 패턴과 매칭되는지 확인
        **/ 패턴 지원
        
        Args:
            path: 확인할 경로
            pattern: 매칭 패턴
            
        Returns:
            매칭 여부 (True/False)
        """
        try:
            import fnmatch
            
            # **/ 패턴을 처리하기 위해 정규화
            if pattern.startswith('**/'):
                # **/ 패턴: 경로의 어느 부분이든 매칭
                pattern = pattern[3:]  # **/ 제거
                return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, f"*/{pattern}")
            else:
                # 일반 패턴: 정확한 매칭
                return fnmatch.fnmatch(path, pattern)
                
        except Exception as e:
            warning(f"패턴 매칭 실패: {path}, {pattern}, 오류: {str(e)}")
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
            except ValueError:
                return type_part, None
        else:
            # 괄호가 없는 경우 (NUMBER, DATE 등)
            return data_type_raw.strip(), None
    
    def save_files_to_database(self, files: List[Dict[str, Any]]) -> bool:
        """
        스캔된 파일들을 files 테이블에 저장
        
        Args:
            files: 파일 정보 리스트
            
        Returns:
            저장 성공 여부
        """
        try:
            if not files:
                warning("저장할 파일이 없습니다")
                return True
            
            # 프로젝트 ID 조회
            project_id = self.get_project_id()
            if not project_id:
                error("프로젝트 ID를 찾을 수 없습니다")
                return False
            
            # 파일 데이터에 프로젝트 ID 추가
            file_data_list = []
            for file_info in files:
                file_data = file_info.copy()
                file_data['project_id'] = project_id
                file_data_list.append(file_data)
            
            # 개별 UPSERT로 파일 정보 저장 (변경사항 반영)
            processed_count = 0
            for file_data in file_data_list:
                success = self.db_utils.upsert('files', file_data, ['file_name', 'file_path', 'project_id'])
                if success:
                    processed_count += 1
            
            if processed_count > 0:
                # info(f"파일 정보 저장 완료: {processed_count}개 파일")  # 로그 제거
                
                # 프로젝트의 총 파일 수 업데이트
                self._update_project_total_files(project_id, processed_count)
                
                return True
            else:
                error("파일 정보 저장 실패")
                return False
                
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, "파일 정보 저장 실패")
            return False
    
    def _update_project_total_files(self, project_id: int, total_files: int):
        """
        프로젝트의 총 파일 수 업데이트
        
        Args:
            project_id: 프로젝트 ID
            total_files: 총 파일 수
        """
        try:
            query = "UPDATE projects SET total_files = ? WHERE project_id = ?"
            self.db_utils.execute_update(query, (total_files, project_id))
            debug(f"프로젝트 총 파일 수 업데이트: {total_files}")
            
        except Exception as e:
            warning(f"프로젝트 총 파일 수 업데이트 실패: {str(e)}")
    
    def load_csv_file(self, csv_path: str) -> List[Dict[str, str]]:
        """
        CSV 파일 로드 (한글 인코딩 지원)
        
        Args:
            csv_path: CSV 파일 경로
            
        Returns:
            CSV 데이터 리스트
        """
        try:
            if not validate_file_exists(csv_path):
                error(f"CSV 파일이 존재하지 않습니다: {csv_path}")
                return []
            
            # FileUtils.read_file()로 파일 내용 읽기
            content = FileUtils.read_file(csv_path)
            if not content:
                error(f"CSV 파일 읽기 실패: {csv_path}")
                return []
            
            # CSV 파싱
            csv_data = []
            lines = content.strip().split('\n')
            if not lines:
                return []
            
            # 헤더 추출
            header = [col.strip() for col in lines[0].split(',')]
            
            # 데이터 행 처리
            for line in lines[1:]:
                if not line.strip():
                    continue
                
                values = [val.strip() for val in line.split(',')]
                if len(values) == len(header):
                    row = dict(zip(header, values))
                    # 빈 행 제거
                    if any(row.values()):
                        csv_data.append(row)
            
            info(f"CSV 파일 로드 완료: {csv_path}, {len(csv_data)}개 행")
            return csv_data
            
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, f"CSV 파일 로드 실패: {csv_path}")
            return []
    
    def save_tables_to_database(self, tables_data: List[Dict[str, str]]) -> bool:
        """
        테이블 정보를 tables 테이블에 저장
        
        Args:
            tables_data: ALL_TABLES.csv 데이터
            
        Returns:
            저장 성공 여부
        """
        try:
            if not tables_data:
                warning("저장할 테이블 데이터가 없습니다")
                return True
            
            # 프로젝트 ID 조회
            project_id = self.get_project_id()
            if not project_id:
                error("프로젝트 ID를 찾을 수 없습니다")
                return False
            
            # ALL_TABLES.csv 파일 ID 조회
            all_tables_file_id = self._get_csv_file_id("ALL_TABLES.csv")
            if not all_tables_file_id:
                error("ALL_TABLES.csv 파일 ID를 찾을 수 없습니다")
                return False
            
            # 테이블 데이터 변환
            table_data_list = []
            for table_info in tables_data:
                try:
                    # 필수 필드 검증
                    table_name = table_info.get('TABLE_NAME', '').strip()
                    table_owner = table_info.get('OWNER', '').strip()
                    
                    if not table_name:
                        error_msg = "테이블명이 없습니다"
                        warning(f"테이블 데이터 오류: {error_msg}")
                        continue
                    
                    if not table_owner:
                        table_owner = 'UNKNOWN'
                        warning(f"테이블 소유자가 없어 UNKNOWN으로 설정: {table_name}")
                    
                    # 해시값 생성
                    table_hash = HashUtils.generate_content_hash(
                        f"{table_owner}{table_name}{table_info.get('COMMENTS', '')}"
                    )
                    
                    table_data = {
                        'project_id': project_id,
                        'component_id': None,  # 나중에 components에서 생성
                        'table_name': table_name,
                        'table_owner': table_owner,
                        'table_comments': table_info.get('COMMENTS', ''),
                        'has_error': 'N',
                        'error_message': None,
                        'hash_value': table_hash,
                        'del_yn': 'N'
                    }
                    table_data_list.append(table_data)
                    
                except Exception as e:
                    error_msg = f"테이블 데이터 처리 실패: {str(e)}"
                    warning(f"테이블 데이터 오류: {error_msg}")
                    # 오류가 있는 테이블도 저장하되 오류 표시
                    table_data = {
                        'project_id': project_id,
                        'component_id': None,
                        'table_name': table_info.get('TABLE_NAME', 'UNKNOWN'),
                        'table_owner': table_info.get('OWNER', 'UNKNOWN'),
                        'table_comments': table_info.get('COMMENTS', ''),
                        'has_error': 'Y',
                        'error_message': error_msg,
                        'hash_value': '-',
                        'del_yn': 'N'
                    }
                    table_data_list.append(table_data)
            
            # 배치 INSERT OR REPLACE
            processed_count = self.db_utils.batch_insert_or_replace('tables', table_data_list)
            
            if processed_count > 0:
                self.stats['tables_loaded'] = processed_count
                
                # 오류가 있는 테이블 수 계산
                error_count = sum(1 for table in table_data_list if table.get('has_error') == 'Y')
                self.stats['tables_with_errors'] = error_count
                
                info(f"테이블 정보 저장 완료: {processed_count}개 테이블 (오류: {error_count}개)")
                return True
            else:
                error("테이블 정보 저장 실패")
                return False
                
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, "테이블 정보 저장 실패")
            return False
    
    def save_columns_to_database(self, columns_data: List[Dict[str, str]]) -> bool:
        """
        컬럼 정보를 columns 테이블에 저장
        
        Args:
            columns_data: ALL_TAB_COLUMNS.csv 데이터
            
        Returns:
            저장 성공 여부
        """
        try:
            if not columns_data:
                warning("저장할 컬럼 데이터가 없습니다")
                return True
            
            # 컬럼 데이터 변환
            column_data_list = []
            for column_info in columns_data:
                try:
                    # 필수 필드 검증
                    column_name = column_info.get('COLUMN_NAME', '').strip()
                    table_name = column_info.get('TABLE_NAME', '').strip()
                    table_owner = column_info.get('OWNER', '').strip()
                    
                    if not column_name:
                        error_msg = "컬럼명이 없습니다"
                        warning(f"컬럼 데이터 오류: {error_msg}")
                        continue
                    
                    if not table_name:
                        error_msg = "테이블명이 없습니다"
                        warning(f"컬럼 데이터 오류: {error_msg}")
                        continue
                    
                    if not table_owner:
                        table_owner = 'UNKNOWN'
                        warning(f"테이블 소유자가 없어 UNKNOWN으로 설정: {table_name}.{column_name}")
                    
                    # 테이블 ID 조회
                    table_id = self._get_table_id(table_owner, table_name)
                    if not table_id:
                        error_msg = f"테이블 ID를 찾을 수 없습니다: {table_owner}.{table_name}"
                        warning(f"컬럼 데이터 오류: {error_msg}")
                        # 테이블이 없는 경우에도 컬럼은 저장하되 오류 표시
                        table_id = 0  # 임시 ID
                    
                    # data_type에서 길이 정보 분리
                    data_type_raw = column_info.get('DATA_TYPE', '')
                    data_type, data_length = self._parse_data_type(data_type_raw)
                    
                    # 해시값 생성
                    column_hash = HashUtils.generate_content_hash(
                        f"{table_owner}{table_name}{column_name}{data_type}"
                    )
                    
                    # 오류 여부 판단
                    has_error = 'Y' if table_id == 0 else 'N'
                    error_message = error_msg if table_id == 0 else None
                    
                    column_data = {
                        'table_id': table_id,
                        'column_name': column_name,
                        'data_type': data_type,
                        'data_length': data_length,
                        'nullable': 'Y' if column_info.get('NULLABLE', 'Y') == 'Y' else 'N',
                        'column_comments': column_info.get('COLUMN_COMMENTS', ''),
                        'position_pk': int(column_info.get('PK', '0')) if column_info.get('PK', '0').isdigit() else None,
                        'data_default': None,  # CSV에 없음
                        'owner': table_owner,
                        'has_error': has_error,
                        'error_message': error_message,
                        'hash_value': column_hash,
                        'del_yn': 'N'
                    }
                    column_data_list.append(column_data)
                    
                except Exception as e:
                    error_msg = f"컬럼 데이터 처리 실패: {str(e)}"
                    warning(f"컬럼 데이터 오류: {error_msg}")
                    # 오류가 있는 컬럼도 저장하되 오류 표시
                    column_data = {
                        'table_id': 0,  # 임시 ID
                        'column_name': column_info.get('COLUMN_NAME', 'UNKNOWN'),
                        'data_type': 'UNKNOWN',
                        'data_length': None,
                        'nullable': 'Y',
                        'column_comments': column_info.get('COLUMN_COMMENTS', ''),
                        'position_pk': None,
                        'data_default': None,
                        'owner': column_info.get('OWNER', 'UNKNOWN'),
                        'has_error': 'Y',
                        'error_message': error_msg,
                        'hash_value': '-',
                        'del_yn': 'N'
                    }
                    column_data_list.append(column_data)
            
            # 배치 INSERT OR REPLACE
            processed_count = self.db_utils.batch_insert_or_replace('columns', column_data_list)
            
            if processed_count > 0:
                self.stats['columns_loaded'] = processed_count
                
                # 오류가 있는 컬럼 수 계산
                error_count = sum(1 for column in column_data_list if column.get('has_error') == 'Y')
                self.stats['columns_with_errors'] = error_count
                
                info(f"컬럼 정보 저장 완료: {processed_count}개 컬럼 (오류: {error_count}개)")
                return True
            else:
                error("컬럼 정보 저장 실패")
                return False
                
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, "컬럼 정보 저장 실패")
            return False
    
    def create_table_components(self) -> bool:
        """
        tables 테이블의 모든 테이블을 components 테이블에 TABLE 타입으로 등록
        
        Returns:
            등록 성공 여부
        """
        try:
            # 프로젝트 ID 조회
            project_id = self.get_project_id()
            if not project_id:
                error("프로젝트 ID를 찾을 수 없습니다")
                return False
            
            # ALL_TABLES.csv 파일 ID 조회
            all_tables_file_id = self._get_csv_file_id("ALL_TABLES.csv")
            if not all_tables_file_id:
                error("ALL_TABLES.csv 파일 ID를 찾을 수 없습니다")
                return False
            
            # tables 테이블에서 모든 테이블 조회
            query = """
                SELECT table_id, table_name, table_owner, table_comments, hash_value
                FROM tables 
                WHERE project_id = ? AND del_yn = 'N'
            """
            tables = self.db_utils.execute_query(query, (project_id,))
            
            if not tables:
                warning("등록할 테이블이 없습니다")
                return True
            
            # 컴포넌트 데이터 생성
            component_data_list = []
            for table in tables:
                component_data = {
                    'project_id': project_id,
                    'file_id': all_tables_file_id,
                    'component_name': table['table_name'],
                    'component_type': 'TABLE',
                    'parent_id': None,
                    'layer': 'DB',
                    'line_start': None,
                    'line_end': None,
                    'has_error': 'N',
                    'error_message': None,
                    'hash_value': table['hash_value'],
                    'del_yn': 'N'
                }
                component_data_list.append(component_data)
            
            # 배치 INSERT OR REPLACE
            processed_count = self.db_utils.batch_insert_or_replace('components', component_data_list)
            
            if processed_count > 0:
                self.stats['components_created'] = processed_count
                info(f"테이블 컴포넌트 생성 완료: {processed_count}개")
                
                # tables 테이블의 component_id 업데이트
                self._update_table_component_ids(project_id)
                
                return True
            else:
                error("테이블 컴포넌트 생성 실패")
                return False
                
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, "테이블 컴포넌트 생성 실패")
            return False
    
    def create_column_components(self) -> bool:
        """
        columns 테이블의 모든 컬럼을 components 테이블에 COLUMN 타입으로 등록
        
        Returns:
            등록 성공 여부
        """
        try:
            # 프로젝트 ID 조회
            project_id = self.get_project_id()
            if not project_id:
                error("프로젝트 ID를 찾을 수 없습니다")
                return False
            
            # ALL_TAB_COLUMNS.csv 파일 ID 조회
            all_columns_file_id = self._get_csv_file_id("ALL_TAB_COLUMNS.csv")
            if not all_columns_file_id:
                error("ALL_TAB_COLUMNS.csv 파일 ID를 찾을 수 없습니다")
                return False
            
            # columns 테이블에서 모든 컬럼 조회
            query = """
                SELECT c.column_id, c.column_name, c.data_type, c.data_length, 
                       c.nullable, c.column_comments, c.position_pk, c.owner,
                       c.hash_value, t.table_name, t.table_owner
                FROM columns c
                JOIN tables t ON c.table_id = t.table_id
                WHERE t.project_id = ? AND c.del_yn = 'N' AND t.del_yn = 'N'
            """
            columns = self.db_utils.execute_query(query, (project_id,))
            
            if not columns:
                warning("등록할 컬럼이 없습니다")
                return True
            
            # 컴포넌트 데이터 생성
            component_data_list = []
            for column in columns:
                # 테이블의 component_id 조회
                table_component_id = self._get_table_component_id(
                    column['table_name'], 
                    column.get('table_owner')
                )
                
                component_data = {
                    'project_id': project_id,
                    'file_id': all_columns_file_id,
                    'component_name': column['column_name'],  # 컬럼명만 사용
                    'component_type': 'COLUMN',
                    'parent_id': table_component_id,  # 테이블의 component_id 설정
                    'layer': 'DB',
                    'line_start': None,
                    'line_end': None,
                    'has_error': 'N',
                    'error_message': None,
                    'hash_value': column['hash_value'],
                    'del_yn': 'N'
                }
                component_data_list.append(component_data)
            
            # 배치 INSERT OR REPLACE
            processed_count = self.db_utils.batch_insert_or_replace('components', component_data_list)
            
            if processed_count > 0:
                self.stats['components_created'] += processed_count
                info(f"컬럼 컴포넌트 생성 완료: {processed_count}개")
                
                # 🔥 새로 추가: columns 테이블의 component_id 업데이트
                self._update_columns_component_id(columns, component_data_list)
                
                return True
            else:
                error("컬럼 컴포넌트 생성 실패")
                return False
                
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, "컬럼 컴포넌트 생성 실패")
            return False
    
    def _update_columns_component_id(self, columns: List[Dict[str, Any]], component_data_list: List[Dict[str, Any]]) -> bool:
        """
        columns 테이블의 component_id 업데이트
        
        Args:
            columns: 컬럼 정보 리스트
            component_data_list: 컴포넌트 데이터 리스트
            
        Returns:
            업데이트 성공 여부
        """
        try:
            # 컬럼명을 기준으로 매핑 테이블 생성
            column_name_to_component_id = {}
            for component_data in component_data_list:
                column_name = component_data['component_name']
                # components 테이블에서 생성된 component_id 조회
                component_id = self._get_component_id_by_name_and_parent(
                    component_data['project_id'],
                    column_name,
                    component_data['parent_id']
                )
                if component_id:
                    column_name_to_component_id[column_name] = component_id
            
            # columns 테이블 업데이트
            updated_count = 0
            for column in columns:
                column_name = column['column_name']
                if column_name in column_name_to_component_id:
                    component_id = column_name_to_component_id[column_name]
                    
                    # columns 테이블의 component_id 업데이트
                    update_data = {'component_id': component_id}
                    where_conditions = {'column_id': column['column_id']}
                    
                    success = self.db_utils.update_record('columns', update_data, where_conditions)
                    if success:
                        updated_count += 1
                    else:
                        warning(f"컬럼 component_id 업데이트 실패: {column_name}")
            
            if updated_count > 0:
                info(f"컬럼 component_id 업데이트 완료: {updated_count}개")
                return True
            else:
                warning("컬럼 component_id 업데이트 실패")
                return False
                
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, "컬럼 component_id 업데이트 실패")
            return False
    
    def _get_component_id_by_name_and_parent(self, project_id: int, component_name: str, parent_id: int) -> Optional[int]:
        """
        컴포넌트명과 부모 ID로 component_id 조회
        
        Args:
            project_id: 프로젝트 ID
            component_name: 컴포넌트명
            parent_id: 부모 ID
            
        Returns:
            component_id 또는 None
        """
        try:
            query = """
                SELECT component_id FROM components 
                WHERE project_id = ? AND component_name = ? AND parent_id = ? AND del_yn = 'N'
            """
            results = self.db_utils.execute_query(query, (project_id, component_name, parent_id))
            
            if results and len(results) > 0:
                return results[0]['component_id']
            return None
            
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, f"컴포넌트 ID 조회 실패: {component_name}")
            return None
    
    def _get_table_component_id(self, table_name: str, table_owner: str = None) -> Optional[int]:
        """
        테이블명으로 테이블의 component_id 조회
        
        Args:
            table_name: 테이블명
            table_owner: 테이블 소유자 (선택사항)
            
        Returns:
            테이블의 component_id 또는 None
        """
        try:
            if table_owner:
                query = """
                    SELECT t.component_id 
                    FROM tables t
                    JOIN projects p ON t.project_id = p.project_id
                    WHERE p.project_name = ? AND t.table_name = ? AND t.table_owner = ? AND t.del_yn = 'N'
                """
                results = self.db_utils.execute_query(query, (self.project_name, table_name, table_owner))
            else:
                query = """
                    SELECT t.component_id 
                    FROM tables t
                    JOIN projects p ON t.project_id = p.project_id
                    WHERE p.project_name = ? AND t.table_name = ? AND t.del_yn = 'N'
                """
                results = self.db_utils.execute_query(query, (self.project_name, table_name))
            
            if results:
                return results[0]['component_id']
            return None
            
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, f"테이블 component_id 조회 실패: {table_name}")
            return None

    def _get_csv_file_id(self, filename: str) -> Optional[int]:
        """
        CSV 파일의 file_id 조회
        
        Args:
            filename: 파일명
            
        Returns:
            file_id 또는 None
        """
        try:
            query = """
                SELECT f.file_id 
                FROM files f
                JOIN projects p ON f.project_id = p.project_id
                WHERE p.project_name = ? AND f.file_name = ? AND f.del_yn = 'N'
            """
            results = self.db_utils.execute_query(query, (self.project_name, filename))
            
            if results:
                return results[0]['file_id']
            return None
            
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, f"CSV 파일 ID 조회 실패: {filename}")
            return None
    
    def _get_table_id(self, owner: str, table_name: str) -> Optional[int]:
        """
        테이블 ID 조회
        
        Args:
            owner: 테이블 소유자
            table_name: 테이블명
            
        Returns:
            table_id 또는 None
        """
        try:
            query = """
                SELECT t.table_id 
                FROM tables t
                JOIN projects p ON t.project_id = p.project_id
                WHERE p.project_name = ? AND t.table_owner = ? AND t.table_name = ? AND t.del_yn = 'N'
            """
            results = self.db_utils.execute_query(query, (self.project_name, owner, table_name))
            
            if results:
                return results[0]['table_id']
            return None
            
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, f"테이블 ID 조회 실패: {owner}.{table_name}")
            return None
    
    def _update_table_component_ids(self, project_id: int):
        """
        tables 테이블의 component_id 업데이트
        
        Args:
            project_id: 프로젝트 ID
        """
        try:
            query = """
                UPDATE tables 
                SET component_id = (
                    SELECT c.component_id 
                    FROM components c 
                    WHERE c.project_id = tables.project_id 
                    AND c.component_name = tables.table_name 
                    AND c.component_type = 'TABLE' 
                    AND c.del_yn = 'N'
                )
                WHERE project_id = ? AND del_yn = 'N'
            """
            self.db_utils.execute_update(query, (project_id,))
            debug("테이블 component_id 업데이트 완료")
            
        except Exception as e:
            warning(f"테이블 component_id 업데이트 실패: {str(e)}")
    
    def execute_file_scan(self, clear_metadb: bool = False) -> bool:
        """
        파일 스캔 실행: 파일 정보 저장 (프로젝트 전체 스캔)
        
        Args:
            clear_metadb: 메타데이터베이스 초기화 여부
            
        Returns:
            실행 성공 여부
        """
        try:
            # info("=== 파일 스캔 시작: 파일 정보 저장 ===")  # 로그 제거
            
            # 1. 메타데이터베이스 초기화
            if not self.initialize_database(clear_metadb):
                return False
            
            # 2. 프로젝트 정보 저장
            if not self.add_project_info():
                return False
            
            # 3. 프로젝트 전체 파일 스캔
            scanned_files = self.scan_project_files()
            if not scanned_files:
                warning("스캔된 파일이 없습니다")
                return False
            
            # 4. 파일 정보를 데이터베이스에 저장
            if not self.save_files_to_database(scanned_files):
                return False
            
            # 5. 통계 정보 출력
            self._print_statistics()
            
            info("=== 파일 스캔 완료 ===")
            return True
            
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, "파일 스캔 실행 실패")
            return False
        finally:
            # 데이터베이스 연결 해제
            if self.db_utils:
                self.db_utils.disconnect()
    
    def execute_db_loading(self) -> bool:
        """
        데이터베이스 로딩 실행: 데이터베이스 구조 저장 및 컴포넌트 생성
        
        Returns:
            실행 성공 여부
        """
        try:
            info("=== 데이터베이스 로딩 시작: 데이터베이스 구조 저장 ===")
            
            # 데이터베이스 연결
            self.db_utils = DatabaseUtils(self.metadata_db_path)
            if not self.db_utils.connect():
                error("메타데이터베이스 연결 실패")
                return False
            
            # 1. ALL_TABLES.csv 로드 및 저장
            all_tables_path = os.path.join(self.project_db_schema_path, "ALL_TABLES.csv")
            tables_data = self.load_csv_file(all_tables_path)
            if not self.save_tables_to_database(tables_data):
                return False
            
            # 2. ALL_TAB_COLUMNS.csv 로드 및 저장
            all_columns_path = os.path.join(self.project_db_schema_path, "ALL_TAB_COLUMNS.csv")
            columns_data = self.load_csv_file(all_columns_path)
            if not self.save_columns_to_database(columns_data):
                return False
            
            # 3. 테이블을 components에 TABLE 타입으로 등록
            if not self.create_table_components():
                return False
            
            # 4. 컬럼을 components에 COLUMN 타입으로 등록
            if not self.create_column_components():
                return False
            
            # 5. 통계 정보 출력
            self._print_db_loading_statistics()
            
            info("=== 데이터베이스 로딩 완료 ===")
            return True
            
        except Exception as e:
            # 파싱에러를 제외한 모든 exception발생시 handle_error()로 exit()해야 에러인지가 가능함.
            handle_error(e, "데이터베이스 로딩 실행 실패")
            return False
        finally:
            # 데이터베이스 연결 해제
            if self.db_utils:
                self.db_utils.disconnect()
    
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
