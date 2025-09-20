package com.example.jpa.repository;

import com.example.jpa.entity.Product;
import com.example.jpa.entity.ProductStatus;
import com.example.jpa.entity.Category;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * JPA Product Repository
 * 상품 관련 다양한 JPA 쿼리 패턴 테스트케이스
 */
@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {
    
    // 1. 기본 메서드명 기반 쿼리
    Optional<Product> findByProductCode(String productCode);
    
    List<Product> findByStatus(ProductStatus status);
    
    List<Product> findByCategory(Category category);
    
    List<Product> findByCategoryCategoryId(Long categoryId);
    
    List<Product> findByStatusAndCategory(ProductStatus status, Category category);
    
    // 2. 가격 범위 검색
    List<Product> findByPriceBetween(BigDecimal minPrice, BigDecimal maxPrice);
    
    List<Product> findByPriceGreaterThan(BigDecimal price);
    
    List<Product> findByPriceLessThanEqual(BigDecimal price);
    
    // 3. 재고 관련 검색
    List<Product> findByStockQuantityLessThan(Integer quantity);
    
    List<Product> findByStockQuantityGreaterThanEqual(Integer quantity);
    
    List<Product> findByStockQuantityIsNull();
    
    @Query("SELECT p FROM Product p WHERE p.stockQuantity <= p.minStockLevel")
    List<Product> findLowStockProducts();
    
    @Query("SELECT p FROM Product p WHERE p.stockQuantity = 0 OR p.stockQuantity IS NULL")
    List<Product> findOutOfStockProducts();
    
    // 4. 상품명 검색
    List<Product> findByProductNameContaining(String name);
    
    List<Product> findByProductNameContainingIgnoreCase(String name);
    
    List<Product> findByDescriptionContaining(String description);
    
    // 5. 복합 조건 검색
    List<Product> findByStatusAndPriceBetween(ProductStatus status, BigDecimal minPrice, BigDecimal maxPrice);
    
    List<Product> findByCategoryCategoryIdAndStatus(Long categoryId, ProductStatus status);
    
    Page<Product> findByStatusAndProductNameContaining(ProductStatus status, String name, Pageable pageable);
    
    // 6. 정렬 쿼리
    List<Product> findByStatusOrderByCreatedAtDesc(ProductStatus status);
    
    List<Product> findByCategoryCategoryIdOrderByPriceAsc(Long categoryId);
    
    List<Product> findByStatusOrderByStockQuantityDesc(ProductStatus status);
    
    // 7. Count 쿼리
    long countByStatus(ProductStatus status);
    
    long countByCategory(Category category);
    
    long countByCategoryCategoryId(Long categoryId);
    
    long countByPriceBetween(BigDecimal minPrice, BigDecimal maxPrice);
    
    // 8. @Query - JPQL 쿼리
    @Query("SELECT p FROM Product p JOIN FETCH p.category WHERE p.status = :status")
    List<Product> findByStatusWithCategory(@Param("status") ProductStatus status);
    
    @Query("SELECT p FROM Product p WHERE p.category.categoryName = :categoryName")
    List<Product> findByCategoryName(@Param("categoryName") String categoryName);
    
    @Query("SELECT p FROM Product p WHERE p.price >= :minPrice AND p.stockQuantity > :minStock")
    List<Product> findExpensiveProductsWithStock(@Param("minPrice") BigDecimal minPrice, 
                                                @Param("minStock") Integer minStock);
    
    // 9. 집계 쿼리
    @Query("SELECT AVG(p.price) FROM Product p WHERE p.status = :status")
    BigDecimal getAveragePriceByStatus(@Param("status") ProductStatus status);
    
    @Query("SELECT MAX(p.price) FROM Product p WHERE p.category.categoryId = :categoryId")
    BigDecimal getMaxPriceByCategoryId(@Param("categoryId") Long categoryId);
    
    @Query("SELECT SUM(p.stockQuantity) FROM Product p WHERE p.status = 'ACTIVE'")
    Long getTotalActiveStock();
    
    @Query("SELECT p.category.categoryName, COUNT(p) FROM Product p GROUP BY p.category.categoryName")
    List<Object[]> getProductCountByCategory();
    
    @Query("SELECT p.status, AVG(p.price) FROM Product p GROUP BY p.status")
    List<Object[]> getAveragePriceByStatus();
    
    // 10. Native SQL 쿼리
    @Query(value = "SELECT * FROM PRODUCTS p WHERE p.PRODUCT_NAME LIKE %?1% AND p.PRICE > ?2", 
           nativeQuery = true)
    List<Product> findByNameAndPriceNative(String name, BigDecimal minPrice);
    
    @Query(value = "SELECT p.*, c.CATEGORY_NAME FROM PRODUCTS p " +
                   "JOIN CATEGORIES c ON p.CATEGORY_ID = c.CATEGORY_ID " +
                   "WHERE p.STATUS = :status ORDER BY p.CREATED_AT DESC", 
           nativeQuery = true)
    List<Product> findByStatusWithCategoryNameNative(@Param("status") String status);
    
    // 11. @Modifying 업데이트 쿼리
    @Modifying
    @Query("UPDATE Product p SET p.stockQuantity = p.stockQuantity + :quantity WHERE p.productId = :productId")
    int addStock(@Param("productId") Long productId, @Param("quantity") Integer quantity);
    
    @Modifying
    @Query("UPDATE Product p SET p.stockQuantity = p.stockQuantity - :quantity " +
           "WHERE p.productId = :productId AND p.stockQuantity >= :quantity")
    int reduceStock(@Param("productId") Long productId, @Param("quantity") Integer quantity);
    
    @Modifying
    @Query("UPDATE Product p SET p.status = :newStatus WHERE p.status = :oldStatus")
    int updateProductStatus(@Param("newStatus") ProductStatus newStatus, 
                           @Param("oldStatus") ProductStatus oldStatus);
    
    @Modifying
    @Query("UPDATE Product p SET p.status = 'OUT_OF_STOCK' WHERE p.stockQuantity = 0")
    int updateOutOfStockProducts();
    
    // 12. 서브쿼리
    @Query("SELECT p FROM Product p WHERE p.productId IN " +
           "(SELECT oi.product.productId FROM OrderItem oi WHERE oi.order.orderDate >= :fromDate)")
    List<Product> findProductsOrderedAfterDate(@Param("fromDate") LocalDateTime fromDate);
    
    @Query("SELECT p FROM Product p WHERE p.category.categoryId IN " +
           "(SELECT c.categoryId FROM Category c WHERE c.isActive = true)")
    List<Product> findProductsInActiveCategories();
    
    // 13. 동적 검색 쿼리
    @Query("SELECT p FROM Product p WHERE " +
           "(:name IS NULL OR p.productName LIKE %:name%) AND " +
           "(:categoryId IS NULL OR p.category.categoryId = :categoryId) AND " +
           "(:status IS NULL OR p.status = :status) AND " +
           "(:minPrice IS NULL OR p.price >= :minPrice) AND " +
           "(:maxPrice IS NULL OR p.price <= :maxPrice) AND " +
           "(:minStock IS NULL OR p.stockQuantity >= :minStock)")
    Page<Product> findProductsByDynamicCriteria(@Param("name") String name,
                                               @Param("categoryId") Long categoryId,
                                               @Param("status") ProductStatus status,
                                               @Param("minPrice") BigDecimal minPrice,
                                               @Param("maxPrice") BigDecimal maxPrice,
                                               @Param("minStock") Integer minStock,
                                               Pageable pageable);
    
    // 14. 복잡한 연관관계 쿼리
    @Query("SELECT p FROM Product p JOIN p.orderItems oi " +
           "WHERE oi.order.orderStatus = 'COMPLETED' " +
           "GROUP BY p.productId " +
           "HAVING COUNT(oi) > :minOrderCount")
    List<Product> findPopularProducts(@Param("minOrderCount") Long minOrderCount);
    
    @Query("SELECT p FROM Product p LEFT JOIN p.orderItems oi " +
           "WHERE oi.orderItemId IS NULL")
    List<Product> findNeverOrderedProducts();
    
    // 15. DTO 프로젝션
    @Query("SELECT new com.example.jpa.dto.ProductSummaryDto(p.productId, p.productName, p.price, p.stockQuantity, p.status) " +
           "FROM Product p WHERE p.category.categoryId = :categoryId")
    List<com.example.jpa.dto.ProductSummaryDto> findProductSummariesByCategoryId(@Param("categoryId") Long categoryId);
}

