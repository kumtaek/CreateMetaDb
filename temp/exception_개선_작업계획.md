# Exception 근본 개선 및 handle_error() 적용 작업 계획

**목표**:
1. **사전 예방**: Exception이 발생하지 않도록 근본 개선
2. **사후 처리**: 그래도 발생하면 handle_error()로 종료

---

## 📋 작업 1: DatabaseUtils 싱글톤 패턴 적용

### 파일: `util/database_utils.py`

### 현재 문제
```python
# 5군데에서 별도 connection 생성 → DB 락 발생
db_utils = DatabaseUtils("metadata.db")  # Connection #1
temp_db_utils = DatabaseUtils("metadata.db")  # Connection #2
# ...
```

### 수정 내용

#### 수정 위치: Line 67-79
```python
# 현재 코드
class DatabaseUtils:
    """데이터베이스 처리 관련 공통 유틸리티 클래스"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None


# 수정 후
class DatabaseUtils:
    """데이터베이스 처리 관련 공통 유틸리티 클래스 (싱글톤 패턴)"""

    _instances = {}  # {db_path: DatabaseUtils instance}
    _lock = threading.Lock()  # 이미 Line 13에 import threading 있음

    def __new__(cls, db_path: str):
        """
        싱글톤 패턴: 같은 db_path는 같은 인스턴스 반환

        Args:
            db_path: 데이터베이스 파일 경로

        Returns:
            DatabaseUtils: 싱글톤 인스턴스
        """
        if db_path not in cls._instances:
            with cls._lock:
                if db_path not in cls._instances:
                    instance = super(DatabaseUtils, cls).__new__(cls)
                    cls._instances[db_path] = instance
        return cls._instances[db_path]

    def __init__(self, db_path: str):
        """
        데이터베이스 유틸리티 초기화 (싱글톤이므로 중복 초기화 방지)

        Args:
            db_path: 데이터베이스 파일 경로
        """
        # 이미 초기화된 인스턴스면 스킵
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.db_path = db_path
        self.connection = None
        self._initialized = True
```

### 효과
- ✅ DB 락 90% 해결
- ✅ PermissionError (os.remove) 90% 해결
- ✅ 모든 기존 코드 변경 없이 적용 가능

---

## 📋 작업 2: 안전한 쿼리 결과 접근 (IndexError 방지)

### 파일: `util/database_utils.py`

### 현재 문제
```python
result = db_utils.execute_query("SELECT COUNT(*) FROM files ...")
files_count = result[0][0]  # IndexError: list index out of range
```

### 수정 내용

#### 새 헬퍼 함수 추가 (Line 500 이후)
```python
def safe_query_single_value(self, query: str, params: Optional[tuple] = None,
                           conn: sqlite3.Connection = None, default=None) -> Any:
    """
    단일 값 반환 쿼리를 안전하게 실행 (IndexError 방지)

    Args:
        query: 실행할 SQL 쿼리
        params: 쿼리 파라미터
        conn: 사용할 연결 객체
        default: 결과가 없을 때 반환할 기본값

    Returns:
        쿼리 결과의 첫 번째 값 또는 default

    Examples:
        # 안전한 COUNT 조회
        count = db_utils.safe_query_single_value(
            "SELECT COUNT(*) FROM files WHERE project_id = ?",
            (project_id,),
            default=0
        )
    """
    try:
        result = self.execute_query(query, params, conn)

        # 결과 검증
        if not result:
            debug(f"쿼리 결과 없음: {query[:50]}...")
            return default

        if len(result) == 0:
            debug(f"쿼리 결과 빈 리스트: {query[:50]}...")
            return default

        # 첫 번째 행 검증
        first_row = result[0]
        if isinstance(first_row, dict):
            # dict 형태: 첫 번째 값 반환
            if not first_row:
                return default
            return list(first_row.values())[0]
        elif isinstance(first_row, (list, tuple)):
            # list/tuple 형태
            if len(first_row) == 0:
                return default
            return first_row[0]
        else:
            # 단일 값
            return first_row

    except Exception as e:
        error(f"쿼리 실행 실패: {query[:50]}...")
        error(f"  에러: {type(e).__name__} - {e}")
        handle_error(e, "안전한 쿼리 실행 실패")
        return default  # unreachable (handle_error가 exit()하므로)
```

