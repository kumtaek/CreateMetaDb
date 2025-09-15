"""
Architecture Report 생성기
- 레이어별 컴포넌트 구조 분석
- 컴포넌트 간 관계 시각화
- SVG 기반 아키텍처 다이어그램 생성
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from util.logger import app_logger, handle_error
from util.path_utils import PathUtils
from util.database_utils import DatabaseUtils
from reports.report_templates import ReportTemplates


class ArchitectureReportGenerator:
    """Architecture Report 생성기 클래스"""
    
    def __init__(self, project_name: str, output_dir: str):
        """
        초기화
        
        Args:
            project_name: 프로젝트명
            output_dir: 출력 디렉토리
        """
        self.project_name = project_name
        self.output_dir = output_dir
        self.path_utils = PathUtils()
        self.templates = ReportTemplates()
        
        # 메타데이터베이스 연결
        self.metadata_db_path = self.path_utils.get_project_metadata_db_path(project_name)
        self.db_utils = DatabaseUtils(self.metadata_db_path)
        
        if not self.db_utils.connect():
            handle_error(Exception("데이터베이스 연결 실패"), f"메타데이터베이스 연결 실패: {self.metadata_db_path}")
    
    def generate_report(self) -> bool:
        """
        Architecture Report 생성
        
        Returns:
            생성 성공 여부 (True/False)
        """
        try:
            app_logger.info(f"Architecture Report 생성 시작: {self.project_name}")
            
            # 1. 통계 정보 조회
            stats = self._get_statistics()
            
            # 2. 레이어별 컴포넌트 데이터 조회
            layer_data = self._get_layer_data()
            
            # 3. 컴포넌트 관계 분석
            relationships = self._get_relationships()
            
            # 4. HTML 생성
            html_content = self._generate_html(stats, layer_data, relationships)
            
            # 5. 파일 저장
            output_file = self._save_report(html_content)
            
            app_logger.info(f"Architecture Report 생성 완료: {output_file}")
            return True
            
        except Exception as e:
            handle_error(e, "Architecture Report 생성 실패")
            return False
        finally:
            self.db_utils.disconnect()
    
    def _get_statistics(self) -> Dict[str, int]:
        """통계 정보 조회"""
        try:
            stats = {}
            
            # 전체 클래스 수
            query = """
                SELECT COUNT(*) as count
                FROM classes c
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? AND c.del_yn = 'N'
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['total_classes'] = result[0]['count'] if result else 0
            
            # 전체 테이블 수
            query = """
                SELECT COUNT(*) as count
                FROM (
                    SELECT DISTINCT t.table_name
                    FROM tables t
                    JOIN projects p ON t.project_id = p.project_id
                    WHERE p.project_name = ? AND t.del_yn = 'N'
                )
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['total_tables'] = result[0]['count'] if result else 0
            
            # 전체 관계 수
            query = """
                SELECT COUNT(*) as count
                FROM relationships r
                JOIN components src_comp ON r.src_id = src_comp.component_id
                JOIN projects p ON src_comp.project_id = p.project_id
                WHERE p.project_name = ? AND r.del_yn = 'N'
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['total_relationships'] = result[0]['count'] if result else 0
            
            app_logger.debug(f"통계 정보 조회 완료: {stats}")
            return stats
            
        except Exception as e:
            handle_error(e, "통계 정보 조회 실패")
            return {}
    
    def _get_layer_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """레이어별 컴포넌트 데이터 조회"""
        try:
            # Controller Layer 컴포넌트 조회
            controller_query = """
                SELECT DISTINCT c.component_name, c.component_type, f.file_name
                FROM components c
                JOIN classes cls ON c.parent_id = cls.class_id
                JOIN files f ON c.file_id = f.file_id
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND c.component_type IN ('CLASS', 'METHOD')
                  AND (cls.class_name LIKE '%Controller' OR c.component_name LIKE '%Controller')
                  AND c.del_yn = 'N'
                  AND cls.del_yn = 'N'
                ORDER BY c.component_name
            """
            controller_results = self.db_utils.execute_query(controller_query, (self.project_name,))
            
            # Service Layer 컴포넌트 조회
            service_query = """
                SELECT DISTINCT c.component_name, c.component_type, f.file_name
                FROM components c
                JOIN classes cls ON c.parent_id = cls.class_id
                JOIN files f ON c.file_id = f.file_id
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND c.component_type IN ('CLASS', 'METHOD')
                  AND (cls.class_name LIKE '%Service' OR c.component_name LIKE '%Service')
                  AND c.del_yn = 'N'
                  AND cls.del_yn = 'N'
                ORDER BY c.component_name
            """
            service_results = self.db_utils.execute_query(service_query, (self.project_name,))
            
            # Mapper Layer 컴포넌트 조회
            mapper_query = """
                SELECT DISTINCT c.component_name, c.component_type, f.file_name
                FROM components c
                JOIN classes cls ON c.parent_id = cls.class_id
                JOIN files f ON c.file_id = f.file_id
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND c.component_type IN ('CLASS', 'METHOD')
                  AND (cls.class_name LIKE '%Mapper' OR c.component_name LIKE '%Mapper')
                  AND c.del_yn = 'N'
                  AND cls.del_yn = 'N'
                ORDER BY c.component_name
            """
            mapper_results = self.db_utils.execute_query(mapper_query, (self.project_name,))
            
            # Model Layer 컴포넌트 조회
            model_query = """
                SELECT DISTINCT c.component_name, c.component_type, f.file_name
                FROM components c
                JOIN classes cls ON c.parent_id = cls.class_id
                JOIN files f ON c.file_id = f.file_id
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND c.component_type IN ('CLASS', 'METHOD')
                  AND (cls.class_name LIKE '%Model' OR cls.class_name LIKE '%Entity' 
                       OR cls.class_name LIKE '%DTO' OR cls.class_name LIKE '%VO')
                  AND c.del_yn = 'N'
                  AND cls.del_yn = 'N'
                ORDER BY c.component_name
            """
            model_results = self.db_utils.execute_query(model_query, (self.project_name,))
            
            layer_data = {
                'controller': controller_results,
                'service': service_results,
                'mapper': mapper_results,
                'model': model_results
            }
            
            app_logger.debug(f"레이어별 데이터 조회 완료: Controller({len(controller_results)}), Service({len(service_results)}), Mapper({len(mapper_results)}), Model({len(model_results)})")
            return layer_data
            
        except Exception as e:
            handle_error(e, "레이어별 데이터 조회 실패")
            return {'controller': [], 'service': [], 'mapper': [], 'model': []}
    
    def _get_relationships(self) -> Dict[str, List[Dict[str, Any]]]:
        """컴포넌트 관계 분석"""
        try:
            relationships = {
                'dependency': [],
                'implementation': [],
                'call': []
            }
            
            # 의존성 관계 조회
            dependency_query = """
                SELECT 
                    src_comp.component_name as src_component,
                    dst_comp.component_name as dst_component,
                    r.rel_type
                FROM relationships r
                JOIN components src_comp ON r.src_id = src_comp.component_id
                JOIN components dst_comp ON r.dst_id = dst_comp.component_id
                JOIN projects p ON src_comp.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND r.rel_type = 'DEPENDENCY'
                  AND r.del_yn = 'N'
                  AND src_comp.del_yn = 'N'
                  AND dst_comp.del_yn = 'N'
                ORDER BY src_comp.component_name
            """
            dependency_results = self.db_utils.execute_query(dependency_query, (self.project_name,))
            relationships['dependency'] = dependency_results
            
            # 구현 관계 조회
            implementation_query = """
                SELECT 
                    src_comp.component_name as src_component,
                    dst_comp.component_name as dst_component,
                    r.rel_type
                FROM relationships r
                JOIN components src_comp ON r.src_id = src_comp.component_id
                JOIN components dst_comp ON r.dst_id = dst_comp.component_id
                JOIN projects p ON src_comp.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND r.rel_type = 'IMPLEMENTS'
                  AND r.del_yn = 'N'
                  AND src_comp.del_yn = 'N'
                  AND dst_comp.del_yn = 'N'
                ORDER BY src_comp.component_name
            """
            implementation_results = self.db_utils.execute_query(implementation_query, (self.project_name,))
            relationships['implementation'] = implementation_results
            
            # 호출 관계 조회
            call_query = """
                SELECT 
                    src_comp.component_name as src_component,
                    dst_comp.component_name as dst_component,
                    r.rel_type
                FROM relationships r
                JOIN components src_comp ON r.src_id = src_comp.component_id
                JOIN components dst_comp ON r.dst_id = dst_comp.component_id
                JOIN projects p ON src_comp.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND r.rel_type LIKE 'CALL_%'
                  AND r.del_yn = 'N'
                  AND src_comp.del_yn = 'N'
                  AND dst_comp.del_yn = 'N'
                ORDER BY src_comp.component_name
            """
            call_results = self.db_utils.execute_query(call_query, (self.project_name,))
            relationships['call'] = call_results
            
            app_logger.debug(f"관계 데이터 조회 완료: Dependency({len(dependency_results)}), Implementation({len(implementation_results)}), Call({len(call_results)})")
            return relationships
            
        except Exception as e:
            handle_error(e, "관계 데이터 조회 실패")
            return {'dependency': [], 'implementation': [], 'call': []}
    
    def _generate_html(self, stats: Dict[str, int], layer_data: Dict[str, List[Dict[str, Any]]], relationships: Dict[str, List[Dict[str, Any]]]) -> str:
        """HTML 생성"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # HTML 템플릿 생성
            html_content = self.templates.get_architecture_template(
                project_name=self.project_name,
                timestamp=timestamp,
                stats=stats,
                layer_data=layer_data,
                relationships=relationships
            )
            
            app_logger.debug("Architecture HTML 생성 완료")
            return html_content
            
        except Exception as e:
            handle_error(e, "Architecture HTML 생성 실패")
            return ""
    
    def _save_report(self, html_content: str) -> str:
        """리포트 파일 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"architecture_mermaid_{timestamp}.html"
            output_path = os.path.join(self.output_dir, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            app_logger.info(f"Architecture 리포트 파일 저장 완료: {output_path}")
            return output_path
            
        except Exception as e:
            handle_error(e, "Architecture 리포트 파일 저장 실패")
            return ""


if __name__ == '__main__':
    # 테스트용 실행
    generator = ArchitectureReportGenerator('sampleSrc', './temp')
    generator.generate_report()
