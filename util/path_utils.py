"""
SourceAnalyzer 경로 처리 공통 유틸리티 모듈
- 상대경로/절대경로 변환
- 경로 정규화
- 경로 검증
- 프로젝트 루트 기준 경로 처리
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from .logger import app_logger, handle_error, error


class PathUtils:
    """경로 처리 관련 공통 유틸리티 클래스"""
    
    def __init__(self, project_root: str = None):
        """
        경로 유틸리티 초기화
        
        Args:
            project_root: 프로젝트 루트 경로 (기본값: 현재 작업 디렉토리)
        """
        if project_root is None:
            # 현재 스크립트가 실행되는 디렉토리를 프로젝트 루트로 설정
            # util 폴더의 상위 디렉토리가 프로젝트 루트
            current_file = os.path.abspath(__file__)
            util_dir = os.path.dirname(current_file)
            self.project_root = os.path.dirname(util_dir)  # util의 상위 디렉토리
        else:
            self.project_root = os.path.abspath(project_root)
    
    def normalize_path(self, path: str) -> str:
        """
        경로 정규화 (절대경로로 변환)
        
        Args:
            path: 정규화할 경로
            
        Returns:
            정규화된 절대경로
        """
        try:
            if not path:
                return ""
            
            # 절대경로인 경우 그대로 정규화
            if os.path.isabs(path):
                return os.path.normpath(path)
            
            # 상대경로인 경우 프로젝트 루트 기준으로 변환
            return os.path.normpath(os.path.join(self.project_root, path))
            
        except Exception as e:
            handle_error(e, f"경로 정규화 실패: {path}")
            return path
    
    def get_relative_path(self, target_path: str, base_path: str = None) -> str:
        """
        상대경로 생성
        
        Args:
            target_path: 대상 경로
            base_path: 기준 경로 (기본값: 프로젝트 루트)
            
        Returns:
            상대경로
        """
        try:
            if not target_path:
                return ""
            
            if base_path is None:
                base_path = self.project_root
            
            # 경로 정규화
            target_abs = self.normalize_path(target_path)
            base_abs = self.normalize_path(base_path)
            
            # 상대경로 생성
            relative_path = os.path.relpath(target_abs, base_abs)
            
            # Windows에서 상대경로가 상위 디렉토리로 나가는 경우 처리
            if relative_path.startswith('..'):
                # USER RULE: 모든 exception 발생시 handle_error()로 exit()
                handle_error(Exception(f"상대경로가 프로젝트 루트를 벗어남: {target_path}"), f"경로 오류: {target_path}")
            
            return relative_path
            
        except ValueError:
            # 다른 드라이브에 있는 경우 절대경로 반환
            # USER RULE: 모든 exception 발생시 handle_error()로 exit()
            handle_error(Exception(f"다른 드라이브 경로: {target_path}"), f"경로 오류: {target_path}")
        except Exception as e:
            handle_error(e, f"상대경로 생성 실패: {target_path}")
            return target_path
    
    def get_absolute_path(self, path: str) -> str:
        """
        절대경로 생성
        
        Args:
            path: 경로
            
        Returns:
            절대경로
        """
        return self.normalize_path(path)
    
    def is_absolute_path(self, path: str) -> bool:
        """
        절대경로 여부 확인
        
        Args:
            path: 확인할 경로
            
        Returns:
            절대경로 여부 (True/False)
        """
        return os.path.isabs(path)
    
    def is_relative_path(self, path: str) -> bool:
        """
        상대경로 여부 확인
        
        Args:
            path: 확인할 경로
            
        Returns:
            상대경로 여부 (True/False)
        """
        return not os.path.isabs(path)
    
    def is_within_project(self, path: str) -> bool:
        """
        경로가 프로젝트 루트 내부에 있는지 확인
        
        Args:
            path: 확인할 경로
            
        Returns:
            프로젝트 내부 여부 (True/False)
        """
        try:
            abs_path = self.normalize_path(path)
            project_abs = self.normalize_path(self.project_root)
            
            # 공통 경로 확인
            common_path = os.path.commonpath([abs_path, project_abs])
            return common_path == project_abs
            
        except Exception as e:
            handle_error(e, f"프로젝트 내부 경로 확인 실패: {path}")
            return False
    
    def join_path(self, *paths: str) -> str:
        """
        경로 결합 (프로젝트 루트 기준)
        
        Args:
            *paths: 결합할 경로들
            
        Returns:
            결합된 경로
        """
        try:
            # 빈 경로 제거
            valid_paths = [p for p in paths if p]
            if not valid_paths:
                return self.project_root
            
            # 첫 번째 경로가 절대경로인 경우
            if os.path.isabs(valid_paths[0]):
                return os.path.normpath(os.path.join(*valid_paths))
            
            # 상대경로인 경우 프로젝트 루트 기준으로 결합
            return os.path.normpath(os.path.join(self.project_root, *valid_paths))
            
        except Exception as e:
            handle_error(e, f"경로 결합 실패: {paths}")
            return ""
    
    def get_project_relative_path(self, path: str) -> str:
        """
        프로젝트 루트 기준 상대경로 생성
        
        Args:
            path: 대상 경로
            
        Returns:
            프로젝트 루트 기준 상대경로
        """
        return self.get_relative_path(path, self.project_root)
    
    def resolve_path(self, path: str) -> str:
        """
        경로 해석 (심볼릭 링크, .., . 처리)
        
        Args:
            path: 해석할 경로
            
        Returns:
            해석된 경로
        """
        try:
            return os.path.realpath(self.normalize_path(path))
        except Exception as e:
            handle_error(e, f"경로 해석 실패: {path}")
            return self.normalize_path(path)
    
    def get_path_components(self, path: str) -> Dict[str, str]:
        """
        경로 구성 요소 분해
        
        Args:
            path: 분해할 경로
            
        Returns:
            경로 구성 요소 딕셔너리
        """
        try:
            path_obj = Path(self.normalize_path(path))
            
            return {
                'absolute_path': str(path_obj.absolute()),
                'relative_path': self.get_project_relative_path(path),
                'directory': str(path_obj.parent),
                'filename': path_obj.name,
                'stem': path_obj.stem,
                'suffix': path_obj.suffix,
                'root': str(path_obj.anchor),
                'parts': list(path_obj.parts)
            }
            
        except Exception as e:
            handle_error(e, f"경로 구성 요소 분해 실패: {path}")
            return {}
    
    def get_filename(self, path: str) -> str:
        """
        경로에서 파일명 추출
        
        Args:
            path: 파일 경로
            
        Returns:
            파일명
        """
        try:
            return os.path.basename(self.normalize_path(path))
        except Exception as e:
            handle_error(e, f"파일명 추출 실패: {path}")
            return ""
    
    def get_directory_path(self, path: str) -> str:
        """
        경로에서 디렉토리 경로 추출
        
        Args:
            path: 파일 경로
            
        Returns:
            디렉토리 경로
        """
        try:
            return os.path.dirname(self.normalize_path(path))
        except Exception as e:
            handle_error(e, f"디렉토리 경로 추출 실패: {path}")
            return ""
    

    
    def convert_to_windows_path(self, path: str) -> str:
        """
        Unix 경로를 Windows 스타일로 변환
        
        Args:
            path: 변환할 경로
            
        Returns:
            Windows 스타일 경로
        """
        return path.replace('/', '\\')
    
    def normalize_path_separator(self, path: str, target_platform: str = 'auto') -> str:
        """
        경로 구분자를 플랫폼에 맞게 정규화
        
        Args:
            path: 정규화할 경로
            target_platform: 대상 플랫폼 ('windows', 'unix', 'auto')
            
        Returns:
            정규화된 경로
        """
        try:
            if not path:
                return ""
            
            if target_platform == 'auto':
                # 현재 플랫폼에 맞게 정규화
                return os.path.normpath(path)
            elif target_platform == 'windows':
                # Windows 스타일로 변환
                return path.replace('/', '\\')
            elif target_platform == 'unix':
                # Unix 스타일로 변환
                return path.replace('\\', '/')
            else:
                return path
                
        except Exception as e:
            handle_error(e, f"경로 구분자 정규화 실패: {path}")
            return path
    
    def is_cross_platform_path(self, path: str) -> bool:
        """
        크로스플랫폼 경로인지 확인 (Windows와 Unix 구분자가 혼재)
        
        Args:
            path: 확인할 경로
            
        Returns:
            크로스플랫폼 경로 여부
        """
        try:
            if not path:
                return False
            
            # Windows와 Unix 구분자가 모두 있는지 확인
            has_windows_sep = '\\' in path
            has_unix_sep = '/' in path
            
            return has_windows_sep and has_unix_sep
            
        except Exception as e:
            handle_error(e, f"크로스플랫폼 경로 확인 실패: {path}")
            return False
    
    def get_common_path(self, paths: List[str]) -> str:
        """
        여러 경로의 공통 경로 찾기
        
        Args:
            paths: 경로 리스트
            
        Returns:
            공통 경로
        """
        try:
            if not paths:
                return ""
            
            if len(paths) == 1:
                return os.path.dirname(self.normalize_path(paths[0]))
            
            # 모든 경로를 절대경로로 변환
            abs_paths = [self.normalize_path(path) for path in paths]
            
            # 공통 경로 찾기
            common_path = os.path.commonpath(abs_paths)
            return common_path
            
        except Exception as e:
            handle_error(e, f"공통 경로 찾기 실패: {paths}")
            return ""
    
    def is_same_path(self, path1: str, path2: str) -> bool:
        """
        두 경로가 같은 경로인지 확인 (정규화 후 비교)
        
        Args:
            path1: 첫 번째 경로
            path2: 두 번째 경로
            
        Returns:
            같은 경로 여부 (True/False)
        """
        try:
            norm_path1 = self.resolve_path(path1)
            norm_path2 = self.resolve_path(path2)
            return norm_path1 == norm_path2
            
        except Exception as e:
            handle_error(e, f"경로 비교 실패: {path1}, {path2}")
            return False
    
    def get_path_depth(self, path: str) -> int:
        """
        경로 깊이 계산 (프로젝트 루트 기준)
        
        Args:
            path: 깊이를 계산할 경로
            
        Returns:
            경로 깊이
        """
        try:
            relative_path = self.get_project_relative_path(path)
            if relative_path == '.' or relative_path == '':
                return 0
            
            # 경로 구분자로 분할하여 깊이 계산
            parts = [part for part in relative_path.split(os.sep) if part and part != '.']
            return len(parts)
            
        except Exception as e:
            handle_error(e, f"경로 깊이 계산 실패: {path}")
            return 0
    
    def find_files_by_pattern(self, directory: str, pattern: str, recursive: bool = True) -> List[str]:
        """
        패턴에 맞는 파일 찾기
        
        Args:
            directory: 검색할 디렉토리
            pattern: 파일 패턴 (예: "*.java", "**/*.xml")
            recursive: 재귀 검색 여부
            
        Returns:
            찾은 파일 경로 리스트
        """
        try:
            import glob
            
            search_dir = self.normalize_path(directory)
            if not os.path.exists(search_dir):
                app_logger.warning(f"디렉토리가 존재하지 않습니다: {search_dir}")
                return []
            
            # 패턴에 따라 검색
            if recursive and '**' not in pattern:
                pattern = f"**/{pattern}"
            
            search_pattern = os.path.join(search_dir, pattern)
            files = glob.glob(search_pattern, recursive=recursive)
            
            # 프로젝트 기준 상대경로로 변환
            relative_files = [self.get_project_relative_path(f) for f in files]
            
            app_logger.debug(f"패턴 검색 완료: {pattern}, 찾은 파일 수: {len(relative_files)}")
            return relative_files
            
        except Exception as e:
            handle_error(e, f"패턴 검색 실패: {directory}, {pattern}")
            return []
    
    def create_relative_path_structure(self, base_path: str, target_path: str) -> str:
        """
        기준 경로에서 대상 경로로의 상대경로 구조 생성
        
        Args:
            base_path: 기준 경로
            target_path: 대상 경로
            
        Returns:
            상대경로 구조
        """
        try:
            base_abs = self.normalize_path(base_path)
            target_abs = self.normalize_path(target_path)
            
            # 상대경로 생성
            relative = os.path.relpath(target_abs, base_abs)
            
            # .. 개수 계산
            up_levels = relative.count('..')
            
            # 상대경로 구조 정보
            structure = {
                'relative_path': relative,
                'up_levels': up_levels,
                'is_within_base': up_levels == 0,
                'target_depth': self.get_path_depth(target_path),
                'base_depth': self.get_path_depth(base_path)
            }
            
            return relative
            
        except Exception as e:
            handle_error(e, f"상대경로 구조 생성 실패: {base_path}, {target_path}")
            return target_path
    
    def validate_path_format(self, path: str) -> Dict[str, Any]:
        """
        경로 형식 검증
        
        Args:
            path: 검증할 경로
            
        Returns:
            검증 결과 딕셔너리
        """
        try:
            result = {
                'is_valid': True,
                'is_absolute': self.is_absolute_path(path),
                'is_relative': self.is_relative_path(path),
                'is_within_project': self.is_within_project(path),
                'normalized_path': self.normalize_path(path),
                'project_relative': self.get_project_relative_path(path),
                'components': self.get_path_components(path),
                'depth': self.get_path_depth(path),
                'errors': []
            }
            
            # 경로 유효성 검사
            if not path or not isinstance(path, str):
                result['is_valid'] = False
                result['errors'].append("경로가 비어있거나 문자열이 아님")
            
            # 특수 문자 검사
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
            for char in invalid_chars:
                if char in path:
                    result['is_valid'] = False
                    result['errors'].append(f"잘못된 문자 포함: {char}")
            
            # 경로 길이 검사
            if len(path) > 260:  # Windows 경로 길이 제한
                result['is_valid'] = False
                result['errors'].append("경로가 너무 깁니다 (260자 초과)")
            
            return result
            
        except Exception as e:
            handle_error(e, f"경로 형식 검증 실패: {path}")
            return {
                'is_valid': False,
                'errors': [f"검증 중 오류 발생: {str(e)}"]
            }
    
    def get_project_source_path(self, project_name: str) -> str:
        """
        프로젝트 소스 경로 생성 (project_root/projects/{project_name})
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            프로젝트 소스 경로
        """
        return self.join_path("projects", project_name)
    
    def get_project_config_path(self, project_name: str) -> str:
        """
        프로젝트 설정 경로 생성 (project_root/projects/{project_name}/config)
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            프로젝트 설정 경로
        """
        return self.join_path("projects", project_name, "config")
    
    def get_project_src_path(self, project_name: str) -> str:
        """
        프로젝트 소스코드 경로 생성 (project_root/projects/{project_name}/src)
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            프로젝트 소스코드 경로
        """
        return self.join_path("projects", project_name, "src")
    
    def get_project_db_schema_path(self, project_name: str) -> str:
        """
        프로젝트 DB 스키마 경로 생성 (project_root/projects/{project_name}/db_schema)
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            프로젝트 DB 스키마 경로
        """
        return self.join_path("projects", project_name, "db_schema")
    
    def get_project_report_path(self, project_name: str) -> str:
        """
        프로젝트 리포트 경로 생성 (project_root/projects/{project_name}/report)
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            프로젝트 리포트 경로
        """
        return self.join_path("projects", project_name, "report")
    
    def get_project_metadata_db_path(self, project_name: str) -> str:
        """
        프로젝트 메타데이터 DB 경로 생성 (project_root/projects/{project_name}/metadata.db)
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            프로젝트 메타데이터 DB 경로
        """
        return self.join_path("projects", project_name, "metadata.db")
    
    def get_metadata_db_path(self, project_name: str) -> str:
        """
        메타데이터 DB 경로 생성 (get_project_metadata_db_path의 별칭)
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            메타데이터 DB 경로
        """
        return self.get_project_metadata_db_path(project_name)
    
    def get_project_path(self, project_name: str) -> str:
        """
        프로젝트 경로 생성 (project_root/projects/{project_name})
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            프로젝트 경로
        """
        return self.join_path("projects", project_name)
    
    def get_config_path(self, config_filename: str) -> str:
        """
        설정 파일 경로 생성 (project_root/config/{config_filename})
        
        Args:
            config_filename: 설정 파일명
            
        Returns:
            설정 파일 경로
        """
        return self.join_path("config", config_filename)
    
    def get_database_schema_path(self) -> str:
        """
        데이터베이스 스키마 파일 경로 생성 (project_root/database/create_table_script.sql)
        
        Returns:
            데이터베이스 스키마 파일 경로
        """
        return self.join_path("database", "create_table_script.sql")
    
    def get_logs_path(self) -> str:
        """
        로그 디렉토리 경로 생성 (project_root/logs)
        
        Returns:
            로그 디렉토리 경로
        """
        return self.join_path("logs")
    
    def get_reports_path(self) -> str:
        """
        리포트 디렉토리 경로 생성 (project_root/reports)
        
        Returns:
            리포트 디렉토리 경로
        """
        return self.join_path("reports")
    
    def get_parser_config_path(self, parser_type: str) -> str:
        """
        파서 설정 파일 경로 생성 (project_root/config/parser/{parser_type}_keyword.yaml)
        
        Args:
            parser_type: 파서 타입 (java, xml, jsp, sql 등)
            
        Returns:
            파서 설정 파일 경로
        """
        return self.join_path("config", "parser", f"{parser_type}_keyword.yaml")
    
    def list_projects(self) -> List[str]:
        """
        프로젝트 목록 조회 (projects 디렉토리 하위)
        
        Returns:
            프로젝트명 리스트
        """
        try:
            projects_dir = self.join_path("projects")
            if not os.path.exists(projects_dir):
                return []
            
            projects = []
            for item in os.listdir(projects_dir):
                item_path = os.path.join(projects_dir, item)
                if os.path.isdir(item_path):
                    projects.append(item)
            
            return sorted(projects)
            
        except Exception as e:
            handle_error(e, "프로젝트 목록 조회 실패")
            return []
    
    def project_exists(self, project_name: str) -> bool:
        """
        프로젝트 존재 여부 확인
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            프로젝트 존재 여부 (True/False)
        """
        project_path = self.get_project_source_path(project_name)
        return os.path.exists(project_path) and os.path.isdir(project_path)
    
    def exists(self, path: str) -> bool:
        """
        경로 존재 여부 확인
        
        Args:
            path: 확인할 경로
            
        Returns:
            경로 존재 여부 (True/False)
        """
        try:
            normalized_path = self.normalize_path(path)
            return os.path.exists(normalized_path)
        except Exception as e:
            handle_error(e, f"경로 존재 여부 확인 실패: {path}")
            return False
    
    def is_file(self, path: str) -> bool:
        """
        파일 여부 확인
        
        Args:
            path: 확인할 경로
            
        Returns:
            파일 여부 (True/False)
        """
        try:
            normalized_path = self.normalize_path(path)
            return os.path.isfile(normalized_path)
        except Exception as e:
            handle_error(e, f"파일 여부 확인 실패: {path}")
            return False
    
    def is_dir(self, path: str) -> bool:
        """
        디렉토리 여부 확인
        
        Args:
            path: 확인할 경로
            
        Returns:
            디렉토리 여부 (True/False)
        """
        try:
            normalized_path = self.normalize_path(path)
            return os.path.isdir(normalized_path)
        except Exception as e:
            handle_error(e, f"디렉토리 여부 확인 실패: {path}")
            return False
    
    def makedirs(self, path: str, exist_ok: bool = True) -> bool:
        """
        디렉토리 생성 (중간 디렉토리도 함께 생성)
        
        Args:
            path: 생성할 디렉토리 경로
            exist_ok: 이미 존재하는 경우 오류 무시 여부
            
        Returns:
            생성 성공 여부 (True/False)
        """
        try:
            normalized_path = self.normalize_path(path)
            os.makedirs(normalized_path, exist_ok=exist_ok)
            return True
        except Exception as e:
            handle_error(e, f"디렉토리 생성 실패: {path}")
            return False
    
    def get_table_component_id(self, project_name: str, table_name: str, table_owner: str = None) -> Optional[int]:
        """
        테이블명으로 테이블의 component_id 조회
        
        Args:
            project_name: 프로젝트명
            table_name: 테이블명
            table_owner: 테이블 소유자 (선택사항)
            
        Returns:
            테이블의 component_id 또는 None
        """
        try:
            from .database_utils import DatabaseUtils
            
            # 캐시에서 먼저 조회
            cache = DatabaseCache()
            cached_id = cache.get_table_component_id(project_name, table_name)
            if cached_id is not None:
                return cached_id
            
            # 데이터베이스에서 조회
            db_utils = DatabaseUtils()
            if not db_utils.connect_to_metadata_db(project_name):
                return None
            
            try:
                if table_owner:
                    query = """
                        SELECT t.component_id 
                        FROM tables t
                        JOIN projects p ON t.project_id = p.project_id
                        WHERE p.project_name = ? AND t.table_name = ? AND t.table_owner = ? AND t.del_yn = 'N'
                    """
                    results = db_utils.execute_query(query, (project_name, table_name.upper(), table_owner.upper()))
                else:
                    query = """
                        SELECT t.component_id 
                        FROM tables t
                        JOIN projects p ON t.project_id = p.project_id
                        WHERE p.project_name = ? AND t.table_name = ? AND t.del_yn = 'N'
                    """
                    results = db_utils.execute_query(query, (project_name, table_name.upper()))
                
                if results:
                    component_id = results[0]['component_id']
                    # 캐시에 저장
                    cache.set_table_component_id(project_name, table_name, component_id)
                    return component_id
                return None
                
            finally:
                db_utils.disconnect()
                
        except Exception as e:
            handle_error(e, f"테이블 component_id 조회 실패: {project_name}.{table_name}")
            return None
    
    def get_columns_by_table_component_id(self, project_name: str, table_component_id: int) -> List[Dict[str, Any]]:
        """
        테이블의 component_id로 해당 테이블의 모든 컬럼 조회
        
        Args:
            project_name: 프로젝트명
            table_component_id: 테이블의 component_id
            
        Returns:
            컬럼 정보 리스트
        """
        try:
            from .database_utils import DatabaseUtils
            
            db_utils = DatabaseUtils()
            if not db_utils.connect_to_metadata_db(project_name):
                return []
            
            try:
                query = """
                    SELECT c.*, comp.component_name, comp.component_type
                    FROM columns c
                    JOIN components comp ON c.table_id = (
                        SELECT t.table_id 
                        FROM tables t 
                        WHERE t.component_id = ?
                    )
                    WHERE comp.parent_id = ? AND comp.component_type = 'COLUMN' AND comp.del_yn = 'N'
                """
                results = db_utils.execute_query(query, (table_component_id, table_component_id))
                return results if results else []
                
            finally:
                db_utils.disconnect()
                
        except Exception as e:
            handle_error(e, f"테이블 컬럼 조회 실패: {project_name}, component_id={table_component_id}")
            return []
    
    def get_column_component_by_name_and_parent(self, project_name: str, column_name: str, parent_id: int) -> Optional[Dict[str, Any]]:
        """
        컬럼명과 parent_id로 컬럼 컴포넌트 조회
        
        Args:
            project_name: 프로젝트명
            column_name: 컬럼명
            parent_id: 부모 테이블의 component_id
            
        Returns:
            컬럼 컴포넌트 정보 또는 None
        """
        try:
            from .database_utils import DatabaseUtils
            
            db_utils = DatabaseUtils()
            if not db_utils.connect_to_metadata_db(project_name):
                return None
            
            try:
                query = """
                    SELECT comp.*, c.*
                    FROM components comp
                    LEFT JOIN columns c ON comp.component_id = c.component_id
                    WHERE comp.project_id = (
                        SELECT project_id FROM projects WHERE project_name = ?
                    )
                    AND comp.component_name = ? 
                    AND comp.parent_id = ? 
                    AND comp.component_type = 'COLUMN' 
                    AND comp.del_yn = 'N'
                """
                results = db_utils.execute_query(query, (project_name, column_name, parent_id))
                return results[0] if results else None
                
            finally:
                db_utils.disconnect()
                
        except Exception as e:
            handle_error(e, f"컬럼 컴포넌트 조회 실패: {project_name}, {column_name}, parent_id={parent_id}")
            return None
    
    def get_components_by_parent_id(self, project_name: str, parent_id: int, component_type: str = None) -> List[Dict[str, Any]]:
        """
        parent_id로 하위 컴포넌트들 조회
        
        Args:
            project_name: 프로젝트명
            parent_id: 부모 컴포넌트 ID
            component_type: 컴포넌트 타입 필터 (선택사항)
            
        Returns:
            하위 컴포넌트 리스트
        """
        try:
            from .database_utils import DatabaseUtils
            
            db_utils = DatabaseUtils()
            if not db_utils.connect_to_metadata_db(project_name):
                return []
            
            try:
                if component_type:
                    query = """
                        SELECT * FROM components 
                        WHERE project_id = (
                            SELECT project_id FROM projects WHERE project_name = ?
                        )
                        AND parent_id = ? 
                        AND component_type = ? 
                        AND del_yn = 'N'
                    """
                    results = db_utils.execute_query(query, (project_name, parent_id, component_type))
                else:
                    query = """
                        SELECT * FROM components 
                        WHERE project_id = (
                            SELECT project_id FROM projects WHERE project_name = ?
                        )
                        AND parent_id = ? 
                        AND del_yn = 'N'
                    """
                    results = db_utils.execute_query(query, (project_name, parent_id))
                
                return results if results else []
                
            finally:
                db_utils.disconnect()
                
        except Exception as e:
            handle_error(e, f"하위 컴포넌트 조회 실패: {project_name}, parent_id={parent_id}")
            return []
    


# 편의 함수들
def normalize_path(path: str, project_root: str = None) -> str:
    """경로 정규화 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.normalize_path(path)


