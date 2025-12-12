# 지침

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 필수 지침은 숙지해서 개발하자.
- **중복 기능 개발 금지**: 기존에 개발된 함수가 있는지 확인해보고, 동일 기능의 소스를 중복해서 개발하지 말 것.  공통화 할 수 있는 부분은 함수화 할 것. 불필요한 소스를 작성하지 않고 효율적인 리팩토링에 신경쓸 것.
- **유추해서 개발 금지**: 확실하게 소스 및 데이터를 확인하여 로직 구현할 것!!! 확인 없이 유추해서 상상 코딩 개발 절대 금지!!!
- **주석, docstring 작성**: 한글로 함수, 클래스, 모듈에 대한 주석, docstring 작성
- **하드코 절대 금지**: 하드코딩된 값이 있는지 확인해보고, 하드코딩된 값을 사용하지 말 것. 특히 sampleSrc이 샘플임을 명심하여 sampleSrc의 특화된 로직을 개발하지 않고 범용적인 로직을 개발할 것!!!
- **크로스플랫폼 대응**: Windows/Unix 환경에서 동일하게 실행되도록 개발할 것.  특히 경로 처리할때 주의.
- **인터넷불가 폐쇄망 사용 가능하도록 개발**: 인터넷망에서 개발하지만 운영은 폐쇄망에서도 실행 가능하도록 개발되어야 함
- **Exception발생시 중지**: Exception 발생시 에러로그 후 중지 -> error_handle()호출
- **메타디비 구조 절대 변경 금지**: 메타디비 구조 변경은 승인받고 변경해야 함.
- **PowerShell 명령 작성 주의**: bash heredoc(`python - <<'PY'`)을 사용하지 말고, PowerShell에서는 `@'... '@ | python -` 패턴을 사용해 스크립트를 전달할 것(구문 오류/시간 낭비 방지).
- **전역 실행 옵션 사용**: `--sql-compress` 등 런타임 플래그는 `util.runtime_options` 전역 객체를 통해 관리하고, 가능한 한 함수 인자 반복 전달을 피할 것.
- **개발 완료 후 컴파일해서 신택스 체크 필수**

## DDL 스키마 변경 절대 금지
- **database/ 폴더의 DDL 파일은 읽기 전용**: `create_table_script.sql`, `create_sql_content_db.sql` 파일은 읽기 전용(Read-Only) 속성이며, 절대 수정하지 말 것
- **스키마 변경 금지 이유**: 테이블 구조 변경은 기존 데이터 마이그레이션, 정규화 위배, 다른 모듈 영향도 분석이 필요하므로 반드시 별도 검토 후 진행
- **읽기 전용 속성 해제 금지**: `attrib -R` 등으로 읽기 전용 속성을 임의로 해제하지 말 것
- **리포트 생성기 원칙**: 리포트 생성 로직은 SQL 재파싱 없이 메타DB(metadata.db, SqlContent.db)에 저장된 데이터만 조회하여 사용할 것. 핵심 분석 로직은 메타DB 생성 단계에서 처리

## 프로젝트 개요

SourceAnalyzer는 Java/Spring/MyBatis 기반 웹 애플리케이션의 소스코드를 분석하여 **프론트엔드 -> 백엔드 -> 데이터베이스**까지의 완전한 연관관계를 도출하는 메타데이터 분석 시스템입니다.

## 프로젝트 구조

- **엔트리**: `main.py`가 전체 분석 파이프라인을 오케스트레이션 (파일 스캔 -> DB 스키마 로드 -> XML -> Java -> 백엔드 엔트리 -> 프론트엔드 -> 관계 백필 -> 일관성 검증)
- **로더**: `file_loading.py`, `xml_loading.py`, `java_loading.py`, `frontend_loading.py`, `backend_entry_loading.py`, `relationship_builder.py`, 공통 베이스 `util/base_loading_engine.py`
- **파서**: `parser/` (SQL, Spring annotations, JSP/front, MyBatis XML)
- **유틸리티**: `util/` (DB, path, hashing, API naming, mapper indexer, logging)
- **리포트**: `reports/` (ERD, call-chain, architecture, sequence, query-list)
- **DDL**: `database/` (metadata.db, SqlContent.db 스키마)
- **데이터/산출물**: `projects/{name}/`에 `src/`, `db_schema/`(CSV), `config/`, `metadata.db`, `SqlContent.db`, `report/`

