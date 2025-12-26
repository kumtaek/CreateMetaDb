# 하드코딩 검사 결과

## consistency_validator.py - _fallback_table_relationship_builder()

### ✅ 범용적 구현 (하드코딩 없음)

| 항목 | 구현 방식 | 범용성 |
|------|----------|--------|
| **프로젝트명** | `self.project_name` 파라미터 사용 | ✅ 모든 프로젝트 대응 |
| **테이블명** | `tables` 테이블에서 동적 조회 | ✅ DB 데이터 기반 |
| **쿼리 ID** | XML에서 정규식으로 동적 추출 | ✅ 패턴 기반 |
| **파일 경로** | `PathUtils` + `project_name` 조합 | ✅ 크로스플랫폼 |
| **SQL 태그** | `['select', 'insert', 'update', 'delete']` | ✅ MyBatis 표준 |
| **컴포넌트 조회** | DB 쿼리로 동적 검색 | ✅ 데이터 기반 |

### 코드 예시

```python
# Line 556: 프로젝트명 동적 전달
xml_parser = XmlParser(project_name=self.project_name)

# Line 559: 프로젝트별 경로 동적 구성
project_source_path = path_utils.join_path(
    path_utils.project_root, "projects", self.project_name, "src"
)

# Line 569-574: 테이블명 DB에서 동적 조회
all_tables = self.db_utils.execute_query("""
    SELECT DISTINCT table_name
    FROM tables
    WHERE project_id = ? AND del_yn = 'N'
    ORDER BY LENGTH(table_name) DESC
""", (self.project_id,))

# Line 602: 쿼리 ID 정규식으로 동적 추출
query_pattern = r'<(?:select|insert|update|delete)\s+[^>]*id\s*=\s*["\']([^"\']+)["\']'
query_ids = re.findall(query_pattern, xml_content, re.IGNORECASE)

# Line 614-621: SQL 컴포넌트 동적 조회
sql_component = self.db_utils.execute_query("""
    SELECT component_id
    FROM components
    WHERE component_name = ?
      AND component_type LIKE 'SQL_%'
      AND del_yn = 'N'
    LIMIT 1
""", (query_id,))
```

## 🐛 수정한 버그

### Before (정의되지 않은 변수 사용)
```python
debug(f"이미 등록된 USE_TABLE 관계 스킵: {full_component_name} -> {table_name}")
debug(f"USE_TABLE 추가: {full_component_name} -> {table_name}")
```

### After (올바른 변수 사용)
```python
debug(f"이미 등록된 USE_TABLE 관계 스킵: {query_id} -> {table_name}")
debug(f"USE_TABLE 추가: {query_id} -> {table_name}")
```

## 테스트 스크립트 (temp/ 폴더)

테스트 스크립트에만 `project_name = "sampleSrc"` 하드코딩 존재 → **정상** (테스트 목적)

- `temp/test_comment_ignore.py`: Line 15
- `temp/check_fallback_result.py`: Line 14
- `temp/check_missing_use_table.py`: Line 15

## 결론

✅ **sampleSrc 특화 하드코딩 없음**
✅ **범용적 로직으로 개발됨**
✅ **모든 프로젝트에서 동작 가능**

- 테이블명, 쿼리 ID, 파일 경로 모두 동적 처리
- 프로젝트명 파라미터로 받아 처리
- 데이터베이스 기반 동적 조회
- 정규식 패턴 기반 추출
