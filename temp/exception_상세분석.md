# Exception 처리 상세 분석 결과

**분석일시**: 2025-12-11
**목적**: 각 exception 케이스의 발생 원인 및 처리 방식의 적절성 상세 분석

---

## 1. PermissionError - DB 파일 잠금 (3건)

### 발생 위치
- `main.py:90` - 메타DB, SQL콘텐츠DB 삭제
- `file_loading.py:657` - 메타DB 삭제
- `file_loading.py:665` - SQL콘텐츠DB 삭제

### 발생 원인
```python
try:
    os.remove(target_path)  # metadata.db 또는 SqlContent.db 삭제
    info(f"기존 {label} 삭제: {target_path}")
except PermissionError as e:
    warning(f"{label} 삭제 실패(잠금 추정, 계속 진행): {target_path} - {e}")
    # 잠금 상태라면 이후 단계에서 기존 파일을 재사용하도록 계속 진행
```

**발생 시나리오**:
1. **다른 프로세스에서 DB 사용 중**
   - IDE에서 DB 브라우저로 열어둠
   - 다른 분석 프로세스가 실행 중
   - DB 연결이 완전히 닫히지 않음

2. **Windows 파일 시스템 잠금**
   - 파일 탐색기에서 미리보기 중
   - 백업 프로그램이 접근 중
   - 바이러스 백신 스캔 중

### 현재 처리 방식
- **warning 로그** 출력 후 **계속 진행**
- 기존 DB 파일 재사용
- `--clear-metadb` 옵션 무시됨

### 사용자 요청
**handle_error()로 변경 요청** ✅

### 변경 시 영향
**장점**:
- 원칙 준수: "Exception발생시 중지"
- 명확한 오류 인지
- DB 초기화 의도 명확히 실행

**단점**:
- 사용성 저하: DB 잠금만으로 프로그램 종료
- 사용자가 IDE 닫고 재실행 필요
- 개발 편의성 감소

### 권장 처리 방식
```python
except PermissionError as e:
    error(f"{label} 삭제 실패 (파일 잠금): {target_path}")
    error(f"다른 프로세스에서 사용 중일 수 있습니다.")
    error(f"DB 브라우저, IDE 등을 닫고 다시 시도하세요.")
    handle_error(e, f"{label} 삭제 실패 - 파일 잠금")
```

---

## 2. 개별 파일 처리 오류 (1건) - XML 파싱 에러

### 발생 위치
`xml_loading.py:200` - XML 파일 개별 처리

### 코드 컨텍스트
```python
for idx, xml_file in enumerate(self.xml_files, start=1):
    try:
        # 파일 컨텍스트 설정
        self.file_context.push(...)

        # XML 파일 파싱
        analysis_result = self.xml_parser.analyze_xml_file(...)

        # SQL 쿼리 저장
        for sql_query in analysis_result['sql_queries']:
            saved = self.sql_content_manager.save_sql_content(...)

        # 통계 업데이트
        self.stats['xml_files_processed'] += 1
        self.stats['sql_queries_extracted'] += len(analysis_result['sql_queries'])

    except Exception as e:
        self.stats['errors'] += 1
        warning(f"XML 파일 처리 중 오류 발생: {xml_file} - {e}")
    finally:
        # 항상 컨텍스트 복원
        self.file_context.pop()
```

### 발생 가능한 Exception 종류

#### 2-1. **XML 파싱 오류**
```
원인: 잘못된 XML 구조
- Malformed XML: 닫는 태그 누락, 특수문자 미처리
- 인코딩 문제: UTF-8이 아닌 EUC-KR 등
- 네임스페이스 충돌
- DTD/Schema 위반

예시 에러:
ParseError: mismatched tag: line 45, column 2
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb0
```

#### 2-2. **파일 I/O 오류**
```
원인: 파일 시스템 문제
- FileNotFoundError: 파일 경로 불일치 (대소문자, 경로 구분자)
- PermissionError: 파일 읽기 권한 없음
- IOError: 디스크 오류, 네트워크 드라이브 끊김

예시 에러:
FileNotFoundError: [Errno 2] No such file or directory: 'UserMapper.xml'
PermissionError: [Errno 13] Permission denied: 'config.xml'
```

#### 2-3. **SQL 저장 오류**
```
원인: DB 작업 실패
- IntegrityError: 중복 키, 외래키 위반
- OperationalError: DB 잠금, 쿼리 타임아웃
- ProgrammingError: 잘못된 SQL 구문

예시 에러:
IntegrityError: UNIQUE constraint failed: components.hash_value
OperationalError: database is locked
```

