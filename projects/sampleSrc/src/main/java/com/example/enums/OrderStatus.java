package com.example.enums;

/**
 * 테스트 케이스: Enum 클래스
 * - enum 키워드 테스트
 * - class_type 'enum'으로 분류 테스트
 * - enum 상수 및 메서드 테스트
 */
public enum OrderStatus {
    PENDING("대기중"),
    PROCESSING("처리중"),
    SHIPPED("배송됨"),
    DELIVERED("배송완료"),
    CANCELLED("취소됨");

    private final String description;

    /**
     * enum 생성자
     */
    OrderStatus(String description) {
        this.description = description;
    }

    /**
     * 설명 getter
     */
    public String getDescription() {
        return description;
    }

    /**
     * 비즈니스 로직이 포함된 메서드 - business 복잡도로 분류
     */
    public boolean canTransitionTo(OrderStatus newStatus) {
        switch (this) {
            case PENDING:
                return newStatus == PROCESSING || newStatus == CANCELLED;
            case PROCESSING:
                return newStatus == SHIPPED || newStatus == CANCELLED;
            case SHIPPED:
                return newStatus == DELIVERED;
            case DELIVERED:
            case CANCELLED:
                return false;
            default:
                return false;
        }
    }
}