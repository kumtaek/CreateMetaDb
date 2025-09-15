# API 매핑 사례 분석

## 개요

CallChain 리포트에서 FRONTEND_API와 API_ENTRY가 서로 다른 의미를 가지는 다양한 사례들을 분석합니다. 이 문서는 sampleSrc 프로젝트에 구현된 실제 사례들을 바탕으로 작성되었습니다.

## 1. 1:N 관계 사례

### 1.1 UserManagementController

**설명**: 하나의 프론트엔드 페이지에서 여러 개의 API를 호출하는 경우

**구조**:
```
FRONTEND_API: UserManagementPage
    ├── API_ENTRY: GET /api/user-management/users
    ├── API_ENTRY: GET /api/user-management/users/{id}
    ├── API_ENTRY: POST /api/user-management/users
    ├── API_ENTRY: PUT /api/user-management/users/{id}
    ├── API_ENTRY: DELETE /api/user-management/users/{id}
    └── API_ENTRY: GET /api/user-management/statistics
```

**실제 사용 예시**:
```javascript
// React 컴포넌트 (FRONTEND_API)
const UserManagementPage = () => {
    // 여러 API 호출
    const fetchUsers = () => fetch('/api/user-management/users');
    const fetchUserDetail = (id) => fetch(`/api/user-management/users/${id}`);
    const createUser = (userData) => fetch('/api/user-management/users', {
        method: 'POST',
        body: JSON.stringify(userData)
    });
    const updateUser = (id, userData) => fetch(`/api/user-management/users/${id}`, {
        method: 'PUT',
        body: JSON.stringify(userData)
    });
    const deleteUser = (id) => fetch(`/api/user-management/users/${id}`, {
        method: 'DELETE'
    });
    const fetchStatistics = () => fetch('/api/user-management/statistics');
    
    return <div>{/* 하나의 페이지에서 여러 API 사용 */}</div>;
};
```

**CallChain 리포트 표시**:
| FRONTEND_API | API_ENTRY | 클래스 | 메서드 |
|-------------|-----------|--------|--------|
| UserManagementPage | GET /api/user-management/users | UserManagementController | getUsers |
| UserManagementPage | GET /api/user-management/users/{id} | UserManagementController | getUserDetail |
| UserManagementPage | POST /api/user-management/users | UserManagementController | createUser |

## 2. 프록시/게이트웨이 패턴 사례

### 2.1 ProxyController

**설명**: 프론트엔드에서 호출하는 URL과 실제 백엔드 서비스 URL이 다른 경우

**구조**:
```
FRONTEND_API: GET /api/users
    └── API_ENTRY: GET /api/v1/users

FRONTEND_API: GET /api/products
    └── API_ENTRY: GET /internal/product-service/products

FRONTEND_API: POST /api/payment
    └── API_ENTRY: POST /external/payment-gateway/process
```

**실제 사용 예시**:
```java
@RestController
@RequestMapping("/api")
public class ProxyController {
    
    @GetMapping("/users")
    public ResponseEntity<Map<String, Object>> getUsers() {
        // 내부적으로 /api/v1/users 호출
        return ResponseEntity.ok().build();
    }
    
    @GetMapping("/products")
    public ResponseEntity<Map<String, Object>> getProducts() {
        // 내부적으로 /internal/product-service/products 호출
        return ResponseEntity.ok().build();
    }
}
```

**CallChain 리포트 표시**:
| FRONTEND_API | API_ENTRY | 클래스 | 메서드 |
|-------------|-----------|--------|--------|
| GET /api/users | GET /api/v1/users | ProxyController | getUsers |
| GET /api/products | GET /internal/product-service/products | ProxyController | getProducts |
| POST /api/payment | POST /external/payment-gateway/process | ProxyController | processPayment |

## 3. 버전 관리 사례

### 3.1 VersionedController

**설명**: 같은 기능이지만 다른 버전의 API를 제공하는 경우

**구조**:
```
FRONTEND_API: GET /api/users
    ├── API_ENTRY: GET /api/v1/users (기본 버전)
    └── API_ENTRY: GET /api/v2/users (개선된 버전)

FRONTEND_API: GET /api/products
    ├── API_ENTRY: GET /api/v1/products (기본 버전)
    └── API_ENTRY: GET /api/v2/products (페이징 지원)
```

