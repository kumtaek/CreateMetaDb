# sampleSrc 프로젝트 쿼리별 테이블 조인조건 분석 v2

## 1. 분석 개요

- **분석 대상**: sampleSrc 프로젝트의 모든 SQL 쿼리
- **분석 범위**: XML 매퍼 파일 + Java 소스 파일의 조인 관계
- **분석 일시**: 2025년 9월 18일
- **버전**: v2 (업데이트)
- **총 조인 관계**: 78개 (v1: 39개 → v2: 78개, +39개 증가)
- **조인 유형**: EXPLICIT JOIN, IMPLICIT JOIN 구분

## 2. 조인 유형 분류

### 2.1 EXPLICIT JOIN (명시적 조인)
- ANSI SQL 표준 JOIN 구문 사용
- JOIN, LEFT JOIN, RIGHT JOIN, INNER JOIN 키워드 명시

### 2.2 IMPLICIT JOIN (암시적 조인)
- Oracle 전통 방식의 WHERE 절 조인
- FROM 절에 콤마(,)로 테이블 나열 후 WHERE 절에서 조인 조건 명시

### 2.3 DYNAMIC JOIN (동적 조인) - v2 신규
- 런타임에 조건에 따라 결정되는 조인
- + 연산자, String.format, 조건부 로직 사용

## 3. 전체 테이블 조인 관계 매트릭스

### 3.1 XML 매퍼 파일 조인 관계

| 기준 테이블 | 조인 테이블 | 조인 조건 | 조인 유형 | JOIN 방식 | 사용 쿼리 수 | 주요 쿼리 |
|-------------|-------------|-----------|-----------|-----------|--------------|-----------|
| users | orders | users.user_id = orders.user_id | LEFT JOIN | EXPLICIT | 3개 | findUsersWithOrderInfo, selectUserProfile, findUsersByComplexSearch |
| users | user_info | users.user_id = user_info.user_id | LEFT JOIN | EXPLICIT | 3개 | selectUsersV2, selectUserById, selectUserProfile |
| users | user_profiles | users.user_id = user_profiles.user_id | LEFT JOIN | EXPLICIT | 3개 | selectUserProfile, getDirectUserList, getDirectDynamicUserData |
| users | user_types | users.type_id = user_types.id | WHERE 절 | IMPLICIT | 1개 | getUsersWithTypes |
| users | user_roles | users.id = user_roles.user_id | LEFT JOIN | EXPLICIT | 2개 | getUserWithDetails, getMixedJoin |
| users | user_activities | users.user_id = user_activities.user_id | LEFT JOIN | EXPLICIT | 2개 | batchDirectUpdateUserStatus, deleteDirectInactiveUsers |
| orders | users | orders.user_id = users.user_id | JOIN | EXPLICIT | 6개 | selectOrderDetails, selectOrdersV2, selectOrdersFromInternalService, getDirectOrderSummary, queryOrdersDirectly |
| orders | order_items | orders.order_id = order_items.order_id | JOIN/LEFT JOIN | EXPLICIT | 8개 | selectOrderDetails, selectOrdersV2, selectProductsV2, getDirectOrderSummary, getDirectTopCustomers, queryComplexDataDirectly |
| products | categories | products.category_id = categories.category_id | JOIN/LEFT JOIN | EXPLICIT | 8개 | selectProductsByAdvancedCondition, selectProductsV2, selectProductsFromInternalService, getDirectOrderSummary, queryProductsDirectly |
| products | brands | products.brand_id = brands.brand_id | LEFT JOIN | EXPLICIT | 5个 | selectProductsByAdvancedCondition, selectProductsFromInternalService, getProductsWithCategoryAndBrand |
| products | order_items | products.product_id = order_items.product_id | JOIN/LEFT JOIN | EXPLICIT | 6개 | selectOrderDetails, selectProductsV2, getDirectOrderSummary, getDirectTopCustomers, queryComplexDataDirectly |
| products | inventory_${environment} | products.product_id = inventory.product_id | INNER JOIN | EXPLICIT | 2개 | executeInventoryOptimizationAnalysis, executeRealTimeDashboardMetrics |
| user_roles | roles | user_roles.role_id = roles.role_id | LEFT JOIN | EXPLICIT | 2개 | getUserWithDetails, getMixedJoin |

### 3.2 새로 추가된 복잡한 조인 관계 (v2)

