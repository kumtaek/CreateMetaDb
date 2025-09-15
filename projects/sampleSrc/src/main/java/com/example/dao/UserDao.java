package com.example.dao;

import com.example.model.User;
import java.util.List;
import java.util.Map;
import java.util.ArrayList;
import java.util.Date;
import java.util.Random;

/**
 * 사용자 데이터 액세스 객체 (DAO)
 * MyBatis를 통한 데이터베이스 접근과 직접 쿼리 조합을 모두 지원
 */
public class UserDao {
    
    private static final String USER_MAPPER_NAMESPACE = "com.example.mapper.UserMapper";
    
    // MyBatis SqlSession (실제로는 의존성 주입으로 받아야 함)
    // private SqlSession sqlSession;
    
    public UserDao() {
        // 실제로는 SqlSession을 의존성 주입으로 받음
        // this.sqlSession = sqlSession;
    }
    
    /**
     * 조건에 따른 사용자 목록 조회 (MyBatis 사용)
     */
    public List<User> findUsersByCondition(Map<String, Object> params) {
        try {
            // MyBatis를 통한 조회
            // return sqlSession.selectList(USER_MAPPER_NAMESPACE + ".findUsersByCondition", params);
            
            // 임시 샘플 데이터 생성 (실제로는 MyBatis 결과)
            return generateSampleUsers(params);
            
        } catch (Exception e) {
            System.err.println("사용자 조건 조회 중 오류: " + e.getMessage());
            throw new RuntimeException("사용자 조회 실패", e);
        }
    }
    
    /**
     * 고급 조건으로 사용자 조회 (MyBatis 사용)
     */
    public List<User> findUsersByAdvancedCondition(Map<String, Object> params) {
        try {
            // MyBatis를 통한 고급 조회
            // return sqlSession.selectList(USER_MAPPER_NAMESPACE + ".findUsersByAdvancedCondition", params);
            
            // 임시 샘플 데이터 생성
            return generateAdvancedSampleUsers(params);
            
        } catch (Exception e) {
            System.err.println("고급 사용자 조회 중 오류: " + e.getMessage());
            throw new RuntimeException("고급 사용자 조회 실패", e);
        }
    }
    
    /**
     * 사용자 타입별 조회 (MyBatis 사용)
     */
    public List<User> findUsersByType(String userType) {
        try {
            // MyBatis를 통한 타입별 조회
            // return sqlSession.selectList(USER_MAPPER_NAMESPACE + ".findUsersByType", userType);
            
            // 임시 샘플 데이터 생성
            return generateUsersByType(userType);
            
        } catch (Exception e) {
            System.err.println("타입별 사용자 조회 중 오류: " + e.getMessage());
            throw new RuntimeException("타입별 사용자 조회 실패", e);
        }
    }
    
    /**
     * 사용자 ID로 조회 (MyBatis 사용)
     */
    public User findUserById(String userId) {
        try {
            // MyBatis를 통한 단일 사용자 조회
            // return sqlSession.selectOne(USER_MAPPER_NAMESPACE + ".findUserById", userId);
            
            // 임시 샘플 데이터 생성
            return generateUserById(userId);
            
        } catch (Exception e) {
            System.err.println("사용자 ID 조회 중 오류: " + e.getMessage());
            throw new RuntimeException("사용자 ID 조회 실패", e);
        }
    }
    
    /**
     * 사용자 생성 (MyBatis 사용)
     */
    public User createUser(Map<String, Object> userData) {
        try {
            // MyBatis를 통한 사용자 생성
            // int result = sqlSession.insert(USER_MAPPER_NAMESPACE + ".createUser", userData);
            // if (result > 0) {
            //     return findUserById((String) userData.get("userId"));
            // }
            
            // 임시 샘플 사용자 생성
            return generateNewUser(userData);
            
        } catch (Exception e) {
            System.err.println("사용자 생성 중 오류: " + e.getMessage());
            throw new RuntimeException("사용자 생성 실패", e);
        }
    }
    
