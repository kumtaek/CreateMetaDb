# SampleSrc 프로젝트 메타데이터 예상 결과 (정답지)

## 문서 목적

이 문서는 SampleSrc 프로젝트를 소스분석기로 분석했을 때 metadata.db에 생성될 것으로 예상되는 데이터를 정답지 형태로 작성한 것입니다.  
실제 분석 결과와 비교하여 검증 목적으로 사용됩니다.

## 분석 대상 프로젝트 개요

- **프로젝트명**: SampleSrc
- **분석 대상**: ./CreateMetaDb/projects/SampleSrc 하위 모든 파일
- **주요 기술 스택**: Java, JSP, MyBatis, Spring MVC
- **데이터베이스**: Oracle (SAMPLE, PUBLIC, SCOTT 스키마)

## 예상 생성 데이터 상세

### 1. projects 테이블

| project_id | project_name | project_path | hash_value | total_files |
|------------|--------------|--------------|------------|-------------|
| 1 | SampleSrc | ./projects/SampleSrc | - | 87 |

### 2. files 테이블 (주요 파일들)

| file_id | project_id | file_name | file_type | line_count |
|---------|------------|-----------|-----------|------------|
| 1 | 1 | UserMapper.xml | xml | 467 |
| 2 | 1 | UserController.java | java | 337 |
| 3 | 1 | UserDao.java | java | 483 |
| 4 | 1 | UserService.java | java | 353 |
| 5 | 1 | list.jsp | jsp | 236 |
| 6 | 1 | ProductMapper.xml | xml | - |
| 7 | 1 | MicroserviceMapper.xml | xml | - |
| 8 | 1 | MicroserviceController.java | java | - |
| 9 | 1 | ProductController.java | java | - |
| 10 | 1 | UserManagementController.java | java | - |

### 3. tables 테이블 (CSV에서 로드)

| table_id | project_id | table_name | table_owner | table_comments |
|----------|------------|------------|-------------|----------------|
| 1 | 1 | USERS | SAMPLE | 사용자 정보를 저장하는 테이블 |
| 2 | 1 | USER_TYPES | SAMPLE | 사용자 타입을 저장하는 테이블 |
| 3 | 1 | CUSTOMERS | SAMPLE | 고객정보 |
| 4 | 1 | ORDERS | SAMPLE | 주문 |
| 5 | 1 | ORDER_ITEMS | SAMPLE | 주문상품 |
| 6 | 1 | PRODUCTS | SAMPLE | 상품 |
| 7 | 1 | CATEGORIES | SAMPLE | 카테고리코드 |
| 8 | 1 | BRANDS | SAMPLE | - |
| 9 | 1 | SUPPLIERS | SAMPLE | 공급업체 |
| 10 | 1 | WAREHOUSES | SAMPLE | - |
| 11 | 1 | INVENTORIES | SAMPLE | 재고 |
| 12 | 1 | PRODUCT_REVIEWS | SAMPLE | 상품리뷰 |
| 13 | 1 | DISCOUNTS | SAMPLE | 할인 |
| 14 | 1 | USER_ROLE | PUBLIC | 사용자권한 |
| 15 | 1 | DYNAMIC_DATA | SCOTT | 동적데이터 |
| 16 | 1 | RELATED_DATA | SCOTT | 관련데이터 |

### 4. columns 테이블 (주요 컬럼들)

| column_id | table_id | column_name | data_type | nullable | position_pk |
|-----------|----------|-------------|-----------|----------|-------------|
| 1 | 1 | ID | NUMBER | N | 1 |
| 2 | 1 | USERNAME | VARCHAR2(50) | N | - |
| 3 | 1 | EMAIL | VARCHAR2(100) | N | - |
| 4 | 1 | PASSWORD | VARCHAR2(100) | N | - |
| 5 | 1 | NAME | VARCHAR2(100) | Y | - |
| 6 | 1 | AGE | NUMBER(3) | Y | - |
| 7 | 1 | STATUS | VARCHAR2(20) | Y | - |
| 8 | 1 | USER_TYPE | VARCHAR2(20) | Y | - |
| 9 | 1 | PHONE | VARCHAR2(20) | Y | - |
| 10 | 1 | ADDRESS | VARCHAR2(200) | Y | - |
| 11 | 1 | CREATED_DATE | DATE | Y | - |
| 12 | 1 | UPDATED_DATE | DATE | Y | - |