#### ComplexEnterpriseMapper.xml의 조인 관계
| 기준 테이블 | 조인 테이블 | 조인 조건 | 조인 유형 | JOIN 방식 | 사용 쿼리 | 특징 |
|-------------|-------------|-----------|-----------|-----------|-----------|------|
| transactions_${environment}_${year} | users_${environment} | t.user_id = u.user_id | INNER JOIN | EXPLICIT | executeFinancialReconciliation | 환경별 동적 테이블 |
| transactions_${environment}_${year} | products_${environment} | t.product_id = p.product_id | INNER JOIN | EXPLICIT | executeFinancialReconciliation | 환경별 동적 테이블 |
| transactions_${environment}_${year} | orders_${environment} | t.order_id = o.order_id | INNER JOIN | EXPLICIT | executeFinancialReconciliation | 환경별 동적 테이블 |
| users_${environment} | user_tiers_${environment} | u.user_id = ut.user_id | LEFT JOIN | EXPLICIT | executeFinancialReconciliation | 사용자 등급 정보 |
| users_${environment} | user_kyc_${environment} | u.user_id = kyc.user_id | INNER JOIN | EXPLICIT | executeFinancialReconciliation | KYC 정보 조인 |
| users_${environment} | orders_${environment} | u.user_id = o.user_id | INNER JOIN | EXPLICIT | executeCustomerSegmentationAnalysis | 고객 행동 분석 |
| orders_${environment} | order_items_${environment} | o.order_id = oi.order_id | INNER JOIN | EXPLICIT | executeCustomerSegmentationAnalysis | 주문 상세 분석 |
| order_items_${environment} | products_${environment} | oi.product_id = p.product_id | INNER JOIN | EXPLICIT | executeCustomerSegmentationAnalysis | 상품 선호도 분석 |
| products_${environment} | categories_${environment} | p.category_id = c.category_id | INNER JOIN | EXPLICIT | executeCustomerSegmentationAnalysis | 카테고리별 분석 |
| users_${environment} | user_preferences_${environment} | u.user_id = up.user_id | LEFT JOIN | EXPLICIT | executeCustomerSegmentationAnalysis | 사용자 선호도 |
| orders_${environment} | payments_${environment} | o.order_id = pm.order_id | INNER JOIN | EXPLICIT | executeCustomerSegmentationAnalysis | 결제 행동 분석 |
| products_${environment} | inventory_${environment} | p.product_id = i.product_id | INNER JOIN | EXPLICIT | executeInventoryOptimizationAnalysis | 재고 최적화 |
| users_${environment} | user_settlements_${environment} | u.user_id = us.user_id | MERGE | EXPLICIT | executeBatchSettlementProcessing | 정산 정보 통합 |

#### DirectXmlQueryMapper.xml의 조인 관계
| 기준 테이블 | 조인 테이블 | 조인 조건 | 조인 유형 | JOIN 방식 | 사용 쿼리 | 특징 |
|-------------|-------------|-----------|-----------|-----------|-----------|------|
| users | user_profiles | u.user_id = p.user_id | LEFT JOIN | EXPLICIT | getDirectUserList | XML 직접 조인 |
| users | orders | u.user_id = o.user_id | INNER JOIN | EXPLICIT | getDirectOrderSummary | XML 직접 복합 조인 |
| orders | order_items | o.order_id = oi.order_id | INNER JOIN | EXPLICIT | getDirectOrderSummary | XML 직접 조인 |
| order_items | products | oi.product_id = p.product_id | INNER JOIN | EXPLICIT | getDirectOrderSummary | XML 직접 조인 |
| products | categories | p.category_id = c.category_id | INNER JOIN | EXPLICIT | getDirectOrderSummary | XML 직접 조인 |
| users | orders | u.user_id = o.user_id | LEFT JOIN | EXPLICIT | getDirectUserStatistics | XML 통계 조인 |
| orders | payments | o.order_id = pm.order_id | LEFT JOIN | EXPLICIT | getDirectUserStatistics | XML 결제 조인 |
| users | user_profiles | u.user_id = p.user_id | WHERE 조건 | IMPLICIT | updateDirectUserLastActivity | XML 업데이트 조인 |
| orders | order_items | o.order_id = oi.order_id | MERGE | EXPLICIT | mergeDirectUserPreferences | XML MERGE 조인 |
| order_items | products | oi.product_id = p.product_id | MERGE | EXPLICIT | mergeDirectUserPreferences | XML MERGE 조인 |
| products | categories | p.category_id = c.category_id | MERGE | EXPLICIT | mergeDirectUserPreferences | XML MERGE 조인 |

### 3.3 기존 조인 관계 (v1에서 유지)

#### Oracle IMPLICIT JOIN 패턴
| 기준 테이블 | 조인 테이블 | 조인 조건 | 조인 유형 | JOIN 방식 | 사용 쿼리 수 | 주요 쿼리 |
|-------------|-------------|-----------|-----------|-----------|--------------|-----------|
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

