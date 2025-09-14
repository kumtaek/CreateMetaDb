package com.example.controller;

import com.example.model.Product;
import com.example.service.ProductService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Controller
@RequestMapping("/product")
public class ProductController {
    
    @Autowired
    private ProductService productService;
    
    @GetMapping("/list")
    public String getProductList(@RequestParam(required = false) String name,
                                @RequestParam(required = false) String category,
                                @RequestParam(required = false) String status,
                                Model model) {
        
        // 다이나믹 쿼리 파라미터 구성
        Map<String, Object> params = new java.util.HashMap<>();
        if (name != null && !name.trim().isEmpty()) {
            params.put("name", "%" + name + "%");
        }
        if (category != null && !category.trim().isEmpty()) {
            params.put("category", category);
        }
        if (status != null && !status.trim().isEmpty()) {
            params.put("status", status);
        }
        
        List<Product> products = productService.getProductsByCondition(params);
        model.addAttribute("products", products);
        model.addAttribute("searchParams", params);
        
        return "product/list";
    }
    
    @PostMapping("/search")
    public String searchProducts(@RequestParam Map<String, String> searchParams, Model model) {
        
        // 복잡한 다이나믹 쿼리 조건 구성
        Map<String, Object> params = new java.util.HashMap<>();
        
        if (searchParams.get("categoryId") != null) {
            params.put("categoryId", searchParams.get("categoryId"));
        }
        
        if (searchParams.get("minPrice") != null && !searchParams.get("minPrice").isEmpty()) {
            params.put("minPrice", Double.parseDouble(searchParams.get("minPrice")));
        }
        
        if (searchParams.get("maxPrice") != null && !searchParams.get("maxPrice").isEmpty()) {
            params.put("maxPrice", Double.parseDouble(searchParams.get("maxPrice")));
        }
        
        // 재고 범위 검색
        if (searchParams.get("minStock") != null && !searchParams.get("minStock").isEmpty()) {
            params.put("minStock", Integer.parseInt(searchParams.get("minStock")));
        }
        
        if (searchParams.get("maxStock") != null && !searchParams.get("maxStock").isEmpty()) {
            params.put("maxStock", Integer.parseInt(searchParams.get("maxStock")));
        }
        
        List<Product> products = productService.getProductsByAdvancedCondition(params);
        model.addAttribute("products", products);
        model.addAttribute("searchParams", searchParams);
        
        return "product/searchResult";
    }
    
    @GetMapping("/category/{categoryId}")
    public String getProductsByCategory(@PathVariable String categoryId, Model model) {
        
        // 카테고리별 다이나믹 쿼리
        List<Product> products = productService.getProductsByCategory(categoryId);
        model.addAttribute("products", products);
        model.addAttribute("categoryId", categoryId);
        
        return "product/categoryList";
    }
    
    @PostMapping("/updateStock")
    public String updateProductStock(@RequestParam String productId, 
                                   @RequestParam int quantity, 
                                   Model model) {
        
        // 동적 업데이트 쿼리
        int result = productService.updateProductStock(productId, quantity);
        model.addAttribute("result", result);
        model.addAttribute("productId", productId);
        
        return "product/updateResult";
    }
}
