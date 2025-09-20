package com.example.jpa.entity;

import javax.persistence.*;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * JPA UserProfile Entity
 * TABLE: USER_PROFILES
 */
@Entity
@Table(name = "USER_PROFILES")
public class UserProfile {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "PROFILE_ID")
    private Long profileId;
    
    @Column(name = "BIRTH_DATE")
    private LocalDate birthDate;
    
    @Column(name = "GENDER", length = 10)
    private String gender;
    
    @Column(name = "ADDRESS", length = 500)
    private String address;
    
    @Column(name = "CITY", length = 100)
    private String city;
    
    @Column(name = "POSTAL_CODE", length = 20)
    private String postalCode;
    
    @Column(name = "COUNTRY", length = 50)
    private String country;
    
    @Column(name = "OCCUPATION", length = 100)
    private String occupation;
    
    @Column(name = "COMPANY", length = 200)
    private String company;
    
    @Column(name = "WEBSITE", length = 255)
    private String website;
    
    @Column(name = "BIO", length = 1000)
    private String bio;
    
    @Column(name = "AVATAR_URL", length = 500)
    private String avatarUrl;
    
    @Column(name = "PREFERENCES", length = 2000)
    private String preferences;
    
    @Column(name = "CREATED_AT")
    private LocalDateTime createdAt;
    
    @Column(name = "UPDATED_AT")
    private LocalDateTime updatedAt;
    
    // JPA 연관관계 - 사용자 (One-to-One)
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "USER_ID", nullable = false)
    private User user;
    
    // 기본 생성자
    public UserProfile() {}
    
    // 생성자
    public UserProfile(User user) {
        this.user = user;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }
    
    // JPA 생명주기 콜백
    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }
    
    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
    
    // Getter/Setter
    public Long getProfileId() {
        return profileId;
    }
    
    public void setProfileId(Long profileId) {
        this.profileId = profileId;
    }
    
    public LocalDate getBirthDate() {
        return birthDate;
    }
    
    public void setBirthDate(LocalDate birthDate) {
        this.birthDate = birthDate;
    }
    
    public String getGender() {
        return gender;
    }
    
    public void setGender(String gender) {
        this.gender = gender;
    }
    
    public String getAddress() {
        return address;
    }
    
    public void setAddress(String address) {
        this.address = address;
    }
    
    public String getCity() {
        return city;
    }
    
    public void setCity(String city) {
        this.city = city;
    }
    
    public String getPostalCode() {
        return postalCode;
    }
    
    public void setPostalCode(String postalCode) {
        this.postalCode = postalCode;
    }
    
    public String getCountry() {
        return country;
    }
    
    public void setCountry(String country) {
        this.country = country;
    }
    
    public String getOccupation() {
        return occupation;
    }
    
    public void setOccupation(String occupation) {
        this.occupation = occupation;
    }
    
    public String getCompany() {
        return company;
    }
    
    public void setCompany(String company) {
        this.company = company;
    }
    
    public String getWebsite() {
        return website;
    }
    
    public void setWebsite(String website) {
        this.website = website;
    }
    
    public String getBio() {
        return bio;
    }
    
    public void setBio(String bio) {
        this.bio = bio;
    }
    
    public String getAvatarUrl() {
        return avatarUrl;
    }
    
    public void setAvatarUrl(String avatarUrl) {
        this.avatarUrl = avatarUrl;
    }
    
    public String getPreferences() {
        return preferences;
    }
    
    public void setPreferences(String preferences) {
        this.preferences = preferences;
    }
    
    public LocalDateTime getCreatedAt() {
        return createdAt;
    }
    
    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
    
    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }
    
    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
    
    public User getUser() {
        return user;
    }
    
    public void setUser(User user) {
        this.user = user;
    }
    
    // 비즈니스 메서드
    public boolean hasCompleteProfile() {
        return this.birthDate != null && 
               this.address != null && !this.address.trim().isEmpty() &&
               this.city != null && !this.city.trim().isEmpty();
    }
    
    public String getFullAddress() {
        StringBuilder fullAddress = new StringBuilder();
        if (this.address != null) {
            fullAddress.append(this.address);
        }
        if (this.city != null) {
            if (fullAddress.length() > 0) fullAddress.append(", ");
            fullAddress.append(this.city);
        }
        if (this.postalCode != null) {
            if (fullAddress.length() > 0) fullAddress.append(" ");
            fullAddress.append(this.postalCode);
        }
        if (this.country != null) {
            if (fullAddress.length() > 0) fullAddress.append(", ");
            fullAddress.append(this.country);
        }
        return fullAddress.toString();
    }
}