#### 2-4. **파서 로직 오류**
```
원인: 복잡한 XML 구조 처리 실패
- AttributeError: 예상하지 못한 XML 구조
- KeyError: 필수 속성 누락
- ValueError: 잘못된 데이터 타입

예시 에러:
AttributeError: 'NoneType' object has no attribute 'text'
KeyError: 'namespace'
ValueError: invalid literal for int() with base 10: ''
```

### 파싱 에러의 의미

**질문**: "파싱에러? 정확한 파싱이 목표가 아니라고. 대략적인 파싱을 해서 누락없이 분석해 내는게 목표야?"

**답변**:
❌ **틀림** - 정확한 파싱이 목표입니다!

**목표**:
1. **정확한 SQL 추출**: MyBatis XML에서 SQL 쿼리 100% 정확히 추출
2. **정확한 관계 생성**: 쿼리 → 테이블 → 컬럼 관계 정확히 매핑
3. **무결성 보장**: 잘못된 데이터로 인한 오분석 방지

**하지만**:
- **100개 XML 중 1개 실패 시**: 나머지 99개는 분석되어야 함
- **개별 파일 오류**: 전체 프로세스 중단하면 안 됨
- **통계 기록**: `self.stats['errors']` += 1로 실패 추적

**비유**:
- ❌ 잘못: "대충 파싱해도 괜찮아" (부정확한 메타데이터 생성)
- ✅ 맞음: "1개 XML 실패해도 나머지는 정확히 파싱해" (전체 중단 방지)

### 현재 처리 방식
- **warning 로그** + **통계 기록** (`errors += 1`)
- 다음 XML 파일 계속 처리
- **finally에서 FileContext 복원** (중요!)

### 처리 방식의 적절성
✅ **Skip 적절**

**이유**:
1. **개별 파일 실패가 전체 중단시키면 안 됨**
2. **통계로 실패 추적 가능** (로그 확인 → 수동 수정)
3. **FileContext 무결성 보장** (finally에서 복원)
4. **99개 정상 XML 분석 > 1개 오류로 전체 중단**

### 개선 제안
현재 처리 유지, 단 로그 강화:
```python
except Exception as e:
    self.stats['errors'] += 1
    error(f"XML 파일 파싱 실패: {xml_file}")
    error(f"  에러 유형: {type(e).__name__}")
    error(f"  에러 내용: {e}")
    warning(f"  다음 파일 계속 처리 (통계에 오류 기록됨)")
```

---

## 3. Fallback 메커니즘 (3건)

### 발생 위치
- `xml_loading.py:335` - 고급 SQL 파서 실패 → 레거시 파서 전환
- `xml_loading.py:400` - 레거시 SQL 파서 실패 → 빈 set 반환
- `xml_loading.py:430` - 테이블명 유효성 검사 실패 → False 반환

### 코드 분석

#### xml_loading.py:335
```python
try:
    # 고급 SQL 파서 (sql_parser.py - 정교한 분석)
    table_names = self.sql_parser.extract_table_names(sql_content)
    return table_names
except Exception as e:
    debug(f"SQL 파서 오류 - 기본 파서로 fallback: {str(e)}")
    # 레거시 파서로 fallback (정규표현식 기반)
    return self._extract_table_names_from_sql_legacy(sql_content)
```

**발생 원인**:
- 고급 파서가 복잡한 SQL 구조 처리 실패
- 새로운 SQL 문법 미지원 (Oracle 확장, 벤더 특화)
- 파서 버그

**처리 방식**: ✅ **Skip 적절** (Fallback 패턴)

#### xml_loading.py:400
```python
try:
    # 레거시 파서 (정규표현식 기반)
    table_names = re.findall(r'FROM\s+(\w+)', sql_content, re.IGNORECASE)
    return set(table_names)
except Exception as e:
    debug(f"기존 SQL 파서에서 테이블명 추출 중 오류: {str(e)}")
    return set()  # 빈 set 반환
```

**발생 원인**:
- 정규표현식 처리 실패 (극단적 케이스)
- SQL이 너무 복잡하거나 비정형

**처리 방식**: ✅ **Skip 적절** (최종 안전망)

#### xml_loading.py:430
```python
try:
    # 테이블명 유효성 검사
    if not table_name or len(table_name) < 2:
        return False
    if table_name.upper() in ORACLE_KEYWORDS:
        return False
    return True
except Exception:
    return False  # 검사 실패 시 False
```