### 3.4 Java 소스 조인 관계 (v2 확장)

#### DirectQueryServlet.java의 조인 관계
| 기준 테이블 | 조인 테이블 | 조인 조건 | 조인 유형 | JOIN 방식 | 사용 메서드 | 설명 |
|-------------|-------------|-----------|-----------|-----------|-------------|------|
| orders | users | orders.user_id = users.user_id | JOIN | EXPLICIT | queryOrdersDirectly | 주문-사용자 정보 조회 |
| products | categories | products.category_id = categories.category_id | LEFT JOIN | EXPLICIT | queryProductsDirectly | 상품-카테고리 정보 조회 |
| users | orders | users.user_id = orders.user_id | LEFT JOIN | EXPLICIT | queryComplexDataDirectly | 사용자-주문 통계 |
| orders | order_items | orders.order_id = order_items.order_id | LEFT JOIN | EXPLICIT | queryComplexDataDirectly | 주문-아이템 상세 |
| order_items | products | order_items.product_id = products.product_id | LEFT JOIN | EXPLICIT | queryComplexDataDirectly | 아이템-상품 정보 |

#### CoreSqlPatternDao.java의 동적 조인 관계 (🆕 새로 추가)
| 기준 테이블 | 조인 테이블 | 조인 조건 | 조인 유형 | JOIN 방식 | 사용 메서드 | 특징 |
|-------------|-------------|-----------|-----------|-----------|-------------|------|
| 동적 테이블 | user_profiles | mainTable.user_id = user_profiles.user_id | LEFT JOIN | DYNAMIC | selectWithPlusOperatorJoin | + 연산자 동적 조인 |
| 동적 테이블 | orders | mainTable.user_id = orders.user_id | LEFT JOIN | DYNAMIC | selectWithPlusOperatorJoin | + 연산자 동적 조인 |
| 동적 테이블 | products | mainTable.product_id = products.product_id | INNER JOIN | DYNAMIC | selectWithPlusOperatorJoin | + 연산자 동적 조인 |
| 동적 테이블 | categories | products.category_id = categories.category_id | LEFT JOIN | DYNAMIC | selectWithPlusOperatorJoin | + 연산자 동적 조인 |
| users_${environment} | products_${environment} | u.user_id = p.created_by | 동적 JOIN | DYNAMIC | selectWithStringFormat | String.format 동적 조인 |
| users_${environment} | orders_${environment} | u.user_id = o.user_id | 동적 JOIN | DYNAMIC | selectWithStringFormat | String.format 동적 조인 |
| orders_${environment} | payments_${environment} | o.order_id = pm.order_id | LEFT JOIN | DYNAMIC | selectWithStringFormat | String.format 조건부 조인 |
| baseTable | users | b.user_id = u.user_id | LEFT JOIN | CONDITIONAL | selectWithConditionalJoin | 조건부 조인 |
| baseTable | products | b.product_id = p.product_id | LEFT JOIN | CONDITIONAL | selectWithConditionalJoin | 조건부 조인 |
| baseTable | orders | b.order_id = o.order_id | LEFT JOIN | CONDITIONAL | selectWithConditionalJoin | 조건부 조인 |
| baseTable | categories | p.category_id = c.category_id | LEFT JOIN | CONDITIONAL | selectWithConditionalJoin | 조건부 조인 |
| baseTable | payments | o.order_id = pm.order_id | LEFT JOIN | CONDITIONAL | selectWithConditionalJoin | 조건부 조인 |

#### 기업급 복잡 쿼리의 조인 관계 (CoreSqlPatternDao.java)
| 기준 테이블 | 조인 테이블 | 조인 조건 | 조인 유형 | JOIN 방식 | 사용 메서드 | 복잡도 |
|-------------|-------------|-----------|-----------|-----------|-------------|---------|
| transactions_${dcPrefix}_${year} | users_${dcPrefix} | t.user_id = u.user_id | INNER JOIN | DYNAMIC | executeEnterpriseComplexQuery | 매우 높음 |
| transactions_${dcPrefix}_${year} | products_${dcPrefix} | t.product_id = p.product_id | INNER JOIN | DYNAMIC | executeEnterpriseComplexQuery | 매우 높음 |
| users_${dcPrefix} | user_tiers_${dcPrefix} | u.user_id = ut.user_id | INNER JOIN | DYNAMIC | executeEnterpriseComplexQuery | 매우 높음 |
| users_${dcPrefix} | orders_${dcPrefix} | u.user_id = o.user_id | INNER JOIN | DYNAMIC | executeEnterpriseComplexQuery | 매우 높음 |
| orders_${dcPrefix} | order_items_${dcPrefix} | o.order_id = oi.order_id | INNER JOIN | DYNAMIC | executeEnterpriseComplexQuery | 매우 높음 |
| order_items_${dcPrefix} | products_${dcPrefix} | oi.product_id = p.product_id | INNER JOIN | DYNAMIC | executeEnterpriseComplexQuery | 매우 높음 |
| products_${dcPrefix} | categories_${dcPrefix} | p.category_id = c.category_id | INNER JOIN | DYNAMIC | executeEnterpriseComplexQuery | 매우 높음 |

