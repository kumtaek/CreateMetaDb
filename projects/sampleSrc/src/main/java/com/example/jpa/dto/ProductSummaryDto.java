package com.example.jpa.dto;

import com.example.jpa.entity.ProductStatus;
import java.math.BigDecimal;

/**
 * Product Summary DTO - JPA Projection용
 */
public class ProductSummaryDto {
    private Long productId;
    private String productName;
    private BigDecimal price;
    private Integer stockQuantity;
    private ProductStatus status;
    
    // 기본 생성자
    public ProductSummaryDto() {}
    
    // JPA Projection 생성자
    public ProductSummaryDto(Long productId, String productName, BigDecimal price, 
                            Integer stockQuantity, ProductStatus status) {
        this.productId = productId;
        this.productName = productName;
        this.price = price;
        this.stockQuantity = stockQuantity;
        this.status = status;
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
    
    public ProductStatus getStatus() {
        return status;
    }
    
    public void setStatus(ProductStatus status) {
        this.status = status;
    }
    
    @Override
    public String toString() {
        return "ProductSummaryDto{" +
                "productId=" + productId +
                ", productName='" + productName + '\'' +
                ", price=" + price +
                ", stockQuantity=" + stockQuantity +
                ", status=" + status +
                '}';
    }
}

