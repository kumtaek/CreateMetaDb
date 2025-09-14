package com.example.service;

import com.example.mapper.UserMapper;
import com.example.model.User;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.*;
import java.util.stream.Collectors;

@Service
@Transactional
public class UserServiceImpl implements UserService {
    
    @Autowired
    private UserMapper userMapper;
    
    @Override
    public List<User> getUsersByCondition(Map<String, Object> params) {
        // 입력 파라미터 검증 및 정제
        Map<String, Object> validatedParams = validateAndSanitizeParams(params);
        
        // 비즈니스 로직: 사용자 상태별 필터링
        List<User> users = userMapper.selectUsersByCondition(validatedParams);
        
        // 비즈니스 로직: 민감한 정보 마스킹
        return maskSensitiveData(users);
    }
    
    @Override
    public List<User> getUsersByAdvancedCondition(Map<String, Object> params) {
        // 고급 검색 조건 검증
        validateAdvancedSearchParams(params);
        
        // 비즈니스 로직: 나이 범위 검증
        if (params.containsKey("minAge") && params.containsKey("maxAge")) {
            Integer minAge = (Integer) params.get("minAge");
            Integer maxAge = (Integer) params.get("maxAge");
            if (minAge > maxAge) {
                throw new IllegalArgumentException("최소 나이는 최대 나이보다 클 수 없습니다.");
            }
        }
        
        // 비즈니스 로직: 날짜 범위 검증
        validateDateRange(params);
        
        List<User> users = userMapper.selectUsersByAdvancedCondition(params);
        
        // 비즈니스 로직: 사용자 타입별 권한 검증
        return filterByUserPermissions(users);
    }
    
    @Override
    public List<User> getUsersByType(String type) {
        // 사용자 타입 검증
        if (!isValidUserType(type)) {
            throw new IllegalArgumentException("유효하지 않은 사용자 타입입니다: " + type);
        }
        
        List<User> users = userMapper.selectUsersByType(type);
        
        // 비즈니스 로직: 타입별 특별 처리
        return applyTypeSpecificLogic(users, type);
    }
    
    @Override
    public User getUserById(Long id) {
        if (id == null || id <= 0) {
            throw new IllegalArgumentException("유효하지 않은 사용자 ID입니다.");
        }
        
        User user = userMapper.selectUserById(id);
        if (user == null) {
            throw new RuntimeException("사용자를 찾을 수 없습니다. ID: " + id);
        }
        
        // 비즈니스 로직: 마지막 접속 시간 업데이트
        updateLastAccessTime(user);
        
        return user;
    }
    
    @Override
    public int updateUserDynamic(User user) {
        if (user == null || user.getId() == null) {
            throw new IllegalArgumentException("사용자 정보가 올바르지 않습니다.");
        }
        
        // 비즈니스 로직: 이메일 중복 검사
        if (StringUtils.hasText(user.getEmail())) {
            validateEmailUniqueness(user.getEmail(), user.getId());
        }
        
        // 비즈니스 로직: 사용자명 중복 검사
        if (StringUtils.hasText(user.getUsername())) {
            validateUsernameUniqueness(user.getUsername(), user.getId());
        }
        
        // 비즈니스 로직: 비밀번호 암호화
        if (StringUtils.hasText(user.getPassword())) {
            user.setPassword(encryptPassword(user.getPassword()));
        }
        
        // 비즈니스 로직: 업데이트 전 로그 기록
        logUserUpdate(user);
        
        int result = userMapper.updateUserDynamic(user);
        
        // 비즈니스 로직: 업데이트 후 캐시 무효화
        invalidateUserCache(user.getId());
        
        return result;
    }
    