#### Oracle 데이터 웨어하우스 조인 (CoreSqlPatternDao.java)
| 기준 테이블 | 조인 테이블 | 조인 조건 | 조인 유형 | JOIN 방식 | 사용 메서드 | 특징 |
|-------------|-------------|-----------|-----------|-----------|-------------|------|
| orders_${environment} | order_items_${environment} | o.order_id = oi.order_id | WHERE 절 | IMPLICIT | executeOracleDataWarehouseQuery | Oracle 스타일 |
| order_items_${environment} | products_${environment} | oi.product_id = p.product_id | WHERE 절 | IMPLICIT | executeOracleDataWarehouseQuery | Oracle 스타일 |
| users_${environment} | user_profiles_${environment} | u.user_id = p.user_id | WHERE 절 | IMPLICIT | executeOracleDataWarehouseQuery | Oracle 스타일 |
| products_${environment} | suppliers_${environment} | pr.supplier_id = s.supplier_id | WHERE 절 | IMPLICIT | executeOracleDataWarehouseQuery | Oracle 스타일 |

#### UnsupportedPatternDao.java의 미지원 조인 패턴 (🆕 새로 추가)
| 기준 테이블 | 조인 테이블 | 조인 조건 | 조인 유형 | JOIN 방식 | 사용 메서드 | 미지원 이유 |
|-------------|-------------|-----------|-----------|-----------|-------------|-----------|
| users | 동적 테이블 | CONCAT + + 연산자 | 혼합 | UNSUPPORTED | findUsersByConcatPattern | CONCAT과 + 연산자 혼합 |
| analytics_${tableSuffix} | 다중 테이블 | String.format + + 연산자 | 혼합 | UNSUPPORTED | getAnalyticsByFormatAndDynamicTable | 패턴 혼합 복잡도 |
| users | 서브쿼리 테이블 | 복잡한 CASE + 서브쿼리 | 혼합 | UNSUPPORTED | getComplexCasePatternData | CASE문과 서브쿼리 혼합 |
| users, orders, products | 다중 서브쿼리 | 서브쿼리 + 문자열 조작 | 혼합 | UNSUPPORTED | getSubqueryWithStringManipulation | 서브쿼리와 문자열 처리 혼합 |

## 4. 조인 패턴별 상세 분석 (v2 확장)

### 4.1 EXPLICIT JOIN 패턴

#### 4.1.1 표준 LEFT JOIN 패턴 (기존)
| 쿼리 ID | 파일 | 조인 체인 | 특징 |
|---------|------|-----------|------|
| selectUserProfile | MicroserviceMapper.xml | users → user_info → user_profiles → orders | 사용자 중심 확장 정보 |
| selectOrderDetails | MicroserviceMapper.xml | orders → users → order_items → products | 주문 중심 상세 정보 |
| selectProductsByAdvancedCondition | ProductMapper.xml | products → categories → brands | 상품 중심 분류 정보 |

#### 4.1.2 새로 추가된 복합 JOIN 패턴 (v2)
| 쿼리 ID | 파일 | JOIN 유형 조합 | 조인 수 | 복잡도 |
|---------|------|----------------|---------|---------|
| executeFinancialReconciliation | ComplexEnterpriseMapper.xml | INNER + LEFT + CTE | 9개 | 매우 높음 |
| executeCustomerSegmentationAnalysis | ComplexEnterpriseMapper.xml | INNER + LEFT + 서브쿼리 | 9개 | 매우 높음 |
| executeInventoryOptimizationAnalysis | ComplexEnterpriseMapper.xml | INNER + CTE + 윈도우함수 | 5개 | 높음 |
| getDirectOrderSummary | DirectXmlQueryMapper.xml | INNER + GROUP BY + HAVING | 5개 | 중간 |
| executeEnterpriseComplexQuery | CoreSqlPatternDao.java | 동적 INNER + CTE + 환경별 | 8개 | 매우 높음 |

### 4.2 IMPLICIT JOIN 패턴 (Oracle 스타일) - 기존 유지

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
| executeOracleDataWarehouseQuery | CoreSqlPatternDao.java | 7개 | 6개 | 매우 높음 |

### 4.3 DYNAMIC JOIN 패턴 (🆕 v2 신규)

