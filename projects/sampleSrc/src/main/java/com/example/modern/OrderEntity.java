package com.example.modern;

import javax.persistence.*;
import javax.validation.constraints.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

/**
 * JPA 주문 엔티티 - 복잡한 연관관계 테스트용
 * 연관관계: Order -> User, Order -> OrderItems, Order -> Payments, Order -> Shipments
 */
@Entity
@Table(name = "orders")
public class OrderEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "order_id")
    private Long id;

    @NotNull
    @Column(name = "user_id", nullable = false)
    private Long userId;

    @NotNull
    @Column(name = "order_date", nullable = false)
    private LocalDateTime orderDate;

    @NotNull
    @DecimalMin("0.0")
    @Column(name = "total_amount", nullable = false, precision = 10, scale = 2)
    private BigDecimal totalAmount;

    @Pattern(regexp = "^(PENDING|CONFIRMED|SHIPPED|DELIVERED|CANCELLED)$")
    @Column(name = "status", nullable = false)
    private String status;

    @Column(name = "payment_method")
    private String paymentMethod;

    @Size(max = 500)
    @Column(name = "shipping_address")
    private String shippingAddress;

    @Column(name = "tracking_number")
    private String trackingNumber;

    // JPA 연관관계 매핑

    /**
     * 다대일 관계: Order -> User
     * 연관 테이블: users
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", referencedColumnName = "user_id", insertable = false, updatable = false)
    private UserEntity user;

    /**
     * 일대다 관계: Order -> OrderItems
     * 연관 테이블: order_items
     */
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<OrderItemEntity> orderItems;

    /**
     * 일대다 관계: Order -> Payments
     * 연관 테이블: payments
     */
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<PaymentEntity> payments;

    /**
     * 일대일 관계: Order -> Shipment
     * 연관 테이블: shipments
     */
    @OneToOne(mappedBy = "order", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private ShipmentEntity shipment;

    // 비즈니스 메서드들
    
    public BigDecimal calculateItemsTotal() {
        if (orderItems == null || orderItems.isEmpty()) {
            return BigDecimal.ZERO;
        }
        
        return orderItems.stream()
            .map(item -> item.getUnitPrice().multiply(BigDecimal.valueOf(item.getQuantity())))
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
    
    public int getTotalItemCount() {
        if (orderItems == null) {
            return 0;
        }
        
        return orderItems.stream()
            .mapToInt(OrderItemEntity::getQuantity)
            .sum();
    }
    
    public boolean isPaid() {
        if (payments == null) {
            return false;
        }
        
        BigDecimal totalPaid = payments.stream()
            .filter(payment -> "COMPLETED".equals(payment.getStatus()))
            .map(PaymentEntity::getAmount)
            .reduce(BigDecimal.ZERO, BigDecimal::add);
        
        return totalPaid.compareTo(totalAmount) >= 0;
    }
    
    public boolean isShipped() {
        return shipment != null && "SHIPPED".equals(shipment.getStatus());
    }
    
    public boolean isDelivered() {
        return shipment != null && "DELIVERED".equals(shipment.getStatus());
    }

    // Constructors
    public OrderEntity() {}

    public OrderEntity(Long userId, BigDecimal totalAmount, String paymentMethod, String shippingAddress) {
        this.userId = userId;
        this.totalAmount = totalAmount;
        this.paymentMethod = paymentMethod;
        this.shippingAddress = shippingAddress;
        this.orderDate = LocalDateTime.now();
        this.status = "PENDING";
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }

    public LocalDateTime getOrderDate() { return orderDate; }
    public void setOrderDate(LocalDateTime orderDate) { this.orderDate = orderDate; }

    public BigDecimal getTotalAmount() { return totalAmount; }
    public void setTotalAmount(BigDecimal totalAmount) { this.totalAmount = totalAmount; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getPaymentMethod() { return paymentMethod; }
    public void setPaymentMethod(String paymentMethod) { this.paymentMethod = paymentMethod; }

    public String getShippingAddress() { return shippingAddress; }
    public void setShippingAddress(String shippingAddress) { this.shippingAddress = shippingAddress; }

    public String getTrackingNumber() { return trackingNumber; }
    public void setTrackingNumber(String trackingNumber) { this.trackingNumber = trackingNumber; }

    public UserEntity getUser() { return user; }
    public void setUser(UserEntity user) { this.user = user; }

    public List<OrderItemEntity> getOrderItems() { return orderItems; }
    public void setOrderItems(List<OrderItemEntity> orderItems) { this.orderItems = orderItems; }

    public List<PaymentEntity> getPayments() { return payments; }
    public void setPayments(List<PaymentEntity> payments) { this.payments = payments; }

    public ShipmentEntity getShipment() { return shipment; }
    public void setShipment(ShipmentEntity shipment) { this.shipment = shipment; }
}



