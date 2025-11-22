# AGENTS.md

This file provides guidance to AI agents when working with code in this repository.

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
