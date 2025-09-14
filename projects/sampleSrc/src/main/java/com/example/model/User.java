package com.example.model;

import java.util.Date;
import java.util.Objects;

public class User {
    
    private Long id;
    private String username;
    private String email;
    private String password;
    private String name;
    private Integer age;
    private String status;
    private String userType;
    private Date createdDate;
    private Date updatedDate;
    private String phone;
    private String address;
    
    // Constructors
    public User() {}
    
    public User(String username, String email, String password) {
        this.username = username;
        this.email = email;
        this.password = password;
    }
    
    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    
    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }
    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public Integer getAge() { return age; }
    public void setAge(Integer age) { this.age = age; }
    
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    
    public String getUserType() { return userType; }
    public void setUserType(String userType) { this.userType = userType; }
    
    public Date getCreatedDate() { return createdDate; }
    public void setCreatedDate(Date createdDate) { this.createdDate = createdDate; }
    
    public Date getUpdatedDate() { return updatedDate; }
    public void setUpdatedDate(Date updatedDate) { this.updatedDate = updatedDate; }
    
    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }
    
    public String getAddress() { return address; }
    public void setAddress(String address) { this.address = address; }
    
    // 비즈니스 로직 메서드들
    public boolean isActive() {
        return "ACTIVE".equals(this.status);
    }
    
    public boolean isAdmin() {
        return "ADMIN".equals(this.userType);
    }
    
    public boolean isPremium() {
        return "PREMIUM".equals(this.userType);
    }
    
    public boolean isAdult() {
        return this.age != null && this.age >= 18;
    }
    
    public String getDisplayName() {
        return this.name != null ? this.name : this.username;
    }
    
    public String getMaskedEmail() {
        if (this.email == null || !this.email.contains("@")) {
            return this.email;
        }
        String[] parts = this.email.split("@");
        if (parts[0].length() <= 2) {
            return this.email;
        }
        return parts[0].substring(0, 2) + "***@" + parts[1];
    }
    
    public String getMaskedPhone() {
        if (this.phone == null || this.phone.length() <= 4) {
            return this.phone;
        }
        return this.phone.substring(0, this.phone.length() - 4) + "****";
    }
    
    public int getAccountAgeInDays() {
        if (this.createdDate == null) {
            return 0;
        }
        long diffInMillies = new java.util.Date().getTime() - this.createdDate.getTime();
        return (int) (diffInMillies / (1000 * 60 * 60 * 24));
    }
    
    public String getStatusDisplayName() {
        if (this.status == null) {
            return "알 수 없음";
        }
        switch (this.status.toUpperCase()) {
            case "ACTIVE": return "활성";
            case "INACTIVE": return "비활성";
            case "SUSPENDED": return "정지";
            case "DELETED": return "삭제됨";
            default: return this.status;
        }
    }
    
    public String getUserTypeDisplayName() {
        if (this.userType == null) {
            return "일반";
        }
        switch (this.userType.toUpperCase()) {
            case "NORMAL": return "일반";
            case "PREMIUM": return "프리미엄";
            case "ADMIN": return "관리자";
            case "GUEST": return "게스트";
            default: return this.userType;
        }
    }
    
    public boolean hasValidEmail() {
        return this.email != null && this.email.contains("@") && this.email.contains(".");
    }
    
    public boolean hasValidPhone() {
        return this.phone != null && this.phone.matches("\\d{3}-\\d{4}-\\d{4}");
    }
    
    public String getAgeGroup() {
        if (this.age == null) {
            return "알 수 없음";
        }
        if (this.age < 13) return "어린이";
        if (this.age < 20) return "청소년";
        if (this.age < 30) return "20대";
        if (this.age < 40) return "30대";
        if (this.age < 50) return "40대";
        if (this.age < 60) return "50대";
        return "60대 이상";
    }
    
    public boolean canAccessAdminFeatures() {
        return isActive() && isAdmin();
    }
    
    public boolean canAccessPremiumFeatures() {
        return isActive() && (isPremium() || isAdmin());
    }
    
    public String getLastUpdateInfo() {
        if (this.updatedDate == null) {
            return "업데이트 정보 없음";
        }
        long diffInHours = (new java.util.Date().getTime() - this.updatedDate.getTime()) / (1000 * 60 * 60);
        if (diffInHours < 1) {
            return "방금 전";
        } else if (diffInHours < 24) {
            return diffInHours + "시간 전";
        } else {
            int diffInDays = (int) (diffInHours / 24);
            return diffInDays + "일 전";
        }
    }
    
    @Override
    public String toString() {
        return "User{" +
                "id=" + id +
                ", username='" + username + '\'' +
                ", email='" + getMaskedEmail() + '\'' +
                ", name='" + name + '\'' +
                ", age=" + age +
                ", status='" + status + '\'' +
                ", userType='" + userType + '\'' +
                ", createdDate=" + createdDate +
                '}';
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        User user = (User) o;
        return Objects.equals(id, user.id) && Objects.equals(username, user.username);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(id, username);
    }
}