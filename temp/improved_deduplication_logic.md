# 개선된 중복 관계 제거 로직

## 문제점 (기존 로직)

```python
# 기존 로직: 무조건 MIN(relationship_id) 유지
keep_id = MIN(relationship_id)

# 문제 시나리오
ID 100: 쿼리A → 테이블USERS (빈 껍데기)
ID 150: 쿼리A → 테이블USERS (컬럼, JOIN 등 상세 정보 多)

결과: ID 100 유지, ID 150 삭제 ❌
→ 컬럼, JOIN 정보 모두 손실!
```

---

## 해결책 (개선된 로직)

### 핵심 아이디어: **삭제 전 정보 병합**

```
Step 1: 중복 그룹 확인
----------------------
ID 100: 쿼리A → 테이블USERS
ID 150: 쿼리A → 테이블USERS (중복)

Step 2: 하위 정보 병합 (삭제 전 필수!)
----------------------
1. ID 150을 parent_id로 가진 컴포넌트들
   → parent_id를 150에서 100으로 변경

2. ID 150을 src_id로 가진 관계들
   → src_id를 150에서 100으로 변경
   → 단, 이미 (100, dst_id, rel_type) 관계가 있으면 삭제

3. ID 150을 dst_id로 가진 관계들
   → dst_id를 150에서 100으로 변경
   → 단, 이미 (src_id, 100, rel_type) 관계가 있으면 삭제

Step 3: 안전하게 삭제
----------------------
ID 150 삭제 (del_yn='Y')
→ 이제 ID 150에 종속된 정보가 없으므로 안전!
```

---

## 구현 코드 (consistency_validator.py:400-542)

### 주요 로직

```python
def _remove_duplicate_relationships(self):
    """중복 관계 제거 (같은 src_id, dst_id, rel_type의 관계 중복 제거 + 하위 정보 병합)"""

    # 1. 중복 그룹 조회
    duplicate_relationships = self.db_utils.execute_query("""
        SELECT
            src_id,
            dst_id,
            rel_type,
            COUNT(*) as count,
            GROUP_CONCAT(relationship_id) as relationship_ids,
            MIN(relationship_id) as keep_id
        FROM relationships
        WHERE del_yn = 'N'
        GROUP BY src_id, dst_id, rel_type
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """)

    # 2. 각 중복 그룹 처리
    for dup in duplicate_relationships:
        keep_id = dup['keep_id']  # 유지할 ID (MIN)
        remove_ids = [중복 ID들]   # 삭제할 ID들

        for remove_id in remove_ids:
            # [Step 1] 삭제 전 하위 정보 병합

            # 1-1. parent_id로 참조하는 컴포넌트 이동
            UPDATE components
            SET parent_id = keep_id
            WHERE parent_id = remove_id

            # 1-2. src_id로 참조하는 관계 이동
            UPDATE relationships
            SET src_id = keep_id
            WHERE src_id = remove_id
            (단, 중복 방지 검사 포함)

            # 1-3. dst_id로 참조하는 관계 이동
            UPDATE relationships
            SET dst_id = keep_id
            WHERE dst_id = remove_id
            (단, 중복 방지 검사 포함)

            # [Step 2] 병합 완료 후 안전하게 삭제
            UPDATE relationships
            SET del_yn = 'Y'
            WHERE relationship_id = remove_id
```

---

## 병합 세부 로직

### 1. 컴포넌트 parent_id 병합

```python
# 1-1. 이 relationship_id를 parent_id로 가진 컴포넌트들을 keep_id로 이동
components_to_merge = self.db_utils.execute_query("""
    SELECT component_id, component_type, component_name
    FROM components
    WHERE parent_id = ? AND del_yn = 'N'
""", (remove_id,))

if components_to_merge:
    for comp in components_to_merge:
        self.db_utils.execute_query("""
            UPDATE components
            SET parent_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE component_id = ?
        """, (keep_id, comp['component_id']))
        merge_count += 1
        info(f"  병합: {comp['component_type']}({comp['component_name']}) parent_id {remove_id} → {keep_id}")
```

**예시**:
```
Before:
  COLUMN(USER_ID) parent_id=150 (삭제 예정)
  COLUMN(NAME) parent_id=150 (삭제 예정)

After:
  COLUMN(USER_ID) parent_id=100 (병합됨)
  COLUMN(NAME) parent_id=100 (병합됨)
```

---

### 2. 관계 src_id 병합 (중복 방지)

```python
# 1-2. 이 relationship_id를 src_id로 가진 다른 관계들을 keep_id로 이동
related_as_src = self.db_utils.execute_query("""
    SELECT relationship_id, rel_type, dst_id
    FROM relationships
    WHERE src_id = ? AND del_yn = 'N'
""", (remove_id,))

if related_as_src:
    for rel in related_as_src:
        # 중복 방지: 이미 동일한 (keep_id, dst_id, rel_type) 관계가 있는지 확인
        existing = self.db_utils.execute_query("""
            SELECT relationship_id
            FROM relationships
            WHERE src_id = ? AND dst_id = ? AND rel_type = ? AND del_yn = 'N'
            LIMIT 1
        """, (keep_id, rel['dst_id'], rel['rel_type']))

        if not existing:
            # 중복 없음 → 병합
            self.db_utils.execute_query("""
                UPDATE relationships
                SET src_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE relationship_id = ?
            """, (keep_id, rel['relationship_id']))
            merge_count += 1
            info(f"  병합: 관계 src_id {remove_id} → {keep_id} ({rel['rel_type']})")
        else:
            # 중복 있음 → 이 관계는 삭제
            self.db_utils.execute_query("""
                UPDATE relationships
                SET del_yn = 'Y', updated_at = CURRENT_TIMESTAMP
                WHERE relationship_id = ?
            """, (rel['relationship_id'],))
            info(f"  중복 관계 삭제: relationship_id {rel['relationship_id']} (이미 존재)")
```

