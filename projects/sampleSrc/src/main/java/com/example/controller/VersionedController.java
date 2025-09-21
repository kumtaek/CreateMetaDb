package com.example.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.util.Map;

/**
 * 버전별 API 컨트롤러 - v2 API 전용
 * 프론트엔드는 단순한 경로를, 백엔드는 버전별 경로를 사용
 */
@RestController
@RequestMapping("/api/v2")
public class VersionedController {

    /**
     * 사용자 조회 - v2 API
     * FRONTEND_API: GET /api/v2/users -> API_ENTRY: GET /api/v2/users
     */
    @GetMapping("/users")
    public ResponseEntity<Map<String, Object>> getUsersV2(
            @RequestParam(defaultValue = "v2") String version) {
        // v2 API 호출: /api/v2/users
        return ResponseEntity.ok().build();
    }

    /**
     * 제품 조회 - v2 API (페이징 지원)
     * FRONTEND_API: GET /api/v2/products -> API_ENTRY: GET /api/v2/products
     */
    @GetMapping("/products")
    public ResponseEntity<Map<String, Object>> getProductsV2(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(defaultValue = "v2") String version) {
        // v2 API 호출: /api/v2/products (페이징 지원)
        return ResponseEntity.ok().build();
    }

    /**
     * 주문 조회 - v2 API (필터링 지원)
     * FRONTEND_API: GET /api/v2/orders -> API_ENTRY: GET /api/v2/orders
     */
    @GetMapping("/orders")
    public ResponseEntity<Map<String, Object>> getOrdersV2(
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String dateFrom,
            @RequestParam(required = false) String dateTo,
            @RequestParam(defaultValue = "v2") String version) {
        // v2 API 호출: /api/v2/orders (필터링 지원)
        return ResponseEntity.ok().build();
    }
}