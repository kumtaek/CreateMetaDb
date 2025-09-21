# Neo4j 마이그레이션 실행 가이드

## 1. 환경 설정

### 1.1. Neo4j 설치

#### Option A: Docker 사용 (권장)
```bash
# Neo4j Docker 컨테이너 실행
docker run -d \
    --name neo4j-analyzer \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password123 \
    -v neo4j_data:/data \
    -v neo4j_logs:/logs \
    neo4j:latest

# 컨테이너 상태 확인
docker ps | grep neo4j
```

#### Option B: Neo4j Desktop 설치
1. https://neo4j.com/download/ 에서 Neo4j Desktop 다운로드
2. 새 프로젝트 생성
3. 데이터베이스 생성 (이름: analyzer-db)
4. 비밀번호 설정: password123

#### Option C: Community Edition 설치
```bash
# Ubuntu/Debian
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable 4.4' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j

# 서비스 시작
sudo systemctl start neo4j
sudo systemctl enable neo4j
```

### 1.2. Python 패키지 설치

```bash
# Neo4j Python 드라이버 설치
pip install neo4j

# 추가 패키지 (이미 설치되어 있을 수 있음)
pip install pandas
```

### 1.3. 연결 확인

```bash
# Neo4j Browser 접속
http://localhost:7474

# 기본 로그인 정보
사용자명: neo4j
비밀번호: password123 (또는 설정한 비밀번호)
```

## 2. 마이그레이션 실행

### 2.1. 기본 마이그레이션

```bash
# 현재 프로젝트 디렉토리에서 실행
cd D:\Analyzer\CreateMetaDb

# 마이그레이션 실행 (sampleSrc 프로젝트)
python ./temp/migration_runner.py sampleSrc
```

### 2.2. 단계별 실행

```bash
# 1. 전제조건만 확인
python ./temp/neo4j_migrator.py --check-only sampleSrc

# 2. 데이터 추출만 실행
python ./temp/neo4j_migrator.py --extract-only sampleSrc

# 3. 변환 및 로드 실행
python ./temp/neo4j_migrator.py --load-only sampleSrc
```

### 2.3. 연결 정보 커스터마이징

Neo4j 연결 정보를 환경변수로 설정:

```bash
# Windows
set NEO4J_URI=bolt://localhost:7687
set NEO4J_USER=neo4j
set NEO4J_PASSWORD=your_password

# Linux/Mac
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your_password

# 마이그레이션 실행
python ./temp/migration_runner.py sampleSrc
```

## 3. 마이그레이션 검증

### 3.1. Neo4j Browser에서 확인

```cypher
// 전체 노드 수 확인
MATCH (n) RETURN count(n) as total_nodes

// 전체 관계 수 확인
MATCH ()-[r]->() RETURN count(r) as total_relationships

// 프로젝트별 통계
MATCH (p:Project {name: 'sampleSrc'})
MATCH (p)-[:CONTAINS*]->(node)
RETURN labels(node)[0] as node_type, count(node) as count
ORDER BY count DESC

// 호출 체인 확인
MATCH (p:Project {name: 'sampleSrc'})
MATCH (p)-[:CONTAINS]->(f:File {type: 'jsp'})
MATCH (f)-[:CONTAINS]->(api:APIEndpoint)
MATCH (api)-[:CALLS]->(method:Method)
OPTIONAL MATCH (method)-[:EXECUTES]->(sql:SQLQuery)
RETURN f.name, api.name, method.name, sql.name
LIMIT 10
```

### 3.2. Python에서 검증

```python
from temp.neo4j_utils import Neo4jUtils

# Neo4j 연결
neo4j = Neo4jUtils()

try:
    # 프로젝트 정보 확인
    project = neo4j.get_project_info("sampleSrc")
    print(f"프로젝트 정보: {project}")
    
    # 호출 체인 확인
    chains = neo4j.get_call_chain("sampleSrc", limit=5)
    print(f"호출 체인 수: {len(chains)}")
    for chain in chains:
        print(f"  {chain['jsp_file']} → {chain['api_url']} → {chain['method_name']}")
    
    # 아키텍처 레이어 확인
    layers = neo4j.get_architecture_layers("sampleSrc")
    print(f"아키텍처 레이어: {layers}")
    
finally:
    neo4j.close()
```

## 4. 성능 최적화

