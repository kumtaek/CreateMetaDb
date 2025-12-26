# handle_error() 미사용 Exception 처리 분석 결과

**분석일시**: 2025-12-11
**분석 목적**: exception 발생 시 handle_error() 미사용 케이스 파악 및 적절성 판단
**원칙**: "Exception발생시 중지 -> error_handle()호출" (CLAUDE.md 지침)

---

## 요약

### 총 발견 케이스: 20개
- **정당한 Skip**: 16개 (80%)
- **handle_error() 적용 권장**: 4개 (20%)

---

## 1. 정당한 Skip 케이스 (예외 허용)

### 1-1. PermissionError: DB 파일 잠금 (3건)

#### main.py:90
```python
try:
    os.remove(target_path)  # metadata.db, SqlContent.db 삭제
    info(f"기존 {label} 삭제: {target_path}")
except PermissionError as e:
    warning(f"{label} 삭제 실패(잠금 추정, 계속 진행): {target_path} - {e}")
    # 잠금 상태라면 이후 단계에서 기존 파일을 재사용하도록 계속 진행
```
**판단**: ✅ **Skip 적절**
**이유**:
- DB 파일이 다른 프로세스에서 사용 중일 수 있음
- `--clear-metadb` 옵션 무시하고 기존 DB 재사용 (사용성 향상)
- 치명적 오류 아님

#### file_loading.py:657, 665
```python
try:
    os.remove(db_path)  # metadata.db 삭제
except PermissionError as e:
    warning(f"메타데이터베이스 삭제 실패(잠금 추정, 계속 진행): {db_path} - {e}")
    # 잠금 상태라면 이후 단계에서 기존 파일을 재사용하도록 계속 진행

try:
    os.remove(sql_content_db_path)  # SqlContent.db 삭제
except PermissionError as e:
    warning(f"SQL 콘텐츠 DB 삭제 실패(잠금 추정, 계속 진행): {sql_content_db_path} - {e}")
```
**판단**: ✅ **Skip 적절**
**이유**: main.py:90과 동일

---

### 1-2. XML 파일별 처리 오류 - 개별 파일 실패 허용 (1건)

#### xml_loading.py:200
```python
try:
    # XML 파일 파싱 및 처리
    ...
except Exception as e:
    self.stats['errors'] += 1
    warning(f"XML 파일 처리 중 오류 발생: {xml_file} - {e}")
finally:
    self.file_context.pop()  # 항상 컨텍스트 복원
```
**판단**: ✅ **Skip 적절**
**이유**:
- **개별 파일 실패가 전체 프로세스 중단시키면 안 됨**
- 100개 XML 중 1개 실패 시 나머지 99개 처리 필요
- 통계에 오류 카운트 기록 (`self.stats['errors']`)
- finally에서 FileContext 복원 (중요!)

---

### 1-3. Fallback 메커니즘 - 대체 로직 존재 (2건)

#### xml_loading.py:335
```python
try:
    # 고급 SQL 파서로 테이블명 추출
    table_names = self.sql_parser.extract_table_names(sql_content)
    return table_names
except Exception as e:
    debug(f"SQL 파서 오류 - 기본 파서로 fallback: {str(e)}")
    # 기존 파서로 fallback
    return self._extract_table_names_from_sql_legacy(sql_content)
```
**판단**: ✅ **Skip 적절**
**이유**:
- **Fallback 패턴**: 고급 파서 실패 시 레거시 파서로 자동 전환
- 안정성 보장 메커니즘
- 오류가 아닌 정상적인 흐름 제어

#### xml_loading.py:400
```python
try:
    # 레거시 SQL 파서로 테이블명 추출
    ...
    return table_names
except Exception as e:
    debug(f"기존 SQL 파서에서 테이블명 추출 중 오류: {str(e)}")
    return set()  # 빈 set 반환
```
**판단**: ✅ **Skip 적절**
**이유**:
- 이미 Fallback의 Fallback (2차 안전망)
- 빈 set 반환하여 계속 진행 (테이블 추출 실패는 허용 가능)