**처리 방식**: ✅ **Skip 적절** (boolean 유틸리티)

---

## 4. 선택적 기능 실패 (1건)

### 발생 위치
`relationship_builder.py:58` - CommonSqlAnalyzer

### 코드 컨텍스트
```python
# 3) Analyze SQL contents for tables/joins (SqlContent.db)
try:
    from util.common_sql_processor import CommonSqlAnalyzer
    CommonSqlAnalyzer(self.project_name).analyze_all_queries()
except Exception:
    warning("CommonSqlAnalyzer analyze_all_queries warning: continue")
```

### 발생 가능한 Exception 종류

#### 4-1. **SqlContent.db 연결 실패**
```python
# common_sql_processor.py:103
conn = sqlite3.connect(self.sql_content_db_path)
# OperationalError: unable to open database file
```
**원인**: SqlContent.db 파일 없음, 권한 문제

#### 4-2. **FileContext 관련 오류**
```python
# common_sql_processor.py:110-141
from util.file_context import get_file_context_manager
ctx_mgr = get_file_context_manager()
ctx_mgr.push(...)  # FileContext 설정 실패
```
**원인**: file_id로 files 테이블 조회 실패

#### 4-3. **DB 쿼리 실패**
```python
# common_sql_processor.py:124-128
file_rows = self.db_utils.execute_query(...)
# OperationalError: no such table: files
```
**원인**: 메타DB 스키마 손상

#### 4-4. **내부 로직 오류 (handle_error 호출)**
```python
# common_sql_processor.py:165-166
except Exception as e:
    handle_error(e, f"쿼리 분석 실패: component_id={component_id}")
    continue
```
**원인**: 개별 쿼리 분석 중 오류 → handle_error() 호출 → **프로그램 종료!**

### **중요 발견!**

`CommonSqlAnalyzer.analyze_all_queries()` 내부에서 **handle_error() 호출**합니다!

```python
# Line 165-166
except Exception as e:
    handle_error(e, f"쿼리 분석 실패: component_id={component_id}")
    continue  # 이 continue는 실행되지 않음 (handle_error가 exit()하므로)
```

**문제점**:
- `handle_error()`는 `sys.exit(1)` 호출
- 개별 쿼리 분석 실패 시 전체 프로그램 종료됨
- `continue`는 dead code

### 처리 방식의 재평가

❌ **Skip 부적절**

**이유**:
1. `analyze_all_queries()` 내부에서 이미 `handle_error()` 사용
2. 외부에서 `except Exception` 캐치하면:
   - 내부 `handle_error()`가 발생시킨 `SystemExit` 예외를 캐치함
   - 프로그램이 종료되어야 하는데 계속 실행됨
   - **의도하지 않은 동작**

### 권장 조치

**옵션 1**: 외부 try-except 제거 (내부 handle_error() 신뢰)
```python
# relationship_builder.py:55-59 수정
from util.common_sql_processor import CommonSqlAnalyzer
CommonSqlAnalyzer(self.project_name).analyze_all_queries()
# try-except 제거 → 내부에서 handle_error() 호출 시 정상 종료
```

**옵션 2**: 내부 handle_error() → warning 변경
```python
# common_sql_processor.py:165-166 수정
except Exception as e:
    warning(f"쿼리 분석 실패: component_id={component_id} - {e}")
    continue  # 다음 쿼리 계속 처리
```

**옵션 3**: 외부에서 SystemExit는 재발생
```python
# relationship_builder.py:58-59 수정
except SystemExit:
    raise  # handle_error()의 종료는 그대로 전파
except Exception:
    warning("CommonSqlAnalyzer analyze_all_queries warning: continue")
```

---

## 5. 조회 실패 None 반환 (2건)

### 발생 위치
- `consistency_validator.py:69` - 프로젝트 ID 조회 실패
- `consistency_validator.py:118` - CSV/스키마 파일 ID 조회 실패

### 코드 분석

#### consistency_validator.py:69
```python
def _get_project_id(self) -> Optional[int]:
    """현재 프로젝트의 project_id 조회"""
    try:
        result = self.db_utils.execute_query("""
            SELECT project_id FROM projects
            WHERE project_name = ? AND del_yn = 'N'
            LIMIT 1
        """, (self.project_name,))

        if result:
            project_id = result[0]['project_id']
            info(f"프로젝트 ID 조회: {self.project_name} -> project_id {project_id}")
            return project_id
        else:
            warning(f"프로젝트를 찾을 수 없음: {self.project_name}")
            return None

    except Exception as e:
        warning(f"프로젝트 ID 조회 실패: {self.project_name} - {e}")
        return None
```

