# Neo4j 네이티브 그래프 시각화 가이드

## 1. Neo4j Browser 기본 사용법

### 접속 및 로그인
```
1. 브라우저에서 http://localhost:7474 접속
2. 로그인: neo4j / password123
3. 상단의 쿼리 입력창에 Cypher 쿼리 입력
```

### 기본 시각화 쿼리들

#### 전체 그래프 구조 보기 (소규모)
```cypher
MATCH (n)-[r]->(m) 
RETURN n, r, m 
LIMIT 50
```

#### 프로젝트별 호출 체인 시각화
```cypher
MATCH (p:Project {name: 'sampleSrc'})
MATCH (p)-[:CONTAINS]->(jsp:File {type: 'jsp'})
MATCH (jsp)-[:CONTAINS]->(api:APIEndpoint)
MATCH (api)-[:CALLS]->(method:Method)
OPTIONAL MATCH (method)-[:EXECUTES]->(sql:SQLQuery)
RETURN jsp, api, method, sql
LIMIT 20
```

#### 특정 테이블을 사용하는 모든 경로 시각화
```cypher
MATCH path = (jsp:File)-[:CONTAINS*]->()-[:USES]->(table:Table {name: 'USERS'})
RETURN path
LIMIT 10
```

## 2. 시각화 결과 해석

### 노드 (원/사각형)
- **색상**: 노드 타입별로 자동 색상 지정
  - 🔵 파일 (File) - 파란색
  - 🟢 메서드 (Method) - 초록색  
  - 🔴 SQL (SQLQuery) - 빨간색
  - 🟡 테이블 (Table) - 노란색
  - 🟣 API (APIEndpoint) - 보라색

- **크기**: 연결된 관계 수에 따라 자동 조절
- **레이블**: 노드 이름 표시

### 엣지 (화살표 선)
- **방향**: 호출/사용 방향 표시
- **타입**: 관계 타입별 다른 스타일
  - CALLS → 실선 화살표
  - EXECUTES → 점선 화살표
  - USES → 굵은 화살표
- **색상**: 관계 타입별 자동 색상

### 인터랙티브 기능
- **드래그**: 노드를 끌어서 레이아웃 조정
- **줌**: 마우스 휠로 확대/축소
- **클릭**: 노드 클릭 시 속성 정보 표시
- **더블클릭**: 연결된 노드들 확장 표시

## 3. 실제 화면 예시

### 호출 체인 시각화 결과
```
[userList.jsp] ──CONTAINS──> [/api/users:GET] ──CALLS──> [UserController.getUsers()]
                                                              │
                                                              │ EXECUTES
                                                              ▼
                                                        [SELECT * FROM users]
                                                              │
                                                              │ USES  
                                                              ▼
                                                          [USERS 테이블]
```

### 복잡한 관계망 시각화
```
                    [OrderController]
                           │ CALLS
                           ▼
                    [OrderService] ──CALLS──> [UserService]
                           │                        │
                           │ EXECUTES               │ EXECUTES
                           ▼                        ▼
                [SELECT * FROM orders]    [SELECT * FROM users]
                           │                        │
                           │ USES                   │ USES
                           ▼                        ▼
                    [ORDERS 테이블] ──FK──> [USERS 테이블]
```

## 4. 고급 시각화 기능

### 스타일 커스터마이징
```cypher
// 노드 스타일 설정 (Browser 설정에서)
:style {
  node.File {
    color: #68bdf6;
    border-color: #5ca8db;
    text-color-internal: #ffffff;
  }
  
  node.Method {
    color: #f79767;
    border-color: #f36924;
  }
  
  relationship.CALLS {
    color: #d9534f;
    shaft-width: 3px;
  }
}
```

### 조건부 시각화
```cypher
// 에러가 있는 컴포넌트만 표시
MATCH (n)-[r]->(m)
WHERE n.has_error = 'Y' OR m.has_error = 'Y'
RETURN n, r, m

// 특정 레이어만 표시
MATCH (n:Method {layer: 'CONTROLLER'})-[r]->(m)
RETURN n, r, m

// 신뢰도가 높은 관계만 표시
MATCH (n)-[r]->(m)
WHERE r.confidence > 0.8
RETURN n, r, m
```

## 5. 시각화 활용 시나리오

### 시나리오 1: 버그 추적
```cypher
// 특정 API에서 에러가 발생한 전체 경로 추적
MATCH path = (api:APIEndpoint {name: '/api/users:POST'})-[:CALLS*]->(component)
WHERE component.has_error = 'Y'
RETURN path
```

### 시나리오 2: 영향도 분석
```cypher
// USERS 테이블 변경 시 영향받는 모든 컴포넌트
MATCH (table:Table {name: 'USERS'})<-[:USES*]-(component)
RETURN table, component
```

### 시나리오 3: 아키텍처 검증
```cypher
// 레이어 위반 사례 찾기 (VIEW에서 직접 DB 접근)
MATCH (view:Method {layer: 'VIEW'})-[:EXECUTES]->(sql:SQLQuery)
RETURN view, sql
```

## 6. 기존 관계형 DB 리포트와 비교

### 기존 방식 (CallChain Report)
- 📊 **테이블 형태**: 행과 열로 표시
- 🔍 **순차적 읽기**: 위에서 아래로 스캔
- 📝 **텍스트 기반**: 관계를 텍스트로 표현

### Neo4j 그래프 시각화
- 🕸️ **네트워크 형태**: 노드와 엣지로 표시
- 👁️ **직관적 이해**: 한눈에 전체 구조 파악
- 🎯 **인터랙티브**: 클릭/드래그로 탐색
- 🔄 **동적 확장**: 필요한 부분만 확장 표시

## 7. 실제 사용 팁

### 성능 최적화
```cypher
// 큰 그래프의 경우 LIMIT 사용 필수
MATCH (n)-[r]->(m) 
RETURN n, r, m 
LIMIT 100

// 특정 영역부터 시작해서 점진적 확장
MATCH (start:APIEndpoint {name: '/api/users:GET'})
MATCH (start)-[r*1..3]->(end)
RETURN start, r, end
```

### 레이아웃 조정
- **Force-directed**: 자동 배치 (기본값)
- **Hierarchical**: 계층적 배치
- **Manual**: 수동 배치 (드래그)

### 필터링
```cypher
// 노드 타입별 필터링
MATCH (n:Method)-[r]->(m:SQLQuery)
RETURN n, r, m

// 속성별 필터링  
MATCH (n)-[r {confidence: 1.0}]->(m)
RETURN n, r, m
```

이렇게 Neo4j Browser를 사용하면 복잡한 메타데이터 관계를 **직관적이고 인터랙티브하게** 탐색할 수 있습니다!
