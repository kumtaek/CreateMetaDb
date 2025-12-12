# WHERE, ON 여러번 나오는 경우, 인라인뷰 알리아스 조인조건 도출 개선

## 배경
- 기존 `CommonSqlAnalyzer._extract_join_relationships`는 **단일 ON/WHERE** 절만 처리했으며, 인라인 뷰(alias)와 별칭 없는 컬럼에 대한 조인 조건을 놓쳤습니다.
- `MERGE` 구문 내부 `USING (SELECT ...)` 와 같이 **서브쿼리**가 여러 번 등장하면 조인 조건이 누락되는 현상이 있었습니다.

## 주요 개선 사항
1. **통합 조인 추출 로직** (`_extract_join_relationships`) 구현
   - `table.column = table.column` (양쪽 모두 별칭),
   - `column = table.column` (왼쪽 별칭 없음),
   - `table.column = column` (오른쪽 별칭 없음) 세 패턴을 정규식으로 한 번에 탐색.
   - 중복 제거를 위해 `seen` 집합 사용.
2. **인라인 뷰 컬럼 매핑**
   - `_build_inline_view_column_map` : `SELECT` 절을 파싱해 `alias -> {col: original_table.column}` 매핑 생성.
   - `_parse_select_columns` 로 `SELECT` 구문에서 컬럼 리스트를 추출.
   - `_resolve_column_with_inline_view` 로 별칭이 인라인 뷰인 경우 실제 테이블·컬럼으로 역추적.
3. **별칭 없는 컬럼 처리**
   - `_find_table_for_column` 활용해 메타DB(`columns` 테이블)에서 컬럼을 소유한 테이블을 추론.
   - 후보 테이블 리스트(`candidate_tables`)는 현재 쿼리에서 사용된 실제 테이블만 포함.
4. **조인 타입 추정** (`_guess_join_type`)
   - `MERGE`, `INSERT ... SELECT`, `SELECT ... FROM` 등에서 조인 유형을 자동 판단.
5. **조인 조건 생성** (`_create_join_condition`)
   - 중복 방지, Oracle 키워드/리터럴 제외, `JOIN` 타입 메타데이터 저장.

## 코드 위치
- `D:/Analyzer/CreateMetaDb/util/common_sql_processor.py` 에서 504~595 라인에 구현되었습니다.
- 헬퍼 메서드 5개는 597~601 라인에 삽입되었습니다.

## 테스트 방법
```bash
# 메타DB 재생성
python main.py --project-name sampleSrc --clear-metadb --verbose

# 조인 관계 확인 (예시: ORDERS, ORDER_SUMMARY)
python temp/check_join_in_db.py
```
- 결과는 `temp/join_check_result.txt` 에 저장됩니다.
- `mergeOrderSummary` 의 `MERGE` 구문에서 `src.user_id = dst.user_id` 와 같은 조인 조건이 정상적으로 추출되는지 확인.

## 현재 상태
- **JOIN 관계 추출 건수**: 290개 (로그 `java_loading` 단계에 기록).
- `mergeOrderSummary` 에 대한 조인 조건이 메타DB에 정상 저장됨.
- 인라인 뷰(`v1`) 컬럼이 실제 테이블(`t2`)와 매핑되어 조인 조건이 생성됩니다.

## 남은 작업 (선택 사항)
- **중첩 인라인 뷰** 지원: 현재는 단일 인라인 뷰만 처리합니다. -> 괄호를 다 풀어서 조인조건 도출해내도록 구현 가능???
- **`SELECT *`** 구문 지원: 컬럼 리스트를 명시적으로 파싱하도록 개선 필요???

---
*이 문서는 최신 커밋을 기준으로 작성되었습니다.*
