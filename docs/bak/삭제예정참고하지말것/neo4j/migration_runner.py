"""
Neo4j 마이그레이션 실행 및 검증 스크립트

기능:
1. 마이그레이션 실행
2. 데이터 검증
3. 성능 비교
4. 롤백 지원
"""

import sys
import os
import time
import json
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j_migrator import Neo4jMigrator
from neo4j_utils import Neo4jUtils, Neo4jDatabaseUtils
from util.database_utils import DatabaseUtils
from util.logger import app_logger, handle_error


class MigrationRunner:
    """마이그레이션 실행 및 검증 클래스"""
    
    def __init__(self):
        self.sqlite_utils = DatabaseUtils()
        self.neo4j_migrator = Neo4jMigrator()
        self.neo4j_utils = None
        self.migration_log = []
    
    def log_migration_step(self, step: str, status: str, details: str = None):
        """마이그레이션 단계 로그 기록"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'status': status,
            'details': details
        }
        self.migration_log.append(log_entry)
        
        status_icon = "✅" if status == "SUCCESS" else "❌" if status == "FAILED" else "⏳"
        print(f"{status_icon} [{datetime.now().strftime('%H:%M:%S')}] {step}: {status}")
        if details:
            print(f"   └─ {details}")
    
    def check_prerequisites(self) -> bool:
        """마이그레이션 전제조건 확인"""
        self.log_migration_step("전제조건 확인", "RUNNING")
        
        try:
            # Neo4j 연결 확인
            if not self.neo4j_migrator.connect_neo4j():
                self.log_migration_step("Neo4j 연결 확인", "FAILED", "Neo4j 서버에 연결할 수 없습니다")
                return False
            self.neo4j_migrator.close_neo4j()
            
            # SQLite 데이터베이스 확인
            projects = self.sqlite_utils.get_all_projects()
            if not projects:
                self.log_migration_step("SQLite 데이터 확인", "FAILED", "마이그레이션할 프로젝트가 없습니다")
                return False
            
            self.log_migration_step("전제조건 확인", "SUCCESS", f"{len(projects)}개 프로젝트 발견")
            return True
            
        except Exception as e:
            self.log_migration_step("전제조건 확인", "FAILED", str(e))
            return False
    
    def backup_neo4j_data(self) -> bool:
        """Neo4j 데이터 백업"""
        self.log_migration_step("Neo4j 데이터 백업", "RUNNING")
        
        try:
            backup_file = f"./temp/neo4j_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Neo4j에서 기존 데이터 추출
            neo4j = Neo4jUtils()
            try:
                with neo4j.session() as session:
                    # 모든 노드 조회
                    nodes_result = session.run("MATCH (n) RETURN n")
                    nodes = [dict(record['n']) for record in nodes_result]
                    
                    # 모든 관계 조회
                    rels_result = session.run("MATCH ()-[r]->() RETURN r")
                    relationships = [dict(record['r']) for record in rels_result]
                
                backup_data = {
                    'backup_time': datetime.now().isoformat(),
                    'nodes_count': len(nodes),
                    'relationships_count': len(relationships),
                    'nodes': nodes,
                    'relationships': relationships
                }
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                
                self.log_migration_step("Neo4j 데이터 백업", "SUCCESS", 
                                      f"백업 파일: {backup_file} (노드: {len(nodes)}, 관계: {len(relationships)})")
                return True
                
            finally:
                neo4j.close()
                
        except Exception as e:
            self.log_migration_step("Neo4j 데이터 백업", "FAILED", str(e))
            return False
    
    def migrate_project(self, project_name: str) -> bool:
        """프로젝트 마이그레이션 실행"""
        self.log_migration_step(f"프로젝트 '{project_name}' 마이그레이션", "RUNNING")
        
        start_time = time.time()
        
        try:
            success = self.neo4j_migrator.migrate_project(project_name)
            
            elapsed_time = time.time() - start_time
            
            if success:
                self.log_migration_step(f"프로젝트 '{project_name}' 마이그레이션", "SUCCESS", 
                                      f"소요시간: {elapsed_time:.2f}초")
            else:
                self.log_migration_step(f"프로젝트 '{project_name}' 마이그레이션", "FAILED", 
                                      f"소요시간: {elapsed_time:.2f}초")
            
            return success
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.log_migration_step(f"프로젝트 '{project_name}' 마이그레이션", "FAILED", 
                                  f"오류: {e}, 소요시간: {elapsed_time:.2f}초")
            return False
    
    def verify_migration(self, project_name: str) -> bool:
        """마이그레이션 결과 검증"""
        self.log_migration_step(f"프로젝트 '{project_name}' 검증", "RUNNING")
        
        try:
            # SQLite 데이터 카운트
            sqlite_counts = self.get_sqlite_counts(project_name)
            
            # Neo4j 데이터 카운트
            neo4j_counts = self.get_neo4j_counts(project_name)
            
            # 데이터 무결성 검증
            verification_results = []
            
            for table, sqlite_count in sqlite_counts.items():
                neo4j_count = neo4j_counts.get(table, 0)
                match_status = "✅" if sqlite_count == neo4j_count else "❌"
                
                verification_results.append({
                    'table': table,
                    'sqlite_count': sqlite_count,
                    'neo4j_count': neo4j_count,
                    'match': sqlite_count == neo4j_count
                })
                
                print(f"   {match_status} {table}: SQLite({sqlite_count}) vs Neo4j({neo4j_count})")
            
            # 전체 검증 결과
            all_match = all(result['match'] for result in verification_results)
            
            if all_match:
                self.log_migration_step(f"프로젝트 '{project_name}' 검증", "SUCCESS", 
                                      "모든 데이터가 정확히 마이그레이션됨")
            else:
                failed_tables = [r['table'] for r in verification_results if not r['match']]
                self.log_migration_step(f"프로젝트 '{project_name}' 검증", "FAILED", 
                                      f"불일치 테이블: {', '.join(failed_tables)}")
            
            return all_match
            
        except Exception as e:
            self.log_migration_step(f"프로젝트 '{project_name}' 검증", "FAILED", str(e))
            return False
    
    def get_sqlite_counts(self, project_name: str) -> Dict[str, int]:
        """SQLite 테이블별 레코드 수 조회"""
        project_id = self.sqlite_utils.get_project_id_by_name(project_name)
        if not project_id:
            return {}
        
        counts = {}
        tables = ['files', 'classes', 'components', 'tables', 'columns', 'relationships']
        
        for table in tables:
            query = f"SELECT COUNT(*) as count FROM {table} WHERE project_id = ? AND del_yn = 'N'"
            result = self.sqlite_utils.execute_query(query, (project_id,), fetch_all=False)
            counts[table] = result['count'] if result else 0
        
        return counts
    
    def get_neo4j_counts(self, project_name: str) -> Dict[str, int]:
        """Neo4j 노드/관계별 레코드 수 조회"""
        if not self.neo4j_utils:
            self.neo4j_utils = Neo4jUtils()
        
        counts = {}
        
        try:
            # 파일 노드 수
            result = self.neo4j_utils.execute_query(
                "MATCH (p:Project {name: $project_name})-[:CONTAINS]->(f:File) RETURN count(f) as count",
                {'project_name': project_name}, fetch_all=False
            )
            counts['files'] = result['count'] if result else 0
            
            # 클래스 노드 수
            result = self.neo4j_utils.execute_query(
                "MATCH (p:Project {name: $project_name})-[:CONTAINS*]->(c:Class) RETURN count(c) as count",
                {'project_name': project_name}, fetch_all=False
            )
            counts['classes'] = result['count'] if result else 0
            
            # 컴포넌트 노드 수 (Method, SQLQuery, APIEndpoint, Table, Column)
            result = self.neo4j_utils.execute_query(
                """MATCH (p:Project {name: $project_name})-[:CONTAINS*]->(c)
                   WHERE c:Method OR c:SQLQuery OR c:APIEndpoint OR c:Table OR c:Column OR c:Component
                   RETURN count(c) as count""",
                {'project_name': project_name}, fetch_all=False
            )
            counts['components'] = result['count'] if result else 0
            
            # 데이터베이스 테이블 노드 수
            result = self.neo4j_utils.execute_query(
                "MATCH (p:Project {name: $project_name})-[:CONTAINS*]->(t:DatabaseTable) RETURN count(t) as count",
                {'project_name': project_name}, fetch_all=False
            )
            counts['tables'] = result['count'] if result else 0
            
            # 데이터베이스 컬럼 노드 수
            result = self.neo4j_utils.execute_query(
                "MATCH (p:Project {name: $project_name})-[:CONTAINS*]->(c:DatabaseColumn) RETURN count(c) as count",
                {'project_name': project_name}, fetch_all=False
            )
            counts['columns'] = result['count'] if result else 0
            
            # 관계 수 (CALLS, EXECUTES, USES 등)
            result = self.neo4j_utils.execute_query(
                """MATCH (p:Project {name: $project_name})-[:CONTAINS*]->(source)
                   MATCH (source)-[r]->(target)
                   WHERE (p)-[:CONTAINS*]->(target)
                     AND type(r) IN ['CALLS', 'EXECUTES', 'USES', 'INHERITS', 'JOINS', 'IMPLICIT_JOINS', 'FOREIGN_KEY']
                   RETURN count(r) as count""",
                {'project_name': project_name}, fetch_all=False
            )
            counts['relationships'] = result['count'] if result else 0
            
        except Exception as e:
            handle_error(f"Neo4j 카운트 조회 실패: {e}")
        
        return counts
    
    def performance_comparison(self, project_name: str) -> Dict[str, Any]:
        """성능 비교 테스트"""
        self.log_migration_step("성능 비교 테스트", "RUNNING")
        
        results = {
            'sqlite': {},
            'neo4j': {},
            'comparison': {}
        }
        
        try:
            # 1. 호출 체인 조회 성능 비교
            # SQLite
            start_time = time.time()
            sqlite_chains = self.get_sqlite_call_chains(project_name)
            sqlite_time = time.time() - start_time
            results['sqlite']['call_chain'] = {
                'time': sqlite_time,
                'count': len(sqlite_chains)
            }
            
            # Neo4j
            if not self.neo4j_utils:
                self.neo4j_utils = Neo4jUtils()
            
            start_time = time.time()
            neo4j_chains = self.neo4j_utils.get_call_chain(project_name)
            neo4j_time = time.time() - start_time
            results['neo4j']['call_chain'] = {
                'time': neo4j_time,
                'count': len(neo4j_chains)
            }
            
            # 성능 비교
            speedup = sqlite_time / neo4j_time if neo4j_time > 0 else 0
            results['comparison']['call_chain'] = {
                'speedup': speedup,
                'faster': 'Neo4j' if speedup > 1 else 'SQLite'
            }
            
            # 2. 컴포넌트 관계 조회 성능 비교
            if sqlite_chains and neo4j_chains:
                # 첫 번째 메서드로 테스트
                test_method = None
                for chain in sqlite_chains:
                    if chain.get('method_name'):
                        test_method = chain['method_name']
                        break
                
                if test_method:
                    # SQLite
                    start_time = time.time()
                    sqlite_rels = self.get_sqlite_component_relationships(test_method, project_name)
                    sqlite_rel_time = time.time() - start_time
                    results['sqlite']['relationships'] = {
                        'time': sqlite_rel_time,
                        'count': len(sqlite_rels)
                    }
                    
                    # Neo4j
                    start_time = time.time()
                    neo4j_rels = self.neo4j_utils.get_component_relationships(test_method, project_name)
                    neo4j_rel_time = time.time() - start_time
                    results['neo4j']['relationships'] = {
                        'time': neo4j_rel_time,
                        'count': len(neo4j_rels)
                    }
                    
                    # 성능 비교
                    rel_speedup = sqlite_rel_time / neo4j_rel_time if neo4j_rel_time > 0 else 0
                    results['comparison']['relationships'] = {
                        'speedup': rel_speedup,
                        'faster': 'Neo4j' if rel_speedup > 1 else 'SQLite'
                    }
            
            # 결과 출력
            print("\n📊 성능 비교 결과:")
            print(f"   호출 체인 조회: SQLite({sqlite_time:.3f}s) vs Neo4j({neo4j_time:.3f}s) - {results['comparison']['call_chain']['faster']} 승리 (x{results['comparison']['call_chain']['speedup']:.2f})")
            
            if 'relationships' in results['comparison']:
                rel_comp = results['comparison']['relationships']
                sqlite_rel_time = results['sqlite']['relationships']['time']
                neo4j_rel_time = results['neo4j']['relationships']['time']
                print(f"   관계 조회: SQLite({sqlite_rel_time:.3f}s) vs Neo4j({neo4j_rel_time:.3f}s) - {rel_comp['faster']} 승리 (x{rel_comp['speedup']:.2f})")
            
            self.log_migration_step("성능 비교 테스트", "SUCCESS", "성능 비교 완료")
            
        except Exception as e:
            self.log_migration_step("성능 비교 테스트", "FAILED", str(e))
        
        return results
    
    def get_sqlite_call_chains(self, project_name: str) -> List[Dict]:
        """SQLite에서 호출 체인 조회 (기존 방식)"""
        project_id = self.sqlite_utils.get_project_id_by_name(project_name)
        if not project_id:
            return []
        
        query = """
        SELECT 
            ROW_NUMBER() OVER (ORDER BY jsp_file.file_name, api_url.component_name) as chain_id,
            jsp_file.file_name as jsp_file,
            api_url.component_name as api_url,
            class.class_name as class_name,
            method.component_name as method_name,
            xml_file.file_name as xml_file,
            sql.component_name as sql_name,
            sql.component_type as sql_type,
            GROUP_CONCAT(DISTINCT table.table_name) as related_tables
        FROM files jsp_file
        JOIN components api_url ON jsp_file.file_id = api_url.file_id
        JOIN relationships r1 ON api_url.component_id = r1.src_id
        JOIN components method ON r1.dst_id = method.component_id
        JOIN classes class ON method.parent_id = class.class_id
        JOIN relationships r2 ON method.component_id = r2.src_id
        JOIN components sql ON r2.dst_id = sql.component_id
        JOIN files xml_file ON sql.file_id = xml_file.file_id
        LEFT JOIN relationships r3 ON sql.component_id = r3.src_id
        LEFT JOIN tables table ON r3.dst_id = table.component_id
        WHERE api_url.component_type = 'API_URL'
          AND r1.rel_type = 'CALL_METHOD'
          AND method.component_type = 'METHOD'
          AND r2.rel_type = 'CALL_QUERY'
          AND sql.component_type LIKE 'SQL_%'
          AND (r3.rel_type = 'USE_TABLE' OR r3.rel_type IS NULL)
          AND jsp_file.project_id = ?
        GROUP BY jsp_file.file_name, api_url.component_name, class.class_name, 
                 method.component_name, xml_file.file_name, sql.component_name, sql.component_type
        """
        
        return self.sqlite_utils.execute_query(query, (project_id,), fetch_all=True)
    
    def get_sqlite_component_relationships(self, component_name: str, project_name: str) -> List[Dict]:
        """SQLite에서 컴포넌트 관계 조회"""
        project_id = self.sqlite_utils.get_project_id_by_name(project_name)
        if not project_id:
            return []
        
        query = """
        SELECT 
            c1.component_name as component_name,
            c1.component_type as component_type,
            r.rel_type as relationship_type,
            c2.component_name as related_name,
            c2.component_type as related_type,
            r.confidence as confidence
        FROM components c1
        JOIN relationships r ON c1.component_id = r.src_id OR c1.component_id = r.dst_id
        JOIN components c2 ON (r.src_id = c2.component_id AND c1.component_id = r.dst_id) 
                           OR (r.dst_id = c2.component_id AND c1.component_id = r.src_id)
        WHERE c1.component_name = ? AND c1.project_id = ?
        """
        
        return self.sqlite_utils.execute_query(query, (component_name, project_id), fetch_all=True)
    
    def save_migration_report(self, project_name: str, results: Dict[str, Any]):
        """마이그레이션 리포트 저장"""
        report_file = f"./temp/migration_report_{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            'project_name': project_name,
            'migration_time': datetime.now().isoformat(),
            'migration_log': self.migration_log,
            'performance_results': results,
            'summary': {
                'total_steps': len(self.migration_log),
                'successful_steps': len([log for log in self.migration_log if log['status'] == 'SUCCESS']),
                'failed_steps': len([log for log in self.migration_log if log['status'] == 'FAILED'])
            }
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n📋 마이그레이션 리포트 저장: {report_file}")
            
        except Exception as e:
            handle_error(f"마이그레이션 리포트 저장 실패: {e}")
    
    def run_full_migration(self, project_name: str) -> bool:
        """전체 마이그레이션 프로세스 실행"""
        print(f"🚀 Neo4j 마이그레이션 시작: {project_name}")
        print("=" * 60)
        
        # 1. 전제조건 확인
        if not self.check_prerequisites():
            return False
        
        # 2. 백업
        if not self.backup_neo4j_data():
            return False
        
        # 3. 마이그레이션 실행
        if not self.migrate_project(project_name):
            return False
        
        # 4. 검증
        if not self.verify_migration(project_name):
            return False
        
        # 5. 성능 비교
        performance_results = self.performance_comparison(project_name)
        
        # 6. 리포트 저장
        self.save_migration_report(project_name, performance_results)
        
        print("\n" + "=" * 60)
        print("🎉 마이그레이션 완료!")
        
        return True
    
    def cleanup(self):
        """리소스 정리"""
        if self.neo4j_utils:
            self.neo4j_utils.close()


def main():
    """메인 실행 함수"""
    if len(sys.argv) < 2:
        print("사용법: python migration_runner.py <project_name>")
        print("예: python migration_runner.py sampleSrc")
        return
    
    project_name = sys.argv[1]
    runner = MigrationRunner()
    
    try:
        success = runner.run_full_migration(project_name)
        exit_code = 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  마이그레이션이 사용자에 의해 중단되었습니다.")
        exit_code = 2
    except Exception as e:
        print(f"\n\n💥 예기치 않은 오류 발생: {e}")
        exit_code = 3
    finally:
        runner.cleanup()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
