package com.example.jpa.entity;

import javax.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

/**
 * JPA Product Entity
 * TABLE: PRODUCTS
 */
@Entity
@Table(name = "PRODUCTS", indexes = {
    @Index(name = "idx_product_category", columnList = "category_id"),
    @Index(name = "idx_product_status", columnList = "status"),
    @Index(name = "idx_product_name", columnList = "product_name")
})
public class Product {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "PRODUCT_ID")
    private Long productId;
    
    @Column(name = "PRODUCT_NAME", nullable = false, length = 200)
    private String productName;
    
    @Column(name = "PRODUCT_CODE", unique = true, length = 50)
    private String productCode;
    
    @Column(name = "DESCRIPTION", length = 1000)
    private String description;
    
    @Column(name = "PRICE", precision = 10, scale = 2)
    private BigDecimal price;
    
    @Column(name = "STOCK_QUANTITY")
    private Integer stockQuantity;
    
    @Column(name = "MIN_STOCK_LEVEL")
    private Integer minStockLevel;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "STATUS", length = 20)
    private ProductStatus status;
    
    @Column(name = "CREATED_AT")
    private LocalDateTime createdAt;
    
    @Column(name = "UPDATED_AT")
    private LocalDateTime updatedAt;
    
    // JPA 연관관계 - 카테고리
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "CATEGORY_ID")
    private Category category;
    
    // JPA 연관관계 - 주문 상품들
    @OneToMany(mappedBy = "product", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<OrderItem> orderItems;
    
    // 기본 생성자
    public Product() {}
    
    // 생성자
    public Product(String productName, String productCode, BigDecimal price) {
        this.productName = productName;
        this.productCode = productCode;
        this.price = price;
        this.status = ProductStatus.ACTIVE;
        this.stockQuantity = 0;
        this.minStockLevel = 10;
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
    public Long getProductId() {
        return productId;
    }
    
    public void setProductId(Long productId) {
        this.productId = productId;
    }
    
    public String getProductName() {
        return productName;
    }
    
    public void setProductName(String productName) {
        this.productName = productName;
    }
    
    public String getProductCode() {
        return productCode;
    }
    
    public void setProductCode(String productCode) {
        this.productCode = productCode;
    }
    
    public String getDescription() {
        return description;
    }
    
    public void setDescription(String description) {
        this.description = description;
    }
    
    public BigDecimal getPrice() {
        return price;
    }
    
    public void setPrice(BigDecimal price) {
        this.price = price;
    }
    
    public Integer getStockQuantity() {
        return stockQuantity;
    }
    
    public void setStockQuantity(Integer stockQuantity) {
        this.stockQuantity = stockQuantity;
    }
    
    public Integer getMinStockLevel() {
        return minStockLevel;
    }
    
    public void setMinStockLevel(Integer minStockLevel) {
        this.minStockLevel = minStockLevel;
    }
    
    public ProductStatus getStatus() {
        return status;
    }
    
    public void setStatus(ProductStatus status) {
        this.status = status;
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
    
    public Category getCategory() {
        return category;
    }
    
    public void setCategory(Category category) {
        this.category = category;
    }
    
    public List<OrderItem> getOrderItems() {
        return orderItems;
    }
    
    public void setOrderItems(List<OrderItem> orderItems) {
        this.orderItems = orderItems;
    }
    
    // 비즈니스 메서드
    public boolean isActive() {
        return ProductStatus.ACTIVE.equals(this.status);
    }
    
    public boolean isOutOfStock() {
        return this.stockQuantity == null || this.stockQuantity <= 0;
    }
    
    public boolean isLowStock() {
        return this.stockQuantity != null && 
               this.minStockLevel != null && 
               this.stockQuantity <= this.minStockLevel;
    }
    
    public void reduceStock(int quantity) {
        if (this.stockQuantity != null && this.stockQuantity >= quantity) {
            this.stockQuantity -= quantity;
        }
    }
    
    public void addStock(int quantity) {
        if (this.stockQuantity == null) {
            this.stockQuantity = quantity;
        } else {
            this.stockQuantity += quantity;
        }
    }
}

