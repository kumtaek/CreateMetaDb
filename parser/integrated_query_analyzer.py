"""
통합 쿼리 분석기 - 심플 버전
목표: Java, XML, JPA 파일에서 쿼리 추출하고 공통 처리
"""

import os
from typing import List, Dict, Any, Optional
from util import handle_error, info, debug
from parser.mybatis_analyzer import MyBatisAnalyzer
from parser.java_query_extractor import JavaQueryExtractor
from parser.jpa_query_extractor import JpaQueryExtractor
from util.common_query_processor import CommonQueryProcessor


class IntegratedQueryAnalyzer:
    """통합 쿼리 분석기 - 심플 버전"""
    
    def __init__(self, project_name: str, conn):
        self.project_name = project_name
        self.conn = conn
        
        self.mybatis_analyzer = MyBatisAnalyzer()
        self.java_query_extractor = JavaQueryExtractor()
        self.jpa_query_extractor = JpaQueryExtractor()
        self.common_processor = CommonQueryProcessor(project_name, conn)
        
        self.stats = {
            'java_files_processed': 0,
            'xml_files_processed': 0,
            'queries_extracted': 0,
            'errors': 0
        }

    def analyze_all_queries(self) -> Dict[str, Any]:
        """모든 쿼리 분석"""
        try:
            info("통합 쿼리 분석 시작")
            
            # 1. Java 파일 분석
            self._analyze_java_files()
            
            # 2. XML 파일 분석
            self._analyze_xml_files()
            
            info(f"통합 쿼리 분석 완료: Java {self.stats['java_files_processed']}개, XML {self.stats['xml_files_processed']}개, 쿼리 {self.stats['queries_extracted']}개")
            
            return {
                'success': True,
                'statistics': self.stats
            }
            
        except Exception as e:
            handle_error(e, "통합 쿼리 분석 실패")
            return {
                'success': False,
                'statistics': self.stats
            }

    def _analyze_java_files(self) -> None:
        """Java 파일 분석"""
        try:
            # Java 파일 목록 수집
            java_files = self._get_java_files()
            
            for java_file in java_files:
                try:
                    self._process_java_file(java_file)
                    self.stats['java_files_processed'] += 1
                except Exception as e:
                    handle_error(e, f"Java 파일 처리 실패: {java_file}")
                    self.stats['errors'] += 1
                    
        except Exception as e:
            handle_error(e, "Java 파일 분석 실패")

    def _analyze_xml_files(self) -> None:
        """XML 파일 분석"""
        try:
            # XML 파일 목록 수집
            xml_files = self._get_xml_files()
            
            for xml_file in xml_files:
                try:
                    self._process_xml_file(xml_file)
                    self.stats['xml_files_processed'] += 1
                except Exception as e:
                    handle_error(e, f"XML 파일 처리 실패: {xml_file}")
                    self.stats['errors'] += 1
                    
        except Exception as e:
            handle_error(e, "XML 파일 분석 실패")

    def _get_java_files(self) -> List[str]:
        """Java 파일 목록 수집"""
        java_files = []
        try:
            project_path = f"projects/{self.project_name}/src"
            for root, _, files in os.walk(project_path):
                for file in files:
                    if file.endswith('.java'):
                        java_files.append(os.path.join(root, file))
            return java_files
        except Exception as e:
            handle_error(e, "Java 파일 목록 수집 실패")
            return []

    def _get_xml_files(self) -> List[str]:
        """XML 파일 목록 수집"""
        xml_files = []
        try:
            project_path = f"projects/{self.project_name}/src"
            for root, _, files in os.walk(project_path):
                for file in files:
                    if file.endswith('.xml'):
                        xml_files.append(os.path.join(root, file))
            return xml_files
        except Exception as e:
            handle_error(e, "XML 파일 목록 수집 실패")
            return []

    def _process_java_file(self, java_file: str) -> None:
        """Java 파일 처리"""
        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. JPA 쿼리 추출
            jpa_queries = self.jpa_query_extractor.extract_jpa_queries(content)
            
            # 2. Java 동적 쿼리 추출
            java_queries = self.java_query_extractor.extract_java_queries(content)
            
            # 3. 모든 쿼리 통합 처리
            all_queries = jpa_queries + java_queries
            
            for query in all_queries:
                self._process_query(java_file, query)
                self.stats['queries_extracted'] += 1
                
        except Exception as e:
            handle_error(e, f"Java 파일 처리 실패: {java_file}")

    def _process_xml_file(self, xml_file: str) -> None:
        """XML 파일 처리"""
        try:
            # MyBatis 쿼리 추출
            result = self.mybatis_analyzer.analyze_xml_file(xml_file)
            
            for query in result['queries']:
                self._process_query(xml_file, query)
                self.stats['queries_extracted'] += 1
                
        except Exception as e:
            handle_error(e, f"XML 파일 처리 실패: {xml_file}")

    def _process_query(self, file_path: str, query_data: Dict[str, Any]) -> None:
        """개별 쿼리 처리"""
        try:
            # 파일 ID 조회
            file_id = self._get_file_id(file_path)
            if not file_id:
                debug(f"파일 ID를 찾을 수 없음: {file_path}")
                return
            
            # 메서드 컴포넌트 ID 조회 (간단히 첫 번째 METHOD 사용)
            method_id = self._get_first_method_id(file_id)
            if not method_id:
                debug(f"메서드 컴포넌트를 찾을 수 없음: {file_path}")
                return
            
            # 공통 쿼리 처리
            self.common_processor.process_query(file_id, method_id, query_data)
            
        except Exception as e:
            handle_error(e, f"쿼리 처리 실패: {query_data.get('query_id', 'Unknown')}")

    def _get_file_id(self, file_path: str) -> Optional[int]:
        """파일 ID 조회"""
        try:
            # 간단한 파일 ID 조회 (실제 구현에서는 더 정확한 로직 필요)
            query = "SELECT file_id FROM files WHERE file_name = ? AND del_yn = 'N' LIMIT 1"
            result = self._execute_query(query, (os.path.basename(file_path),))
            return result[0]['file_id'] if result else None
        except Exception as e:
            handle_error(e, f"파일 ID 조회 실패: {file_path}")
            return None

    def _get_first_method_id(self, file_id: int) -> Optional[int]:
        """첫 번째 메서드 컴포넌트 ID 조회"""
        try:
            query = "SELECT component_id FROM components WHERE file_id = ? AND component_type = 'METHOD' AND del_yn = 'N' LIMIT 1"
            result = self._execute_query(query, (file_id,))
            return result[0]['component_id'] if result else None
        except Exception as e:
            handle_error(e, f"메서드 컴포넌트 ID 조회 실패: {file_id}")
            return None

    def _execute_query(self, sql: str, params: tuple) -> List[Dict[str, Any]]:
        """SQL 쿼리 실행 (self.conn 사용)"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            handle_error(e, f"SQL 실행 실패: {sql}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """통계 반환"""
        stats = self.stats.copy()
        stats.update(self.common_processor.get_statistics())
        return stats
