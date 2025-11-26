# file_path = '', file_name = '' 에러 방지 개선 방안

## 📋 문제 요약

**DDL 변경**: `file_path`, `file_name`에 `NOT NULL` 제약조건 추가
**문제**: `java_loading.py`에서 빈 문자열로 INSERT 시도 시 에러 발생

---

## 🔍 근본 원인

### 파일: `java_loading.py` Line 228-238

```python
file_path = ''  # ❌ 초기값이 빈 문자열
file_name = ''  # ❌ 초기값이 빈 문자열

if file_id:
    rows = self.db_utils.execute_query(
        "SELECT file_path, file_name FROM files WHERE file_id = ? AND del_yn='N'",
        (file_id,),
        conn=self.conn
    )
    if rows:
        file_path = rows[0].get('file_path', '') or ''
        file_name = rows[0].get('file_name', '') or ''
    # ❌ else 블록 없음!
```

**문제**:
- `file_id`가 존재하지만 `files` 테이블에서 조회 결과가 없으면
- `file_path = ''`, `file_name = ''` 상태 유지
- SqlContent.db INSERT 시 NOT NULL 제약조건 위반

---

## ✅ 개선 방안 1: file_id 유효성 검증 강화 (권장)

### 수정 위치: `java_loading.py` Line 228-242

```python
def _process_collected_queries(self, project_id: int):
    """Process all collected SQL queries by saving them to SqlContent.db"""
    info(f"Collected SQL queries: {len(self.collected_sql_queries)} → saving to SqlContent.db")
    if not self.sql_content_manager or not self.sql_content_manager.initialized:
        handle_error(Exception("SQL Content Manager not initialized"), "SQL Content Manager가 초기화되지 않아 쿼리 처리를 건너뜁니다.")

    try:
        for query_data in self.collected_sql_queries:
            # 파일 컨텍스트 세팅: 저장 대상 쿼리가 속한 파일 기준
            file_id = query_data.get('file_id')
            
            # ✅ file_id 필수 체크
            if not file_id:
                handle_error(
                    Exception("file_id missing in collected query"), 
                    f"SQL content save failed: file_id 누락, query_id={query_data.get('query_id', 'unknown')}"
                )
                continue  # ✅ 해당 쿼리 스킵하고 다음으로
            
            # ✅ files 테이블에서 파일 정보 조회
            rows = self.db_utils.execute_query(
                "SELECT file_path, file_name FROM files WHERE file_id = ? AND del_yn='N'",
                (file_id,),
                conn=self.conn
            )
            
            # ✅ 조회 결과 검증
            if not rows:
                handle_error(
                    Exception(f"file_id {file_id}에 해당하는 파일 정보 없음"),
                    f"SQL content save failed: query_id={query_data.get('query_id', 'unknown')}"
                )
                continue  # ✅ 해당 쿼리 스킵하고 다음으로
            
            # ✅ file_path, file_name 추출 및 검증
            file_path = rows[0].get('file_path', '') or ''
            file_name = rows[0].get('file_name', '') or ''
            
            # ✅ 빈 문자열 검증 (NOT NULL 제약조건 대비)
            if not file_path or not file_name:
                handle_error(
                    Exception(f"file_path 또는 file_name이 비어있음: file_id={file_id}"),
                    f"SQL content save failed: query_id={query_data.get('query_id', 'unknown')}"
                )
                continue  # ✅ 해당 쿼리 스킵하고 다음으로
            
            # 컨텍스트 push
            self.file_context.push(
                project_name=self.project_name,
                project_id=project_id,
                file_id=file_id,
                file_path=file_path,
                file_name=file_name,
                file_type='JAVA',
                source_type='JAVA',
                stage='Java-SQLSave'
            )
            try:
                self.sql_content_manager.save_sql_content(conn=self.conn, **query_data)
            finally:
                self.file_context.pop()
    except Exception as e:
        handle_error(e, "SQL content save failed")
```