def get_relative_path(target_path: str, base_path: str = None, project_root: str = None) -> str:
    """상대경로 생성 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_relative_path(target_path, base_path)


def get_absolute_path(path: str, project_root: str = None) -> str:
    """절대경로 생성 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_absolute_path(path)


def is_within_project(path: str, project_root: str = None) -> bool:
    """프로젝트 내부 경로 확인 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.is_within_project(path)


def join_path(*paths: str, project_root: str = None) -> str:
    """경로 결합 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.join_path(*paths)


def get_project_source_path(project_name: str, project_root: str = None) -> str:
    """프로젝트 소스 경로 생성 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_project_source_path(project_name)


def get_project_config_path(project_name: str, project_root: str = None) -> str:
    """프로젝트 설정 경로 생성 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_project_config_path(project_name)


def get_project_src_path(project_name: str, project_root: str = None) -> str:
    """프로젝트 소스코드 경로 생성 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_project_src_path(project_name)


def get_project_db_schema_path(project_name: str, project_root: str = None) -> str:
    """프로젝트 DB 스키마 경로 생성 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_project_db_schema_path(project_name)


def get_project_report_path(project_name: str, project_root: str = None) -> str:
    """프로젝트 리포트 경로 생성 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_project_report_path(project_name)


def get_project_metadata_db_path(project_name: str, project_root: str = None) -> str:
    """프로젝트 메타데이터 DB 경로 생성 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_project_metadata_db_path(project_name)