    @Override
    public int deleteUsersByCondition(Map<String, Object> params) {
        // 삭제 조건 검증
        validateDeleteConditions(params);
        
        // 비즈니스 로직: 삭제 전 사용자 수 확인
        int userCount = userMapper.countUsersByCondition(params);
        if (userCount == 0) {
            throw new RuntimeException("삭제할 사용자가 없습니다.");
        }
        
        // 비즈니스 로직: 관리자 계정 삭제 방지
        preventAdminDeletion(params);
        
        // 비즈니스 로직: 삭제 전 로그 기록
        logBulkDelete(params, userCount);
        
        int result = userMapper.deleteUsersByCondition(params);
        
        // 비즈니스 로직: 삭제 후 관련 데이터 정리
        cleanupRelatedData(params);
        
        return result;
    }
    
    // 비즈니스 로직 메서드들
    private Map<String, Object> validateAndSanitizeParams(Map<String, Object> params) {
        Map<String, Object> validated = new HashMap<>();
        
        if (params.containsKey("name")) {
            String name = (String) params.get("name");
            if (StringUtils.hasText(name)) {
                validated.put("name", name.trim().replaceAll("[<>\"']", ""));
            }
        }
        
        if (params.containsKey("email")) {
            String email = (String) params.get("email");
            if (StringUtils.hasText(email) && isValidEmail(email)) {
                validated.put("email", email.toLowerCase().trim());
            }
        }
        
        if (params.containsKey("status")) {
            String status = (String) params.get("status");
            if (isValidStatus(status)) {
                validated.put("status", status.toUpperCase());
            }
        }
        
        return validated;
    }
    
    private List<User> maskSensitiveData(List<User> users) {
        return users.stream().map(user -> {
            User maskedUser = new User();
            maskedUser.setId(user.getId());
            maskedUser.setUsername(user.getUsername());
            maskedUser.setEmail(maskEmail(user.getEmail()));
            maskedUser.setName(user.getName());
            maskedUser.setAge(user.getAge());
            maskedUser.setStatus(user.getStatus());
            maskedUser.setUserType(user.getUserType());
            maskedUser.setPhone(maskPhone(user.getPhone()));
            maskedUser.setAddress(user.getAddress());
            maskedUser.setCreatedDate(user.getCreatedDate());
            maskedUser.setUpdatedDate(user.getUpdatedDate());
            return maskedUser;
        }).collect(Collectors.toList());
    }
    
    private void validateAdvancedSearchParams(Map<String, Object> params) {
        if (params.containsKey("minAge")) {
            Integer minAge = (Integer) params.get("minAge");
            if (minAge < 0 || minAge > 150) {
                throw new IllegalArgumentException("나이는 0-150 사이여야 합니다.");
            }
        }
        
        if (params.containsKey("maxAge")) {
            Integer maxAge = (Integer) params.get("maxAge");
            if (maxAge < 0 || maxAge > 150) {
                throw new IllegalArgumentException("나이는 0-150 사이여야 합니다.");
            }
        }
    }
    
    private void validateDateRange(Map<String, Object> params) {
        if (params.containsKey("startDate") && params.containsKey("endDate")) {
            String startDate = (String) params.get("startDate");
            String endDate = (String) params.get("endDate");
            
            try {
                Date start = new Date(startDate);
                Date end = new Date(endDate);
                if (start.after(end)) {
                    throw new IllegalArgumentException("시작일은 종료일보다 늦을 수 없습니다.");
                }
            } catch (Exception e) {
                throw new IllegalArgumentException("날짜 형식이 올바르지 않습니다.");
            }
        }
    }
    
    private List<User> filterByUserPermissions(List<User> users) {
        // 비즈니스 로직: 사용자 권한에 따른 필터링
        return users.stream()
                .filter(user -> !"DELETED".equals(user.getStatus()))
                .filter(user -> user.getCreatedDate() != null)
                .collect(Collectors.toList());
    }
    
    private boolean isValidUserType(String type) {
        return Arrays.asList("NORMAL", "PREMIUM", "ADMIN", "GUEST").contains(type.toUpperCase());
    }
    
