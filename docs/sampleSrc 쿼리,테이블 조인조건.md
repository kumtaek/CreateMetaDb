# sampleSrc 프로젝트 쿼리별 테이블 조인조건 분석

## 1. 분석 개요

- **분석 대상**: sampleSrc 프로젝트의 모든 SQL 쿼리
- **분석 범위**: XML 매퍼 파일 + Java 소스 파일의 조인 관계
- **분석 일시**: 2025년 9월 18일
- **총 조인 관계**: 39개 (XML: 34개, Java: 5개)
- **조인 유형**: EXPLICIT JOIN, IMPLICIT JOIN 구분

## 2. 조인 유형 분류

### 2.1 EXPLICIT JOIN (명시적 조인)
- ANSI SQL 표준 JOIN 구문 사용
- JOIN, LEFT JOIN, RIGHT JOIN, INNER JOIN 키워드 명시

### 2.2 IMPLICIT JOIN (암시적 조인)
- Oracle 전통 방식의 WHERE 절 조인
- FROM 절에 콤마(,)로 테이블 나열 후 WHERE 절에서 조인 조건 명시

## 3. 전체 테이블 조인 관계 매트릭스

### 3.1 XML 매퍼 파일 조인 관계

| 기준 테이블 | 조인 테이블 | 조인 조건 | 조인 유형 | JOIN 방식 | 사용 쿼리 수 | 주요 쿼리 |
|-------------|-------------|-----------|-----------|-----------|--------------|-----------|
| users | orders | users.user_id = orders.user_id | LEFT JOIN | EXPLICIT | 3개 | findUsersWithOrderInfo, selectUserProfile, findUsersByComplexSearch |
| users | user_info | users.user_id = user_info.user_id | LEFT JOIN | EXPLICIT | 3개 | selectUsersV2, selectUserById, selectUserProfile |
| users | user_profiles | users.user_id = user_profiles.user_id | LEFT JOIN | EXPLICIT | 1개 | selectUserProfile |
| users | user_types | users.type_id = user_types.id | WHERE 절 | IMPLICIT | 1개 | getUsersWithTypes |
| users | user_roles | users.id = user_roles.user_id | LEFT JOIN | EXPLICIT | 2개 | getUserWithDetails, getMixedJoin |
| orders | users | orders.user_id = users.user_id | JOIN | EXPLICIT | 4개 | selectOrderDetails, selectOrdersV2, selectOrdersFromInternalService |
| orders | order_items | orders.order_id = order_items.order_id | JOIN/LEFT JOIN | EXPLICIT | 4개 | selectOrderDetails, selectOrdersV2, selectProductsV2 |
| products | categories | products.category_id = categories.category_id | JOIN/LEFT JOIN | EXPLICIT | 4개 | selectProductsByAdvancedCondition, selectProductsV2, selectProductsFromInternalService |
| products | brands | products.brand_id = brands.brand_id | LEFT JOIN | EXPLICIT | 3개 | selectProductsByAdvancedCondition, selectProductsFromInternalService |
| products | order_items | products.product_id = order_items.product_id | JOIN/LEFT JOIN | EXPLICIT | 3개 | selectOrderDetails, selectProductsV2 |
| user_roles | roles | user_roles.role_id = roles.role_id | LEFT JOIN | EXPLICIT | 2개 | getUserWithDetails, getMixedJoin |
| USERS | DEPARTMENTS | USERS.DEPT_ID = DEPARTMENTS.DEPT_ID | WHERE 절 | IMPLICIT | 6개 | findUsers, findUsersWithAnsiJoin, findUsersWithScatteredConditions |
| USERS | USER_PROFILES | USERS.USER_ID = USER_PROFILES.USER_ID | WHERE 절 | IMPLICIT | 5개 | findUsers, findUsersWithAliasOmission, findUsersWithMixedJoins |
| USERS | USER_TYPES | USERS.USER_TYPE = USER_TYPES.TYPE_CODE | WHERE 절 | IMPLICIT | 3개 | findUsersWithMixedJoins, findUsersWithScatteredConditions |
| USERS | USER_ROLES | USERS.USER_ID = USER_ROLES.USER_ID | WHERE 절 | IMPLICIT | 2개 | findUsersWithScatteredConditions |
| USERS | EMPLOYEES | USERS.USER_ID = EMPLOYEES.USER_ID | WHERE 절 | IMPLICIT | 3개 | selectUsersAndEmployeesWithSameColumn, selectMultipleImplicitJoinsWithSameColumn |
| ORDERS | CUSTOMERS | ORDERS.CUSTOMER_ID = CUSTOMERS.CUSTOMER_ID | WHERE 절 | IMPLICIT | 4개 | findComplexJoins, findOrdersWithScatteredJoins, findComplexScatteredJoins |
| ORDERS | ORDER_ITEMS | ORDERS.ORDER_ID = ORDER_ITEMS.ORDER_ID | WHERE 절 | IMPLICIT | 3개 | findComplexJoins, findOrdersWithScatteredJoins |
| PRODUCTS | CATEGORIES | PRODUCTS.CATEGORY_ID = CATEGORIES.CATEGORY_ID | WHERE 절 | IMPLICIT | 2개 | findOrdersWithScatteredJoins |
| PRODUCTS | BRANDS | PRODUCTS.BRAND_ID = BRANDS.BRAND_ID | WHERE 절 | IMPLICIT | 1개 | findOrdersWithScatteredJoins |
| USER_ROLES | ROLES | USER_ROLES.ROLE_ID = ROLES.ROLE_ID | WHERE 절 | IMPLICIT | 1개 | findUsersWithScatteredConditions |
| EMPLOYEES | DEPARTMENTS | EMPLOYEES.DEPT_ID = DEPARTMENTS.DEPT_ID | JOIN | EXPLICIT | 2개 | selectComplexQueryExample, selectQueryWithExistsAndInSubqueries |
| EMPLOYEES | PROJECT_MEMBERS | EMPLOYEES.USER_ID = PROJECT_MEMBERS.USER_ID | JOIN | EXPLICIT | 2개 | selectComplexQueryExample, selectQueryWithExistsAndInSubqueries |
| PROJECT_MEMBERS | PROJECTS | PROJECT_MEMBERS.PROJECT_ID = PROJECTS.PROJECT_ID | JOIN | EXPLICIT | 2개 | selectComplexQueryExample, selectQueryWithExistsAndInSubqueries |