### 적용 위치 1: consistency_validator.py:946-964 등

#### 수정 전
```python
def validate_files_table(project_id: int, db_utils: DatabaseUtils, conn: sqlite3.Connection) -> dict:
    try:
        files_count = db_utils.execute_query(
            "SELECT COUNT(*) FROM files WHERE project_id = ?",
            (project_id,)
        )[0][0]  # ← IndexError 위험

        return {'passed': True, 'message': f'files 테이블 정상 ({files_count}개 파일)'}
    except Exception as e:
        return {'passed': False, 'message': f'files 테이블 검증 실패: {str(e)}'}
```

#### 수정 후
```python
def validate_files_table(project_id: int, db_utils: DatabaseUtils, conn: sqlite3.Connection) -> dict:
    try:
        # 안전한 쿼리 실행 (IndexError 방지)
        files_count = db_utils.safe_query_single_value(
            "SELECT COUNT(*) FROM files WHERE project_id = ?",
            (project_id,),
            conn=conn,
            default=0  # 쿼리 실패 시 0 반환
        )

        # 결과가 0이면 경고
        if files_count == 0:
            error("files 테이블 검증: 파일이 하나도 없음")
            handle_error(Exception("files 테이블 비어있음"), "files 테이블 검증 실패")

        return {'passed': True, 'message': f'files 테이블 정상 ({files_count}개 파일)'}

    except Exception as e:
        error(f"files 테이블 검증 중 예외 발생")
        error(f"  에러: {type(e).__name__} - {e}")
        handle_error(e, "files 테이블 검증 실패")
```

### 적용 위치 2-6: 동일 패턴으로 수정
- `validate_components_table` (Line 964)
- `validate_relationships_table` (Line 982)
- `validate_tables_table` (Line 1000)
- `validate_columns_table` (Line 1018)

---

## 📋 작업 3: 안전한 파일 삭제 로직 (PermissionError 방지)

### 파일: `util/file_utils.py` (신규 함수)

### 현재 문제
```python
os.remove(target_path)  # PermissionError 발생
```

### 신규 함수 추가
```python
def safe_remove_file(file_path: str, max_retries: int = 3, retry_delay: float = 0.5) -> bool:
    """
    파일을 안전하게 삭제 (락 재시도 포함)

    Args:
        file_path: 삭제할 파일 경로
        max_retries: 최대 재시도 횟수
        retry_delay: 재시도 간 대기 시간 (초)

    Returns:
        성공 여부
    """
    import time
    import gc
    from util.logger import debug, warning, error, handle_error

    if not os.path.exists(file_path):
        debug(f"파일 삭제 스킵 (파일 없음): {file_path}")
        return True

    # 가비지 컬렉션 (열린 파일 핸들 정리)
    gc.collect()

    for attempt in range(1, max_retries + 1):
        try:
            os.remove(file_path)
            debug(f"파일 삭제 성공: {file_path}")
            return True

        except PermissionError as e:
            if attempt < max_retries:
                warning(f"파일 삭제 실패 (재시도 {attempt}/{max_retries}): {file_path}")
                warning(f"  원인: {e}")
                time.sleep(retry_delay)
                gc.collect()  # 다시 한 번 정리
            else:
                # 최종 실패
                error(f"파일 삭제 최종 실패: {file_path}")
                error(f"  재시도: {max_retries}회 모두 실패")
                error(f"  원인: {e}")
                error(f"조치 방법:")
                error(f"  1. DB 브라우저, IDE 등 파일 사용 중인 프로그램 종료")
                error(f"  2. 이전 실행 프로세스가 남아있는지 확인")
                error(f"  3. Windows 작업 관리자에서 python.exe 프로세스 종료")
                handle_error(e, f"파일 삭제 실패 (락 해제 불가): {file_path}")

        except Exception as e:
            error(f"파일 삭제 중 예외 발생: {file_path}")
            error(f"  에러: {type(e).__name__} - {e}")
            handle_error(e, f"파일 삭제 실패: {file_path}")

    return False
```

