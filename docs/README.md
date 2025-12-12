# SourceAnalyzer 문서 가이드

SourceAnalyzer 프로젝트의 전체 문서를 체계적으로 안내하는 통합 가이드입니다.

## 빠른 시작

### 역할별 권장 문서

| 역할 | 시작 문서 | 다음 문서 |
|------|-----------|-----------|
| **신규 투입 개발자** | [00_신규투입_개발자_스타트가이드.md](./00_신규투입_개발자_스타트가이드.md) | [01_시스템_요구사항_정의서.md](./01_시스템_요구사항_정의서.md) |
| **아키텍트/설계자** | [01_시스템_요구사항_정의서.md](./01_시스템_요구사항_정의서.md) | [03_처리_플로우_개요.md](./03_처리_플로우_개요.md) |
| **유지보수 담당자** | [03_처리_플로우_개요.md](./03_처리_플로우_개요.md) | 단계별 구현서 (04~10) |
| **리포트 생성/분석** | [20_리포트생성_구현서.md](./20_리포트생성_구현서.md) | [01_시스템_요구사항_정의서.md](./01_시스템_요구사항_정의서.md) |

### 5분 빠른 시작

```bash
# 1. 환경 설정
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements-dev.txt

# 2. 분석 실행
python main.py --project-name sampleSrc --verbose

# 3. 리포트 생성
python create_report.py --project-name sampleSrc

# 4. 리포트 확인
# projects/sampleSrc/report/ 폴더에서 HTML 파일 열기
```

## 문서 구조

### 핵심 문서 (필수 읽기)

| 문서 | 설명 | 대상 |
|------|------|------|
| [00_신규투입_개발자_스타트가이드.md](./00_신규투입_개발자_스타트가이드.md) | 프로젝트 빠른 시작 가이드 | 모든 신규 개발자 |
| [01_시스템_요구사항_정의서.md](./01_시스템_요구사항_정의서.md) | 전체 시스템 요구사항 및 9단계 파이프라인 개요 | 모든 개발자 |
| [02_데이터베이스_스키마_정의서.md](./02_데이터베이스_스키마_정의서.md) | metadata.db, SqlContent.db 스키마 정의 | DB 작업자 |
| [03_처리_플로우_개요.md](./03_처리_플로우_개요.md) | 9단계 분석 파이프라인 상세 처리 흐름 | 모든 개발자 |

### 단계별 구현서 (상세 구현)

SourceAnalyzer의 9단계 분석 파이프라인에 대한 상세 구현 문서입니다.

| 단계 | 문서 | 모듈 | 설명 |
|------|------|------|------|
| **1단계** | [04_1단계_파일_스캔_구현서.md](./04_1단계_파일_스캔_구현서.md) | `file_loading.py` | 프로젝트 파일 스캔 및 files 테이블 등록 |
| **2단계** | [05_2단계_DB_구조_저장_구현서.md](./05_2단계_DB_구조_저장_구현서.md) | `file_loading.py` | CSV에서 DB 스키마 로드 (tables/columns) |
| **2-1단계** | - | `sqltext_loading.py` | sqltext 폴더 SQL 파일 로딩 |
| **3단계** | [06_3단계_XML_분석_구현서.md](./06_3단계_XML_분석_구현서.md) | `xml_loading.py` | MyBatis XML 파싱 및 SQL 컴포넌트 생성 |
| **4단계** | [07_4단계_Java_분석_구현서.md](./07_4단계_Java_분석_구현서.md) | `java_loading.py` | Java 클래스/메서드 추출 |
| **4-1단계** | - | `sqltext_java_matcher.py` | sqltext SQL과 Java 문자열 매칭 |
| **5단계** | [08_5단계_API_매핑_구현서.md](./08_5단계_API_매핑_구현서.md) | `backend_entry_loading.py` | Spring/Servlet API 진입점 분석 |
| **6단계** | [09_6단계_프론트엔드_분석_구현서.md](./09_6단계_프론트엔드_분석_구현서.md) | `frontend_loading.py` | 프론트엔드 API 호출 분석 및 관계 구축 |
| **7단계** | [10_7단계_일관성_검증_구현서.md](./10_7단계_일관성_검증_구현서.md) | `consistency_validator.py` | DB 기반 관계 보강 및 무결성 검증 |

### 공통 모듈 구현서

| 문서 | 설명 | 관련 모듈 |
|------|------|-----------|
| [07.SQL공통파서_구현서.md](./07.SQL공통파서_구현서.md) | SQL 파서 공통 로직 (Oracle, ANSI) | `parser/sql_parser.py` |

### 리포트 생성

| 문서 | 설명 | 리포트 타입 |
|------|------|-------------|
| [20_리포트생성_구현서.md](./20_리포트생성_구현서.md) | 9종 리포트 생성기 상세 설명 | callchain, erd, erd-dagre, architecture, architecture-layer, sequence, query-list, backend-mapping, frontend-mapping |