#### xml_loading.py:430
```python
try:
    # 테이블명 유효성 검사
    ...
    return True
except Exception:
    return False
```
**판단**: ✅ **Skip 적절**
**이유**:
- 단순 boolean 반환 유틸리티 함수
- 오류 시 False 반환이 정상적인 제어 흐름

---

### 1-4. 선택적 기능 실패 허용 (1건)

#### relationship_builder.py:58
```python
try:
    from util.common_sql_processor import CommonSqlAnalyzer
    CommonSqlAnalyzer(self.project_name).analyze_all_queries()
except Exception:
    warning("CommonSqlAnalyzer analyze_all_queries warning: continue")
```
**판단**: ✅ **Skip 적절**
**이유**:
- **선택적/보조 기능**: 전체 쿼리 분석은 필수가 아님
- 실패해도 핵심 관계 구축 기능은 동작
- 경고 로그 출력으로 추적 가능

---

### 1-5. 조회 실패 시 None 반환 - 비치명적 (2건)

#### consistency_validator.py:69
```python
try:
    # 프로젝트 ID 조회
    ...
    return project_id
except Exception as e:
    warning(f"프로젝트 ID 조회 실패: {self.project_name} - {e}")
    return None
```
**판단**: ✅ **Skip 적절**
**이유**:
- 조회 실패 시 None 반환 (일반적인 패턴)
- 호출자가 None 체크하여 후속 처리
- 치명적 오류는 호출자에서 처리

#### consistency_validator.py:118
```python
try:
    # CSV/스키마 파일 ID 조회
    ...
    return file_id
except Exception as e:
    warning(f"CSV/스키마 파일 ID 조회 실패: {file_name} - {e}")
    return None
```
**판단**: ✅ **Skip 적절**
**이유**: 동일 (조회 실패 → None 반환)

---

### 1-6. 검증 함수 - Dict 반환으로 오류 전달 (3건)

#### consistency_validator.py:946
```python
try:
    # files 테이블 검증
    files_count = db_utils.execute_query(...)
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
**판단**: ✅ **Skip 적절**
**이유**:
- **검증 함수 패턴**: passed=False로 오류 상태 반환
- 호출자가 검증 결과 dict를 받아 통합 처리
- 개별 검증 실패가 전체 검증 중단시키면 안 됨

#### consistency_validator.py:964, 982, 1000, 1018
```python
# components, relationships, tables, columns 테이블 검증
# 모두 동일한 패턴
```
**판단**: ✅ **Skip 적절**
**이유**: 동일 (검증 함수 패턴)

---

### 1-7. 개별 작업 실패 허용 - 루프 내 처리 (3건)

#### consistency_validator.py:563
```python
try:
    # 중복 관계 개별 삭제
    db_utils.execute_update(...)
    info(f"중복 관계 제거 (병합 {merge_count}건): ...")
except Exception as e:
    warning(f"관계 삭제 실패 (relationship_id: {remove_id}): {e}")
    # 개별 관계 삭제 실패해도 다음 관계 계속 처리
```
**판단**: ✅ **Skip 적절**
**이유**:
- 루프 내에서 개별 항목 처리
- 1개 실패해도 나머지 항목 처리 필요

#### consistency_validator.py:927
```python
try:
    # getter/setter 메소드 개별 정리
    db_utils.execute_update(...)
except Exception as e:
    warning(f"  정리 실패: {method['component_name']} - {e}")
    # 개별 메소드 정리 실패해도 다음 메소드 계속 처리
```
**판단**: ✅ **Skip 적절**
**이유**: 동일 (루프 내 개별 처리)

#### consistency_validator.py:1059
```python
try:
    # 개별 warning 케이스 처리
    ...
except Exception as e:
    warning(f"경고 케이스 처리 실패: {e}")
```
**판단**: ✅ **Skip 적절**
**이유**: 경고성 검사 실패는 치명적이지 않음

---

### 1-8. 중첩 Exception 처리 - 내부 오류는 Skip (1건)

#### create_report.py:139
```python
try:
    # 프로젝트 유효성 검증
    ...
    try:
        # DB 연결 및 검증
        ...
        return True
    except Exception as db_err:
        app_logger.error(f"DB 검증 중 오류 발생: {db_err}")
        return False  # False 반환으로 실패 전달

