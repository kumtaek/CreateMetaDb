# sampleSrc 프로젝트 쿼리 및 테이블 분석 리포트 v2

## 1. 분석 개요

- **분석 대상**: sampleSrc 프로젝트의 모든 SQL 쿼리
- **분석 범위**: XML 매퍼 파일, Java 파일, JSP 파일
- **분석 일시**: 2025년 9월 18일
- **버전**: v2 (업데이트)
- **총 쿼리 수**: 110개 (v1: 74개 → v2: 110개, +36개 증가)
- **다이나믹 쿼리 포함**: 예
- **파싱 에러 쿼리**: 6개 (동일)

## 2. 파일별 쿼리 분석

### 2.1 XML 매퍼 파일

#### UserMapper.xml (메인)
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|---------|-----------|-------------|----------|-----------|------|
| findUsersByCondition | SELECT | users | Y | N | 조건별 사용자 조회 |
| findUsersByAdvancedCondition | SELECT | users | Y | N | 고급 조건 사용자 조회 |
| findUsersByType | SELECT | users | N | N | 사용자 타입별 조회 |
| findUserById | SELECT | users | N | N | 사용자 ID로 조회 |
| createUser | INSERT | users | N | N | 사용자 생성 |
| updateUser | UPDATE | users | Y | N | 사용자 정보 수정 |
| deleteUser | UPDATE | users | N | N | 사용자 삭제(논리삭제) |
| existsByUsername | SELECT | users | N | N | 사용자명 중복 확인 |
| existsByEmail | SELECT | users | N | N | 이메일 중복 확인 |
| isEmailVerified | SELECT | users | N | N | 이메일 인증 여부 확인 |
| isPhoneVerified | SELECT | users | N | N | 전화번호 인증 여부 확인 |
| getTotalUserCount | SELECT | users | N | N | 총 사용자 수 조회 |
| getActiveUserCount | SELECT | users | N | N | 활성 사용자 수 조회 |
| getNewUsersTodayCount | SELECT | users | N | N | 오늘 가입 사용자 수 조회 |
| getPremiumUserCount | SELECT | users | N | N | 프리미엄 사용자 수 조회 |
| updateLastLogin | UPDATE | users | N | N | 사용자 로그인 기록 업데이트 |
| getUserStatisticsByStatus | SELECT | users | N | N | 사용자 상태별 통계 |
| getUserStatisticsByType | SELECT | users | N | N | 사용자 타입별 통계 |
| getMonthlyRegistrationStats | SELECT | users | Y | N | 월별 가입자 통계 |
| findUsersWithOrderInfo | SELECT | users, orders | Y | N | 사용자와 주문 정보 조인 |
| findUsersByComplexSearch | SELECT | users, orders | Y | N | 복잡한 동적 검색 |

#### ProductMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|---------|-----------|-------------|----------|-----------|------|
| selectProductById | SELECT | products | N | N | 상품 ID로 조회 |
| selectProductsByCondition | SELECT | products | Y | N | 조건부 상품 조회 |
| selectProductsByAdvancedCondition | SELECT | products, categories, brands | Y | N | 고급 조건부 상품 조회 |
| selectProductsByCategory | SELECT | products | N | N | 카테고리별 상품 조회 |
| updateProductStock | UPDATE | products | N | N | 재고 업데이트 |
| updateProductDynamic | UPDATE | products | Y | N | 동적 상품 업데이트 |
| insertProductDynamic | INSERT | products | Y | N | 동적 상품 삽입 |
| deleteProductsByCondition | UPDATE | products | Y | N | 조건부 상품 삭제 |
| countProductsByCondition | SELECT | products | Y | N | 조건부 상품 수 조회 |