**실제 사용 예시**:
```java
@RestController
@RequestMapping("/api")
public class VersionedController {
    
    @GetMapping("/v1/users")
    public ResponseEntity<Map<String, Object>> getUsersV1() {
        // v1 사용자 조회 로직
        return ResponseEntity.ok().build();
    }
    
    @GetMapping("/v2/users")
    public ResponseEntity<Map<String, Object>> getUsersV2() {
        // v2 사용자 조회 로직 (개선된 기능)
        return ResponseEntity.ok().build();
    }
}
```

**CallChain 리포트 표시**:
| FRONTEND_API | API_ENTRY | 클래스 | 메서드 |
|-------------|-----------|--------|--------|
| GET /api/users | GET /api/v1/users | VersionedController | getUsersV1 |
| GET /api/users | GET /api/v2/users | VersionedController | getUsersV2 |
| GET /api/products | GET /api/v1/products | VersionedController | getProductsV1 |
| GET /api/products | GET /api/v2/products | VersionedController | getProductsV2 |

## 4. 마이크로서비스 패턴 사례

### 4.1 MicroserviceController

**설명**: 프론트엔드에서 하나의 API를 호출하지만 내부적으로 여러 서비스를 조합하는 경우

**구조**:
```
FRONTEND_API: GET /api/user-profile
    └── API_ENTRY: GET /internal/user-service/profile
        ├── 내부 호출: /internal/user-service/users/{userId}
        ├── 내부 호출: /internal/profile-service/profiles/{userId}
        └── 내부 호출: /internal/preference-service/preferences/{userId}

FRONTEND_API: GET /api/dashboard
    └── API_ENTRY: GET /internal/analytics-service/dashboard
        ├── 내부 호출: /internal/analytics-service/statistics
        ├── 내부 호출: /internal/notification-service/unread-count
        └── 내부 호출: /internal/recommendation-service/suggestions
```

**실제 사용 예시**:
```java
@RestController
@RequestMapping("/api")
public class MicroserviceController {
    
    @GetMapping("/user-profile")
    public ResponseEntity<Map<String, Object>> getUserProfile(@RequestParam Long userId) {
        // 내부적으로 여러 서비스 조합:
        // 1. /internal/user-service/users/{userId}
        // 2. /internal/profile-service/profiles/{userId}
        // 3. /internal/preference-service/preferences/{userId}
        return ResponseEntity.ok().build();
    }
    
    @GetMapping("/dashboard")
    public ResponseEntity<Map<String, Object>> getDashboardData() {
        // 내부적으로 여러 서비스 조합:
        // 1. /internal/analytics-service/statistics
        // 2. /internal/notification-service/unread-count
        // 3. /internal/recommendation-service/suggestions
        return ResponseEntity.ok().build();
    }
}
```

**CallChain 리포트 표시**:
| FRONTEND_API | API_ENTRY | 클래스 | 메서드 |
|-------------|-----------|--------|--------|
| GET /api/user-profile | GET /internal/user-service/profile | MicroserviceController | getUserProfile |
| GET /api/dashboard | GET /internal/analytics-service/dashboard | MicroserviceController | getDashboardData |
| GET /api/search | GET /internal/search-service/global | MicroserviceController | globalSearch |

## 5. 데이터베이스 관계 구조

### 5.1 Components 테이블

```sql
-- FRONTEND_API 컴포넌트
INSERT INTO components VALUES (
    1001, 1, NULL, 'UserManagementPage', 'FRONTEND_API', 
    NULL, 'FRONTEND', NULL, NULL, 'N', NULL, 'hash123', '2024-01-01', '2024-01-01', 'N'
);

-- API_ENTRY 컴포넌트들
INSERT INTO components VALUES 
(1002, 1, 201, 'UserManagementController', 'API_ENTRY', NULL, 'CONTROLLER', 25, 35, 'N', NULL, 'hash456', '2024-01-01', '2024-01-01', 'N'),
(1003, 1, 202, 'UserManagementController', 'API_ENTRY', NULL, 'CONTROLLER', 40, 50, 'N', NULL, 'hash789', '2024-01-01', '2024-01-01', 'N'),
(1004, 1, 203, 'UserManagementController', 'API_ENTRY', NULL, 'CONTROLLER', 55, 65, 'N', NULL, 'hash101', '2024-01-01', '2024-01-01', 'N');
```