#### 4.3.1 + 연산자 동적 조인
| 메서드 | 조인 패턴 | 특징 | 복잡도 |
|--------|-----------|------|---------|
| selectWithPlusOperatorJoin | 동적 테이블 + 동적 조인 조건 | 런타임에 조인 테이블 결정 | 높음 |
| updateWithPlusOperatorJoin | 동적 UPDATE + JOIN | UPDATE문에서 동적 조인 | 중간 |
| mergeWithPlusOperator | 동적 MERGE + 조인 | MERGE문에서 동적 조인 | 높음 |

#### 4.3.2 String.format 동적 조인
| 메서드 | 조인 패턴 | 특징 | 복잡도 |
|--------|-----------|------|---------|
| selectWithStringFormat | 환경별 테이블 조인 | 환경 변수로 테이블명 결정 | 중간 |
| updateWithStringFormat | 다중 환경 UPDATE | 여러 환경 테이블 동시 조인 | 높음 |
| mergeWithStringFormat | 환경 간 MERGE | 소스/타겟 환경 간 데이터 조인 | 높음 |

#### 4.3.3 조건부 조인
| 메서드 | 조인 패턴 | 특징 | 복잡도 |
|--------|-----------|------|---------|
| selectWithConditionalJoin | 옵션 기반 조인 | 필요한 테이블만 선택적 조인 | 중간 |
| getDirectDynamicUserData | MyBatis 조건부 조인 | XML 태그로 조건부 조인 제어 | 중간 |

### 4.4 문제가 있는 조인 패턴 (has_error='Y') - 기존 유지

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

## 5. 조인 복잡도별 분류 (v2 확장)

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
| getDirectUserList | DirectXmlQueryMapper.xml | users | user_profiles | EXPLICIT LEFT JOIN |

### 5.3 중간 복잡도 (3개 테이블)
| 쿼리 ID | 파일/메서드 | 테이블 조합 | 조인 방식 |
|---------|-------------|-----------|-----------|
| selectProductsByAdvancedCondition | ProductMapper.xml | products + categories + brands | EXPLICIT LEFT JOIN |
| getProductsWithCategoryAndBrand | ImplicitJoinMapper.xml | products + categories + brands | IMPLICIT |
| findUsersWithAnsiJoin | UserMapper.xml(dynamicquery) | USERS + DEPARTMENTS + USER_PROFILES | EXPLICIT |
| getDirectUserStatistics | DirectXmlQueryMapper.xml | users + orders + payments | EXPLICIT LEFT JOIN |

### 5.4 고복잡도 (4-5개 테이블)
| 쿼리 ID | 파일/메서드 | 테이블 수 | 조인 방식 | 특징 |
|---------|-------------|-----------|-----------|------|
| selectOrderDetails | MicroserviceMapper.xml | 4개 | EXPLICIT | orders → users → order_items → products |
| selectUserProfile | MicroserviceMapper.xml | 4개 | EXPLICIT | users 중심 확장 |
| queryComplexDataDirectly | DirectQueryServlet.java | 4개 | EXPLICIT | Java 복합 조인 쿼리 |
| getDirectOrderSummary | DirectXmlQueryMapper.xml | 5개 | EXPLICIT | XML 직접 복합 조인 |
| getDirectTopCustomers | DirectXmlQueryMapper.xml | 5개 | EXPLICIT + 서브쿼리 | XML 복합 서브쿼리 조인 |
| selectComplexQueryExample | ImplicitJoinTestMapper.xml | 5개 | EXPLICIT + 서브쿼리 | 스칼라 서브쿼리 포함 |

### 5.5 매우 고복잡도 (6개 이상 테이블) - 🆕 v2 신규
| 쿼리 ID | 파일/메서드 | 테이블 수 | 조인 방식 | 특징 |
|---------|-------------|-----------|-----------|------|
| findUsersWithScatteredConditions | UserMapper.xml(dynamicquery) | 6개 | IMPLICIT | 분산된 조인 조건 |
| findOrdersWithScatteredJoins | UserMapper.xml(dynamicquery) | 6개 | IMPLICIT | 복잡한 비즈니스 로직 |
| executeOracleDataWarehouseQuery | CoreSqlPatternDao.java | 7개 | IMPLICIT + 윈도우함수 | 데이터 웨어하우스 스타일 |
| executeEnterpriseComplexQuery | CoreSqlPatternDao.java | 8개 | DYNAMIC + CTE | 기업급 복잡 쿼리 |
| executeFinancialReconciliation | ComplexEnterpriseMapper.xml | 9개 | EXPLICIT + CTE | 금융 정산 쿼리 |
| executeCustomerSegmentationAnalysis | ComplexEnterpriseMapper.xml | 9개 | EXPLICIT + CTE | 고객 세분화 분석 |