def get_metadata_db_path(project_name: str, project_root: str = None) -> str:
    """메타데이터 DB 경로 생성 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_metadata_db_path(project_name)


def get_config_path(config_filename: str, project_root: str = None) -> str:
    """설정 파일 경로 생성 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_config_path(config_filename)


def get_database_schema_path(project_root: str = None) -> str:
    """데이터베이스 스키마 파일 경로 생성 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_database_schema_path()


def get_parser_config_path(parser_type: str, project_root: str = None) -> str:
    """파서 설정 파일 경로 생성 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_parser_config_path(parser_type)


def list_projects(project_root: str = None) -> List[str]:
    """프로젝트 목록 조회 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.list_projects()


def project_exists(project_name: str, project_root: str = None) -> bool:
    """프로젝트 존재 여부 확인 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.project_exists(project_name)


def get_table_component_id(project_name: str, table_name: str, table_owner: str = None, project_root: str = None) -> Optional[int]:
    """테이블 component_id 조회 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_table_component_id(project_name, table_name, table_owner)


def get_columns_by_table_component_id(project_name: str, table_component_id: int, project_root: str = None) -> List[Dict[str, Any]]:
    """테이블의 component_id로 컬럼 조회 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_columns_by_table_component_id(project_name, table_component_id)


def get_column_component_by_name_and_parent(project_name: str, column_name: str, parent_id: int, project_root: str = None) -> Optional[Dict[str, Any]]:
    """컬럼명과 parent_id로 컬럼 컴포넌트 조회 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_column_component_by_name_and_parent(project_name, column_name, parent_id)


def get_components_by_parent_id(project_name: str, parent_id: int, component_type: str = None, project_root: str = None) -> List[Dict[str, Any]]:
    """parent_id로 하위 컴포넌트 조회 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.get_components_by_parent_id(project_name, parent_id, component_type)


