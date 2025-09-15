package com.example.service;

import com.example.dao.UserDao;
import com.example.model.User;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.Date;

/**
 * 사용자 관리 Service 계층
 * Servlet과 DAO 사이의 비즈니스 로직을 처리
 */
public class UserService {
    
    private UserDao userDao;
    
    public UserService() {
        this.userDao = new UserDao();
    }
    
    /**
     * 조건에 따른 사용자 목록 조회
     */
    public List<User> getUsersByCondition(Map<String, Object> params) {
        try {
            // 비즈니스 로직: 검색 조건 검증
            validateSearchParams(params);
            
            // DAO를 통한 데이터 조회
            List<User> users = userDao.findUsersByCondition(params);
            
            // 비즈니스 로직: 사용자 데이터 가공
            processUserData(users);
            
            return users;
            
        } catch (Exception e) {
            System.err.println("사용자 조회 중 오류 발생: " + e.getMessage());
            throw new RuntimeException("사용자 조회 실패", e);
        }
    }
    
    /**
     * 고급 조건으로 사용자 조회
     */
    public List<User> getUsersByAdvancedCondition(Map<String, Object> params) {
        try {
            // 복잡한 비즈니스 로직: 고급 검색 조건 처리
            Map<String, Object> processedParams = processAdvancedSearchParams(params);
            
            // DAO를 통한 데이터 조회
            List<User> users = userDao.findUsersByAdvancedCondition(processedParams);
            
            // 비즈니스 로직: 사용자 데이터 보강
            enrichUserData(users);
            
            return users;
            
        } catch (Exception e) {
            System.err.println("고급 사용자 조회 중 오류 발생: " + e.getMessage());
            throw new RuntimeException("고급 사용자 조회 실패", e);
        }
    }
    
    /**
     * 사용자 타입별 조회
     */
    public List<User> getUsersByType(String userType) {
        try {
            // 비즈니스 로직: 사용자 타입 검증
            if (!isValidUserType(userType)) {
                throw new IllegalArgumentException("유효하지 않은 사용자 타입: " + userType);
            }
            
            List<User> users = userDao.findUsersByType(userType);
            
            // 타입별 특별 처리
            processUserTypeSpecific(users, userType);
            
            return users;
            
        } catch (Exception e) {
            System.err.println("타입별 사용자 조회 중 오류 발생: " + e.getMessage());
            throw new RuntimeException("타입별 사용자 조회 실패", e);
        }
    }
    
    /**
     * 사용자 생성
     */
    public User createUser(Map<String, Object> userData) {
        try {
            // 비즈니스 로직: 사용자 데이터 검증
            validateUserData(userData);
            
            // 비즈니스 로직: 중복 검사
            checkUserDuplication(userData);
            
            // 비즈니스 로직: 사용자 데이터 전처리
            Map<String, Object> processedData = processUserCreationData(userData);
            
            // DAO를 통한 사용자 생성
            User newUser = userDao.createUser(processedData);
            
            // 비즈니스 로직: 생성 후 처리
            postCreateUserProcessing(newUser);
            
            return newUser;
            
        } catch (Exception e) {
            System.err.println("사용자 생성 중 오류 발생: " + e.getMessage());
            throw new RuntimeException("사용자 생성 실패", e);
        }
    }
    
    /**
     * 사용자 통계 정보 조회
     */
    public Map<String, Object> getUserStatistics() {
        try {
            Map<String, Object> stats = new HashMap<>();
            
            // DAO를 통한 통계 데이터 조회
            stats.put("totalUsers", userDao.getTotalUserCount());
            stats.put("activeUsers", userDao.getActiveUserCount());
            stats.put("newUsersToday", userDao.getNewUsersTodayCount());
            stats.put("premiumUsers", userDao.getPremiumUserCount());
            
            // 비즈니스 로직: 통계 데이터 가공
            processStatisticsData(stats);
            
            return stats;
            
        } catch (Exception e) {
            System.err.println("사용자 통계 조회 중 오류 발생: " + e.getMessage());
            throw new RuntimeException("사용자 통계 조회 실패", e);
        }
    }
    
    // 비즈니스 로직 메서드들
    
    private void validateSearchParams(Map<String, Object> params) {
        if (params == null) {
            throw new IllegalArgumentException("검색 파라미터가 null입니다.");
        }
        
        String searchKeyword = (String) params.get("searchKeyword");
        if (searchKeyword != null && searchKeyword.length() > 100) {
            throw new IllegalArgumentException("검색어는 100자를 초과할 수 없습니다.");
        }
    }
    
    private void processUserData(List<User> users) {
        if (users == null) return;
        
        for (User user : users) {
            // 이메일 마스킹 처리
            if (user.getEmail() != null && user.getEmail().contains("@")) {
                String[] parts = user.getEmail().split("@");
                if (parts[0].length() > 2) {
                    String maskedEmail = parts[0].substring(0, 2) + "***@" + parts[1];
                    user.setMaskedEmail(maskedEmail);
                }
            }
            
            // 전화번호 마스킹 처리
            if (user.getPhone() != null && user.getPhone().length() > 4) {
                String maskedPhone = user.getPhone().substring(0, 3) + "****" + user.getPhone().substring(user.getPhone().length() - 4);
                user.setMaskedPhone(maskedPhone);
            }
            
            // 사용자 타입 표시명 설정
            user.setUserTypeDisplayName(getUserTypeDisplayName(user.getUserType()));
            
            // 상태 표시명 설정
            user.setStatusDisplayName(getStatusDisplayName(user.getStatus()));
            
            // 계정 나이 계산
            if (user.getCreatedDate() != null) {
                long accountAgeInDays = (System.currentTimeMillis() - user.getCreatedDate().getTime()) / (1000 * 60 * 60 * 24);
                user.setAccountAgeInDays((int) accountAgeInDays);
            }
        }
    }
    