### 발생 가능한 Exception

#### 5-1. **DB 연결 실패**
```
OperationalError: unable to open database file
OperationalError: database is locked
```
**원인**: DB 파일 없음, 잠금, 권한 문제

#### 5-2. **SQL 실행 오류**
```
OperationalError: no such table: projects
ProgrammingError: Incorrect number of bindings supplied
```
**원인**: 스키마 손상, SQL 문법 오류

#### 5-3. **데이터 처리 오류**
```
KeyError: 'project_id'
TypeError: 'NoneType' object is not subscriptable
```
**원인**: 쿼리 결과 구조 불일치

### 처리 방식의 적절성

✅ **Skip 적절**

**이유**:
1. **조회 함수 패턴**: 조회 실패 시 None 반환은 일반적
2. **호출자가 처리**: `if project_id is None:` 체크 후 후속 조치
3. **비치명적**: 조회 실패 자체는 프로그램 종료 사유 아님
4. **호출자가 판단**: None을 받아서 치명적이면 handle_error() 호출

### 호출자 확인 필요

**호출 패턴**:
```python
project_id = validator._get_project_id()
if project_id is None:
    # 여기서 어떻게 처리하는가?
    # - handle_error() 호출?
    # - warning만 하고 계속?
    # - 검증 실패로 처리?
```

**확인 필요**: 호출자 코드에서 None 처리 로직 검증

---

## 6. 검증 함수 Dict 반환 (5건)

### 발생 위치
- `consistency_validator.py:946` - files 테이블 검증
- `consistency_validator.py:964` - components 테이블 검증
- `consistency_validator.py:982` - relationships 테이블 검증
- `consistency_validator.py:1000` - tables 테이블 검증
- `consistency_validator.py:1018` - columns 테이블 검증

### 코드 패턴
```python
def validate_files_table(project_id: int, db_utils: DatabaseUtils, conn: sqlite3.Connection) -> dict:
    """files 테이블 검증"""
    try:
        # files 테이블 기본 검증
        files_count = db_utils.execute_query(
            "SELECT COUNT(*) FROM files WHERE project_id = ?",
            (project_id,)
        )[0][0]

        return {
            'check_name': 'files 테이블',
            'passed': True,
            'message': f'files 테이블 정상 ({files_count}개 파일)'
        }
    except Exception as e:
        return {
            'check_name': 'files 테이블',
            'passed': False,
            'message': f'files 테이블 검증 실패: {str(e)}'
        }
```

### 발생 가능한 Exception

#### 6-1. **DB 쿼리 실패**
```
OperationalError: no such table: files
OperationalError: database is locked
```

#### 6-2. **결과 처리 오류**
```
IndexError: list index out of range (쿼리 결과 없음)
TypeError: 'NoneType' object is not subscriptable
```

#### 6-3. **통계 계산 오류**
```
ValueError: invalid literal for int()
OverflowError: integer overflow
```

### 호출자 코드 분석
```python
# consistency_validator.py:1043-1051
validation_results = []
validation_results.append(validate_files_table(project_id, db_utils, conn))
validation_results.append(validate_components_table(project_id, db_utils, conn))
validation_results.append(validate_relationships_table(project_id, db_utils, conn))
validation_results.append(validate_tables_table(project_id, db_utils, conn))
validation_results.append(validate_columns_table(project_id, db_utils, conn))

# 모든 검증 결과 취합
all_passed = all(result['passed'] for result in validation_results)

if all_passed:
    info("일관성 검증 완료: 모든 검사 통과")
else:
    warning("일관성 검증 완료: 일부 문제 발견됨")
    for result in validation_results:
        if not result['passed']:
            warning(f"  - {result['check_name']}: {result['message']}")

return all_passed
```

### 처리 방식의 적절성

✅ **Skip 적절**

**이유**:
1. **검증 함수 패턴**: `passed=False` dict로 오류 상태 반환
2. **통합 처리**: 호출자가 모든 검증 결과 수집 후 통합 판단
3. **개별 검증 실패 허용**: 1개 테이블 검증 실패해도 나머지 계속
4. **최종 판단**: `all_passed = all(result['passed']...)`로 전체 결과 판단

### 호출자의 최종 처리

**현재**:
```python
return all_passed  # True/False만 반환
```

**문제**: 검증 실패(all_passed=False) 시 **warning만 출력**