### 개발 지침

| 문서 | 설명 | 대상 |
|------|------|------|
| [지침/개발지침.md](./지침/개발지침.md) | 코딩 컨벤션, 개발 원칙 | 모든 개발자 |
| [지침/Mermaid오류조치방법.md](./지침/Mermaid오류조치방법.md) | Mermaid 다이어그램 오류 해결 | 리포트 개발자 |

## 시스템 개요

**SourceAnalyzer**는 Java/Spring/MyBatis 기반 웹 애플리케이션의 소스코드를 분석하여 **프론트엔드 → 백엔드 → 데이터베이스**까지의 완전한 연관관계를 도출하는 메타데이터 분석 시스템입니다.

### 핵심 특징

- **9단계 분석 파이프라인**: 파일 스캔 → DB 스키마 → sqltext → XML → Java → sqltext 매칭 → API → 프론트엔드 → 검증
- **듀얼 DB 아키텍처**: metadata.db (메타데이터) + SqlContent.db (압축 SQL)
- **FileContext 기반 추적**: 모든 컴포넌트가 원본 파일과 연결
- **INFERRED 생성 금지**: 파일을 찾을 수 없으면 즉시 오류 처리
- **sqltext 독립 관리**: SQL 파일을 독립적으로 관리하고 Java와 자동 매칭
- **9종 리포트 생성**: ERD, CallChain, Architecture, Mapping 등 다양한 리포트

### 기술 스택

**백엔드 분석**:
- Java 클래스/메서드, StringBuilder SQL
- Spring Framework (@Controller, @RequestMapping, @RestController)
- MyBatis XML (DOM + SAX Fallback)
- JPA (@Entity, @Repository, @Query)

**프론트엔드 분석**:
- JSP, JSX, Vue, TypeScript, JavaScript, HTML
- HTTP 클라이언트: jQuery, Axios, Fetch API, XMLHttpRequest

**SQL 분석**:
- Oracle EXPLICIT/IMPLICIT JOIN 분석
- 테이블/컬럼 추출, 별칭 해석

## 9단계 분석 파이프라인

```
1단계: 파일 스캔
   ↓
2단계: DB 스키마 로드
   ↓
2-1단계: sqltext SQL 로딩
   ↓
3단계: MyBatis XML 분석
   ↓
4단계: Java 분석
   ↓
4-1단계: sqltext-Java 매칭
   ↓
5단계: API 진입점 분석
   ↓
6단계: 프론트엔드 분석
   ↓
7단계: 일관성 검증
```

각 단계의 상세 내용은 [03_처리_플로우_개요.md](./03_처리_플로우_개요.md)를 참조하세요.

## 9가지 리포트 타입

| 리포트 | 설명 | 용도 |
|--------|------|------|
| **callchain** | 프론트엔드 → API → METHOD → SQL → TABLE 전체 호출 체인 | 전체 데이터 흐름 추적 |
| **erd** | Mermaid 기반 ERD (테이블/컬럼/관계) | DB 구조 이해 |
| **erd-dagre** | Cytoscape.js 인터랙티브 ERD | DB 구조 시각화 (인터랙티브) |
| **architecture** | 컴포넌트 기반 아키텍처 구조 | 시스템 아키텍처 분석 |
| **architecture-layer** | 레이어별 아키텍처 구조 | 레이어 간 의존성 분석 |
| **sequence** | 시퀀스 다이어그램 (호출 순서) | 실행 흐름 이해 |
| **query-list** | SQL 쿼리 목록 분석 | SQL 쿼리 현황 파악 |
| **backend-mapping** | Java/XML/sqltext → 테이블/조인 매핑 | 백엔드 데이터 접근 추적 |
| **frontend-mapping** | 프론트엔드 → API → METHOD → QUERY 매핑 | 프론트엔드 데이터 흐름 추적 |

자세한 내용은 [20_리포트생성_구현서.md](./20_리포트생성_구현서.md)를 참조하세요.

## 핵심 개념

### FileContext 스택 관리

모든 파일 분석 시 FileContext를 push/pop하여 원본 파일 정보를 추적합니다.

```python
FileContext.push_file(file_id, path, file_type, stage)
try:
    # 분석 로직
    db_utils.insert_component(...)
finally:
    FileContext.pop_file()
```

### INFERRED 생성 금지

과거에는 파일을 찾지 못하면 "INFERRED_*" 파일을 자동 생성했으나, **현재는 즉시 오류를 발생**시킵니다.

### sqltext 기능

`projects/{project}/sqltext/**/*.sql` 폴더에 독립적으로 SQL 파일을 관리할 수 있습니다.

- **2-1단계**: sqltext 폴더의 모든 SQL 파일을 `layer='QUERY_FROM_SQLTEXT'`로 등록
- **4-1단계**: Java 파일 내용에서 SQL 파일명(쿼리 ID) 문자열 검색
- **자동 매칭**: Java METHOD → sqltext SQL 간 CALL_QUERY 관계 자동 생성