def exists(path: str, project_root: str = None) -> bool:
    """경로 존재 여부 확인 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.exists(path)


def is_file(path: str, project_root: str = None) -> bool:
    """파일 여부 확인 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.is_file(path)


def is_dir(path: str, project_root: str = None) -> bool:
    """디렉토리 여부 확인 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.is_dir(path)


def makedirs(path: str, exist_ok: bool = True, project_root: str = None) -> bool:
    """디렉토리 생성 편의 함수"""
    path_utils = PathUtils(project_root)
    return path_utils.makedirs(path, exist_ok)


def normalize_url_path(*parts: str) -> str:
    """
    여러 경로 조각을 안전하게 조합하여 표준 URL 경로로 만듭니다.
    예: normalize_url_path("/api/", "users", "list") -> "/api/users/list"
    예: normalize_url_path("api/users", "/list/") -> "/api/users/list"
    
    Args:
        *parts: 결합할 URL 경로 조각들
        
    Returns:
        정규화된 URL 경로
    """
    from urllib.parse import urljoin
    
    # 빈 경로 조각 제거
    valid_parts = [part for part in parts if part and part.strip()]
    if not valid_parts:
        return "/"
    
    # 항상 절대 경로 형태로 시작하도록 보장
    result = "/"
    for part in valid_parts:
        # 각 부분을 슬래시로 끝나도록 만들어 urljoin이 상대경로로 인식하게 함
        if not part.endswith('/'):
            part += '/'
        result = urljoin(result, part)

    # 마지막에 불필요한 슬래시 제거 (루트 경로 제외)
    if result != '/' and result.endswith('/'):
        result = result[:-1]
        
    return result


