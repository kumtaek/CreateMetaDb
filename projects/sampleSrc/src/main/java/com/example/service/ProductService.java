package com.example.service;

import com.example.model.Product;
import java.util.List;
import java.util.Map;

public interface ProductService {
    
    List<Product> getProductsByCondition(Map<String, Object> params);
    
    List<Product> getProductsByAdvancedCondition(Map<String, Object> params);
    
    List<Product> getProductsByCategory(String categoryId);
    
    Product getProductById(String productId);
    
    int updateProductStock(String productId, int quantity);
    
    int updateProductDynamic(Product product);
    
    int deleteProductsByCondition(Map<String, Object> params);
}
