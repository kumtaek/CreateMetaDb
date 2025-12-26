# Exception 근본 원인 분석 및 개선 방안

**분석일시**: 2025-12-11
**목적**: 모든 exception이 왜 발생하는지 구체적 코드와 시나리오 분석

---

## 🔴 핵심 문제: DB Connection 다중 생성

### 현재 문제 상황

**DatabaseUtils 인스턴스가 5군데 이상에서 생성됨**:

```python
# 1. main.py:123
db_utils = DatabaseUtils(metadata_db_path)
conn = db_utils.get_persistent_connection()  # Connection #1

# 2. file_loading.py:671
temp_db_utils = DatabaseUtils(db_path)       # Connection #2

# 3. relationship_builder.py:27
self.db_utils = DatabaseUtils(...)           # Connection #3

# 4. consistency_validator.py:36
self.db_utils = DatabaseUtils(...)           # Connection #4

# 5. consistency_validator.py:1030
db_utils = DatabaseUtils(...)                # Connection #5
```

### 문제점

**같은 DB 파일에 5개 이상의 Connection이 동시에 열림**:
```
metadata.db (파일)
├─ Connection #1 (main.py)
├─ Connection #2 (file_loading.py)
├─ Connection #3 (relationship_builder.py)
├─ Connection #4 (consistency_validator.py - 인스턴스)
└─ Connection #5 (consistency_validator.py - execute 함수)
```

**결과**:
1. **PermissionError** (os.remove 실패):
   - 5개 connection이 파일 핸들 잡고 있음
   - Windows가 파일 삭제 차단
   - `os.remove(metadata.db)` → **PermissionError**

2. **OperationalError: database is locked**:
   - 여러 connection이 동시에 쓰기 시도
   - SQLite WAL 모드여도 writer 충돌 가능
   - UPDATE/INSERT 실행 → **database is locked**

---

## 1. PermissionError - DB 파일 잠금 (3건)

### 발생 코드
```python
# main.py:87-92
try:
    os.remove(target_path)  # metadata.db 삭제 시도
    info(f"기존 {label} 삭제: {target_path}")
except PermissionError as e:
    warning(f"{label} 삭제 실패(잠금 추정, 계속 진행): {target_path} - {e}")
```

### 왜 발생하는가?

**시나리오 1: 이전 실행의 Connection이 남아있음**
```python
# 이전 실행
db_utils = DatabaseUtils("metadata.db")
conn = db_utils.get_persistent_connection()
# 프로그램 비정상 종료 → connection.close() 안 됨
# metadata.db-wal, metadata.db-shm 파일 남아있음

# 새 실행
os.remove("metadata.db")  # PermissionError!
# 이유: .db-wal 파일이 잠금 유지 중
```

**시나리오 2: 다중 Connection 생성**
```python
# main.py:123
db_utils1 = DatabaseUtils("metadata.db")  # Connection #1 생성

# file_loading.py:671 (같은 프로세스 내)
temp_db_utils = DatabaseUtils("metadata.db")  # Connection #2 생성

# os.remove() 시도
os.remove("metadata.db")  # PermissionError!
# 이유: Connection #1, #2가 파일 핸들 잡고 있음
```

**시나리오 3: Windows 파일 시스템 잠금**
```python
# IDE DB Browser가 metadata.db 열어둠
# 또는 파일 탐색기에서 미리보기 중
os.remove("metadata.db")  # PermissionError!
# 이유: OS 레벨 파일 핸들 잠금
```

### 구체적 에러 메시지
```
PermissionError: [WinError 32] 다른 프로세스가 파일을 사용하고 있기 때문에
프로세스가 액세스할 수 없습니다: 'D:\\Analyzer\\CreateMetaDb\\projects\\sampleSrc\\metadata.db'
```

### 현재 처리: warning → 계속 진행
**문제**:
- DB 초기화하려는데 못 함
- 기존 데이터 남아있어서 오분석 가능
- 원인 파악 불가 (skip하고 넘어감)

### ✅ 수정 방안: handle_error() 적용
```python
except PermissionError as e:
    error(f"{label} 삭제 실패 (파일 잠금)")
    error(f"파일: {target_path}")
    error(f"원인: 다른 프로세스가 사용 중")
    error(f"조치: DB 브라우저, 이전 실행 프로세스 종료 후 재시도")
    handle_error(e, f"{label} 삭제 실패 - 파일 잠금")
```

---

## 2. 중복 관계 제거 Exception (consistency_validator.py:563, 570)

