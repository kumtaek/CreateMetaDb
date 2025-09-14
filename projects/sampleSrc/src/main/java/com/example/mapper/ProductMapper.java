package com.example.mapper;

import com.example.model.Product;
import org.apache.ibatis.annotations.Param;
import java.util.List;
import java.util.Map;

public interface ProductMapper {
    
    List<Product> selectProductsByCondition(Map<String, Object> params);
    
    List<Product> selectProductsByAdvancedCondition(Map<String, Object> params);
    
    List<Product> selectProductsByCategory(@Param("categoryId") String categoryId);
    
    Product selectProductById(@Param("productId") String productId);
    
    int updateProductStock(@Param("productId") String productId, @Param("quantity") int quantity);
    
    int updateProductDynamic(Product product);
    
    int deleteProductsByCondition(Map<String, Object> params);
    
    // 동적 INSERT 쿼리
    int insertProductDynamic(Product product);
    
    // 동적 COUNT 쿼리
    int countProductsByCondition(Map<String, Object> params);
}