### 5.2 Relationships 테이블

```sql
-- 1:N 관계 테이블
INSERT INTO relationships VALUES 
(1001, 1002, 'CALL_API_F2B', 0.95, 'N', NULL, 'hash_rel1', '2024-01-01', '2024-01-01', 'N'),  -- UserManagementPage -> getUsers
(1001, 1003, 'CALL_API_F2B', 0.95, 'N', NULL, 'hash_rel2', '2024-01-01', '2024-01-01', 'N'),  -- UserManagementPage -> getUserDetail  
(1001, 1004, 'CALL_API_F2B', 0.95, 'N', NULL, 'hash_rel3', '2024-01-01', '2024-01-01', 'N');  -- UserManagementPage -> createUser
```

## 6. CallChain 리포트 해석

### 6.1 1:N 관계 해석

**의미**: 하나의 프론트엔드 페이지가 여러 백엔드 API를 호출하는 경우
**활용**: 프론트엔드 페이지의 복잡도 분석, API 사용량 분석

### 6.2 프록시 패턴 해석

**의미**: 프론트엔드와 백엔드 간의 URL 매핑 차이
**활용**: API 게이트웨이 분석, 서비스 간 의존성 분석

### 6.3 버전 관리 해석

**의미**: API 버전별 사용 현황
**활용**: API 마이그레이션 계획, 버전별 성능 분석

### 6.4 마이크로서비스 해석

**의미**: 통합 API의 내부 서비스 조합
**활용**: 서비스 의존성 분석, 성능 병목 지점 파악

## 7. 분석 도구 활용

### 7.1 CallChain 리포트 필터링

- **FRONTEND_API별 그룹화**: 같은 프론트엔드에서 호출하는 API들 확인
- **API_ENTRY별 그룹화**: 같은 백엔드 API를 호출하는 프론트엔드들 확인
- **관계 유형별 분석**: 1:1, 1:N, N:1 관계 패턴 분석

### 7.2 성능 분석

- **API 호출 빈도**: FRONTEND_API별 API_ENTRY 호출 횟수
- **응답 시간**: API_ENTRY별 평균 응답 시간
- **에러율**: API_ENTRY별 에러 발생률

## 8. 완전한 메타데이터 샘플

### 8.1 UserManagementController - 1:N 관계 완전 구현

#### Service 클래스
```java
@Service
public class UserManagementService {
    @Autowired
    private UserManagementDao userManagementDao;

    public List<Map<String, Object>> getUsers() {
        return userManagementDao.selectUsers();
    }

    public Map<String, Object> getUserDetail(Long userId) {
        return userManagementDao.selectUserById(userId);
    }

    public int createUser(Map<String, Object> userData) {
        return userManagementDao.insertUser(userData);
    }
}
```

#### DAO 인터페이스
```java
@Mapper
public interface UserManagementDao {
    List<Map<String, Object>> selectUsers();
    Map<String, Object> selectUserById(@Param("userId") Long userId);
    int insertUser(@Param("userData") Map<String, Object> userData);
}
```

#### XML Mapper
```xml
<select id="selectUsers" resultType="map">
    SELECT 
        user_id, username, email, status, created_at, updated_at
    FROM users
    WHERE del_yn = 'N'
    ORDER BY created_at DESC
</select>

<select id="selectUserById" parameterType="long" resultType="map">
    SELECT 
        u.user_id, u.username, u.email, u.status,
        ui.phone, ui.address, ui.birth_date
    FROM users u
    LEFT JOIN user_info ui ON u.user_id = ui.user_id
    WHERE u.user_id = #{userId} AND u.del_yn = 'N'
</select>
```

#### 데이터베이스 테이블
```sql
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    del_yn CHAR(1) DEFAULT 'N'
);

CREATE TABLE user_info (
    user_info_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    birth_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### 8.2 ProxyController - 프록시 패턴 완전 구현

#### Service 클래스
```java
@Service
public class ProxyService {
    @Autowired
    private ProxyDao proxyDao;

    public Map<String, Object> getUsers() {
        return proxyDao.selectUsersFromV1();
    }

