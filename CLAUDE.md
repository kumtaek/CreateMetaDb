# CLAUDE.md



User Rules 내용 검토 숙지하여 개발할 것!!!  
하드코딩 금지. 
이전 단계의 소스를 수정하면 안됨. 또한 공통함수 수정시에도 이전단계의 소스에 영향가도록 수정해도 안됨.
모든 exception발생시 handle_error()로 변경할 것!!!!
exit()해야 에러인지가 가능함.  warning후 계속 실행하면 안됨.
현재 has_error='Y'되어 있는 파싱에러를 제외하고는 모두 handle_error() 처리한다.
공통함수(특히 경로관련 함수) 사용 지향. (Windows, RHEL 크로스플랫폼 대응)
다른소스에 공통함수 사용 사례도 검토해 볼 것.
중복공통함수 생성 금지 - ./util/ 확인 후 신규 공통함수 개발할 것.
target_source_config.yaml에 분석대상 폴더,파일에 대한 정의가 있음. 하드코딩 금지!
크로스플랫폼 대응, 오픈소스, 폐쇄망 오프라인 실행 가능하도록 개발.
이모지 사용 금지!!!!
파싱로직 개발시 메뉴얼 참고 -> D:\Analyzer\CreateMetaDb\parser\manual
파싱 키워드,패턴 설정은 여기에 -> D:\Analyzer\CreateMetaDb\config\parser





This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 개요

SourceAnalyzer는 Java/Spring 기반 웹 애플리케이션의 소스코드를 분석하고 메타데이터를 추출하여 ERD, CallChain, Architecture 리포트를 생성하는 도구입니다.

## 주요 명령어

### 소스코드 분석 실행

```bash
# 기본 분석 실행
python main.py --project-name <프로젝트명>

# 메타데이터베이스 초기화 후 분석
python main.py --project-name <프로젝트명> --clear-metadb

# 상세 로그와 함께 분석
python main.py --project-name <프로젝트명> --verbose

# SQL Content 분석 포함
python main.py --project-name <프로젝트명> --sql-content

# 드라이런 모드 (설정 확인만)
python main.py --project-name <프로젝트명> --dry-run
```

### 리포트 생성

```bash
# 모든 리포트 생성
python create_report.py --project-name <프로젝트명>

# 특정 리포트만 생성
python create_report.py --project-name <프로젝트명> --report-type callchain
python create_report.py --project-name <프로젝트명> --report-type erd
python create_report.py --project-name <프로젝트명> --report-type erd-dagre
python create_report.py --project-name <프로젝트명> --report-type architecture

# 출력 디렉토리 지정
python create_report.py --project-name <프로젝트명> --output-dir <경로>
```

### 테스트 실행

```bash
# 간단한 테스트
python test_simple.py

# JSP 파일 체크
python check_jsp_files.py

# JSP 단계별 테스트
python test_jsp_phases.py
```

## 아키텍처 구조

### 5단계 분석 파이프라인

1. **1단계**: 파일 정보 저장 (file_loading.py) - 프로젝트 전체 파일 스캔
2. **2단계**: 데이터베이스 구조 저장 및 컴포넌트 생성 (file_loading.py)
3. **3단계**: XML 파일 분석 및 SQL 컴포넌트 등록 (xml_loading.py)
4. **4단계**: Java 소스코드 분석 및 관계 생성 (java_loading.py)
5. **5단계**: Spring API 진입점 분석 (backend_entry_loading.py)

### 핵심 모듈 구조

#### 파서 모듈 (parser/)

- `java_parser.py`: Java 소스코드 파싱
- `xml_parser.py`: XML 파일 파싱 (DOM/SAX fallback 지원)
- `jsp_parser.py`: JSP 파일 파싱
- `spring_entry_analyzer.py`: Spring Controller/Service 분석
- `servlet_entry_analyzer.py`: Servlet 분석
- `sax_fallback_parser.py`: XML 파싱 실패 시 SAX fallback

#### 리포트 생성 (reports/)

- `callchain_report_generator.py`: 호출 체인 리포트
- `erd_report_generator.py`: ERD 리포트 (Mermaid 기반)
- `erd_dagre_report_generator.py`: ERD 리포트 (Cytoscape/Dagre 기반)
- `architecture_report_generator.py`: 아키텍처 리포트

#### 공통 유틸리티 (util/)

- `database_utils.py`: SQLite 데이터베이스 처리
- `file_utils.py`: 파일 I/O 및 해시 계산
- `path_utils.py`: 경로 처리 및 프로젝트 구조 관리
- `arg_utils.py`: 명령행 인자 처리
- `logger.py`: 로깅 시스템
- `validation_utils.py`: 데이터 검증

### 데이터베이스 스키마

- 각 프로젝트는 `projects/<프로젝트명>/metadata.db` SQLite 파일에 메타데이터 저장
- Components, Relationships, API_URLS, USE_TABLE 등의 테이블 구조

### 에러 처리 특징

- Recursion limit 설정 (XML DOM 파싱 오류 방지): sys.setrecursionlimit(50)
- XML 파싱 실패 시 SAX fallback 자동 전환
- Circular import 문제 회피를 위한 지연 import 패턴

## 개발 시 주의사항

### 메모리 최적화

- 대용량 파일 처리 시 메모리 사용량 고려
- XML 파싱 시 DOM/SAX 선택적 사용

### 로깅 패턴

- `util.logger`의 info, error, handle_error 함수 사용
- 에러 발생 시 handle_error()로 통합 처리

### 프로젝트 구조

- 분석 대상 프로젝트는 `projects/<프로젝트명>/src/` 경로에 위치
- 리포트는 `projects/<프로젝트명>/report/` 경로에 생성

### 공통 함수 사용 원칙

- 경로 처리는 PathUtils 사용
- 파일 I/O는 FileUtils 사용
- 데이터베이스 처리는 DatabaseUtils 사용
- 하드코딩된 경로 사용 금지

## 프로젝트 설정

### 필수 디렉토리 구조

```
projects/
└── <프로젝트명>/
    ├── src/           # 분석 대상 소스코드
    ├── metadata.db    # 메타데이터베이스
    └── report/        # 생성된 리포트 파일들
```

### 로그 파일

- 로그는 `logs/` 디렉토리에 타임스탬프별로 생성
- 24시간 이상 된 로그 파일은 자동 삭제

### 지원 파일 형식

- Java (.java)
- JSP (.jsp)
- XML (.xml)
- SQL (.sql)
- Properties (.properties)