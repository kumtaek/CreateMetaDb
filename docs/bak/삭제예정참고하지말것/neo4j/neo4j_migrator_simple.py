"""
간단한 Neo4j 마이그레이션 스크립트 (Docker 없이)

사용법:
1. pip install neo4j pandas
2. Neo4j Desktop 설치 및 데이터베이스 생성
3. python neo4j_migrator_simple.py sampleSrc
"""

import sys
import os
from neo4j import GraphDatabase, exceptions
import time

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from util.database_utils import DatabaseUtils
    from util.logger import app_logger, handle_error
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    print("현재 디렉토리가 프로젝트 루트인지 확인하세요.")
    sys.exit(1)


def check_neo4j_connection(uri="bolt://localhost:7687", user="neo4j", password="password123", max_retries=3):
    """Neo4j 연결 확인"""
    print("🔍 Neo4j 연결 확인 중...")
    
    for i in range(max_retries):
        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            with driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            driver.close()
            print("✅ Neo4j 연결 성공")
            return True
        except exceptions.ServiceUnavailable:
            print(f"⏳ 연결 시도 {i+1}/{max_retries}: Neo4j 서버에 연결할 수 없습니다.")
            if i < max_retries - 1:
                print("   5초 후 재시도...")
                time.sleep(5)
        except exceptions.AuthError:
            print("❌ 인증 실패: 사용자명/비밀번호를 확인하세요.")
            return False
        except Exception as e:
            print(f"❌ 연결 오류: {e}")
            return False
    
    print("\n❌ Neo4j 연결 실패")
    print("다음을 확인하세요:")
    print("1. Neo4j Desktop이 실행 중인가요?")
    print("2. 데이터베이스가 시작되었나요?")
    print("3. 비밀번호가 'password123'인가요?")
    print("4. Neo4j Browser(http://localhost:7474)에 접속되나요?")
    return False


def get_sqlite_data(project_name):
    """SQLite에서 데이터 추출"""
    print(f"📊 프로젝트 '{project_name}' 데이터 추출 중...")
    
    try:
        db_utils = DatabaseUtils()
        project_id = db_utils.get_project_id_by_name(project_name)
        
        if not project_id:
            print(f"❌ 프로젝트 '{project_name}'을 찾을 수 없습니다.")
            
            # 사용 가능한 프로젝트 목록 표시
            projects = db_utils.get_all_projects()
            if projects:
                print("\n사용 가능한 프로젝트:")
                for project in projects:
                    print(f"  - {project['project_name']}")
            return None
        
        # 간단한 통계만 추출
        stats = {}
        tables = ['files', 'classes', 'components', 'relationships']
        
        for table in tables:
            query = f"SELECT COUNT(*) as count FROM {table} WHERE project_id = ? AND del_yn = 'N'"
            result = db_utils.execute_query(query, (project_id,), fetch_all=False)
            stats[table] = result['count'] if result else 0
        
        print(f"✅ 데이터 추출 완료:")
        for table, count in stats.items():
            print(f"   - {table}: {count}개")
        
        return {'project_id': project_id, 'stats': stats}
        
    except Exception as e:
        print(f"❌ 데이터 추출 실패: {e}")
        return None


def simple_migration(project_name):
    """간단한 마이그레이션 실행"""
    print(f"\n🚀 '{project_name}' 마이그레이션 시작")
    print("=" * 50)
    
    # 1. Neo4j 연결 확인
    if not check_neo4j_connection():
        return False
    
    # 2. SQLite 데이터 확인
    sqlite_data = get_sqlite_data(project_name)
    if not sqlite_data:
        return False
    
    # 3. 실제 마이그레이션은 기존 스크립트 사용
    print("\n🔄 전체 마이그레이션 실행 중...")
    print("이 과정은 몇 분 소요될 수 있습니다...")
    
    try:
        # 기존 마이그레이션 스크립트 import 및 실행
        from neo4j_migrator import Neo4jMigrator
        
        migrator = Neo4jMigrator(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password123"
        )
        
        success = migrator.migrate_project(project_name)
        
        if success:
            print("\n✅ 마이그레이션 성공!")
            print("\n📌 확인 방법:")
            print("1. Neo4j Browser: http://localhost:7474")
            print("2. 로그인: neo4j / password123")
            print("3. 쿼리 실행:")
            print("   MATCH (n) RETURN count(n) as total_nodes")
            print("   MATCH ()-[r]->() RETURN count(r) as total_relationships")
        else:
            print("\n❌ 마이그레이션 실패")
            print("로그를 확인하세요: ./logs/app.log")
        
        return success
        
    except ImportError:
        print("❌ 마이그레이션 모듈을 찾을 수 없습니다.")
        print("neo4j_migrator.py 파일이 ./temp/ 디렉토리에 있는지 확인하세요.")
        return False
    except Exception as e:
        print(f"❌ 마이그레이션 실행 오류: {e}")
        return False


def main():
    """메인 함수"""
    print("🔧 Neo4j 간단 마이그레이션 도구")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("사용법: python neo4j_migrator_simple.py <project_name>")
        print("예: python neo4j_migrator_simple.py sampleSrc")
        return
    
    project_name = sys.argv[1]
    
    # 전제조건 확인
    print("📋 전제조건 확인:")
    print("1. ✅ pip install neo4j pandas 완료")
    print("2. ⏳ Neo4j Desktop 설치 및 데이터베이스 시작 확인 중...")
    
    success = simple_migration(project_name)
    
    if success:
        print("\n🎉 모든 작업이 완료되었습니다!")
        print("\nNeo4j Browser에서 다음 쿼리로 결과를 확인하세요:")
        print(f"MATCH (p:Project {{name: '{project_name}'}}) RETURN p")
    else:
        print("\n💡 문제 해결 방법:")
        print("1. Neo4j Desktop에서 데이터베이스가 시작되었는지 확인")
        print("2. http://localhost:7474 접속 테스트")
        print("3. 비밀번호가 'password123'인지 확인")
        print("4. 로그 파일 확인: ./logs/app.log")


if __name__ == "__main__":
    main()
