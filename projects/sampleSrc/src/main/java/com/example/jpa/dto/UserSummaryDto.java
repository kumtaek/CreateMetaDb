package com.example.jpa.dto;

import com.example.jpa.entity.UserStatus;

/**
 * User Summary DTO - JPA Projection용
 */
public class UserSummaryDto {
    private Long userId;
    private String username;
    private String email;
    private UserStatus status;
    
    // 기본 생성자
    public UserSummaryDto() {}
    
    // JPA Projection 생성자
    public UserSummaryDto(Long userId, String username, String email, UserStatus status) {
        this.userId = userId;
        this.username = username;
        this.email = email;
        this.status = status;
    }
    
    // Getter/Setter
    public Long getUserId() {
        return userId;
    }
    
    public void setUserId(Long userId) {
        this.userId = userId;
    }
    
    public String getUsername() {
        return username;
    }
    
    public void setUsername(String username) {
        this.username = username;
    }
    
    public String getEmail() {
        return email;
    }
    
    public void setEmail(String email) {
        this.email = email;
    }
    
    public UserStatus getStatus() {
        return status;
    }
    
    public void setStatus(UserStatus status) {
        this.status = status;
    }
    
    @Override
    public String toString() {
        return "UserSummaryDto{" +
                "userId=" + userId +
                ", username='" + username + '\'' +
                ", email='" + email + '\'' +
                ", status=" + status +
                '}';
    }
}