    private Map<String, Object> processAdvancedSearchParams(Map<String, Object> params) {
        Map<String, Object> processedParams = new HashMap<>(params);
        
        // 날짜 범위 처리
        if (processedParams.containsKey("startDate") && processedParams.containsKey("endDate")) {
            // 날짜 형식 검증 및 변환
            validateDateFormat((String) processedParams.get("startDate"));
            validateDateFormat((String) processedParams.get("endDate"));
        }
        
        // 나이 범위 처리
        if (processedParams.containsKey("minAge") && processedParams.containsKey("maxAge")) {
            int minAge = (Integer) processedParams.get("minAge");
            int maxAge = (Integer) processedParams.get("maxAge");
            
            if (minAge > maxAge) {
                throw new IllegalArgumentException("최소 나이는 최대 나이보다 클 수 없습니다.");
            }
        }
        
        return processedParams;
    }
    
    private void enrichUserData(List<User> users) {
        for (User user : users) {
            // 추가 정보 조회 및 설정
            user.setHasValidEmail(userDao.isEmailVerified(user.getUserId()));
            user.setHasValidPhone(userDao.isPhoneVerified(user.getUserId()));
            
            // 마지막 업데이트 정보
            if (user.getLastLoginDate() != null) {
                long hoursSinceLogin = (System.currentTimeMillis() - user.getLastLoginDate().getTime()) / (1000 * 60 * 60);
                if (hoursSinceLogin < 24) {
                    user.setLastUpdateInfo(hoursSinceLogin + "시간 전 로그인");
                } else {
                    user.setLastUpdateInfo((hoursSinceLogin / 24) + "일 전 로그인");
                }
            } else {
                user.setLastUpdateInfo("로그인 기록 없음");
            }
        }
    }
    
    private boolean isValidUserType(String userType) {
        return userType != null && 
               (userType.equals("NORMAL") || userType.equals("PREMIUM") || 
                userType.equals("ADMIN") || userType.equals("GUEST"));
    }
    
    private void processUserTypeSpecific(List<User> users, String userType) {
        for (User user : users) {
            switch (userType) {
                case "PREMIUM":
                    user.setIsPremium(true);
                    break;
                case "ADMIN":
                    user.setIsAdmin(true);
                    break;
                case "GUEST":
                    user.setIsGuest(true);
                    break;
                default:
                    user.setIsNormal(true);
                    break;
            }
        }
    }
    
    private void validateUserData(Map<String, Object> userData) {
        if (userData == null) {
            throw new IllegalArgumentException("사용자 데이터가 null입니다.");
        }
        
        String username = (String) userData.get("username");
        if (username == null || username.trim().isEmpty()) {
            throw new IllegalArgumentException("사용자명은 필수입니다.");
        }
        
        String email = (String) userData.get("email");
        if (email == null || !email.contains("@")) {
            throw new IllegalArgumentException("유효한 이메일 주소를 입력해주세요.");
        }
    }
    
    private void checkUserDuplication(Map<String, Object> userData) {
        String username = (String) userData.get("username");
        String email = (String) userData.get("email");
        
        if (userDao.existsByUsername(username)) {
            throw new RuntimeException("이미 존재하는 사용자명입니다: " + username);
        }
        
        if (userDao.existsByEmail(email)) {
            throw new RuntimeException("이미 존재하는 이메일입니다: " + email);
        }
    }
    
    private Map<String, Object> processUserCreationData(Map<String, Object> userData) {
        Map<String, Object> processedData = new HashMap<>(userData);
        
        // 기본값 설정
        processedData.put("status", "ACTIVE");
        processedData.put("createdDate", new Date());
        processedData.put("userType", "NORMAL");
        
        // 비밀번호 해싱 (실제로는 BCrypt 등 사용)
        String password = (String) processedData.get("password");
        if (password != null) {
            processedData.put("password", hashPassword(password));
        }
        
        return processedData;
    }
    
    private void postCreateUserProcessing(User newUser) {
        // 사용자 생성 후 처리 로직
        System.out.println("새 사용자 생성 완료: " + newUser.getUsername());
    }
    
    private void processStatisticsData(Map<String, Object> stats) {
        // 통계 데이터 가공
        Integer totalUsers = (Integer) stats.get("totalUsers");
        Integer activeUsers = (Integer) stats.get("activeUsers");
        
        if (totalUsers != null && totalUsers > 0 && activeUsers != null) {
            double activeRate = (double) activeUsers / totalUsers * 100;
            stats.put("activeRate", Math.round(activeRate * 100.0) / 100.0);
        }
    }
    
    // 유틸리티 메서드들
    
    private String getUserTypeDisplayName(String userType) {
        switch (userType) {
            case "NORMAL": return "일반";
            case "PREMIUM": return "프리미엄";
            case "ADMIN": return "관리자";
            case "GUEST": return "게스트";
            default: return userType;
        }
    }
    
    private String getStatusDisplayName(String status) {
        switch (status) {
            case "ACTIVE": return "활성";
            case "INACTIVE": return "비활성";
            case "PENDING": return "대기";
            case "SUSPENDED": return "정지";
            default: return status;
        }
    }
    
    private void validateDateFormat(String dateStr) {
        try {
            java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("yyyy-MM-dd");
            sdf.setLenient(false);
            sdf.parse(dateStr);
        } catch (Exception e) {
            throw new IllegalArgumentException("잘못된 날짜 형식입니다: " + dateStr);
        }
    }
    
    private String hashPassword(String password) {
        // 실제로는 BCrypt 등 안전한 해싱 알고리즘 사용
        return "hashed_" + password.hashCode();
    }
}