package com.example.jpa.entity;

import javax.persistence.*;
import java.time.LocalDateTime;
import java.util.List;

/**
 * JPA Category Entity
 * TABLE: CATEGORIES
 */
@Entity
@Table(name = "CATEGORIES")
public class Category {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "CATEGORY_ID")
    private Long categoryId;
    
    @Column(name = "CATEGORY_NAME", nullable = false, length = 100)
    private String categoryName;
    
    @Column(name = "CATEGORY_CODE", unique = true, length = 20)
    private String categoryCode;
    
    @Column(name = "DESCRIPTION", length = 500)
    private String description;
    
    @Column(name = "DISPLAY_ORDER")
    private Integer displayOrder;
    
    @Column(name = "IS_ACTIVE")
    private Boolean isActive;
    
    @Column(name = "CREATED_AT")
    private LocalDateTime createdAt;
    
    @Column(name = "UPDATED_AT")
    private LocalDateTime updatedAt;
    
    // JPA 연관관계 - 부모 카테고리
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "PARENT_CATEGORY_ID")
    private Category parentCategory;
    
    // JPA 연관관계 - 자식 카테고리들
    @OneToMany(mappedBy = "parentCategory", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Category> subCategories;
    
    // JPA 연관관계 - 카테고리의 상품들
    @OneToMany(mappedBy = "category", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Product> products;
    
    // 기본 생성자
    public Category() {}
    
    // 생성자
    public Category(String categoryName, String categoryCode) {
        this.categoryName = categoryName;
        this.categoryCode = categoryCode;
        this.isActive = true;
        this.displayOrder = 0;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }
    
    // JPA 생명주기 콜백
    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
        if (this.isActive == null) {
            this.isActive = true;
        }
    }
    
    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
    
    // Getter/Setter
    public Long getCategoryId() {
        return categoryId;
    }
    
    public void setCategoryId(Long categoryId) {
        this.categoryId = categoryId;
    }
    
    public String getCategoryName() {
        return categoryName;
    }
    
    public void setCategoryName(String categoryName) {
        this.categoryName = categoryName;
    }
    
    public String getCategoryCode() {
        return categoryCode;
    }
    
    public void setCategoryCode(String categoryCode) {
        this.categoryCode = categoryCode;
    }
    
    public String getDescription() {
        return description;
    }
    
    public void setDescription(String description) {
        this.description = description;
    }
    
    public Integer getDisplayOrder() {
        return displayOrder;
    }
    
    public void setDisplayOrder(Integer displayOrder) {
        this.displayOrder = displayOrder;
    }
    
    public Boolean getIsActive() {
        return isActive;
    }
    
    public void setIsActive(Boolean isActive) {
        this.isActive = isActive;
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
    
    public Category getParentCategory() {
        return parentCategory;
    }
    
    public void setParentCategory(Category parentCategory) {
        this.parentCategory = parentCategory;
    }
    
    public List<Category> getSubCategories() {
        return subCategories;
    }
    
    public void setSubCategories(List<Category> subCategories) {
        this.subCategories = subCategories;
    }
    
    public List<Product> getProducts() {
        return products;
    }
    
    public void setProducts(List<Product> products) {
        this.products = products;
    }
    
    // 비즈니스 메서드
    public boolean isActive() {
        return Boolean.TRUE.equals(this.isActive);
    }
    
    public boolean hasSubCategories() {
        return this.subCategories != null && !this.subCategories.isEmpty();
    }
    
    public boolean hasProducts() {
        return this.products != null && !this.products.isEmpty();
    }
    
    public int getProductCount() {
        return this.products != null ? this.products.size() : 0;
    }
}

