package com.example.jpa.controller;

import com.example.jpa.entity.User;
import com.example.jpa.entity.UserStatus;
import com.example.jpa.entity.UserType;
import com.example.jpa.service.JpaUserService;
import com.example.jpa.dto.UserSummaryDto;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * JPA User REST Controller
 * JpaUserService를 통한 사용자 관리 REST API
 * FRONTEND_API -> API_ENTRY -> JPA Repository -> TABLE 연결 구조 테스트케이스
 */
@RestController
@RequestMapping("/api/jpa/users")
@CrossOrigin(origins = "*")
public class JpaUserController {
    
    @Autowired
    private JpaUserService jpaUserService;
    
    // 1. 기본 CRUD API
    /**
     * 사용자 생성
     * FRONTEND_API: POST /api/jpa/users -> API_ENTRY: createUser() -> JPA: UserRepository.save() -> TABLE: USERS
     */
    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody User user) {
        try {
            User createdUser = jpaUserService.createUser(user);
            return ResponseEntity.status(HttpStatus.CREATED).body(createdUser);
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.CONFLICT).build();
        }
    }
    
    /**
     * 사용자 조회 (ID)
     * FRONTEND_API: GET /api/jpa/users/{id} -> API_ENTRY: getUserById() -> JPA: UserRepository.findById() -> TABLE: USERS
     */
    @GetMapping("/{id}")
    public ResponseEntity<User> getUserById(@PathVariable Long id) {
        Optional<User> user = jpaUserService.getUserById(id);
        return user.map(ResponseEntity::ok)
                  .orElse(ResponseEntity.notFound().build());
    }
    
    /**
     * 사용자 수정
     * FRONTEND_API: PUT /api/jpa/users/{id} -> API_ENTRY: updateUser() -> JPA: UserRepository.save() -> TABLE: USERS
     */
    @PutMapping("/{id}")
    public ResponseEntity<User> updateUser(@PathVariable Long id, @RequestBody User user) {
        try {
            user.setUserId(id);
            User updatedUser = jpaUserService.updateUser(user);
            return ResponseEntity.ok(updatedUser);
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * 사용자 삭제
     * FRONTEND_API: DELETE /api/jpa/users/{id} -> API_ENTRY: deleteUser() -> JPA: UserRepository.deleteById() -> TABLE: USERS
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
        try {
            jpaUserService.deleteUser(id);
            return ResponseEntity.noContent().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    // 2. 검색 API
    /**
     * 사용자명으로 조회
     * FRONTEND_API: GET /api/jpa/users/by-username/{username} -> API_ENTRY: getUserByUsername() -> JPA: UserRepository.findByUsername() -> TABLE: USERS
     */
    @GetMapping("/by-username/{username}")
    public ResponseEntity<User> getUserByUsername(@PathVariable String username) {
        Optional<User> user = jpaUserService.getUserByUsername(username);
        return user.map(ResponseEntity::ok)
                  .orElse(ResponseEntity.notFound().build());
    }
    
    /**
     * 이메일로 조회
     * FRONTEND_API: GET /api/jpa/users/by-email/{email} -> API_ENTRY: getUserByEmail() -> JPA: UserRepository.findByEmail() -> TABLE: USERS
     */
    @GetMapping("/by-email/{email}")
    public ResponseEntity<User> getUserByEmail(@PathVariable String email) {
        Optional<User> user = jpaUserService.getUserByEmail(email);
        return user.map(ResponseEntity::ok)
                  .orElse(ResponseEntity.notFound().build());
    }
    
    /**
     * 상태별 사용자 조회
     * FRONTEND_API: GET /api/jpa/users/by-status/{status} -> API_ENTRY: getUsersByStatus() -> JPA: UserRepository.findByStatus() -> TABLE: USERS
     */
    @GetMapping("/by-status/{status}")
    public ResponseEntity<List<User>> getUsersByStatus(@PathVariable UserStatus status) {
        List<User> users = jpaUserService.getUsersByStatus(status);
        return ResponseEntity.ok(users);
    }
    
    /**
     * 사용자 타입별 조회
     * FRONTEND_API: GET /api/jpa/users/by-type/{userType} -> API_ENTRY: getUsersByUserType() -> JPA: UserRepository.findByUserType() -> TABLE: USERS
     */
    @GetMapping("/by-type/{userType}")
    public ResponseEntity<List<User>> getUsersByUserType(@PathVariable UserType userType) {
        List<User> users = jpaUserService.getUsersByUserType(userType);
        return ResponseEntity.ok(users);
    }
    
    // 3. 검색 API
    /**
     * 사용자명 검색
     * FRONTEND_API: GET /api/jpa/users/search/username?q={query} -> API_ENTRY: searchUsersByUsername() -> JPA: UserRepository.findByUsernameContaining() -> TABLE: USERS
     */
    @GetMapping("/search/username")
    public ResponseEntity<List<User>> searchUsersByUsername(@RequestParam String q) {
        List<User> users = jpaUserService.searchUsersByUsername(q);
        return ResponseEntity.ok(users);
    }
    
    /**
     * 이메일 검색
     * FRONTEND_API: GET /api/jpa/users/search/email?q={query} -> API_ENTRY: searchUsersByEmail() -> JPA: UserRepository.findByEmailContaining() -> TABLE: USERS
     */
    @GetMapping("/search/email")
    public ResponseEntity<List<User>> searchUsersByEmail(@RequestParam String q) {
        List<User> users = jpaUserService.searchUsersByEmail(q);
        return ResponseEntity.ok(users);
    }
    
    /**
     * 전체 이름 검색
     * FRONTEND_API: GET /api/jpa/users/search/fullname?q={query} -> API_ENTRY: searchUsersByFullName() -> JPA: UserRepository.findByFullNameContainingIgnoreCase() -> TABLE: USERS
     */
    @GetMapping("/search/fullname")
    public ResponseEntity<List<User>> searchUsersByFullName(@RequestParam String q) {
        List<User> users = jpaUserService.searchUsersByFullName(q);
        return ResponseEntity.ok(users);
    }
    
    // 4. 동적 검색 API
    /**
     * 동적 조건 검색
     * FRONTEND_API: GET /api/jpa/users/search -> API_ENTRY: searchUsers() -> JPA: UserRepository.findUsersByDynamicCriteria() -> TABLE: USERS
     */
    @GetMapping("/search")
    public ResponseEntity<Page<User>> searchUsers(
            @RequestParam(required = false) String username,
            @RequestParam(required = false) String email,
            @RequestParam(required = false) UserStatus status,
            @RequestParam(required = false) UserType userType,
            Pageable pageable) {
        Page<User> users = jpaUserService.searchUsers(username, email, status, userType, pageable);
        return ResponseEntity.ok(users);
    }
    
    // 5. 날짜 기반 검색 API
    /**
     * 기간별 가입 사용자 조회
     * FRONTEND_API: GET /api/jpa/users/created-between -> API_ENTRY: getUsersCreatedBetween() -> JPA: UserRepository.findByCreatedAtBetween() -> TABLE: USERS
     */
    @GetMapping("/created-between")
    public ResponseEntity<List<User>> getUsersCreatedBetween(
            @RequestParam String startDate,
            @RequestParam String endDate) {
        LocalDateTime start = LocalDateTime.parse(startDate);
        LocalDateTime end = LocalDateTime.parse(endDate);
        List<User> users = jpaUserService.getUsersCreatedBetween(start, end);
        return ResponseEntity.ok(users);
    }
    
    /**
     * 특정 날짜 이후 가입 사용자
     * FRONTEND_API: GET /api/jpa/users/created-after -> API_ENTRY: getUsersCreatedAfter() -> JPA: UserRepository.findByCreatedAtAfter() -> TABLE: USERS
     */
    @GetMapping("/created-after")
    public ResponseEntity<List<User>> getUsersCreatedAfter(@RequestParam String date) {
        LocalDateTime dateTime = LocalDateTime.parse(date);
        List<User> users = jpaUserService.getUsersCreatedAfter(dateTime);
        return ResponseEntity.ok(users);
    }
    
    /**
     * 로그인 이력이 없는 사용자
     * FRONTEND_API: GET /api/jpa/users/never-logged-in -> API_ENTRY: getUsersWithoutLogin() -> JPA: UserRepository.findByLastLoginAtIsNull() -> TABLE: USERS
     */
    @GetMapping("/never-logged-in")
    public ResponseEntity<List<User>> getUsersWithoutLogin() {
        List<User> users = jpaUserService.getUsersWithoutLogin();
        return ResponseEntity.ok(users);
    }
    
    // 6. 통계 API
    /**
     * 상태별 사용자 수
     * FRONTEND_API: GET /api/jpa/users/count/by-status/{status} -> API_ENTRY: getUserCountByStatus() -> JPA: UserRepository.countByStatus() -> TABLE: USERS
     */
    @GetMapping("/count/by-status/{status}")
    public ResponseEntity<Long> getUserCountByStatus(@PathVariable UserStatus status) {
        long count = jpaUserService.getUserCountByStatus(status);
        return ResponseEntity.ok(count);
    }
    
    /**
     * 사용자 타입별 통계
     * FRONTEND_API: GET /api/jpa/users/statistics/by-type -> API_ENTRY: getUserTypeStatistics() -> JPA: UserRepository.getUserTypeStatistics() -> TABLE: USERS
     */
    @GetMapping("/statistics/by-type")
    public ResponseEntity<List<Object[]>> getUserTypeStatistics() {
        List<Object[]> statistics = jpaUserService.getUserTypeStatistics();
        return ResponseEntity.ok(statistics);
    }
    
    /**
     * 상태별 통계 (기간별)
     * FRONTEND_API: GET /api/jpa/users/statistics/by-status -> API_ENTRY: getUserStatusStatistics() -> JPA: UserRepository.getUserStatusStatistics() -> TABLE: USERS
     */
    @GetMapping("/statistics/by-status")
    public ResponseEntity<List<Object[]>> getUserStatusStatistics(@RequestParam String fromDate) {
        LocalDateTime dateTime = LocalDateTime.parse(fromDate);
        List<Object[]> statistics = jpaUserService.getUserStatusStatistics(dateTime);
        return ResponseEntity.ok(statistics);
    }
    
    // 7. 특수 검색 API
    /**
     * 이메일 도메인별 사용자 조회
     * FRONTEND_API: GET /api/jpa/users/by-email-domain/{domain} -> API_ENTRY: getUsersByEmailDomain() -> JPA: UserRepository.findByEmailDomain() -> TABLE: USERS
     */
    @GetMapping("/by-email-domain/{domain}")
    public ResponseEntity<List<User>> getUsersByEmailDomain(@PathVariable String domain) {
        List<User> users = jpaUserService.getUsersByEmailDomain(domain);
        return ResponseEntity.ok(users);
    }
    
    /**
     * 주문 정보와 함께 사용자 조회
     * FRONTEND_API: GET /api/jpa/users/{id}/with-orders -> API_ENTRY: getUserWithOrders() -> JPA: UserRepository.findByIdWithOrders() -> TABLE: USERS, ORDERS
     */
    @GetMapping("/{id}/with-orders")
    public ResponseEntity<User> getUserWithOrders(@PathVariable Long id) {
        Optional<User> user = jpaUserService.getUserWithOrders(id);
        return user.map(ResponseEntity::ok)
                  .orElse(ResponseEntity.notFound().build());
    }
    
    /**
     * 고액 주문 사용자 조회
     * FRONTEND_API: GET /api/jpa/users/high-value-orders -> API_ENTRY: getUsersWithHighValueOrders() -> JPA: UserRepository.findUsersWithOrdersAboveAmount() -> TABLE: USERS, ORDERS
     */
    @GetMapping("/high-value-orders")
    public ResponseEntity<List<User>> getUsersWithHighValueOrders(@RequestParam BigDecimal minAmount) {
        List<User> users = jpaUserService.getUsersWithHighValueOrders(minAmount);
        return ResponseEntity.ok(users);
    }
    
    // 8. 업데이트 API
    /**
     * 로그인 시간 업데이트
     * FRONTEND_API: PUT /api/jpa/users/{id}/login -> API_ENTRY: updateLastLoginTime() -> JPA: UserRepository.updateLastLoginTime() -> TABLE: USERS
     */
    @PutMapping("/{id}/login")
    public ResponseEntity<Integer> updateLastLoginTime(@PathVariable Long id) {
        int updated = jpaUserService.updateLastLoginTime(id);
        return ResponseEntity.ok(updated);
    }
    
    /**
     * 사용자 활성화
     * FRONTEND_API: PUT /api/jpa/users/{id}/activate -> API_ENTRY: activateUser() -> JPA: UserRepository.save() -> TABLE: USERS
     */
    @PutMapping("/{id}/activate")
    public ResponseEntity<Void> activateUser(@PathVariable Long id) {
        try {
            jpaUserService.activateUser(id);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * 사용자 비활성화
     * FRONTEND_API: PUT /api/jpa/users/{id}/deactivate -> API_ENTRY: deactivateUser() -> JPA: UserRepository.save() -> TABLE: USERS
     */
    @PutMapping("/{id}/deactivate")
    public ResponseEntity<Void> deactivateUser(@PathVariable Long id) {
        try {
            jpaUserService.deactivateUser(id);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * 프리미엄 사용자로 업그레이드
     * FRONTEND_API: PUT /api/jpa/users/{id}/upgrade-premium -> API_ENTRY: upgradeUserToPremium() -> JPA: UserRepository.save() -> TABLE: USERS
     */
    @PutMapping("/{id}/upgrade-premium")
    public ResponseEntity<Void> upgradeUserToPremium(@PathVariable Long id) {
        try {
            jpaUserService.upgradeUserToPremium(id);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    // 9. 검증 API
    /**
     * 사용자명 중복 확인
     * FRONTEND_API: GET /api/jpa/users/check/username/{username} -> API_ENTRY: isUsernameAvailable() -> JPA: UserRepository.existsByUsername() -> TABLE: USERS
     */
    @GetMapping("/check/username/{username}")
    public ResponseEntity<Boolean> checkUsernameAvailability(@PathVariable String username) {
        boolean available = jpaUserService.isUsernameAvailable(username);
        return ResponseEntity.ok(available);
    }
    
    /**
     * 이메일 중복 확인
     * FRONTEND_API: GET /api/jpa/users/check/email/{email} -> API_ENTRY: isEmailAvailable() -> JPA: UserRepository.existsByEmail() -> TABLE: USERS
     */
    @GetMapping("/check/email/{email}")
    public ResponseEntity<Boolean> checkEmailAvailability(@PathVariable String email) {
        boolean available = jpaUserService.isEmailAvailable(email);
        return ResponseEntity.ok(available);
    }
    
    // 10. DTO 프로젝션 API
    /**
     * 사용자 요약 정보 조회
     * FRONTEND_API: GET /api/jpa/users/summaries/by-status/{status} -> API_ENTRY: getUserSummariesByStatus() -> JPA: UserRepository.findUserSummariesByStatus() -> TABLE: USERS
     */
    @GetMapping("/summaries/by-status/{status}")
    public ResponseEntity<List<UserSummaryDto>> getUserSummariesByStatus(@PathVariable UserStatus status) {
        List<UserSummaryDto> summaries = jpaUserService.getUserSummariesByStatus(status);
        return ResponseEntity.ok(summaries);
    }
    
    // 11. 전체 목록 API
    /**
     * 전체 사용자 목록
     * FRONTEND_API: GET /api/jpa/users -> API_ENTRY: getAllUsers() -> JPA: UserRepository.findAll() -> TABLE: USERS
     */
    @GetMapping
    public ResponseEntity<List<User>> getAllUsers() {
        List<User> users = jpaUserService.getAllUsers();
        return ResponseEntity.ok(users);
    }
    
    // 12. 페이징 API
    /**
     * 페이징된 사용자 목록
     * FRONTEND_API: GET /api/jpa/users/paged -> API_ENTRY: getUsersByStatusAndUserType() -> JPA: UserRepository.findByStatusAndUserType() -> TABLE: USERS
     */
    @GetMapping("/paged")
    public ResponseEntity<Page<User>> getPagedUsers(
            @RequestParam(required = false) UserStatus status,
            @RequestParam(required = false) UserType userType,
            Pageable pageable) {
        Page<User> users = jpaUserService.getUsersByStatusAndUserType(status, userType, pageable);
        return ResponseEntity.ok(users);
    }
}
