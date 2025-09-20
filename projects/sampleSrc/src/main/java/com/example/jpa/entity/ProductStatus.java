package com.example.jpa.entity;

/**
 * 상품 상태 Enum
 */
public enum ProductStatus {
    ACTIVE("판매중"),
    INACTIVE("판매중지"),
    OUT_OF_STOCK("품절"),
    DISCONTINUED("단종"),
    PENDING("승인대기");
    
    private final String description;
    
    ProductStatus(String description) {
        this.description = description;
    }
    
    public String getDescription() {
        return description;
    }
    
    public static ProductStatus fromString(String status) {
        for (ProductStatus productStatus : ProductStatus.values()) {
            if (productStatus.name().equalsIgnoreCase(status)) {
                return productStatus;
            }
        }
        return ACTIVE; // 기본값
    }
}