### 5. classes 테이블 (Java 클래스들)

| class_id | project_id | file_id | class_name | class_type | package_name | line_start | line_end |
|----------|------------|---------|------------|------------|--------------|------------|----------|
| 1 | 1 | 2 | UserController | class | com.example.controller | 15 | 337 |
| 2 | 1 | 3 | UserDao | class | com.example.dao | 14 | 483 |
| 3 | 1 | 4 | UserService | class | com.example.service | 14 | 353 |
| 4 | 1 | 8 | MicroserviceController | class | com.example.controller | - | - |
| 5 | 1 | 9 | ProductController | class | com.example.controller | - | - |
| 6 | 1 | 10 | UserManagementController | class | com.example.controller | - | - |

### 6. components 테이블

#### 6.1 TABLE 컴포넌트 (CSV에서 로드된 테이블들)

| component_id | project_id | file_id | component_name | component_type | parent_id | layer |
|--------------|------------|---------|----------------|----------------|-----------|-------|
| 1 | 1 | - | USERS | TABLE | - | DATA |
| 2 | 1 | - | USER_TYPES | TABLE | - | DATA |
| 3 | 1 | - | CUSTOMERS | TABLE | - | DATA |
| 4 | 1 | - | ORDERS | TABLE | - | DATA |
| 5 | 1 | - | ORDER_ITEMS | TABLE | - | DATA |
| 6 | 1 | - | PRODUCTS | TABLE | - | DATA |
| 7 | 1 | - | CATEGORIES | TABLE | - | DATA |
| 8 | 1 | - | BRANDS | TABLE | - | DATA |
| 9 | 1 | - | SUPPLIERS | TABLE | - | DATA |
| 10 | 1 | - | WAREHOUSES | TABLE | - | DATA |
| 11 | 1 | - | INVENTORIES | TABLE | - | DATA |
| 12 | 1 | - | PRODUCT_REVIEWS | TABLE | - | DATA |
| 13 | 1 | - | DISCOUNTS | TABLE | - | DATA |
| 14 | 1 | - | USER_ROLE | TABLE | - | DATA |
| 15 | 1 | - | DYNAMIC_DATA | TABLE | - | DATA |
| 16 | 1 | - | RELATED_DATA | TABLE | - | DATA |

#### 6.2 COLUMN 컴포넌트 (주요 컬럼들)

| component_id | project_id | file_id | component_name | component_type | parent_id | layer |
|--------------|------------|---------|----------------|----------------|-----------|-------|
| 17 | 1 | - | ID | COLUMN | 1 | DATA |
| 18 | 1 | - | USERNAME | COLUMN | 1 | DATA |
| 19 | 1 | - | EMAIL | COLUMN | 1 | DATA |
| 20 | 1 | - | PASSWORD | COLUMN | 1 | DATA |
| 21 | 1 | - | NAME | COLUMN | 1 | DATA |
| 22 | 1 | - | AGE | COLUMN | 1 | DATA |
| 23 | 1 | - | STATUS | COLUMN | 1 | DATA |
| 24 | 1 | - | USER_TYPE | COLUMN | 1 | DATA |
| 25 | 1 | - | PHONE | COLUMN | 1 | DATA |
| 26 | 1 | - | ADDRESS | COLUMN | 1 | DATA |
| 27 | 1 | - | CREATED_DATE | COLUMN | 1 | DATA |
| 28 | 1 | - | UPDATED_DATE | COLUMN | 1 | DATA |

#### 6.3 CLASS 컴포넌트 (Java 클래스들)

| component_id | project_id | file_id | component_name | component_type | parent_id | layer |
|--------------|------------|---------|----------------|----------------|-----------|-------|
| 29 | 1 | 2 | UserController | CLASS | - | APPLICATION |
| 30 | 1 | 3 | UserDao | CLASS | - | APPLICATION |
| 31 | 1 | 4 | UserService | CLASS | - | APPLICATION |
| 32 | 1 | 8 | MicroserviceController | CLASS | - | APPLICATION |
| 33 | 1 | 9 | ProductController | CLASS | - | APPLICATION |
| 34 | 1 | 10 | UserManagementController | CLASS | - | APPLICATION |

