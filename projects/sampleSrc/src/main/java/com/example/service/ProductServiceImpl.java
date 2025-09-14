package com.example.service;

import com.example.mapper.ProductMapper;
import com.example.model.Product;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.*;
import java.util.stream.Collectors;

@Service
@Transactional
public class ProductServiceImpl implements ProductService {
    
    @Autowired
    private ProductMapper productMapper;
    
    @Override
    public List<Product> getProductsByCondition(Map<String, Object> params) {
        // 입력 파라미터 검증 및 정제
        Map<String, Object> validatedParams = validateProductSearchParams(params);
        
        // 비즈니스 로직: 상품 상태별 필터링
        List<Product> products = productMapper.selectProductsByCondition(validatedParams);
        
        // 비즈니스 로직: 재고 부족 상품 표시
        return enhanceProductDisplay(products);
    }
    
    @Override
    public List<Product> getProductsByAdvancedCondition(Map<String, Object> params) {
        // 고급 검색 조건 검증
        validateAdvancedProductSearchParams(params);
        
        // 비즈니스 로직: 가격 범위 검증
        if (params.containsKey("minPrice") && params.containsKey("maxPrice")) {
            Double minPrice = (Double) params.get("minPrice");
            Double maxPrice = (Double) params.get("maxPrice");
            if (minPrice > maxPrice) {
                throw new IllegalArgumentException("최소 가격은 최대 가격보다 클 수 없습니다.");
            }
        }
        
        // 비즈니스 로직: 재고 범위 검증
        validateStockRange(params);
        
        List<Product> products = productMapper.selectProductsByAdvancedCondition(params);
        
        // 비즈니스 로직: 상품별 할인율 적용
        return applyDiscountLogic(products);
    }
    
    @Override
    public List<Product> getProductsByCategory(String categoryId) {
        // 카테고리 ID 검증
        if (!isValidCategoryId(categoryId)) {
            throw new IllegalArgumentException("유효하지 않은 카테고리 ID입니다: " + categoryId);
        }
        
        List<Product> products = productMapper.selectProductsByCategory(categoryId);
        
        // 비즈니스 로직: 카테고리별 특별 처리
        return applyCategorySpecificLogic(products, categoryId);
    }
    
    @Override
    public Product getProductById(String productId) {
        if (!StringUtils.hasText(productId)) {
            throw new IllegalArgumentException("상품 ID가 올바르지 않습니다.");
        }
        
        Product product = productMapper.selectProductById(productId);
        if (product == null) {
            throw new RuntimeException("상품을 찾을 수 없습니다. ID: " + productId);
        }
        
        // 비즈니스 로직: 상품 조회 수 증가
        incrementProductViewCount(product);
        
        // 비즈니스 로직: 관련 상품 정보 추가
        enhanceProductWithRelatedInfo(product);
        
        return product;
    }
    
    @Override
    public int updateProductStock(String productId, int quantity) {
        if (!StringUtils.hasText(productId)) {
            throw new IllegalArgumentException("상품 ID가 올바르지 않습니다.");
        }
        
        // 비즈니스 로직: 재고 업데이트 전 검증
        Product product = productMapper.selectProductById(productId);
        if (product == null) {
            throw new RuntimeException("상품을 찾을 수 없습니다: " + productId);
        }
        
        // 비즈니스 로직: 재고 부족 경고
        int currentStock = product.getStockQuantity() != null ? product.getStockQuantity() : 0;
        int newStock = currentStock + quantity;
        
        if (newStock < 0) {
            throw new RuntimeException("재고가 부족합니다. 현재 재고: " + currentStock + ", 요청 수량: " + quantity);
        }
        
        // 비즈니스 로직: 재고 업데이트 로그
        logStockUpdate(productId, currentStock, newStock, quantity);
        
        int result = productMapper.updateProductStock(productId, quantity);
        
        // 비즈니스 로직: 재고 부족 알림
        if (newStock <= 10) {
            sendLowStockAlert(product, newStock);
        }
        
        return result;
    }
    
    @Override
    public int updateProductDynamic(Product product) {
        if (product == null || !StringUtils.hasText(product.getProductId())) {
            throw new IllegalArgumentException("상품 정보가 올바르지 않습니다.");
        }
        
        // 비즈니스 로직: 상품명 중복 검사
        if (StringUtils.hasText(product.getProductName())) {
            validateProductNameUniqueness(product.getProductName(), product.getProductId());
        }
        
        // 비즈니스 로직: 가격 검증
        if (product.getPrice() != null) {
            validateProductPrice(product.getPrice());
        }
        
        // 비즈니스 로직: 재고 검증
        if (product.getStockQuantity() != null) {
            validateStockQuantity(product.getStockQuantity());
        }
        
        // 비즈니스 로직: 업데이트 전 로그 기록
        logProductUpdate(product);
        
        int result = productMapper.updateProductDynamic(product);
        
        // 비즈니스 로직: 업데이트 후 캐시 무효화
        invalidateProductCache(product.getProductId());
        
        return result;
    }
    