**개선 효과**:
1. ✅ `file_id`가 없으면 즉시 스킵
2. ✅ `files` 테이블 조회 결과가 없으면 즉시 스킵
3. ✅ `file_path` 또는 `file_name`이 빈 문자열이면 즉시 스킵
4. ✅ NOT NULL 제약조건 위반 방지
5. ✅ 에러 발생 시 해당 쿼리만 스킵하고 나머지는 계속 처리

---

## ✅ 개선 방안 2: sql_content_manager.py에서 검증 (추가 방어)

### 수정 위치: `util/sql_content_manager.py` Line 166-176

```python
def save_sql_content(self, sql_content: str, project_id: int, conn=None, **kwargs) -> bool:
    try:
        # ... (기존 코드)
        
        # ✅ file_path, file_name 검증 추가
        file_path = kwargs.get('file_path')
        file_name = kwargs.get('file_name')
        
        if not file_path or not file_name:
            handle_error(
                Exception("file_path 또는 file_name이 비어있음"),
                f"SQL content save failed: query_id={kwargs.get('query_id', 'unknown')}"
            )
            return False
        
        # 3. SQL Content 저장 (SqlContent.db)
        sql_content_data = {
            'project_id': project_id,
            'file_id': kwargs.get('file_id'),
            'component_id': component_id,
            'sql_content_compressed': compressed_content,
            'file_path': file_path,  # ✅ 검증된 값
            'component_name': kwargs.get('query_id', kwargs.get('component_name', '')),
            'file_name': file_name,  # ✅ 검증된 값
            'hash_value': kwargs.get('hash_value'),
            'del_yn': 'N'
        }
        
        # ... (기존 코드)
```

**개선 효과**:
- ✅ 2차 방어선: `java_loading.py`에서 누락되어도 여기서 차단
- ✅ NOT NULL 제약조건 위반 방지

---

## 📊 수정 우선순위

| 순위 | 파일 | 라인 | 내용 | 중요도 |
|------|------|------|------|--------|
| 1 | `java_loading.py` | 228-242 | file_id 유효성 검증 강화 | ⭐⭐⭐ 필수 |
| 2 | `sql_content_manager.py` | 166-176 | file_path/file_name 검증 추가 | ⭐⭐ 권장 |

---

## 🔧 테스트 방법

1. **기존 DB 초기화**:
   ```bash
   del projects\sampleSrc\SqlContent.db
   ```

2. **분석 재실행**:
   ```bash
   python main.py --project-name sampleSrc
   ```

3. **에러 로그 확인**:
   - `file_id 누락` 에러가 로그에 기록되는지 확인
   - `file_id에 해당하는 파일 정보 없음` 에러 확인
   - `file_path 또는 file_name이 비어있음` 에러 확인

4. **SqlContent.db 검증**:
   ```sql
   SELECT COUNT(*) FROM sql_contents 
   WHERE file_path = '' OR file_name = '';
   -- 결과: 0 (빈 문자열 없어야 함)
   ```

---

## 📝 추가 고려사항

### Q: 왜 `files` 테이블에서 조회 결과가 없을 수 있나?

**가능한 원인**:
1. `file_id`가 잘못 설정됨 (다른 프로젝트의 file_id)
2. `files` 테이블에 파일이 등록되지 않음
3. `del_yn = 'Y'`로 삭제된 파일

**해결책**:
- `java_loading.py`의 `_get_file_id` 메서드 검증 강화
- 파일 등록 로직 확인 (`file_loading.py`)

### Q: `file_path` 또는 `file_name`이 NULL인 경우는?

**현재 상황**:
- `files` 테이블에는 `file_path`, `file_name`이 NOT NULL
- 따라서 조회 결과가 있으면 항상 값이 존재함

**하지만**:
- `rows[0].get('file_path', '') or ''` 로직 때문에
- NULL이 아니라 빈 문자열일 수 있음

**개선**:
```python
file_path = rows[0].get('file_path')
file_name = rows[0].get('file_name')

if not file_path or not file_name:
    # 에러 처리
```