#### 6.4 METHOD 컴포넌트 (Java 메서드들)

| component_id | project_id | file_id | component_name | component_type | parent_id | layer |
|--------------|------------|---------|----------------|----------------|-----------|-------|
| 35 | 1 | 2 | getUserList | METHOD | 29 | APPLICATION |
| 36 | 1 | 2 | searchUsers | METHOD | 29 | APPLICATION |
| 37 | 1 | 2 | getUsersByType | METHOD | 29 | APPLICATION |
| 38 | 1 | 2 | validateSearchParameters | METHOD | 29 | APPLICATION |
| 39 | 1 | 2 | calculateUserStatistics | METHOD | 29 | APPLICATION |
| 40 | 1 | 3 | findUsersByCondition | METHOD | 30 | APPLICATION |
| 41 | 1 | 3 | findUsersByAdvancedCondition | METHOD | 30 | APPLICATION |
| 42 | 1 | 3 | findUsersByType | METHOD | 30 | APPLICATION |
| 43 | 1 | 3 | findUserById | METHOD | 30 | APPLICATION |
| 44 | 1 | 3 | createUser | METHOD | 30 | APPLICATION |
| 45 | 1 | 3 | updateUser | METHOD | 30 | APPLICATION |
| 46 | 1 | 3 | deleteUser | METHOD | 30 | APPLICATION |
| 47 | 1 | 3 | existsByUsername | METHOD | 30 | APPLICATION |
| 48 | 1 | 3 | existsByEmail | METHOD | 30 | APPLICATION |
| 49 | 1 | 3 | isEmailVerified | METHOD | 30 | APPLICATION |
| 50 | 1 | 3 | isPhoneVerified | METHOD | 30 | APPLICATION |
| 51 | 1 | 3 | getTotalUserCount | METHOD | 30 | APPLICATION |
| 52 | 1 | 3 | getActiveUserCount | METHOD | 30 | APPLICATION |
| 53 | 1 | 3 | getNewUsersTodayCount | METHOD | 30 | APPLICATION |
| 54 | 1 | 3 | getPremiumUserCount | METHOD | 30 | APPLICATION |
| 55 | 1 | 3 | findUsersByDirectQuery | METHOD | 30 | APPLICATION |
| 56 | 1 | 4 | getUsersByCondition | METHOD | 31 | APPLICATION |
| 57 | 1 | 4 | getUsersByAdvancedCondition | METHOD | 31 | APPLICATION |
| 58 | 1 | 4 | getUsersByType | METHOD | 31 | APPLICATION |
| 59 | 1 | 4 | createUser | METHOD | 31 | APPLICATION |
| 60 | 1 | 4 | getUserStatistics | METHOD | 31 | APPLICATION |
| 61 | 1 | 4 | validateSearchParams | METHOD | 31 | APPLICATION |
| 62 | 1 | 4 | processUserData | METHOD | 31 | APPLICATION |
| 63 | 1 | 4 | processAdvancedSearchParams | METHOD | 31 | APPLICATION |
| 64 | 1 | 4 | enrichUserData | METHOD | 31 | APPLICATION |
| 65 | 1 | 4 | isValidUserType | METHOD | 31 | APPLICATION |
| 66 | 1 | 4 | processUserTypeSpecific | METHOD | 31 | APPLICATION |
| 67 | 1 | 4 | validateUserData | METHOD | 31 | APPLICATION |
| 68 | 1 | 4 | checkUserDuplication | METHOD | 31 | APPLICATION |
| 69 | 1 | 4 | processUserCreationData | METHOD | 31 | APPLICATION |
| 70 | 1 | 4 | postCreateUserProcessing | METHOD | 31 | APPLICATION |
| 71 | 1 | 4 | processStatisticsData | METHOD | 31 | APPLICATION |

#### 6.5 SQL 컴포넌트 (MyBatis XML에서 추출)