    @Override
    public int deleteProductsByCondition(Map<String, Object> params) {
        // 삭제 조건 검증
        validateDeleteProductConditions(params);
        
        // 비즈니스 로직: 삭제 전 상품 수 확인
        int productCount = productMapper.countProductsByCondition(params);
        if (productCount == 0) {
            throw new RuntimeException("삭제할 상품이 없습니다.");
        }
        
        // 비즈니스 로직: 활성 상품 삭제 방지
        preventActiveProductDeletion(params);
        
        // 비즈니스 로직: 삭제 전 로그 기록
        logBulkProductDelete(params, productCount);
        
        int result = productMapper.deleteProductsByCondition(params);
        
        // 비즈니스 로직: 삭제 후 관련 데이터 정리
        cleanupRelatedProductData(params);
        
        return result;
    }
    
    // 비즈니스 로직 메서드들
    private Map<String, Object> validateProductSearchParams(Map<String, Object> params) {
        Map<String, Object> validated = new HashMap<>();
        
        if (params.containsKey("name")) {
            String name = (String) params.get("name");
            if (StringUtils.hasText(name)) {
                validated.put("name", name.trim().replaceAll("[<>\"']", ""));
            }
        }
        
        if (params.containsKey("category")) {
            String category = (String) params.get("category");
            if (StringUtils.hasText(category) && isValidCategoryId(category)) {
                validated.put("category", category.toUpperCase());
            }
        }
        
        if (params.containsKey("status")) {
            String status = (String) params.get("status");
            if (isValidProductStatus(status)) {
                validated.put("status", status.toUpperCase());
            }
        }
        
        return validated;
    }
    
    private List<Product> enhanceProductDisplay(List<Product> products) {
        return products.stream().map(product -> {
            // 비즈니스 로직: 재고 부족 표시
            if (product.getStockQuantity() != null && product.getStockQuantity() <= 5) {
                product.setStatus("LOW_STOCK");
            }
            
            // 비즈니스 로직: 가격 포맷팅
            if (product.getPrice() != null) {
                product.setDescription(formatPrice(product.getPrice()));
            }
            
            return product;
        }).collect(Collectors.toList());
    }
    
    private void validateAdvancedProductSearchParams(Map<String, Object> params) {
        if (params.containsKey("minPrice")) {
            Double minPrice = (Double) params.get("minPrice");
            if (minPrice < 0) {
                throw new IllegalArgumentException("가격은 0 이상이어야 합니다.");
            }
        }
        
        if (params.containsKey("maxPrice")) {
            Double maxPrice = (Double) params.get("maxPrice");
            if (maxPrice < 0) {
                throw new IllegalArgumentException("가격은 0 이상이어야 합니다.");
            }
        }
    }
    
    private void validateStockRange(Map<String, Object> params) {
        if (params.containsKey("minStock")) {
            Integer minStock = (Integer) params.get("minStock");
            if (minStock < 0) {
                throw new IllegalArgumentException("재고는 0 이상이어야 합니다.");
            }
        }
        
        if (params.containsKey("maxStock")) {
            Integer maxStock = (Integer) params.get("maxStock");
            if (maxStock < 0) {
                throw new IllegalArgumentException("재고는 0 이상이어야 합니다.");
            }
        }
    }
    
    private List<Product> applyDiscountLogic(List<Product> products) {
        return products.stream().map(product -> {
            // 비즈니스 로직: 카테고리별 할인율 적용
            double discountRate = getDiscountRateByCategory(product.getCategoryId());
            if (discountRate > 0) {
                double originalPrice = product.getPrice();
                double discountedPrice = originalPrice * (1 - discountRate);
                product.setPrice(discountedPrice);
            }
            
            return product;
        }).collect(Collectors.toList());
    }
    
    private boolean isValidCategoryId(String categoryId) {
        return Arrays.asList("CAT001", "CAT002", "CAT003", "CAT004", "CAT005").contains(categoryId);
    }
    