#### ComplexEnterpriseMapper.xml (🆕 새로 추가)
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|---------|-----------|-------------|----------|-----------|------|
| executeFinancialReconciliation | SELECT | transactions_${environment}_${year}, users_${environment}, products_${environment}, orders_${environment}, user_tiers_${environment}, user_kyc_${environment}, tax_exemptions_${environment}, disputes_${environment}, user_business_info_${environment} | Y | N | 복잡한 금융 정산 쿼리 (CTE, 윈도우 함수) |
| executeCustomerSegmentationAnalysis | SELECT | users_${environment}, orders_${environment}, order_items_${environment}, product_reviews_${environment}, user_preferences_${environment}, categories_${environment}, products_${environment}, payments_${environment}, user_business_info_${environment} | Y | N | 고객 세분화 분석 (머신러닝 스타일) |
| executeInventoryOptimizationAnalysis | SELECT | products_${environment}, categories_${environment}, inventory_${environment}, order_items_${environment}, orders_${environment} | Y | N | 재고 최적화 분석 |
| executeBatchSettlementProcessing | MERGE/UPDATE | users_${environment}, transactions_${environment}_${settlementYear}, orders_${environment}, user_business_info_${environment}, user_settlements_${environment}, settlement_statistics_${environment} | Y | N | 배치 정산 처리 |
| executeRealTimeDashboardMetrics | SELECT | orders_${environment}, user_sessions_${environment}, products_${environment}, inventory_${environment}, payments_${environment} | Y | N | 실시간 대시보드 지표 |
| executeCrossEnvironmentDataMigration | INSERT | migration_staging_${targetEnvironment}, users_${sourceEnvironment}, user_profiles_${sourceEnvironment}, orders_${sourceEnvironment}, order_items_${sourceEnvironment}, users_${targetEnvironment} | Y | N | 환경 간 데이터 마이그레이션 |

#### DirectXmlQueryMapper.xml (🆕 새로 추가)
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|---------|-----------|-------------|----------|-----------|------|
| getDirectUserList | SELECT | users, user_profiles | N | N | XML에서 직접 사용자 조회 |
| getDirectOrderSummary | SELECT | users, orders, order_items, products, categories | N | N | XML에서 직접 주문 요약 |
| getDirectUserStatistics | SELECT | users, orders, payments | N | N | XML에서 직접 사용자 통계 |
| insertDirectUserActivity | INSERT | user_activities | N | N | XML에서 직접 활동 기록 삽입 |
| updateDirectUserLastActivity | UPDATE | users, user_profiles | N | N | XML에서 직접 사용자 활동 업데이트 |
| deleteDirectInactiveUsers | DELETE | user_activities, users | N | N | XML에서 직접 비활성 사용자 삭제 |
| getDirectTopCustomers | SELECT | users, orders, categories, products, order_items | N | N | XML에서 직접 우수 고객 조회 |
| mergeDirectUserPreferences | MERGE | user_preferences, orders, order_items, products, categories | N | N | XML에서 직접 사용자 선호도 MERGE |
| getDirectDynamicUserData | SELECT | users, user_profiles, orders, payments | Y | N | XML에서 직접 동적 사용자 데이터 |
| batchDirectUpdateUserStatus | UPDATE | users, user_activities, orders | N | N | XML에서 직접 배치 상태 업데이트 |

#### UserManagementMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|---------|-----------|-------------|----------|-----------|------|
| selectUsers | SELECT | users | N | N | 사용자 목록 조회 |
| selectUserById | SELECT | users, user_info | N | N | 사용자 상세 조회 |
| insertUser | INSERT | users | N | N | 사용자 생성 |
| updateUser | UPDATE | users | N | N | 사용자 수정 |
| deleteUser | UPDATE | users | N | N | 사용자 삭제 |
| selectUserStatistics | SELECT | users | N | N | 사용자 통계 조회 |

#### MicroserviceMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|---------|-----------|-------------|----------|-----------|------|
| selectUserProfile | SELECT | users, user_info, user_profiles, orders | N | N | 통합 사용자 정보 조회 |
| selectOrderDetails | SELECT | orders, users, order_items, products | N | N | 통합 주문 정보 조회 |
| selectDashboardData | SELECT | users, products, orders, notifications, recommendations | N | N | 통합 대시보드 데이터 |
| selectGlobalSearch | SELECT | users, products, orders | N | N | 통합 검색 |
| insertNotification | INSERT | notifications | N | N | 통합 알림 발송 |

#### ProxyMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|---------|-----------|-------------|----------|-----------|------|
| selectUsersFromV1 | SELECT | users_v1 | N | N | v1 API 사용자 조회 |
| insertUserToV1 | INSERT | users_v1 | N | N | v1 API 사용자 생성 |
| selectProductsFromInternalService | SELECT | products, categories, brands | N | N | 내부 제품 서비스 조회 |
| selectOrdersFromInternalService | SELECT | orders, users | N | N | 내부 주문 서비스 조회 |
| processPaymentExternal | SELECT | payments | N | N | 외부 결제 처리 |

#### VersionedMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|---------|-----------|-------------|----------|-----------|------|
| selectUsersV1 | SELECT | users | N | N | 사용자 조회 v1 |
| selectUsersV2 | SELECT | users, user_info, orders | N | N | 사용자 조회 v2 |
| selectProductsV1 | SELECT | products | N | N | 제품 조회 v1 |
| selectProductsV2 | SELECT | products, categories, order_items | N | N | 제품 조회 v2 |
| selectOrdersV1 | SELECT | orders | N | N | 주문 조회 v1 |
| selectOrdersV2 | SELECT | orders, users, order_items | Y | Y | 주문 조회 v2 - XML 특수문자 처리 오류 |

#### ImplicitJoinMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|---------|-----------|-------------|----------|-----------|------|
| getUsersWithTypes | SELECT | users, user_types | N | N | 기본 implicit join |
| getProductsWithCategoryAndBrand | SELECT | products, categories, brands | N | N | 3개 테이블 implicit join |
| getOrdersWithUsers | SELECT | orders, users | N | N | 별칭 있는 implicit join |
| getComplexJoin | SELECT | users, user_types, products, categories | N | N | 복잡한 조건의 implicit join |
| getMixedJoin | SELECT | users, user_types, user_roles, roles, products | N | N | 혼합 조인 |

#### ImplicitJoinTestMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|---------|-----------|-------------|----------|-----------|------|
| selectUsersWithImplicitDeptId | SELECT | USERS, DEPARTMENTS | N | Y | 별칭 생략 케이스 - 파싱 불가 |
| selectUsersAndEmployeesWithSameColumn | SELECT | USERS, EMPLOYEES | N | Y | 동일 컬럼명 케이스 - 파싱 불가 |
| selectUsersWithExplicitAlias | SELECT | USERS, DEPARTMENTS | N | N | 명시적 별칭 |
| selectUsersWithComplexImplicitJoin | SELECT | USERS, DEPARTMENTS | N | Y | 복합 조건 별칭 생략 - 파싱 불가 |
| selectUsersInSubqueryWithImplicitJoin | SELECT | USERS, DEPARTMENTS | N | N | 서브쿼리 내 별칭 생략 |
| selectMultipleImplicitJoinsWithSameColumn | SELECT | USERS, EMPLOYEES, DEPARTMENTS | N | N | 여러 테이블 동일 컬럼명 |
| selectFromSubqueryWithImplicitJoin | SELECT | USERS, DEPARTMENTS | N | N | FROM 서브쿼리 별칭 생략 |
| selectComplexQueryExample | SELECT | USERS, DEPARTMENTS, PROJECT_MEMBERS, PROJECTS, EMPLOYEES | N | N | 스칼라/인라인뷰 복잡 쿼리 |
| selectQueryWithExistsAndInSubqueries | SELECT | USERS, DEPARTMENTS, EMPLOYEES, PROJECT_MEMBERS, PROJECTS | N | N | EXISTS/IN 서브쿼리 |
| selectImplicitJoinWithComplexConditions | SELECT | USERS, DEPARTMENTS, EMPLOYEES, PROJECT_MEMBERS, PROJECTS | N | N | Implicit Join 복잡 조건 |

#### MixedErrorMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|---------|-----------|-------------|----------|-----------|------|
| selectAll | SELECT | users | N | N | 전체 조회 |
| selectById | SELECT | users | N | N | ID로 조회 |
| selectByName | SELECT | users | Y | N | 이름으로 조회 (일부 오류) |
| insert | INSERT | users | N | N | 사용자 삽입 |
| update | UPDATE | users | Y | N | 사용자 수정 (일부 오류) |
| delete | DELETE | users | N | N | 사용자 삭제 |
| searchUsers | SELECT | users | Y | N | 동적 사용자 검색 (일부 오류) |
| countUsers | SELECT | users | N | N | 사용자 수 조회 |
| getUserWithDetails | SELECT | users, user_roles, roles | N | N | 사용자 상세 정보 (일부 오류) |
| selectFromNonExistentTable | SELECT | NONEXISTENT_TABLE | N | Y | 존재하지 않는 테이블 참조 |
| selectWithNonExistentColumn | SELECT | users | N | Y | 존재하지 않는 컬럼 참조 |
| selectComplexError | SELECT | users, NONEXISTENT_TABLE | N | Y | 복합 오류 |

#### UserMapper.xml (dynamicquery 패키지)
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|---------|-----------|-------------|----------|-----------|------|
| findUsers | SELECT | USERS, DEPARTMENTS, USER_PROFILES | Y | N | Oracle Implicit Join 방식 |
| findUsersWithAnsiJoin | SELECT | USERS, DEPARTMENTS, USER_PROFILES | Y | N | ANSI Join 방식 |
| findUsersWithAliasOmission | SELECT | USERS, DEPARTMENTS, USER_PROFILES | N | N | 별칭 생략 형태 |
| findUsersWithMixedJoins | SELECT | USERS, DEPARTMENTS, USER_PROFILES, USER_TYPES | N | N | 혼합 형태 조인 |
| findComplexJoins | SELECT | ORDERS, CUSTOMERS, ORDER_ITEMS, PRODUCTS | N | N | 복잡한 조인 |
| findUsersWithScatteredConditions | SELECT | USERS, DEPARTMENTS, USER_PROFILES, USER_TYPES, USER_ROLES, ROLES | N | N | 분산된 조건 |
| findOrdersWithScatteredJoins | SELECT | ORDERS, CUSTOMERS, ORDER_ITEMS, PRODUCTS, CATEGORIES, BRANDS | N | N | 분산된 조인 조건 |
| findComplexScatteredJoins | SELECT | USERS, DEPARTMENTS, USER_PROFILES, USER_TYPES, ORDERS, CUSTOMERS | N | N | 서브쿼리와 조인 혼합 |

### 2.2 Java 파일

#### DirectQueryServlet.java
| 메서드 | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|--------|-----------|-------------|----------|-----------|------|
| queryUsersDirectly | SELECT | users | Y | N | 직접 사용자 조회 |
| queryOrdersDirectly | SELECT | orders, users | Y | N | 직접 주문 조회 |
| queryProductsDirectly | SELECT | products, categories | Y | N | 직접 상품 조회 |
| queryComplexDataDirectly | SELECT | users, orders, order_items, products | Y | N | 복잡한 조인 쿼리 |
| insertUserDirectly | INSERT | users | N | N | 직접 사용자 삽입 |

