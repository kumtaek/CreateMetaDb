package com.example.jpa.controller;

import com.example.jpa.entity.Product;
import com.example.jpa.entity.ProductStatus;
import com.example.jpa.service.JpaProductService;
import com.example.jpa.dto.ProductSummaryDto;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * JPA Product REST Controller
 * JpaProductService를 통한 상품 관리 REST API
 * FRONTEND_API -> API_ENTRY -> JPA Repository -> TABLE 연결 구조 테스트케이스
 */
@RestController
@RequestMapping("/api/jpa/products")
@CrossOrigin(origins = "*")
public class JpaProductController {
    
    @Autowired
    private JpaProductService jpaProductService;
    
    // 1. 기본 CRUD API
    /**
     * 상품 생성
     * FRONTEND_API: POST /api/jpa/products -> API_ENTRY: createProduct() -> JPA: ProductRepository.save() -> TABLE: PRODUCTS
     */
    @PostMapping
    public ResponseEntity<Product> createProduct(@RequestBody Product product) {
        try {
            Product createdProduct = jpaProductService.createProduct(product);
            return ResponseEntity.status(HttpStatus.CREATED).body(createdProduct);
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.CONFLICT).build();
        }
    }
    
    /**
     * 상품 조회 (ID)
     * FRONTEND_API: GET /api/jpa/products/{id} -> API_ENTRY: getProductById() -> JPA: ProductRepository.findById() -> TABLE: PRODUCTS
     */
    @GetMapping("/{id}")
    public ResponseEntity<Product> getProductById(@PathVariable Long id) {
        Optional<Product> product = jpaProductService.getProductById(id);
        return product.map(ResponseEntity::ok)
                     .orElse(ResponseEntity.notFound().build());
    }
    
    /**
     * 상품 수정
     * FRONTEND_API: PUT /api/jpa/products/{id} -> API_ENTRY: updateProduct() -> JPA: ProductRepository.save() -> TABLE: PRODUCTS
     */
    @PutMapping("/{id}")
    public ResponseEntity<Product> updateProduct(@PathVariable Long id, @RequestBody Product product) {
        try {
            product.setProductId(id);
            Product updatedProduct = jpaProductService.updateProduct(product);
            return ResponseEntity.ok(updatedProduct);
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * 상품 삭제
     * FRONTEND_API: DELETE /api/jpa/products/{id} -> API_ENTRY: deleteProduct() -> JPA: ProductRepository.deleteById() -> TABLE: PRODUCTS
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteProduct(@PathVariable Long id) {
        try {
            jpaProductService.deleteProduct(id);
            return ResponseEntity.noContent().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    // 2. 검색 API
    /**
     * 상품 코드로 조회
     * FRONTEND_API: GET /api/jpa/products/by-code/{code} -> API_ENTRY: getProductByCode() -> JPA: ProductRepository.findByProductCode() -> TABLE: PRODUCTS
     */
    @GetMapping("/by-code/{code}")
    public ResponseEntity<Product> getProductByCode(@PathVariable String code) {
        Optional<Product> product = jpaProductService.getProductByCode(code);
        return product.map(ResponseEntity::ok)
                     .orElse(ResponseEntity.notFound().build());
    }
    
    /**
     * 상태별 상품 조회
     * FRONTEND_API: GET /api/jpa/products/by-status/{status} -> API_ENTRY: getProductsByStatus() -> JPA: ProductRepository.findByStatus() -> TABLE: PRODUCTS
     */
    @GetMapping("/by-status/{status}")
    public ResponseEntity<List<Product>> getProductsByStatus(@PathVariable ProductStatus status) {
        List<Product> products = jpaProductService.getProductsByStatus(status);
        return ResponseEntity.ok(products);
    }
    
    /**
     * 카테고리별 상품 조회
     * FRONTEND_API: GET /api/jpa/products/by-category/{categoryId} -> API_ENTRY: getProductsByCategory() -> JPA: ProductRepository.findByCategoryCategoryId() -> TABLE: PRODUCTS, CATEGORIES
     */
    @GetMapping("/by-category/{categoryId}")
    public ResponseEntity<List<Product>> getProductsByCategory(@PathVariable Long categoryId) {
        List<Product> products = jpaProductService.getProductsByCategory(categoryId);
        return ResponseEntity.ok(products);
    }
    
    // 3. 상품명 검색 API
    /**
     * 상품명 검색
     * FRONTEND_API: GET /api/jpa/products/search/name?q={query} -> API_ENTRY: searchProductsByName() -> JPA: ProductRepository.findByProductNameContaining() -> TABLE: PRODUCTS
     */
    @GetMapping("/search/name")
    public ResponseEntity<List<Product>> searchProductsByName(@RequestParam String q) {
        List<Product> products = jpaProductService.searchProductsByName(q);
        return ResponseEntity.ok(products);
    }
    
    /**
     * 상품명 검색 (대소문자 무시)
     * FRONTEND_API: GET /api/jpa/products/search/name-ignore-case?q={query} -> API_ENTRY: searchProductsByNameIgnoreCase() -> JPA: ProductRepository.findByProductNameContainingIgnoreCase() -> TABLE: PRODUCTS
     */
    @GetMapping("/search/name-ignore-case")
    public ResponseEntity<List<Product>> searchProductsByNameIgnoreCase(@RequestParam String q) {
        List<Product> products = jpaProductService.searchProductsByNameIgnoreCase(q);
        return ResponseEntity.ok(products);
    }
    
    /**
     * 설명으로 검색
     * FRONTEND_API: GET /api/jpa/products/search/description?q={query} -> API_ENTRY: searchProductsByDescription() -> JPA: ProductRepository.findByDescriptionContaining() -> TABLE: PRODUCTS
     */
    @GetMapping("/search/description")
    public ResponseEntity<List<Product>> searchProductsByDescription(@RequestParam String q) {
        List<Product> products = jpaProductService.searchProductsByDescription(q);
        return ResponseEntity.ok(products);
    }
    
    // 4. 가격 기반 검색 API
    /**
     * 가격 범위 검색
     * FRONTEND_API: GET /api/jpa/products/price-range -> API_ENTRY: getProductsByPriceRange() -> JPA: ProductRepository.findByPriceBetween() -> TABLE: PRODUCTS
     */
    @GetMapping("/price-range")
    public ResponseEntity<List<Product>> getProductsByPriceRange(
            @RequestParam BigDecimal minPrice,
            @RequestParam BigDecimal maxPrice) {
        List<Product> products = jpaProductService.getProductsByPriceRange(minPrice, maxPrice);
        return ResponseEntity.ok(products);
    }
    
    /**
     * 최소 가격 이상 상품
     * FRONTEND_API: GET /api/jpa/products/price-above/{price} -> API_ENTRY: getProductsAbovePrice() -> JPA: ProductRepository.findByPriceGreaterThan() -> TABLE: PRODUCTS
     */
    @GetMapping("/price-above/{price}")
    public ResponseEntity<List<Product>> getProductsAbovePrice(@PathVariable BigDecimal price) {
        List<Product> products = jpaProductService.getProductsAbovePrice(price);
        return ResponseEntity.ok(products);
    }
    
    /**
     * 최대 가격 이하 상품
     * FRONTEND_API: GET /api/jpa/products/price-below/{price} -> API_ENTRY: getProductsBelowPrice() -> JPA: ProductRepository.findByPriceLessThanEqual() -> TABLE: PRODUCTS
     */
    @GetMapping("/price-below/{price}")
    public ResponseEntity<List<Product>> getProductsBelowPrice(@PathVariable BigDecimal price) {
        List<Product> products = jpaProductService.getProductsBelowPrice(price);
        return ResponseEntity.ok(products);
    }
    
    // 5. 재고 관리 API
    /**
     * 재고 부족 상품 조회
     * FRONTEND_API: GET /api/jpa/products/low-stock -> API_ENTRY: getLowStockProducts() -> JPA: ProductRepository.findLowStockProducts() -> TABLE: PRODUCTS
     */
    @GetMapping("/low-stock")
    public ResponseEntity<List<Product>> getLowStockProducts() {
        List<Product> products = jpaProductService.getLowStockProducts();
        return ResponseEntity.ok(products);
    }
    
    /**
     * 품절 상품 조회
     * FRONTEND_API: GET /api/jpa/products/out-of-stock -> API_ENTRY: getOutOfStockProducts() -> JPA: ProductRepository.findOutOfStockProducts() -> TABLE: PRODUCTS
     */
    @GetMapping("/out-of-stock")
    public ResponseEntity<List<Product>> getOutOfStockProducts() {
        List<Product> products = jpaProductService.getOutOfStockProducts();
        return ResponseEntity.ok(products);
    }
    
    /**
     * 재고 추가
     * FRONTEND_API: PUT /api/jpa/products/{id}/add-stock -> API_ENTRY: addStock() -> JPA: ProductRepository.addStock() -> TABLE: PRODUCTS
     */
    @PutMapping("/{id}/add-stock")
    public ResponseEntity<Integer> addStock(@PathVariable Long id, @RequestParam Integer quantity) {
        int updated = jpaProductService.addStock(id, quantity);
        return ResponseEntity.ok(updated);
    }
    
    /**
     * 재고 감소
     * FRONTEND_API: PUT /api/jpa/products/{id}/reduce-stock -> API_ENTRY: reduceStock() -> JPA: ProductRepository.reduceStock() -> TABLE: PRODUCTS
     */
    @PutMapping("/{id}/reduce-stock")
    public ResponseEntity<Integer> reduceStock(@PathVariable Long id, @RequestParam Integer quantity) {
        int updated = jpaProductService.reduceStock(id, quantity);
        return ResponseEntity.ok(updated);
    }
    
    /**
     * 재고 업데이트
     * FRONTEND_API: PUT /api/jpa/products/{id}/stock -> API_ENTRY: updateProductStock() -> JPA: ProductRepository.save() -> TABLE: PRODUCTS
     */
    @PutMapping("/{id}/stock")
    public ResponseEntity<Void> updateProductStock(@PathVariable Long id, @RequestParam Integer stock) {
        try {
            jpaProductService.updateProductStock(id, stock);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    // 6. 복합 검색 API
    /**
     * 상태와 가격 범위로 검색
     * FRONTEND_API: GET /api/jpa/products/status-price-range -> API_ENTRY: getProductsByStatusAndPriceRange() -> JPA: ProductRepository.findByStatusAndPriceBetween() -> TABLE: PRODUCTS
     */
    @GetMapping("/status-price-range")
    public ResponseEntity<List<Product>> getProductsByStatusAndPriceRange(
            @RequestParam ProductStatus status,
            @RequestParam BigDecimal minPrice,
            @RequestParam BigDecimal maxPrice) {
        List<Product> products = jpaProductService.getProductsByStatusAndPriceRange(status, minPrice, maxPrice);
        return ResponseEntity.ok(products);
    }
    
    /**
     * 카테고리와 상태로 검색
     * FRONTEND_API: GET /api/jpa/products/category-status -> API_ENTRY: getProductsByCategoryAndStatus() -> JPA: ProductRepository.findByCategoryCategoryIdAndStatus() -> TABLE: PRODUCTS, CATEGORIES
     */
    @GetMapping("/category-status")
    public ResponseEntity<List<Product>> getProductsByCategoryAndStatus(
            @RequestParam Long categoryId,
            @RequestParam ProductStatus status) {
        List<Product> products = jpaProductService.getProductsByCategoryAndStatus(categoryId, status);
        return ResponseEntity.ok(products);
    }
    
    // 7. 동적 검색 API
    /**
     * 동적 조건 검색
     * FRONTEND_API: GET /api/jpa/products/search -> API_ENTRY: searchProducts() -> JPA: ProductRepository.findProductsByDynamicCriteria() -> TABLE: PRODUCTS, CATEGORIES
     */
    @GetMapping("/search")
    public ResponseEntity<Page<Product>> searchProducts(
            @RequestParam(required = false) String name,
            @RequestParam(required = false) Long categoryId,
            @RequestParam(required = false) ProductStatus status,
            @RequestParam(required = false) BigDecimal minPrice,
            @RequestParam(required = false) BigDecimal maxPrice,
            @RequestParam(required = false) Integer minStock,
            Pageable pageable) {
        Page<Product> products = jpaProductService.searchProducts(name, categoryId, status, 
                                                                 minPrice, maxPrice, minStock, pageable);
        return ResponseEntity.ok(products);
    }
    
    // 8. 통계 API
    /**
     * 상태별 상품 수
     * FRONTEND_API: GET /api/jpa/products/count/by-status/{status} -> API_ENTRY: getProductCountByStatus() -> JPA: ProductRepository.countByStatus() -> TABLE: PRODUCTS
     */
    @GetMapping("/count/by-status/{status}")
    public ResponseEntity<Long> getProductCountByStatus(@PathVariable ProductStatus status) {
        long count = jpaProductService.getProductCountByStatus(status);
        return ResponseEntity.ok(count);
    }
    
    /**
     * 카테고리별 상품 수
     * FRONTEND_API: GET /api/jpa/products/count/by-category/{categoryId} -> API_ENTRY: getProductCountByCategory() -> JPA: ProductRepository.countByCategoryCategoryId() -> TABLE: PRODUCTS, CATEGORIES
     */
    @GetMapping("/count/by-category/{categoryId}")
    public ResponseEntity<Long> getProductCountByCategory(@PathVariable Long categoryId) {
        long count = jpaProductService.getProductCountByCategory(categoryId);
        return ResponseEntity.ok(count);
    }
    
    /**
     * 상태별 평균 가격
     * FRONTEND_API: GET /api/jpa/products/average-price/by-status/{status} -> API_ENTRY: getAveragePriceByStatus() -> JPA: ProductRepository.getAveragePriceByStatus() -> TABLE: PRODUCTS
     */
    @GetMapping("/average-price/by-status/{status}")
    public ResponseEntity<BigDecimal> getAveragePriceByStatus(@PathVariable ProductStatus status) {
        BigDecimal avgPrice = jpaProductService.getAveragePriceByStatus(status);
        return ResponseEntity.ok(avgPrice);
    }
    
    /**
     * 카테고리별 최고 가격
     * FRONTEND_API: GET /api/jpa/products/max-price/by-category/{categoryId} -> API_ENTRY: getMaxPriceByCategory() -> JPA: ProductRepository.getMaxPriceByCategoryId() -> TABLE: PRODUCTS, CATEGORIES
     */
    @GetMapping("/max-price/by-category/{categoryId}")
    public ResponseEntity<BigDecimal> getMaxPriceByCategory(@PathVariable Long categoryId) {
        BigDecimal maxPrice = jpaProductService.getMaxPriceByCategory(categoryId);
        return ResponseEntity.ok(maxPrice);
    }
    
    /**
     * 전체 활성 재고
     * FRONTEND_API: GET /api/jpa/products/total-active-stock -> API_ENTRY: getTotalActiveStock() -> JPA: ProductRepository.getTotalActiveStock() -> TABLE: PRODUCTS
     */
    @GetMapping("/total-active-stock")
    public ResponseEntity<Long> getTotalActiveStock() {
        Long totalStock = jpaProductService.getTotalActiveStock();
        return ResponseEntity.ok(totalStock);
    }
    
    /**
     * 카테고리별 상품 수 통계
     * FRONTEND_API: GET /api/jpa/products/statistics/by-category -> API_ENTRY: getProductCountByCategory() -> JPA: ProductRepository.getProductCountByCategory() -> TABLE: PRODUCTS, CATEGORIES
     */
    @GetMapping("/statistics/by-category")
    public ResponseEntity<List<Object[]>> getProductCountByCategory() {
        List<Object[]> statistics = jpaProductService.getProductCountByCategory();
        return ResponseEntity.ok(statistics);
    }
    
    // 9. 특수 검색 API
    /**
     * 카테고리명으로 상품 검색
     * FRONTEND_API: GET /api/jpa/products/by-category-name/{categoryName} -> API_ENTRY: getProductsByCategoryName() -> JPA: ProductRepository.findByCategoryName() -> TABLE: PRODUCTS, CATEGORIES
     */
    @GetMapping("/by-category-name/{categoryName}")
    public ResponseEntity<List<Product>> getProductsByCategoryName(@PathVariable String categoryName) {
        List<Product> products = jpaProductService.getProductsByCategoryName(categoryName);
        return ResponseEntity.ok(products);
    }
    
    /**
     * 인기 상품 조회
     * FRONTEND_API: GET /api/jpa/products/popular -> API_ENTRY: getPopularProducts() -> JPA: ProductRepository.findPopularProducts() -> TABLE: PRODUCTS, ORDER_ITEMS, ORDERS
     */
    @GetMapping("/popular")
    public ResponseEntity<List<Product>> getPopularProducts(@RequestParam Long minOrderCount) {
        List<Product> products = jpaProductService.getPopularProducts(minOrderCount);
        return ResponseEntity.ok(products);
    }
    
    /**
     * 주문된 적 없는 상품
     * FRONTEND_API: GET /api/jpa/products/never-ordered -> API_ENTRY: getNeverOrderedProducts() -> JPA: ProductRepository.findNeverOrderedProducts() -> TABLE: PRODUCTS, ORDER_ITEMS
     */
    @GetMapping("/never-ordered")
    public ResponseEntity<List<Product>> getNeverOrderedProducts() {
        List<Product> products = jpaProductService.getNeverOrderedProducts();
        return ResponseEntity.ok(products);
    }
    
    /**
     * 특정 날짜 이후 주문된 상품
     * FRONTEND_API: GET /api/jpa/products/ordered-after -> API_ENTRY: getProductsOrderedAfterDate() -> JPA: ProductRepository.findProductsOrderedAfterDate() -> TABLE: PRODUCTS, ORDER_ITEMS, ORDERS
     */
    @GetMapping("/ordered-after")
    public ResponseEntity<List<Product>> getProductsOrderedAfterDate(@RequestParam String date) {
        LocalDateTime dateTime = LocalDateTime.parse(date);
        List<Product> products = jpaProductService.getProductsOrderedAfterDate(dateTime);
        return ResponseEntity.ok(products);
    }
    
    // 10. 상태 변경 API
    /**
     * 상품 활성화
     * FRONTEND_API: PUT /api/jpa/products/{id}/activate -> API_ENTRY: activateProduct() -> JPA: ProductRepository.save() -> TABLE: PRODUCTS
     */
    @PutMapping("/{id}/activate")
    public ResponseEntity<Void> activateProduct(@PathVariable Long id) {
        try {
            jpaProductService.activateProduct(id);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * 상품 비활성화
     * FRONTEND_API: PUT /api/jpa/products/{id}/deactivate -> API_ENTRY: deactivateProduct() -> JPA: ProductRepository.save() -> TABLE: PRODUCTS
     */
    @PutMapping("/{id}/deactivate")
    public ResponseEntity<Void> deactivateProduct(@PathVariable Long id) {
        try {
            jpaProductService.deactivateProduct(id);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * 가격 업데이트
     * FRONTEND_API: PUT /api/jpa/products/{id}/price -> API_ENTRY: updateProductPrice() -> JPA: ProductRepository.save() -> TABLE: PRODUCTS
     */
    @PutMapping("/{id}/price")
    public ResponseEntity<Void> updateProductPrice(@PathVariable Long id, @RequestParam BigDecimal price) {
        try {
            jpaProductService.updateProductPrice(id, price);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    // 11. DTO 프로젝션 API
    /**
     * 카테고리별 상품 요약 정보
     * FRONTEND_API: GET /api/jpa/products/summaries/by-category/{categoryId} -> API_ENTRY: getProductSummariesByCategory() -> JPA: ProductRepository.findProductSummariesByCategoryId() -> TABLE: PRODUCTS, CATEGORIES
     */
    @GetMapping("/summaries/by-category/{categoryId}")
    public ResponseEntity<List<ProductSummaryDto>> getProductSummariesByCategory(@PathVariable Long categoryId) {
        List<ProductSummaryDto> summaries = jpaProductService.getProductSummariesByCategory(categoryId);
        return ResponseEntity.ok(summaries);
    }
    
    // 12. 전체 목록 API
    /**
     * 전체 상품 목록
     * FRONTEND_API: GET /api/jpa/products -> API_ENTRY: getAllProducts() -> JPA: ProductRepository.findAll() -> TABLE: PRODUCTS
     */
    @GetMapping
    public ResponseEntity<List<Product>> getAllProducts() {
        List<Product> products = jpaProductService.getAllProducts();
        return ResponseEntity.ok(products);
    }
}

