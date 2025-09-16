"""
SourceAnalyzer 리포트 생성 공통 유틸리티 모듈
- 리포트 생성 관련 공통 함수들
- CSS/JS 파일 복사
- 리포트 파일 저장
- 통계 정보 조회
"""

import os
import shutil
import time
from typing import Dict, Any, Optional
from .logger import app_logger, handle_error
from .path_utils import PathUtils


class ReportUtils:
    """리포트 생성 관련 공통 유틸리티 클래스"""
    
    def __init__(self, project_name: str, output_dir: str):
        """
        리포트 유틸리티 초기화
        
        Args:
            project_name: 프로젝트명
            output_dir: 출력 디렉토리
        """
        self.project_name = project_name
        self.output_dir = output_dir
        self.path_utils = PathUtils()
    
    def copy_assets(self):
        """CSS 및 JS 파일 복사 (권한 오류 방지)"""
        try:
            # CSS 디렉토리 생성
            css_dir = self.path_utils.join_path(self.output_dir, "css")
            if not os.path.exists(css_dir):
                os.makedirs(css_dir)
            
            # JS 디렉토리 생성
            js_dir = self.path_utils.join_path(self.output_dir, "js")
            if not os.path.exists(js_dir):
                os.makedirs(js_dir)
            
            # CSS 파일 복사
            reports_path = self.path_utils.get_reports_path()
            source_css = self.path_utils.join_path(reports_path, "css", "woori.css")
            
            if os.path.exists(source_css):
                dest_css = self.path_utils.join_path(css_dir, "woori.css")
                self._safe_copy_file(source_css, dest_css, "CSS")
            
            # JS 파일들 복사
            source_js_dir = self.path_utils.join_path(reports_path, "js")
            
            if os.path.exists(source_js_dir):
                for js_file in os.listdir(source_js_dir):
                    if js_file.endswith('.js'):
                        source_js = self.path_utils.join_path(source_js_dir, js_file)
                        dest_js = self.path_utils.join_path(js_dir, js_file)
                        self._safe_copy_file(source_js, dest_js, f"JS ({js_file})")
            
        except Exception as e:
            handle_error(e, "CSS/JS 파일 복사 실패")
    
    def copy_js_folder(self) -> bool:
        """js 폴더를 출력 디렉토리로 복사 (권한 오류 방지)"""
        try:
            # JS 디렉토리 생성
            js_dir = self.path_utils.join_path(self.output_dir, "js")
            if not os.path.exists(js_dir):
                os.makedirs(js_dir)
            
            # JS 파일들 복사
            reports_path = self.path_utils.get_reports_path()
            source_js_dir = self.path_utils.join_path(reports_path, "js")
            
            if os.path.exists(source_js_dir):
                for js_file in os.listdir(source_js_dir):
                    if js_file.endswith('.js'):
                        source_js = self.path_utils.join_path(source_js_dir, js_file)
                        dest_js = self.path_utils.join_path(js_dir, js_file)
                        self._safe_copy_file(source_js, dest_js, f"JS ({js_file})")
                return True
            else:
                app_logger.warning(f"소스 JS 디렉토리가 존재하지 않습니다: {source_js_dir}")
                return False
            
        except Exception as e:
            handle_error(e, "JS 폴더 복사 실패")
    
    def _safe_copy_file(self, source: str, dest: str, file_type: str, max_retries: int = 3) -> bool:
        """파일 복사 (권한 오류 방지를 위한 재시도 로직)"""
        for attempt in range(max_retries):
            try:
                # 대상 파일이 이미 존재하고 사용 중인 경우 삭제 시도
                if os.path.exists(dest):
                    try:
                        os.remove(dest)
                    except PermissionError:
                        # 삭제 실패 시 잠시 대기 후 재시도
                        time.sleep(0.1)
                        continue
                
                # 파일 복사
                shutil.copy2(source, dest)
                app_logger.info(f"{file_type} 파일 복사 완료: {dest}")
                return True
                
            except PermissionError as e:
                if attempt < max_retries - 1:
                    app_logger.warning(f"{file_type} 파일 복사 재시도 {attempt + 1}/{max_retries}: {e}")
                    time.sleep(0.2)  # 200ms 대기
                else:
                    app_logger.warning(f"{file_type} 파일 복사 실패 (최대 재시도 횟수 초과): {source} -> {dest}")
                    return False
            except Exception as e:
                handle_error(e, f"{file_type} 파일 복사 실패")
        
        return False
    
    def save_report(self, html_content: str, report_type: str = "Report") -> str:
        """리포트 파일 저장"""
        try:
            from datetime import datetime
            
            # 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.project_name}_{report_type}_{timestamp}.html"
            
            # 출력 디렉토리 생성
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            
            # 파일 저장
            output_file = self.path_utils.join_path(self.output_dir, filename)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            app_logger.info(f"리포트 파일 저장 완료: {output_file}")
            return output_file
            
        except Exception as e:
            handle_error(e, "리포트 파일 저장 실패")
            return ""
    
    def get_database_statistics(self, db_utils) -> Dict[str, int]:
        """데이터베이스 통계 정보 조회"""
        try:
            stats = {}
            
            # 전체 테이블 수
            query = """
                SELECT COUNT(*) as table_count
                FROM tables t
                JOIN projects p ON t.project_id = p.project_id
                WHERE p.project_name = ? AND t.del_yn = 'N'
            """
            results = db_utils.execute_query(query, (self.project_name,))
            stats['total_tables'] = results[0]['table_count'] if results else 0
            
            # 전체 컬럼 수
            query = """
                SELECT COUNT(*) as column_count
                FROM columns c
                JOIN tables t ON c.table_id = t.table_id
                JOIN projects p ON t.project_id = p.project_id
                WHERE p.project_name = ? AND c.del_yn = 'N'
            """
            results = db_utils.execute_query(query, (self.project_name,))
            stats['total_columns'] = results[0]['column_count'] if results else 0
            
            # 전체 컴포넌트 수
            query = """
                SELECT COUNT(*) as component_count
                FROM components c
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? AND c.del_yn = 'N'
            """
            results = db_utils.execute_query(query, (self.project_name,))
            stats['total_components'] = results[0]['component_count'] if results else 0
            
            return stats
            
        except Exception as e:
            handle_error(e, "통계 정보 조회 실패")
            return {}


# 편의 함수들
def copy_assets(project_name: str, output_dir: str):
    """CSS 및 JS 파일 복사 편의 함수"""
    report_utils = ReportUtils(project_name, output_dir)
    report_utils.copy_assets()


def copy_js_folder(project_name: str, output_dir: str) -> bool:
    """js 폴더 복사 편의 함수"""
    report_utils = ReportUtils(project_name, output_dir)
    return report_utils.copy_js_folder()


def save_report(project_name: str, output_dir: str, html_content: str, report_type: str = "Report") -> str:
    """리포트 파일 저장 편의 함수"""
    report_utils = ReportUtils(project_name, output_dir)
    return report_utils.save_report(html_content, report_type)


def get_database_statistics(project_name: str, db_utils) -> Dict[str, int]:
    """데이터베이스 통계 정보 조회 편의 함수"""
    report_utils = ReportUtils(project_name, "")
    return report_utils.get_database_statistics(db_utils)
