package com.example.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.util.Map;

/**
 * 마이크로서비스 컨트롤러 - 서비스 분리 예시
 * 프론트엔드에서 하나의 API를 호출하지만 내부적으로 여러 서비스를 조합하는 경우
 */
@RestController
@RequestMapping("/api")
public class MicroserviceController {

    /**
     * 통합 사용자 정보 조회
     * FRONTEND_API: GET /api/user-profile -> API_ENTRY: GET /internal/user-service/profile
     */
    @GetMapping("/user-profile")
    public ResponseEntity<Map<String, Object>> getUserProfile(@RequestParam Long userId) {
        // 내부적으로 여러 서비스 조합:
        // 1. /internal/user-service/users/{userId}
        // 2. /internal/profile-service/profiles/{userId}
        // 3. /internal/preference-service/preferences/{userId}
        return ResponseEntity.ok().build();
    }

    /**
     * 통합 주문 정보 조회
     * FRONTEND_API: GET /api/order-details -> API_ENTRY: GET /internal/order-service/details
     */
    @GetMapping("/order-details")
    public ResponseEntity<Map<String, Object>> getOrderDetails(@RequestParam Long orderId) {
        // 내부적으로 여러 서비스 조합:
        // 1. /internal/order-service/orders/{orderId}
        // 2. /internal/product-service/products/{productId}
        // 3. /internal/user-service/users/{userId}
        return ResponseEntity.ok().build();
    }

    /**
     * 통합 대시보드 데이터
     * FRONTEND_API: GET /api/dashboard -> API_ENTRY: GET /internal/analytics-service/dashboard
     */
    @GetMapping("/dashboard")
    public ResponseEntity<Map<String, Object>> getDashboardData() {
        // 내부적으로 여러 서비스 조합:
        // 1. /internal/analytics-service/statistics
        // 2. /internal/notification-service/unread-count
        // 3. /internal/recommendation-service/suggestions
        return ResponseEntity.ok().build();
    }

    /**
     * 통합 검색
     * FRONTEND_API: GET /api/search -> API_ENTRY: GET /internal/search-service/global
     */
    @GetMapping("/search")
    public ResponseEntity<Map<String, Object>> globalSearch(@RequestParam String query) {
        // 내부적으로 여러 서비스 조합:
        // 1. /internal/search-service/users?q={query}
        // 2. /internal/search-service/products?q={query}
        // 3. /internal/search-service/orders?q={query}
        return ResponseEntity.ok().build();
    }

    /**
     * 통합 알림 발송
     * FRONTEND_API: POST /api/notify -> API_ENTRY: POST /internal/notification-service/send
     */
    @PostMapping("/notify")
    public ResponseEntity<Map<String, Object>> sendNotification(@RequestBody Map<String, Object> notificationData) {
        // 내부적으로 여러 서비스 조합:
        // 1. /internal/notification-service/email
        // 2. /internal/notification-service/sms
        // 3. /internal/notification-service/push
        return ResponseEntity.ok().build();
    }
}