### 3.2 Java 소스 조인 관계 (DirectQueryServlet.java)

| 기준 테이블 | 조인 테이블 | 조인 조건 | 조인 유형 | JOIN 방식 | 사용 메서드 | 설명 |
|-------------|-------------|-----------|-----------|-----------|-------------|------|
| orders | users | orders.user_id = users.user_id | JOIN | EXPLICIT | queryOrdersDirectly | 주문-사용자 정보 조회 |
| products | categories | products.category_id = categories.category_id | LEFT JOIN | EXPLICIT | queryProductsDirectly | 상품-카테고리 정보 조회 |
| users | orders | users.user_id = orders.user_id | LEFT JOIN | EXPLICIT | queryComplexDataDirectly | 사용자-주문 통계 |
| orders | order_items | orders.order_id = order_items.order_id | LEFT JOIN | EXPLICIT | queryComplexDataDirectly | 주문-아이템 상세 |
| order_items | products | order_items.product_id = products.product_id | LEFT JOIN | EXPLICIT | queryComplexDataDirectly | 아이템-상품 정보 |

## 4. 조인 패턴별 상세 분석

### 4.1 EXPLICIT JOIN 패턴

#### 4.1.1 표준 LEFT JOIN 패턴
| 쿼리 ID | 파일 | 조인 체인 | 특징 |
|---------|------|-----------|------|
| selectUserProfile | MicroserviceMapper.xml | users → user_info → user_profiles → orders | 사용자 중심 확장 정보 |
| selectOrderDetails | MicroserviceMapper.xml | orders → users → order_items → products | 주문 중심 상세 정보 |
| selectProductsByAdvancedCondition | ProductMapper.xml | products → categories → brands | 상품 중심 분류 정보 |

#### 4.1.2 복합 JOIN 패턴
| 쿼리 ID | 파일 | JOIN 유형 조합 | 조인 수 |
|---------|------|----------------|---------|
| selectOrderDetails | MicroserviceMapper.xml | JOIN + JOIN + JOIN | 3개 |
| selectUserProfile | MicroserviceMapper.xml | LEFT JOIN + LEFT JOIN + LEFT JOIN | 3개 |
| getMixedJoin | ImplicitJoinMapper.xml | IMPLICIT + LEFT JOIN + INNER JOIN | 혼합 |

### 4.2 IMPLICIT JOIN 패턴 (Oracle 스타일)

