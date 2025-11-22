

# Repository Guidelines (레포지토리 가이드라인)

## Project Structure & Module Organization (프로젝트 구조 및 모듈 조직)

- Loaders: `base_loading_engine.py` (common base), `file_loading.py`, `java_loading.py`, `xml_loading.py`, `frontend_loading.py` (ingest sources → components) (로드러: 공통 베이스 및 파일, 자바, XML, 프론트엔드 로더 (소스 → 컴포넌트))
- Parsers: `parser/` (SQL, Spring annotations, JSP/front, String.format SQL) (파서: `parser/` (SQL, 스프링 어노테이션, JSP/프론트, String.format SQL))
- Relationships: `relationship_builder.py` (Frontend→Method→Query→Table builders) (관계: `relationship_builder.py` (프론트엔드→메서드→쿼리→테이블 빌더))
- Utilities: `util/` (DB, path, hashing, API naming, mapper indexer, logging) (유틸리티: `util/` (DB, 경로, 해싱, API 명명, 매퍼 인덱서, 로깅))
- Reports: `reports/` (ERD, call-chain, architecture) (리포트: `reports/` (ERD, 호출 체인, 아키텍처))
- Database DDL: `database/` (metadata and SqlContent schemas) (데이터베이스 DDL: `database/` (메타데이터 및 SqlContent 스키마))
- **temp 폴더 용도**: `./temp` 디렉터리는 프로젝트 소스 코드를 직접 수정하지 않고, 임시 파이썬 스크립트를 작성·실행·검증하기 위한 공간입니다.
  - 임시 스크립트는 `temp` 안에만 두며, `.gitignore` 에 의해 Git에 포함되지 않으므로 커밋되지 않습니다.
  - 테스트가 끝나면 스크립트를 삭제하거나 `temp` 폴더를 비워 두어도 무방합니다.

## Build, Test, and Development Commands

- Run analyzer: `python main.py --project-name SampleSrc` (분석기 실행: `python main.py --project-name SampleSrc`)
- Generate reports: `python create_report.py --project-name SampleSrc` (리포트 생성: `python create_report.py --project-name SampleSrc`)
- Run tests: `pytest -q` (테스트 실행: `pytest -q`)
- Clean DBs: delete `projects/SampleSrc/metadata.db` and `projects/SampleSrc/SqlContent.db` (DB 정리: `projects/SampleSrc/metadata.db` 및 `projects/SampleSrc/SqlContent.db` 삭제)

### main.py 실행 파라미터 (소스 기준)

- `--project-name <이름>`: 필수. 분석 대상 프로젝트명. (`--project-name <name>`: required, target project name)
- `--clear-metadb`: 선택. 옵션 값은 읽지만, 현재 메인 플로우의 스키마 생성 분기에는 직접 연동되어 있지 않음. (`--clear-metadb`: optional, currently not directly linked to schema creation in main flow)
- `--verbose`: 선택. 상세 로그 출력(DEBUG 레벨 설정). (`--verbose`: optional, detailed log output (DEBUG level))
- `--dry-run`: 선택. 실제 분석을 수행하지 않고 설정만 확인 후 종료. (`--dry-run`: optional, validates settings without running analysis)
- `--help`, `-h`: 도움말 출력 후 종료. (`--help`, `-h`: display help and exit)

### main.py 개요 (소스 기준)

- 목적: 프로젝트 소스 분석 및 메타데이터 DB 구축 전 과정 오케스트레이션 (Purpose: orchestrate the entire process of source analysis and metadata DB construction)
- 주요 단계:
  - 로그 정리(24h 지난 파일 삭제), 재귀 제한 설정(50) (Log cleanup (delete files older than 24h), set recursion limit (50))
  - 인자 파싱/검증, 프로젝트 존재 여부 확인 (Argument parsing/validation, check project existence)
  - 메타데이터 DB 연결 및 스키마 생성 시도(`database/create_table_script.sql`) (Connect to metadata DB and attempt schema creation (`database/create_table_script.sql`))
  - 1단계: 파일 스캔 및 파일/컴포넌트 로드 (`FileLoadingEngine.execute_file_loading()`) (Step 1: file scan and component loading (`FileLoadingEngine.execute_file_loading()`))
  - 프로젝트 ID 조회 후 전역 설정 (Retrieve project ID and set global configuration)
  - 2단계: DB 구조 로드 (`FileLoadingEngine.execute_db_loading()`) (Step 2: load DB structure (`FileLoadingEngine.execute_db_loading()`))
  - 3단계: XML 분석 및 SQL/Join 로드 (`XmlLoadingEngine.execute_xml_loading()`) (Step 3: XML analysis and SQL/Join loading (`XmlLoadingEngine.execute_xml_loading()`))
  - 4단계: Java 분석 (`load_java_files_simple`) (Step 4: Java analysis (`load_java_files_simple`))
  - 5단계: 백엔드 API 진입점 분석 (`execute_backend_entry_loading`) (Step 5: backend API entry point analysis (`execute_backend_entry_loading`))
  - 6단계: 프론트엔드 분석 (`FrontendLoadingEngine.execute_frontend_loading`) 및 관계 구축(`RelationshipBuilder.build_all_relationships`) (Step 6: frontend analysis (`FrontendLoadingEngine.execute_frontend_loading`) and relationship building (`RelationshipBuilder.build_all_relationships`))
  - 7단계: DB 기반 관계 보강(`execute_db_relationship_backfill`) + 일관성 검증(`execute_consistency_validation`) (Step 7: DB-based relationship backfill (`execute_db_relationship_backfill`) and consistency validation (`execute_consistency_validation`))
- 실행 모드: 기본 Auto Commit 성격으로 단계별 진행, `--dry-run` 시 분석 미수행 (Execution mode: default Auto Commit, step‑wise execution; analysis skipped with `--dry-run`)

### create_report.py 개요 및 파라미터 (소스 기준)

- 목적: 메타데이터 DB 기반 리포트 HTML 생성 (Purpose: generate HTML reports based on metadata DB)
- 리포트 타입(`--report-type` / `-t`): `callchain`, `erd`, `erd-dagre`, `architecture`, `architecture-layer`, `sequence`, `query-list`, `all`(기본값) (Report types (`--report-type` / `-t`): `callchain`, `erd`, `erd-dagre`, `architecture`, `architecture-layer`, `sequence`, `query-list`, `all` (default))
- 필수: `--project-name` / `-p` (Required: `--project-name` / `-p`)
- 선택: `--output-dir` / `-o` (기본: `projects/{project}/report`), `--verbose` / `-v`, `--include-orphan`(ERD/ERD-dagre에서 고아 테이블 포함) (Optional: `--output-dir` / `-o` (default: `projects/{project}/report`), `--verbose` / `-v`, `--include-orphan` (include orphan tables in ERD/ERD-dagre))
- 전제: 프로젝트 디렉터리와 `metadata.db`가 존재해야 함 (Prerequisite: project directory and `metadata.db` must exist)
- 생성기: `reports/` 하위 각 Generator의 `generate_report()` 호출 (Generators: invoke `generate_report()` of each generator under `reports/`)
