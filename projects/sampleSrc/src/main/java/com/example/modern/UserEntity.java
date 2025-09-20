package com.example.modern;

import javax.persistence.*;
import javax.validation.constraints.*;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Set;

/**
 * JPA/Hibernate 사용자 엔티티 - 연관관계 도출 테스트용
 * 목적: @Entity, @OneToMany, @ManyToOne 등 JPA 어노테이션 패턴 테스트
 * 연관관계 중심: JPA 관계 매핑을 통한 테이블 간 연결 표현
 */
@Entity
@Table(name = "users", 
       indexes = {
           @Index(name = "idx_username", columnList = "username"),
           @Index(name = "idx_email", columnList = "email"),
           @Index(name = "idx_dept_status", columnList = "department_id, status")
       })
public class UserEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "user_id")
    private Long id;

    @NotBlank
    @Size(min = 3, max = 50)
    @Column(name = "username", nullable = false, unique = true)
    private String username;

    @Email
    @NotBlank
    @Column(name = "email", nullable = false, unique = true)
    private String email;

    @NotBlank
    @Size(min = 2, max = 100)
    @Column(name = "full_name", nullable = false)
    private String fullName;

    @Pattern(regexp = "^(ADMIN|USER|MANAGER|GUEST)$")
    @Column(name = "user_type", nullable = false)
    private String userType;

    @Pattern(regexp = "^(ACTIVE|INACTIVE|PENDING|SUSPENDED)$")
    @Column(name = "status", nullable = false)
    private String status;

    @Column(name = "created_date", nullable = false)
    private LocalDateTime createdDate;

    @Column(name = "updated_date")
    private LocalDateTime updatedDate;

    @Column(name = "last_login_date")
    private LocalDateTime lastLoginDate;

    // JPA 연관관계 매핑들

    /**
     * 다대일 관계: User -> Department
     * 연관 테이블: departments
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "department_id", referencedColumnName = "dept_id")
    private DepartmentEntity department;

    /**
     * 일대일 관계: User -> UserProfile
     * 연관 테이블: user_profiles
     */
    @OneToOne(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private UserProfileEntity profile;

    /**
     * 일대다 관계: User -> Orders
     * 연관 테이블: orders
     */
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<OrderEntity> orders;

    /**
     * 다대다 관계: User -> Roles (through user_roles)
     * 연관 테이블: user_roles, roles
     */
    @ManyToMany(fetch = FetchType.LAZY)
    @JoinTable(
        name = "user_roles",
        joinColumns = @JoinColumn(name = "user_id"),
        inverseJoinColumns = @JoinColumn(name = "role_id")
    )
    private Set<RoleEntity> roles;

    /**
     * 일대일 관계: User -> UserSettings
     * 연관 테이블: user_settings
     */
    @OneToOne(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private UserSettingsEntity settings;

    /**
     * 일대다 관계: User -> UserActivities
     * 연관 테이블: user_activities
     */
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<UserActivityEntity> activities;

    // JPA 라이프사이클 콜백
    @PrePersist
    protected void onCreate() {
        createdDate = LocalDateTime.now();
        if (status == null) {
            status = "PENDING";
        }
    }

    @PreUpdate
    protected void onUpdate() {
        updatedDate = LocalDateTime.now();
    }

    // 비즈니스 메서드들 (연관관계 활용)
    
    public boolean isActive() {
        return "ACTIVE".equals(this.status);
    }
    
    public boolean hasRole(String roleName) {
        return roles != null && roles.stream()
            .anyMatch(role -> roleName.equals(role.getRoleName()));
    }
    
    public int getTotalOrderCount() {
        return orders != null ? orders.size() : 0;
    }
    
    public BigDecimal getTotalSpent() {
        if (orders == null || orders.isEmpty()) {
            return BigDecimal.ZERO;
        }
        
        return orders.stream()
            .filter(order -> "COMPLETED".equals(order.getStatus()))
            .map(OrderEntity::getTotalAmount)
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
    
    public LocalDateTime getLastOrderDate() {
        if (orders == null || orders.isEmpty()) {
            return null;
        }
        
        return orders.stream()
            .map(OrderEntity::getOrderDate)
            .max(LocalDateTime::compareTo)
            .orElse(null);
    }

    // Constructors
    public UserEntity() {}

    public UserEntity(String username, String email, String fullName, String userType) {
        this.username = username;
        this.email = email;
        this.fullName = fullName;
        this.userType = userType;
        this.status = "PENDING";
        this.createdDate = LocalDateTime.now();
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getFullName() { return fullName; }
    public void setFullName(String fullName) { this.fullName = fullName; }

    public String getUserType() { return userType; }
    public void setUserType(String userType) { this.userType = userType; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public LocalDateTime getCreatedDate() { return createdDate; }
    public void setCreatedDate(LocalDateTime createdDate) { this.createdDate = createdDate; }

    public LocalDateTime getUpdatedDate() { return updatedDate; }
    public void setUpdatedDate(LocalDateTime updatedDate) { this.updatedDate = updatedDate; }

    public LocalDateTime getLastLoginDate() { return lastLoginDate; }
    public void setLastLoginDate(LocalDateTime lastLoginDate) { this.lastLoginDate = lastLoginDate; }

    public DepartmentEntity getDepartment() { return department; }
    public void setDepartment(DepartmentEntity department) { this.department = department; }

    public UserProfileEntity getProfile() { return profile; }
    public void setProfile(UserProfileEntity profile) { this.profile = profile; }

    public List<OrderEntity> getOrders() { return orders; }
    public void setOrders(List<OrderEntity> orders) { this.orders = orders; }

    public Set<RoleEntity> getRoles() { return roles; }
    public void setRoles(Set<RoleEntity> roles) { this.roles = roles; }

    public UserSettingsEntity getSettings() { return settings; }
    public void setSettings(UserSettingsEntity settings) { this.settings = settings; }

    public List<UserActivityEntity> getActivities() { return activities; }
    public void setActivities(List<UserActivityEntity> activities) { this.activities = activities; }

    @Override
    public String toString() {
        return "UserEntity{" +
                "id=" + id +
                ", username='" + username + '\'' +
                ", email='" + email + '\'' +
                ", fullName='" + fullName + '\'' +
                ", userType='" + userType + '\'' +
                ", status='" + status + '\'' +
                ", createdDate=" + createdDate +
                '}';
    }
}