#### 4.2.1 기본 WHERE 절 조인
| 쿼리 ID | 파일 | 테이블 수 | 조인 조건 수 | 특징 |
|---------|------|-----------|-------------|------|
| findUsers | UserMapper.xml(dynamicquery) | 3개 | 2개 | 기본 Oracle 스타일 |
| getUsersWithTypes | ImplicitJoinMapper.xml | 2개 | 1개 | 단순 조인 |
| getProductsWithCategoryAndBrand | ImplicitJoinMapper.xml | 3개 | 2개 | 체인 조인 |

#### 4.2.2 복잡한 IMPLICIT JOIN
| 쿼리 ID | 파일 | 테이블 수 | 조인 조건 수 | 복잡도 |
|---------|------|-----------|-------------|---------|
| findUsersWithScatteredConditions | UserMapper.xml(dynamicquery) | 6개 | 5개 | 매우 높음 |
| findOrdersWithScatteredJoins | UserMapper.xml(dynamicquery) | 6개 | 5개 | 매우 높음 |
| findComplexScatteredJoins | UserMapper.xml(dynamicquery) | 6개 | 5개 | 매우 높음 |

### 4.3 Java 소스 조인 패턴 (DirectQueryServlet.java)

#### 4.3.1 동적 EXPLICIT JOIN
| 메서드 | 조인 패턴 | 특징 |
|--------|-----------|------|
| queryOrdersDirectly | orders → users | 기본 내부 조인 |
| queryProductsDirectly | products → categories | 선택적 카테고리 정보 |
| queryComplexDataDirectly | users → orders → order_items → products | 4단계 체인 조인 |

#### 4.3.2 Java 동적 쿼리 특성
- **런타임 조건부 조인**: 파라미터에 따라 조인 여부 결정
- **StringBuilder 기반**: 동적으로 쿼리 문자열 조합
- **EXPLICIT JOIN만 사용**: 표준 ANSI SQL 준수

### 4.4 문제가 있는 조인 패턴 (has_error='Y')

#### 4.4.1 별칭 생략 에러
| 쿼리 ID | 파일 | 에러 조인 조건 | 올바른 조인 조건 |
|---------|------|----------------|------------------|
| selectUsersWithImplicitDeptId | ImplicitJoinTestMapper.xml | u.DEPT_ID = DEPT_ID | u.DEPT_ID = d.DEPT_ID |
| selectUsersAndEmployeesWithSameColumn | ImplicitJoinTestMapper.xml | u.DEPT_ID = DEPT_ID | u.DEPT_ID = d.DEPT_ID |
| selectUsersWithComplexImplicitJoin | ImplicitJoinTestMapper.xml | u.DEPT_ID = DEPT_ID | u.DEPT_ID = d.DEPT_ID |

#### 4.4.2 존재하지 않는 테이블 참조
| 쿼리 ID | 파일 | 에러 테이블 | 에러 조인 조건 |
|---------|------|-------------|----------------|
| selectFromNonExistentTable | MixedErrorMapper.xml | NONEXISTENT_TABLE | - |
| selectComplexError | MixedErrorMapper.xml | NONEXISTENT_TABLE | users.id = NONEXISTENT_TABLE.user_id |

## 5. 조인 복잡도별 분류

### 5.1 단일 테이블 쿼리 (조인 없음)
| 쿼리 ID | 파일/메서드 | 테이블 | 쿼리 유형 | 비고 |
|---------|-------------|--------|-----------|------|
| findUserById | UserMapper.xml | users | SELECT | 단순 조회 |
| selectProductById | ProductMapper.xml | products | SELECT | 단순 조회 |
| getTotalUserCount | UserMapper.xml | users | SELECT | 집계 함수 |
| queryUsersDirectly | DirectQueryServlet.java | users | SELECT | Java 동적 쿼리 |
| insertUserDirectly | DirectQueryServlet.java | users | INSERT | Java 동적 INSERT |

### 5.2 단순 조인 (2개 테이블)
| 쿼리 ID | 파일/메서드 | 테이블 1 | 테이블 2 | 조인 방식 |
|---------|-------------|-----------|-----------|-----------|
| findUsersWithOrderInfo | UserMapper.xml | users | orders | EXPLICIT LEFT JOIN |
| selectUserById | UserManagementMapper.xml | users | user_info | EXPLICIT LEFT JOIN |
| getUsersWithTypes | ImplicitJoinMapper.xml | users | user_types | IMPLICIT |
| queryOrdersDirectly | DirectQueryServlet.java | orders | users | EXPLICIT JOIN |
| queryProductsDirectly | DirectQueryServlet.java | products | categories | EXPLICIT LEFT JOIN |