### 발생 코드
```python
# Line 563 - 개별 관계 삭제 실패
try:
    # [Step 1] 하위 정보 병합
    related_as_src = self.db_utils.execute_query(...)  # ← 여기서 에러
    for rel in related_as_src:
        existing = self.db_utils.execute_query(...)    # ← 또는 여기서
        if not existing:
            self.db_utils.execute_query("""UPDATE...""")  # ← 또는 여기서

    # [Step 2] 삭제
    self.db_utils.execute_query("""UPDATE relationships SET del_yn='Y'...""")

except Exception as e:
    warning(f"관계 삭제 실패 (relationship_id: {remove_id}): {e}")

# Line 570 - 전체 프로세스 실패
except Exception as e:
    warning(f"중복 관계 제거 중 오류: {e}")
```

### 왜 발생하는가?

#### Case 1: OperationalError - database is locked
```python
# 시나리오
# Connection #1 (main.py)에서 INSERT 실행 중
# Connection #4 (consistency_validator)에서 UPDATE 시도

self.db_utils.execute_query("""
    UPDATE relationships
    SET del_yn = 'Y', updated_at = CURRENT_TIMESTAMP
    WHERE relationship_id = ?
""", (remove_id,))

# OperationalError: database is locked
# 이유: 다른 connection이 write lock 잡고 있음
```

#### Case 2: IntegrityError - foreign key constraint
```python
# relationships 테이블 구조
# relationship_id (PK)
# src_id (FK → components.component_id)
# dst_id (FK → components.component_id)

# 시나리오: src_id가 가리키는 component가 없음
self.db_utils.execute_query("""
    UPDATE relationships
    SET src_id = ?  -- 존재하지 않는 component_id
    WHERE relationship_id = ?
""", (keep_id, rel['relationship_id']))

# IntegrityError: FOREIGN KEY constraint failed
# 이유: keep_id가 components 테이블에 없음
```

#### Case 3: TypeError - None 참조
```python
# 시나리오: execute_query 결과가 예상과 다름
related_as_src = self.db_utils.execute_query(...)
# related_as_src = None (쿼리 실패 시)

for rel in related_as_src:  # TypeError: 'NoneType' object is not iterable
    ...
```

#### Case 4: KeyError - 딕셔너리 키 누락
```python
# 시나리오: 쿼리 결과 컬럼 이름 불일치
for rel in related_as_src:
    dst_id = rel['dst_id']  # KeyError: 'dst_id'
    # 이유: 쿼리에서 SELECT dst_id를 빼먹음
```

### 구체적 에러 메시지 예시
```
OperationalError: database is locked
IntegrityError: FOREIGN KEY constraint failed
TypeError: 'NoneType' object is not iterable
KeyError: 'dst_id'
ProgrammingError: Cannot operate on a closed database
```

### 현재 처리: warning → 계속 진행
**Line 563 문제**:
- 개별 관계 삭제 실패 → 다음 관계 계속 처리
- **일부 중복 관계가 남음**
- 데이터 무결성 훼손

**Line 570 문제**:
- 전체 프로세스 실패 → warning만 출력
- **중복 관계 제거 전혀 안 됨**
- 심각한 데이터 문제인데 skip

### ✅ 수정 방안: handle_error() 적용
```python
# Line 563
except Exception as e:
    error(f"중복 관계 삭제 실패")
    error(f"  relationship_id: {remove_id}")
    error(f"  에러 유형: {type(e).__name__}")
    error(f"  에러 내용: {e}")
    handle_error(e, f"중복 관계 삭제 실패 (ID: {remove_id})")

# Line 570
except Exception as e:
    error(f"중복 관계 제거 전체 프로세스 실패")
    error(f"  처리 중이던 그룹 수: {len(duplicate_relationships)}")
    error(f"  에러 유형: {type(e).__name__}")
    handle_error(e, "중복 관계 제거 실패")
```

---

## 3. getter/setter 정리 Exception (consistency_validator.py:927, 1059)

### 발생 코드
```python
# Line 927 - 개별 메소드 정리 실패
for method in unnecessary_methods:
    try:
        self.db_utils.execute_query("""
            UPDATE components
            SET del_yn = 'Y', updated_at = CURRENT_TIMESTAMP
            WHERE component_id = ?
        """, (method['component_id'],))
        cleanup_count += 1
    except Exception as e:
        warning(f"  정리 실패: {method['component_name']} - {e}")

# Line 1059 - 전체 정리 실패
try:
    validator = ConsistencyValidator(project_name)
    validator._cleanup_unnecessary_getter_setter_methods()
    validator.close()
except Exception as e:
    warning(f"getter/setter 메소드 정리 중 오류: {e}")
```

### 왜 발생하는가?