| component_id | project_id | file_id | component_name | component_type | parent_id | layer |
|--------------|------------|---------|----------------|----------------|-----------|-------|
| 72 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 73 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 74 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 75 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 76 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 77 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 78 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 79 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 80 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 81 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 82 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 83 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 84 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 85 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 86 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 87 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 88 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 89 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 90 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 91 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 92 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 93 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 94 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 95 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 96 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 97 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 98 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 99 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 100 | 1 | 1 | SQL_CONTENT_SELECT | SQL_SELECT | - | DATA |
| 101 | 1 | 1 | SQL_CONTENT_INSERT | SQL_INSERT | - | DATA |
| 102 | 1 | 1 | SQL_CONTENT_UPDATE | SQL_UPDATE | - | DATA |
| 103 | 1 | 1 | SQL_CONTENT_UPDATE | SQL_UPDATE | - | DATA |
| 104 | 1 | 1 | SQL_CONTENT_UPDATE | SQL_UPDATE | - | DATA |

#### 6.6 JSP 컴포넌트

| component_id | project_id | file_id | component_name | component_type | parent_id | layer |
|--------------|------------|---------|----------------|----------------|-----------|-------|
| 105 | 1 | 5 | list.jsp | JSP | - | VIEW |

### 7. relationships 테이블

#### 7.1 CALL_QUERY 관계 (METHOD → SQL)

| relationship_id | src_id | dst_id | rel_type | confidence |
|-----------------|--------|--------|----------|------------|
| 1 | 40 | 72 | CALL_QUERY_M2S | 1.0 |
| 2 | 41 | 73 | CALL_QUERY_M2S | 1.0 |
| 3 | 42 | 74 | CALL_QUERY_M2S | 1.0 |
| 4 | 43 | 75 | CALL_QUERY_M2S | 1.0 |
| 5 | 44 | 101 | CALL_QUERY_M2S | 1.0 |
| 6 | 45 | 102 | CALL_QUERY_M2S | 1.0 |
| 7 | 46 | 103 | CALL_QUERY_M2S | 1.0 |
| 8 | 47 | 76 | CALL_QUERY_M2S | 1.0 |
| 9 | 48 | 77 | CALL_QUERY_M2S | 1.0 |
| 10 | 49 | 78 | CALL_QUERY_M2S | 1.0 |
| 11 | 50 | 79 | CALL_QUERY_M2S | 1.0 |
| 12 | 51 | 80 | CALL_QUERY_M2S | 1.0 |
| 13 | 52 | 81 | CALL_QUERY_M2S | 1.0 |
| 14 | 53 | 82 | CALL_QUERY_M2S | 1.0 |
| 15 | 54 | 83 | CALL_QUERY_M2S | 1.0 |
| 16 | 55 | 84 | CALL_QUERY_M2S | 1.0 |

#### 7.2 CALL_METHOD 관계 (METHOD → METHOD)

| relationship_id | src_id | dst_id | rel_type | confidence |
|-----------------|--------|--------|----------|------------|
| 17 | 35 | 56 | CALL_METHOD_C2S | 1.0 |
| 18 | 36 | 57 | CALL_METHOD_C2S | 1.0 |
| 19 | 37 | 58 | CALL_METHOD_C2S | 1.0 |
| 20 | 56 | 40 | CALL_METHOD_S2D | 1.0 |
| 21 | 57 | 41 | CALL_METHOD_S2D | 1.0 |
| 22 | 58 | 42 | CALL_METHOD_S2D | 1.0 |
| 23 | 59 | 44 | CALL_METHOD_S2D | 1.0 |
| 24 | 60 | 51 | CALL_METHOD_S2D | 1.0 |
| 25 | 60 | 52 | CALL_METHOD_S2D | 1.0 |
| 26 | 60 | 53 | CALL_METHOD_S2D | 1.0 |
| 27 | 60 | 54 | CALL_METHOD_S2D | 1.0 |

#### 7.3 USE_TABLE 관계 (METHOD → TABLE)