### 5.3 중간 복잡도 (3개 테이블)
| 쿼리 ID | 파일/메서드 | 테이블 조합 | 조인 방식 |
|---------|-------------|-----------|-----------|
| selectProductsByAdvancedCondition | ProductMapper.xml | products + categories + brands | EXPLICIT LEFT JOIN |
| getProductsWithCategoryAndBrand | ImplicitJoinMapper.xml | products + categories + brands | IMPLICIT |
| findUsersWithAnsiJoin | UserMapper.xml(dynamicquery) | USERS + DEPARTMENTS + USER_PROFILES | EXPLICIT |

### 5.4 고복잡도 (4개 이상 테이블)
| 쿼리 ID | 파일/메서드 | 테이블 수 | 조인 방식 | 특징 |
|---------|-------------|-----------|-----------|------|
| selectOrderDetails | MicroserviceMapper.xml | 4개 | EXPLICIT | orders → users → order_items → products |
| selectUserProfile | MicroserviceMapper.xml | 4개 | EXPLICIT | users 중심 확장 |
| queryComplexDataDirectly | DirectQueryServlet.java | 4개 | EXPLICIT | Java 복합 조인 쿼리 |
| findUsersWithScatteredConditions | UserMapper.xml(dynamicquery) | 6개 | IMPLICIT | 분산된 조인 조건 |
| findOrdersWithScatteredJoins | UserMapper.xml(dynamicquery) | 6개 | IMPLICIT | 복잡한 비즈니스 로직 |
| selectComplexQueryExample | ImplicitJoinTestMapper.xml | 5개 | EXPLICIT + 서브쿼리 | 스칼라 서브쿼리 포함 |

## 6. 조인 조건 패턴 분석

### 6.1 표준 PK-FK 조인
| 조인 조건 | 빈도 | 주요 사용 쿼리 |
|-----------|------|----------------|
| users.user_id = orders.user_id | 7회 | 사용자-주문 관계 |
| products.category_id = categories.category_id | 4회 | 상품-카테고리 관계 |
| orders.order_id = order_items.order_id | 4회 | 주문-아이템 관계 |
| users.user_id = user_info.user_id | 3회 | 사용자-상세정보 관계 |

### 6.2 Oracle IMPLICIT JOIN 조건
| 조인 조건 | 빈도 | 특징 |
|-----------|------|------|
| u.DEPT_ID = d.DEPT_ID | 6회 | 사용자-부서 관계 (Oracle 스타일) |
| u.USER_ID = p.USER_ID | 5회 | 사용자-프로필 관계 |
| u.USER_TYPE = ut.TYPE_CODE | 3회 | 사용자-타입 관계 |

### 6.3 문제가 있는 조인 조건 (has_error='Y')
| 에러 조인 조건 | 올바른 조건 | 에러 유형 | 파일 |
|----------------|-------------|-----------|------|
| u.DEPT_ID = DEPT_ID | u.DEPT_ID = d.DEPT_ID | 별칭 생략 | ImplicitJoinTestMapper.xml |
| u.USER_ID = USER_ID | u.USER_ID = p.USER_ID | 별칭 생략 | ImplicitJoinTestMapper.xml |
| users.id = NONEXISTENT_TABLE.user_id | - | 존재하지 않는 테이블 | MixedErrorMapper.xml |

## 7. 파일별 조인 특성 분석

### 7.1 UserMapper.xml (메인) - EXPLICIT JOIN 중심
| 조인 관계 | 조인 유형 | 사용 빈도 | 비고 |
|-----------|-----------|-----------|------|
| users ↔ orders | LEFT JOIN | 2회 | 사용자 중심 주문 정보 |
| users ↔ orders (서브쿼리) | LEFT JOIN | 1회 | 복잡한 동적 검색 |

### 7.2 MicroserviceMapper.xml - 복합 EXPLICIT JOIN
| 조인 관계 | 조인 유형 | 사용 빈도 | 특징 |
|-----------|-----------|-----------|------|
| users → user_info → user_profiles → orders | LEFT JOIN 체인 | 1회 | 통합 사용자 정보 |
| orders → users → order_items → products | JOIN 체인 | 1회 | 통합 주문 상세 |

