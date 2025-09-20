package com.example.modern;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.transaction.annotation.Transactional;
import java.util.*;
import java.time.LocalDateTime;

/**
 * 사용자 엔티티 서비스 - ModernRestController 연결용
 * 연관관계: ModernRestController -> UserEntityService -> UserEntityRepository -> users 테이블
 */
@Service
@Transactional
public class UserEntityService {

    @Autowired
    private UserEntityRepository userRepository;
    
    @Autowired
    private DepartmentEntityRepository departmentRepository;
    
    @Autowired
    private UserProfileEntityRepository profileRepository;
    
    @Autowired
    private UserRoleEntityRepository userRoleRepository;

    /**
     * 조건별 사용자 조회 (페이징)
     * 연관 테이블: users, departments, user_profiles
     */
    public Page<UserEntity> findUsersByCriteria(UserSearchCriteria criteria, Pageable pageable) {
        // 실제로는 JPA Repository 사용
        // return userRepository.findByCriteria(criteria, pageable);
        
        // 시뮬레이션을 위한 목 데이터
        return createMockUserPage(criteria, pageable);
    }

    /**
     * 사용자 ID로 조회
     * 연관 테이블: users
     */
    public Optional<UserEntity> findById(Long userId) {
        // return userRepository.findById(userId);
        
        if (userId != null && userId > 0) {
            UserEntity user = new UserEntity();
            user.setId(userId);
            user.setUsername("user" + userId);
            user.setEmail("user" + userId + "@example.com");
            user.setFullName("User " + userId);
            user.setUserType("USER");
            user.setStatus("ACTIVE");
            user.setCreatedDate(LocalDateTime.now().minusDays(30));
            return Optional.of(user);
        }
        
        return Optional.empty();
    }

    /**
     * 프로필과 함께 사용자 생성
     * 연관 테이블: users, user_profiles, user_settings, user_roles (INFERRED)
     */
    @Transactional
    public UserEntity createUserWithProfile(UserEntity userEntity, Map<String, Object> profileData) {
        // 1. 사용자 기본 정보 저장
        UserEntity savedUser = saveUser(userEntity);
        
        // 2. 프로필 정보 저장 (INFERRED user_profiles 테이블)
        if (profileData != null && !profileData.isEmpty()) {
            createUserProfile(savedUser.getId(), profileData);
        }
        
        // 3. 기본 설정 생성 (INFERRED user_settings 테이블)
        createDefaultUserSettings(savedUser.getId());
        
        // 4. 기본 역할 할당 (INFERRED user_roles 테이블)
        assignDefaultRole(savedUser.getId(), savedUser.getUserType());
        
        return savedUser;
    }

    /**
     * 관련 데이터와 함께 사용자 업데이트
     * 연관 테이블: users, user_profiles, departments
     */
    @Transactional
    public UserEntity updateUserWithRelations(UserEntity userEntity, UpdateUserRequestDto request) {
        // 1. 사용자 기본 정보 업데이트
        UserEntity updatedUser = saveUser(userEntity);
        
        // 2. 부서 변경 시 부서 관련 처리 (departments 테이블)
        if (request.getDepartmentId() != null) {
            updateUserDepartment(updatedUser.getId(), request.getDepartmentId());
        }
        
        // 3. 프로필 정보 업데이트 (user_profiles 테이블)
        if (request.getProfileData() != null) {
            updateUserProfile(updatedUser.getId(), request.getProfileData());
        }
        
        return updatedUser;
    }

    // 헬퍼 메서드들 (실제 데이터 처리 시뮬레이션)
    
    private UserEntity saveUser(UserEntity userEntity) {
        // 실제로는 userRepository.save(userEntity);
        
        if (userEntity.getId() == null) {
            userEntity.setId(generateNewUserId());
            userEntity.setCreatedDate(LocalDateTime.now());
        } else {
            userEntity.setUpdatedDate(LocalDateTime.now());
        }
        
        System.out.println("User saved: " + userEntity.getUsername());
        return userEntity;
    }
    
    private void createUserProfile(Long userId, Map<String, Object> profileData) {
        // INFERRED user_profiles 테이블에 데이터 생성 시뮬레이션
        System.out.println("Creating user profile for user ID: " + userId);
        System.out.println("Profile data: " + profileData);
    }
    
    private void createDefaultUserSettings(Long userId) {
        // INFERRED user_settings 테이블에 기본 설정 생성
        Map<String, Object> defaultSettings = Map.of(
            "theme", "LIGHT",
            "language", "ko",
            "timezone", "Asia/Seoul",
            "emailNotifications", true,
            "smsNotifications", false
        );
        
        System.out.println("Creating default settings for user ID: " + userId);
        System.out.println("Settings: " + defaultSettings);
    }
    
