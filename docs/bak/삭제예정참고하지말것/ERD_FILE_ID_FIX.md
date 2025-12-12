# ERD 생성 오류 수정 - file_id 컬럼 참조 제거

## 문제 발생

ERD 리포트 생성 시 SQL 오류 발생:

```
sqlite3.OperationalError: no such column: t.file_id
sqlite3.OperationalError: no such column: f.file_type
```

## 원인 분석

### tables 테이블 스키마

```sql
CREATE TABLE tables (
    table_id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    component_id INTEGER,          -- 있음
    table_name VARCHAR(100) NOT NULL,
    table_owner VARCHAR(50) NOT NULL,
    table_comments TEXT,
    hash_value VARCHAR(64) NOT NULL,
    created_at DATETIME DEFAULT datetime('now', '+9 hours'),
    updated_at DATETIME DEFAULT datetime('now', '+9 hours'),
    del_yn CHAR(1) DEFAULT 'N'
    -- file_id 컬럼 없음!
);
```

**문제**: `tables` 테이블에 `file_id` 컬럼이 존재하지 않음
**이유**: 테이블 정보는 CSV에서 로드되므로 file_id가 필요 없음

### 잘못된 SQL (erd_metadata_service.py)

#### 1. 라인 189: get_all_tables_with_columns
```sql
LEFT JOIN files f ON t.file_id = f.file_id  -- ✗ t.file_id 없음
```

#### 2. 라인 522: get_tables_with_columns_by_relationships
```sql
LEFT JOIN files f ON t.file_id = f.file_id  -- ✗ t.file_id 없음
SELECT f.file_type                          -- ✗ files 테이블 JOIN 안됨
```

#### 3. 라인 254, 271: _get_tables_with_relationships
```sql
CASE WHEN f.file_type != 'CSV' THEN 1 ELSE 0 END  -- ✗ files 테이블 참조
```

## 해결 방법

### 1단계: file_id JOIN 제거

**파일**: `reports/erd_metadata_service.py`

#### 수정 1 (라인 186-190)
```sql
-- 변경 전
FROM tables t
LEFT JOIN columns c ON t.table_id = c.table_id AND c.del_yn = 'N'
JOIN projects p ON t.project_id = p.project_id
LEFT JOIN files f ON t.file_id = f.file_id AND f.del_yn = 'N'  -- ✗ 제거
WHERE p.project_name = ? AND t.del_yn = 'N'

-- 변경 후
FROM tables t
LEFT JOIN columns c ON t.table_id = c.table_id AND c.del_yn = 'N'
JOIN projects p ON t.project_id = p.project_id
WHERE p.project_name = ? AND t.del_yn = 'N'  -- ✓ JOIN 제거
```

#### 수정 2 (라인 519-523)
```sql
-- 변경 전
FROM tables t
JOIN columns c ON t.table_id = c.table_id
JOIN projects p ON t.project_id = p.project_id
LEFT JOIN files f ON t.file_id = f.file_id AND f.del_yn = 'N'  -- ✗ 제거
WHERE p.project_name = ?

-- 변경 후
FROM tables t
JOIN columns c ON t.table_id = c.table_id
JOIN projects p ON t.project_id = p.project_id
WHERE p.project_name = ?  -- ✓ JOIN 제거
```

### 2단계: file_type 컬럼 참조 수정

#### 수정 3 (라인 177)
```sql
-- 변경 전
SELECT
    t.table_name,
    t.table_owner,
    t.table_comments,
    f.file_type,  -- ✗ files 테이블 없음

-- 변경 후
SELECT
    t.table_name,
    t.table_owner,
    t.table_comments,
    NULL as file_type,  -- ✓ NULL 반환
```

#### 수정 4 (라인 510)
```sql
-- 변경 전
SELECT
    t.table_name,
    t.table_owner,
    t.table_comments,
    f.file_type,  -- ✗ files 테이블 없음
    c.column_name,

-- 변경 후
SELECT
    t.table_name,
    t.table_owner,
    t.table_comments,
    NULL as file_type,  -- ✓ NULL 반환
    c.column_name,
```

#### 수정 5 & 6 (라인 254, 271)
```sql
-- 변경 전
CASE WHEN f.file_type != 'CSV' THEN 1 ELSE 0 END as is_inferred

-- 변경 후
0 as is_inferred  -- ✓ 모두 추론되지 않은 것으로 처리
```

**참고**: `is_inferred` 플래그는 현재 사용되지 않으므로 0으로 고정

## 테이블 vs 컴포넌트

### 데이터 흐름 이해

```
파일 분석 → components 테이블 (file_id 보유)
             ↓
       테이블 추출
             ↓
       tables 테이블 (component_id 보유, file_id 없음)
```

### 관계

- **components**: SQL 컴포넌트 (쿼리, 테이블, 컬럼 등) - `file_id` 보유
- **tables**: 테이블 메타데이터 (CSV에서 로드) - `component_id` 보유, `file_id` 없음

**결론**: tables 테이블은 files 테이블과 직접 관계가 없음

## 검증 결과

### Mermaid ERD (erd)
```bash
python create_report.py --project-name sampleSrc --report-type erd
```
✓ 생성 성공: `[sampleSrc]_ERD_20251126_154735.html`

### Cytoscape ERD (erd-dagre)
```bash
python create_report.py --project-name sampleSrc --report-type erd-dagre
```
✓ 생성 성공: `[sampleSrc]_ERD_Dagre_20251126_154817.html`

### 확인 사항
- ✓ SQL 오류 없음
- ✓ 26개 테이블 정상 조회
- ✓ 관계 정보 정상 표시
- ✓ 레이아웃 개선 사항 반영됨

## 영향 범위

### 수정된 파일
- `reports/erd_metadata_service.py` (6곳 수정)

### 영향받는 기능
- ✓ ERD Report (Mermaid)
- ✓ ERD Dagre Report (Cytoscape)

### 영향 없는 기능
- ✓ 다른 리포트 (CallChain, Architecture, Sequence 등)
- ✓ 메타DB 생성 로직
- ✓ 분석 엔진

## 근본 원인

### 왜 이런 오류가 발생했나?

1. **초기 설계**: 테이블 정보를 `files`에서 추출하도록 설계
2. **변경**: CSV에서 테이블 스키마를 별도로 로드하도록 변경
3. **미반영**: ERD 생성 로직에서 `files` 테이블 참조 제거 안됨

### 향후 방지책

1. **스키마 검증**: 리포트 생성 전 테이블 스키마 확인
2. **테스트 강화**: ERD 생성 테스트 추가
3. **문서화**: 테이블 간 관계 명확히 문서화

## 관련 문서

- `temp/ERD_MERMAID_LAYOUT_FIX.md`: Mermaid ERD 레이아웃 개선
- `temp/ERD_LAYOUT_IMPROVEMENT.md`: Cytoscape ERD 레이아웃 개선
- 현재 문서: ERD 생성 오류 수정

## 수정 일시

2025-11-26 15:48 KST