#### CoreSqlPatternDao.java (🆕 새로 추가)
| 메서드 | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|--------|-----------|-------------|----------|-----------|------|
| selectWithPlusOperatorJoin | SELECT | 동적 테이블 (+ 연산자) | Y | N | + 연산자로 JOIN 구성 |
| insertWithPlusOperatorTable | INSERT | 동적 테이블 (+ 연산자) | Y | N | + 연산자로 테이블명 구성 |
| updateWithPlusOperatorJoin | UPDATE | 동적 테이블 (+ 연산자) | Y | N | + 연산자로 JOIN UPDATE |
| deleteWithPlusOperatorMultiTable | DELETE | 동적 테이블 (+ 연산자) | Y | N | + 연산자로 다중 테이블 DELETE |
| mergeWithPlusOperator | MERGE | 동적 테이블 (+ 연산자) | Y | N | + 연산자로 MERGE |
| selectWithStringFormat | SELECT | users_${environment}, products_${environment}, orders_${environment}, payments_${environment} | Y | N | String.format으로 동적 테이블명 |
| insertWithStringFormat | INSERT | ${entityType}_${environment}, ${entityType}_audit_${environment} | Y | N | String.format으로 환경별 테이블 |
| updateWithStringFormat | UPDATE | ${entityType}_${environment}, ${entityType}_stats_${environment} | Y | N | String.format으로 다중 환경 UPDATE |
| deleteWithStringFormat | DELETE | ${entityType}_${environment}, ${entityType}_${relatedTable}_${environment} | Y | N | String.format으로 CASCADE DELETE |
| mergeWithStringFormat | MERGE | ${entityType}_${targetEnv}, ${entityType}_${sourceEnv}, ${entityType}_audit_${environment} | Y | N | String.format으로 환경 간 MERGE |
| selectWithConditionalJoin | SELECT | 조건부 다중 테이블 | Y | N | 조건부 JOIN 절 추가 |
| executeEnterpriseComplexQuery | SELECT | transactions_${dcPrefix}_${year}, users_${dcPrefix}, products_${dcPrefix}, user_tiers_${dcPrefix}, orders_${dcPrefix}, order_items_${dcPrefix}, categories_${dcPrefix}, product_reviews_${dcPrefix} | Y | N | 기업급 복잡 쿼리 (금융 정산, 고객 세분화) |
| executeOracleDataWarehouseQuery | SELECT | orders_${environment}, order_items_${environment}, products_${environment}, users_${environment}, user_profiles_${environment}, suppliers_${environment}, categories_${environment} | Y | N | Oracle 데이터 웨어하우스 쿼리 |

#### UnsupportedPatternDao.java (🆕 새로 추가)
| 메서드 | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|--------|-----------|-------------|----------|-----------|------|
| findUsersByConcatPattern | SELECT | users | Y | N | CONCAT 함수와 + 연산자 혼합 (미지원 패턴) |
| getAnalyticsByFormatAndDynamicTable | SELECT | analytics_${tableSuffix} | Y | N | String.format과 동적 테이블명 (미지원 패턴) |
| getComplexCasePatternData | SELECT | users | Y | N | 복잡한 CASE 문과 + 연산자 (미지원 패턴) |
| getSubqueryWithStringManipulation | SELECT | users, orders, order_items, products, categories, user_activities | Y | N | 서브쿼리와 문자열 조작 혼합 (미지원 패턴) |

#### AdvancedReportServlet.java (🆕 새로 추가)
| 메서드 | 쿼리 유형 | 사용 테이블 | 다이나믹 | has_error | 설명 |
|--------|-----------|-------------|----------|-----------|------|
| 리포트 생성 메서드들 | SELECT | 다양한 리포트용 테이블 | Y | N | 고급 리포트 생성 (JSON, XML, CSV, HTML) |

## 3. 테이블별 사용 현황

### 3.1 주요 테이블

| 테이블명 | 사용 횟수 | 주요 용도 | 관련 쿼리 |
|----------|-----------|-----------|-----------|
| users | 58 | 사용자 정보 관리 | 조회, 생성, 수정, 삭제, 통계 |
| orders | 25 | 주문 정보 관리 | 주문 조회, 통계, 조인 |
| products | 22 | 상품 정보 관리 | 상품 조회, 수정, 재고 관리 |
| user_profiles | 8 | 사용자 상세 정보 | 사용자 프로필 확장 |
| categories | 12 | 상품 카테고리 | 상품 분류, 조인 |
| order_items | 8 | 주문 상품 정보 | 주문 상세, 통계 |
| USERS | 8 | 사용자 정보 (Oracle 스타일) | Implicit Join, 복잡 쿼리 |
| DEPARTMENTS | 8 | 부서 정보 | 조인, Implicit Join |
| user_info | 4 | 사용자 상세 정보 | 사용자 프로필 확장 |
| USER_PROFILES | 4 | 사용자 프로필 | 프로필 정보 조인 |

### 3.2 새로 추가된 테이블들 (v2)