| relationship_id | src_id | dst_id | rel_type | confidence |
|-----------------|--------|--------|----------|------------|
| 28 | 40 | 1 | USE_TABLE_S2D | 1.0 |
| 29 | 41 | 1 | USE_TABLE_S2D | 1.0 |
| 30 | 42 | 1 | USE_TABLE_S2D | 1.0 |
| 31 | 43 | 1 | USE_TABLE_S2D | 1.0 |
| 32 | 44 | 1 | USE_TABLE_S2D | 1.0 |
| 33 | 45 | 1 | USE_TABLE_S2D | 1.0 |
| 34 | 46 | 1 | USE_TABLE_S2D | 1.0 |
| 35 | 47 | 1 | USE_TABLE_S2D | 1.0 |
| 36 | 48 | 1 | USE_TABLE_S2D | 1.0 |
| 37 | 49 | 1 | USE_TABLE_S2D | 1.0 |
| 38 | 50 | 1 | USE_TABLE_S2D | 1.0 |
| 39 | 51 | 1 | USE_TABLE_S2D | 1.0 |
| 40 | 52 | 1 | USE_TABLE_S2D | 1.0 |
| 41 | 53 | 1 | USE_TABLE_S2D | 1.0 |
| 42 | 54 | 1 | USE_TABLE_S2D | 1.0 |
| 43 | 55 | 1 | USE_TABLE_S2D | 1.0 |

#### 7.4 JOIN 관계 (TABLE → TABLE)

| relationship_id | src_id | dst_id | rel_type | confidence |
|-----------------|--------|--------|----------|------------|
| 44 | 1 | 4 | JOIN_EXPLICIT | 1.0 |
| 45 | 4 | 5 | JOIN_EXPLICIT | 1.0 |
| 46 | 5 | 6 | JOIN_EXPLICIT | 1.0 |
| 47 | 6 | 7 | JOIN_EXPLICIT | 1.0 |
| 48 | 6 | 8 | JOIN_EXPLICIT | 1.0 |
| 49 | 6 | 9 | JOIN_EXPLICIT | 1.0 |
| 50 | 6 | 10 | JOIN_EXPLICIT | 1.0 |
| 51 | 6 | 11 | JOIN_EXPLICIT | 1.0 |

#### 7.5 JSP → METHOD 관계

| relationship_id | src_id | dst_id | rel_type | confidence |
|-----------------|--------|--------|----------|------------|
| 52 | 105 | 35 | CALL_METHOD_C2S | 1.0 |
| 53 | 105 | 36 | CALL_METHOD_C2S | 1.0 |
| 54 | 105 | 37 | CALL_METHOD_C2S | 1.0 |

## 컴포넌트 타입별 통계

### components 테이블 - component_type별 건수

| component_type | 건수 |
|----------------|------|
| TABLE | 16 |
| COLUMN | 12+ |
| CLASS | 6+ |
| METHOD | 37+ |
| SQL_SELECT | 30+ |
| SQL_INSERT | 1+ |
| SQL_UPDATE | 3+ |
| SQL_DELETE | 0+ |
| SQL_MERGE | 0+ |
| JSP | 1+ |

### relationships 테이블 - rel_type별 건수

| rel_type | 건수 |
|----------|------|
| CALL_QUERY_M2S | 16+ |
| CALL_METHOD_C2S | 10+ |
| CALL_METHOD_S2D | 10+ |
| USE_TABLE_S2D | 16+ |
| JOIN_EXPLICIT | 8+ |
| JOIN_IMPLICIT | 0+ |

## 주요 분석 포인트

### 1. XML 분석 결과 (UserMapper.xml)
- **SELECT 쿼리**: 30개 이상 (findUsersByCondition, findUsersByAdvancedCondition, findUsersByType, findUserById, existsByUsername, existsByEmail, isEmailVerified, isPhoneVerified, getTotalUserCount, getActiveUserCount, getNewUsersTodayCount, getPremiumUserCount, getUserStatisticsByStatus, getUserStatisticsByType, getMonthlyRegistrationStats, findUsersWithOrderInfo, findUsersByComplexSearch 등)
- **INSERT 쿼리**: 1개 (createUser)
- **UPDATE 쿼리**: 3개 (updateUser, deleteUser, updateLastLogin)
- **DELETE 쿼리**: 0개 (논리삭제로 UPDATE 사용)
- **JOIN 관계**: USERS ↔ ORDERS, ORDERS ↔ ORDER_ITEMS, ORDER_ITEMS ↔ PRODUCTS 등

