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
        """레이어별 컴포넌트 데이터 조회 (전체 클래스 대상 동적 분류, 기타 레이어 포함)"""
        try:
            # 전체 클래스 조회 (APPLICATION 레이어 제한 제거)
            all_classes = self._get_all_classes()
            
            # 설정 파일에서 레이어 분류 패턴 로드
            layer_patterns = self._load_layer_classification_patterns()
            
            # 전체 처리된 클래스 추적 (중복 방지)
            all_processed_classes = set()
            layer_data = {}
            
            # 전체 클래스들을 세분화된 레이어로 분류 (util 제외, 우선순위 순서)
            layer_order = ['model', 'controller', 'service', 'mapper']  # Model Layer 우선 (폴더 구조 우선)
            for layer_name in layer_order:
                if layer_name in layer_patterns:
                    patterns = layer_patterns[layer_name]
                    layer_classes = self._classify_classes_by_patterns(all_classes, layer_name, patterns, all_processed_classes)
                    # ABCD 순으로 정렬
                    layer_classes.sort(key=lambda x: x['component_name'])
                    layer_data[layer_name] = layer_classes
                    app_logger.info(f"{layer_name.title()} Layer: {len(layer_classes)}개 클래스")
            
            # 고아 클래스 (분류되지 않은 클래스들)를 기타 레이어로 추가
            orphan_classes = []
            for class_info in all_classes:
                class_name = class_info['component_name']
                if class_name not in all_processed_classes:
                    orphan_classes.append(class_info)
            
            # ABCD 순으로 정렬
            orphan_classes.sort(key=lambda x: x['component_name'])
            layer_data['etc'] = orphan_classes
            app_logger.info(f"Etc Layer: {len(orphan_classes)}개 클래스 (고아 클래스)")
            
            app_logger.debug(f"레이어별 데이터 조회 완료: {dict((k, len(v)) for k, v in layer_data.items())}")
            return layer_data
            
        except Exception as e:
            handle_error(e, "레이어별 데이터 조회 실패")
            return {'controller': [], 'service': [], 'mapper': [], 'model': [], 'etc': []}
    
    def _load_layer_classification_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """설정 파일에서 레이어 분류 패턴 로드"""
        try:
            import yaml
            
            # 설정 파일 경로 (공통함수 사용)
            config_path = self.path_utils.get_parser_config_path("java")
            
            if not self.path_utils.exists(config_path):
                handle_error(Exception(f"설정 파일이 존재하지 않습니다: {config_path}"), "설정 파일 부재")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            layer_classification = config.get('layer_classification', {})
            
            # 기본 레이어 패턴이 없으면 기본값 사용
            if not layer_classification:
                return self._get_default_layer_patterns()
            
            return layer_classification
            
        except Exception as e:
            handle_error(e, "설정 파일 로드 실패")
    
    def _get_default_layer_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """기본 레이어 분류 패턴 (설정 파일 로드 실패 시 사용)"""
        return {
            'controller': {
                'suffixes': ['controller', 'ctrl'],
                'keywords': ['controller', 'rest', 'api'],
                'folder_patterns': ['*controller*', '*ctrl*', '*web*', '*api*']
            },
            'service': {
                'suffixes': ['service', 'svc'],
                'keywords': ['service', 'business', 'logic'],
                'folder_patterns': ['*service*', '*business*', '*logic*']
            },
            'mapper': {
                'suffixes': ['dao', 'repository', 'repo', 'mapper'],
                'keywords': ['dao', 'repository', 'mapper', 'data'],
                'folder_patterns': ['*dao*', '*repository*', '*mapper*', '*data*']
            },
            'model': {
                'suffixes': ['entity', 'model', 'vo', 'dto', 'domain'],
                'keywords': ['entity', 'model', 'vo', 'dto', 'domain', 'bean'],
                'folder_patterns': ['*model*', '*entity*', '*vo*', '*dto*', '*domain*', '*bean*']
            }
        }
    
    def _get_all_classes(self) -> List[Dict[str, Any]]:
        """전체 클래스 조회 (파일명, 폴더명 패턴 활용)"""
        try:
            query = """
                SELECT DISTINCT cls.class_name, f.file_name, f.file_path
                FROM classes cls
                JOIN files f ON cls.file_id = f.file_id
                JOIN projects p ON cls.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND cls.del_yn = 'N'
                ORDER BY cls.class_name
            """
            
            results = self.db_utils.execute_query(query, (self.project_name,))
            
            # 결과를 컴포넌트 형태로 변환
            components = []
            for result in results:
                components.append({
                    'component_name': result['class_name'],
                    'component_type': 'CLASS',
                    'file_name': result['file_name'],
                    'file_path': result['file_path']
                })
            
            app_logger.info(f"전체 클래스 {len(components)}개 조회 완료")
            return components
            
        except Exception as e:
            app_logger.error(f"전체 클래스 조회 실패: {e}")
            return []
    
    def _get_application_layer_classes(self) -> List[Dict[str, Any]]:
        """APPLICATION 레이어의 모든 클래스 조회"""
        try:
            query = """
                SELECT DISTINCT cls.class_name, f.file_name, f.file_path
                FROM classes cls
                JOIN files f ON cls.file_id = f.file_id
                JOIN components c ON c.parent_id = cls.class_id
                JOIN projects p ON cls.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND c.layer = 'APPLICATION'
                  AND c.component_type = 'METHOD'
                  AND cls.del_yn = 'N'
                  AND c.del_yn = 'N'
                ORDER BY cls.class_name
            """
            
            results = self.db_utils.execute_query(query, (self.project_name,))
            
            # 결과를 컴포넌트 형태로 변환
            components = []
            for result in results:
                components.append({
                    'component_name': result['class_name'],
                    'component_type': 'CLASS',
                    'file_name': result['file_name'],
                    'file_path': result['file_path']
                })
            
            return components
            
        except Exception as e:
            app_logger.error(f"APPLICATION 레이어 클래스 조회 실패: {e}")
            return []
    
    def _classify_classes_by_patterns(self, classes: List[Dict[str, Any]], layer_name: str, patterns: Dict[str, List[str]], all_processed_classes: set) -> List[Dict[str, Any]]:
        """클래스들을 패턴에 따라 분류 (중복 제거, 우선순위 적용, 파일명 패턴 포함)"""
        try:
            suffixes = patterns.get('suffixes', [])
            keywords = patterns.get('keywords', [])
            folder_patterns = patterns.get('folder_patterns', [])
            
            classified_classes = []
            
            # Model Layer 디버깅용 로그
            if layer_name == 'model':
                app_logger.info(f"Model Layer 분류 시작 - 패턴: {patterns}")
            
            for class_info in classes:
                class_name = class_info['component_name']
                file_path = class_info.get('file_path', '')
                file_name = class_info.get('file_name', '')
                
                # 이미 다른 레이어에서 처리된 클래스는 건너뛰기
                if class_name in all_processed_classes:
                    if layer_name == 'model' and class_name in ['Product', 'User', 'OrderStatus']:
                        app_logger.info(f"Model Layer: {class_name} 이미 처리됨 (다른 레이어에서)")
                    continue
                
                is_matched = False
                
                # 1순위: folder_patterns 매칭 (폴더 구조가 가장 정확한 분류)
                if folder_patterns and not is_matched:
                    for pattern in folder_patterns:
                        # 와일드카드 패턴을 정규식으로 변환 (폴더 경로만 매칭)
                        import re
                        # Windows와 Unix 경로 구분자 모두 고려
                        normalized_path = file_path.replace('\\', '/')
                        regex_pattern = pattern.replace('*', '.*')
                        if re.search(regex_pattern, normalized_path, re.IGNORECASE):
                            classified_classes.append(class_info)
                            all_processed_classes.add(class_name)
                            is_matched = True
                            app_logger.debug(f"{layer_name.title()} Layer: {class_name} 매칭됨 (폴더 패턴: {pattern})")
                            break
                
                # 2순위: 클래스명 keyword 매칭 (클래스명 기반 분류)
                if keywords and not is_matched:
                    for keyword in keywords:
                        if keyword.lower() in class_name.lower():
                            classified_classes.append(class_info)
                            all_processed_classes.add(class_name)
                            is_matched = True
                            app_logger.debug(f"{layer_name.title()} Layer: {class_name} 매칭됨 (클래스명 keyword: {keyword})")
                            break
                
                # 3순위: 파일명 패턴 매칭
                if not is_matched:
                    for suffix in suffixes:
                        if file_name.lower().endswith(suffix.lower() + '.java'):
                            classified_classes.append(class_info)
                            all_processed_classes.add(class_name)
                            is_matched = True
                            app_logger.debug(f"{layer_name.title()} Layer: {class_name} 매칭됨 (파일명: {file_name}, suffix: {suffix})")
                            break
                
                # 서블릿 디버깅용 로그
                if layer_name == 'controller' and 'servlet' in file_name.lower() and not is_matched:
                    app_logger.debug(f"Controller Layer: {class_name} 서블릿 매칭 실패 - file_name: {file_name}")
                
                # 3순위: 클래스명 suffix 패턴 매칭
                if suffixes and not is_matched:
                    for suffix in suffixes:
                        if class_name.lower().endswith(suffix.lower()):
                            classified_classes.append(class_info)
                            all_processed_classes.add(class_name)
                            is_matched = True
                            if layer_name in ['model', 'service', 'mapper', 'controller'] and class_name in ['Product', 'User', 'OrderStatus']:
                                app_logger.debug(f"{layer_name.title()} Layer: {class_name} 매칭됨 (클래스명 suffix: {suffix})")
                            break
                
                # 4순위: keyword 패턴 매칭
                if keywords and not is_matched:
                    for keyword in keywords:
                        if keyword.lower() in class_name.lower():
                            classified_classes.append(class_info)
                            all_processed_classes.add(class_name)
                            is_matched = True
                            if layer_name in ['model', 'service', 'mapper', 'controller'] and class_name in ['Product', 'User', 'OrderStatus']:
                                app_logger.info(f"{layer_name.title()} Layer: {class_name} 매칭됨 (keyword: {keyword})")
                            break
                
                # Model Layer 디버깅: 매칭되지 않은 경우
                if layer_name == 'model' and class_name in ['Product', 'User', 'OrderStatus'] and not is_matched:
                    app_logger.info(f"Model Layer: {class_name} 매칭 실패 - file_path: {file_path}")
            
            return classified_classes
            
        except Exception as e:
            app_logger.error(f"클래스 분류 실패 ({layer_name}): {e}")
            return []
    
    def _get_classes_by_layer_patterns(self, layer_name: str, patterns: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """패턴에 따라 특정 레이어의 클래스들 조회 (보편적인 동적 분류)"""
        try:
            suffixes = patterns.get('suffixes', [])
            keywords = patterns.get('keywords', [])
            folder_patterns = patterns.get('folder_patterns', [])
            
            # WHERE 조건 생성
            where_conditions = []
            params = [self.project_name]
            
            # suffix 패턴 조건 (클래스명 접미사)
            if suffixes:
                suffix_conditions = []
                for suffix in suffixes:
                    suffix_conditions.append("cls.class_name LIKE ?")
                    params.append(f"%{suffix}")
                where_conditions.append(f"({' OR '.join(suffix_conditions)})")
            
            # keyword 패턴 조건 (클래스명에 키워드 포함)
            if keywords:
                keyword_conditions = []
                for keyword in keywords:
                    keyword_conditions.append("cls.class_name LIKE ?")
                    params.append(f"%{keyword}%")
                where_conditions.append(f"({' OR '.join(keyword_conditions)})")
            
            # folder_patterns 조건 (파일 경로 패턴)
            if folder_patterns:
                folder_conditions = []
                for pattern in folder_patterns:
                    # 와일드카드 패턴을 SQL LIKE 패턴으로 변환
                    sql_pattern = pattern.replace('*', '%')
                    folder_conditions.append("f.file_path LIKE ?")
                    params.append(f"%{sql_pattern}%")
                where_conditions.append(f"({' OR '.join(folder_conditions)})")
            
            # WHERE 조건이 없으면 빈 결과 반환
            if not where_conditions:
                return []
            
            where_clause = " OR ".join(where_conditions)
            
            # 클래스 조회 쿼리
            query = f"""
                SELECT DISTINCT cls.class_name, f.file_name, f.file_path
                FROM classes cls
                JOIN files f ON cls.file_id = f.file_id
                JOIN projects p ON cls.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND ({where_clause})
                  AND cls.del_yn = 'N'
                ORDER BY cls.class_name
            """
            
            results = self.db_utils.execute_query(query, params)
            
            # 결과를 컴포넌트 형태로 변환
            components = []
            for result in results:
                components.append({
                    'component_name': result['class_name'],
                    'component_type': 'CLASS',
                    'file_name': result['file_name'],
                    'file_path': result['file_path']
                })
            
            return components
            
        except Exception as e:
            app_logger.error(f"레이어 {layer_name} 클래스 조회 실패: {e}")
            return []
    
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
            output_path = self.path_utils.join_path(self.output_dir, filename)
            
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
