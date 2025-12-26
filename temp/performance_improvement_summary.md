# CSV 테이블 검색 성능 개선 및 중복 제거 작업 완료 보고

## 개요
- **목적**: 5천여 개 CSV 테이블 검색 시 성능 병목 해결 및 중복 관계 제거
- **작업일**: 2025-11-28
- **적용 범위**: `util/sql_content_manager.py`, `consistency_validator.py`, `reports/backend_mapping_report_generator.py`

---

## 1. 성능 개선 작업

### 1.1 정규식 패턴 사전 컴파일 (성능 개선 핵심)

**문제점**:
- 기존: 쿼리 개수(N) × 테이블 개수(M) = **O(N × M)** 정규식 재컴파일
- 5천 개 테이블 × 500개 쿼리 = **250만 번** 정규식 컴파일

**해결 방법**:
```python
# util/sql_content_manager.py:770-789
def _compile_regex_patterns(self, table_names: set):
    """테이블명에 대한 정규식 패턴을 사전 컴파일 (성능 최적화)"""
    import re
    self._compiled_regex_patterns = {}

    for table_name in table_names:
        # 단어 경계로 검색하는 패턴 사전 컴파일
        pattern = re.compile(r'\b' + re.escape(table_name) + r'\b')
        self._compiled_regex_patterns[table_name] = pattern
```

**효과**:
- 정규식 객체를 **한 번만 컴파일**하고 재사용
- 예상 속도 향상: **3~5배**

---

### 1.2 SQL 전처리 결과 캐싱 (중복 처리 제거)

**문제점**:
- 기존: 동일 SQL도 매번 주석 제거 정규식 4번 실행
- MyBatis 태그, 라인 주석, 블록 주석, 공백 정규화 반복

**해결 방법**:
```python
# util/sql_content_manager.py:791-831
def _remove_comments_simple(self, sql: str) -> str:
    """SQL에서 주석 및 태그를 제거하는 간단한 전처리 (캐싱 적용)"""
    import hashlib

    # SQL 해시 생성 (캐시 키)
    sql_hash = hashlib.md5(sql.encode('utf-8')).hexdigest()

    # 캐시 확인
    if sql_hash in self._cleaned_sql_cache:
        return self._cleaned_sql_cache[sql_hash]

    # ... 주석 제거 로직 ...

    # 캐시 저장 (메모리 제한: 최대 1만 개)
    if len(self._cleaned_sql_cache) < 10000:
        self._cleaned_sql_cache[sql_hash] = cleaned

    return cleaned
```

**효과**:
- 동일 SQL 재처리 비용 **제로**
- 예상 속도 향상: **1.5~2배**

---

### 1.3 사전 컴파일된 패턴 활용

**변경 전** (lines 154-164):
```python
# 매번 정규식 재컴파일
if re.search(r'\b' + re.escape(known_table) + r'\b', cleaned_sql):
    table_names.add(known_table)
```

**변경 후** (lines 154-166):
```python
# 사전 컴파일된 패턴 재사용
if self._compiled_regex_patterns:
    pattern = self._compiled_regex_patterns.get(known_table)
    if pattern and pattern.search(cleaned_sql):
        table_names.add(known_table)
```

---

## 2. 중복 제거 작업

### 2.1 relationships 테이블 중복 관계 제거

**위치**: `consistency_validator.py:400-446`

**기능**:
- 같은 `(src_id, dst_id, rel_type)` 조합의 중복 관계 자동 감지
- 최소 `relationship_id`만 유지, 나머지는 `del_yn='Y'`로 삭제

**실행 시점**:
- 메타데이터 생성 완료 후 검증 단계 (`_check_warning_cases()`)

**코드**:
```python
def _remove_duplicate_relationships(self):
    """중복 관계 제거 (같은 src_id, dst_id, rel_type의 관계 중복 제거)"""
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

    # 최소 ID 제외 나머지 삭제
    for dup in duplicate_relationships:
        relationship_ids = [int(id_str) for id_str in dup['relationship_ids'].split(',')]
        keep_id = dup['keep_id']
        remove_ids = [rid for rid in relationship_ids if rid != keep_id]

        for remove_id in remove_ids:
            self.db_utils.execute_query("""
                UPDATE relationships
                SET del_yn = 'Y', updated_at = CURRENT_TIMESTAMP
                WHERE relationship_id = ?
            """, (remove_id,))
```

---

### 2.2 백엔드매핑 보고서 중복 표시 제거

**위치**: `reports/backend_mapping_report_generator.py:244-284`

**변경 내용**:
1. **SQL 쿼리에 DISTINCT 추가** (line 254)
2. **Python 레벨 중복 체크** (lines 272-280)

