# exception 개선안 요약

## 적용 사항
- **DB 커넥션 싱글톤화**: `util/database_utils.py`에서 동일한 DB 경로는 단일 인스턴스/커넥션만 사용하도록 변경해 잠금·PermissionError 가능성을 차단.
- **닫힌 커넥션 자동 복구**: `insert_or_replace_with_id()`가 `_ensure_connection`을 사용해 닫힌 커넥션을 즉시 재연결하도록 보강, `Cannot operate on a closed database` 방지.
- **안전 쿼리 헬퍼 추가**: `safe_query_single_value`로 결과 없음/None/IndexError를 사전에 방지하고, 예외 시 `handle_error()`로 즉시 종료.
- **안전 파일 삭제**: `safe_remove_file`을 도입해 DB/로그 파일 삭제 시 재시도 후 실패하면 `handle_error()`로 중단. `main.py`, `file_loading.py` 삭제 로직에 적용.
- **handle_error 일괄 적용**: 중복 관계 제거, getter/setter 정리, CSV/프로젝트 ID 조회, XML 로딩, CommonSqlAnalyzer 호출 등에서 경고·skip 대신 `handle_error()`로 종료하도록 수정.

## 예상 문제점 및 대응
- **XML 파일 1건 오류 시 전체 종료**: 요구사항에 따라 `handle_error()`로 중단되므로, 손상된 XML이 있으면 바로 종료된다. 필요 시 특정 환경에서만 continue하도록 플래그 도입을 검토.
- **로그 파일 잠금**: 오래된 로그 삭제도 `safe_remove_file`로 처리해 잠금 시 재시도 후 중단한다. 현재 세션 로그는 다른 파일명이므로 삭제 대상에 포함되지 않지만, 추가로 “현재 로그 파일은 스킵” 조건을 넣어도 된다.
- **공유 커넥션 전제**: 싱글톤 적용으로 연결 객체를 공유하므로, 외부에서 임의로 close하면 이후 작업이 실패한다. 커넥션 해제는 공용 종료 지점에서만 수행하도록 유지 필요.
- **에러 로그 중복 방지**: `handle_error()`에 위임해 중복 error 로그를 줄였고, 추가 정보가 필요하면 `custom_message`에만 담도록 했다.

## 권장 후속 조치
- XML 파싱 실패 시 continue 모드가 필요한 경우 옵션 플래그를 추가해 운영/개발 모드별로 동작을 분리.
- 로그 삭제 시 현재 실행 중인 로그 파일은 스킵하도록 예외 조건을 추가(추가 방어막).***