    /**
     * 사용자 정보 수정 (MyBatis 사용)
     */
    public User updateUser(String userId, Map<String, Object> updateData) {
        try {
            // MyBatis를 통한 사용자 수정
            // updateData.put("userId", userId);
            // int result = sqlSession.update(USER_MAPPER_NAMESPACE + ".updateUser", updateData);
            // if (result > 0) {
            //     return findUserById(userId);
            // }
            
            // 임시 샘플 사용자 수정
            return generateUpdatedUser(userId, updateData);
            
        } catch (Exception e) {
            System.err.println("사용자 수정 중 오류: " + e.getMessage());
            throw new RuntimeException("사용자 수정 실패", e);
        }
    }
    
    /**
     * 사용자 삭제 (MyBatis 사용)
     */
    public boolean deleteUser(String userId) {
        try {
            // MyBatis를 통한 사용자 삭제
            // int result = sqlSession.delete(USER_MAPPER_NAMESPACE + ".deleteUser", userId);
            // return result > 0;
            
            // 임시 샘플 삭제 처리
            System.out.println("사용자 삭제 처리: " + userId);
            return true;
            
        } catch (Exception e) {
            System.err.println("사용자 삭제 중 오류: " + e.getMessage());
            throw new RuntimeException("사용자 삭제 실패", e);
        }
    }
    
    /**
     * 사용자명 중복 확인 (MyBatis 사용)
     */
    public boolean existsByUsername(String username) {
        try {
            // MyBatis를 통한 중복 확인
            // Integer count = sqlSession.selectOne(USER_MAPPER_NAMESPACE + ".existsByUsername", username);
            // return count != null && count > 0;
            
            // 임시 샘플 중복 확인
            return "admin".equals(username) || "test".equals(username);
            
        } catch (Exception e) {
            System.err.println("사용자명 중복 확인 중 오류: " + e.getMessage());
            return false;
        }
    }
    
    /**
     * 이메일 중복 확인 (MyBatis 사용)
     */
    public boolean existsByEmail(String email) {
        try {
            // MyBatis를 통한 중복 확인
            // Integer count = sqlSession.selectOne(USER_MAPPER_NAMESPACE + ".existsByEmail", email);
            // return count != null && count > 0;
            
            // 임시 샘플 중복 확인
            return "admin@example.com".equals(email) || "test@example.com".equals(email);
            
        } catch (Exception e) {
            System.err.println("이메일 중복 확인 중 오류: " + e.getMessage());
            return false;
        }
    }
    
    /**
     * 이메일 인증 여부 확인 (MyBatis 사용)
     */
    public boolean isEmailVerified(String userId) {
        try {
            // MyBatis를 통한 이메일 인증 확인
            // Boolean verified = sqlSession.selectOne(USER_MAPPER_NAMESPACE + ".isEmailVerified", userId);
            // return verified != null && verified;
            
            // 임시 샘플 이메일 인증 확인
            return !userId.endsWith("_unverified");
            
        } catch (Exception e) {
            System.err.println("이메일 인증 확인 중 오류: " + e.getMessage());
            return false;
        }
    }
    
    /**
     * 전화번호 인증 여부 확인 (MyBatis 사용)
     */
    public boolean isPhoneVerified(String userId) {
        try {
            // MyBatis를 통한 전화번호 인증 확인
            // Boolean verified = sqlSession.selectOne(USER_MAPPER_NAMESPACE + ".isPhoneVerified", userId);
            // return verified != null && verified;
            
            // 임시 샘플 전화번호 인증 확인
            return !userId.endsWith("_no_phone");
            
        } catch (Exception e) {
            System.err.println("전화번호 인증 확인 중 오류: " + e.getMessage());
            return false;
        }
    }
    
    // 통계 관련 메서드들
    
    public int getTotalUserCount() {
        try {
            // MyBatis를 통한 총 사용자 수 조회
            // Integer count = sqlSession.selectOne(USER_MAPPER_NAMESPACE + ".getTotalUserCount");
            // return count != null ? count : 0;
            
            // 임시 샘플 총 사용자 수
            return 150;
            
        } catch (Exception e) {
            System.err.println("총 사용자 수 조회 중 오류: " + e.getMessage());
            return 0;
        }
    }
    
    public int getActiveUserCount() {
        try {
            // MyBatis를 통한 활성 사용자 수 조회
            // Integer count = sqlSession.selectOne(USER_MAPPER_NAMESPACE + ".getActiveUserCount");
            // return count != null ? count : 0;
            
            // 임시 샘플 활성 사용자 수
            return 120;
            
        } catch (Exception e) {
            System.err.println("활성 사용자 수 조회 중 오류: " + e.getMessage());
            return 0;
        }
    }
    