**변경 후 코드**:
```python
def _load_metadata_use_tables(self) -> Dict[str, List[Dict[str, str]]]:
    """metadata.db의 USE_TABLE 관계를 component_name 기준으로 맵으로 적재 (중복 제거)"""
    cursor.execute(
        """
        SELECT DISTINCT  -- DISTINCT 추가
               src.component_name AS sql_comp,
               dst.component_name AS table_name,
               COALESCE(t.table_owner, 'UNKNOWN') AS table_owner
        FROM relationships r
        ...
        """,
        (self.project_name,)
    )
    for comp_name, table_name, table_owner in cursor.fetchall():
        key = (comp_name or '').upper()
        # 중복 방지: 이미 같은 owner+table 조합이 있는지 확인
        existing_tables = meta_map.setdefault(key, [])
        table_info = {
            'owner': table_owner or 'UNKNOWN',
            'table': table_name or ''
        }
        # 동일한 테이블이 이미 있는지 확인
        if not any(t['owner'] == table_info['owner'] and t['table'] == table_info['table'] for t in existing_tables):
            existing_tables.append(table_info)
```

---

## 3. 종합 성능 예상

### 3.1 5천 개 테이블 환경 예상 개선 효과

| 최적화 항목 | 개선 배율 | 누적 효과 |
|------------|----------|----------|
| 정규식 사전 컴파일 | 3~5배 | 3~5배 |
| SQL 전처리 캐싱 | 1.5~2배 | 4.5~10배 |
| **종합 예상 효과** | - | **5~10배** |

### 3.2 실행 시간 예상

**기존**:
- 5,000 테이블 × 500 쿼리 = 2,500,000번 정규식 실행
- 예상 시간: **10~20분**

**개선 후**:
- 5,000개 패턴 사전 컴파일: **1회** (1~2초)
- 500 쿼리 × 5,000 패턴 검색: **캐싱된 정규식 재사용**
- 예상 시간: **2~4분** (**5~10배 개선**)

---

## 4. 메모리 사용량

| 캐시 종류 | 크기 | 제한 |
|----------|------|------|
| 정규식 패턴 캐시 | ~500KB (5,000개 × 100byte) | 테이블 개수만큼 |
| SQL 전처리 캐시 | ~10MB (10,000개 × 1KB) | 최대 10,000개 |
| **총 메모리 증가** | ~10.5MB | 허용 가능 수준 |

---

## 5. 검증 포인트

테스트 실행 시 확인할 항목:

### 5.1 성능 확인
- [ ] 정규식 패턴 사전 컴파일 로그 확인: `정규식 패턴 사전 컴파일 완료: 5000개`
- [ ] 전체 분석 시간 측정 (기존 대비 5~10배 개선 예상)
- [ ] SQL 전처리 캐싱 적중률 확인

### 5.2 중복 제거 확인
- [ ] relationships 중복 제거 로그: `중복 관계 제거 완료: N개 제거됨`
- [ ] 백엔드매핑 보고서에서 쿼리-테이블 중복 없음 확인
- [ ] relationships 테이블 쿼리:
```sql
SELECT src_id, dst_id, rel_type, COUNT(*) as cnt
FROM relationships
WHERE del_yn = 'N'
GROUP BY src_id, dst_id, rel_type
HAVING COUNT(*) > 1
-- 결과: 0 rows (중복 없음)
```

---

## 6. 주요 변경 파일

| 파일 | 변경 내용 | 라인 |
|------|----------|------|
| `util/sql_content_manager.py` | 정규식 패턴 사전 컴파일 함수 추가 | 770-789 |
| `util/sql_content_manager.py` | SQL 전처리 캐싱 로직 추가 | 791-831 |
| `util/sql_content_manager.py` | 사전 컴파일된 패턴 활용 로직 | 154-178 |
| `util/sql_content_manager.py` | 캐시 변수 초기화 | 36-37 |
| `consistency_validator.py` | 중복 관계 제거 함수 추가 | 400-446 |
| `consistency_validator.py` | 검증 단계에서 중복 제거 실행 | 451-452 |
| `reports/backend_mapping_report_generator.py` | USE_TABLE 쿼리에 DISTINCT 추가 | 254 |
| `reports/backend_mapping_report_generator.py` | Python 레벨 중복 체크 로직 | 272-280 |

---

## 7. 결론

✅ **성능 개선**: 5천 개 테이블 환경에서 5~10배 속도 향상 예상
✅ **중복 제거**: relationships 및 보고서에서 자동 중복 제거
✅ **메모리 효율**: 약 10MB 증가 (허용 가능 수준)
✅ **기존 로직 무영향**: 기존 로직 변경 없이 최적화 레이어만 추가

**다음 단계**:
1. 성능 테스트 완료 후 로그 확인
2. 실제 5천 개 테이블 환경에서 검증
3. 필요시 추가 최적화 (병렬 처리 등)
