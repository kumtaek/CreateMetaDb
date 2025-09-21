"""
Sequence Diagram Report 생성기
- 메타디비 호출 체인 데이터를 기반으로 Mermaid 시퀀스 다이어그램 생성
- 다양한 시퀀스 다이어그램 타입 지원 (Full Chain, Method Call, Layer-based)
- 크로스플랫폼 호환 및 오프라인 실행 지원
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# 크로스플랫폼 경로 처리는 PathUtils 공통함수 사용
from util.logger import app_logger, handle_error
from util.path_utils import PathUtils
from util.database_utils import DatabaseUtils
from util.report_utils import ReportUtils
from util.config_utils import ConfigUtils
from util.layer_classification_utils import get_layer_classifier
from reports.report_templates import ReportTemplates


class SequenceDiagramReportGenerator:
    """Sequence Diagram Report 생성기 클래스"""
    
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
        self.report_utils = ReportUtils(project_name, output_dir)
        self.layer_classifier = get_layer_classifier()
        
        # 설정 로드 (공통함수 사용)
        try:
            self.config_utils = ConfigUtils()
            # target_source_config.yaml 로드 (동적 로직 구현)
            self.config = self.config_utils.load_yaml_config("config/target_source_config.yaml")
            if not self.config:
                # 기본 설정으로 폴백
                self.config = {}
                app_logger.warning("설정 파일 로드 실패, 기본 설정 사용")
        except Exception as e:
            handle_error(e, "설정 파일 로드 실패")
        
        # 메타데이터베이스 연결
        self.metadata_db_path = self.path_utils.get_project_metadata_db_path(project_name)
        self.db_utils = DatabaseUtils(self.metadata_db_path)
        
        if not self.db_utils.connect():
            handle_error(Exception("데이터베이스 연결 실패"), f"메타데이터베이스 연결 실패: {self.metadata_db_path}")
    
    def generate_report(self, diagram_types: Optional[List[str]] = None) -> bool:
        """
        Sequence Diagram Report 생성
        
        Args:
            diagram_types: 생성할 다이어그램 타입 리스트 
                          ['full_chain', 'method_call', 'layer_based', 'query_type']
                          None이면 모든 타입 생성
        
        Returns:
            생성 성공 여부 (True/False)
        """
        try:
            app_logger.info(f"Sequence Diagram Report 생성 시작: {self.project_name}")
            
            # 기본 다이어그램 타입 설정
            if diagram_types is None:
                diagram_types = ['full_chain', 'method_call', 'layer_based', 'query_type']
            
            # 1. 통계 정보 조회
            stats = self._get_statistics()
            
            # 2. 각 타입별 다이어그램 데이터 조회 및 생성
            diagrams_data = {}
            for diagram_type in diagram_types:
                try:
                    app_logger.info(f"다이어그램 생성 중: {diagram_type}")
                    
                    if diagram_type == 'full_chain':
                        diagrams_data[diagram_type] = self._generate_full_chain_diagram()
                    elif diagram_type == 'method_call':
                        diagrams_data[diagram_type] = self._generate_method_call_diagram()
                    elif diagram_type == 'layer_based':
                        diagrams_data[diagram_type] = self._generate_layer_based_diagram()
                    elif diagram_type == 'query_type':
                        diagrams_data[diagram_type] = self._generate_query_type_diagram()
                    else:
                        app_logger.warning(f"지원하지 않는 다이어그램 타입: {diagram_type}")
                        continue
                        
                except Exception as e:
                    handle_error(e, f"{diagram_type} 다이어그램 생성 실패")
            
            # 3. HTML 생성
            html_content = self._generate_html(stats, diagrams_data)
            
            # 4. CSS 및 JS 파일 복사
            self.report_utils.copy_assets()
            
            # 5. 파일 저장
            output_file = self.report_utils.save_report(html_content, "SequenceDiagramReport")
            
            app_logger.info(f"Sequence Diagram Report 생성 완료: {output_file}")
            return True
            
        except Exception as e:
            handle_error(e, "Sequence Diagram Report 생성 실패")
            return False
        finally:
            self.db_utils.disconnect()
    
    def _get_statistics(self) -> Dict[str, int]:
        """통계 정보 조회"""
        try:
            stats = {}
            
            # 호출 체인 수
            query = """
                SELECT COUNT(*) as count
                FROM components api
                JOIN relationships r1 ON api.component_id = r1.src_id AND r1.rel_type = 'CALL_METHOD'
                JOIN components method ON r1.dst_id = method.component_id
                JOIN projects p ON api.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND api.component_type = 'API_URL'
                  AND api.del_yn = 'N'
                  AND method.del_yn = 'N'
                  AND r1.del_yn = 'N'
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['call_chains'] = result[0]['count'] if result else 0
            
            # 메서드 호출 관계 수
            query = """
                SELECT COUNT(*) as count
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                JOIN components dst ON r.dst_id = dst.component_id
                JOIN projects p ON src.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND r.rel_type = 'CALL_METHOD'
                  AND src.component_type = 'METHOD'
                  AND dst.component_type = 'METHOD'
                  AND r.del_yn = 'N'
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['method_calls'] = result[0]['count'] if result else 0
            
            # 쿼리 호출 관계 수
            query = """
                SELECT COUNT(*) as count
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                JOIN components dst ON r.dst_id = dst.component_id
                JOIN projects p ON src.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND r.rel_type = 'CALL_QUERY'
                  AND src.component_type = 'METHOD'
                  AND r.del_yn = 'N'
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['query_calls'] = result[0]['count'] if result else 0
            
            # 레이어별 컴포넌트 수
            query = """
                SELECT layer, COUNT(*) as count
                FROM components c
                JOIN projects p ON c.project_id = p.project_id
                WHERE p.project_name = ? 
                  AND c.del_yn = 'N'
                  AND c.layer IS NOT NULL
                GROUP BY layer
            """
            result = self.db_utils.execute_query(query, (self.project_name,))
            stats['layers'] = {row['layer']: row['count'] for row in result} if result else {}
            
            app_logger.debug(f"통계 정보 조회 완료: {stats}")
            return stats
            
        except Exception as e:
            handle_error(e, "통계 정보 조회 실패")
            return {}
    
    def _generate_full_chain_diagram(self) -> Dict[str, Any]:
        """Full Chain 시퀀스 다이어그램 생성"""
        try:
            # 호출 체인 데이터 조회
            query = """
                SELECT 
                    f.file_name as jsp_file,
                    api.component_name as api_entry,
                    cls.class_name,
                    method.component_name as method_name,
                    xml_f.file_name as xml_file,
                    sql.component_name as query_id,
                    sql.component_type as query_type,
                    GROUP_CONCAT(DISTINCT t.table_name) as related_tables
                FROM components api
                JOIN files f ON api.file_id = f.file_id
                JOIN relationships r1 ON api.component_id = r1.src_id AND r1.rel_type = 'CALL_METHOD'
                JOIN components method ON r1.dst_id = method.component_id
                JOIN classes cls ON method.parent_id = cls.class_id
                LEFT JOIN relationships r2 ON method.component_id = r2.src_id AND r2.rel_type = 'CALL_QUERY'
                LEFT JOIN components sql ON r2.dst_id = sql.component_id
                LEFT JOIN files xml_f ON sql.file_id = xml_f.file_id
                LEFT JOIN relationships r3 ON sql.component_id = r3.src_id AND r3.rel_type = 'USE_TABLE'
                LEFT JOIN tables t ON r3.dst_id = t.component_id
                JOIN projects p ON api.project_id = p.project_id
                WHERE p.project_name = ?
                  AND api.component_type = 'API_URL'
                  AND api.del_yn = 'N'
                  AND method.del_yn = 'N'
                  AND r1.del_yn = 'N'
                GROUP BY f.file_name, api.component_name, cls.class_name, 
                         method.component_name, xml_f.file_name, sql.component_name
                LIMIT 10
            """
            
            results = self.db_utils.execute_query(query, (self.project_name,))
            
            if not results:
                return {
                    'title': 'Full Call Chain Sequence',
                    'mermaid_code': 'sequenceDiagram\n    Note over Client: 호출 체인 데이터가 없습니다',
                    'description': '프론트엔드부터 데이터베이스까지의 완전한 호출 체인'
                }
            
            # Mermaid 시퀀스 다이어그램 코드 생성
            mermaid_lines = ['sequenceDiagram']
            
            # 참가자 정의
            participants = set()
            for row in results:
                participants.add('Frontend')
                participants.add('API_Gateway')
                participants.add(row['class_name'])
                if row['xml_file'] and row['xml_file'] != 'NO-QUERY':
                    participants.add('XML_Mapper')
                if row['related_tables'] and row['related_tables'] != 'NO-TABLE':
                    participants.add('Database')
            
            # 참가자 선언
            for participant in sorted(participants):
                clean_name = self._clean_participant_name(participant)
                mermaid_lines.append(f'    participant {clean_name} as {participant}')
            
            mermaid_lines.append('')
            
            # 시퀀스 생성
            for i, row in enumerate(results):
                api_name = self._clean_api_name(row['api_entry'])
                method_name = row['method_name']
                class_name = self._clean_participant_name(row['class_name'])
                
                # Database participant가 없으면 다른 participant 사용
                if 'Database' in participants:
                    mermaid_lines.append(f'    Note over Frontend,Database: Flow {i+1} - {api_name}')
                else:
                    mermaid_lines.append(f'    Note over Frontend,API_Gateway: Flow {i+1} - {api_name}')
                mermaid_lines.append(f'    Frontend->>API_Gateway: {api_name}')
                mermaid_lines.append(f'    API_Gateway->>{class_name}: {method_name}()')
                
                if row['xml_file'] and row['xml_file'] != 'NO-QUERY':
                    query_name = row['query_id'] or 'query'
                    mermaid_lines.append(f'    {class_name}->>XML_Mapper: {query_name}')
                    
                    if row['related_tables'] and row['related_tables'] != 'NO-TABLE':
                        tables = row['related_tables'].split(',')[:3]  # 최대 3개 테이블만
                        table_list = ','.join(tables)
                        mermaid_lines.append(f'    XML_Mapper->>Database: SELECT FROM {table_list}')
                        mermaid_lines.append(f'    Database-->>XML_Mapper: Result Set')
                        
                    mermaid_lines.append(f'    XML_Mapper-->>{class_name}: Data')
                else:
                    mermaid_lines.append(f'    Note right of {class_name}: Calculation Only')
                
                mermaid_lines.append(f'    {class_name}-->>API_Gateway: Response')
                mermaid_lines.append(f'    API_Gateway-->>Frontend: JSON Data')
                mermaid_lines.append('')
            
            mermaid_code = '\n'.join(mermaid_lines)
            
            return {
                'title': 'Full Call Chain Sequence',
                'mermaid_code': mermaid_code,
                'description': '프론트엔드부터 데이터베이스까지의 완전한 호출 체인',
                'data_count': len(results)
            }
            
        except Exception as e:
            handle_error(e, "Full Chain 다이어그램 생성 실패")
            return {}
    
    def _generate_method_call_diagram(self) -> Dict[str, Any]:
        """Method Call 시퀀스 다이어그램 생성"""
        try:
            # 메서드 호출 관계 조회
            query = """
                SELECT 
                    src_cls.class_name as src_class,
                    src_method.component_name as src_method,
                    dst_cls.class_name as dst_class,
                    dst_method.component_name as dst_method
                FROM relationships r
                JOIN components src_method ON r.src_id = src_method.component_id
                JOIN components dst_method ON r.dst_id = dst_method.component_id
                JOIN classes src_cls ON src_method.parent_id = src_cls.class_id
                JOIN classes dst_cls ON dst_method.parent_id = dst_cls.class_id
                JOIN projects p ON src_method.project_id = p.project_id
                WHERE p.project_name = ?
                  AND r.rel_type = 'CALL_METHOD'
                  AND src_method.component_type = 'METHOD'
                  AND dst_method.component_type = 'METHOD'
                  AND r.del_yn = 'N'
                LIMIT 15
            """
            
            results = self.db_utils.execute_query(query, (self.project_name,))
            
            if not results:
                return {
                    'title': 'Method Call Sequence',
                    'mermaid_code': 'sequenceDiagram\n    Note over Client: 메서드 호출 관계 데이터가 없습니다',
                    'description': 'Java 메서드 간 호출 관계'
                }
            
            # Mermaid 시퀀스 다이어그램 코드 생성
            mermaid_lines = ['sequenceDiagram']
            
            # 참가자 수집
            participants = set()
            for row in results:
                participants.add(row['src_class'])
                participants.add(row['dst_class'])
            
            # 참가자 선언
            for participant in sorted(participants):
                clean_name = self._clean_participant_name(participant)
                mermaid_lines.append(f'    participant {clean_name} as {participant}')
            
            mermaid_lines.append('')
            # Note over에는 최대 2개 participant만 사용 (Mermaid 제한)
            participant_names = [self._clean_participant_name(p) for p in sorted(participants)]
            if len(participant_names) <= 2:
                note_participants = ','.join(participant_names)
            else:
                note_participants = f'{participant_names[0]},{participant_names[-1]}'
            mermaid_lines.append(f'    Note over {note_participants}: Method Call Chain')
            
            # 시퀀스 생성
            for row in results:
                src_class = self._clean_participant_name(row['src_class'])
                dst_class = self._clean_participant_name(row['dst_class'])
                dst_method = row['dst_method']
                
                mermaid_lines.append(f'    {src_class}->>{dst_class}: {dst_method}()')
                mermaid_lines.append(f'    {dst_class}-->>{src_class}: return')
            
            mermaid_code = '\n'.join(mermaid_lines)
            
            return {
                'title': 'Method Call Sequence',
                'mermaid_code': mermaid_code,
                'description': 'Java 메서드 간 호출 관계',
                'data_count': len(results)
            }
            
        except Exception as e:
            handle_error(e, "Method Call 다이어그램 생성 실패")
            return {}
    
    def _generate_layer_based_diagram(self) -> Dict[str, Any]:
        """Layer-based 시퀀스 다이어그램 생성"""
        try:
            # 레이어별 호출 관계 조회
            query = """
                SELECT DISTINCT
                    src.layer as src_layer,
                    dst.layer as dst_layer,
                    r.rel_type,
                    COUNT(*) as call_count
                FROM relationships r
                JOIN components src ON r.src_id = src.component_id
                JOIN components dst ON r.dst_id = dst.component_id
                JOIN projects p ON src.project_id = p.project_id
                WHERE p.project_name = ?
                  AND src.layer IS NOT NULL
                  AND dst.layer IS NOT NULL
                  AND src.layer != dst.layer
                  AND r.del_yn = 'N'
                GROUP BY src.layer, dst.layer, r.rel_type
                ORDER BY call_count DESC
                LIMIT 10
            """
            
            results = self.db_utils.execute_query(query, (self.project_name,))
            
            if not results:
                return {
                    'title': 'Layer-based Sequence',
                    'mermaid_code': 'sequenceDiagram\n    Note over Client: 레이어 간 호출 관계 데이터가 없습니다',
                    'description': '시스템 레이어별 호출 관계'
                }
            
            # Mermaid 시퀀스 다이어그램 코드 생성
            mermaid_lines = ['sequenceDiagram']
            
            # 참가자 수집 및 정렬
            participants = set()
            for row in results:
                participants.add(row['src_layer'])
                participants.add(row['dst_layer'])
            
            # 레이어 순서 정의
            layer_order = ['FRONTEND', 'API_ENTRY', 'CONTROLLER', 'SERVICE', 'DAO', 'MAPPER', 'DATA']
            ordered_participants = []
            for layer in layer_order:
                if layer in participants:
                    ordered_participants.append(layer)
            
            # 순서에 없는 레이어 추가
            for participant in sorted(participants):
                if participant not in ordered_participants:
                    ordered_participants.append(participant)
            
            # 참가자 선언
            for participant in ordered_participants:
                clean_name = self._clean_participant_name(participant)
                mermaid_lines.append(f'    participant {clean_name} as {participant}_Layer')
            
            mermaid_lines.append('')
            # Note over에는 최대 2개 participant만 사용 (Mermaid 제한)
            participant_names = [self._clean_participant_name(p) for p in ordered_participants]
            if len(participant_names) <= 2:
                note_participants = ','.join(participant_names)
            else:
                note_participants = f'{participant_names[0]},{participant_names[-1]}'
            mermaid_lines.append(f'    Note over {note_participants}: Layered Architecture Flow')
            
            # 시퀀스 생성
            for row in results:
                src_layer = self._clean_participant_name(row['src_layer'])
                dst_layer = self._clean_participant_name(row['dst_layer'])
                rel_type = row['rel_type']
                call_count = row['call_count']
                
                if rel_type == 'CALL_METHOD':
                    mermaid_lines.append(f'    {src_layer}->>{dst_layer}: Method Call ({call_count})')
                elif rel_type == 'CALL_QUERY':
                    mermaid_lines.append(f'    {src_layer}->>{dst_layer}: Query Call ({call_count})')
                else:
                    mermaid_lines.append(f'    {src_layer}->>{dst_layer}: {rel_type} ({call_count})')
                
                mermaid_lines.append(f'    {dst_layer}-->>{src_layer}: Response')
            
            mermaid_code = '\n'.join(mermaid_lines)
            
            return {
                'title': 'Layer-based Sequence',
                'mermaid_code': mermaid_code,
                'description': '시스템 레이어별 호출 관계',
                'data_count': len(results)
            }
            
        except Exception as e:
            handle_error(e, "Layer-based 다이어그램 생성 실패")
            return {}
    
    def _generate_query_type_diagram(self) -> Dict[str, Any]:
        """Query Type별 시퀀스 다이어그램 생성"""
        try:
            # 쿼리 타입별 호출 관계 조회
            query = """
                SELECT 
                    method.component_name as method_name,
                    cls.class_name,
                    sql.component_name as query_id,
                    sql.component_type as query_type,
                    GROUP_CONCAT(DISTINCT t.table_name) as related_tables
                FROM relationships r
                JOIN components method ON r.src_id = method.component_id
                JOIN components sql ON r.dst_id = sql.component_id
                JOIN classes cls ON method.parent_id = cls.class_id
                LEFT JOIN relationships r2 ON sql.component_id = r2.src_id AND r2.rel_type = 'USE_TABLE'
                LEFT JOIN tables t ON r2.dst_id = t.component_id
                JOIN projects p ON method.project_id = p.project_id
                WHERE p.project_name = ?
                  AND r.rel_type = 'CALL_QUERY'
                  AND method.component_type = 'METHOD'
                  AND r.del_yn = 'N'
                GROUP BY method.component_name, cls.class_name, sql.component_name, sql.component_type
                ORDER BY sql.component_type, sql.component_name
                LIMIT 8
            """
            
            results = self.db_utils.execute_query(query, (self.project_name,))
            
            if not results:
                return {
                    'title': 'Query Type Sequence',
                    'mermaid_code': 'sequenceDiagram\n    Note over Client: 쿼리 타입별 호출 관계 데이터가 없습니다',
                    'description': '쿼리 타입별 호출 관계'
                }
            
            # Mermaid 시퀀스 다이어그램 코드 생성
            mermaid_lines = ['sequenceDiagram']
            
            # 참가자 선언
            mermaid_lines.extend([
                '    participant Client as Client',
                '    participant App as Application',
                '    participant XML as XML_Mapper',
                '    participant Inferred as Inferred_Query',
                '    participant DB as Database'
            ])
            
            mermaid_lines.append('')
            mermaid_lines.append('    Note over Client,DB: Different Query Types')
            
            # 쿼리 타입별 그룹핑
            sql_queries = [r for r in results if r['query_type'] and r['query_type'].startswith('SQL_')]
            inferred_queries = [r for r in results if r['query_type'] == 'QUERY']
            
            # SQL 타입 쿼리
            if sql_queries:
                mermaid_lines.append('')
                mermaid_lines.append('    rect rgb(200, 255, 200)')
                mermaid_lines.append('        Note right of Client: XML-based Queries')
                
                for row in sql_queries[:3]:  # 최대 3개만
                    method_name = row['method_name']
                    query_type = row['query_type'][4:]  # SQL_ 제거
                    tables = row['related_tables'] or 'UNKNOWN'
                    
                    mermaid_lines.extend([
                        f'        Client->>App: {method_name}()',
                        f'        App->>XML: {query_type} Query',
                        f'        XML->>DB: {query_type} FROM {tables}',
                        f'        DB-->>XML: Result Set',
                        f'        XML-->>App: Mapped Objects',
                        f'        App-->>Client: Data'
                    ])
                
                mermaid_lines.append('    end')
            
            # INFERRED 쿼리
            if inferred_queries:
                mermaid_lines.append('')
                mermaid_lines.append('    rect rgb(255, 255, 200)')
                mermaid_lines.append('        Note right of Client: Inferred Queries')
                
                for row in inferred_queries[:2]:  # 최대 2개만
                    method_name = row['method_name']
                    query_id = row['query_id']
                    
                    mermaid_lines.extend([
                        f'        Client->>App: {method_name}()',
                        f'        App->>Inferred: {query_id}',
                        '        Note right of Inferred: Java에서 추론된 쿼리',
                        f'        Inferred->>DB: Inferred SQL',
                        f'        DB-->>Inferred: Result',
                        f'        Inferred-->>App: Data',
                        f'        App-->>Client: Response'
                    ])
                
                mermaid_lines.append('    end')
            
            mermaid_code = '\n'.join(mermaid_lines)
            
            return {
                'title': 'Query Type Sequence',
                'mermaid_code': mermaid_code,
                'description': '쿼리 타입별 호출 관계 (XML-based vs Inferred)',
                'data_count': len(results)
            }
            
        except Exception as e:
            handle_error(e, "Query Type 다이어그램 생성 실패")
            return {}
    
    def _clean_participant_name(self, name: str) -> str:
        """참가자 이름을 Mermaid 호환 형태로 정리"""
        if not name:
            return "Unknown"
        
        # 특수문자 제거 및 언더스코어로 변환
        clean_name = ''.join(c if c.isalnum() else '_' for c in name)
        
        # 연속된 언더스코어 제거
        while '__' in clean_name:
            clean_name = clean_name.replace('__', '_')
        
        # 앞뒤 언더스코어 제거
        clean_name = clean_name.strip('_')
        
        # 빈 문자열이면 기본값
        if not clean_name:
            clean_name = "Unknown"
        
        return clean_name
    
    def _clean_api_name(self, api_name: str) -> str:
        """API 이름을 정리"""
        if not api_name:
            return "API"
        
        # API_ENTRY. 접두사 제거
        if api_name.startswith('API_ENTRY.'):
            api_name = api_name[10:]
        
        # HTTP 메소드와 URL 분리
        if '_' in api_name:
            parts = api_name.split('_', 1)
            if len(parts) == 2:
                return f"{parts[0]} {parts[1]}"
        
        return api_name
    
    def _generate_html(self, stats: Dict[str, int], diagrams_data: Dict[str, Dict[str, Any]]) -> str:
        """HTML 생성 - woori.css 기반 통일된 스타일 적용"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 다이어그램 섹션 HTML 생성
            diagrams_html = self._generate_diagrams_html(diagrams_data)
            
            # 통계 HTML 생성 (woori.css 스타일 적용)
            stats_html = self._generate_sequence_stats_html(stats)
            
            html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sequence Diagram Report - {self.project_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
    <link rel="stylesheet" href="css/woori.css">
    <style>
        /* === Sequence Diagram 전용 스타일 === */
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 2px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            width: 100%;
            max-width: 100%;
            margin: 0;
            background: white;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
            min-height: 100vh;
        }}
        
        .content {{
            padding: 6px;
        }}
        
        .section {{
            margin-bottom: 8px;
            background: white;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
            overflow: hidden;
        }}
        
        .section h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding: 8px 12px;
            margin: 0;
            font-size: 1.1em;
            background: #f8f9fa;
        }}
        
        .diagram-description {{
            color: #7f8c8d;
            margin: 8px 12px;
            font-style: italic;
            font-size: 0.9em;
        }}
        
        .diagram-controls {{
            padding: 8px 12px;
            text-align: right;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .btn {{
            background: var(--primary-blue);
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: var(--border-radius-small);
            cursor: pointer;
            margin-left: 5px;
            font-size: 0.8em;
            transition: background-color 0.3s ease;
        }}
        
        .btn:hover {{
            background: var(--primary-dark);
        }}
        
        /* === Mermaid 시퀀스 다이어그램 최적화 === */
        .mermaid-container {{
            background: white;
            padding: 15px;
            overflow-x: auto;
            overflow-y: hidden;
            /* 가로 스크롤 허용하여 축소 방지 */
            min-width: 100%;
            max-height: 70vh;
        }}
        
        .mermaid {{
            /* 시퀀스 다이어그램 최소 너비 보장 */
            min-width: 800px;
            width: max-content;
            margin: 0 auto;
            font-size: 14px;
        }}
        
        /* === 시퀀스 다이어그램 스크롤바 스타일링 === */
        .mermaid-container::-webkit-scrollbar {{
            height: 8px;
        }}
        
        .mermaid-container::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 4px;
        }}
        
        .mermaid-container::-webkit-scrollbar-thumb {{
            background: var(--primary-blue);
            border-radius: 4px;
        }}
        
        .mermaid-container::-webkit-scrollbar-thumb:hover {{
            background: var(--primary-dark);
        }}
        
        /* === 반응형 최적화 === */
        @media (max-width: 768px) {{
            .mermaid {{
                min-width: 600px;
                font-size: 12px;
            }}
        }}
        
        /* === 다이어그램별 색상 구분 === */
        .diagram-full-chain .mermaid-container {{
            border-left: 4px solid #27ae60;
        }}
        
        .diagram-method-call .mermaid-container {{
            border-left: 4px solid #e74c3c;
        }}
        
        .diagram-layer-based .mermaid-container {{
            border-left: 4px solid #f39c12;
        }}
        
        .diagram-query-type .mermaid-container {{
            border-left: 4px solid #9b59b6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- woori.css 헤더 스타일 적용 -->
        <div class="header">
            <h1>Sequence Diagram Report</h1>
            <div class="subtitle">프로젝트: {self.project_name} | 생성일시: {timestamp}</div>
        </div>
        
        <!-- woori.css 통계 스타일 적용 -->
        {stats_html}
        
        <div class="content">
            {diagrams_html}
        </div>
        
        <!-- woori.css 푸터 스타일 적용 -->
        <div class="footer">
            <p>Sequence Diagram Report | Generated by SourceAnalyzer</p>
        </div>
    </div>

    <script>
        // Mermaid 초기화 - 시퀀스 다이어그램 최적화
        mermaid.initialize({{
            startOnLoad: false,
            theme: 'default',
            securityLevel: 'loose',
            sequence: {{
                diagramMarginX: 30,
                diagramMarginY: 15,
                actorMargin: 60,
                width: 120,
                height: 50,
                boxMargin: 8,
                boxTextMargin: 4,
                noteMargin: 8,
                messageMargin: 30,
                mirrorActors: false,
                bottomMarginAdj: 1,
                useMaxWidth: false,  // 축소 방지
                rightAngles: false,
                showSequenceNumbers: false,
                wrap: false,
                fontSize: 14
            }},
            flowchart: {{
                useMaxWidth: false
            }}
        }});

        // 다이어그램 내보내기 함수 개선
        function exportDiagram(diagramId, format) {{
            const element = document.getElementById(diagramId);
            if (!element) {{
                alert('다이어그램을 찾을 수 없습니다.');
                return;
            }}
            
            try {{
                if (format === 'png') {{
                    // PNG 내보내기 로직 (향후 구현)
                    console.log('PNG 내보내기:', diagramId);
                    alert('PNG 내보내기 기능은 준비 중입니다.');
                }} else if (format === 'svg') {{
                    // SVG 내보내기 로직 (향후 구현)
                    console.log('SVG 내보내기:', diagramId);
                    alert('SVG 내보내기 기능은 준비 중입니다.');
                }}
            }} catch (error) {{
                console.error('내보내기 오류:', error);
                alert('내보내기 중 오류가 발생했습니다.');
            }}
        }}

        // 다이어그램 확대/축소 함수
        function zoomDiagram(diagramId, scale) {{
            const element = document.getElementById(diagramId);
            if (!element) return;
            
            const currentTransform = element.style.transform;
            const currentScale = currentTransform.match(/scale\\(([^)]+)\\)/);
            const newScale = currentScale ? parseFloat(currentScale[1]) * scale : scale;
            
            element.style.transform = `scale(${{newScale}})`;
            element.style.transformOrigin = 'top left';
        }}

        // 페이지 로드 완료 후 Mermaid 렌더링
        document.addEventListener('DOMContentLoaded', function() {{
            // 순차적으로 다이어그램 렌더링
            setTimeout(() => {{
                mermaid.init(undefined, '.mermaid').then(() => {{
                    console.log('모든 시퀀스 다이어그램 렌더링 완료');
                }}).catch(error => {{
                    console.error('Mermaid 렌더링 오류:', error);
                }});
            }}, 100);
        }});

        // 스크롤 위치 저장/복원
        window.addEventListener('beforeunload', function() {{
            sessionStorage.setItem('scrollPosition', window.scrollY);
        }});

        window.addEventListener('load', function() {{
            const scrollPosition = sessionStorage.getItem('scrollPosition');
            if (scrollPosition) {{
                window.scrollTo(0, parseInt(scrollPosition));
                sessionStorage.removeItem('scrollPosition');
            }}
        }});
    </script>
</body>
</html>"""
            
            app_logger.debug("HTML 생성 완료")
            return html_content
            
        except Exception as e:
            handle_error(e, "HTML 생성 실패")
            return ""
    
    def _generate_diagrams_html(self, diagrams_data: Dict[str, Dict[str, Any]]) -> str:
        """다이어그램 섹션 HTML 생성 - woori.css 스타일 적용"""
        html_parts = []
        
        # 다이어그램 타입별 색상 및 라벨 매핑 (이모지 사용 금지)
        diagram_config = {
            'full_chain': {'color': '#27ae60', 'label': '[Full Chain]', 'order': 1},
            'method_call': {'color': '#e74c3c', 'label': '[Method Call]', 'order': 2},
            'layer_based': {'color': '#f39c12', 'label': '[Layer Based]', 'order': 3},
            'query_type': {'color': '#9b59b6', 'label': '[Query Type]', 'order': 4}
        }
        
        # 순서대로 정렬
        sorted_diagrams = sorted(diagrams_data.items(), 
                               key=lambda x: diagram_config.get(x[0], {}).get('order', 999))
        
        for diagram_type, data in sorted_diagrams:
            if not data:
                continue
            
            title = data.get('title', diagram_type)
            description = data.get('description', '')
            mermaid_code = data.get('mermaid_code', '')
            data_count = data.get('data_count', 0)
            
            config = diagram_config.get(diagram_type, {'color': '#3498db', 'label': '[Diagram]', 'order': 999})
            diagram_id = f"diagram_{diagram_type}"
            
            html_parts.append(f"""
            <div class="section diagram-{diagram_type}">
                <h2>{config['label']} {title}</h2>
                <p class="diagram-description">{description} (데이터: {data_count}건)</p>
                <div class="diagram-controls">
                    <button class="btn" onclick="zoomDiagram('{diagram_id}', 1.2)" title="확대">확대</button>
                    <button class="btn" onclick="zoomDiagram('{diagram_id}', 0.8)" title="축소">축소</button>
                    <button class="btn" onclick="zoomDiagram('{diagram_id}', 1)" title="원본크기">100%</button>
                    <button class="btn" onclick="exportDiagram('{diagram_id}', 'png')">PNG</button>
                    <button class="btn" onclick="exportDiagram('{diagram_id}', 'svg')">SVG</button>
                </div>
                <div class="mermaid-container">
                    <div id="{diagram_id}" class="mermaid">
{mermaid_code}
                    </div>
                </div>
            </div>
            """)
        
        # 다이어그램이 없는 경우
        if not html_parts:
            html_parts.append("""
            <div class="section">
                <h2>시퀀스 다이어그램</h2>
                <p class="diagram-description">생성할 수 있는 시퀀스 다이어그램 데이터가 없습니다.</p>
                <div class="mermaid-container">
                    <div class="mermaid">
                        sequenceDiagram
                            Note over Client: 호출 체인 데이터가 부족합니다
                            Note over Client: 메타디비를 다시 생성해주세요
                    </div>
                </div>
            </div>
            """)
        
        return '\n'.join(html_parts)
    
    def _generate_sequence_stats_html(self, stats: Dict[str, int]) -> str:
        """시퀀스 다이어그램용 통계 HTML 생성 - woori.css 스타일 적용"""
        return f"""
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{stats.get('call_chains', 0)}</div>
                <div class="stat-label">호출 체인</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('method_calls', 0)}</div>
                <div class="stat-label">메서드 호출</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('query_calls', 0)}</div>
                <div class="stat-label">쿼리 호출</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(stats.get('layers', {}))}</div>
                <div class="stat-label">아키텍처 레이어</div>
            </div>
        </div>
        """


if __name__ == '__main__':
    import sys
    from util.arg_utils import ArgUtils
    
    # 명령행 인자 파싱
    arg_utils = ArgUtils()
    parser = arg_utils.create_parser("Sequence Diagram Report 생성기")
    
    # 다이어그램 타입 옵션 추가
    parser.add_argument('--diagram-types', 
                       nargs='*',
                       choices=['full_chain', 'method_call', 'layer_based', 'query_type'],
                       help='생성할 다이어그램 타입 (기본: 모든 타입)')
    
    args = parser.parse_args()
    
    project_name = args.project_name
    diagram_types = args.diagram_types
    
    print(f"Sequence Diagram Report 생성 시작: {project_name}")
    if diagram_types:
        print(f"다이어그램 타입: {', '.join(diagram_types)}")
    
    generator = SequenceDiagramReportGenerator(project_name, './temp')
    result = generator.generate_report(diagram_types)
    
    if result:
        print(f"Sequence Diagram Report 생성 완료: {project_name}")
    else:
        print(f"Sequence Diagram Report 생성 실패: {project_name}")
