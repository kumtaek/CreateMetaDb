# IMPLICIT JOIN 테이블 추출 누락 버그 분석 보고서

## 1. 문제 요약

**증상**: `FROM users u, orders o` 형식의 IMPLICIT JOIN에서 첫 번째 테이블만 추출되고 나머지 테이블 누락

**영향**:
- 총 SQL 302개 중 IMPLICIT JOIN 사용 SQL 29개 (9.6%)
- 2개 이상 테이블을 IMPLICIT JOIN으로 연결하는 모든 쿼리에서 2번째 이후 테이블 누락

## 2. 정확한 원인

### 문제 위치
- **파일**: `parser/sql_parser.py`
- **메서드**: `extract_tables_and_aliases()` (68-106줄)
- **라인**: 73번 줄

### 문제 코드
```python
r"\bFROM\s+(.*?)(?=\bWHERE|\bGROUP|\bORDER|\bUNION|\bHAVING|\bFOR|\bLIMIT|\bFETCH|\bCONNECT|\bMODEL|\bPIVOT|\s*,\s*\(|;|$)"
```

### 원인 분석

**lookahead 패턴 `\s*,\s*\(`의 의도**:
- 서브쿼리 구분용: `FROM table1, (SELECT ...) sub` 에서 괄호 앞에서 종료

**실제 동작**:
1. SQL: `FROM users u, orders o WHERE`
2. 정규식이 `FROM users u,` 까지 매칭
3. `, ` (쉼표+공백) 부분이 lookahead의 `\s*,\s*` 와 부분 매칭
4. 괄호 `\(`는 없지만, 정규식 엔진이 **lookahead 시작**으로 인식
5. 결과: `users u,` 에서 조기 종료

**테스트 결과**:
```
FROM users u, orders o WHERE
  → 추출: [users u,]
  → 누락: orders o

FROM users u, orders o, products p WHERE
  → 추출: [users u,]
  → 누락: orders o, products p

FROM users u, (SELECT * FROM orders) o WHERE  (서브쿼리)
  → 추출: [users u]  (정상: 서브쿼리 전에서 종료)
```

## 3. 영향 범위 평가

### 3.1 전체 통계
- **총 SQL 개수**: 302개
- **IMPLICIT JOIN 사용**: 29개 (9.6%)

### 3.2 테이블 개수별 분포

| 테이블 개수 | SQL 개수 | 추출된 테이블 | 누락된 테이블 |
|------------|----------|--------------|--------------|
| 2개 | 18개 | 1개 | 1개 |
| 3개 | 7개 | 1개 | 2개 |
| 4개 | 2개 | 1개 | 3개 |
| 5개 | 1개 | 1개 | 4개 |
| 6개 | 1개 | 1개 | 5개 |

**총 누락 테이블**: 최소 51개 이상

### 3.3 구체적 사례

#### 사례 1: component_id 64 (findUsers)
- **SQL**: `FROM USERS U, DEPARTMENTS D, USER_PROFILES P`
- **기대 테이블**: USERS, DEPARTMENTS, USER_PROFILES (3개)
- **실제 저장**: USERS (1개)
- **누락**: DEPARTMENTS, USER_PROFILES

#### 사례 2: component_id 1391 (insertQuery)
- **SQL**: `FROM users u, orders o`
- **기대 테이블**: USERS, ORDERS (2개)
- **실제 저장**: USERS, USER_ORDER_STATISTICS (2개)
  - USER_ORDER_STATISTICS는 INSERT INTO 대상 테이블 (별도 패턴으로 추출)
- **누락**: ORDERS

#### 사례 3: component_id 1394 (insertProductRecommendations.insertQuery)
- **SQL**: `FROM users u, orders o, order_items oi, products p`
- **기대 테이블**: USERS, ORDERS, ORDER_ITEMS, PRODUCTS (4개)
- **실제 저장**: USERS, PRODUCT_RECOMMENDATIONS (2개)
  - PRODUCT_RECOMMENDATIONS는 INSERT INTO 대상
- **누락**: ORDERS, ORDER_ITEMS, PRODUCTS