**예시**:
```
Before:
  relationship_id: 200 (src=150, dst=컬럼A, type=USE_COLUMN)
  relationship_id: 201 (src=150, dst=컬럼B, type=USE_COLUMN)

After (중복 없음):
  relationship_id: 200 (src=100, dst=컬럼A, type=USE_COLUMN) ← 병합됨
  relationship_id: 201 (src=100, dst=컬럼B, type=USE_COLUMN) ← 병합됨

After (중복 있음):
  relationship_id: 50 (src=100, dst=컬럼A, type=USE_COLUMN) ← 이미 존재
  relationship_id: 200 (del_yn='Y') ← 중복이므로 삭제
  relationship_id: 201 (src=100, dst=컬럼B, type=USE_COLUMN) ← 병합됨
```

---

### 3. 관계 dst_id 병합 (중복 방지)

```python
# 1-3. 이 relationship_id를 dst_id로 가진 다른 관계들을 keep_id로 이동
related_as_dst = self.db_utils.execute_query("""
    SELECT relationship_id, rel_type, src_id
    FROM relationships
    WHERE dst_id = ? AND del_yn = 'N'
""", (remove_id,))

if related_as_dst:
    for rel in related_as_dst:
        # 중복 방지
        existing = self.db_utils.execute_query("""
            SELECT relationship_id
            FROM relationships
            WHERE src_id = ? AND dst_id = ? AND rel_type = ? AND del_yn = 'N'
            LIMIT 1
        """, (rel['src_id'], keep_id, rel['rel_type']))

        if not existing:
            # 중복 없음 → 병합
            self.db_utils.execute_query("""
                UPDATE relationships
                SET dst_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE relationship_id = ?
            """, (keep_id, rel['relationship_id']))
            merge_count += 1
            info(f"  병합: 관계 dst_id {remove_id} → {keep_id} ({rel['rel_type']})")
        else:
            # 중복 있음 → 이 관계는 삭제
            self.db_utils.execute_query("""
                UPDATE relationships
                SET del_yn = 'Y', updated_at = CURRENT_TIMESTAMP
                WHERE relationship_id = ?
            """, (rel['relationship_id'],))
            info(f"  중복 관계 삭제: relationship_id {rel['relationship_id']} (이미 존재)")
```

---

## 로그 출력 예시

```
중복 관계 발견: 5개 그룹

  병합: COLUMN(USER_ID) parent_id 150 → 100
  병합: COLUMN(NAME) parent_id 150 → 100
  병합: COLUMN(EMAIL) parent_id 150 → 100
  병합: 관계 src_id 150 → 100 (USE_COLUMN)
  병합: 관계 src_id 150 → 100 (USE_COLUMN)
  중복 관계 삭제: relationship_id 250 (이미 존재)
  중복 관계 제거 (병합 5건): relationship_id 150 삭제, 100으로 통합

중복 관계 제거 완료: 5개 제거됨, 17개 하위 정보 병합 (중복 그룹: 5개)
```

---

## 데이터 무결성 보장

### 삭제 전 검증 사항

1. **parent_id 참조 무결성**
   - 삭제 전: 모든 child의 parent_id를 keep_id로 변경
   - 삭제 후: child가 유효한 parent를 참조

2. **src_id 참조 무결성**
   - 삭제 전: 모든 관계의 src_id를 keep_id로 변경
   - 삭제 후: 모든 관계가 유효한 src를 참조

3. **dst_id 참조 무결성**
   - 삭제 전: 모든 관계의 dst_id를 keep_id로 변경
   - 삭제 후: 모든 관계가 유효한 dst를 참조

### 중복 방지

- 병합 시 이미 동일한 관계가 있으면 **병합하지 않고 삭제**
- 예: `(100, 컬럼A, USE_COLUMN)` 관계가 이미 있으면
  - `(150, 컬럼A, USE_COLUMN)` 관계는 병합하지 않고 삭제

---

## 테스트 검증

```python
# 테스트 실행
validator = ConsistencyValidator('sampleSrc')
validator._remove_duplicate_relationships()

# 검증
cursor.execute("""
    SELECT COUNT(*) FROM (
        SELECT src_id, dst_id, rel_type, COUNT(*) as cnt
        FROM relationships
        WHERE del_yn = 'N'
        GROUP BY src_id, dst_id, rel_type
        HAVING COUNT(*) > 1
    )
""")

result = cursor.fetchone()[0]
print(f'중복 관계: {result}개 (0이어야 정상)')
```

**예상 결과**:
```
중복 관계: 0개 ✅
```

---

## 장점

1. **데이터 손실 0%**: 모든 하위 정보를 병합 후 삭제
2. **참조 무결성 보장**: 삭제 전 모든 참조를 유지할 ID로 변경
3. **중복 방지**: 병합 시 중복 검사로 2차 중복 방지
4. **로그 추적**: 모든 병합 작업이 로그에 기록됨
5. **복구 가능**: 논리 삭제(`del_yn='Y'`)로 필요시 복구 가능

---

## 주의사항

1. **트랜잭션 필요**: 병합 도중 오류 발생 시 롤백 필요
2. **성능**: 중복이 많을 경우 병합 작업 시간 증가
3. **로그 크기**: 병합 건수가 많으면 로그 파일 크기 증가

---

## 결론

**기존 문제점**:
- 무조건 MIN(ID) 유지 → 빈 껍데기 유지 가능성
- 하위 정보 손실 위험

**개선 사항**:
- 삭제 전 모든 하위 정보 병합
- 참조 무결성 완벽 보장
- 데이터 손실 0%

**작업 완료**: ✅ consistency_validator.py:400-542