    private void assignDefaultRole(Long userId, String userType) {
        // INFERRED user_roles 테이블에 기본 역할 할당
        String defaultRole = switch (userType) {
            case "ADMIN" -> "SYSTEM_ADMIN";
            case "MANAGER" -> "DEPARTMENT_MANAGER";
            case "USER" -> "GENERAL_USER";
            default -> "GUEST_USER";
        };
        
        System.out.println("Assigning role '" + defaultRole + "' to user ID: " + userId);
    }
    
    private void updateUserDepartment(Long userId, Long departmentId) {
        // departments 테이블 연관 처리
        System.out.println("Updating department for user ID: " + userId + " to dept ID: " + departmentId);
    }
    
    private void updateUserProfile(Long userId, Map<String, Object> profileData) {
        // user_profiles 테이블 업데이트
        System.out.println("Updating profile for user ID: " + userId);
        System.out.println("Profile updates: " + profileData);
    }
    
    private Page<UserEntity> createMockUserPage(UserSearchCriteria criteria, Pageable pageable) {
        // 페이징된 사용자 목록 시뮬레이션
        List<UserEntity> users = new ArrayList<>();
        
        for (int i = 1; i <= pageable.getPageSize(); i++) {
            UserEntity user = new UserEntity();
            user.setId((long) (pageable.getPageNumber() * pageable.getPageSize() + i));
            user.setUsername("user" + user.getId());
            user.setEmail("user" + user.getId() + "@example.com");
            user.setFullName("User " + user.getId());
            user.setUserType("USER");
            user.setStatus("ACTIVE");
            user.setCreatedDate(LocalDateTime.now().minusDays(i));
            users.add(user);
        }
        
        // Page 객체 시뮬레이션 (실제로는 PageImpl 사용)
        return new MockPage<>(users, pageable, 100L);
    }
    
    private Long generateNewUserId() {
        return System.currentTimeMillis() % 100000;
    }
}

// Mock Repository 클래스들 (연결 시뮬레이션용)
interface UserEntityRepository {
    Page<UserEntity> findByCriteria(UserSearchCriteria criteria, Pageable pageable);
    Optional<UserEntity> findById(Long id);
    UserEntity save(UserEntity user);
}

interface DepartmentEntityRepository {
    Optional<DepartmentEntity> findById(Long id);
}

interface UserProfileEntityRepository {
    UserProfileEntity save(UserProfileEntity profile);
    Optional<UserProfileEntity> findByUserId(Long userId);
}

interface UserRoleEntityRepository {
    List<UserRoleEntity> findByUserId(Long userId);
    UserRoleEntity save(UserRoleEntity userRole);
}

// Mock Page 구현 (간단한 시뮬레이션)
class MockPage<T> implements Page<T> {
    private final List<T> content;
    private final Pageable pageable;
    private final long totalElements;
    
    public MockPage(List<T> content, Pageable pageable, long totalElements) {
        this.content = content;
        this.pageable = pageable;
        this.totalElements = totalElements;
    }
    
    @Override
    public List<T> getContent() { return content; }
    
    @Override
    public int getNumber() { return pageable.getPageNumber(); }
    
    @Override
    public int getSize() { return pageable.getPageSize(); }
    
    @Override
    public long getTotalElements() { return totalElements; }
    
    @Override
    public int getTotalPages() { return (int) Math.ceil((double) totalElements / pageable.getPageSize()); }
    
    @Override
    public boolean isFirst() { return pageable.getPageNumber() == 0; }
    
    @Override
    public boolean isLast() { return getNumber() >= getTotalPages() - 1; }
    
    // 기타 Page 인터페이스 메서드들 (기본 구현)
    @Override public int getNumberOfElements() { return content.size(); }
    @Override public boolean hasContent() { return !content.isEmpty(); }
    @Override public boolean hasNext() { return !isLast(); }
    @Override public boolean hasPrevious() { return !isFirst(); }
    @Override public Pageable nextPageable() { return pageable.next(); }
    @Override public Pageable previousPageable() { return pageable.previousOrFirst(); }
    @Override public java.util.Iterator<T> iterator() { return content.iterator(); }
    @Override public Pageable getPageable() { return pageable; }
    @Override public Sort getSort() { return pageable.getSort(); }
    @Override public boolean isEmpty() { return content.isEmpty(); }
    @Override public <U> Page<U> map(java.util.function.Function<? super T, ? extends U> converter) { return null; }
}



