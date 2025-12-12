# DB 커넥션 공통 가이드

## DatabaseUtils 싱글톤/커넥션 재사용
- 같은 `db_path`에 대해 `DatabaseUtils`는 **싱글톤 인스턴스**를 반환한다.
- `connect()`는 이미 열린 커넥션이면 재사용하고, 닫혔으면 자동 재연결한다.
- `get_persistent_connection()`으로 항상 동일 커넥션을 사용하고, 중간 `disconnect()`는 `force=True`일 때만 수행한다.
- 쿼리 실행(`execute_query`, `execute_update`) 시 내부에서 커넥션 유효성(`_ensure_connection`)을 확인해 닫힌 커넥션 오류를 방지한다.

## 파일 컨텍스트 사용 원칙
- `sql_content_manager.save_sql_content()`는 `file_context`가 설정되어 있어야 한다.
- 외부 로더는 호출 전에 `get_file_context_manager().push(...)`로 현재 파일 정보를 설정하고, 처리 완료 후 `pop()`으로 정리한다.

## sqltext 로더 사용 흐름 (최신)
- 위치: `sqltext_loading.py`
- 처리 단계:
  1) `projects/{project}/sqltext` 이하 모든 서브폴더 `*.sql` 재귀 스캔.
  2) `files` 테이블에 SQL 파일 저장 (`file_type='SQL'`, 경로는 프로젝트 기준 상대경로).
  3) `components`에 `component_type`을 쿼리 내용으로 추론하여 저장  
     (`SQL_SELECT/INSERT/UPDATE/DELETE/MERGE` 등, layer=`QUERY_FROM_SQLTEXT`, `component_name=파일명`).
  4) `SqlContent.db`에 SQL 본문 저장 (`query_id=파일명`, `file_id` 매핑, layer=`QUERY_FROM_SQLTEXT`).
- 매칭/리포트 시 `component_id` 기준으로 USE_TABLE/조인 정보를 조회하여, 동일한 쿼리 ID라도 파일별로 테이블이 섞이지 않도록 한다.
- 주의: DB 접근은 싱글톤 `DatabaseUtils`/`SqlContentManager`의 **지속 커넥션**을 사용하며, 커넥션을 임의로 닫지 않는다.

## 잠금/중복 방지
- INSERT 시 `INSERT OR IGNORE` 또는 upsert는 PK/UNIQUE(`project_id, file_id, component_name` 등)를 기준으로 멱등하게 처리한다.
- 싱글 사용자 환경을 전제로 잠금/PermissionError가 발생하면 개발 오류로 간주하고 `handle_error()`로 즉시 종료한다(재시도 없음).
- `insert_or_replace_with_id` 등은 `_ensure_connection`을 통해 닫힌 커넥션을 자동 재연결하고, 실패 시 중단한다.

## 로그/스로틀
- 반복 디버그 로그는 1초 주기 스로틀링(프론트엔드 로더)으로 콘솔 스팸을 줄이되, 스로틀된 로그는 로그 파일에 별도로 기록하여 추적성을 유지한다.