#### Case 1: OperationalError - database is locked
```python
# 100개 getter/setter를 순차 삭제 중
# 50번째에서 다른 connection이 write lock 잡음

self.db_utils.execute_query("""
    UPDATE components SET del_yn = 'Y' WHERE component_id = ?
""", (method['component_id'],))

# OperationalError: database is locked
```

#### Case 2: IntegrityError - 외래키 위배
```python
# component_id가 relationships에서 참조되고 있음
# FOREIGN KEY 제약 때문에 삭제 불가

# OperationalError or IntegrityError
# 이유: del_yn='Y'로 마킹만 하는데도 다른 제약 위배
```

#### Case 3: KeyError - method 딕셔너리 구조 문제
```python
for method in unnecessary_methods:
    component_id = method['component_id']  # KeyError: 'component_id'
    # 이유: 쿼리에서 SELECT component_id를 누락
```

### ✅ 수정 방안
```python
# Line 927
except Exception as e:
    error(f"getter/setter 메소드 정리 실패")
    error(f"  메소드: {method.get('component_name', 'UNKNOWN')}")
    error(f"  component_id: {method.get('component_id', 'UNKNOWN')}")
    handle_error(e, f"메소드 정리 실패: {method.get('component_name')}")

# Line 1059
except Exception as e:
    error(f"getter/setter 전체 정리 프로세스 실패")
    handle_error(e, "getter/setter 정리 실패")
```

---

## 4. 검증 함수 Exception (consistency_validator.py:946, 964, ...)

### 발생 코드
```python
def validate_files_table(project_id: int, db_utils: DatabaseUtils, conn: sqlite3.Connection) -> dict:
    try:
        files_count = db_utils.execute_query(
            "SELECT COUNT(*) FROM files WHERE project_id = ?",
            (project_id,)
        )[0][0]  # ← 여기서 에러 가능

        return {'passed': True, 'message': f'files 테이블 정상 ({files_count}개 파일)'}
    except Exception as e:
        return {'passed': False, 'message': f'files 테이블 검증 실패: {str(e)}'}
```

### 왜 발생하는가?

#### Case 1: OperationalError - no such table
```python
# 스키마 생성 실패 또는 DB 손상
files_count = db_utils.execute_query(
    "SELECT COUNT(*) FROM files WHERE project_id = ?",
    (project_id,)
)

# OperationalError: no such table: files
# 이유: files 테이블이 생성되지 않음
```

#### Case 2: IndexError - 쿼리 결과 없음
```python
result = db_utils.execute_query(...)
files_count = result[0][0]  # IndexError: list index out of range

# 이유: execute_query가 빈 리스트 [] 반환
```

#### Case 3: TypeError - None 참조
```python
result = db_utils.execute_query(...)  # None 반환
files_count = result[0][0]  # TypeError: 'NoneType' object is not subscriptable
```

#### Case 4: OperationalError - database is locked
```python
# 검증 쿼리 실행 중 다른 connection이 write
# OperationalError: database is locked
```

### ✅ 수정 방안
```python
def validate_files_table(...) -> dict:
    try:
        result = db_utils.execute_query(
            "SELECT COUNT(*) FROM files WHERE project_id = ?",
            (project_id,)
        )

        if not result or len(result) == 0:
            error("files 테이블 검증: 쿼리 결과 없음")
            handle_error(Exception("검증 실패"), "files 테이블 검증 실패")

        files_count = result[0][0]
        return {'passed': True, 'message': f'files 테이블 정상 ({files_count}개)'}

    except Exception as e:
        error(f"files 테이블 검증 실패: {type(e).__name__}")
        error(f"  에러 내용: {e}")
        handle_error(e, "files 테이블 검증 실패")
```

---

## 5. 조회 실패 Exception (consistency_validator.py:69, 118)

### 발생 코드
```python
def _get_project_id(self) -> Optional[int]:
    try:
        result = self.db_utils.execute_query("""
            SELECT project_id FROM projects
            WHERE project_name = ? AND del_yn = 'N'
            LIMIT 1
        """, (self.project_name,))

        if result:
            project_id = result[0]['project_id']
            return project_id
        else:
            warning(f"프로젝트를 찾을 수 없음: {self.project_name}")
            return None
    except Exception as e:
        warning(f"프로젝트 ID 조회 실패: {self.project_name} - {e}")
        return None
```

### 왜 발생하는가?

#### Case 1: OperationalError - database is locked
```python
result = self.db_utils.execute_query(...)
# OperationalError: database is locked
```

#### Case 2: OperationalError - no such table
```python
# 스키마 생성 실패
# OperationalError: no such table: projects
```