    public Map<String, Object> getProducts() {
        return proxyDao.selectProductsFromInternalService();
    }
}
```

#### DAO 인터페이스
```java
@Mapper
public interface ProxyDao {
    Map<String, Object> selectUsersFromV1();
    Map<String, Object> selectProductsFromInternalService();
}
```

#### XML Mapper
```xml
<select id="selectUsersFromV1" resultType="map">
    SELECT user_id, username, email, status, created_at
    FROM users_v1
    WHERE del_yn = 'N'
    ORDER BY created_at DESC
    LIMIT 100
</select>

<select id="selectProductsFromInternalService" resultType="map">
    SELECT 
        p.product_id, p.product_name, p.price, p.stock_quantity,
        c.category_name, b.brand_name
    FROM products p
    JOIN categories c ON p.category_id = c.category_id
    JOIN brands b ON p.brand_id = b.brand_id
    WHERE p.del_yn = 'N' AND p.status = 'ACTIVE'
</select>
```

#### 데이터베이스 테이블
```sql
CREATE TABLE users_v1 (
    user_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    del_yn CHAR(1) DEFAULT 'N'
);

CREATE TABLE products (
    product_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category_id BIGINT,
    brand_id BIGINT,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    del_yn CHAR(1) DEFAULT 'N'
);
```

### 8.3 VersionedController - 버전 관리 완전 구현

#### Service 클래스
```java
@Service
public class VersionedService {
    @Autowired
    private VersionedDao versionedDao;

    public Map<String, Object> getUsersV1() {
        return versionedDao.selectUsersV1();
    }

    public Map<String, Object> getUsersV2() {
        return versionedDao.selectUsersV2();
    }
}
```

#### DAO 인터페이스
```java
@Mapper
public interface VersionedDao {
    Map<String, Object> selectUsersV1();
    Map<String, Object> selectUsersV2();
}
```

#### XML Mapper
```xml
<!-- v1 API -->
<select id="selectUsersV1" resultType="map">
    SELECT user_id, username, email, status, created_at
    FROM users
    WHERE del_yn = 'N'
    ORDER BY created_at DESC
</select>

<!-- v2 API (개선된 버전) -->
<select id="selectUsersV2" resultType="map">
    SELECT 
        u.user_id, u.username, u.email, u.status, u.created_at,
        ui.phone, ui.last_login_at,
        COUNT(o.order_id) as order_count
    FROM users u
    LEFT JOIN user_info ui ON u.user_id = ui.user_id
    LEFT JOIN orders o ON u.user_id = o.user_id AND o.del_yn = 'N'
    WHERE u.del_yn = 'N'
    GROUP BY u.user_id
    ORDER BY u.created_at DESC
</select>
```

### 8.4 MicroserviceController - 마이크로서비스 패턴 완전 구현

#### Service 클래스
```java
@Service
public class MicroserviceService {
    @Autowired
    private MicroserviceDao microserviceDao;

    public Map<String, Object> getUserProfile(Long userId) {
        return microserviceDao.selectUserProfile(userId);
    }

    public Map<String, Object> getDashboardData() {
        return microserviceDao.selectDashboardData();
    }
}
```

#### DAO 인터페이스
```java
@Mapper
public interface MicroserviceDao {
    Map<String, Object> selectUserProfile(@Param("userId") Long userId);
    Map<String, Object> selectDashboardData();
}
```

#### XML Mapper
```xml
<select id="selectUserProfile" parameterType="long" resultType="map">
    SELECT 
        u.user_id, u.username, u.email, u.status,
        ui.phone, ui.address, ui.birth_date,
        up.profile_image, up.bio, up.preferences,
        COUNT(o.order_id) as total_orders,
        SUM(o.total_amount) as total_spent
    FROM users u
    LEFT JOIN user_info ui ON u.user_id = ui.user_id
    LEFT JOIN user_profiles up ON u.user_id = up.user_id
    LEFT JOIN orders o ON u.user_id = o.user_id AND o.del_yn = 'N'
    WHERE u.user_id = #{userId} AND u.del_yn = 'N'
    GROUP BY u.user_id
</select>