### 2. Java 분석 결과
- **클래스**: UserController, UserDao, UserService, MicroserviceController, ProductController, UserManagementController 등
- **메서드**: 각 클래스별로 10-20개 메서드
- **관계**: Controller → Service → DAO → SQL 호출 체인

### 3. JSP 분석 결과
- **JSP 파일**: list.jsp, searchResult.jsp, typeList.jsp, error.jsp 등
- **관계**: JSP → Controller 메서드 호출

### 4. 데이터베이스 스키마
- **테이블**: 16개 (USERS, USER_TYPES, CUSTOMERS, ORDERS, ORDER_ITEMS, PRODUCTS, CATEGORIES, BRANDS, SUPPLIERS, WAREHOUSES, INVENTORIES, PRODUCT_REVIEWS, DISCOUNTS, USER_ROLE, DYNAMIC_DATA, RELATED_DATA)
- **컬럼**: 각 테이블별로 5-15개 컬럼

## 검증 체크리스트

### ✅ 확인해야 할 항목들

1. **프로젝트 정보**
   - [ ] projects 테이블에 SampleSrc 프로젝트 등록
   - [ ] total_files가 87개 정도로 설정

2. **파일 정보**
   - [ ] files 테이블에 모든 Java, XML, JSP 파일 등록
   - [ ] file_type이 올바르게 설정 (java, xml, jsp)

3. **테이블/컬럼 정보**
   - [ ] tables 테이블에 CSV의 16개 테이블 등록
   - [ ] columns 테이블에 각 테이블의 컬럼들 등록
   - [ ] components 테이블에 TABLE, COLUMN 타입 컴포넌트 등록

4. **클래스/메서드 정보**
   - [ ] classes 테이블에 Java 클래스들 등록
   - [ ] components 테이블에 CLASS, METHOD 타입 컴포넌트 등록
   - [ ] parent_id로 클래스-메서드 관계 설정

5. **SQL 컴포넌트**
   - [ ] components 테이블에 SQL_SELECT, SQL_INSERT, SQL_UPDATE 타입 등록
   - [ ] UserMapper.xml의 모든 쿼리가 컴포넌트로 등록

6. **JSP 컴포넌트**
   - [ ] components 테이블에 JSP 타입 등록

7. **관계 정보**
   - [ ] CALL_QUERY_M2S: 메서드 → SQL 쿼리 관계
   - [ ] CALL_METHOD_C2S: Controller → Service 관계
   - [ ] CALL_METHOD_S2D: Service → DAO 관계
   - [ ] USE_TABLE_S2D: 메서드 → 테이블 관계
   - [ ] JOIN_EXPLICIT: 테이블 간 조인 관계
   - [ ] JSP → METHOD 관계

### ❌ 주의사항

1. **중복 방지**: 동일한 컴포넌트가 중복 등록되지 않았는지 확인
2. **참조 무결성**: parent_id, src_id, dst_id가 올바른 ID를 참조하는지 확인
3. **데이터 타입**: component_type, rel_type이 올바른 값으로 설정되었는지 확인
4. **해시값**: hash_value가 적절히 생성되었는지 확인
5. **오류 처리**: has_error='Y'인 레코드가 있는지 확인

## 예상 통계 요약

- **총 파일 수**: 87개
- **총 테이블 수**: 16개
- **총 컬럼 수**: 100개 이상
- **총 클래스 수**: 6개 이상
- **총 메서드 수**: 37개 이상
- **총 SQL 쿼리 수**: 35개 이상
- **총 JSP 파일 수**: 1개 이상
- **총 관계 수**: 54개 이상

이 정답지는 SampleSrc 프로젝트의 소스코드를 분석하여 예상되는 메타데이터 생성 결과를 정리한 것입니다. 실제 분석 결과와 비교하여 소스분석기의 정확도를 검증하는 데 사용할 수 있습니다.