    public int getNewUsersTodayCount() {
        try {
            // MyBatis를 통한 오늘 가입 사용자 수 조회
            // Integer count = sqlSession.selectOne(USER_MAPPER_NAMESPACE + ".getNewUsersTodayCount");
            // return count != null ? count : 0;
            
            // 임시 샘플 오늘 가입 사용자 수
            return 8;
            
        } catch (Exception e) {
            System.err.println("오늘 가입 사용자 수 조회 중 오류: " + e.getMessage());
            return 0;
        }
    }
    
    public int getPremiumUserCount() {
        try {
            // MyBatis를 통한 프리미엄 사용자 수 조회
            // Integer count = sqlSession.selectOne(USER_MAPPER_NAMESPACE + ".getPremiumUserCount");
            // return count != null ? count : 0;
            
            // 임시 샘플 프리미엄 사용자 수
            return 25;
            
        } catch (Exception e) {
            System.err.println("프리미엄 사용자 수 조회 중 오류: " + e.getMessage());
            return 0;
        }
    }
    
    // 직접 쿼리 조합 메서드들
    
    /**
     * 직접 쿼리 조합으로 사용자 조회
     */
    public List<User> findUsersByDirectQuery(Map<String, Object> params) {
        try {
            StringBuilder query = new StringBuilder();
            query.append("SELECT u.user_id, u.username, u.full_name, u.email, u.phone, ");
            query.append("u.status, u.user_type, u.created_date, u.last_login_date ");
            query.append("FROM users u WHERE 1=1 ");
            
            // 동적 쿼리 조건 추가
            if (params.get("searchKeyword") != null) {
                String searchType = (String) params.get("searchType");
                String keyword = (String) params.get("searchKeyword");
                
                switch (searchType) {
                    case "username":
                        query.append("AND u.username LIKE '%").append(keyword).append("%' ");
                        break;
                    case "email":
                        query.append("AND u.email LIKE '%").append(keyword).append("%' ");
                        break;
                    case "name":
                        query.append("AND u.full_name LIKE '%").append(keyword).append("%' ");
                        break;
                    case "phone":
                        query.append("AND u.phone LIKE '%").append(keyword).append("%' ");
                        break;
                    default:
                        query.append("AND (u.username LIKE '%").append(keyword).append("%' ");
                        query.append("OR u.email LIKE '%").append(keyword).append("%' ");
                        query.append("OR u.full_name LIKE '%").append(keyword).append("%') ");
                        break;
                }
            }
            
            if (params.get("status") != null) {
                query.append("AND u.status = '").append(params.get("status")).append("' ");
            }
            
            if (params.get("userType") != null) {
                query.append("AND u.user_type = '").append(params.get("userType")).append("' ");
            }
            
            // 페이징 처리
            int page = (Integer) params.getOrDefault("page", 1);
            int pageSize = (Integer) params.getOrDefault("pageSize", 10);
            int offset = (page - 1) * pageSize;
            
            query.append("ORDER BY u.created_date DESC ");
            query.append("LIMIT ").append(pageSize).append(" OFFSET ").append(offset);
            
            System.out.println("직접 쿼리: " + query.toString());
            
            // 실제로는 JDBC를 통해 쿼리 실행
            // return executeQuery(query.toString(), params);
            
            // 임시 샘플 데이터 반환
            return generateSampleUsers(params);
            
        } catch (Exception e) {
            System.err.println("직접 쿼리 조회 중 오류: " + e.getMessage());
            throw new RuntimeException("직접 쿼리 조회 실패", e);
        }
    }
    
    // 샘플 데이터 생성 메서드들 (실제로는 MyBatis 결과)
    