except Exception as e:
    handle_error(e, f"프로젝트 유효성 검증 실패: {project_name}")
    return False
```
**판단**: ✅ **Skip 적절** (내부 except만)
**이유**:
- **내부 except (Line 139)**: False 반환으로 오류 상태 전달
- **외부 except (Line 146)**: handle_error() 사용 ✅
- 중첩 구조에서 내부는 오류 전달, 외부는 치명적 처리

---

## 2. handle_error() 적용 권장 케이스 (4건)

### ⚠️ consistency_validator.py:570
```python
try:
    # 중복 관계 제거 전체 로직
    ...
except Exception as e:
    warning(f"중복 관계 제거 중 오류: {e}")
```
**판단**: ❌ **handle_error() 적용 권장**
**이유**:
- **전체 중복 관계 제거 프로세스 실패** (개별 항목이 아님)
- 데이터 무결성에 영향을 줄 수 있는 중요한 작업
- warning만 출력하고 계속 진행하면 중복 관계가 남음
- **수정 권장**: `handle_error(e, "중복 관계 제거 중 치명적 오류")`

---

### ⚠️ consistency_validator.py:944 ~ 1018 (전체 검증 함수 그룹)

**현재**: 개별 검증 함수는 dict 반환으로 처리 ✅
**문제**: 호출자에서 passed=False 처리 확인 필요

검증이 필요한 호출 패턴:
```python
result = validate_files_table(project_id, db_utils, conn)
if not result['passed']:
    # 여기서 handle_error() 호출해야 하는가?
    # 아니면 warning만 하고 계속 진행?
```

**확인 필요**: 호출자 코드에서 검증 실패 시 처리 방식
**권장**: 치명적 검증 실패는 handle_error() 호출

---

## 3. 패턴별 통계

| 패턴 유형 | 건수 | Skip 적절성 |
|----------|------|-----------|
| PermissionError (DB 잠금) | 3 | ✅ 적절 |
| 개별 파일 처리 오류 | 1 | ✅ 적절 |
| Fallback 메커니즘 | 3 | ✅ 적절 |
| 선택적 기능 실패 | 1 | ✅ 적절 |
| 조회 실패 None 반환 | 2 | ✅ 적절 |
| 검증 함수 Dict 반환 | 5 | ✅ 적절 |
| 루프 내 개별 처리 | 3 | ✅ 적절 |
| 중첩 Exception (내부) | 1 | ✅ 적절 |
| **전체 프로세스 실패** | **1** | **❌ 권장** |

---

## 4. 권장 조치사항

### 🔴 즉시 수정 권장
1. **consistency_validator.py:570** - 중복 관계 제거 실패 시 handle_error() 적용

### 🟡 검토 필요
1. **검증 함수 호출자** - passed=False 시 처리 로직 확인
   - 치명적 검증 실패는 handle_error() 호출 권장
   - 경고성 검증 실패는 warning 후 계속 진행 적절

### ✅ 현상 유지
- 나머지 16건은 모두 정당한 Skip 케이스로 판단
- 현재 구현이 적절하며 수정 불필요

---

## 5. 지침 개선 제안

**현재 지침** (CLAUDE.md):
> Exception발생시 중지 -> error_handle()호출

**개선 제안**:
> **Exception 처리 원칙**:
> - **치명적 오류**: handle_error() 호출하여 프로그램 종료
> - **허용 가능한 예외** (다음 중 하나):
>   1. PermissionError (리소스 잠금) - warning 후 대체 방안
>   2. 개별 항목 처리 실패 (루프 내) - 통계 기록 후 계속
>   3. Fallback 메커니즘 존재 - 대체 로직으로 전환
>   4. 선택적/보조 기능 실패 - 핵심 기능 영향 없음
>   5. 검증 함수 - 오류 상태를 반환값으로 전달
>   6. 조회 실패 - None 반환, 호출자가 처리
> - **판단 기준**: "이 오류가 전체 시스템 무결성에 영향을 주는가?"

---

**분석 완료**
**다음 단계**: consistency_validator.py:570 수정 검토
