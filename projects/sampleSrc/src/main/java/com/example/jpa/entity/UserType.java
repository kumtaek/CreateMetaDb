package com.example.jpa.entity;

/**
 * 사용자 타입 Enum
 */
public enum UserType {
    REGULAR("일반회원"),
    PREMIUM("프리미엄회원"),
    VIP("VIP회원"),
    ADMIN("관리자"),
    GUEST("게스트");
    
    private final String description;
    
    UserType(String description) {
        this.description = description;
    }
    
    public String getDescription() {
        return description;
    }
    
    public static UserType fromString(String type) {
        for (UserType userType : UserType.values()) {
            if (userType.name().equalsIgnoreCase(type)) {
                return userType;
            }
        }
        return REGULAR; // 기본값
    }
}

