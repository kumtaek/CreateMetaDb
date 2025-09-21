#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neo4j 연결 테스트 스크립트
"""

from neo4j import GraphDatabase
import sys

def test_neo4j_connection():
    """Neo4j 연결 테스트"""
    
    # 연결 정보 (비밀번호는 실제 설정한 값으로 변경)
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "neo4j"  # 실제 비밀번호로 변경하세요
    
    try:
        print("Neo4j 연결 시도 중...")
        print(f"URI: {uri}")
        print(f"Username: {username}")
        
        # 드라이버 생성
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # 연결 테스트
        with driver.session() as session:
            result = session.run("RETURN 'Hello Neo4j!' AS message")
            record = result.single()
            print(f"✅ 연결 성공! 메시지: {record['message']}")
            
            # Neo4j 버전 확인
            version_result = session.run("CALL dbms.components() YIELD name, versions")
            for record in version_result:
                print(f"✅ {record['name']}: {record['versions'][0]}")
            
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        print("\n문제 해결 방법:")
        print("1. Neo4j Desktop에서 데이터베이스가 실행 중인지 확인")
        print("2. 비밀번호가 올바른지 확인")
        print("3. 포트 7687이 사용 중인지 확인")
        return False

if __name__ == "__main__":
    success = test_neo4j_connection()
    if success:
        print("\n🎉 Neo4j 연결이 정상적으로 작동합니다!")
    else:
        print("\n💡 Neo4j Desktop 설정을 확인해주세요.")
        sys.exit(1)
