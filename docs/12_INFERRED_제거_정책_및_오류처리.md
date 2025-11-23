# INFERRED 제거 정책 및 오류 처리 가이드

## 1. 배경
- 과거: 원본 파일을 찾지 못하면 `inferred/xxx.inferre` 같은 가짜 파일을 생성해 컴포넌트를 이어붙였다.
- 문제: 출처 불명 데이터, DB 락/무결성 문제, 디버깅 불가.
- 현재: **inferred 파일/컴포넌트 생성 금지**. 출처가 없으면 즉시 실패로 전환.

## 2. 정책 요약
- **파일 미발견 시 즉시 예외**: 어떤 단계에서든 파일을 찾지 못하면 프로세스를 중단하고 로그로 원인 노출.
- **실제 `file_id` 필수**: 모든 컴포넌트/관계/SQL 저장 시 `file_id`를 포함. 대체 파일명 사용 금지.
- **컨텍스트 기반 저장**: `require_current_file()` 검증 실패 시 저장하지 않고 종료.

## 3. 구현 포인트 (현재 소스 기준)
- `util/file_context.py`: 컨텍스트 스택으로 파일 출처 관리. 미설정 시 `ContextError` 발생.
- `util/sql_content_manager.py`: SQL 저장 시 컨텍스트 필수, inferred 파일 자동 생성 로직 제거.
- `parser/common_sql_analyzer.py` & `util/common_sql_processor.py`: 테이블/컬럼/관계 생성 시 컨텍스트가 없으면 런타임 예외. 누락된 테이블은 현재 파일의 `file_id`로 생성하며, inferred 파일을 만들지 않는다.
- `xml_loading.py`, `java_loading.py`, `frontend_loading.py`: 각 파일 처리 시작/종료에 `push_file`/`pop_file` 적용.

## 4. 오류 발생 시 조치
1. **컨텍스트 오류**: "현재 파일 컨텍스트가 설정되지 않았습니다"  
   - 해당 단계 로더에서 `push_file` 호출 여부 확인.
   - 1단계 파일 스캔에서 파일이 등록되었는지 metadata.db의 `files` 테이블 확인.
2. **테이블/컴포넌트 누락**: 예: `[CommonSqlAnalyzer] 테이블 컴포넌트 누락`  
   - 해당 쿼리가 나온 원본 파일 컨텍스트가 유지되는지 확인.
   - 실제 스키마에 없는 경우라도 inferred 파일을 만들지 말고, 현재 파일의 `file_id`로 컴포넌트를 생성하거나 스키마 CSV를 보완한다.
3. **DB 락 의심**: 분석 실패 시 로그 타임스탬프 기준으로 병행 실행 여부, 파일 핸들 미정리 여부 점검. `pop_file()` 누락이 없는지 확인.

## 5. 개발 가이드
- 신규 로직 추가 시 **inferred 대체물**을 만들지 말고, 컨텍스트 상의 실제 파일만 사용한다.
- 파일이 없다면 로직을 멈추고 원인(파일 스캔 누락, 경로 정규화 오류 등)을 수정한다.
- 크로스플랫폼 경로는 항상 `/` 구분자(`PathUtils.normalize_path_separator(..., 'unix')`).
- 주석/Docstring을 한글로 남기고, 중복 기능을 만들지 말고 공용 유틸을 재사용한다.
