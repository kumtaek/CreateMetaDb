package com.example.jpa.service;

import com.example.jpa.entity.User;
import com.example.jpa.entity.UserStatus;
import com.example.jpa.entity.UserType;
import com.example.jpa.repository.UserRepository;
import com.example.jpa.dto.UserSummaryDto;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * JPA 기반 User Service
 * UserRepository를 활용한 사용자 관리 서비스
 */
@Service
@Transactional
public class JpaUserService {
    
    @Autowired
    private UserRepository userRepository;
    
    // 1. 기본 CRUD 작업
    public User createUser(User user) {
        // 중복 체크
        if (userRepository.existsByUsername(user.getUsername())) {
            throw new RuntimeException("Username already exists: " + user.getUsername());
        }
        if (userRepository.existsByEmail(user.getEmail())) {
            throw new RuntimeException("Email already exists: " + user.getEmail());
        }
        
        return userRepository.save(user);
    }
    
    @Transactional(readOnly = true)
    public Optional<User> getUserById(Long userId) {
        return userRepository.findById(userId);
    }
    
    @Transactional(readOnly = true)
    public Optional<User> getUserByUsername(String username) {
        return userRepository.findByUsername(username);
    }
    
    @Transactional(readOnly = true)
    public Optional<User> getUserByEmail(String email) {
        return userRepository.findByEmail(email);
    }
    
    public User updateUser(User user) {
        // 존재 여부 확인
        if (!userRepository.existsById(user.getUserId())) {
            throw new RuntimeException("User not found: " + user.getUserId());
        }
        
        // 중복 체크 (자기 자신 제외)
        if (userRepository.existsByUsernameAndUserIdNot(user.getUsername(), user.getUserId())) {
            throw new RuntimeException("Username already exists: " + user.getUsername());
        }
        
        return userRepository.save(user);
    }
    
    public void deleteUser(Long userId) {
        if (!userRepository.existsById(userId)) {
            throw new RuntimeException("User not found: " + userId);
        }
        userRepository.deleteById(userId);
    }
    
    // 2. 검색 기능
    @Transactional(readOnly = true)
    public List<User> getUsersByStatus(UserStatus status) {
        return userRepository.findByStatus(status);
    }
    
    @Transactional(readOnly = true)
    public List<User> getUsersByUserType(UserType userType) {
        return userRepository.findByUserType(userType);
    }
    
    @Transactional(readOnly = true)
    public List<User> searchUsersByUsername(String username) {
        return userRepository.findByUsernameContaining(username);
    }
    
    @Transactional(readOnly = true)
    public List<User> searchUsersByEmail(String email) {
        return userRepository.findByEmailContaining(email);
    }
    
    @Transactional(readOnly = true)
    public List<User> searchUsersByFullName(String fullName) {
        return userRepository.findByFullNameContainingIgnoreCase(fullName);
    }
    
    // 3. 동적 검색
    @Transactional(readOnly = true)
    public Page<User> searchUsers(String username, String email, UserStatus status, 
                                 UserType userType, Pageable pageable) {
        return userRepository.findUsersByDynamicCriteria(username, email, status, userType, pageable);
    }
    
    // 4. 날짜 기반 검색
    @Transactional(readOnly = true)
    public List<User> getUsersCreatedBetween(LocalDateTime startDate, LocalDateTime endDate) {
        return userRepository.findByCreatedAtBetween(startDate, endDate);
    }
    
    @Transactional(readOnly = true)
    public List<User> getUsersCreatedAfter(LocalDateTime date) {
        return userRepository.findByCreatedAtAfter(date);
    }
    
    @Transactional(readOnly = true)
    public List<User> getUsersWithoutLogin() {
        return userRepository.findByLastLoginAtIsNull();
    }
    
    @Transactional(readOnly = true)
    public List<User> getActiveUsersFromDate(LocalDateTime fromDate) {
        return userRepository.findActiveUsersFromDate(UserStatus.ACTIVE, fromDate);
    }
    
    // 5. 통계 기능
    @Transactional(readOnly = true)
    public long getUserCountByStatus(UserStatus status) {
        return userRepository.countByStatus(status);
    }
    
    @Transactional(readOnly = true)
    public long getUserCountByUserType(UserType userType) {
        return userRepository.countByUserType(userType);
    }
    
    @Transactional(readOnly = true)
    public long getNewUserCountAfter(LocalDateTime date) {
        return userRepository.countByCreatedAtAfter(date);
    }
    
