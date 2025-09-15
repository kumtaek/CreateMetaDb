"""
CallChain Report 생성기
- JSP-Class-Method-XML-Query-Table 연계 정보 표시
- 통계 정보 및 필터링 기능 제공
- SqlContent.db 연동으로 정제된 SQL 쿼리 툴팁 표시
"""

import os
import sys
import gzip
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# 크로스플랫폼 경로 처리는 PathUtils 공통함수 사용

from util.logger import app_logger, handle_error
from util.path_utils import PathUtils
from util.database_utils import DatabaseUtils
from reports.report_templates import ReportTemplates


class CallChainReportGenerator:
    """CallChain Report 생성기 클래스"""
    
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
        CallChain Report 생성
        
        Returns:
            생성 성공 여부 (True/False)
        """
        try:
            app_logger.info(f"CallChain Report 생성 시작: {self.project_name}")
            
            # 1. 통계 정보 조회
            stats = self._get_statistics()
            
            # 2. 연계 체인 데이터 조회 (JSP 연계 경로 포함)
            chain_data = self._get_call_chain_data()
            
            # 3. 필터링 옵션 데이터 조회 (동적 생성)
            filter_options = self._get_filter_options()
            
            # 4. HTML 생성
            html_content = self._generate_html(stats, chain_data, filter_options)
            
            # 5. 파일 저장
            output_file = self._save_report(html_content)
            
            app_logger.info(f"CallChain Report 생성 완료: {output_file}")
            return True
            
        except Exception as e:
            handle_error(e, "CallChain Report 생성 실패")
            return False
        finally:
            self.db_utils.disconnect()
    
    def _get_statistics(self) -> Dict[str, int]:
        """통계 정보 조회"""
        try:
            stats = {}
            
            # Java 클래스 수
            query = """
                SELECT COUNT(*) as count
                FROM classes c
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? AND c.del_yn = 'N'
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['java_classes'] = result[0]['count'] if result else 0
            
            # 데이터베이스 테이블 수
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
            stats['database_tables'] = result[0]['count'] if result else 0
            
            # XML 파일 수
            query = """
                SELECT COUNT(*) as count
                FROM (
                    SELECT DISTINCT f.file_name
                    FROM files f
                    JOIN projects p ON f.project_id = p.project_id
                    WHERE p.project_name = ? AND f.file_type = 'XML' AND f.del_yn = 'N'
                )
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['xml_files'] = result[0]['count'] if result else 0
            
            # JSP 파일 수
            query = """
                SELECT COUNT(*) as count
                FROM (
                    SELECT DISTINCT f.file_name
                    FROM files f
                    JOIN projects p ON f.project_id = p.project_id
                    WHERE p.project_name = ? AND f.file_type = 'JSP' AND f.del_yn = 'N'
                )
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['jsp_files'] = result[0]['count'] if result else 0
            
            # JOIN 관계 수
            query = """
                SELECT COUNT(*) as count
                FROM relationships r
                JOIN projects p ON r.src_id IN (
                    SELECT c.component_id FROM components c WHERE c.project_id = p.project_id
                )
                WHERE p.project_name = ? AND r.rel_type LIKE 'JOIN_%' AND r.del_yn = 'N'
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['join_relations'] = result[0]['count'] if result else 0
            
            # API ENTRY 수
            query = """
                SELECT COUNT(*) as count
                FROM components c
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? AND c.component_type = 'API_ENTRY' AND c.del_yn = 'N'
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['api_entries'] = result[0]['count'] if result else 0
            
            app_logger.debug(f"통계 정보 조회 완료: {stats}")
            return stats
            
        except Exception as e:
            handle_error(e, "통계 정보 조회 실패")
            return {}
    
    def _get_call_chain_data(self) -> List[Dict[str, Any]]:
        """연계 체인 데이터 조회 (API_ENTRY 포함, JSP 제외, SqlContent.db 연동)"""
        try:
            # 기존 Method -> Class -> Method -> XML -> Query -> Table 연계 체인
            method_chain_query = """
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY src_m.component_name, cls.class_name, dst_m.component_name) as chain_id,
                    '' as jsp_file,
                    '' as api_entry,
                    '' as virtual_endpoint,
                    cls.class_name as class_name,
                    src_m.component_name as method_name,
                    xml_file.file_name as xml_file,
                    q.component_name as query_id,
                    q.component_type as query_type,
                    GROUP_CONCAT(DISTINCT t.table_name) as related_tables
                FROM components src_m
                JOIN classes cls ON src_m.parent_id = cls.class_id
                JOIN relationships r1 ON src_m.component_id = r1.src_id AND r1.rel_type = 'CALL_METHOD'
                JOIN components dst_m ON r1.dst_id = dst_m.component_id AND dst_m.component_type = 'METHOD'
                JOIN relationships r2 ON dst_m.component_id = r2.src_id AND r2.rel_type = 'CALL_QUERY'
                JOIN components q ON r2.dst_id = q.component_id AND q.component_type = 'QUERY'
                JOIN files xml_file ON q.file_id = xml_file.file_id
                LEFT JOIN relationships r3 ON q.component_id = r3.src_id AND r3.rel_type = 'USE_TABLE'
                LEFT JOIN tables t ON r3.dst_id = t.component_id
                JOIN projects p ON src_m.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND src_m.component_type = 'METHOD'
                  AND src_m.del_yn = 'N'
                  AND cls.del_yn = 'N'
                  AND dst_m.del_yn = 'N'
                  AND q.del_yn = 'N'
                GROUP BY src_m.component_name, cls.class_name, dst_m.component_name, xml_file.file_name, q.component_name, q.component_type
            """
            
            # SQL_% 타입 쿼리 체인 (USE_TABLE 관계를 통해)
            sql_chain_query = """
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY q.component_name) as chain_id,
                    '' as jsp_file,
                    '' as api_entry,
                    '' as virtual_endpoint,
                    f.file_name as class_name,
                    q.component_name as method_name,
                    f.file_name as xml_file,
                    q.component_name as query_id,
                    q.component_type as query_type,
                    GROUP_CONCAT(DISTINCT t.table_name) as related_tables
                FROM components q
                JOIN files f ON q.file_id = f.file_id
                JOIN relationships r3 ON q.component_id = r3.src_id AND r3.rel_type = 'USE_TABLE'
                JOIN tables t ON r3.dst_id = t.component_id
                JOIN projects p ON q.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND q.component_type LIKE 'SQL_%'
                  AND q.del_yn = 'N'
                  AND f.del_yn = 'N'
                GROUP BY q.component_name, f.file_name, q.component_type
            """
            
            # FRONTEND_API -> API_ENTRY 체인 (간단한 버전)
            api_chain_query = """
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY frontend.component_name, api.component_name) as chain_id,
                    '' as jsp_file,
                    api.component_name as api_entry,
                    frontend.component_name as virtual_endpoint,
                    f.file_name as class_name,
                    '' as method_name,
                    '' as xml_file,
                    '' as query_id,
                    '' as query_type,
                    '' as related_tables
                FROM components frontend
                JOIN relationships r1 ON frontend.component_id = r1.src_id AND r1.rel_type = 'CALL_API_F2B'
                JOIN components api ON r1.dst_id = api.component_id
                JOIN files f ON api.file_id = f.file_id
                JOIN projects p ON frontend.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND frontend.component_type = 'FRONTEND_API'
                  AND api.component_type = 'API_ENTRY'
                  AND frontend.del_yn = 'N'
                  AND api.del_yn = 'N'
            """
            
            # 세 쿼리를 UNION으로 결합
            query = f"""
                {method_chain_query}
                UNION ALL
                {sql_chain_query}
                UNION ALL
                {api_chain_query}
                ORDER BY method_name, class_name
            """
            
            results = self.db_utils.execute_query(query, (self.project_name, self.project_name, self.project_name))
            
            # SqlContent.db에서 정제된 SQL 내용 조회
            sql_content_map = self._get_sql_contents()
            
            # 데이터 정제
            chain_data = []
            for row in results:
                query_id = row['query_id']
                sql_content = sql_content_map.get(query_id, '')
                
                # 쿼리 타입 변환
                query_type = self._convert_query_type(row['query_type'])
                
                # 관련 테이블 별도 조회 (API_ENTRY 체인에서도 적용)
                related_tables = self._get_related_tables_for_query(query_id)
                
                # API_ENTRY 접두사 제거 및 의미있는 표시로 변환
                api_entry = row.get('api_entry', '')
                if api_entry.startswith('API_ENTRY.'):
                    api_entry = api_entry[10:]  # 'API_ENTRY.' 제거
                    # HTTP 메소드와 URL 패턴만 표시
                    if '_' in api_entry:
                        parts = api_entry.split('_', 1)
                        if len(parts) == 2:
                            api_entry = f"{parts[0]} {parts[1]}"
                
                # FRONTEND_API 접두사 제거 및 의미있는 표시로 변환
                virtual_endpoint = row.get('virtual_endpoint', '')
                if virtual_endpoint.startswith('FRONTEND_API.'):
                    virtual_endpoint = virtual_endpoint[13:]  # 'FRONTEND_API.' 제거
                    # HTTP 메소드와 URL 패턴만 표시
                    if '_' in virtual_endpoint:
                        parts = virtual_endpoint.split('_', 1)
                        if len(parts) == 2:
                            virtual_endpoint = f"{parts[0]} {parts[1]}"
                
                # 메서드명에서도 API_ENTRY 접두사 제거
                method_name = row['method_name']
                if method_name.startswith('API_ENTRY.'):
                    method_name = method_name[10:]  # 'API_ENTRY.' 제거
                
                chain_data.append({
                    'chain_id': row['chain_id'],
                    'jsp_file': row['jsp_file'],
                    'api_entry': api_entry,
                    'virtual_endpoint': virtual_endpoint,
                    'class_name': row['class_name'],
                    'method_name': method_name,
                    'xml_file': row['xml_file'],
                    'query_id': query_id,
                    'query_type': query_type,
                    'related_tables': related_tables,
                    'sql_content': sql_content  # 정제된 SQL 내용 추가
                })
            
            app_logger.debug(f"연계 체인 데이터 조회 완료: {len(chain_data)}건")
            return chain_data
            
        except Exception as e:
            handle_error(e, "연계 체인 데이터 조회 실패")
            return []
    
    def _get_related_tables_for_query(self, query_id: str) -> str:
        """특정 쿼리의 관련 테이블 조회"""
        try:
            query = """
                SELECT GROUP_CONCAT(DISTINCT t.table_name) as related_tables
                FROM components q
                LEFT JOIN relationships r ON q.component_id = r.src_id AND r.rel_type = 'USE_TABLE'
                LEFT JOIN tables t ON r.dst_id = t.component_id
                WHERE q.component_name = ? AND q.del_yn = 'N'
            """
            
            result = self.db_utils.execute_query(query, (query_id,))
            if result and result[0]['related_tables']:
                return result[0]['related_tables']
            return ''
            
        except Exception as e:
            app_logger.warning(f"관련 테이블 조회 실패: {query_id}, {e}")
            return ''
    
    def _convert_query_type(self, component_type: str) -> str:
        """컴포넌트 타입을 쿼리 타입으로 변환 (SQL_ 뒤의 부분 사용)"""
        if component_type.startswith('SQL_'):
            return component_type[4:]  # SQL_ 제거하고 뒤의 부분만 반환
        return component_type
    
    def _get_sql_contents(self) -> Dict[str, str]:
        """SqlContent.db에서 정제된 SQL 내용 조회 및 압축 해제 (크로스플랫폼 지원)"""
        try:
            # 크로스플랫폼 경로 생성 (공통함수 사용)
            sql_content_db_path = self.path_utils.join_path("projects", self.project_name, "SqlContent.db")
            
            if not os.path.exists(sql_content_db_path):
                app_logger.warning(f"SqlContent.db 파일이 존재하지 않습니다: {sql_content_db_path}")
                return {}
            
            # SqlContent.db 연결
            sql_content_db = DatabaseUtils(sql_content_db_path)
            if not sql_content_db.connect():
                app_logger.warning("SqlContent.db 연결 실패")
                return {}
            
            try:
                # 정제된 SQL 내용 조회
                query = """
                    SELECT component_name, sql_content_compressed
                    FROM sql_contents
                    WHERE project_id = (
                        SELECT project_id FROM projects WHERE project_name = ?
                    )
                    AND del_yn = 'N'
                """
                
                results = sql_content_db.execute_query(query, (self.project_name,))
                
                sql_content_map = {}
                for row in results:
                    component_name = row['component_name']
                    compressed_content = row['sql_content_compressed']
                    
                    # gzip 압축 해제 (크로스플랫폼 호환)
                    try:
                        decompressed_content = gzip.decompress(compressed_content).decode('utf-8')
                        sql_content_map[component_name] = decompressed_content
                    except Exception as decompress_error:
                        app_logger.warning(f"SQL 내용 압축 해제 실패: {component_name}, 오류: {str(decompress_error)}")
                        sql_content_map[component_name] = ''
                
                app_logger.debug(f"정제된 SQL 내용 조회 완료: {len(sql_content_map)}건")
                return sql_content_map
                
            finally:
                sql_content_db.disconnect()
                
        except Exception as e:
            app_logger.warning(f"SqlContent.db 조회 실패: {str(e)}")
            return {}
    
    def _get_filter_options(self) -> Dict[str, List[str]]:
        """필터링 옵션 데이터 조회 (동적 생성)"""
        try:
            filter_options = {}
            
            # 테이블 목록 (동적 조회)
            query = """
                SELECT DISTINCT t.table_name
                FROM tables t
                JOIN projects p ON t.project_id = p.project_id
                WHERE p.project_name = ? AND t.del_yn = 'N'
                ORDER BY t.table_name
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            filter_options['tables'] = [row['table_name'] for row in result]
            
            # 쿼리 타입 목록 (동적 조회)
            query = """
                SELECT DISTINCT component_type 
                FROM components 
                WHERE project_id = (SELECT project_id FROM projects WHERE project_name = ?)
                  AND (component_type LIKE 'SQL_%' OR component_type = 'QUERY')
                  AND del_yn = 'N'
                ORDER BY component_type
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            query_types = [row['component_type'] for row in result]
            
            # SQL_ 접두사 제거하여 표시용으로 변환
            display_query_types = []
            for qt in query_types:
                if qt.startswith('SQL_'):
                    display_query_types.append(qt[4:])  # SQL_ 제거
                else:
                    display_query_types.append(qt)
            
            filter_options['query_types'] = display_query_types
            
            app_logger.debug(f"필터링 옵션 조회 완료: {len(filter_options['tables'])}개 테이블, {len(filter_options['query_types'])}개 쿼리타입")
            return filter_options
            
        except Exception as e:
            handle_error(e, "필터링 옵션 조회 실패")
            return {'tables': [], 'query_types': []}
    
    def _generate_html(self, stats: Dict[str, int], chain_data: List[Dict[str, Any]], filter_options: Dict[str, List[str]]) -> str:
        """HTML 생성"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # HTML 템플릿 생성
            html_content = self.templates.get_callchain_template(
                project_name=self.project_name,
                timestamp=timestamp,
                stats=stats,
                chain_data=chain_data,
                filter_options=filter_options
            )
            
            app_logger.debug("HTML 생성 완료")
            return html_content
            
        except Exception as e:
            handle_error(e, "HTML 생성 실패")
            return ""
    
    def _save_report(self, html_content: str) -> str:
        """리포트 파일 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.project_name}_CallChainReport_{timestamp}.html"
            output_path = os.path.join(self.output_dir, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            app_logger.info(f"리포트 파일 저장 완료: {output_path}")
            return output_path
            
        except Exception as e:
            handle_error(e, "리포트 파일 저장 실패")
            return ""


if __name__ == '__main__':
    # 테스트용 실행
    generator = CallChainReportGenerator('sampleSrc', './temp')
    generator.generate_report()