### 7.3 UserMapper.xml (dynamicquery) - IMPLICIT JOIN 중심
| 조인 관계 | 조인 유형 | 사용 빈도 | 특징 |
|-----------|-----------|-----------|------|
| USERS, DEPARTMENTS, USER_PROFILES | WHERE 절 | 3회 | Oracle 스타일 기본 패턴 |
| 6개 테이블 복합 조인 | WHERE 절 | 3회 | 매우 복잡한 비즈니스 로직 |

### 7.4 ImplicitJoinMapper.xml - 혼합 JOIN
| 조인 관계 | 조인 유형 | 사용 빈도 | 특징 |
|-----------|-----------|-----------|------|
| users, user_types | IMPLICIT | 1회 | 기본 Oracle 스타일 |
| users + EXPLICIT JOIN | 혼합 | 1회 | IMPLICIT + EXPLICIT 혼용 |

### 7.5 ProductMapper.xml - 상품 중심 EXPLICIT JOIN
| 조인 관계 | 조인 유형 | 사용 빈도 | 특징 |
|-----------|-----------|-----------|------|
| products → categories | LEFT JOIN | 2회 | 상품 분류 정보 |
| products → brands | LEFT JOIN | 1회 | 상품 브랜드 정보 |

## 8. 조인 조건 품질 분석

### 8.1 정상 조인 조건 (has_error='N')
- **총 68개 쿼리**: 모든 조인 조건이 올바르게 작성됨
- **표준 준수**: PK-FK 관계를 정확히 반영
- **성능 고려**: 적절한 인덱스 활용 가능한 조건

### 8.2 문제 조인 조건 (has_error='Y')
- **총 6개 쿼리**: 조인 조건에 문제 있음
- **별칭 생략**: 3개 (ImplicitJoinTestMapper.xml)
- **존재하지 않는 테이블**: 3개 (MixedErrorMapper.xml)

### 8.3 조인 방식별 에러율
| 조인 방식 | 총 쿼리 수 | 에러 쿼리 수 | 에러율 | 비고 |
|-----------|------------|--------------|--------|------|
| EXPLICIT JOIN | 50개 | 0개 | 0% | 매우 안정적 (XML + Java) |
| IMPLICIT JOIN | 29개 | 6개 | 20.7% | 별칭 생략 위험 (XML만) |

### 8.4 소스 유형별 조인 특성
| 소스 유형 | 총 조인 관계 | EXPLICIT | IMPLICIT | 특징 |
|-----------|--------------|----------|----------|------|
| XML 매퍼 | 34개 | 25개 (73.5%) | 9개 (26.5%) | 혼합 사용 |
| Java 소스 | 5개 | 5개 (100%) | 0개 (0%) | EXPLICIT만 사용 |
| **전체** | **39개** | **30개 (76.9%)** | **9개 (23.1%)** | **EXPLICIT 우세** |

## 9. 권장사항

### 9.1 조인 방식 표준화
1. **EXPLICIT JOIN 우선**: 가독성과 안정성이 높음
2. **IMPLICIT JOIN 제한적 사용**: Oracle 환경에서만 필요시 사용
3. **혼합 사용 지양**: 하나의 쿼리에서 두 방식 혼용 지양

### 9.2 조인 조건 품질 개선
1. **별칭 명시**: 모든 테이블에 명확한 별칭 사용
2. **조건 검증**: 존재하지 않는 테이블/컬럼 참조 제거
3. **성능 최적화**: 조인 순서와 인덱스 활용 고려

### 9.3 복잡도 관리
1. **단순화**: 6개 이상 테이블 조인 시 쿼리 분할 검토
2. **서브쿼리 활용**: 복잡한 조인 대신 서브쿼리 사용 고려
3. **뷰 활용**: 자주 사용되는 복잡한 조인은 뷰로 정의

### 9.4 Java 소스 조인 품질
1. **표준 준수**: 모든 Java 쿼리가 EXPLICIT JOIN 사용
2. **동적 생성**: 런타임에 조건부 조인 구성
3. **안정성**: 에러율 0%로 매우 안정적

---

**분석 완료일**: 2025년 9월 18일  
**총 분석 조인 관계**: 39개 (XML: 34개, Java: 5개)  
**EXPLICIT JOIN**: 30개 (76.9%)  
**IMPLICIT JOIN**: 9개 (23.1%)  
**Java 소스 에러율**: 0% (매우 안정적)
