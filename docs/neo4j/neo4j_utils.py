"""
Neo4j 그래프 데이터베이스 연동 유틸리티 모듈

기능:
1. Neo4j 연결 관리
2. 그래프 쿼리 실행
3. 관계 탐색 및 분석
4. 기존 database_utils.py와 호환 인터페이스 제공
"""

from neo4j import GraphDatabase, Record
from typing import Dict, List, Any, Optional, Union
import json
from contextlib import contextmanager
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.logger import app_logger, handle_error


class Neo4jUtils:
    """Neo4j 데이터베이스 연동 유틸리티 클래스"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", password: str = "password"):
        """
        Neo4j 연결 초기화
        
        Args:
            uri: Neo4j 데이터베이스 URI
            user: 사용자명
            password: 비밀번호
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Neo4j 데이터베이스 연결"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # 연결 테스트
            with self.driver.session() as session:
                session.run("RETURN 1").single()
            app_logger.info("Neo4j 연결 성공")
        except Exception as e:
            handle_error(f"Neo4j 연결 실패: {e}")
            raise
    
    def close(self):
        """연결 종료"""
        if self.driver:
            self.driver.close()
            app_logger.info("Neo4j 연결 종료")
    
    @contextmanager
    def session(self):
        """Neo4j 세션 컨텍스트 매니저"""
        session = self.driver.session()
        try:
            yield session
        finally:
            session.close()
    
    def execute_query(self, cypher: str, parameters: Dict = None, 
                     fetch_all: bool = True) -> Union[List[Dict], Dict, None]:
        """
        Cypher 쿼리 실행
        
        Args:
            cypher: Cypher 쿼리문
            parameters: 쿼리 파라미터
            fetch_all: 모든 결과 반환 여부
            
        Returns:
            쿼리 결과
        """
        try:
            with self.session() as session:
                result = session.run(cypher, parameters or {})
                
                if fetch_all:
                    records = []
                    for record in result:
                        records.append(dict(record))
                    return records
                else:
                    record = result.single()
                    return dict(record) if record else None
                    
        except Exception as e:
            handle_error(f"Cypher 쿼리 실행 실패: {cypher}, 오류: {e}")
            return [] if fetch_all else None
    
    def get_project_info(self, project_name: str) -> Optional[Dict]:
        """
        프로젝트 정보 조회
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            프로젝트 정보 딕셔너리
        """
        cypher = """
        MATCH (p:Project {name: $project_name})
        RETURN p.project_id as project_id, p.name as project_name, 
               p.path as project_path, p.total_files as total_files,
               p.created_at as created_at, p.updated_at as updated_at
        """
        return self.execute_query(cypher, {'project_name': project_name}, fetch_all=False)
    
    def get_call_chain(self, project_name: str, limit: int = 100) -> List[Dict]:
        """
        호출 체인 조회 (JSP → API → METHOD → SQL → TABLE)
        
        Args:
            project_name: 프로젝트명
            limit: 결과 제한 수
            
        Returns:
            호출 체인 리스트
        """
        cypher = """
        MATCH (proj:Project {name: $project_name})
        MATCH (proj)-[:CONTAINS]->(jsp_file:File {type: 'jsp'})
        MATCH (jsp_file)-[:CONTAINS]->(api:APIEndpoint)
        MATCH (api)-[:CALLS]->(method:Method)
        OPTIONAL MATCH (method)-[:EXECUTES]->(sql:SQLQuery)
        OPTIONAL MATCH (sql)-[:USES]->(table:Table)
        OPTIONAL MATCH (method)-[:BELONGS_TO]->(class:Class)
        RETURN 
            jsp_file.name as jsp_file,
            api.name as api_url,
            class.name as class_name,
            method.name as method_name,
            sql.name as sql_name,
            sql.type as sql_type,
            collect(DISTINCT table.name) as related_tables
        LIMIT $limit
        """
        return self.execute_query(cypher, {'project_name': project_name, 'limit': limit})
    
    def get_component_relationships(self, component_name: str, 
                                  project_name: str = None) -> List[Dict]:
        """
        컴포넌트의 모든 관계 조회
        
        Args:
            component_name: 컴포넌트명
            project_name: 프로젝트명 (선택)
            
        Returns:
            관계 정보 리스트
        """
        where_clause = "WHERE c.name = $component_name"
        params = {'component_name': component_name}
        
        if project_name:
            where_clause += " AND proj.name = $project_name"
            params['project_name'] = project_name
        
        cypher = f"""
        MATCH (proj:Project)-[:CONTAINS*]->(c)
        {where_clause}
        MATCH (c)-[r]-(related)
        RETURN 
            c.name as component_name,
            c.type as component_type,
            type(r) as relationship_type,
            related.name as related_name,
            labels(related)[0] as related_type,
            r.confidence as confidence
        """
        return self.execute_query(cypher, params)
    
    def find_components_by_type(self, component_type: str, 
                              project_name: str = None) -> List[Dict]:
        """
        타입별 컴포넌트 검색
        
        Args:
            component_type: 컴포넌트 타입 (METHOD, API_URL, SQL_SELECT 등)
            project_name: 프로젝트명 (선택)
            
        Returns:
            컴포넌트 리스트
        """
        where_clause = "WHERE c.type = $component_type"
        params = {'component_type': component_type}
        
        if project_name:
            where_clause += " AND proj.name = $project_name"
            params['project_name'] = project_name
        
        cypher = f"""
        MATCH (proj:Project)-[:CONTAINS*]->(c)
        {where_clause}
        RETURN 
            c.component_id as component_id,
            c.name as component_name,
            c.type as component_type,
            c.layer as layer,
            c.line_start as line_start,
            c.line_end as line_end
        ORDER BY c.name
        """
        return self.execute_query(cypher, params)
    
    def get_table_usage(self, table_name: str, project_name: str = None) -> List[Dict]:
        """
        테이블 사용 현황 조회
        
        Args:
            table_name: 테이블명
            project_name: 프로젝트명 (선택)
            
        Returns:
            테이블 사용 정보 리스트
        """
        where_clause = "WHERE t.name = $table_name"
        params = {'table_name': table_name}
        
        if project_name:
            where_clause += " AND proj.name = $project_name"
            params['project_name'] = project_name
        
        cypher = f"""
        MATCH (proj:Project)-[:CONTAINS*]->(t)
        {where_clause}
        MATCH (sql)-[:USES]->(t)
        OPTIONAL MATCH (method)-[:EXECUTES]->(sql)
        OPTIONAL MATCH (api)-[:CALLS]->(method)
        RETURN 
            t.name as table_name,
            sql.name as sql_name,
            sql.type as sql_type,
            method.name as method_name,
            api.name as api_url
        """
        return self.execute_query(cypher, params)
    
    def find_broken_chains(self, project_name: str) -> List[Dict]:
        """
        끊어진 호출 체인 탐지
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            끊어진 체인 정보 리스트
        """
        cypher = """
        MATCH (proj:Project {name: $project_name})
        MATCH (proj)-[:CONTAINS*]->(api:APIEndpoint)
        WHERE NOT (api)-[:CALLS]->(:Method)
        RETURN 
            api.name as broken_api,
            'API without METHOD' as issue_type
        
        UNION
        
        MATCH (proj:Project {name: $project_name})
        MATCH (proj)-[:CONTAINS*]->(method:Method)
        WHERE NOT (method)-[:EXECUTES]->(:SQLQuery)
          AND method.layer IN ['REPOSITORY', 'DAO']
        RETURN 
            method.name as broken_api,
            'DAO METHOD without SQL' as issue_type
        """
        return self.execute_query(cypher, {'project_name': project_name})
    
    def get_architecture_layers(self, project_name: str) -> List[Dict]:
        """
        아키텍처 레이어별 통계
        
        Args:
            project_name: 프로젝트명
            
        Returns:
            레이어별 통계 정보
        """
        cypher = """
        MATCH (proj:Project {name: $project_name})
        MATCH (proj)-[:CONTAINS*]->(c)
        WHERE c.layer IS NOT NULL
        RETURN 
            c.layer as layer,
            count(c) as component_count,
            collect(DISTINCT c.type) as component_types
        ORDER BY component_count DESC
        """
        return self.execute_query(cypher, {'project_name': project_name})
    
    def get_shortest_path(self, from_component: str, to_component: str,
                         project_name: str = None) -> List[Dict]:
        """
        두 컴포넌트 간 최단 경로 탐색
        
        Args:
            from_component: 시작 컴포넌트명
            to_component: 대상 컴포넌트명
            project_name: 프로젝트명 (선택)
            
        Returns:
            최단 경로 정보
        """
        where_clause = ""
        params = {
            'from_component': from_component,
            'to_component': to_component
        }
        
        if project_name:
            where_clause = "AND proj.name = $project_name"
            params['project_name'] = project_name
        
        cypher = f"""
        MATCH (proj:Project)-[:CONTAINS*]->(from_comp)
        MATCH (proj)-[:CONTAINS*]->(to_comp)
        WHERE from_comp.name = $from_component 
          AND to_comp.name = $to_component
          {where_clause}
        MATCH path = shortestPath((from_comp)-[*]-(to_comp))
        RETURN 
            [node in nodes(path) | {{name: node.name, type: labels(node)[0]}}] as path_nodes,
            [rel in relationships(path) | type(rel)] as relationship_types,
            length(path) as path_length
        """
        return self.execute_query(cypher, params)
    
    def analyze_component_impact(self, component_name: str, 
                               project_name: str = None) -> Dict[str, Any]:
        """
        컴포넌트 영향도 분석
        
        Args:
            component_name: 컴포넌트명
            project_name: 프로젝트명 (선택)
            
        Returns:
            영향도 분석 결과
        """
        where_clause = ""
        params = {'component_name': component_name}
        
        if project_name:
            where_clause = "AND proj.name = $project_name"
            params['project_name'] = project_name
        
        # 직접 의존하는 컴포넌트 수
        direct_deps_cypher = f"""
        MATCH (proj:Project)-[:CONTAINS*]->(c)
        WHERE c.name = $component_name {where_clause}
        MATCH (c)<-[r]-(dependent)
        RETURN count(DISTINCT dependent) as direct_dependents
        """
        
        # 간접 의존하는 컴포넌트 수
        indirect_deps_cypher = f"""
        MATCH (proj:Project)-[:CONTAINS*]->(c)
        WHERE c.name = $component_name {where_clause}
        MATCH (c)<-[*1..3]-(dependent)
        RETURN count(DISTINCT dependent) as indirect_dependents
        """
        
        # 직접 사용하는 컴포넌트 수
        direct_uses_cypher = f"""
        MATCH (proj:Project)-[:CONTAINS*]->(c)
        WHERE c.name = $component_name {where_clause}
        MATCH (c)-[r]->(used)
        RETURN count(DISTINCT used) as direct_uses
        """
        
        direct_deps = self.execute_query(direct_deps_cypher, params, fetch_all=False)
        indirect_deps = self.execute_query(indirect_deps_cypher, params, fetch_all=False)
        direct_uses = self.execute_query(direct_uses_cypher, params, fetch_all=False)
        
        return {
            'component_name': component_name,
            'direct_dependents': direct_deps.get('direct_dependents', 0) if direct_deps else 0,
            'indirect_dependents': indirect_deps.get('indirect_dependents', 0) if indirect_deps else 0,
            'direct_uses': direct_uses.get('direct_uses', 0) if direct_uses else 0,
            'impact_score': (direct_deps.get('direct_dependents', 0) if direct_deps else 0) * 2 + 
                          (indirect_deps.get('indirect_dependents', 0) if indirect_deps else 0)
        }
    
    def export_graph_data(self, project_name: str, output_file: str = None) -> Dict[str, Any]:
        """
        그래프 데이터 내보내기 (시각화용)
        
        Args:
            project_name: 프로젝트명
            output_file: 출력 파일 경로 (선택)
            
        Returns:
            그래프 데이터 (nodes, edges)
        """
        # 노드 조회
        nodes_cypher = """
        MATCH (proj:Project {name: $project_name})
        MATCH (proj)-[:CONTAINS*]->(node)
        RETURN 
            node.component_id as id,
            node.name as name,
            labels(node)[0] as label,
            node.type as type,
            node.layer as layer
        """
        
        # 엣지 조회
        edges_cypher = """
        MATCH (proj:Project {name: $project_name})
        MATCH (proj)-[:CONTAINS*]->(source)
        MATCH (source)-[rel]->(target)
        WHERE (proj)-[:CONTAINS*]->(target)
        RETURN 
            source.component_id as source,
            target.component_id as target,
            type(rel) as relationship,
            rel.confidence as confidence
        """
        
        nodes = self.execute_query(nodes_cypher, {'project_name': project_name})
        edges = self.execute_query(edges_cypher, {'project_name': project_name})
        
        graph_data = {
            'nodes': nodes,
            'edges': edges,
            'project_name': project_name,
            'exported_at': str(datetime.now())
        }
        
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(graph_data, f, ensure_ascii=False, indent=2)
                app_logger.info(f"그래프 데이터를 {output_file}에 저장")
            except Exception as e:
                handle_error(f"그래프 데이터 저장 실패: {e}")
        
        return graph_data