**개선 필요 여부**:
- 치명적 검증 실패 시 handle_error() 호출 고려
- 예: files 테이블이 없으면 → 치명적 오류
- 예: 일부 통계 불일치 → 경고성 문제

### 권장 조치

검증 결과에 따라 **치명도 분류**:
```python
# 치명적 검증 항목
CRITICAL_CHECKS = ['files 테이블', 'components 테이블', 'projects 테이블']

critical_failed = [
    r for r in validation_results
    if not r['passed'] and r['check_name'] in CRITICAL_CHECKS
]

if critical_failed:
    error("치명적 검증 실패:")
    for r in critical_failed:
        error(f"  - {r['check_name']}: {r['message']}")
    handle_error(Exception("일관성 검증 실패"), "치명적 테이블 손상")

# 경고성 검증 실패는 warning만
```

---

## 7. 루프 내 개별 처리 (3건)

### 발생 위치
- `consistency_validator.py:563` - 개별 중복 관계 삭제 실패
- `consistency_validator.py:927` - 개별 getter/setter 메소드 정리 실패
- `consistency_validator.py:1059` - getter/setter 전체 정리 실패

### 코드 분석

#### consistency_validator.py:563
```python
# 중복 관계 제거 루프
for group in duplicate_relationships:
    keep_id = group[0]['relationship_id']  # 첫 번째를 유지

    for remove_entry in group[1:]:  # 나머지는 삭제
        remove_id = remove_entry['relationship_id']

        try:
            # [Step 1] 하위 정보 병합
            ...병합 로직...

            # [Step 2] 병합 완료 후 안전하게 삭제
            self.db_utils.execute_query("""
                UPDATE relationships
                SET del_yn = 'Y', updated_at = CURRENT_TIMESTAMP
                WHERE relationship_id = ?
            """, (remove_id,))
            total_removed += 1

        except Exception as e:
            warning(f"관계 삭제 실패 (relationship_id: {remove_id}): {e}")
            # 개별 관계 삭제 실패해도 다음 관계 계속 처리
```

**발생 가능한 Exception**:
```
OperationalError: database is locked
IntegrityError: foreign key constraint failed
ProgrammingError: SQL syntax error
```

**처리 방식**: ✅ **Skip 적절**
**이유**: 루프 내 개별 항목 실패, 나머지 계속 처리 필요

#### consistency_validator.py:927
```python
# getter/setter 메소드 정리 루프
for method in unnecessary_methods:
    try:
        # components 테이블에서 del_yn='Y'로 업데이트
        self.db_utils.execute_query("""
            UPDATE components
            SET del_yn = 'Y', updated_at = CURRENT_TIMESTAMP
            WHERE component_id = ?
        """, (method['component_id'],))

        cleanup_count += 1

    except Exception as e:
        warning(f"  정리 실패: {method['component_name']} - {e}")
```

**처리 방식**: ✅ **Skip 적절**
**이유**: 동일 (개별 메소드 정리 실패)

#### consistency_validator.py:1059
```python
# getter/setter 전체 정리 (외부 except)
try:
    validator = ConsistencyValidator(project_name)
    validator._cleanup_unnecessary_getter_setter_methods()
    validator.close()
    info("불필요한 getter/setter 메소드 정리 완료")
except Exception as e:
    warning(f"getter/setter 메소드 정리 중 오류: {e}")
```

**발생 가능한 Exception**:
```
- ConsistencyValidator 초기화 실패
- _cleanup_unnecessary_getter_setter_methods() 전체 실패
- validator.close() 실패
```

**처리 방식**: ✅ **Skip 적절**
**이유**: **선택적 기능** (필수 검증이 아님), getter/setter 정리는 보조 기능

---

## 종합 결론

### 수정 필요 (사용자 요청)
1. **PermissionError (3건)** → handle_error() 변경 ✅
   - main.py:90
   - file_loading.py:657, 665

### 재검토 필요
2. **CommonSqlAnalyzer (1건)** → 내부 handle_error() 충돌 ⚠️
   - relationship_builder.py:58
   - 내부에서 이미 handle_error() 사용 중
   - 외부 except가 SystemExit 캐치하는 문제

### Skip 적절 (변경 불필요)
3. **XML 파싱 에러 (1건)** ✅
4. **Fallback 메커니즘 (3건)** ✅
5. **조회 실패 None 반환 (2건)** ✅
6. **검증 함수 Dict 반환 (5건)** ✅ (단, 치명도 분류 개선 권장)
7. **루프 내 개별 처리 (3건)** ✅

---

**작성 완료**
**다음 단계**: 수정 필요 항목 처리