#### 사례 4: component_id 69 (findUsersWithScatteredConditions)
- **SQL**: `FROM USERS U, DEPARTMENTS D, USER_PROFILES P, USER_TYPES UT, USER_ROLES UR, ROLES R`
- **기대 테이블**: 6개
- **실제 저장**: USERS (1개)
- **누락**: 5개

### 3.4 JOIN 조건 누락

IMPLICIT JOIN의 경우 WHERE 절에 조인 조건이 있으나, 테이블이 누락되면서 JOIN 조건도 추출되지 않음:

```sql
WHERE u.user_id = o.user_id  -- ORDERS 테이블 누락으로 이 조인 조건도 누락
  AND o.order_id = oi.order_id  -- ORDER_ITEMS 테이블 누락으로 이 조인 조건도 누락
```

## 4. 3개 이상 테이블 vs 2개 테이블

**질문**: "3개 이상 테이블 컴마로 IMPLICIT 조인시 문제야?"

**답변**: **아니요. 2개 이상 모든 IMPLICIT JOIN에서 문제 발생**

- **2개 테이블**: `FROM users u, orders o` → `users u,` 추출 (1개 누락)
- **3개 테이블**: `FROM users u, orders o, products p` → `users u,` 추출 (2개 누락)
- **4개 테이블**: `FROM users u, orders o, oi, p` → `users u,` 추출 (3개 누락)

**공통점**: 첫 번째 쉼표(,) 이후 모든 테이블 누락

## 5. EXPLICIT JOIN은 정상인가?

**테스트 필요**: EXPLICIT JOIN (`FROM users u JOIN orders o ON ...`)의 경우

패턴 중 `r"\bJOIN\s+(.*?)(?=\bON)"` 가 별도로 존재하므로, EXPLICIT JOIN은 정상 작동할 가능성이 높음.

## 6. 해결 방안

### 방안 1: `\s*,\s*\(` 패턴 제거 (권장)

**장점**:
- 간단하고 직관적
- IMPLICIT JOIN 완전 해결

**단점**:
- 서브쿼리 구분 불가
- `FROM table1, (SELECT ...) sub` 케이스에서 서브쿼리까지 포함

**검증 필요**:
- 서브쿼리 포함 케이스가 실제 존재하는지 확인
- 서브쿼리가 별도로 파싱되는지 확인

### 방안 2: FROM 절 전체 추출 후 쉼표 split

```python
# FROM 절 전체 추출
from_clause = extract_from_clause(sql)  # "users u, orders o, products p"

# 괄호로 묶인 서브쿼리 제거
from_clause = remove_subqueries(from_clause)

# 쉼표로 split
for part in from_clause.split(','):
    # 각 부분 파싱
    table, alias = parse_table_alias(part)
```

**장점**:
- 서브쿼리와 IMPLICIT JOIN 모두 처리
- 정확성 높음

**단점**:
- 로직 복잡도 증가

### 방안 3: lookahead 패턴 정교화

```python
# 괄호가 실제로 있을 때만 종료
r"\bFROM\s+(.*?)(?=\bWHERE|\bGROUP|...|,\s*\(SELECT|;|$)"
```

**장점**:
- 서브쿼리만 정확히 구분

**단점**:
- 복잡한 케이스 처리 어려움

## 7. 권장 조치

1. **즉시 수정**: `\s*,\s*\(` 패턴 제거 (방안 1)
2. **검증**: 서브쿼리 포함 SQL이 정상 동작하는지 확인
3. **필요시**: 방안 2로 정교화

## 8. 테스트 케이스

수정 후 다음 케이스 테스트 필요:

```sql
-- IMPLICIT JOIN 2개
SELECT * FROM users u, orders o WHERE u.id = o.user_id

-- IMPLICIT JOIN 3개
SELECT * FROM users u, orders o, products p WHERE ...

-- 서브쿼리
SELECT * FROM users u, (SELECT * FROM orders WHERE ...) o WHERE ...

-- 혼합 (IMPLICIT + EXPLICIT)
SELECT * FROM users u, orders o JOIN products p ON o.product_id = p.id WHERE ...

-- INSERT ... SELECT with IMPLICIT JOIN
INSERT INTO target SELECT * FROM users u, orders o WHERE ...
```