## 6. 조인 조건 패턴 분석 (v2 확장)

### 6.1 표준 PK-FK 조인 (기존)
| 조인 조건 | 빈도 | 주요 사용 쿼리 |
|-----------|------|----------------|
| users.user_id = orders.user_id | 12회 | 사용자-주문 관계 (v1: 7회 → v2: 12회) |
| products.category_id = categories.category_id | 8회 | 상품-카테고리 관계 (v1: 4회 → v2: 8회) |
| orders.order_id = order_items.order_id | 8회 | 주문-아이템 관계 (v1: 4회 → v2: 8회) |
| users.user_id = user_info.user_id | 3회 | 사용자-상세정보 관계 |
| products.product_id = order_items.product_id | 6회 | 상품-주문아이템 관계 |

### 6.2 새로 추가된 조인 조건 패턴 (v2)

#### 환경별 동적 테이블 조인
| 조인 조건 패턴 | 빈도 | 특징 |
|----------------|------|------|
| table_${environment}.id = related_${environment}.id | 15회 | 환경별 테이블 간 조인 |
| table_${dcPrefix}_${year}.id = related_${dcPrefix}.id | 8회 | 데이터센터별, 연도별 조인 |
| ${entityType}_${sourceEnv}.id = ${entityType}_${targetEnv}.id | 3회 | 환경 간 데이터 마이그레이션 |

#### 복잡한 비즈니스 조인
| 조인 조건 | 빈도 | 사용 쿼리 | 특징 |
|-----------|------|-----------|------|
| users.user_id = user_tiers.user_id | 3회 | 금융 정산, 고객 분석 | 사용자 등급 조인 |
| users.user_id = user_kyc.user_id | 2회 | 금융 정산 | KYC 정보 조인 |
| products.product_id = inventory.product_id | 2회 | 재고 최적화, 대시보드 | 재고 정보 조인 |
| orders.order_id = payments.payment_id | 4회 | 결제 분석, 통계 | 결제 정보 조인 |

#### 동적 생성 조인 조건
| 조인 패턴 | 생성 방식 | 사용 메서드 | 특징 |
|-----------|-----------|-------------|------|
| mainTable + ".user_id = " + joinTable + ".user_id" | + 연산자 | selectWithPlusOperatorJoin | 런타임 문자열 결합 |
| String.format("%s.%s = %s.%s", t1, col1, t2, col2) | String.format | selectWithStringFormat | 템플릿 기반 생성 |
| 조건부 JOIN 절 추가 | if-else 로직 | selectWithConditionalJoin | 조건부 조인 생성 |

### 6.3 Oracle IMPLICIT JOIN 조건 (기존 유지)
| 조인 조건 | 빈도 | 특징 |
|-----------|------|------|
| u.DEPT_ID = d.DEPT_ID | 6회 | 사용자-부서 관계 (Oracle 스타일) |
| u.USER_ID = p.USER_ID | 5회 | 사용자-프로필 관계 |
| u.USER_TYPE = ut.TYPE_CODE | 3회 | 사용자-타입 관계 |

### 6.4 문제가 있는 조인 조건 (has_error='Y') - 기존 유지
| 에러 조인 조건 | 올바른 조건 | 에러 유형 | 파일 |
|----------------|-------------|-----------|------|
| u.DEPT_ID = DEPT_ID | u.DEPT_ID = d.DEPT_ID | 별칭 생략 | ImplicitJoinTestMapper.xml |
| u.USER_ID = USER_ID | u.USER_ID = p.USER_ID | 별칭 생략 | ImplicitJoinTestMapper.xml |
| users.id = NONEXISTENT_TABLE.user_id | - | 존재하지 않는 테이블 | MixedErrorMapper.xml |

## 7. 파일별 조인 특성 분석 (v2 확장)

### 7.1 기존 파일들 (v1에서 유지)

#### UserMapper.xml (메인) - EXPLICIT JOIN 중심
| 조인 관계 | 조인 유형 | 사용 빈도 | 비고 |
|-----------|-----------|-----------|------|
| users ↔ orders | LEFT JOIN | 2회 | 사용자 중심 주문 정보 |
| users ↔ orders (서브쿼리) | LEFT JOIN | 1회 | 복잡한 동적 검색 |

#### MicroserviceMapper.xml - 복합 EXPLICIT JOIN
| 조인 관계 | 조인 유형 | 사용 빈도 | 특징 |
|-----------|-----------|-----------|------|
| users → user_info → user_profiles → orders | LEFT JOIN 체인 | 1회 | 통합 사용자 정보 |
| orders → users → order_items → products | JOIN 체인 | 1회 | 통합 주문 상세 |