### 4.1. Neo4j 설정 최적화

Neo4j 설정 파일 (`neo4j.conf`) 수정:

```conf
# 메모리 설정
dbms.memory.heap.initial_size=1G
dbms.memory.heap.max_size=2G
dbms.memory.pagecache.size=1G

# 성능 설정
dbms.logs.query.enabled=false
dbms.track_query_cpu_time=false
dbms.track_query_allocation=false

# 병렬 처리
dbms.cypher.parallel_runtime_support=all
```

### 4.2. 인덱스 생성

```cypher
// 성능 향상을 위한 추가 인덱스
CREATE INDEX component_name_type_idx IF NOT EXISTS 
FOR (c:Component) ON (c.name, c.type)

CREATE INDEX method_layer_idx IF NOT EXISTS 
FOR (m:Method) ON (m.layer)

CREATE INDEX sql_type_idx IF NOT EXISTS 
FOR (s:SQLQuery) ON (s.type)

CREATE INDEX file_type_path_idx IF NOT EXISTS 
FOR (f:File) ON (f.type, f.path)
```

## 5. 문제 해결

### 5.1. 일반적인 오류

#### Neo4j 연결 실패
```
오류: Neo4j 연결 실패: ServiceUnavailable
해결: 
1. Neo4j 서버가 실행 중인지 확인
2. 포트 7687이 열려있는지 확인
3. 방화벽 설정 확인
```

#### 메모리 부족 오류
```
오류: Java heap space
해결:
1. Neo4j 힙 메모리 증가
2. 배치 크기 줄이기 (migrator.py의 batch_size 조정)
3. 대용량 데이터는 분할 처리
```

#### 권한 오류
```
오류: Access denied
해결:
1. Neo4j 사용자 권한 확인
2. 데이터 디렉토리 권한 확인
3. Docker 볼륨 권한 확인
```

### 5.2. 로그 확인

```bash
# 마이그레이션 로그
tail -f ./logs/app.log

# Neo4j 로그 (Docker)
docker logs neo4j-analyzer

# Neo4j 로그 (로컬 설치)
tail -f /var/log/neo4j/neo4j.log
```

### 5.3. 롤백 방법

```bash
# 1. Neo4j 데이터 삭제
# Neo4j Browser에서:
MATCH (n) DETACH DELETE n

# 2. 백업에서 복원
# 백업 파일을 이용한 복원은 별도 스크립트 필요

# 3. SQLite 데이터는 그대로 유지됨
```

## 6. 병행 운영

### 6.1. 기존 코드 수정 없이 병행 운영

```python
# 기존 코드 (SQLite 사용)
from util.database_utils import DatabaseUtils
db_utils = DatabaseUtils()
call_chains = db_utils.get_call_chain_data("sampleSrc")

# 새로운 코드 (Neo4j 사용)
from temp.neo4j_utils import Neo4jDatabaseUtils
neo4j_utils = Neo4jDatabaseUtils()  # 기존 인터페이스와 호환
call_chains = neo4j_utils.get_call_chain_data("sampleSrc")
```

### 6.2. 점진적 전환

1. **Phase 1**: 관계 분석만 Neo4j 사용
2. **Phase 2**: 리포트 생성에 Neo4j 활용  
3. **Phase 3**: 모든 쿼리를 Neo4j로 전환

## 7. 모니터링

### 7.1. 성능 모니터링

```cypher
// 쿼리 성능 모니터링
CALL dbms.queryJmx("org.neo4j:instance=kernel#0,name=Transactions")

// 메모리 사용량 확인
CALL dbms.queryJmx("java.lang:type=Memory")

// 활성 연결 수 확인
CALL dbms.listConnections()
```

### 7.2. 데이터 품질 모니터링

```cypher
// 고아 노드 확인 (관계가 없는 노드)
MATCH (n)
WHERE NOT (n)-[]-()
RETURN labels(n)[0] as node_type, count(n) as orphan_count

// 끊어진 호출 체인 확인
MATCH (api:APIEndpoint)
WHERE NOT (api)-[:CALLS]->(:Method)
RETURN count(api) as broken_apis
```

이 가이드를 따라 실행하면 현재 SQLite 메타데이터베이스를 Neo4j 그래프 데이터베이스로 성공적으로 마이그레이션할 수 있습니다.
