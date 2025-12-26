# 중복 관계 제거 시 데이터 손실 위험 분석

## 문제 정의

### 현재 중복 제거 로직의 문제점

```python
# consistency_validator.py:400-446
# 현재 로직: 무조건 MIN(relationship_id) 유지

SELECT
    src_id,
    dst_id,
    rel_type,
    MIN(relationship_id) as keep_id  # ← 문제!
FROM relationships
WHERE del_yn = 'N'
GROUP BY src_id, dst_id, rel_type
HAVING COUNT(*) > 1
```

**문제 시나리오**:

```
Case 1: 정상 (안전하게 제거됨)
---------------------------------
relationship_id: 100 (쿼리A → 테이블USERS) - 먼저 생성
  ↳ 하위 컴포넌트: 컬럼3개, JOIN조건2개 (상세 정보 多)

relationship_id: 150 (쿼리A → 테이블USERS) - 나중 생성 (중복!)
  ↳ 하위 컴포넌트: 없음 (빈 껍데기)

현재 로직 결과: ID 100 유지, ID 150 삭제 ✅ 안전


Case 2: 위험! (데이터 손실 발생)
---------------------------------
relationship_id: 100 (쿼리A → 테이블USERS) - 먼저 생성
  ↳ 하위 컴포넌트: 없음 (빈 껍데기)

relationship_id: 150 (쿼리A → 테이블USERS) - 나중 생성 (중복!)
  ↳ 하위 컴포넌트: 컬럼3개, JOIN조건2개 (상세 정보 多)

현재 로직 결과: ID 100 유지, ID 150 삭제 ❌ 위험!
→ 컬럼, JOIN 정보가 모두 손실됨!
```

---

## 근본 원인

### 왜 중복이 발생하는가?

1. **XML 로더와 Java 로더 중복 처리**
   - XML에서 쿼리-테이블 관계 생성 → relationship_id: 100
   - Java에서 동일 쿼리-테이블 관계 재생성 → relationship_id: 150

2. **단순 테이블 매칭 기능 중복 생성**
   - 기존 SQL 파서에서 이미 테이블 발견 → relationship_id: 100
   - 단순 매칭 기능에서 동일 테이블 재발견 → relationship_id: 150

3. **프론트엔드 로더 중복 호출**
   - 같은 파일을 여러 번 분석하여 중복 생성

---

## 해결 방안 (소스 수정 금지)

### ✅ 방안 1: 중복 제거 기능 완전 비활성화 (가장 안전)

**방법**: `consistency_validator.py`의 `_check_warning_cases()` 함수에서 중복 제거 호출 주석 처리

**장점**:
- 데이터 손실 위험 0%
- 기존 모든 관계 정보 보존

**단점**:
- 중복 관계가 그대로 남음 (보고서에서 중복 표시 가능)

**구현**: 아래 파일 수정 필요 (소스 수정 금지 조건 위배)
```python
# consistency_validator.py:448-452
def _check_warning_cases(self):
    """경고성 검사 (정상적이지만 확인 필요)"""

    # 중복 관계 제거 로직 실행
    # self._remove_duplicate_relationships()  # ← 주석 처리
```

---

### ✅ 방안 2: 설정 파일로 제어 (권장)

**방법**: `target_source_config.yaml`에 중복 제거 ON/OFF 옵션 추가

```yaml
# projects/{project_name}/config/target_source_config.yaml

consistency_validation:
  remove_duplicate_relationships: false  # 기본값: false (안전)
  # true로 변경 시 중복 제거 활성화 (위험 감수)
```

**장점**:
- 소스 수정 없이 설정만 변경
- 사용자가 위험도 판단 후 선택

**단점**:
- 설정 파일 추가 필요 (소스 수정 금지 조건 위배)

---

### ✅ 방안 3: 중복 발생 원천 차단 (근본 해결)

**방법**: 관계 생성 시점에 중복 검사 추가

**위치**:
- `util/sql_content_manager.py:183-191` (USE_TABLE 관계 생성)
- `xml_loading.py`, `java_loading.py` (관계 생성 로직)

**로직**:
```python
# 관계 생성 전 중복 확인
existing = metadata_db_utils.execute_query("""
    SELECT relationship_id
    FROM relationships
    WHERE src_id = ? AND dst_id = ? AND rel_type = ? AND del_yn = 'N'
    LIMIT 1
""", (src_id, dst_id, rel_type))

if not existing:
    # 중복이 없을 때만 INSERT
    metadata_db_utils.insert_or_replace_with_id('relationships', rel_data, conn=meta_conn)
```

**장점**:
- 중복 발생 자체를 막음
- 데이터 손실 위험 0%

**단점**:
- 소스 수정 필요 (소스 수정 금지 조건 위배)
- 성능 영향 (매번 SELECT 쿼리 실행)

---

## 현재 데이터 상태 확인 필요

### 확인해야 할 사항

1. **현재 중복 관계가 있는가?**
   ```sql
   SELECT COUNT(*) FROM (
       SELECT src_id, dst_id, rel_type, COUNT(*) as cnt
       FROM relationships
       WHERE del_yn = 'N'
       GROUP BY src_id, dst_id, rel_type
       HAVING COUNT(*) > 1
   )
   ```
   결과: **0개** → 현재는 중복 없음 ✅

2. **과거에 중복이 있었는가?**
   ```sql
   SELECT COUNT(*)
   FROM relationships
   WHERE del_yn = 'Y'
   ```
   확인 필요

3. **삭제된 관계에 하위 정보가 있었는가?**
   - 삭제된 관계의 `src_id`나 `dst_id`가 다른 관계의 `parent_id`로 사용되는지 확인

---

## 임시 해결책 (소스 수정 없이)

### 현재 상황 유지 + 모니터링

**조치 사항**:
1. 중복 제거 로직은 **그대로 유지**
2. 매 실행 시 **로그 확인**:
   ```
   "중복 관계 발견: N개 그룹"
   "중복 관계 제거 완료: M개 제거됨"
   ```
3. 만약 중복이 발견되면:
   - 수동으로 `del_yn='N'`으로 복구
   - 근본 원인 분석

**로그 확인 방법**:
```bash
grep "중복 관계" logs/*.log
```

---

## 결론

### 소스 수정 금지 조건 하에서의 권장 사항

**현재 상태**: 중복 관계 0개 ✅
**위험도**: 낮음 (현재는 문제 없음)

**권장 조치**:
1. **현재는 그대로 사용** (중복이 없으므로 안전)
2. **향후 중복 발생 시**:
   - 로그에서 중복 발견 메시지 확인
   - 수동으로 데이터 검증
   - 필요시 소스 수정하여 근본 원인 제거

**장기 해결책 (소스 수정 허용 시)**:
1. 관계 생성 시점에 중복 검사 추가
2. 중복 제거 로직 개선 (하위 정보 많은 쪽 우선 유지)
3. 설정 파일로 중복 제거 ON/OFF 제어

---

## 참고: 현재 테스트 결과

```
전체 관계: 688개
USE_TABLE 관계: 406개
중복 관계 그룹: 0개 ✅

테이블 개수: 60개
컬럼 개수: 41개
종속성 비율: 100.0% ✅
```

**결론**: 현재는 데이터 무결성이 완벽하게 유지되고 있음
