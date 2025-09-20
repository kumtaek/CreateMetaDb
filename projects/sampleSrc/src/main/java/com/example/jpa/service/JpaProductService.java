package com.example.jpa.service;

import com.example.jpa.entity.Product;
import com.example.jpa.entity.ProductStatus;
import com.example.jpa.entity.Category;
import com.example.jpa.repository.ProductRepository;
import com.example.jpa.repository.CategoryRepository;
import com.example.jpa.dto.ProductSummaryDto;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * JPA 기반 Product Service
 * ProductRepository를 활용한 상품 관리 서비스
 */
@Service
@Transactional
public class JpaProductService {
    
    @Autowired
    private ProductRepository productRepository;
    
    @Autowired
    private CategoryRepository categoryRepository;
    
    // 1. 기본 CRUD 작업
    public Product createProduct(Product product) {
        // 상품 코드 중복 체크
        if (product.getProductCode() != null && 
            productRepository.findByProductCode(product.getProductCode()).isPresent()) {
            throw new RuntimeException("Product code already exists: " + product.getProductCode());
        }
        
        return productRepository.save(product);
    }
    
    @Transactional(readOnly = true)
    public Optional<Product> getProductById(Long productId) {
        return productRepository.findById(productId);
    }
    
    @Transactional(readOnly = true)
    public Optional<Product> getProductByCode(String productCode) {
        return productRepository.findByProductCode(productCode);
    }
    
    public Product updateProduct(Product product) {
        if (!productRepository.existsById(product.getProductId())) {
            throw new RuntimeException("Product not found: " + product.getProductId());
        }
        return productRepository.save(product);
    }
    
    public void deleteProduct(Long productId) {
        if (!productRepository.existsById(productId)) {
            throw new RuntimeException("Product not found: " + productId);
        }
        productRepository.deleteById(productId);
    }
    
    // 2. 상품 검색 기능
    @Transactional(readOnly = true)
    public List<Product> getProductsByStatus(ProductStatus status) {
        return productRepository.findByStatus(status);
    }
    
    @Transactional(readOnly = true)
    public List<Product> getProductsByCategory(Long categoryId) {
        return productRepository.findByCategoryCategoryId(categoryId);
    }
    
    @Transactional(readOnly = true)
    public List<Product> searchProductsByName(String name) {
        return productRepository.findByProductNameContaining(name);
    }
    
    @Transactional(readOnly = true)
    public List<Product> searchProductsByNameIgnoreCase(String name) {
        return productRepository.findByProductNameContainingIgnoreCase(name);
    }
    
    @Transactional(readOnly = true)
    public List<Product> searchProductsByDescription(String description) {
        return productRepository.findByDescriptionContaining(description);
    }
    
    // 3. 가격 기반 검색
    @Transactional(readOnly = true)
    public List<Product> getProductsByPriceRange(BigDecimal minPrice, BigDecimal maxPrice) {
        return productRepository.findByPriceBetween(minPrice, maxPrice);
    }
    
    @Transactional(readOnly = true)
    public List<Product> getProductsAbovePrice(BigDecimal price) {
        return productRepository.findByPriceGreaterThan(price);
    }
    
    @Transactional(readOnly = true)
    public List<Product> getProductsBelowPrice(BigDecimal price) {
        return productRepository.findByPriceLessThanEqual(price);
    }
    
    // 4. 재고 관리 기능
    @Transactional(readOnly = true)
    public List<Product> getLowStockProducts() {
        return productRepository.findLowStockProducts();
    }
    
    @Transactional(readOnly = true)
    public List<Product> getOutOfStockProducts() {
        return productRepository.findOutOfStockProducts();
    }
    
    @Transactional(readOnly = true)
    public List<Product> getProductsWithStockBelow(Integer quantity) {
        return productRepository.findByStockQuantityLessThan(quantity);
    }
    
    @Transactional(readOnly = true)
    public List<Product> getProductsWithStockAbove(Integer quantity) {
        return productRepository.findByStockQuantityGreaterThanEqual(quantity);
    }
    
    // 5. 재고 업데이트
    public int addStock(Long productId, Integer quantity) {
        return productRepository.addStock(productId, quantity);
    }
    
    public int reduceStock(Long productId, Integer quantity) {
        return productRepository.reduceStock(productId, quantity);
    }
    
    public int updateOutOfStockProducts() {
        return productRepository.updateOutOfStockProducts();
    }
    
    // 6. 복합 검색
    @Transactional(readOnly = true)
    public List<Product> getProductsByStatusAndPriceRange(ProductStatus status, BigDecimal minPrice, BigDecimal maxPrice) {
        return productRepository.findByStatusAndPriceBetween(status, minPrice, maxPrice);
    }
    
    @Transactional(readOnly = true)
    public List<Product> getProductsByCategoryAndStatus(Long categoryId, ProductStatus status) {
        return productRepository.findByCategoryCategoryIdAndStatus(categoryId, status);
    }
    
    @Transactional(readOnly = true)
    public List<Product> getExpensiveProductsWithStock(BigDecimal minPrice, Integer minStock) {
        return productRepository.findExpensiveProductsWithStock(minPrice, minStock);
    }
    
    // 7. 동적 검색
    @Transactional(readOnly = true)
    public Page<Product> searchProducts(String name, Long categoryId, ProductStatus status, 
                                       BigDecimal minPrice, BigDecimal maxPrice, 
                                       Integer minStock, Pageable pageable) {
        return productRepository.findProductsByDynamicCriteria(name, categoryId, status, 
                                                              minPrice, maxPrice, minStock, pageable);
    }
    
