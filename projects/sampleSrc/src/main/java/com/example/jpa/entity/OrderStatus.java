package com.example.jpa.entity;

/**
 * 주문 상태 Enum
 */
public enum OrderStatus {
    PENDING("주문접수"),
    CONFIRMED("주문확인"),
    PROCESSING("처리중"),
    SHIPPED("배송중"),
    DELIVERED("배송완료"),
    COMPLETED("주문완료"),
    CANCELLED("주문취소"),
    REFUNDED("환불완료");
    
    private final String description;
    
    OrderStatus(String description) {
        this.description = description;
    }
    
    public String getDescription() {
        return description;
    }
    
    public static OrderStatus fromString(String status) {
        for (OrderStatus orderStatus : OrderStatus.values()) {
            if (orderStatus.name().equalsIgnoreCase(status)) {
                return orderStatus;
            }
        }
        return PENDING; // 기본값
    }
    
    public boolean canTransitionTo(OrderStatus newStatus) {
        switch (this) {
            case PENDING:
                return newStatus == CONFIRMED || newStatus == CANCELLED;
            case CONFIRMED:
                return newStatus == PROCESSING || newStatus == CANCELLED;
            case PROCESSING:
                return newStatus == SHIPPED || newStatus == CANCELLED;
            case SHIPPED:
                return newStatus == DELIVERED || newStatus == CANCELLED;
            case DELIVERED:
                return newStatus == COMPLETED || newStatus == REFUNDED;
            case COMPLETED:
                return newStatus == REFUNDED;
            case CANCELLED:
            case REFUNDED:
                return false; // 최종 상태
            default:
                return false;
        }
    }
}
