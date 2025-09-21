# SQLite to Neo4j 마이그레이션 계획

## 1. Neo4j 환경 설정

### 1.1. Neo4j 설치 및 설정
```bash
# Neo4j Desktop 또는 Community Edition 설치
# Docker 사용 시:
docker run -d \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    neo4j:latest
```

### 1.2. Python Neo4j 드라이버 설치
```bash
pip install neo4j pandas
```

## 2. 그래프 모델 설계

### 2.1. 노드 레이블 매핑
```
SQLite 테이블 → Neo4j 노드 레이블
- projects → Project
- files → File  
- classes → Class
- components → Component (METHOD, API_URL, SQL_*, TABLE, COLUMN 등)
- tables → Table (components의 TABLE 타입과 통합)
- columns → Column (components의 COLUMN 타입과 통합)
```

### 2.2. 관계 매핑
```
SQLite relationships.rel_type → Neo4j 관계
- CALL_METHOD → :CALLS
- CALL_QUERY → :EXECUTES  
- USE_TABLE → :USES
- INHERITANCE → :INHERITS
- JOIN_EXPLICIT → :JOINS
- JOIN_IMPLICIT → :IMPLICIT_JOINS
- FK → :FOREIGN_KEY
```

### 2.3. 속성 매핑
모든 SQLite 컬럼을 Neo4j 노드 속성으로 변환:
- 기본 속성: id, name, type, created_at, updated_at
- 메타 속성: has_error, error_message, confidence, del_yn
- 특수 속성: hash_value, layer, line_start, line_end

## 3. 마이그레이션 스크립트 구조

### 3.1. 데이터 추출 (SQLite)
- 기존 database_utils.py 활용
- 모든 테이블 데이터를 JSON/CSV로 추출

### 3.2. 데이터 변환 (Transform)
- 관계형 → 그래프 구조 변환
- 중복 제거 및 데이터 정제
- 신뢰도 기반 필터링

### 3.3. 데이터 로드 (Neo4j)
- 노드 생성 (Cypher CREATE)
- 관계 생성 (Cypher MATCH + CREATE)
- 인덱스 및 제약조건 생성

## 4. 점진적 마이그레이션 전략

### Phase 1: 병행 운영
- SQLite 메인DB 유지
- Neo4j 관계 분석용으로만 사용
- 데이터 동기화 스크립트

### Phase 2: 부분 전환  
- 관계 쿼리만 Neo4j 사용
- 기본 CRUD는 SQLite 유지
- 성능 및 안정성 검증

### Phase 3: 완전 전환
- 모든 쿼리를 Neo4j로 변경
- SQLite는 백업용으로만 유지
- 기존 리포트 생성 로직 변경