### 7.2 새로 추가된 파일들 (v2)

#### ComplexEnterpriseMapper.xml - 기업급 복잡 조인
| 조인 관계 | 조인 유형 | 사용 빈도 | 특징 |
|-----------|-----------|-----------|------|
| 환경별 다중 테이블 조인 | INNER + LEFT JOIN | 6회 | CTE와 윈도우 함수 활용 |
| MERGE 기반 조인 | MERGE | 2회 | 데이터 통합 처리 |
| JSON 함수와 조인 | INNER JOIN + JSON | 1회 | 데이터 마이그레이션 |

#### DirectXmlQueryMapper.xml - XML 직접 조인
| 조인 관계 | 조인 유형 | 사용 빈도 | 특징 |
|-----------|-----------|-----------|------|
| 직접 다중 테이블 조인 | INNER + LEFT JOIN | 8회 | Java 없이 XML에서 직접 처리 |
| MERGE 조인 | MERGE | 2회 | XML 레벨에서 데이터 통합 |
| 배치 처리 조인 | UPDATE + 서브쿼리 | 2회 | 대량 데이터 처리 |

#### CoreSqlPatternDao.java - 동적 조인 패턴
| 조인 관계 | 조인 유형 | 사용 빈도 | 특징 |
|-----------|-----------|-----------|------|
| + 연산자 동적 조인 | DYNAMIC | 5회 | 런타임 조인 구성 |
| String.format 동적 조인 | DYNAMIC | 5회 | 템플릿 기반 조인 |
| 조건부 조인 | CONDITIONAL | 5회 | 필요시에만 조인 |
| 기업급 복잡 조인 | DYNAMIC + CTE | 2회 | 매우 복잡한 비즈니스 로직 |

#### UnsupportedPatternDao.java - 미지원 조인 패턴
| 조인 관계 | 조인 유형 | 사용 빈도 | 특징 |
|-----------|-----------|-----------|------|
| CONCAT + + 연산자 혼합 | UNSUPPORTED | 1회 | 함수와 연산자 혼합 |
| 복잡한 CASE + 서브쿼리 | UNSUPPORTED | 1회 | 조건문과 서브쿼리 혼합 |
| 동적 테이블 + 서브쿼리 | UNSUPPORTED | 2회 | 다중 패턴 혼합 |

### 7.3 UserMapper.xml (dynamicquery) - IMPLICIT JOIN 중심 (기존 유지)
| 조인 관계 | 조인 유형 | 사용 빈도 | 특징 |
|-----------|-----------|-----------|------|
| USERS, DEPARTMENTS, USER_PROFILES | WHERE 절 | 3회 | Oracle 스타일 기본 패턴 |
| 6개 테이블 복합 조인 | WHERE 절 | 3회 | 매우 복잡한 비즈니스 로직 |

## 8. 조인 조건 품질 분석 (v2 업데이트)

### 8.1 정상 조인 조건 (has_error='N')
- **총 104개 쿼리**: 모든 조인 조건이 올바르게 작성됨 (v1: 68개 → v2: 104개)
- **표준 준수**: PK-FK 관계를 정확히 반영
- **성능 고려**: 적절한 인덱스 활용 가능한 조건
- **동적 조인 품질**: 새로 추가된 동적 조인들도 안전한 패턴 사용

### 8.2 문제 조인 조건 (has_error='Y') - 기존 유지
- **총 6개 쿼리**: 조인 조건에 문제 있음
- **별칭 생략**: 3개 (ImplicitJoinTestMapper.xml)
- **존재하지 않는 테이블**: 3개 (MixedErrorMapper.xml)

### 8.3 조인 방식별 에러율 (v2 업데이트)
| 조인 방식 | 총 쿼리 수 | 에러 쿼리 수 | 에러율 | 비고 |
|-----------|------------|--------------|--------|------|
| EXPLICIT JOIN | 85개 | 0개 | 0% | 매우 안정적 (XML + Java) |
| IMPLICIT JOIN | 29개 | 6개 | 20.7% | 별칭 생략 위험 (XML만) |
| DYNAMIC JOIN | 18개 | 0개 | 0% | 새로운 패턴이지만 안정적 |

### 8.4 소스 유형별 조인 특성 (v2 업데이트)
| 소스 유형 | 총 조인 관계 | EXPLICIT | IMPLICIT | DYNAMIC | 특징 |
|-----------|--------------|----------|----------|---------|------|
| XML 매퍼 | 55개 | 40개 (72.7%) | 15개 (27.3%) | 0개 (0%) | 전통적 패턴 |
| Java 소스 | 23개 | 5개 (21.7%) | 0개 (0%) | 18개 (78.3%) | 동적 패턴 우세 |
| **전체** | **78개** | **45개 (57.7%)** | **15개 (19.2%)** | **18개 (23.1%)** | **다양한 패턴 혼재** |