### 작업 규칙
- **임시 파일**: 반드시 `temp/` 폴더에만 생성 (`.gitignore`에서 제외됨)
- **백업**: `backup/` 폴더
- **로그**: `logs/` 폴더 (24시간 경과 파일 자동 삭제)
- 폴더 구조를 임의로 변경하지 말 것

## 빌드/테스트/개발 명령

```bash
# 가상환경 설정
python -m venv .venv && .\.venv\Scripts\activate

# 의존성 설치
pip install -r requirements-dev.txt

# 분석 실행 (필수: --project-name)
python main.py --project-name sampleSrc               # 기본 실행
python main.py --project-name sampleSrc --verbose     # 상세 로그 (DEBUG)
python main.py --project-name sampleSrc --clear-metadb  # 메타DB 초기화
python main.py --project-name sampleSrc --dry-run     # 설정 검증만

# 리포트 생성 (필수: --project-name)
python create_report.py --project-name sampleSrc                    # 모든 리포트 (기본)
python create_report.py --project-name sampleSrc --report-type erd  # 특정 리포트
# 리포트 타입: callchain, erd, erd-dagre, architecture, architecture-layer, sequence, query-list, all
# 옵션: --output-dir, --verbose, --include-orphan (ERD에서 고아 테이블 포함)

# 테스트 실행
pytest temp                                  # 회귀 테스트
pytest --maxfail=1 --disable-warnings -q     # 스모크 테스트
pytest --cov=. --cov-report=term-missing     # 커버리지 확인

# DB 초기화 (수동)
del projects\sampleSrc\metadata.db projects\sampleSrc\SqlContent.db
```

## 7단계 분석 파이프라인

| 단계 | 모듈 | 역할 |
|------|------|------|
| 1단계 | `file_loading.py` | 프로젝트 파일 스캔 -> `files` 테이블 등록 |
| 2단계 | `file_loading.py` | CSV에서 DB 스키마 로드 -> `tables`/`columns` 등록 |
| 3단계 | `xml_loading.py` | MyBatis XML 파싱 -> SQL 컴포넌트/JOIN 관계 생성 |
| 4단계 | `java_loading.py` | Java 클래스/메서드 추출 -> `classes`/`components` 등록 |
| 5단계 | `backend_entry_loading.py` | Spring/Servlet API 진입점 분석 -> `API_URL` 생성 |
| 6단계 | `frontend_loading.py` + `relationship_builder.py` | 프론트엔드 API 호출 분석 + 관계 구축 |
| 7단계 | `consistency_validator.py` | DB 기반 관계 보강 + 데이터 무결성 검증 |

## 코딩 스타일/네이밍

- Python 3 / PEP 8, 4스페이스 인덴트
- `lower_snake_case` 함수/변수, `UpperCamelCase` 클래스
- 타입힌트와 docstring 권장
- 로깅: `util.logger.app_logger`의 `info`/`warning`/`error`/`handle_error` 사용, print 지양
- 기존 한영 혼용 로그 톤 유지
- 경로 처리: `PathUtils().normalize_path_separator(..., 'unix')` (항상 `/` 구분자)
- DB 저장: `INSERT OR IGNORE` (멱등성 보장)

## 테스트 가이드

- 프레임워크: `pytest`, 파일/함수 이름은 `test_` 접두어
- 중점 케이스: XML/Java 파싱, 경로 정규화, DB 기록/관계 백필, 리포트 생성기 입출력
- 데이터: `projects/`의 경량 샘플 활용, 대용량 픽스처는 커밋 금지

## 커밋/PR 가이드

- 메시지: 명령형/범위 명시 (예: `Add XML SAX fallback logging`, `Refine frontend relationship builder`)
- 커밋 전 `pytest temp` 실행
- `temp/`, `logs/`, 샘플 DB 파일은 커밋하지 말 것

## 지원 기술

### 백엔드
- Java 클래스/메서드, StringBuilder SQL 추출
- Spring Framework (@Controller, @RequestMapping, @RestController)
- MyBatis XML (DOM + SAX Fallback)
- JPA (@Entity, @Repository, @Query)

### 프론트엔드
- JSP, JSX, Vue, TypeScript, JavaScript, HTML
- HTTP 클라이언트: jQuery, Axios, Fetch API, XMLHttpRequest, Vue Resource

### SQL
- Oracle EXPLICIT/IMPLICIT JOIN 분석
- 테이블/컬럼 추출, 별칭 해석
