"""
SQLite 메타데이터베이스를 Neo4j 그래프 데이터베이스로 마이그레이션하는 스크립트

주요 기능:
1. SQLite 데이터 추출
2. 그래프 구조로 변환
3. Neo4j에 노드 및 관계 생성
4. 인덱스 및 제약조건 설정
"""

import sqlite3
import json
import pandas as pd
from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional
import os
import sys
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.database_utils import DatabaseUtils
from util.logger import app_logger, handle_error


class Neo4jMigrator:
    """SQLite to Neo4j 마이그레이션 클래스"""
    
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687", 
                 neo4j_user: str = "neo4j", neo4j_password: str = "password"):
        """
        Neo4j 연결 초기화
        
        Args:
            neo4j_uri: Neo4j 데이터베이스 URI
            neo4j_user: Neo4j 사용자명
            neo4j_password: Neo4j 비밀번호
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver = None
        self.db_utils = DatabaseUtils()
        
    def connect_neo4j(self):
        """Neo4j 데이터베이스 연결"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, self.neo4j_password)
            )
            # 연결 테스트
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            app_logger.info("Neo4j 연결 성공")
            return True
        except Exception as e:
            handle_error(f"Neo4j 연결 실패: {e}")
            return False
    
    def close_neo4j(self):
        """Neo4j 연결 종료"""
        if self.driver:
            self.driver.close()
            app_logger.info("Neo4j 연결 종료")
    
    def extract_sqlite_data(self, project_name: str) -> Dict[str, List[Dict]]:
        """
        SQLite에서 모든 테이블 데이터 추출
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            테이블별 데이터 딕셔너리
        """
        data = {}
        
        try:
            # 프로젝트 정보 조회
            project_id = self.db_utils.get_project_id_by_name(project_name)
            if not project_id:
                raise ValueError(f"프로젝트 '{project_name}'을 찾을 수 없습니다")
            
            # 각 테이블별 데이터 추출
            tables = ['projects', 'files', 'classes', 'components', 'tables', 'columns', 'relationships']
            
            for table in tables:
                if table == 'projects':
                    query = f"SELECT * FROM {table} WHERE project_id = ?"
                    data[table] = self.db_utils.execute_query(query, (project_id,), fetch_all=True)
                else:
                    query = f"SELECT * FROM {table} WHERE project_id = ? AND del_yn = 'N'"
                    data[table] = self.db_utils.execute_query(query, (project_id,), fetch_all=True)
                
                app_logger.info(f"{table} 테이블: {len(data[table])}개 레코드 추출")
            
            return data
            
        except Exception as e:
            handle_error(f"SQLite 데이터 추출 실패: {e}")
            return {}
    
    def transform_to_graph_model(self, data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        관계형 데이터를 그래프 모델로 변환
        
        Args:
            data: SQLite에서 추출한 데이터
            
        Returns:
            그래프 모델 데이터 (nodes, relationships)
        """
        nodes = []
        relationships = []
        
        try:
            # 1. Project 노드 생성
            for project in data.get('projects', []):
                nodes.append({
                    'label': 'Project',
                    'id': f"project_{project['project_id']}",
                    'properties': {
                        'project_id': project['project_id'],
                        'name': project['project_name'],
                        'path': project['project_path'],
                        'hash_value': project.get('hash_value'),
                        'created_at': project['created_at'],
                        'updated_at': project['updated_at'],
                        'total_files': project.get('total_files', 0)
                    }
                })
            
            # 2. File 노드 생성
            for file in data.get('files', []):
                nodes.append({
                    'label': 'File',
                    'id': f"file_{file['file_id']}",
                    'properties': {
                        'file_id': file['file_id'],
                        'name': file['file_name'],
                        'path': file['file_path'],
                        'type': file['file_type'],
                        'hash_value': file['hash_value'],
                        'line_count': file.get('line_count'),
                        'file_size': file.get('file_size'),
                        'has_error': file['has_error'],
                        'error_message': file.get('error_message'),
                        'created_at': file['created_at'],
                        'updated_at': file['updated_at']
                    }
                })
                
                # Project-File 관계 생성
                relationships.append({
                    'type': 'CONTAINS',
                    'from_id': f"project_{file['project_id']}",
                    'to_id': f"file_{file['file_id']}",
                    'properties': {}
                })
            
            # 3. Class 노드 생성
            for cls in data.get('classes', []):
                nodes.append({
                    'label': 'Class',
                    'id': f"class_{cls['class_id']}",
                    'properties': {
                        'class_id': cls['class_id'],
                        'name': cls['class_name'],
                        'line_start': cls.get('line_start'),
                        'line_end': cls.get('line_end'),
                        'hash_value': cls['hash_value'],
                        'has_error': cls['has_error'],
                        'error_message': cls.get('error_message'),
                        'created_at': cls['created_at'],
                        'updated_at': cls['updated_at']
                    }
                })
                
                # File-Class 관계 생성
                relationships.append({
                    'type': 'DEFINES',
                    'from_id': f"file_{cls['file_id']}",
                    'to_id': f"class_{cls['class_id']}",
                    'properties': {}
                })
                
                # Class 상속 관계 생성
                if cls.get('parent_class_id'):
                    relationships.append({
                        'type': 'INHERITS',
                        'from_id': f"class_{cls['class_id']}",
                        'to_id': f"class_{cls['parent_class_id']}",
                        'properties': {}
                    })
            
            # 4. Component 노드 생성
            for component in data.get('components', []):
                # 컴포넌트 타입에 따른 레이블 결정
                component_type = component['component_type']
                if component_type in ['SQL_SELECT', 'SQL_INSERT', 'SQL_UPDATE', 'SQL_DELETE']:
                    label = 'SQLQuery'
                elif component_type == 'API_URL':
                    label = 'APIEndpoint'
                elif component_type == 'METHOD':
                    label = 'Method'
                elif component_type == 'TABLE':
                    label = 'Table'
                elif component_type == 'COLUMN':
                    label = 'Column'
                else:
                    label = 'Component'
                
                nodes.append({
                    'label': label,
                    'id': f"component_{component['component_id']}",
                    'properties': {
                        'component_id': component['component_id'],
                        'name': component['component_name'],
                        'type': component_type,
                        'layer': component.get('layer'),
                        'line_start': component.get('line_start'),
                        'line_end': component.get('line_end'),
                        'hash_value': component['hash_value'],
                        'has_error': component['has_error'],
                        'error_message': component.get('error_message'),
                        'created_at': component['created_at'],
                        'updated_at': component['updated_at']
                    }
                })
                
                # File-Component 관계 생성
                relationships.append({
                    'type': 'CONTAINS',
                    'from_id': f"file_{component['file_id']}",
                    'to_id': f"component_{component['component_id']}",
                    'properties': {}
                })
                
                # Parent-Child 관계 생성 (METHOD의 경우 Class와 연결)
                if component.get('parent_id'):
                    if component_type == 'METHOD':
                        relationships.append({
                            'type': 'BELONGS_TO',
                            'from_id': f"component_{component['component_id']}",
                            'to_id': f"class_{component['parent_id']}",
                            'properties': {}
                        })
                    else:
                        relationships.append({
                            'type': 'BELONGS_TO',
                            'from_id': f"component_{component['component_id']}",
                            'to_id': f"component_{component['parent_id']}",
                            'properties': {}
                        })
            
            # 5. Table 노드 생성 (components의 TABLE과 별도)
            for table in data.get('tables', []):
                nodes.append({
                    'label': 'DatabaseTable',
                    'id': f"table_{table['table_id']}",
                    'properties': {
                        'table_id': table['table_id'],
                        'name': table['table_name'],
                        'owner': table['table_owner'],
                        'comments': table.get('table_comments'),
                        'hash_value': table['hash_value'],
                        'has_error': table['has_error'],
                        'error_message': table.get('error_message'),
                        'created_at': table['created_at'],
                        'updated_at': table['updated_at']
                    }
                })
                
                # Component-Table 연결 (있는 경우)
                if table.get('component_id'):
                    relationships.append({
                        'type': 'REPRESENTS',
                        'from_id': f"component_{table['component_id']}",
                        'to_id': f"table_{table['table_id']}",
                        'properties': {}
                    })
            
            # 6. Column 노드 생성
            for column in data.get('columns', []):
                nodes.append({
                    'label': 'DatabaseColumn',
                    'id': f"column_{column['column_id']}",
                    'properties': {
                        'column_id': column['column_id'],
                        'name': column['column_name'],
                        'data_type': column.get('data_type'),
                        'data_length': column.get('data_length'),
                        'nullable': column.get('nullable'),
                        'comments': column.get('column_comments'),
                        'position_pk': column.get('position_pk'),
                        'data_default': column.get('data_default'),
                        'owner': column.get('owner'),
                        'hash_value': column['hash_value'],
                        'has_error': column['has_error'],
                        'error_message': column.get('error_message'),
                        'created_at': column['created_at'],
                        'updated_at': column['updated_at']
                    }
                })
                
                # Table-Column 관계 생성
                relationships.append({
                    'type': 'HAS_COLUMN',
                    'from_id': f"table_{column['table_id']}",
                    'to_id': f"column_{column['column_id']}",
                    'properties': {}
                })
                
                # Component-Column 연결 (있는 경우)
                if column.get('component_id'):
                    relationships.append({
                        'type': 'REPRESENTS',
                        'from_id': f"component_{column['component_id']}",
                        'to_id': f"column_{column['column_id']}",
                        'properties': {}
                    })
            
            # 7. Relationship 관계 생성
            rel_type_mapping = {
                'CALL_METHOD': 'CALLS',
                'CALL_QUERY': 'EXECUTES',
                'USE_TABLE': 'USES',
                'INHERITANCE': 'INHERITS',
                'JOIN_EXPLICIT': 'JOINS',
                'JOIN_IMPLICIT': 'IMPLICIT_JOINS',
                'FK': 'FOREIGN_KEY'
            }
            
            for rel in data.get('relationships', []):
                rel_type = rel_type_mapping.get(rel['rel_type'], rel['rel_type'])
                relationships.append({
                    'type': rel_type,
                    'from_id': f"component_{rel['src_id']}",
                    'to_id': f"component_{rel['dst_id']}",
                    'properties': {
                        'confidence': rel.get('confidence', 1.0),
                        'has_error': rel['has_error'],
                        'error_message': rel.get('error_message'),
                        'created_at': rel['created_at'],
                        'updated_at': rel['updated_at']
                    }
                })
            
            app_logger.info(f"그래프 모델 변환 완료: 노드 {len(nodes)}개, 관계 {len(relationships)}개")
            
            return {
                'nodes': nodes,
                'relationships': relationships
            }
            
        except Exception as e:
            handle_error(f"그래프 모델 변환 실패: {e}")
            return {'nodes': [], 'relationships': []}
    
    def create_neo4j_constraints(self):
        """Neo4j 제약조건 및 인덱스 생성"""
        constraints = [
            # 고유 제약조건
            "CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.project_id IS UNIQUE",
            "CREATE CONSTRAINT file_id_unique IF NOT EXISTS FOR (f:File) REQUIRE f.file_id IS UNIQUE",
            "CREATE CONSTRAINT class_id_unique IF NOT EXISTS FOR (c:Class) REQUIRE c.class_id IS UNIQUE",
            "CREATE CONSTRAINT component_id_unique IF NOT EXISTS FOR (c:Component) REQUIRE c.component_id IS UNIQUE",
            "CREATE CONSTRAINT method_id_unique IF NOT EXISTS FOR (m:Method) REQUIRE m.component_id IS UNIQUE",
            "CREATE CONSTRAINT sql_id_unique IF NOT EXISTS FOR (s:SQLQuery) REQUIRE s.component_id IS UNIQUE",
            "CREATE CONSTRAINT api_id_unique IF NOT EXISTS FOR (a:APIEndpoint) REQUIRE a.component_id IS UNIQUE",
            "CREATE CONSTRAINT table_id_unique IF NOT EXISTS FOR (t:Table) REQUIRE t.component_id IS UNIQUE",
            "CREATE CONSTRAINT db_table_id_unique IF NOT EXISTS FOR (t:DatabaseTable) REQUIRE t.table_id IS UNIQUE",
            "CREATE CONSTRAINT column_id_unique IF NOT EXISTS FOR (c:Column) REQUIRE c.component_id IS UNIQUE",
            "CREATE CONSTRAINT db_column_id_unique IF NOT EXISTS FOR (c:DatabaseColumn) REQUIRE c.column_id IS UNIQUE",
            
            # 인덱스 생성
            "CREATE INDEX project_name_idx IF NOT EXISTS FOR (p:Project) ON (p.name)",
            "CREATE INDEX file_name_idx IF NOT EXISTS FOR (f:File) ON (f.name)",
            "CREATE INDEX component_name_idx IF NOT EXISTS FOR (c:Component) ON (c.name)",
            "CREATE INDEX component_type_idx IF NOT EXISTS FOR (c:Component) ON (c.type)",
            "CREATE INDEX component_layer_idx IF NOT EXISTS FOR (c:Component) ON (c.layer)"
        ]
        
        try:
            with self.driver.session() as session:
                for constraint in constraints:
                    try:
                        session.run(constraint)
                        app_logger.debug(f"제약조건 생성: {constraint}")
                    except Exception as e:
                        app_logger.warning(f"제약조건 생성 실패 (무시): {constraint}, 오류: {e}")
                        
            app_logger.info("Neo4j 제약조건 및 인덱스 생성 완료")
            
        except Exception as e:
            handle_error(f"Neo4j 제약조건 생성 실패: {e}")
    
    def load_to_neo4j(self, graph_data: Dict[str, Any]) -> bool:
        """
        그래프 데이터를 Neo4j에 로드
        
        Args:
            graph_data: 변환된 그래프 데이터
            
        Returns:
            성공 여부
        """
        try:
            with self.driver.session() as session:
                # 기존 데이터 삭제 (선택사항)
                # session.run("MATCH (n) DETACH DELETE n")
                
                # 노드 생성
                for node in graph_data['nodes']:
                    properties_str = ", ".join([f"{k}: ${k}" for k in node['properties'].keys()])
                    cypher = f"CREATE (n:{node['label']} {{{properties_str}}})"
                    session.run(cypher, **node['properties'])
                
                app_logger.info(f"노드 {len(graph_data['nodes'])}개 생성 완료")
                
                # 관계 생성
                for rel in graph_data['relationships']:
                    properties_str = ""
                    if rel['properties']:
                        props = ", ".join([f"{k}: ${k}" for k in rel['properties'].keys()])
                        properties_str = f" {{{props}}}"
                    
                    cypher = f"""
                    MATCH (a), (b)
                    WHERE a.{self._get_id_property(rel['from_id'])} = $from_id
                      AND b.{self._get_id_property(rel['to_id'])} = $to_id
                    CREATE (a)-[r:{rel['type']}{properties_str}]->(b)
                    """
                    
                    params = {
                        'from_id': self._extract_id_value(rel['from_id']),
                        'to_id': self._extract_id_value(rel['to_id']),
                        **rel['properties']
                    }
                    
                    session.run(cypher, **params)
                
                app_logger.info(f"관계 {len(graph_data['relationships'])}개 생성 완료")
                
            return True
            
        except Exception as e:
            handle_error(f"Neo4j 데이터 로드 실패: {e}")
            return False
    
    def _get_id_property(self, node_id: str) -> str:
        """노드 ID에서 속성명 추출"""
        if node_id.startswith('project_'):
            return 'project_id'
        elif node_id.startswith('file_'):
            return 'file_id'
        elif node_id.startswith('class_'):
            return 'class_id'
        elif node_id.startswith('component_'):
            return 'component_id'
        elif node_id.startswith('table_'):
            return 'table_id'
        elif node_id.startswith('column_'):
            return 'column_id'
        else:
            return 'id'
    
    def _extract_id_value(self, node_id: str) -> int:
        """노드 ID에서 실제 ID 값 추출"""
        return int(node_id.split('_')[1])
    
    def migrate_project(self, project_name: str) -> bool:
        """
        프로젝트 전체 마이그레이션 실행
        
        Args:
            project_name: 마이그레이션할 프로젝트명
            
        Returns:
            성공 여부
        """
        try:
            app_logger.info(f"프로젝트 '{project_name}' 마이그레이션 시작")
            
            # 1. Neo4j 연결
            if not self.connect_neo4j():
                return False
            
            # 2. 제약조건 생성
            self.create_neo4j_constraints()
            
            # 3. SQLite 데이터 추출
            sqlite_data = self.extract_sqlite_data(project_name)
            if not sqlite_data:
                return False
            
            # 4. 그래프 모델로 변환
            graph_data = self.transform_to_graph_model(sqlite_data)
            if not graph_data['nodes']:
                return False
            
            # 5. Neo4j에 로드
            success = self.load_to_neo4j(graph_data)
            
            # 6. 연결 종료
            self.close_neo4j()
            
            if success:
                app_logger.info(f"프로젝트 '{project_name}' 마이그레이션 완료")
            
            return success
            
        except Exception as e:
            handle_error(f"프로젝트 마이그레이션 실패: {e}")
            return False


def main():
    """메인 실행 함수"""
    if len(sys.argv) < 2:
        print("사용법: python neo4j_migrator.py <project_name>")
        print("예: python neo4j_migrator.py sampleSrc")
        return
    
    project_name = sys.argv[1]
    
    # Neo4j 연결 정보 (필요시 수정)
    migrator = Neo4jMigrator(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j", 
        neo4j_password="password"
    )
    
    # 마이그레이션 실행
    success = migrator.migrate_project(project_name)
    
    if success:
        print(f"✅ 프로젝트 '{project_name}' 마이그레이션 성공")
        print("\nNeo4j Browser에서 확인:")
        print("http://localhost:7474")
        print("\n기본 쿼리 예시:")
        print("MATCH (n) RETURN count(n) as total_nodes")
        print("MATCH ()-[r]->() RETURN count(r) as total_relationships")
    else:
        print(f"❌ 프로젝트 '{project_name}' 마이그레이션 실패")


if __name__ == "__main__":
    main()
