# 백엔드매핑 리포트 중복 표시 근본 원인 분석

## 문제 요약

백엔드매핑 리포트에서 하나의 쿼리에 동일 테이블이 중복으로 표시되는 문제 발생

## 근본 원인

**파일**: `reports/backend_mapping_report_generator.py`
**위치**: Line 306 (`_load_metadata_join_conditions()` 함수)

### 문제 코드

```python
# Line 304-319
cursor.execute(
    """
    SELECT src.component_name AS sql_comp,
           GROUP_CONCAT(dst.component_name) AS table_list  # ← DISTINCT 없음!
    FROM relationships r
    JOIN components src ON r.src_id = src.component_id AND src.del_yn = 'N'
    JOIN components dst ON r.dst_id = dst.component_id AND dst.del_yn = 'N'
    JOIN projects p ON src.project_id = p.project_id
    WHERE p.project_name = ?
      AND r.rel_type = 'USE_TABLE'
      AND r.del_yn = 'N'
      AND dst.component_type = 'TABLE'
    GROUP BY src.component_name
    """,
    (self.project_name,)
)
sql_tables_map = {row[0].upper(): row[1].split(',') if row[1] else [] for row in cursor.fetchall()}
```

### 왜 문제가 되는가?

**시나리오**:
```
relationships 테이블에 중복 관계가 있는 경우:
- relationship_id: 100 (쿼리A → 테이블USERS, del_yn='N')
- relationship_id: 150 (쿼리A → 테이블USERS, del_yn='N') [중복!]

현재 쿼리 결과:
sql_comp: "쿼리A"
table_list: "USERS,USERS"  ← 중복!

sql_tables_map 결과:
{
  "쿼리A": ["USERS", "USERS"]  ← 중복 배열!
}
```

**결과**:
- `sql_tables_map`에 중복 테이블이 저장됨
- 이후 JOIN 조건 수집 시 (lines 352-392) 중복 테이블로 인해 동일 조인 조건이 여러 번 수집됨
- 최종 리포트에서 중복 테이블 표시됨

---

## 기존 수정 내역 (불완전)

### 1차 수정: `_load_metadata_use_tables()` (Line 244-284)
```python
cursor.execute("""
    SELECT DISTINCT  # ✅ DISTINCT 추가됨
           src.component_name AS sql_comp,
           dst.component_name AS table_name,
           COALESCE(t.table_owner, 'UNKNOWN') AS table_owner
    FROM relationships r
    ...
""")
```

**결과**: 이 함수는 정상 동작하지만, `_load_metadata_join_conditions()`에서 **별도로 USE_TABLE을 다시 조회**하기 때문에 효과 없음!

---

## 해결 방안

### 수정 위치

**파일**: `reports/backend_mapping_report_generator.py`
**라인**: 306

### 수정 내용

```python
# 기존
GROUP_CONCAT(dst.component_name) AS table_list

# 수정
GROUP_CONCAT(DISTINCT dst.component_name) AS table_list
```

### 수정 후 예상 결과

```sql
-- Before (중복 관계가 있을 때)
sql_comp: "쿼리A"
table_list: "USERS,USERS"  # ← 중복

-- After (DISTINCT 적용)
sql_comp: "쿼리A"
table_list: "USERS"  # ✅ 중복 제거
```

```python
# sql_tables_map 결과
{
  "쿼리A": ["USERS"]  # ✅ 단일 테이블
}
```

---

## 추가 분석: 왜 두 곳에서 USE_TABLE을 조회하는가?

### 1. `_load_metadata_use_tables()` (Line 244-284)
- **목적**: 쿼리별 사용 테이블 목록 조회 (owner 포함)
- **사용처**: `_get_query_data()` 함수에서 `metadata_tables` 필드로 사용
- **반환**: `Dict[str, List[Dict[str, str]]]` (owner + table 정보)

### 2. `_load_metadata_join_conditions()` (Line 286-397)
- **목적**: 쿼리별 JOIN 조건 수집
- **부수 효과**: USE_TABLE 관계도 다시 조회하여 `sql_tables_map` 생성
- **사용처**: JOIN 조건 수집 시 테이블 쌍 확인용 (lines 352-392)
- **반환**: `Dict[str, Dict[str, Any]]` (join_type + join_conditions)

### 중복 조회 이유
- JOIN 조건 수집을 위해 "어떤 SQL이 어떤 테이블들을 사용하는지" 알아야 함
- 테이블 쌍별로 조인 관계를 확인하려면 먼저 SQL이 사용하는 테이블 목록 필요
- 이미 `_load_metadata_use_tables()`에서 조회했지만, 이 함수는 owner 정보 포함한 복잡한 구조 반환
- `_load_metadata_join_conditions()`는 단순 테이블명 리스트만 필요하므로 별도 조회

**문제**: 별도 조회할 때 DISTINCT를 빠뜨림!

---

## 검증 방법

### 1. 현재 상태 확인 (수정 전)

```bash
python create_report.py --project-name sampleSrc --report-type backend-mapping
```

**확인 사항**:
- 리포트에서 동일 쿼리에 중복 테이블 표시되는지 확인

### 2. 수정 후 확인

```python
# Line 306 수정 후
python create_report.py --project-name sampleSrc --report-type backend-mapping
```

**기대 결과**:
- 동일 쿼리에 중복 테이블 표시 제거됨
- JOIN 조건도 중복 없이 정상 표시됨

---

## 결론

**근본 원인**: `_load_metadata_join_conditions()` 함수에서 USE_TABLE 관계 조회 시 DISTINCT 누락

**해결책**: Line 306에 `GROUP_CONCAT(DISTINCT dst.component_name)` 적용

**예상 효과**:
- 백엔드매핑 리포트에서 중복 테이블 표시 완전 제거
- JOIN 조건 수집 정확도 향상
- 데이터 무결성 유지 (실제 relationships 테이블은 이미 중복 제거됨)

**작업 범위**: 1줄 수정 (`GROUP_CONCAT` → `GROUP_CONCAT(DISTINCT)`)
