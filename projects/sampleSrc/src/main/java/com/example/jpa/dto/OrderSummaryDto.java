package com.example.jpa.dto;

import com.example.jpa.entity.OrderStatus;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * Order Summary DTO - JPA Projection용
 */
public class OrderSummaryDto {
    private Long orderId;
    private String orderNumber;
    private LocalDateTime orderDate;
    private OrderStatus orderStatus;
    private BigDecimal totalAmount;
    private String username;
    
    // 기본 생성자
    public OrderSummaryDto() {}
    
    // JPA Projection 생성자
    public OrderSummaryDto(Long orderId, String orderNumber, LocalDateTime orderDate, 
                          OrderStatus orderStatus, BigDecimal totalAmount, String username) {
        this.orderId = orderId;
        this.orderNumber = orderNumber;
        this.orderDate = orderDate;
        this.orderStatus = orderStatus;
        this.totalAmount = totalAmount;
        this.username = username;
    }
    
    // Getter/Setter
    public Long getOrderId() {
        return orderId;
    }
    
    public void setOrderId(Long orderId) {
        this.orderId = orderId;
    }
    
    public String getOrderNumber() {
        return orderNumber;
    }
    
    public void setOrderNumber(String orderNumber) {
        this.orderNumber = orderNumber;
    }
    
    public LocalDateTime getOrderDate() {
        return orderDate;
    }
    
    public void setOrderDate(LocalDateTime orderDate) {
        this.orderDate = orderDate;
    }
    
    public OrderStatus getOrderStatus() {
        return orderStatus;
    }
    
    public void setOrderStatus(OrderStatus orderStatus) {
        this.orderStatus = orderStatus;
    }
    
    public BigDecimal getTotalAmount() {
        return totalAmount;
    }
    
    public void setTotalAmount(BigDecimal totalAmount) {
        this.totalAmount = totalAmount;
    }
    
    public String getUsername() {
        return username;
    }
    
    public void setUsername(String username) {
        this.username = username;
    }
    
    @Override
    public String toString() {
        return "OrderSummaryDto{" +
                "orderId=" + orderId +
                ", orderNumber='" + orderNumber + '\'' +
                ", orderDate=" + orderDate +
                ", orderStatus=" + orderStatus +
                ", totalAmount=" + totalAmount +
                ", username='" + username + '\'' +
                '}';
    }
}