    private List<User> generateSampleUsers(Map<String, Object> params) {
        List<User> users = new ArrayList<>();
        Random random = new Random();
        
        int count = 10; // 기본 10개
        if (params.get("pageSize") != null) {
            count = Math.min((Integer) params.get("pageSize"), 20);
        }
        
        for (int i = 1; i <= count; i++) {
            User user = new User();
            user.setUserId("USER" + String.format("%03d", i));
            user.setUsername("user" + i);
            user.setFullName("사용자" + i);
            user.setEmail("user" + i + "@example.com");
            user.setPhone("010-1234-" + String.format("%04d", 1000 + i));
            user.setStatus(i % 4 == 0 ? "INACTIVE" : "ACTIVE");
            user.setUserType(i % 5 == 0 ? "PREMIUM" : "NORMAL");
            user.setCreatedDate(new Date(System.currentTimeMillis() - random.nextInt(365 * 24 * 60 * 60 * 1000)));
            user.setLastLoginDate(new Date(System.currentTimeMillis() - random.nextInt(30 * 24 * 60 * 60 * 1000)));
            user.setIsAdmin(i == 1);
            user.setIsPremium(i % 5 == 0);
            user.setEmailVerified(i % 3 != 0);
            user.setPhoneVerified(i % 4 != 0);
            
            users.add(user);
        }
        
        return users;
    }
    
    private List<User> generateAdvancedSampleUsers(Map<String, Object> params) {
        // 고급 검색 결과 샘플 데이터
        return generateSampleUsers(params);
    }
    
    private List<User> generateUsersByType(String userType) {
        List<User> users = new ArrayList<>();
        Random random = new Random();
        
        int count = userType.equals("ADMIN") ? 3 : 8;
        
        for (int i = 1; i <= count; i++) {
            User user = new User();
            user.setUserId(userType + "_" + String.format("%03d", i));
            user.setUsername(userType.toLowerCase() + "_user" + i);
            user.setFullName(userType + " 사용자" + i);
            user.setEmail(userType.toLowerCase() + i + "@example.com");
            user.setPhone("010-1234-" + String.format("%04d", 2000 + i));
            user.setStatus("ACTIVE");
            user.setUserType(userType);
            user.setCreatedDate(new Date(System.currentTimeMillis() - random.nextInt(180 * 24 * 60 * 60 * 1000)));
            user.setLastLoginDate(new Date(System.currentTimeMillis() - random.nextInt(7 * 24 * 60 * 60 * 1000)));
            
            switch (userType) {
                case "ADMIN":
                    user.setIsAdmin(true);
                    break;
                case "PREMIUM":
                    user.setIsPremium(true);
                    break;
                case "GUEST":
                    user.setIsGuest(true);
                    break;
                default:
                    user.setIsNormal(true);
                    break;
            }
            
            users.add(user);
        }
        
        return users;
    }
    
    private User generateUserById(String userId) {
        if ("USER001".equals(userId)) {
            User user = new User();
            user.setUserId("USER001");
            user.setUsername("admin");
            user.setFullName("관리자");
            user.setEmail("admin@example.com");
            user.setPhone("010-1234-5678");
            user.setStatus("ACTIVE");
            user.setUserType("ADMIN");
            user.setCreatedDate(new Date(System.currentTimeMillis() - 365 * 24 * 60 * 60 * 1000L));
            user.setLastLoginDate(new Date(System.currentTimeMillis() - 2 * 60 * 60 * 1000L));
            user.setIsAdmin(true);
            user.setEmailVerified(true);
            user.setPhoneVerified(true);
            return user;
        }
        return null;
    }
    
    private User generateNewUser(Map<String, Object> userData) {
        User user = new User();
        user.setUserId("USER" + System.currentTimeMillis());
        user.setUsername((String) userData.get("username"));
        user.setFullName((String) userData.get("fullName"));
        user.setEmail((String) userData.get("email"));
        user.setPhone((String) userData.get("phone"));
        user.setStatus("ACTIVE");
        user.setUserType("NORMAL");
        user.setCreatedDate(new Date());
        user.setIsNormal(true);
        return user;
    }
    
    private User generateUpdatedUser(String userId, Map<String, Object> updateData) {
        User user = generateUserById(userId);
        if (user != null) {
            if (updateData.get("fullName") != null) {
                user.setFullName((String) updateData.get("fullName"));
            }
            if (updateData.get("email") != null) {
                user.setEmail((String) updateData.get("email"));
            }
            if (updateData.get("phone") != null) {
                user.setPhone((String) updateData.get("phone"));
            }
        }
        return user;
    }
}
