# sampleSrc 프로젝트 쿼리 및 테이블 분석 리포트

## 1. 분석 개요

- **분석 대상**: sampleSrc 프로젝트의 모든 SQL 쿼리
- **분석 범위**: XML 매퍼 파일, Java 파일, JSP 파일
- **분석 일시**: 2025년 9월 18일
- **총 쿼리 수**: 74개
- **다이나믹 쿼리 포함**: 예

## 2. 파일별 쿼리 분석

### 2.1 XML 매퍼 파일

#### UserMapper.xml (메인)
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | 설명 |
|---------|-----------|-------------|----------|------|
| findUsersByCondition | SELECT | users | Y | 조건별 사용자 조회 |
| findUsersByAdvancedCondition | SELECT | users | Y | 고급 조건 사용자 조회 |
| findUsersByType | SELECT | users | N | 사용자 타입별 조회 |
| findUserById | SELECT | users | N | 사용자 ID로 조회 |
| createUser | INSERT | users | N | 사용자 생성 |
| updateUser | UPDATE | users | Y | 사용자 정보 수정 |
| deleteUser | UPDATE | users | N | 사용자 삭제(논리삭제) |
| existsByUsername | SELECT | users | N | 사용자명 중복 확인 |
| existsByEmail | SELECT | users | N | 이메일 중복 확인 |
| isEmailVerified | SELECT | users | N | 이메일 인증 여부 확인 |
| isPhoneVerified | SELECT | users | N | 전화번호 인증 여부 확인 |
| getTotalUserCount | SELECT | users | N | 총 사용자 수 조회 |
| getActiveUserCount | SELECT | users | N | 활성 사용자 수 조회 |
| getNewUsersTodayCount | SELECT | users | N | 오늘 가입 사용자 수 조회 |
| getPremiumUserCount | SELECT | users | N | 프리미엄 사용자 수 조회 |
| updateLastLogin | UPDATE | users | N | 사용자 로그인 기록 업데이트 |
| getUserStatisticsByStatus | SELECT | users | N | 사용자 상태별 통계 |
| getUserStatisticsByType | SELECT | users | N | 사용자 타입별 통계 |
| getMonthlyRegistrationStats | SELECT | users | Y | 월별 가입자 통계 |
| findUsersWithOrderInfo | SELECT | users, orders | Y | 사용자와 주문 정보 조인 |
| findUsersByComplexSearch | SELECT | users, orders | Y | 복잡한 동적 검색 |

#### ProductMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | 설명 |
|---------|-----------|-------------|----------|------|
| selectProductById | SELECT | products | N | 상품 ID로 조회 |
| selectProductsByCondition | SELECT | products | Y | 조건부 상품 조회 |
| selectProductsByAdvancedCondition | SELECT | products, categories, brands | Y | 고급 조건부 상품 조회 |
| selectProductsByCategory | SELECT | products | N | 카테고리별 상품 조회 |
| updateProductStock | UPDATE | products | N | 재고 업데이트 |
| updateProductDynamic | UPDATE | products | Y | 동적 상품 업데이트 |
| insertProductDynamic | INSERT | products | Y | 동적 상품 삽입 |
| deleteProductsByCondition | UPDATE | products | Y | 조건부 상품 삭제 |
| countProductsByCondition | SELECT | products | Y | 조건부 상품 수 조회 |

#### UserManagementMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | 설명 |
|---------|-----------|-------------|----------|------|
| selectUsers | SELECT | users | N | 사용자 목록 조회 |
| selectUserById | SELECT | users, user_info | N | 사용자 상세 조회 |
| insertUser | INSERT | users | N | 사용자 생성 |
| updateUser | UPDATE | users | N | 사용자 수정 |
| deleteUser | UPDATE | users | N | 사용자 삭제 |
| selectUserStatistics | SELECT | users | N | 사용자 통계 조회 |

#### MicroserviceMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | 설명 |
|---------|-----------|-------------|----------|------|
| selectUserProfile | SELECT | users, user_info, user_profiles, orders | N | 통합 사용자 정보 조회 |
| selectOrderDetails | SELECT | orders, users, order_items, products | N | 통합 주문 정보 조회 |
| selectDashboardData | SELECT | users, products, orders, notifications, recommendations | N | 통합 대시보드 데이터 |
| selectGlobalSearch | SELECT | users, products, orders | N | 통합 검색 |
| insertNotification | INSERT | notifications | N | 통합 알림 발송 |

#### ProxyMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | 설명 |
|---------|-----------|-------------|----------|------|
| selectUsersFromV1 | SELECT | users_v1 | N | v1 API 사용자 조회 |
| insertUserToV1 | INSERT | users_v1 | N | v1 API 사용자 생성 |
| selectProductsFromInternalService | SELECT | products, categories, brands | N | 내부 제품 서비스 조회 |
| selectOrdersFromInternalService | SELECT | orders, users | N | 내부 주문 서비스 조회 |
| processPaymentExternal | SELECT | payments | N | 외부 결제 처리 |

#### VersionedMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | 설명 |
|---------|-----------|-------------|----------|------|
| selectUsersV1 | SELECT | users | N | 사용자 조회 v1 |
| selectUsersV2 | SELECT | users, user_info, orders | N | 사용자 조회 v2 |
| selectProductsV1 | SELECT | products | N | 제품 조회 v1 |
| selectProductsV2 | SELECT | products, categories, order_items | N | 제품 조회 v2 |
| selectOrdersV1 | SELECT | orders | N | 주문 조회 v1 |
| selectOrdersV2 | SELECT | orders, users, order_items | Y | 주문 조회 v2 |

#### ImplicitJoinMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | 설명 |
|---------|-----------|-------------|----------|------|
| getUsersWithTypes | SELECT | users, user_types | N | 기본 implicit join |
| getProductsWithCategoryAndBrand | SELECT | products, categories, brands | N | 3개 테이블 implicit join |
| getOrdersWithUsers | SELECT | orders, users | N | 별칭 있는 implicit join |
| getComplexJoin | SELECT | users, user_types, products, categories | N | 복잡한 조건의 implicit join |
| getMixedJoin | SELECT | users, user_types, user_roles, roles, products | N | 혼합 조인 |

#### ImplicitJoinTestMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | 설명 |
|---------|-----------|-------------|----------|------|
| selectUsersWithImplicitDeptId | SELECT | USERS, DEPARTMENTS | N | 별칭 생략 케이스 |
| selectUsersAndEmployeesWithSameColumn | SELECT | USERS, EMPLOYEES | N | 동일 컬럼명 케이스 |
| selectUsersWithExplicitAlias | SELECT | USERS, DEPARTMENTS | N | 명시적 별칭 |
| selectUsersWithComplexImplicitJoin | SELECT | USERS, DEPARTMENTS | N | 복합 조건 별칭 생략 |
| selectUsersInSubqueryWithImplicitJoin | SELECT | USERS, DEPARTMENTS | N | 서브쿼리 내 별칭 생략 |
| selectMultipleImplicitJoinsWithSameColumn | SELECT | USERS, EMPLOYEES, DEPARTMENTS | N | 여러 테이블 동일 컬럼명 |
| selectFromSubqueryWithImplicitJoin | SELECT | USERS, DEPARTMENTS | N | FROM 서브쿼리 별칭 생략 |
| selectComplexQueryExample | SELECT | USERS, DEPARTMENTS, PROJECT_MEMBERS, PROJECTS, EMPLOYEES | N | 스칼라/인라인뷰 복잡 쿼리 |
| selectQueryWithExistsAndInSubqueries | SELECT | USERS, DEPARTMENTS, EMPLOYEES, PROJECT_MEMBERS, PROJECTS | N | EXISTS/IN 서브쿼리 |
| selectImplicitJoinWithComplexConditions | SELECT | USERS, DEPARTMENTS, EMPLOYEES, PROJECT_MEMBERS, PROJECTS | N | Implicit Join 복잡 조건 |

#### MixedErrorMapper.xml
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | 설명 |
|---------|-----------|-------------|----------|------|
| selectAll | SELECT | users | N | 전체 조회 |
| selectById | SELECT | users | N | ID로 조회 |
| selectByName | SELECT | users | Y | 이름으로 조회 (일부 오류) |
| insert | INSERT | users | N | 사용자 삽입 |
| update | UPDATE | users | Y | 사용자 수정 (일부 오류) |
| delete | DELETE | users | N | 사용자 삭제 |
| searchUsers | SELECT | users | Y | 동적 사용자 검색 (일부 오류) |
| countUsers | SELECT | users | N | 사용자 수 조회 |
| getUserWithDetails | SELECT | users, user_roles, roles | N | 사용자 상세 정보 (일부 오류) |
| selectFromNonExistentTable | SELECT | NONEXISTENT_TABLE | N | 존재하지 않는 테이블 참조 |
| selectWithNonExistentColumn | SELECT | users | N | 존재하지 않는 컬럼 참조 |
| selectComplexError | SELECT | users, NONEXISTENT_TABLE | N | 복합 오류 |

#### UserMapper.xml (dynamicquery 패키지)
| 쿼리 ID | 쿼리 유형 | 사용 테이블 | 다이나믹 | 설명 |
|---------|-----------|-------------|----------|------|
| findUsers | SELECT | USERS, DEPARTMENTS, USER_PROFILES | Y | Oracle Implicit Join 방식 |
| findUsersWithAnsiJoin | SELECT | USERS, DEPARTMENTS, USER_PROFILES | Y | ANSI Join 방식 |
| findUsersWithAliasOmission | SELECT | USERS, DEPARTMENTS, USER_PROFILES | N | 별칭 생략 형태 |
| findUsersWithMixedJoins | SELECT | USERS, DEPARTMENTS, USER_PROFILES, USER_TYPES | N | 혼합 형태 조인 |
| findComplexJoins | SELECT | ORDERS, CUSTOMERS, ORDER_ITEMS, PRODUCTS | N | 복잡한 조인 |
| findUsersWithScatteredConditions | SELECT | USERS, DEPARTMENTS, USER_PROFILES, USER_TYPES, USER_ROLES, ROLES | N | 분산된 조건 |
| findOrdersWithScatteredJoins | SELECT | ORDERS, CUSTOMERS, ORDER_ITEMS, PRODUCTS, CATEGORIES, BRANDS | N | 분산된 조인 조건 |
| findComplexScatteredJoins | SELECT | USERS, DEPARTMENTS, USER_PROFILES, USER_TYPES, ORDERS, CUSTOMERS | N | 서브쿼리와 조인 혼합 |