    // 8. 페이징 검색
    @Transactional(readOnly = true)
    public Page<Product> getProductsByStatusAndName(ProductStatus status, String name, Pageable pageable) {
        return productRepository.findByStatusAndProductNameContaining(status, name, pageable);
    }
    
    // 9. 정렬된 목록
    @Transactional(readOnly = true)
    public List<Product> getProductsByStatusOrderByDate(ProductStatus status) {
        return productRepository.findByStatusOrderByCreatedAtDesc(status);
    }
    
    @Transactional(readOnly = true)
    public List<Product> getProductsByCategoryOrderByPrice(Long categoryId) {
        return productRepository.findByCategoryCategoryIdOrderByPriceAsc(categoryId);
    }
    
    @Transactional(readOnly = true)
    public List<Product> getProductsByStatusOrderByStock(ProductStatus status) {
        return productRepository.findByStatusOrderByStockQuantityDesc(status);
    }
    
    // 10. 통계 기능
    @Transactional(readOnly = true)
    public long getProductCountByStatus(ProductStatus status) {
        return productRepository.countByStatus(status);
    }
    
    @Transactional(readOnly = true)
    public long getProductCountByCategory(Long categoryId) {
        return productRepository.countByCategoryCategoryId(categoryId);
    }
    
    @Transactional(readOnly = true)
    public long getProductCountByPriceRange(BigDecimal minPrice, BigDecimal maxPrice) {
        return productRepository.countByPriceBetween(minPrice, maxPrice);
    }
    
    @Transactional(readOnly = true)
    public BigDecimal getAveragePriceByStatus(ProductStatus status) {
        return productRepository.getAveragePriceByStatus(status);
    }
    
    @Transactional(readOnly = true)
    public BigDecimal getMaxPriceByCategory(Long categoryId) {
        return productRepository.getMaxPriceByCategoryId(categoryId);
    }
    
    @Transactional(readOnly = true)
    public Long getTotalActiveStock() {
        return productRepository.getTotalActiveStock();
    }
    
    @Transactional(readOnly = true)
    public List<Object[]> getProductCountByCategory() {
        return productRepository.getProductCountByCategory();
    }
    
    @Transactional(readOnly = true)
    public List<Object[]> getAveragePriceByStatus() {
        return productRepository.getAveragePriceByStatus();
    }
    
    // 11. 카테고리 관련
    @Transactional(readOnly = true)
    public List<Product> getProductsByStatusWithCategory(ProductStatus status) {
        return productRepository.findByStatusWithCategory(status);
    }
    
    @Transactional(readOnly = true)
    public List<Product> getProductsByCategoryName(String categoryName) {
        return productRepository.findByCategoryName(categoryName);
    }
    
    @Transactional(readOnly = true)
    public List<Product> getProductsInActiveCategories() {
        return productRepository.findProductsInActiveCategories();
    }
    
    // 12. 주문 관련
    @Transactional(readOnly = true)
    public List<Product> getProductsOrderedAfterDate(LocalDateTime fromDate) {
        return productRepository.findProductsOrderedAfterDate(fromDate);
    }
    
    @Transactional(readOnly = true)
    public List<Product> getPopularProducts(Long minOrderCount) {
        return productRepository.findPopularProducts(minOrderCount);
    }
    
    @Transactional(readOnly = true)
    public List<Product> getNeverOrderedProducts() {
        return productRepository.findNeverOrderedProducts();
    }
    
    // 13. 상태 변경
    public void activateProduct(Long productId) {
        Optional<Product> productOpt = productRepository.findById(productId);
        if (productOpt.isPresent()) {
            Product product = productOpt.get();
            product.setStatus(ProductStatus.ACTIVE);
            productRepository.save(product);
        } else {
            throw new RuntimeException("Product not found: " + productId);
        }
    }
    
    public void deactivateProduct(Long productId) {
        Optional<Product> productOpt = productRepository.findById(productId);
        if (productOpt.isPresent()) {
            Product product = productOpt.get();
            product.setStatus(ProductStatus.INACTIVE);
            productRepository.save(product);
        } else {
            throw new RuntimeException("Product not found: " + productId);
        }
    }
    
    public int updateProductStatus(ProductStatus newStatus, ProductStatus oldStatus) {
        return productRepository.updateProductStatus(newStatus, oldStatus);
    }
    
    // 14. DTO 프로젝션
    @Transactional(readOnly = true)
    public List<ProductSummaryDto> getProductSummariesByCategory(Long categoryId) {
        return productRepository.findProductSummariesByCategoryId(categoryId);
    }
    
    // 15. 비즈니스 로직
    public void updateProductStock(Long productId, Integer newStock) {
        Optional<Product> productOpt = productRepository.findById(productId);
        if (productOpt.isPresent()) {
            Product product = productOpt.get();
            product.setStockQuantity(newStock);
            
            // 재고에 따른 상태 자동 변경
            if (newStock <= 0) {
                product.setStatus(ProductStatus.OUT_OF_STOCK);
            } else if (product.getStatus() == ProductStatus.OUT_OF_STOCK) {
                product.setStatus(ProductStatus.ACTIVE);
            }
            
            productRepository.save(product);
        } else {
            throw new RuntimeException("Product not found: " + productId);
        }
    }
    
    public void updateProductPrice(Long productId, BigDecimal newPrice) {
        Optional<Product> productOpt = productRepository.findById(productId);
        if (productOpt.isPresent()) {
            Product product = productOpt.get();
            product.setPrice(newPrice);
            productRepository.save(product);
        } else {
            throw new RuntimeException("Product not found: " + productId);
        }
    }
    
    @Transactional(readOnly = true)
    public List<Product> getAllProducts() {
        return productRepository.findAll();
    }
}