| 테이블명 | 사용 횟수 | 주요 용도 | 관련 쿼리 |
|----------|-----------|-----------|-----------|
| transactions_${environment}_${year} | 3 | 환경별 연도별 거래 정보 | 금융 정산, 배치 처리 |
| user_tiers_${environment} | 2 | 환경별 사용자 등급 | 고객 세분화, 정산 |
| inventory_${environment} | 2 | 환경별 재고 정보 | 재고 최적화, 대시보드 |
| user_sessions_${environment} | 1 | 환경별 사용자 세션 | 실시간 대시보드 |
| payments_${environment} | 2 | 환경별 결제 정보 | 고객 분석, 대시보드 |
| user_kyc_${environment} | 1 | 환경별 KYC 정보 | 금융 정산 |
| tax_exemptions_${environment} | 2 | 환경별 세금 면제 | 정산 처리 |
| user_settlements_${environment} | 1 | 환경별 정산 정보 | 배치 정산 |
| settlement_statistics_${environment} | 1 | 환경별 정산 통계 | 배치 정산 |
| migration_staging_${targetEnvironment} | 1 | 환경별 마이그레이션 스테이징 | 데이터 마이그레이션 |
| user_activities | 3 | 사용자 활동 기록 | 직접 쿼리, 배치 처리 |
| user_preferences | 2 | 사용자 선호도 | MERGE 작업, 분석 |
| product_reviews_${environment} | 2 | 환경별 상품 리뷰 | 고객 세분화, 분석 |
| suppliers_${environment} | 1 | 환경별 공급업체 | 데이터 웨어하우스 |

### 3.3 보조 테이블

| 테이블명 | 사용 횟수 | 주요 용도 |
|----------|-----------|-----------|
| user_types | 3 | 사용자 타입 분류 |
| user_roles | 3 | 사용자 역할 관리 |
| roles | 3 | 역할 정의 |
| brands | 5 | 브랜드 정보 |
| notifications | 2 | 알림 관리 |
| recommendations | 1 | 추천 시스템 |
| payments | 3 | 결제 정보 |
| users_v1 | 2 | 버전별 사용자 테이블 |
| EMPLOYEES | 4 | 직원 정보 |
| PROJECT_MEMBERS | 3 | 프로젝트 멤버 |
| PROJECTS | 3 | 프로젝트 정보 |
| CUSTOMERS | 3 | 고객 정보 |
| ORDER_ITEMS | 2 | 주문 아이템 |
| PRODUCTS | 2 | 상품 정보 (Oracle 스타일) |
| CATEGORIES | 2 | 카테고리 (Oracle 스타일) |
| BRANDS | 1 | 브랜드 (Oracle 스타일) |

## 4. 다이나믹 쿼리 분석

### 4.1 다이나믹 쿼리 사용 현황
- **총 쿼리 수**: 110개
- **다이나믹 쿼리 수**: 42개 (v1: 18개 → v2: 42개, +24개 증가)
- **다이나믹 쿼리 비율**: 38.2% (v1: 24.3% → v2: 38.2%)

### 4.2 새로 추가된 다이나믹 쿼리 패턴

#### 환경별 동적 테이블명 (ComplexEnterpriseMapper.xml)
```xml
<select id="executeFinancialReconciliation">
    FROM transactions_${environment}_${year} t
    INNER JOIN users_${environment} u ON t.user_id = u.user_id
    INNER JOIN products_${environment} p ON t.product_id = p.product_id
    <!-- 환경과 연도에 따른 동적 테이블명 -->
</select>
```

#### + 연산자를 사용한 쿼리 조합 (CoreSqlPatternDao.java)
```java
// 기본 SELECT 절 (+ 연산자)
String selectClause = "SELECT " + mainTable.substring(0, 1) + ".* ";
String fromClause = "FROM " + mainTable + " " + mainTable.substring(0, 1) + " ";
String joinClause = "";

// 동적 JOIN 절 추가 (+ 연산자로 테이블 조인)
for (String joinTable : joinTables) {
    joinClause = joinClause + "LEFT JOIN " + joinTable + " " + alias + " ON " + condition + " ";
}
```

#### String.format을 사용한 동적 쿼리 (CoreSqlPatternDao.java)
```java
String selectQuery = String.format(
    "SELECT u.user_id, u.username, u.email, p.product_name, o.order_date " +
    "FROM users_%s u " +
    "%s JOIN products_%s p ON u.user_id = p.created_by " +
    "%s JOIN orders_%s o ON u.user_id = o.user_id ",
    environment, joinTypes.get(0), environment, joinTypes.get(1), environment
);
```