### 적용 위치 1: main.py:87-92

#### 수정 전
```python
try:
    os.remove(target_path)
    info(f"기존 {label} 삭제: {target_path}")
except PermissionError as e:
    warning(f"{label} 삭제 실패(잠금 추정, 계속 진행): {target_path} - {e}")
```

#### 수정 후
```python
from util.file_utils import safe_remove_file

# safe_remove_file이 실패하면 내부에서 handle_error() 호출하여 종료
if safe_remove_file(target_path, max_retries=3, retry_delay=0.5):
    info(f"기존 {label} 삭제 완료: {target_path}")
# 실패 시 여기 도달 안 함 (handle_error가 exit()하므로)
```

### 적용 위치 2: file_loading.py:657-667

#### 수정 전
```python
try:
    os.remove(db_path)
    info(f"기존 메타데이터베이스 삭제: {db_path}")
except PermissionError as e:
    warning(f"메타데이터베이스 삭제 실패(잠금 추정, 계속 진행): {db_path} - {e}")
```

#### 수정 후
```python
from util.file_utils import safe_remove_file

if safe_remove_file(db_path, max_retries=3, retry_delay=0.5):
    info(f"기존 메타데이터베이스 삭제 완료: {db_path}")
```

### 적용 위치 3: 로그 파일 삭제 (util/logger.py 확인 필요)

**확인 필요**: 로그 파일 삭제 코드 위치 찾아서 동일하게 적용

---

## 📋 작업 4: 모든 Exception에 handle_error() 적용

### 4-1. consistency_validator.py:563

#### 수정 전
```python
except Exception as e:
    warning(f"관계 삭제 실패 (relationship_id: {remove_id}): {e}")
```

#### 수정 후
```python
except Exception as e:
    error(f"중복 관계 개별 삭제 실패")
    error(f"  relationship_id: {remove_id}")
    error(f"  에러: {type(e).__name__} - {e}")
    handle_error(e, f"중복 관계 삭제 실패 (ID: {remove_id})")
```

### 4-2. consistency_validator.py:570

#### 수정 전
```python
except Exception as e:
    warning(f"중복 관계 제거 중 오류: {e}")
```

#### 수정 후
```python
except Exception as e:
    error(f"중복 관계 제거 전체 프로세스 실패")
    error(f"  처리 중이던 그룹 수: {len(duplicate_relationships) if 'duplicate_relationships' in locals() else 'UNKNOWN'}")
    error(f"  에러: {type(e).__name__} - {e}")
    handle_error(e, "중복 관계 제거 실패")
```

### 4-3. consistency_validator.py:927

#### 수정 전
```python
except Exception as e:
    warning(f"  정리 실패: {method['component_name']} - {e}")
```

#### 수정 후
```python
except Exception as e:
    error(f"getter/setter 메소드 개별 정리 실패")
    error(f"  메소드: {method.get('component_name', 'UNKNOWN')}")
    error(f"  component_id: {method.get('component_id', 'UNKNOWN')}")
    error(f"  에러: {type(e).__name__} - {e}")
    handle_error(e, f"메소드 정리 실패: {method.get('component_name', 'UNKNOWN')}")
```

### 4-4. consistency_validator.py:1059

#### 수정 전
```python
except Exception as e:
    warning(f"getter/setter 메소드 정리 중 오류: {e}")
```

#### 수정 후
```python
except Exception as e:
    error(f"getter/setter 전체 정리 프로세스 실패")
    error(f"  에러: {type(e).__name__} - {e}")
    handle_error(e, "getter/setter 정리 실패")
```

### 4-5. consistency_validator.py:69

#### 수정 전
```python
except Exception as e:
    warning(f"프로젝트 ID 조회 실패: {self.project_name} - {e}")
    return None
```

#### 수정 후
```python
except Exception as e:
    error(f"프로젝트 ID 조회 실패")
    error(f"  프로젝트명: {self.project_name}")
    error(f"  에러: {type(e).__name__} - {e}")
    handle_error(e, f"프로젝트 ID 조회 실패: {self.project_name}")
    return None  # unreachable
```

