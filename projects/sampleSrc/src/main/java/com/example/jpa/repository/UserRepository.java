package com.example.jpa.repository;

import com.example.jpa.entity.User;
import com.example.jpa.entity.UserStatus;
import com.example.jpa.entity.UserType;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * JPA User Repository
 * 다양한 JPA 쿼리 메서드 패턴을 포함한 테스트케이스
 */
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    
    // 1. 기본 메서드명 기반 쿼리 (Method Query Creation)
    Optional<User> findByUsername(String username);
    
    Optional<User> findByEmail(String email);
    
    List<User> findByStatus(UserStatus status);
    
    List<User> findByUserType(UserType userType);
    
    List<User> findByStatusAndUserType(UserStatus status, UserType userType);
    
    // 2. Like 검색 쿼리
    List<User> findByUsernameContaining(String username);
    
    List<User> findByEmailContaining(String email);
    
    List<User> findByFullNameContainingIgnoreCase(String fullName);
    
    // 3. 날짜 범위 검색
    List<User> findByCreatedAtBetween(LocalDateTime startDate, LocalDateTime endDate);
    
    List<User> findByCreatedAtAfter(LocalDateTime date);
    
    List<User> findByLastLoginAtIsNull();
    
    List<User> findByLastLoginAtIsNotNull();
    
    // 4. 정렬과 페이징
    List<User> findByStatusOrderByCreatedAtDesc(UserStatus status);
    
    Page<User> findByStatusAndUserType(UserStatus status, UserType userType, Pageable pageable);
    
    // 5. Count 쿼리
    long countByStatus(UserStatus status);
    
    long countByUserType(UserType userType);
    
    long countByCreatedAtAfter(LocalDateTime date);
    
    // 6. Exists 쿼리
    boolean existsByUsername(String username);
    
    boolean existsByEmail(String email);
    
    boolean existsByUsernameAndUserIdNot(String username, Long userId);
    
    // 7. Delete 쿼리
    void deleteByStatus(UserStatus status);
    
    long deleteByCreatedAtBefore(LocalDateTime date);
    
    // 8. @Query 어노테이션 - JPQL 쿼리
    @Query("SELECT u FROM User u WHERE u.status = :status AND u.createdAt >= :fromDate")
    List<User> findActiveUsersFromDate(@Param("status") UserStatus status, 
                                      @Param("fromDate") LocalDateTime fromDate);
    
    @Query("SELECT u FROM User u WHERE u.email LIKE %:domain%")
    List<User> findByEmailDomain(@Param("domain") String domain);
    
    @Query("SELECT u FROM User u LEFT JOIN FETCH u.orders WHERE u.userId = :userId")
    Optional<User> findByIdWithOrders(@Param("userId") Long userId);
    
    @Query("SELECT u FROM User u LEFT JOIN FETCH u.userProfile WHERE u.status = :status")
    List<User> findByStatusWithProfile(@Param("status") UserStatus status);
    
    // 9. @Query 어노테이션 - Native SQL 쿼리
    @Query(value = "SELECT * FROM USERS u WHERE u.USER_TYPE = ?1 AND u.CREATED_AT > ?2", 
           nativeQuery = true)
    List<User> findByUserTypeAndCreatedAtAfterNative(String userType, LocalDateTime createdAt);
    
    @Query(value = "SELECT COUNT(*) FROM USERS WHERE STATUS = :status", nativeQuery = true)
    long countUsersByStatusNative(@Param("status") String status);
    
    // 10. 복잡한 JPQL 쿼리 - 집계 함수
    @Query("SELECT u.userType, COUNT(u) FROM User u GROUP BY u.userType")
    List<Object[]> getUserTypeStatistics();
    
    @Query("SELECT u.status, COUNT(u) FROM User u WHERE u.createdAt >= :fromDate GROUP BY u.status")
    List<Object[]> getUserStatusStatistics(@Param("fromDate") LocalDateTime fromDate);
    
    // 11. @Modifying 어노테이션 - 업데이트 쿼리
    @Modifying
    @Query("UPDATE User u SET u.lastLoginAt = :loginTime WHERE u.userId = :userId")
    int updateLastLoginTime(@Param("userId") Long userId, @Param("loginTime") LocalDateTime loginTime);
    
    @Modifying
    @Query("UPDATE User u SET u.status = :newStatus WHERE u.status = :oldStatus AND u.createdAt < :beforeDate")
    int updateUserStatusByDateAndStatus(@Param("newStatus") UserStatus newStatus, 
                                       @Param("oldStatus") UserStatus oldStatus, 
                                       @Param("beforeDate") LocalDateTime beforeDate);
    
    // 12. 서브쿼리를 포함한 복잡한 쿼리
    @Query("SELECT u FROM User u WHERE u.userId IN " +
           "(SELECT o.user.userId FROM Order o WHERE o.orderDate >= :fromDate)")
    List<User> findUsersWithOrdersAfterDate(@Param("fromDate") LocalDateTime fromDate);
    
    @Query("SELECT u FROM User u WHERE u.userId NOT IN " +
           "(SELECT o.user.userId FROM Order o WHERE o.orderStatus = 'COMPLETED')")
    List<User> findUsersWithoutCompletedOrders();
    
    // 13. 동적 쿼리를 위한 메서드
    @Query("SELECT u FROM User u WHERE " +
           "(:username IS NULL OR u.username LIKE %:username%) AND " +
           "(:email IS NULL OR u.email LIKE %:email%) AND " +
           "(:status IS NULL OR u.status = :status) AND " +
           "(:userType IS NULL OR u.userType = :userType)")
    Page<User> findUsersByDynamicCriteria(@Param("username") String username,
                                         @Param("email") String email,
                                         @Param("status") UserStatus status,
                                         @Param("userType") UserType userType,
                                         Pageable pageable);
    
    // 14. 연관관계 조인 쿼리
    @Query("SELECT u FROM User u JOIN u.orders o WHERE o.totalAmount > :minAmount")
    List<User> findUsersWithOrdersAboveAmount(@Param("minAmount") java.math.BigDecimal minAmount);
    
    @Query("SELECT DISTINCT u FROM User u LEFT JOIN u.userProfile p WHERE p.city = :city OR p.city IS NULL")
    List<User> findUsersByCityOrNoProfile(@Param("city") String city);
    
    // 15. DTO 프로젝션 쿼리
    @Query("SELECT new com.example.jpa.dto.UserSummaryDto(u.userId, u.username, u.email, u.status) " +
           "FROM User u WHERE u.status = :status")
    List<com.example.jpa.dto.UserSummaryDto> findUserSummariesByStatus(@Param("status") UserStatus status);
}