    private List<Product> applyCategorySpecificLogic(List<Product> products, String categoryId) {
        switch (categoryId) {
            case "CAT001": // 전자제품
                return products.stream()
                        .filter(product -> product.getPrice() != null && product.getPrice() > 0)
                        .collect(Collectors.toList());
            case "CAT002": // 의류
                return products.stream()
                        .filter(product -> product.getStockQuantity() != null && product.getStockQuantity() > 0)
                        .collect(Collectors.toList());
            case "CAT003": // 도서
                return products.stream()
                        .filter(product -> "ACTIVE".equals(product.getStatus()))
                        .collect(Collectors.toList());
            default:
                return products;
        }
    }
    
    private void incrementProductViewCount(Product product) {
        // 비즈니스 로직: 상품 조회 수 증가
        product.setUpdatedDate(new Date());
        // 실제로는 별도 테이블에 조회 로그를 기록할 수 있음
    }
    
    private void enhanceProductWithRelatedInfo(Product product) {
        // 비즈니스 로직: 관련 상품 정보 추가
        if (product.getCategoryId() != null) {
            List<Product> relatedProducts = productMapper.selectProductsByCategory(product.getCategoryId());
            // 관련 상품 정보를 product 객체에 추가할 수 있음
        }
    }
    
    private void logStockUpdate(String productId, int currentStock, int newStock, int quantity) {
        System.out.println("Stock updated: Product=" + productId + 
                          ", Current=" + currentStock + 
                          ", New=" + newStock + 
                          ", Change=" + quantity);
    }
    
    private void sendLowStockAlert(Product product, int currentStock) {
        System.out.println("LOW STOCK ALERT: Product=" + product.getProductName() + 
                          ", Current Stock=" + currentStock);
    }
    
    private void validateProductNameUniqueness(String productName, String productId) {
        // 비즈니스 로직: 상품명 중복 검사
        Map<String, Object> params = new HashMap<>();
        params.put("name", productName);
        List<Product> existingProducts = productMapper.selectProductsByCondition(params);
        
        boolean isDuplicate = existingProducts.stream()
                .anyMatch(product -> !product.getProductId().equals(productId));
        
        if (isDuplicate) {
            throw new RuntimeException("이미 사용 중인 상품명입니다: " + productName);
        }
    }
    
    private void validateProductPrice(Double price) {
        if (price < 0) {
            throw new IllegalArgumentException("상품 가격은 0 이상이어야 합니다.");
        }
        if (price > 1000000) {
            throw new IllegalArgumentException("상품 가격이 너무 높습니다.");
        }
    }
    
    private void validateStockQuantity(Integer stockQuantity) {
        if (stockQuantity < 0) {
            throw new IllegalArgumentException("재고 수량은 0 이상이어야 합니다.");
        }
        if (stockQuantity > 10000) {
            throw new IllegalArgumentException("재고 수량이 너무 많습니다.");
        }
    }
    
    private void logProductUpdate(Product product) {
        System.out.println("Product updated: ID=" + product.getProductId() + 
                          ", Name=" + product.getProductName() + 
                          ", Time=" + new Date());
    }
    
    private void invalidateProductCache(String productId) {
        System.out.println("Product cache invalidated: " + productId);
    }
    
    private void validateDeleteProductConditions(Map<String, Object> params) {
        if (params.isEmpty()) {
            throw new IllegalArgumentException("삭제 조건이 없습니다.");
        }
    }
    
    private void preventActiveProductDeletion(Map<String, Object> params) {
        if ("ACTIVE".equals(params.get("status"))) {
            throw new RuntimeException("활성 상품은 삭제할 수 없습니다.");
        }
    }
    
    private void logBulkProductDelete(Map<String, Object> params, int productCount) {
        System.out.println("Bulk product delete initiated: " + params + ", Count: " + productCount);
    }
    
    private void cleanupRelatedProductData(Map<String, Object> params) {
        System.out.println("Related product data cleanup completed for: " + params);
    }
    
    private boolean isValidProductStatus(String status) {
        return Arrays.asList("ACTIVE", "INACTIVE", "DISCONTINUED", "LOW_STOCK").contains(status.toUpperCase());
    }
    
    private String formatPrice(Double price) {
        return String.format("₩%,.0f", price);
    }
    
    private double getDiscountRateByCategory(String categoryId) {
        switch (categoryId) {
            case "CAT001": return 0.1; // 전자제품 10% 할인
            case "CAT002": return 0.15; // 의류 15% 할인
            case "CAT003": return 0.05; // 도서 5% 할인
            default: return 0.0;
        }
    }
}