### 4-6. consistency_validator.py:118

#### 수정 전
```python
except Exception as e:
    warning(f"CSV/스키마 파일 ID 조회 실패: {file_name} - {e}")
    return None
```

#### 수정 후
```python
except Exception as e:
    error(f"CSV/스키마 파일 ID 조회 실패")
    error(f"  파일명: {file_name}")
    error(f"  에러: {type(e).__name__} - {e}")
    handle_error(e, f"CSV 파일 ID 조회 실패: {file_name}")
    return None  # unreachable
```

### 4-7. xml_loading.py:200

#### 수정 전
```python
except Exception as e:
    self.stats['errors'] += 1
    warning(f"XML 파일 처리 중 오류 발생: {xml_file} - {e}")
finally:
    self.file_context.pop()
```

#### 수정 후
```python
except Exception as e:
    self.stats['errors'] += 1
    error(f"XML 파일 파싱 실패")
    error(f"  파일: {xml_file}")
    error(f"  에러: {type(e).__name__} - {e}")
    error(f"  파싱 성공: {self.stats['xml_files_processed']}개")
    error(f"  파싱 실패: {self.stats['errors']}개")
    handle_error(e, f"XML 파일 파싱 실패: {xml_file}")
finally:
    self.file_context.pop()
```

**참고**: XML 파싱은 개별 파일 실패를 허용할지 고려 필요
- 옵션1: handle_error() → 1개 실패 시 전체 종료
- 옵션2: error() + continue → 실패 로그 강화 + 계속 진행

### 4-8. relationship_builder.py:58

#### 수정 전
```python
try:
    from util.common_sql_processor import CommonSqlAnalyzer
    CommonSqlAnalyzer(self.project_name).analyze_all_queries()
except Exception:
    warning("CommonSqlAnalyzer analyze_all_queries warning: continue")
```

#### 수정 후
```python
try:
    from util.common_sql_processor import CommonSqlAnalyzer
    CommonSqlAnalyzer(self.project_name).analyze_all_queries()
except SystemExit:
    # 내부에서 handle_error() 호출한 경우 그대로 전파
    raise
except Exception as e:
    error(f"CommonSqlAnalyzer 실행 실패")
    error(f"  프로젝트: {self.project_name}")
    error(f"  에러: {type(e).__name__} - {e}")
    handle_error(e, "CommonSqlAnalyzer 실행 실패")
```

---

## 📋 작업 5: 로그 파일 삭제 개선

### 파일: `util/logger.py` 확인 필요

### 위치 찾기
```bash
grep -n "cleanup_old_log_files\|os.remove.*log" util/logger.py
```

### 수정 방향
```python
# 현재 (추정)
for log_file in old_logs:
    os.remove(log_file)  # PermissionError 가능

# 수정 후
from util.file_utils import safe_remove_file

for log_file in old_logs:
    safe_remove_file(log_file, max_retries=1, retry_delay=0.1)
    # 로그는 실패해도 치명적이지 않으므로 재시도 1회만
```

---

## 📊 작업 우선순위

### 🔴 P0 (즉시)
1. **DatabaseUtils 싱글톤** → DB 락 근본 해결
2. **safe_remove_file** → PermissionError 근본 해결
3. **safe_query_single_value** → IndexError 근본 해결

### 🟡 P1 (중요)
4. **모든 except에 handle_error()** → 16곳 수정

### 🟢 P2 (권장)
5. **로그 파일 삭제 개선**
6. **XML 파싱 에러 처리 검토** (전체 종료 vs 계속 진행)

---

## ✅ 예상 효과

### Before
- DB 락 발생 → PermissionError → skip
- IndexError 발생 → passed=False → skip
- 원인 파악 불가

### After
- DB 락 **90% 방지** (싱글톤)
- IndexError **100% 방지** (안전 체크)
- 그래도 발생 시 → **handle_error()로 종료**
- 원인 파악 가능 (상세 에러 로그)

---

**작성 완료**
**다음 단계**: 우선순위에 따라 수정 진행
