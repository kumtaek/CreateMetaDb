package com.example.jpa.entity;

import javax.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

/**
 * JPA Order Entity
 * TABLE: ORDERS
 */
@Entity
@Table(name = "ORDERS", indexes = {
    @Index(name = "idx_order_user", columnList = "user_id"),
    @Index(name = "idx_order_status", columnList = "order_status"),
    @Index(name = "idx_order_date", columnList = "order_date")
})
public class Order {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "ORDER_ID")
    private Long orderId;
    
    @Column(name = "ORDER_NUMBER", unique = true, nullable = false, length = 50)
    private String orderNumber;
    
    @Column(name = "ORDER_DATE")
    private LocalDateTime orderDate;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "ORDER_STATUS", length = 20)
    private OrderStatus orderStatus;
    
    @Column(name = "TOTAL_AMOUNT", precision = 12, scale = 2)
    private BigDecimal totalAmount;
    
    @Column(name = "DISCOUNT_AMOUNT", precision = 10, scale = 2)
    private BigDecimal discountAmount;
    
    @Column(name = "SHIPPING_FEE", precision = 8, scale = 2)
    private BigDecimal shippingFee;
    
    @Column(name = "PAYMENT_METHOD", length = 50)
    private String paymentMethod;
    
    @Column(name = "SHIPPING_ADDRESS", length = 500)
    private String shippingAddress;
    
    @Column(name = "ORDER_NOTES", length = 1000)
    private String orderNotes;
    
    @Column(name = "CREATED_AT")
    private LocalDateTime createdAt;
    
    @Column(name = "UPDATED_AT")
    private LocalDateTime updatedAt;
    
    // JPA 연관관계 - 주문자
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "USER_ID", nullable = false)
    private User user;
    
    // JPA 연관관계 - 주문 상품들
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<OrderItem> orderItems;
    
    // 기본 생성자
    public Order() {}
    
    // 생성자
    public Order(String orderNumber, User user) {
        this.orderNumber = orderNumber;
        this.user = user;
        this.orderDate = LocalDateTime.now();
        this.orderStatus = OrderStatus.PENDING;
        this.totalAmount = BigDecimal.ZERO;
        this.discountAmount = BigDecimal.ZERO;
        this.shippingFee = BigDecimal.ZERO;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }
    
    // JPA 생명주기 콜백
    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
        if (this.orderDate == null) {
            this.orderDate = LocalDateTime.now();
        }
    }
    
    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
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
    
    public BigDecimal getDiscountAmount() {
        return discountAmount;
    }
    
    public void setDiscountAmount(BigDecimal discountAmount) {
        this.discountAmount = discountAmount;
    }
    
    public BigDecimal getShippingFee() {
        return shippingFee;
    }
    
    public void setShippingFee(BigDecimal shippingFee) {
        this.shippingFee = shippingFee;
    }
    
    public String getPaymentMethod() {
        return paymentMethod;
    }
    
    public void setPaymentMethod(String paymentMethod) {
        this.paymentMethod = paymentMethod;
    }
    
    public String getShippingAddress() {
        return shippingAddress;
    }
    
    public void setShippingAddress(String shippingAddress) {
        this.shippingAddress = shippingAddress;
    }
    
    public String getOrderNotes() {
        return orderNotes;
    }
    
    public void setOrderNotes(String orderNotes) {
        this.orderNotes = orderNotes;
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
    
    public List<OrderItem> getOrderItems() {
        return orderItems;
    }
    
    public void setOrderItems(List<OrderItem> orderItems) {
        this.orderItems = orderItems;
    }
    
    // 비즈니스 메서드
    public boolean isPending() {
        return OrderStatus.PENDING.equals(this.orderStatus);
    }
    
    public boolean isCompleted() {
        return OrderStatus.COMPLETED.equals(this.orderStatus);
    }
    
    public boolean isCancelled() {
        return OrderStatus.CANCELLED.equals(this.orderStatus);
    }
    
    public BigDecimal getFinalAmount() {
        BigDecimal final_amount = this.totalAmount;
        if (this.discountAmount != null) {
            final_amount = final_amount.subtract(this.discountAmount);
        }
        if (this.shippingFee != null) {
            final_amount = final_amount.add(this.shippingFee);
        }
        return final_amount;
    }
    
    public int getItemCount() {
        return this.orderItems != null ? this.orderItems.size() : 0;
    }
}

