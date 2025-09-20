package com.example.jpa.controller;

import com.example.jpa.entity.Order;
import com.example.jpa.entity.OrderStatus;
import com.example.jpa.service.JpaOrderService;
import com.example.jpa.dto.OrderSummaryDto;
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
 * JPA Order REST Controller
 * JpaOrderService를 통한 주문 관리 REST API
 * FRONTEND_API -> API_ENTRY -> JPA Repository -> TABLE 연결 구조 테스트케이스
 */
@RestController
@RequestMapping("/api/jpa/orders")
@CrossOrigin(origins = "*")
public class JpaOrderController {
    
    @Autowired
    private JpaOrderService jpaOrderService;
    
    // 1. 기본 CRUD API
    /**
     * 주문 생성
     * FRONTEND_API: POST /api/jpa/orders -> API_ENTRY: createOrder() -> JPA: OrderRepository.save() -> TABLE: ORDERS
     */
    @PostMapping
    public ResponseEntity<Order> createOrder(@RequestBody Order order) {
        try {
            Order createdOrder = jpaOrderService.createOrder(order);
            return ResponseEntity.status(HttpStatus.CREATED).body(createdOrder);
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.CONFLICT).build();
        }
    }
    
    /**
     * 주문 조회 (ID)
     * FRONTEND_API: GET /api/jpa/orders/{id} -> API_ENTRY: getOrderById() -> JPA: OrderRepository.findById() -> TABLE: ORDERS
     */
    @GetMapping("/{id}")
    public ResponseEntity<Order> getOrderById(@PathVariable Long id) {
        Optional<Order> order = jpaOrderService.getOrderById(id);
        return order.map(ResponseEntity::ok)
                   .orElse(ResponseEntity.notFound().build());
    }
    
    /**
     * 주문 수정
     * FRONTEND_API: PUT /api/jpa/orders/{id} -> API_ENTRY: updateOrder() -> JPA: OrderRepository.save() -> TABLE: ORDERS
     */
    @PutMapping("/{id}")
    public ResponseEntity<Order> updateOrder(@PathVariable Long id, @RequestBody Order order) {
        try {
            order.setOrderId(id);
            Order updatedOrder = jpaOrderService.updateOrder(order);
            return ResponseEntity.ok(updatedOrder);
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * 주문 삭제
     * FRONTEND_API: DELETE /api/jpa/orders/{id} -> API_ENTRY: deleteOrder() -> JPA: OrderRepository.deleteById() -> TABLE: ORDERS
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteOrder(@PathVariable Long id) {
        try {
            jpaOrderService.deleteOrder(id);
            return ResponseEntity.noContent().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    // 2. 주문번호 조회 API
    /**
     * 주문번호로 조회
     * FRONTEND_API: GET /api/jpa/orders/by-number/{orderNumber} -> API_ENTRY: getOrderByOrderNumber() -> JPA: OrderRepository.findByOrderNumber() -> TABLE: ORDERS
     */
    @GetMapping("/by-number/{orderNumber}")
    public ResponseEntity<Order> getOrderByOrderNumber(@PathVariable String orderNumber) {
        Optional<Order> order = jpaOrderService.getOrderByOrderNumber(orderNumber);
        return order.map(ResponseEntity::ok)
                   .orElse(ResponseEntity.notFound().build());
    }
    
    /**
     * 주문 상세 정보 조회
     * FRONTEND_API: GET /api/jpa/orders/details/{orderNumber} -> API_ENTRY: getOrderWithDetails() -> JPA: OrderRepository.findByOrderNumberWithDetails() -> TABLE: ORDERS, USERS, ORDER_ITEMS
     */
    @GetMapping("/details/{orderNumber}")
    public ResponseEntity<Order> getOrderWithDetails(@PathVariable String orderNumber) {
        Optional<Order> order = jpaOrderService.getOrderWithDetails(orderNumber);
        return order.map(ResponseEntity::ok)
                   .orElse(ResponseEntity.notFound().build());
    }
    
    /**
     * 주문 아이템과 함께 조회
     * FRONTEND_API: GET /api/jpa/orders/{id}/with-items -> API_ENTRY: getOrderWithItems() -> JPA: OrderRepository.findByIdWithOrderItems() -> TABLE: ORDERS, ORDER_ITEMS
     */
    @GetMapping("/{id}/with-items")
    public ResponseEntity<Order> getOrderWithItems(@PathVariable Long id) {
        Optional<Order> order = jpaOrderService.getOrderWithItems(id);
        return order.map(ResponseEntity::ok)
                   .orElse(ResponseEntity.notFound().build());
    }
    
    // 3. 상태별 조회 API
    /**
     * 상태별 주문 조회
     * FRONTEND_API: GET /api/jpa/orders/by-status/{status} -> API_ENTRY: getOrdersByStatus() -> JPA: OrderRepository.findByOrderStatus() -> TABLE: ORDERS
     */
    @GetMapping("/by-status/{status}")
    public ResponseEntity<List<Order>> getOrdersByStatus(@PathVariable OrderStatus status) {
        List<Order> orders = jpaOrderService.getOrdersByStatus(status);
        return ResponseEntity.ok(orders);
    }
    
    /**
     * 상태별 주문 (사용자 정보 포함)
     * FRONTEND_API: GET /api/jpa/orders/by-status-with-user/{status} -> API_ENTRY: getOrdersByStatusWithUser() -> JPA: OrderRepository.findByOrderStatusWithUser() -> TABLE: ORDERS, USERS
     */
    @GetMapping("/by-status-with-user/{status}")
    public ResponseEntity<List<Order>> getOrdersByStatusWithUser(@PathVariable OrderStatus status) {
        List<Order> orders = jpaOrderService.getOrdersByStatusWithUser(status);
        return ResponseEntity.ok(orders);
    }
    
    // 4. 사용자별 조회 API
    /**
     * 사용자별 주문 조회
     * FRONTEND_API: GET /api/jpa/orders/by-user/{userId} -> API_ENTRY: getOrdersByUserId() -> JPA: OrderRepository.findByUserUserId() -> TABLE: ORDERS, USERS
     */
    @GetMapping("/by-user/{userId}")
    public ResponseEntity<List<Order>> getOrdersByUserId(@PathVariable Long userId) {
        List<Order> orders = jpaOrderService.getOrdersByUserId(userId);
        return ResponseEntity.ok(orders);
    }
    
    /**
     * 사용자별 주문 (금액순 정렬)
     * FRONTEND_API: GET /api/jpa/orders/by-user-ordered/{userId} -> API_ENTRY: getOrdersByUserIdOrderByAmount() -> JPA: OrderRepository.findByUserUserIdOrderByTotalAmountDesc() -> TABLE: ORDERS, USERS
     */
    @GetMapping("/by-user-ordered/{userId}")
    public ResponseEntity<List<Order>> getOrdersByUserIdOrderByAmount(@PathVariable Long userId) {
        List<Order> orders = jpaOrderService.getOrdersByUserIdOrderByAmount(userId);
        return ResponseEntity.ok(orders);
    }
    
    // 5. 날짜 기반 조회 API
    /**
     * 기간별 주문 조회
     * FRONTEND_API: GET /api/jpa/orders/between-dates -> API_ENTRY: getOrdersBetweenDates() -> JPA: OrderRepository.findByOrderDateBetween() -> TABLE: ORDERS
     */
    @GetMapping("/between-dates")
    public ResponseEntity<List<Order>> getOrdersBetweenDates(
            @RequestParam String startDate,
            @RequestParam String endDate) {
        LocalDateTime start = LocalDateTime.parse(startDate);
        LocalDateTime end = LocalDateTime.parse(endDate);
        List<Order> orders = jpaOrderService.getOrdersBetweenDates(start, end);
        return ResponseEntity.ok(orders);
    }
    
    /**
     * 특정 날짜 이후 주문
     * FRONTEND_API: GET /api/jpa/orders/after-date -> API_ENTRY: getOrdersAfterDate() -> JPA: OrderRepository.findByOrderDateAfter() -> TABLE: ORDERS
     */
    @GetMapping("/after-date")
    public ResponseEntity<List<Order>> getOrdersAfterDate(@RequestParam String date) {
        LocalDateTime dateTime = LocalDateTime.parse(date);
        List<Order> orders = jpaOrderService.getOrdersAfterDate(dateTime);
        return ResponseEntity.ok(orders);
    }
    
    // 6. 금액 기반 조회 API
    /**
     * 최소 금액 이상 주문
     * FRONTEND_API: GET /api/jpa/orders/above-amount/{amount} -> API_ENTRY: getOrdersAboveAmount() -> JPA: OrderRepository.findByTotalAmountGreaterThan() -> TABLE: ORDERS
     */
    @GetMapping("/above-amount/{amount}")
    public ResponseEntity<List<Order>> getOrdersAboveAmount(@PathVariable BigDecimal amount) {
        List<Order> orders = jpaOrderService.getOrdersAboveAmount(amount);
        return ResponseEntity.ok(orders);
    }
    
    /**
     * 금액 범위별 주문
     * FRONTEND_API: GET /api/jpa/orders/amount-range -> API_ENTRY: getOrdersByAmountRange() -> JPA: OrderRepository.findByTotalAmountBetween() -> TABLE: ORDERS
     */
    @GetMapping("/amount-range")
    public ResponseEntity<List<Order>> getOrdersByAmountRange(
            @RequestParam BigDecimal minAmount,
            @RequestParam BigDecimal maxAmount) {
        List<Order> orders = jpaOrderService.getOrdersByAmountRange(minAmount, maxAmount);
        return ResponseEntity.ok(orders);
    }
    
    // 7. 동적 검색 API
    /**
     * 동적 조건 검색
     * FRONTEND_API: GET /api/jpa/orders/search -> API_ENTRY: searchOrders() -> JPA: OrderRepository.findOrdersByDynamicCriteria() -> TABLE: ORDERS, USERS
     */
    @GetMapping("/search")
    public ResponseEntity<Page<Order>> searchOrders(
            @RequestParam(required = false) Long userId,
            @RequestParam(required = false) OrderStatus status,
            @RequestParam(required = false) String fromDate,
            @RequestParam(required = false) String toDate,
            @RequestParam(required = false) BigDecimal minAmount,
            @RequestParam(required = false) BigDecimal maxAmount,
            Pageable pageable) {
        
        LocalDateTime from = fromDate != null ? LocalDateTime.parse(fromDate) : null;
        LocalDateTime to = toDate != null ? LocalDateTime.parse(toDate) : null;
        
        Page<Order> orders = jpaOrderService.searchOrders(userId, status, from, to, minAmount, maxAmount, pageable);
        return ResponseEntity.ok(orders);
    }
    
    // 8. 통계 API
    /**
     * 상태별 주문 수
     * FRONTEND_API: GET /api/jpa/orders/count/by-status/{status} -> API_ENTRY: getOrderCountByStatus() -> JPA: OrderRepository.countByOrderStatus() -> TABLE: ORDERS
     */
    @GetMapping("/count/by-status/{status}")
    public ResponseEntity<Long> getOrderCountByStatus(@PathVariable OrderStatus status) {
        long count = jpaOrderService.getOrderCountByStatus(status);
        return ResponseEntity.ok(count);
    }
    
    /**
     * 사용자별 주문 수
     * FRONTEND_API: GET /api/jpa/orders/count/by-user/{userId} -> API_ENTRY: getOrderCountByUserId() -> JPA: OrderRepository.countByUserUserId() -> TABLE: ORDERS, USERS
     */
    @GetMapping("/count/by-user/{userId}")
    public ResponseEntity<Long> getOrderCountByUserId(@PathVariable Long userId) {
        long count = jpaOrderService.getOrderCountByUserId(userId);
        return ResponseEntity.ok(count);
    }
    
    /**
     * 사용자 총 주문 금액
     * FRONTEND_API: GET /api/jpa/orders/total-amount/by-user/{userId} -> API_ENTRY: getUserTotalAmount() -> JPA: OrderRepository.getTotalAmountByUserId() -> TABLE: ORDERS, USERS
     */
    @GetMapping("/total-amount/by-user/{userId}")
    public ResponseEntity<BigDecimal> getUserTotalAmount(@PathVariable Long userId) {
        BigDecimal totalAmount = jpaOrderService.getUserTotalAmount(userId);
        return ResponseEntity.ok(totalAmount);
    }
    
    /**
     * 상태별 평균 주문 금액
     * FRONTEND_API: GET /api/jpa/orders/average-amount/by-status/{status} -> API_ENTRY: getAverageOrderAmountByStatus() -> JPA: OrderRepository.getAverageOrderAmountByStatus() -> TABLE: ORDERS
     */
    @GetMapping("/average-amount/by-status/{status}")
    public ResponseEntity<BigDecimal> getAverageOrderAmountByStatus(@PathVariable OrderStatus status) {
        BigDecimal avgAmount = jpaOrderService.getAverageOrderAmountByStatus(status);
        return ResponseEntity.ok(avgAmount);
    }
    
    /**
     * 상태별 주문 통계
     * FRONTEND_API: GET /api/jpa/orders/statistics/by-status -> API_ENTRY: getOrderCountByStatus() -> JPA: OrderRepository.getOrderCountByStatus() -> TABLE: ORDERS
     */
    @GetMapping("/statistics/by-status")
    public ResponseEntity<List<Object[]>> getOrderCountByStatus() {
        List<Object[]> statistics = jpaOrderService.getOrderCountByStatus();
        return ResponseEntity.ok(statistics);
    }
    
    /**
     * 일별 주문 통계
     * FRONTEND_API: GET /api/jpa/orders/statistics/daily -> API_ENTRY: getDailyOrderCount() -> JPA: OrderRepository.getDailyOrderCount() -> TABLE: ORDERS
     */
    @GetMapping("/statistics/daily")
    public ResponseEntity<List<Object[]>> getDailyOrderCount(@RequestParam String fromDate) {
        LocalDateTime dateTime = LocalDateTime.parse(fromDate);
        List<Object[]> statistics = jpaOrderService.getDailyOrderCount(dateTime);
        return ResponseEntity.ok(statistics);
    }
    
    /**
     * 최고 고객 통계
     * FRONTEND_API: GET /api/jpa/orders/statistics/top-customers -> API_ENTRY: getTopCustomersByTotalAmount() -> JPA: OrderRepository.getTopCustomersByTotalAmount() -> TABLE: ORDERS, USERS
     */
    @GetMapping("/statistics/top-customers")
    public ResponseEntity<List<Object[]>> getTopCustomersByTotalAmount() {
        List<Object[]> statistics = jpaOrderService.getTopCustomersByTotalAmount();
        return ResponseEntity.ok(statistics);
    }
    
    // 9. 특수 검색 API
    /**
     * 프리미엄 사용자 주문
     * FRONTEND_API: GET /api/jpa/orders/premium-users -> API_ENTRY: getOrdersByPremiumUsers() -> JPA: OrderRepository.findOrdersByPremiumUsers() -> TABLE: ORDERS, USERS
     */
    @GetMapping("/premium-users")
    public ResponseEntity<List<Order>> getOrdersByPremiumUsers() {
        List<Order> orders = jpaOrderService.getOrdersByPremiumUsers();
        return ResponseEntity.ok(orders);
    }
    
    /**
     * 카테고리별 상품이 포함된 주문
     * FRONTEND_API: GET /api/jpa/orders/containing-category/{categoryName} -> API_ENTRY: getOrdersContainingProductsFromCategory() -> JPA: OrderRepository.findOrdersContainingProductsFromCategory() -> TABLE: ORDERS, ORDER_ITEMS, PRODUCTS, CATEGORIES
     */
    @GetMapping("/containing-category/{categoryName}")
    public ResponseEntity<List<Order>> getOrdersContainingProductsFromCategory(@PathVariable String categoryName) {
        List<Order> orders = jpaOrderService.getOrdersContainingProductsFromCategory(categoryName);
        return ResponseEntity.ok(orders);
    }
    
    /**
     * 특정 상품이 포함된 주문
     * FRONTEND_API: GET /api/jpa/orders/containing-product -> API_ENTRY: getOrdersContainingProduct() -> JPA: OrderRepository.findOrdersContainingProduct() -> TABLE: ORDERS, ORDER_ITEMS, PRODUCTS
     */
    @GetMapping("/containing-product")
    public ResponseEntity<List<Order>> getOrdersContainingProduct(@RequestParam String productName) {
        List<Order> orders = jpaOrderService.getOrdersContainingProduct(productName);
        return ResponseEntity.ok(orders);
    }
    
    /**
     * 최소 아이템 수 이상 주문
     * FRONTEND_API: GET /api/jpa/orders/minimum-items/{count} -> API_ENTRY: getOrdersWithMinimumItems() -> JPA: OrderRepository.findOrdersWithMinimumItems() -> TABLE: ORDERS, ORDER_ITEMS
     */
    @GetMapping("/minimum-items/{count}")
    public ResponseEntity<List<Order>> getOrdersWithMinimumItems(@PathVariable int count) {
        List<Order> orders = jpaOrderService.getOrdersWithMinimumItems(count);
        return ResponseEntity.ok(orders);
    }
    
    // 10. 주문 상태 변경 API
    /**
     * 주문 확인
     * FRONTEND_API: PUT /api/jpa/orders/{id}/confirm -> API_ENTRY: confirmOrder() -> JPA: OrderRepository.save() -> TABLE: ORDERS
     */
    @PutMapping("/{id}/confirm")
    public ResponseEntity<Void> confirmOrder(@PathVariable Long id) {
        try {
            jpaOrderService.confirmOrder(id);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * 주문 취소
     * FRONTEND_API: PUT /api/jpa/orders/{id}/cancel -> API_ENTRY: cancelOrder() -> JPA: OrderRepository.cancelOrder() -> TABLE: ORDERS
     */
    @PutMapping("/{id}/cancel")
    public ResponseEntity<Integer> cancelOrder(@PathVariable Long id) {
        int updated = jpaOrderService.cancelOrder(id);
        return ResponseEntity.ok(updated);
    }
    
    /**
     * 주문 처리
     * FRONTEND_API: PUT /api/jpa/orders/{id}/process -> API_ENTRY: processOrder() -> JPA: OrderRepository.save() -> TABLE: ORDERS
     */
    @PutMapping("/{id}/process")
    public ResponseEntity<Void> processOrder(@PathVariable Long id) {
        try {
            jpaOrderService.processOrder(id);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * 주문 배송
     * FRONTEND_API: PUT /api/jpa/orders/{id}/ship -> API_ENTRY: shipOrder() -> JPA: OrderRepository.save() -> TABLE: ORDERS
     */
    @PutMapping("/{id}/ship")
    public ResponseEntity<Void> shipOrder(@PathVariable Long id) {
        try {
            jpaOrderService.shipOrder(id);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * 주문 완료
     * FRONTEND_API: PUT /api/jpa/orders/{id}/complete -> API_ENTRY: completeOrder() -> JPA: OrderRepository.save() -> TABLE: ORDERS
     */
    @PutMapping("/{id}/complete")
    public ResponseEntity<Void> completeOrder(@PathVariable Long id) {
        try {
            jpaOrderService.completeOrder(id);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * 배송 주소 변경
     * FRONTEND_API: PUT /api/jpa/orders/{id}/shipping-address -> API_ENTRY: updateShippingAddress() -> JPA: OrderRepository.updateShippingAddress() -> TABLE: ORDERS
     */
    @PutMapping("/{id}/shipping-address")
    public ResponseEntity<Integer> updateShippingAddress(@PathVariable Long id, @RequestParam String address) {
        int updated = jpaOrderService.updateShippingAddress(id, address);
        return ResponseEntity.ok(updated);
    }
    
    // 11. 비즈니스 로직 API
    /**
     * 주문 총액 업데이트
     * FRONTEND_API: PUT /api/jpa/orders/{id}/total -> API_ENTRY: updateOrderTotal() -> JPA: OrderRepository.save() -> TABLE: ORDERS
     */
    @PutMapping("/{id}/total")
    public ResponseEntity<Void> updateOrderTotal(@PathVariable Long id, @RequestParam BigDecimal total) {
        try {
            jpaOrderService.updateOrderTotal(id, total);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * 할인 적용
     * FRONTEND_API: PUT /api/jpa/orders/{id}/discount -> API_ENTRY: applyDiscount() -> JPA: OrderRepository.save() -> TABLE: ORDERS
     */
    @PutMapping("/{id}/discount")
    public ResponseEntity<Void> applyDiscount(@PathVariable Long id, @RequestParam BigDecimal discountAmount) {
        try {
            jpaOrderService.applyDiscount(id, discountAmount);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    // 12. DTO 프로젝션 API
    /**
     * 주문 요약 정보 조회
     * FRONTEND_API: GET /api/jpa/orders/summaries/by-status/{status} -> API_ENTRY: getOrderSummariesByStatus() -> JPA: OrderRepository.findOrderSummariesByStatus() -> TABLE: ORDERS, USERS
     */
    @GetMapping("/summaries/by-status/{status}")
    public ResponseEntity<List<OrderSummaryDto>> getOrderSummariesByStatus(@PathVariable OrderStatus status) {
        List<OrderSummaryDto> summaries = jpaOrderService.getOrderSummariesByStatus(status);
        return ResponseEntity.ok(summaries);
    }
    
    // 13. 전체 목록 API
    /**
     * 전체 주문 목록
     * FRONTEND_API: GET /api/jpa/orders -> API_ENTRY: getAllOrders() -> JPA: OrderRepository.findAll() -> TABLE: ORDERS
     */
    @GetMapping
    public ResponseEntity<List<Order>> getAllOrders() {
        List<Order> orders = jpaOrderService.getAllOrders();
        return ResponseEntity.ok(orders);
    }
}

