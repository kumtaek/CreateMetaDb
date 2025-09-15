package com.example.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.util.Map;

/**
 * 버전별 API 컨트롤러 - 버전 관리 예시
 * 같은 기능이지만 다른 버전의 API를 제공하는 경우
 */
@RestController
@RequestMapping("/api")
public class VersionedController {

    /**
     * 사용자 조회 - v1 API
     * FRONTEND_API: GET /api/users -> API_ENTRY: GET /api/v1/users
     */
    @GetMapping("/v1/users")
    public ResponseEntity<Map<String, Object>> getUsersV1() {
        // v1 사용자 조회 로직
        return ResponseEntity.ok().build();
    }

    /**
     * 사용자 조회 - v2 API (개선된 버전)
     * FRONTEND_API: GET /api/users -> API_ENTRY: GET /api/v2/users
     */
    @GetMapping("/v2/users")
    public ResponseEntity<Map<String, Object>> getUsersV2() {
        // v2 사용자 조회 로직 (개선된 기능)
        return ResponseEntity.ok().build();
    }

    /**
     * 제품 조회 - v1 API
     * FRONTEND_API: GET /api/products -> API_ENTRY: GET /api/v1/products
     */
    @GetMapping("/v1/products")
    public ResponseEntity<Map<String, Object>> getProductsV1() {
        // v1 제품 조회 로직
        return ResponseEntity.ok().build();
    }

    /**
     * 제품 조회 - v2 API (페이징 지원)
     * FRONTEND_API: GET /api/products -> API_ENTRY: GET /api/v2/products
     */
    @GetMapping("/v2/products")
    public ResponseEntity<Map<String, Object>> getProductsV2(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        // v2 제품 조회 로직 (페이징 지원)
        return ResponseEntity.ok().build();
    }

    /**
     * 주문 조회 - v1 API
     * FRONTEND_API: GET /api/orders -> API_ENTRY: GET /api/v1/orders
     */
    @GetMapping("/v1/orders")
    public ResponseEntity<Map<String, Object>> getOrdersV1() {
        // v1 주문 조회 로직
        return ResponseEntity.ok().build();
    }

    /**
     * 주문 조회 - v2 API (필터링 지원)
     * FRONTEND_API: GET /api/orders -> API_ENTRY: GET /api/v2/orders
     */
    @GetMapping("/v2/orders")
    public ResponseEntity<Map<String, Object>> getOrdersV2(
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String dateFrom,
            @RequestParam(required = false) String dateTo) {
        // v2 주문 조회 로직 (필터링 지원)
        return ResponseEntity.ok().build();
    }
}
