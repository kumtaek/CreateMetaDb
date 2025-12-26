# 단순 테이블 매칭 기능 테스트 결과

## 개요
- **기능명**: 단순 문자열 매칭을 통한 쿼리-테이블 관계 추출
- **설정 파일**: `projects/{project_name}/config/target_source_config.yaml`
- **설정 키**: `sql_analysis.enable_brute_force_table_search`
- **기본값**: `true` (활성화)

## 구현 위치
- **핵심 로직**: `util/sql_content_manager.py` (lines 142-165)
- **테이블 로드**: `util/sql_content_manager.py::_load_all_tables()` (line 718)
- **SQL 주석 제거**: `util/sql_content_manager.py::_remove_comments_simple()` (line 764)
- **XML 로더**: `xml_loading.py::__init__()` (lines 54-61)
- **Java 로더**: `java_loading.py::__init__()` (lines 30-38)

## 테스트 결과

### 1. enable_brute_force_table_search = true (활성화)
- **실행 시간**: 2025-11-28 11:46:39 ~ 11:47:30
- **USE_TABLE 관계**: **463개**
- **전체 관계**: 3,622개
- **결과 파일**: `temp/brute_force_analysis_test.txt`

### 2. enable_brute_force_table_search = false (비활성화)
- **실행 시간**: 2025-11-28 11:51:04 ~ 11:51:45
- **USE_TABLE 관계**: **346개**
- **전체 관계**: 3,501개
- **결과 파일**: `temp/brute_force_false_test.txt`

### 비교 결과
| 설정 | USE_TABLE | 전체 관계 | 차이 |
|------|-----------|-----------|------|
| **true (활성화)** | **463개** | 3,622개 | 기준 |
| **false (비활성화)** | 346개 | 3,501개 | **-117개** (-25.3%) |

**단순 매칭 기능으로 인한 추가 발견**: **117개의 쿼리-테이블 관계**

## 관계 타입별 통계 (true 설정)
| 관계 타입 | 개수 |
|-----------|------|
| CALL_METHOD | 2,869 |
| USE_TABLE | **463** |
| CALL_API | 139 |
| CALL_QUERY | 87 |
| USE_COLUMN | 20 |
| JOIN_MERGE | 18 |
| JOIN_EXPLICIT | 18 |
| JOIN_IMPLICIT | 8 |
| **합계** | **3,622** |

## 기능 동작 방식

### 1. 초기화 단계 (XML/Java 로더)
1. `ConfigUtils`를 사용하여 `target_source_config.yaml` 로드
2. `sql_analysis.enable_brute_force_table_search` 설정 읽기 (기본값: true)
3. `SqlContentManager` 초기화 시 `enable_brute_force_search` 파라미터 전달

### 2. SQL 저장 단계 (`save_sql_content()`)
1. 기존 SQL 파서로 테이블명 추출 (`SqlParser.extract_table_names()`)
2. **[NEW]** `enable_brute_force_search=true`인 경우:
   - CSV에서 로드된 전체 테이블 목록 캐싱
   - SQL 주석 제거 (MyBatis 태그, 라인 주석, 블록 주석)
   - 정규표현식 단어 경계 검색 (`\b{table_name}\b`)
   - 기존 파서에서 누락된 테이블 추가
3. 모든 테이블에 대해 `USE_TABLE` 관계 생성

### 3. 주요 특징
- **Lazy Loading**: 테이블 목록은 첫 쿼리 처리 시 한 번만 로드하고 캐싱
- **중복 방지**: 이미 기존 파서에서 찾은 테이블은 건너뜀
- **단어 경계 검색**: 부분 일치 방지 (`\bPRODUCTS\b`)
- **대소문자 무시**: SQL을 대문자로 변환 후 검색
- **Owner 무시**: 테이블명만으로 검색 (`SCOTT.USERS` → `USERS`)

## 설정 변경 방법

```yaml
# projects/{project_name}/config/target_source_config.yaml

sql_analysis:
  enable_brute_force_table_search: true  # 활성화 (기본값, 누락 최소화)
  # enable_brute_force_table_search: false  # 비활성화 (정확도 우선)
```

## 성능 고려사항
- **첫 쿼리 처리 시**: 테이블 목록 로드로 인한 약간의 지연 (한 번만 발생)
- **이후 쿼리 처리**: 캐싱된 목록 사용으로 성능 영향 최소
- **메모리 사용**: 테이블 목록 크기에 비례 (일반적으로 수백 개 수준)

## 결론
- ✅ 기능 정상 작동 확인
- ✅ 설정 파일 기반 ON/OFF 가능
- ✅ 기본값 true (누락 방지 우선)
- ✅ 기존 로직에 영향 없음 (추가 로직만 실행)