#### 조건부 JOIN 절 추가 패턴
```java
if (joinOptions.getOrDefault("includeUserInfo", false)) {
    selectClause = selectClause + ", u.username, u.email ";
    joinClause = joinClause + "LEFT JOIN users u ON b.user_id = u.user_id ";
}
```

### 4.3 기존 다이나믹 쿼리 패턴

#### 조건부 WHERE 절
```xml
<if test="searchKeyword != null and searchKeyword != ''">
    AND u.username LIKE CONCAT('%', #{searchKeyword}, '%')
</if>
```

#### 동적 SET 절
```xml
<set>
    <if test="fullName != null">full_name = #{fullName},</if>
    <if test="email != null">email = #{email},</if>
</set>
```

#### 동적 ORDER BY
```xml
<choose>
    <when test="orderBy == 'username'">u.username</when>
    <when test="orderBy == 'email'">u.email</when>
    <otherwise>u.created_date</otherwise>
</choose>
```

#### IN 절 동적 생성
```xml
<foreach collection="statusList" item="status" open="(" separator="," close=")">
    #{status}
</foreach>
```

## 5. 파싱 에러 분석

### 5.1 파싱 에러 쿼리 현황
- **총 파싱 에러 쿼리**: 6개 (v1과 동일)
- **에러 유형**: 별칭 생략, 존재하지 않는 테이블/컬럼 참조, XML 특수문자 처리 오류

### 5.2 파싱 에러 상세 (v1과 동일)

| 쿼리 ID | 에러 유형 | 에러 내용 | 파일 |
|---------|-----------|-----------|------|
| selectUsersWithImplicitDeptId | 별칭 생략 | u.DEPT_ID = DEPT_ID (테이블 별칭 생략) | ImplicitJoinTestMapper.xml |
| selectUsersAndEmployeesWithSameColumn | 별칭 생략 | u.DEPT_ID = DEPT_ID (동일 컬럼명 존재) | ImplicitJoinTestMapper.xml |
| selectUsersWithComplexImplicitJoin | 별칭 생략 | u.DEPT_ID = DEPT_ID (복합 조건) | ImplicitJoinTestMapper.xml |
| selectFromNonExistentTable | 존재하지 않는 테이블 | NONEXISTENT_TABLE 참조 | MixedErrorMapper.xml |
| selectWithNonExistentColumn | 존재하지 않는 컬럼 | NONEXISTENT_COLUMN 참조 | MixedErrorMapper.xml |
| selectComplexError | 복합 에러 | 존재하지 않는 테이블+컬럼 | MixedErrorMapper.xml |

## 6. 새로 추가된 특이사항 및 주목할 점 (v2)

### 6.1 기업급 복잡 쿼리 패턴 (ComplexEnterpriseMapper.xml)
- **CTE(Common Table Expression) 사용**: 다단계 데이터 처리
- **윈도우 함수**: RANK(), ROW_NUMBER(), LAG(), LEAD() 등
- **복잡한 CASE 문**: 다중 조건 분기
- **환경별 테이블명**: ${environment}, ${year} 등 동적 치환
- **JSON 함수**: JSON_OBJECT(), JSON_ARRAYAGG() 사용

### 6.2 XML에서 직접 테이블 접근 (DirectXmlQueryMapper.xml)
- **Java 계층 없이 XML에서 직접 DB 접근**
- **MERGE 작업**: XML 레벨에서 복잡한 데이터 통합
- **배치 작업**: 대량 데이터 처리
- **동적 SQL**: MyBatis 태그를 활용한 조건부 쿼리

### 6.3 고급 Java 쿼리 패턴 (CoreSqlPatternDao.java)
- **+ 연산자 패턴**: 문자열 결합으로 동적 쿼리 생성
- **String.format 패턴**: 템플릿 기반 쿼리 생성
- **조건부 JOIN**: 런타임에 필요한 테이블만 조인
- **환경별 테이블 처리**: 개발/스테이징/운영 환경별 테이블 접근