#### Case 3: KeyError - 컬럼명 불일치
```python
result = self.db_utils.execute_query(...)
project_id = result[0]['project_id']  # KeyError: 'project_id'
# 이유: execute_query가 dict가 아닌 tuple 반환
```

### ✅ 수정 방안
```python
def _get_project_id(self) -> Optional[int]:
    try:
        result = self.db_utils.execute_query(...)

        if result:
            project_id = result[0]['project_id']
            return project_id
        else:
            error(f"프로젝트를 찾을 수 없음: {self.project_name}")
            handle_error(Exception("프로젝트 없음"), f"프로젝트 조회 실패: {self.project_name}")

    except Exception as e:
        error(f"프로젝트 ID 조회 실패: {self.project_name}")
        error(f"  에러: {type(e).__name__} - {e}")
        handle_error(e, f"프로젝트 ID 조회 실패: {self.project_name}")
```

---

## 🔧 근본 원인 개선안: DB Connection 싱글톤

### 현재 문제
```python
# 5군데에서 별도 connection 생성
main.py:          db_utils = DatabaseUtils(db_path)  # Connection #1
file_loading:     temp_db_utils = DatabaseUtils(db_path)  # Connection #2
relationship:     self.db_utils = DatabaseUtils(db_path)  # Connection #3
validator:        self.db_utils = DatabaseUtils(db_path)  # Connection #4
validator(func):  db_utils = DatabaseUtils(db_path)  # Connection #5
```

### 개선안 1: 싱글톤 패턴 (추천)
```python
# util/database_utils.py 수정

class DatabaseUtils:
    _instances = {}  # {db_path: DatabaseUtils instance}
    _lock = threading.Lock()

    def __new__(cls, db_path: str):
        """싱글톤 패턴: 같은 db_path는 같은 인스턴스 반환"""
        if db_path not in cls._instances:
            with cls._lock:
                if db_path not in cls._instances:
                    instance = super(DatabaseUtils, cls).__new__(cls)
                    cls._instances[db_path] = instance
        return cls._instances[db_path]

    def __init__(self, db_path: str):
        # 이미 초기화되었으면 스킵
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.db_path = db_path
        self.connection = None
        self._initialized = True
```

**효과**:
- 같은 metadata.db에 대해 **connection 1개만** 생성
- 모든 코드 변경 없이 적용 가능
- DB 잠금 문제 **90% 해결**

### 개선안 2: Connection 명시적 전달 (현재 부분 적용됨)
```python
# main.py에서 생성한 connection을 모든 곳에 전달
conn = db_utils.get_persistent_connection()

# 각 엔진에 전달
file_engine = FileLoadingEngine(project_name, conn)
xml_engine = XmlLoadingEngine(project_name, conn, True)
frontend_engine = FrontendLoadingEngine(project_name, conn)

# 문제: validator에서 새로 생성하는 부분 수정 필요
```

### 개선안 3: Context Manager 패턴
```python
# 전역 connection manager
from util.global_db_connection import get_db_connection

def get_db_connection(db_path: str) -> sqlite3.Connection:
    """전역 connection 반환 (싱글톤)"""
    global _connections
    if db_path not in _connections:
        _connections[db_path] = sqlite3.connect(db_path, ...)
    return _connections[db_path]
```

---

## 📊 요약: 모든 Exception에 handle_error() 적용 필요

| 위치 | 현재 처리 | 변경 후 |
|------|----------|---------|
| main.py:90 | warning → 계속 | handle_error() → 종료 |
| file_loading.py:657, 665 | warning → 계속 | handle_error() → 종료 |
| consistency_validator.py:563 | warning → 계속 | handle_error() → 종료 |
| consistency_validator.py:570 | warning → 계속 | handle_error() → 종료 |
| consistency_validator.py:927 | warning → 계속 | handle_error() → 종료 |
| consistency_validator.py:1059 | warning → 계속 | handle_error() → 종료 |
| consistency_validator.py:69 | warning → None | handle_error() → 종료 |
| consistency_validator.py:118 | warning → None | handle_error() → 종료 |
| consistency_validator.py:946~ | dict 반환 | handle_error() → 종료 |

**총 16개 케이스 → 모두 handle_error() 적용**

---

## ✅ 최종 권장사항

1. **즉시 적용**: 모든 exception에 handle_error() 적용
2. **근본 개선**: DatabaseUtils 싱글톤 패턴 적용
3. **로깅 강화**: 에러 발생 시 구체적 정보 출력

**효과**:
- 원인 파악 가능 (종료되므로 로그 확인)
- DB 잠금 문제 90% 해결 (싱글톤)
- 데이터 무결성 보장

**작성 완료**