# 기존 database_utils.py와 호환성을 위한 래퍼 클래스
class Neo4jDatabaseUtils:
    """기존 DatabaseUtils와 호환되는 Neo4j 래퍼 클래스"""
    
    def __init__(self):
        self.neo4j = Neo4jUtils()
    
    def get_project_id_by_name(self, project_name: str) -> Optional[int]:
        """프로젝트 ID 조회"""
        project = self.neo4j.get_project_info(project_name)
        return project.get('project_id') if project else None
    
    def get_call_chain_data(self, project_name: str) -> List[Dict]:
        """호출 체인 데이터 조회"""
        return self.neo4j.get_call_chain(project_name)
    
    def get_components_by_type(self, project_name: str, component_type: str) -> List[Dict]:
        """타입별 컴포넌트 조회"""
        return self.neo4j.find_components_by_type(component_type, project_name)
    
    def close(self):
        """연결 종료"""
        self.neo4j.close()


if __name__ == "__main__":
    # 테스트 코드
    neo4j = Neo4jUtils()
    
    try:
        # 프로젝트 정보 조회
        project_info = neo4j.get_project_info("sampleSrc")
        print(f"프로젝트 정보: {project_info}")
        
        # 호출 체인 조회
        call_chains = neo4j.get_call_chain("sampleSrc", limit=5)
        print(f"호출 체인 수: {len(call_chains)}")
        
        # 아키텍처 레이어 분석
        layers = neo4j.get_architecture_layers("sampleSrc")
        print(f"아키텍처 레이어: {layers}")
        
    finally:
        neo4j.close()
