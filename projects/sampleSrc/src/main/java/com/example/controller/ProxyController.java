package com.example.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.util.Map;

/**
 * 프록시/게이트웨이 컨트롤러 - 다른 URL 매핑 예시
 * 프론트엔드 URL과 실제 백엔드 URL이 다른 경우
 */
@RestController
@RequestMapping("/api")
public class ProxyController {

    /**
     * 사용자 조회 - 프록시 패턴
     * FRONTEND_API: GET /api/users -> API_ENTRY: GET /api/v1/users
     */
    @GetMapping("/users")
    public ResponseEntity<Map<String, Object>> getUsers() {
        // 내부적으로 /api/v1/users 호출
        return ResponseEntity.ok().build();
    }

    /**
     * 사용자 생성 - 프록시 패턴
     * FRONTEND_API: POST /api/users -> API_ENTRY: POST /api/v1/users
     */
    @PostMapping("/users")
    public ResponseEntity<Map<String, Object>> createUser(@RequestBody Map<String, Object> userData) {
        // 내부적으로 /api/v1/users 호출
        return ResponseEntity.ok().build();
    }

    /**
     * 제품 조회 - 게이트웨이 패턴
     * FRONTEND_API: GET /api/products -> API_ENTRY: GET /internal/product-service/products
     */
    @GetMapping("/products")
    public ResponseEntity<Map<String, Object>> getProducts() {
        // 내부적으로 /internal/product-service/products 호출
        return ResponseEntity.ok().build();
    }

    /**
     * 주문 조회 - 마이크로서비스 패턴
     * FRONTEND_API: GET /api/orders -> API_ENTRY: GET /internal/order-service/orders
     */
    @GetMapping("/orders")
    public ResponseEntity<Map<String, Object>> getOrders() {
        // 내부적으로 /internal/order-service/orders 호출
        return ResponseEntity.ok().build();
    }

    /**
     * 결제 처리 - 외부 서비스 연동
     * FRONTEND_API: POST /api/payment -> API_ENTRY: POST /external/payment-gateway/process
     */
    @PostMapping("/payment")
    public ResponseEntity<Map<String, Object>> processPayment(@RequestBody Map<String, Object> paymentData) {
        // 내부적으로 /external/payment-gateway/process 호출
        return ResponseEntity.ok().build();
    }
}
