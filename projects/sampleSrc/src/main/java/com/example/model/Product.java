package com.example.model;

import java.util.Date;
import java.util.Objects;

public class Product {
    
    private String productId;
    private String productName;
    private String description;
    private Double price;
    private Integer stockQuantity;
    private String status;
    private String categoryId;
    private String brandId;
    private String supplierId;
    private String warehouseId;
    private Date createdDate;
    private Date updatedDate;
    private String delYn;
    
    // Constructors
    public Product() {}
    
    public Product(String productId, String productName, Double price) {
        this.productId = productId;
        this.productName = productName;
        this.price = price;
    }
    
    // Getters and Setters
    public String getProductId() { return productId; }
    public void setProductId(String productId) { this.productId = productId; }
    
    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName; }
    
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    
    public Double getPrice() { return price; }
    public void setPrice(Double price) { this.price = price; }
    
    public Integer getStockQuantity() { return stockQuantity; }
    public void setStockQuantity(Integer stockQuantity) { this.stockQuantity = stockQuantity; }
    
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    
    public String getCategoryId() { return categoryId; }
    public void setCategoryId(String categoryId) { this.categoryId = categoryId; }
    
    public String getBrandId() { return brandId; }
    public void setBrandId(String brandId) { this.brandId = brandId; }
    
    public String getSupplierId() { return supplierId; }
    public void setSupplierId(String supplierId) { this.supplierId = supplierId; }
    
    public String getWarehouseId() { return warehouseId; }
    public void setWarehouseId(String warehouseId) { this.warehouseId = warehouseId; }
    
    public Date getCreatedDate() { return createdDate; }
    public void setCreatedDate(Date createdDate) { this.createdDate = createdDate; }
    
    public Date getUpdatedDate() { return updatedDate; }
    public void setUpdatedDate(Date updatedDate) { this.updatedDate = updatedDate; }
    
    public String getDelYn() { return delYn; }
    public void setDelYn(String delYn) { this.delYn = delYn; }
    
    // 비즈니스 로직 메서드들
    public boolean isActive() {
        return "ACTIVE".equals(this.status);
    }
    
    public boolean isInStock() {
        return this.stockQuantity != null && this.stockQuantity > 0;
    }
    
    public boolean isLowStock() {
        return this.stockQuantity != null && this.stockQuantity <= 10;
    }
    
    public boolean isOutOfStock() {
        return this.stockQuantity == null || this.stockQuantity <= 0;
    }
    
    public boolean isDeleted() {
        return "Y".equals(this.delYn);
    }
    
    public String getStockStatus() {
        if (isOutOfStock()) {
            return "품절";
        } else if (isLowStock()) {
            return "재고부족";
        } else {
            return "재고있음";
        }
    }
    
    public String getFormattedPrice() {
        if (this.price == null) {
            return "가격 미정";
        }
        return String.format("₩%,.0f", this.price);
    }
    
    public String getCategoryDisplayName() {
        if (this.categoryId == null) {
            return "미분류";
        }
        switch (this.categoryId) {
            case "CAT001": return "전자제품";
            case "CAT002": return "의류";
            case "CAT003": return "도서";
            case "CAT004": return "스포츠";
            case "CAT005": return "뷰티";
            default: return this.categoryId;
        }
    }
    
    public String getStatusDisplayName() {
        if (this.status == null) {
            return "알 수 없음";
        }
        switch (this.status.toUpperCase()) {
            case "ACTIVE": return "활성";
            case "INACTIVE": return "비활성";
            case "DISCONTINUED": return "단종";
            case "LOW_STOCK": return "재고부족";
            default: return this.status;
        }
    }
    
    public boolean isExpensive() {
        return this.price != null && this.price > 100000;
    }
    
    public boolean isCheap() {
        return this.price != null && this.price < 10000;
    }
    
    public String getPriceRange() {
        if (this.price == null) {
            return "가격 미정";
        }
        if (isCheap()) {
            return "저가";
        } else if (isExpensive()) {
            return "고가";
        } else {
            return "중가";
        }
    }
    
    public int getDaysSinceCreated() {
        if (this.createdDate == null) {
            return 0;
        }
        long diffInMillies = new java.util.Date().getTime() - this.createdDate.getTime();
        return (int) (diffInMillies / (1000 * 60 * 60 * 24));
    }
    
    public boolean isNewProduct() {
        return getDaysSinceCreated() <= 30;
    }
    
    public boolean isOldProduct() {
        return getDaysSinceCreated() > 365;
    }
    
    public String getProductAge() {
        int days = getDaysSinceCreated();
        if (days < 1) {
            return "오늘 등록";
        } else if (days < 7) {
            return days + "일 전 등록";
        } else if (days < 30) {
            return (days / 7) + "주 전 등록";
        } else if (days < 365) {
            return (days / 30) + "개월 전 등록";
        } else {
            return (days / 365) + "년 전 등록";
        }
    }
    
    public boolean hasValidPrice() {
        return this.price != null && this.price > 0;
    }
    
    public boolean hasValidStock() {
        return this.stockQuantity != null && this.stockQuantity >= 0;
    }
    
    public String getDisplayName() {
        return this.productName != null ? this.productName : this.productId;
    }
    
    public boolean canBeOrdered() {
        return isActive() && isInStock() && !isDeleted();
    }
    
    public double getStockPercentage() {
        if (this.stockQuantity == null) {
            return 0.0;
        }
        // 최대 재고를 1000으로 가정
        return Math.min(100.0, (this.stockQuantity / 1000.0) * 100.0);
    }
    
    public String getStockLevel() {
        double percentage = getStockPercentage();
        if (percentage <= 10) {
            return "매우 낮음";
        } else if (percentage <= 30) {
            return "낮음";
        } else if (percentage <= 70) {
            return "보통";
        } else {
            return "충분";
        }
    }
    
    @Override
    public String toString() {
        return "Product{" +
                "productId='" + productId + '\'' +
                ", productName='" + productName + '\'' +
                ", price=" + price +
                ", stockQuantity=" + stockQuantity +
                ", status='" + status + '\'' +
                ", categoryId='" + categoryId + '\'' +
                '}';
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Product product = (Product) o;
        return Objects.equals(productId, product.productId);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(productId);
    }
}