### 듀얼 DB 아키텍처

- **metadata.db**: 컴포넌트, 관계, 테이블 스키마 등 메타데이터 저장 (SQLite)
- **SqlContent.db**: SQL 쿼리 본문을 gzip 압축하여 저장 (성능 최적화)

## 주요 명령어

### 분석 실행

```bash
# 기본 실행
python main.py --project-name sampleSrc

# 상세 로그
python main.py --project-name sampleSrc --verbose

# 메타DB 초기화
python main.py --project-name sampleSrc --clear-metadb

# 설정 검증만
python main.py --project-name sampleSrc --dry-run
```

### 리포트 생성

```bash
# 모든 리포트
python create_report.py --project-name sampleSrc

# 특정 리포트
python create_report.py --project-name sampleSrc --report-type erd
python create_report.py --project-name sampleSrc --report-type callchain
```

### 테스트

```bash
# 회귀 테스트
pytest temp

# 스모크 테스트
pytest --maxfail=1 --disable-warnings -q

# 커버리지
pytest --cov=. --cov-report=term-missing
```

## 주요 디렉토리

```
D:\Analyzer\CreateMetaDb\
├── main.py                      # 9단계 파이프라인 오케스트레이션
├── create_report.py             # 리포트 생성 엔트리
├── file_loading.py              # 1단계, 2단계
├── sqltext_loading.py           # 2-1단계
├── xml_loading.py               # 3단계
├── java_loading.py              # 4단계
├── sqltext_java_matcher.py      # 4-1단계
├── backend_entry_loading.py     # 5단계
├── frontend_loading.py          # 6단계
├── relationship_builder.py      # 6단계 관계 구축
├── consistency_validator.py     # 7단계
├── parser/                      # 파서 모듈
├── util/                        # 유틸리티
├── reports/                     # 리포트 생성기 (9종)
├── database/                    # DDL 스키마
├── projects/{project}/          # 프로젝트별 데이터
│   ├── src/                     # 분석 대상 소스
│   ├── sqltext/                 # 독립 SQL 파일
│   ├── db_schema/               # DB 스키마 CSV
│   ├── metadata.db              # 메타데이터 DB
│   ├── SqlContent.db            # SQL 본문 DB
│   └── report/                  # 생성된 리포트
├── docs/                        # 문서 (현재 위치)
├── logs/                        # 실행 로그
└── temp/                        # 임시 파일
```

## 문서 작성 원칙

이 프로젝트의 문서는 다음 원칙을 따릅니다:

1. **현행화 중심**: 과거 버전 내용 제거, 현재 구현 기준 작성
2. **체계적 구조**: 각 문서는 명확한 목적과 대상 독자 정의
3. **실행 가능**: 모든 예제 코드와 명령어는 실제 실행 가능
4. **상호 참조**: 관련 문서 간 링크로 연결
5. **한글 우선**: 모든 문서는 한글로 작성 (코드 제외)

## 자주 묻는 질문

**Q1. 어디서부터 시작해야 하나요?**
- [00_신규투입_개발자_스타트가이드.md](./00_신규투입_개발자_스타트가이드.md)부터 시작하세요.

**Q2. 특정 단계의 구현을 수정하려면?**
- [03_처리_플로우_개요.md](./03_처리_플로우_개요.md)에서 전체 흐름 파악 후, 해당 단계의 구현서 (04~10) 참조

**Q3. 리포트가 어떻게 생성되는지 알고 싶어요**
- [20_리포트생성_구현서.md](./20_리포트생성_구현서.md) 참조

**Q4. DB 스키마 구조를 알고 싶어요**
- [02_데이터베이스_스키마_정의서.md](./02_데이터베이스_스키마_정의서.md) 참조

**Q5. sqltext 기능이 뭔가요?**
- [01_시스템_요구사항_정의서.md](./01_시스템_요구사항_정의서.md)의 2-1단계, 4-1단계 참조

## 문서 히스토리

| 날짜 | 변경 내용 | 담당자 |
|------|-----------|--------|
| 2025-12-11 | 전체 문서 현행화 (9단계 파이프라인, sqltext, 9종 리포트 반영) | - |
| 2025-12-11 | README.md 생성 | - |

## 기여 가이드

문서 수정 시:
1. 실제 구현된 소스코드 기준으로 작성
2. 과거 버전 내용은 삭제 (bak 폴더로 이동)
3. 예제는 실행 가능한 코드로 작성
4. 관련 문서 간 링크 유지
5. 한글 문서 작성 원칙 준수

## 문의

- 프로젝트 관련 문의: 기존 개발자에게 문의
- 문서 오류 발견: 즉시 수정 또는 담당자에게 보고

---

**환영합니다!** SourceAnalyzer 프로젝트에 오신 것을 환영합니다. 이 문서가 프로젝트 이해에 도움이 되기를 바랍니다.