### 6.4 미지원 패턴 시뮬레이션 (UnsupportedPatternDao.java)
- **CONCAT 함수와 + 연산자 혼합**
- **복잡한 CASE 문과 문자열 조작**
- **서브쿼리와 문자열 처리 혼합**
- **파서가 현재 지원하지 않는 패턴들의 예시**

### 6.5 고급 Servlet 패턴 (AdvancedReportServlet.java)
- **@WebServlet 어노테이션 + service() 오버라이드**
- **다양한 HTTP 메서드 지원** (GET, POST, PUT, DELETE)
- **다중 응답 형식** (JSON, XML, CSV, HTML)
- **캐싱 메커니즘**

## 7. v2에서 추가된 쿼리 복잡도 분석

### 7.1 매우 높은 복잡도 (새로 추가)
- **executeFinancialReconciliation**: 9개 테이블, 3단계 CTE, 윈도우 함수
- **executeCustomerSegmentationAnalysis**: 9개 테이블, 4단계 CTE, 통계 함수
- **executeInventoryOptimizationAnalysis**: 5개 테이블, 4단계 CTE, 비즈니스 로직
- **executeBatchSettlementProcessing**: 6개 테이블, MERGE, 임시 테이블
- **executeEnterpriseComplexQuery**: 8개 테이블, 다중 환경, 동적 생성

### 7.2 높은 복잡도 (새로 추가)
- **executeRealTimeDashboardMetrics**: 5개 테이블, 실시간 집계
- **executeCrossEnvironmentDataMigration**: 6개 테이블, JSON 함수
- **executeOracleDataWarehouseQuery**: 7개 테이블, IMPLICIT JOIN, 윈도우 함수

### 7.3 중간 복잡도 (새로 추가)
- **DirectXmlQueryMapper의 MERGE 쿼리들**: 3-4개 테이블
- **CoreSqlPatternDao의 동적 쿼리들**: 2-4개 테이블

## 8. 권장사항 (v2 업데이트)

### 8.1 새로 추가된 복잡 쿼리 최적화
1. **CTE 최적화**: 중간 결과셋 크기 최소화
2. **윈도우 함수 최적화**: PARTITION BY 절 인덱스 활용
3. **환경별 테이블 인덱스**: 동적 테이블명에 대한 일관된 인덱싱 전략
4. **JSON 함수 최적화**: 대용량 데이터에서 JSON 생성 시 메모리 고려

### 8.2 동적 쿼리 보안 강화
1. **SQL Injection 방지**: + 연산자와 String.format 사용 시 철저한 입력 검증
2. **파라미터 바인딩**: 동적 테이블명도 가능한 한 사전 검증된 값만 사용
3. **권한 체크**: 환경별 테이블 접근 시 환경별 권한 검증

### 8.3 파서 개선 권장사항
1. **+ 연산자 패턴 지원**: 문자열 결합 패턴 파싱 능력 향상
2. **String.format 패턴 지원**: 템플릿 기반 쿼리 인식
3. **CONCAT 함수 지원**: 함수와 연산자 혼합 패턴 처리
4. **환경 변수 처리**: ${environment} 등 동적 치환자 인식

### 8.4 유지보수성 개선 (기존 + 신규)
1. **쿼리 복잡도 관리**: 매우 복잡한 쿼리는 뷰나 프로시저로 분리 고려
2. **환경별 설정 통합**: 환경별 테이블명 매핑을 설정 파일로 관리
3. **동적 쿼리 테스트**: + 연산자와 String.format 패턴의 단위 테스트 강화
4. **문서화**: 복잡한 비즈니스 로직이 포함된 CTE와 윈도우 함수에 상세 주석

---

**분석 완료일**: 2025년 9월 18일  
**총 분석 파일 수**: 16개 (XML 12개, Java 4개) - v1: 10개 → v2: 16개  
**총 쿼리 수**: 110개 - v1: 74개 → v2: 110개 (+36개 증가)  
**파싱 에러 쿼리**: 6개 (동일)  
**새로 추가된 주요 패턴**: 기업급 복잡 쿼리, XML 직접 접근, + 연산자 패턴, String.format 패턴, 미지원 패턴 시뮬레이션