<select id="selectDashboardData" resultType="map">
    SELECT 
        (SELECT COUNT(*) FROM users WHERE del_yn = 'N') as total_users,
        (SELECT COUNT(*) FROM products WHERE del_yn = 'N' AND status = 'ACTIVE') as total_products,
        (SELECT COUNT(*) FROM orders WHERE del_yn = 'N') as total_orders,
        (SELECT SUM(total_amount) FROM orders WHERE del_yn = 'N' AND status = 'COMPLETED') as total_revenue
</select>
```

#### 데이터베이스 테이블
```sql
CREATE TABLE user_profiles (
    profile_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    profile_image VARCHAR(255),
    bio TEXT,
    preferences JSON,
    del_yn CHAR(1) DEFAULT 'N',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE notifications (
    notification_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    is_read CHAR(1) DEFAULT 'N',
    del_yn CHAR(1) DEFAULT 'N',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### 8.5 CallChain 리포트 예상 결과

#### 1:N 관계 결과
| FRONTEND_API | API_ENTRY | 클래스 | 메서드 | XML파일 | 쿼리ID | 쿼리종류 | 관련테이블들 |
|-------------|-----------|--------|--------|---------|--------|----------|-------------|
| UserManagementPage | GET /api/user-management/users | UserManagementController | getUsers | UserManagementMapper.xml | selectUsers | SELECT | USERS |
| UserManagementPage | GET /api/user-management/users/{id} | UserManagementController | getUserDetail | UserManagementMapper.xml | selectUserById | SELECT | USERS,USER_INFO |
| UserManagementPage | POST /api/user-management/users | UserManagementController | createUser | UserManagementMapper.xml | insertUser | INSERT | USERS |

#### 프록시 패턴 결과
| FRONTEND_API | API_ENTRY | 클래스 | 메서드 | XML파일 | 쿼리ID | 쿼리종류 | 관련테이블들 |
|-------------|-----------|--------|--------|---------|--------|----------|-------------|
| GET /api/users | GET /api/v1/users | ProxyController | getUsers | ProxyMapper.xml | selectUsersFromV1 | SELECT | USERS_V1 |
| GET /api/products | GET /internal/product-service/products | ProxyController | getProducts | ProxyMapper.xml | selectProductsFromInternalService | SELECT | PRODUCTS,CATEGORIES,BRANDS |

#### 버전 관리 결과
| FRONTEND_API | API_ENTRY | 클래스 | 메서드 | XML파일 | 쿼리ID | 쿼리종류 | 관련테이블들 |
|-------------|-----------|--------|--------|---------|--------|----------|-------------|
| GET /api/users | GET /api/v1/users | VersionedController | getUsersV1 | VersionedMapper.xml | selectUsersV1 | SELECT | USERS |
| GET /api/users | GET /api/v2/users | VersionedController | getUsersV2 | VersionedMapper.xml | selectUsersV2 | SELECT | USERS,USER_INFO,ORDERS |

#### 마이크로서비스 결과
| FRONTEND_API | API_ENTRY | 클래스 | 메서드 | XML파일 | 쿼리ID | 쿼리종류 | 관련테이블들 |
|-------------|-----------|--------|--------|---------|--------|----------|-------------|
| GET /api/user-profile | GET /internal/user-service/profile | MicroserviceController | getUserProfile | MicroserviceMapper.xml | selectUserProfile | SELECT | USERS,USER_INFO,USER_PROFILES,ORDERS |
| GET /api/dashboard | GET /internal/analytics-service/dashboard | MicroserviceController | getDashboardData | MicroserviceMapper.xml | selectDashboardData | SELECT | USERS,PRODUCTS,ORDERS |

## 9. 결론

FRONTEND_API와 API_ENTRY의 다양한 매핑 사례를 통해:

1. **1:N 관계**: 프론트엔드 페이지의 복잡도 파악
2. **프록시 패턴**: API 게이트웨이 역할 분석
3. **버전 관리**: API 진화 과정 추적
4. **마이크로서비스**: 서비스 간 의존성 분석

**완전한 메타데이터 구현**을 통해:
- **Service → DAO → XML → Query → Table** 전체 호출 체인 추적
- **실제 사용 가능한 샘플 코드** 제공
- **데이터베이스 스키마**와 **샘플 데이터** 포함
- **CallChain 리포트**에서 의미있는 차이점 표시

이러한 분석을 통해 시스템의 아키텍처 이해도 향상과 성능 최적화 방안 도출이 가능합니다.