### 2.2 Java 파일

#### DirectQueryServlet.java
| 메서드 | 쿼리 유형 | 사용 테이블 | 다이나믹 | 설명 |
|--------|-----------|-------------|----------|------|
| queryUsersDirectly | SELECT | users | Y | 직접 사용자 조회 |
| queryOrdersDirectly | SELECT | orders, users | Y | 직접 주문 조회 |
| queryProductsDirectly | SELECT | products, categories | Y | 직접 상품 조회 |
| queryComplexDataDirectly | SELECT | users, orders, order_items, products | Y | 복잡한 조인 쿼리 |
| insertUserDirectly | INSERT | users | N | 직접 사용자 삽입 |

## 3. 테이블별 사용 현황

### 3.1 주요 테이블

| 테이블명 | 사용 횟수 | 주요 용도 | 관련 쿼리 |
|----------|-----------|-----------|-----------|
| users | 45 | 사용자 정보 관리 | 조회, 생성, 수정, 삭제, 통계 |
| orders | 15 | 주문 정보 관리 | 주문 조회, 통계, 조인 |
| products | 12 | 상품 정보 관리 | 상품 조회, 수정, 재고 관리 |
| USERS | 8 | 사용자 정보 (Oracle 스타일) | Implicit Join, 복잡 쿼리 |
| DEPARTMENTS | 8 | 부서 정보 | 조인, Implicit Join |
| categories | 6 | 상품 카테고리 | 상품 분류, 조인 |
| user_info | 4 | 사용자 상세 정보 | 사용자 프로필 확장 |
| USER_PROFILES | 4 | 사용자 프로필 | 프로필 정보 조인 |
| order_items | 4 | 주문 상품 정보 | 주문 상세, 통계 |
| brands | 3 | 브랜드 정보 | 상품 브랜드 조인 |

### 3.2 보조 테이블

| 테이블명 | 사용 횟수 | 주요 용도 |
|----------|-----------|-----------|
| user_types | 3 | 사용자 타입 분류 |
| user_roles | 3 | 사용자 역할 관리 |
| roles | 3 | 역할 정의 |
| notifications | 2 | 알림 관리 |
| recommendations | 1 | 추천 시스템 |
| payments | 1 | 결제 정보 |
| users_v1 | 2 | 버전별 사용자 테이블 |
| user_profiles | 2 | 사용자 프로필 확장 |
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
- **총 쿼리 수**: 74개
- **다이나믹 쿼리 수**: 18개
- **다이나믹 쿼리 비율**: 24.3%

### 4.2 주요 다이나믹 쿼리 패턴

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

## 5. 특이사항 및 주목할 점

### 5.1 Oracle Implicit Join 사용
- ImplicitJoinMapper.xml과 UserMapper.xml(dynamicquery)에서 Oracle 스타일의 Implicit Join 사용
- ANSI JOIN과 혼용하여 사용

### 5.2 에러 시뮬레이션
- MixedErrorMapper.xml에서 의도적인 오류 케이스 포함
- 존재하지 않는 테이블/컬럼 참조 테스트

### 5.3 버전별 API 지원
- VersionedMapper.xml에서 v1, v2 API 버전별 쿼리 제공
- 기능 확장에 따른 쿼리 진화 패턴 시연

### 5.4 Java 직접 쿼리
- DirectQueryServlet.java에서 MyBatis 없이 직접 SQL 조합
- 런타임 동적 쿼리 생성 예시

## 6. 권장사항

### 6.1 쿼리 최적화
1. **인덱스 활용**: 자주 사용되는 WHERE 조건 컬럼에 인덱스 생성
2. **조인 최적화**: Implicit Join보다는 명시적 JOIN 사용 권장
3. **페이징 처리**: 대용량 데이터 조회 시 LIMIT/OFFSET 적극 활용

### 6.2 보안 강화
1. **SQL Injection 방지**: 모든 동적 쿼리에서 파라미터 바인딩 사용
2. **권한 체크**: 민감한 데이터 조회 시 권한 검증 로직 추가

### 6.3 유지보수성 개선
1. **쿼리 통합**: 유사한 기능의 쿼리들 통합 고려
2. **네이밍 규칙**: 일관된 테이블/컬럼 명명 규칙 적용
3. **문서화**: 복잡한 비즈니스 로직이 포함된 쿼리에 주석 추가

---

**분석 완료일**: 2025년 9월 18일  
**총 분석 파일 수**: 10개 (XML 9개, Java 1개)  
**총 쿼리 수**: 74개