## 9. 새로운 조인 패턴 분석 (v2 신규)

### 9.1 환경별 동적 테이블 조인
- **패턴**: `table_${environment}` 형태의 테이블명 사용
- **장점**: 환경별 데이터 분리, 배포 유연성
- **단점**: 파싱 복잡도 증가, 런타임 에러 가능성
- **사용 사례**: 개발/스테이징/운영 환경별 데이터 처리

### 9.2 CTE(Common Table Expression)와 조인
- **패턴**: WITH 절을 사용한 다단계 조인
- **장점**: 복잡한 비즈니스 로직 표현, 가독성 향상
- **단점**: 성능 최적화 어려움, 파싱 복잡도
- **사용 사례**: 금융 정산, 고객 세분화, 재고 분석

### 9.3 MERGE 문과 조인
- **패턴**: MERGE ... USING ... ON 구문
- **장점**: 데이터 통합 처리, UPSERT 기능
- **단점**: 복잡한 조인 조건, 성능 이슈
- **사용 사례**: 배치 정산, 데이터 마이그레이션

### 9.4 JSON 함수와 조인
- **패턴**: JSON_OBJECT, JSON_ARRAYAGG와 조인
- **장점**: 계층적 데이터 표현, API 응답 최적화
- **단점**: 메모리 사용량 증가, 파싱 복잡도
- **사용 사례**: 데이터 마이그레이션, API 통합

## 10. 권장사항 (v2 업데이트)

### 10.1 조인 방식 표준화 (기존 + 신규)
1. **EXPLICIT JOIN 우선**: 가독성과 안정성이 높음
2. **DYNAMIC JOIN 신중 사용**: 성능과 보안 고려
3. **환경별 테이블 관리**: 설정 파일로 중앙화
4. **CTE 사용 가이드라인**: 복잡도와 성능 균형

### 10.2 새로운 패턴 품질 관리
1. **동적 조인 검증**: 런타임 에러 방지를 위한 사전 검증
2. **환경 변수 관리**: ${environment} 등 변수의 안전한 치환
3. **CTE 최적화**: 중간 결과셋 크기 최소화
4. **JSON 함수 성능**: 대용량 데이터에서 메모리 고려

### 10.3 파서 개선 권장사항 (v2 신규)
1. **환경 변수 지원**: ${environment}, ${year} 등 동적 치환자 인식
2. **CTE 구문 지원**: WITH 절과 복잡한 서브쿼리 파싱
3. **MERGE 구문 지원**: MERGE ... USING ... ON 패턴 처리
4. **JSON 함수 지원**: JSON_OBJECT, JSON_ARRAYAGG 등 함수 인식
5. **동적 문자열 패턴**: + 연산자, String.format 패턴 처리

### 10.4 복잡도 관리 (v2 신규)
1. **매우 복잡한 쿼리 분할**: 9개 이상 테이블 조인 시 분할 검토
2. **CTE 단계 제한**: 3단계 이상 CTE 사용 시 성능 검토
3. **환경별 테이블 인덱싱**: 동적 테이블에 대한 일관된 인덱스 전략
4. **모니터링 강화**: 복잡한 조인 쿼리의 성능 모니터링

### 10.5 Java 소스 조인 품질 (v2 업데이트)
1. **동적 조인 안전성**: 입력 검증과 SQL Injection 방지
2. **패턴 일관성**: + 연산자와 String.format 사용 규칙 정립
3. **조건부 조인 최적화**: 불필요한 조인 제거를 통한 성능 향상
4. **테스트 강화**: 동적 생성 쿼리에 대한 단위 테스트

---

**분석 완료일**: 2025년 9월 18일  
**총 분석 조인 관계**: 78개 (v1: 39개 → v2: 78개, +39개 증가)  
**EXPLICIT JOIN**: 45개 (57.7%) - v1: 30개 (76.9%) → v2: 45개 (57.7%)  
**IMPLICIT JOIN**: 15개 (19.2%) - v1: 9개 (23.1%) → v2: 15개 (19.2%)  
**DYNAMIC JOIN**: 18개 (23.1%) - v1: 0개 → v2: 18개 (신규)  
**Java 소스 에러율**: 0% (매우 안정적, 기존과 동일)  
**새로운 패턴**: 환경별 동적 테이블, CTE 조인, MERGE 조인, JSON 함수 조인, + 연산자 조인, String.format 조인