    @Transactional(readOnly = true)
    public List<Object[]> getUserTypeStatistics() {
        return userRepository.getUserTypeStatistics();
    }
    
    @Transactional(readOnly = true)
    public List<Object[]> getUserStatusStatistics(LocalDateTime fromDate) {
        return userRepository.getUserStatusStatistics(fromDate);
    }
    
    // 6. 특수 검색
    @Transactional(readOnly = true)
    public List<User> getUsersByEmailDomain(String domain) {
        return userRepository.findByEmailDomain(domain);
    }
    
    @Transactional(readOnly = true)
    public Optional<User> getUserWithOrders(Long userId) {
        return userRepository.findByIdWithOrders(userId);
    }
    
    @Transactional(readOnly = true)
    public List<User> getUsersWithProfile(UserStatus status) {
        return userRepository.findByStatusWithProfile(status);
    }
    
    // 7. 업데이트 작업
    public int updateLastLoginTime(Long userId) {
        return userRepository.updateLastLoginTime(userId, LocalDateTime.now());
    }
    
    public int updateUserStatusByDateAndStatus(UserStatus newStatus, UserStatus oldStatus, LocalDateTime beforeDate) {
        return userRepository.updateUserStatusByDateAndStatus(newStatus, oldStatus, beforeDate);
    }
    
    // 8. 주문 관련 사용자 검색
    @Transactional(readOnly = true)
    public List<User> getUsersWithOrdersAfterDate(LocalDateTime fromDate) {
        return userRepository.findUsersWithOrdersAfterDate(fromDate);
    }
    
    @Transactional(readOnly = true)
    public List<User> getUsersWithoutCompletedOrders() {
        return userRepository.findUsersWithoutCompletedOrders();
    }
    
    @Transactional(readOnly = true)
    public List<User> getUsersWithHighValueOrders(java.math.BigDecimal minAmount) {
        return userRepository.findUsersWithOrdersAboveAmount(minAmount);
    }
    
    // 9. DTO 프로젝션
    @Transactional(readOnly = true)
    public List<UserSummaryDto> getUserSummariesByStatus(UserStatus status) {
        return userRepository.findUserSummariesByStatus(status);
    }
    
    // 10. 비즈니스 로직
    public void activateUser(Long userId) {
        Optional<User> userOpt = userRepository.findById(userId);
        if (userOpt.isPresent()) {
            User user = userOpt.get();
            user.setStatus(UserStatus.ACTIVE);
            userRepository.save(user);
        } else {
            throw new RuntimeException("User not found: " + userId);
        }
    }
    
    public void deactivateUser(Long userId) {
        Optional<User> userOpt = userRepository.findById(userId);
        if (userOpt.isPresent()) {
            User user = userOpt.get();
            user.setStatus(UserStatus.INACTIVE);
            userRepository.save(user);
        } else {
            throw new RuntimeException("User not found: " + userId);
        }
    }
    
    public void upgradeUserToPremium(Long userId) {
        Optional<User> userOpt = userRepository.findById(userId);
        if (userOpt.isPresent()) {
            User user = userOpt.get();
            user.setUserType(UserType.PREMIUM);
            userRepository.save(user);
        } else {
            throw new RuntimeException("User not found: " + userId);
        }
    }
    
    // 11. 검증 메서드
    @Transactional(readOnly = true)
    public boolean isUsernameAvailable(String username) {
        return !userRepository.existsByUsername(username);
    }
    
    @Transactional(readOnly = true)
    public boolean isEmailAvailable(String email) {
        return !userRepository.existsByEmail(email);
    }
    
    @Transactional(readOnly = true)
    public boolean isUsernameAvailableForUpdate(String username, Long userId) {
        return !userRepository.existsByUsernameAndUserIdNot(username, userId);
    }
    
    // 12. 대량 작업
    public void deleteInactiveUsers() {
        userRepository.deleteByStatus(UserStatus.INACTIVE);
    }
    
    public long deleteOldUsers(LocalDateTime beforeDate) {
        return userRepository.deleteByCreatedAtBefore(beforeDate);
    }
    
    // 13. 페이징 검색
    @Transactional(readOnly = true)
    public Page<User> getUsersByStatusAndUserType(UserStatus status, UserType userType, Pageable pageable) {
        return userRepository.findByStatusAndUserType(status, userType, pageable);
    }
    
    @Transactional(readOnly = true)
    public List<User> getAllUsers() {
        return userRepository.findAll();
    }
}