    private List<User> applyTypeSpecificLogic(List<User> users, String type) {
        switch (type.toUpperCase()) {
            case "ADMIN":
                return users.stream()
                        .filter(user -> "ACTIVE".equals(user.getStatus()))
                        .collect(Collectors.toList());
            case "PREMIUM":
                return users.stream()
                        .filter(user -> user.getAge() != null && user.getAge() >= 18)
                        .collect(Collectors.toList());
            default:
                return users;
        }
    }
    
    private void updateLastAccessTime(User user) {
        // 비즈니스 로직: 마지막 접속 시간 업데이트
        user.setUpdatedDate(new Date());
        // 실제로는 별도 테이블에 접속 로그를 기록할 수 있음
    }
    
    private void validateEmailUniqueness(String email, Long userId) {
        // 비즈니스 로직: 이메일 중복 검사
        Map<String, Object> params = new HashMap<>();
        params.put("email", email);
        List<User> existingUsers = userMapper.selectUsersByCondition(params);
        
        boolean isDuplicate = existingUsers.stream()
                .anyMatch(user -> !user.getId().equals(userId));
        
        if (isDuplicate) {
            throw new RuntimeException("이미 사용 중인 이메일입니다: " + email);
        }
    }
    
    private void validateUsernameUniqueness(String username, Long userId) {
        // 비즈니스 로직: 사용자명 중복 검사
        Map<String, Object> params = new HashMap<>();
        params.put("username", username);
        List<User> existingUsers = userMapper.selectUsersByCondition(params);
        
        boolean isDuplicate = existingUsers.stream()
                .anyMatch(user -> !user.getId().equals(userId));
        
        if (isDuplicate) {
            throw new RuntimeException("이미 사용 중인 사용자명입니다: " + username);
        }
    }
    
    private String encryptPassword(String password) {
        // 비즈니스 로직: 비밀번호 암호화 (실제로는 BCrypt 등 사용)
        return "ENCRYPTED_" + password.hashCode();
    }
    
    private void logUserUpdate(User user) {
        // 비즈니스 로직: 사용자 업데이트 로그
        System.out.println("User updated: ID=" + user.getId() + ", Time=" + new Date());
    }
    
    private void invalidateUserCache(Long userId) {
        // 비즈니스 로직: 사용자 캐시 무효화
        System.out.println("Cache invalidated for user: " + userId);
    }
    
    private void validateDeleteConditions(Map<String, Object> params) {
        if (params.isEmpty()) {
            throw new IllegalArgumentException("삭제 조건이 없습니다.");
        }
    }
    
    private void preventAdminDeletion(Map<String, Object> params) {
        if ("ADMIN".equals(params.get("userType"))) {
            throw new RuntimeException("관리자 계정은 삭제할 수 없습니다.");
        }
    }
    
    private void logBulkDelete(Map<String, Object> params, int userCount) {
        System.out.println("Bulk delete initiated: " + params + ", Count: " + userCount);
    }
    
    private void cleanupRelatedData(Map<String, Object> params) {
        // 비즈니스 로직: 관련 데이터 정리 (세션, 로그 등)
        System.out.println("Related data cleanup completed for: " + params);
    }
    
    private boolean isValidEmail(String email) {
        return email != null && email.contains("@") && email.contains(".");
    }
    
    private boolean isValidStatus(String status) {
        return Arrays.asList("ACTIVE", "INACTIVE", "SUSPENDED", "DELETED").contains(status.toUpperCase());
    }
    
    private String maskEmail(String email) {
        if (email == null || !email.contains("@")) return email;
        String[] parts = email.split("@");
        if (parts[0].length() <= 2) return email;
        return parts[0].substring(0, 2) + "***@" + parts[1];
    }
    
    private String maskPhone(String phone) {
        if (phone == null || phone.length() <= 4) return phone;
        return phone.substring(0, phone.length() - 4) + "****";
    }
}