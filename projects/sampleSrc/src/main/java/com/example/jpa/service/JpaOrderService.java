package com.example.jpa.service;

import com.example.jpa.entity.Order;
import com.example.jpa.entity.OrderStatus;
import com.example.jpa.entity.User;
import com.example.jpa.repository.OrderRepository;
import com.example.jpa.repository.UserRepository;
import com.example.jpa.dto.OrderSummaryDto;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * JPA 기반 Order Service
 * OrderRepository를 활용한 주문 관리 서비스
 */
@Service
@Transactional
public class JpaOrderService {
    
    @Autowired
    private OrderRepository orderRepository;
    
    @Autowired
    private UserRepository userRepository;
    
    // 1. 기본 CRUD 작업
    public Order createOrder(Order order) {
        // 주문번호 중복 체크
        if (order.getOrderNumber() != null && 
            orderRepository.findByOrderNumber(order.getOrderNumber()).isPresent()) {
            throw new RuntimeException("Order number already exists: " + order.getOrderNumber());
        }
        
        return orderRepository.save(order);
    }
    
    @Transactional(readOnly = true)
    public Optional<Order> getOrderById(Long orderId) {
        return orderRepository.findById(orderId);
    }
    
    @Transactional(readOnly = true)
    public Optional<Order> getOrderByOrderNumber(String orderNumber) {
        return orderRepository.findByOrderNumber(orderNumber);
    }
    
    @Transactional(readOnly = true)
    public Optional<Order> getOrderWithDetails(String orderNumber) {
        return orderRepository.findByOrderNumberWithDetails(orderNumber);
    }
    
    @Transactional(readOnly = true)
    public Optional<Order> getOrderWithItems(Long orderId) {
        return orderRepository.findByIdWithOrderItems(orderId);
    }
    
    public Order updateOrder(Order order) {
        if (!orderRepository.existsById(order.getOrderId())) {
            throw new RuntimeException("Order not found: " + order.getOrderId());
        }
        return orderRepository.save(order);
    }
    
    public void deleteOrder(Long orderId) {
        if (!orderRepository.existsById(orderId)) {
            throw new RuntimeException("Order not found: " + orderId);
        }
        orderRepository.deleteById(orderId);
    }
    
    // 2. 주문 상태별 검색
    @Transactional(readOnly = true)
    public List<Order> getOrdersByStatus(OrderStatus status) {
        return orderRepository.findByOrderStatus(status);
    }
    
    @Transactional(readOnly = true)
    public List<Order> getOrdersByStatusWithUser(OrderStatus status) {
        return orderRepository.findByOrderStatusWithUser(status);
    }
    
    @Transactional(readOnly = true)
    public List<Order> getOrdersByStatusOrderByDate(OrderStatus status) {
        return orderRepository.findByOrderStatusOrderByOrderDateDesc(status);
    }
    
    // 3. 사용자별 주문 검색
    @Transactional(readOnly = true)
    public List<Order> getOrdersByUserId(Long userId) {
        return orderRepository.findByUserUserId(userId);
    }
    
    @Transactional(readOnly = true)
    public List<Order> getOrdersByUser(User user) {
        return orderRepository.findByUser(user);
    }
    
    @Transactional(readOnly = true)
    public List<Order> getOrdersByUserIdOrderByAmount(Long userId) {
        return orderRepository.findByUserUserIdOrderByTotalAmountDesc(userId);
    }
    
    @Transactional(readOnly = true)
    public List<Order> getRecentOrdersByUserId(Long userId, Pageable pageable) {
        return orderRepository.findRecentOrdersByUserId(userId, pageable);
    }
    
    // 4. 날짜 기반 검색
    @Transactional(readOnly = true)
    public List<Order> getOrdersBetweenDates(LocalDateTime startDate, LocalDateTime endDate) {
        return orderRepository.findByOrderDateBetween(startDate, endDate);
    }
    
    @Transactional(readOnly = true)
    public List<Order> getOrdersAfterDate(LocalDateTime date) {
        return orderRepository.findByOrderDateAfter(date);
    }
    
    @Transactional(readOnly = true)
    public List<Order> getOrdersCreatedBefore(LocalDateTime date) {
        return orderRepository.findByCreatedAtBefore(date);
    }
    
    @Transactional(readOnly = true)
    public List<Order> getOrdersBetweenDatesOrderByCreated(LocalDateTime start, LocalDateTime end) {
        return orderRepository.findByOrderDateBetweenOrderByCreatedAtAsc(start, end);
    }
    
    // 5. 금액 기반 검색
    @Transactional(readOnly = true)
    public List<Order> getOrdersAboveAmount(BigDecimal amount) {
        return orderRepository.findByTotalAmountGreaterThan(amount);
    }
    
    @Transactional(readOnly = true)
    public List<Order> getOrdersByAmountRange(BigDecimal minAmount, BigDecimal maxAmount) {
        return orderRepository.findByTotalAmountBetween(minAmount, maxAmount);
    }
    
    @Transactional(readOnly = true)
    public List<Order> getOrdersWithDiscount(BigDecimal minDiscount) {
        return orderRepository.findByDiscountAmountGreaterThan(minDiscount);
    }
    
    // 6. 복합 조건 검색
    @Transactional(readOnly = true)
    public List<Order> getOrdersByStatusAndDateAfter(OrderStatus status, LocalDateTime date) {
        return orderRepository.findByOrderStatusAndOrderDateAfter(status, date);
    }
    
    @Transactional(readOnly = true)
    public List<Order> getOrdersByUserAndStatus(Long userId, OrderStatus status) {
        return orderRepository.findByUserUserIdAndOrderStatus(userId, status);
    }
    
    @Transactional(readOnly = true)
    public Page<Order> getOrdersByStatusAndAmount(OrderStatus status, BigDecimal amount, Pageable pageable) {
        return orderRepository.findByOrderStatusAndTotalAmountGreaterThan(status, amount, pageable);
    }
    
    // 7. 동적 검색
    @Transactional(readOnly = true)
    public Page<Order> searchOrders(Long userId, OrderStatus status, LocalDateTime fromDate, 
                                   LocalDateTime toDate, BigDecimal minAmount, BigDecimal maxAmount, 
                                   Pageable pageable) {
        return orderRepository.findOrdersByDynamicCriteria(userId, status, fromDate, toDate, 
                                                          minAmount, maxAmount, pageable);
    }
    
    // 8. 통계 기능
    @Transactional(readOnly = true)
    public long getOrderCountByStatus(OrderStatus status) {
        return orderRepository.countByOrderStatus(status);
    }
    
    @Transactional(readOnly = true)
    public long getOrderCountByUserId(Long userId) {
        return orderRepository.countByUserUserId(userId);
    }
    
    @Transactional(readOnly = true)
    public long getOrderCountAfterDate(LocalDateTime date) {
        return orderRepository.countByOrderDateAfter(date);
    }
    
    @Transactional(readOnly = true)
    public long getOrderCountAboveAmount(BigDecimal amount) {
        return orderRepository.countByTotalAmountGreaterThan(amount);
    }
    
    @Transactional(readOnly = true)
    public long getUserOrderCountByStatus(Long userId, OrderStatus status) {
        return orderRepository.countUserOrdersByStatus(userId, status);
    }
    
    @Transactional(readOnly = true)
    public BigDecimal getUserTotalAmount(Long userId) {
        return orderRepository.getTotalAmountByUserId(userId);
    }
    
    @Transactional(readOnly = true)
    public BigDecimal getAverageOrderAmountByStatus(OrderStatus status) {
        return orderRepository.getAverageOrderAmountByStatus(status);
    }
    
    // 9. 집계 및 분석
    @Transactional(readOnly = true)
    public List<Object[]> getOrderCountByStatus() {
        return orderRepository.getOrderCountByStatus();
    }
    
    @Transactional(readOnly = true)
    public List<Object[]> getDailyOrderCount(LocalDateTime fromDate) {
        return orderRepository.getDailyOrderCount(fromDate);
    }
    
    @Transactional(readOnly = true)
    public List<Object[]> getTopCustomersByTotalAmount() {
        return orderRepository.getTopCustomersByTotalAmount();
    }
    
    // 10. 특수 검색
    @Transactional(readOnly = true)
    public List<Order> getOrdersByPremiumUsers() {
        return orderRepository.findOrdersByPremiumUsers();
    }
    
    @Transactional(readOnly = true)
    public List<Order> getOrdersContainingProductsFromCategory(String categoryName) {
        return orderRepository.findOrdersContainingProductsFromCategory(categoryName);
    }
    
    @Transactional(readOnly = true)
    public List<Order> getOrdersContainingProduct(String productName) {
        return orderRepository.findOrdersContainingProduct(productName);
    }
    
    @Transactional(readOnly = true)
    public List<Order> getOrdersWithMinimumItems(int minItemCount) {
        return orderRepository.findOrdersWithMinimumItems(minItemCount);
    }
    
    @Transactional(readOnly = true)
    public List<Order> getOrdersWithInconsistentTotals() {
        return orderRepository.findOrdersWithInconsistentTotals();
    }
    
    @Transactional(readOnly = true)
    public List<Order> getRecentOrdersByStatuses(LocalDateTime fromDate, List<OrderStatus> statuses) {
        return orderRepository.findRecentOrdersByStatuses(fromDate, statuses);
    }
    
    // 11. 주문 상태 변경
    public void confirmOrder(Long orderId) {
        Optional<Order> orderOpt = orderRepository.findById(orderId);
        if (orderOpt.isPresent()) {
            Order order = orderOpt.get();
            if (order.getOrderStatus().canTransitionTo(OrderStatus.CONFIRMED)) {
                order.setOrderStatus(OrderStatus.CONFIRMED);
                orderRepository.save(order);
            } else {
                throw new RuntimeException("Cannot confirm order in current status: " + order.getOrderStatus());
            }
        } else {
            throw new RuntimeException("Order not found: " + orderId);
        }
    }
    
    public int cancelOrder(Long orderId) {
        return orderRepository.cancelOrder(orderId);
    }
    
    public void processOrder(Long orderId) {
        Optional<Order> orderOpt = orderRepository.findById(orderId);
        if (orderOpt.isPresent()) {
            Order order = orderOpt.get();
            if (order.getOrderStatus().canTransitionTo(OrderStatus.PROCESSING)) {
                order.setOrderStatus(OrderStatus.PROCESSING);
                orderRepository.save(order);
            } else {
                throw new RuntimeException("Cannot process order in current status: " + order.getOrderStatus());
            }
        } else {
            throw new RuntimeException("Order not found: " + orderId);
        }
    }
    
    public void shipOrder(Long orderId) {
        Optional<Order> orderOpt = orderRepository.findById(orderId);
        if (orderOpt.isPresent()) {
            Order order = orderOpt.get();
            if (order.getOrderStatus().canTransitionTo(OrderStatus.SHIPPED)) {
                order.setOrderStatus(OrderStatus.SHIPPED);
                orderRepository.save(order);
            } else {
                throw new RuntimeException("Cannot ship order in current status: " + order.getOrderStatus());
            }
        } else {
            throw new RuntimeException("Order not found: " + orderId);
        }
    }
    
    public void completeOrder(Long orderId) {
        Optional<Order> orderOpt = orderRepository.findById(orderId);
        if (orderOpt.isPresent()) {
            Order order = orderOpt.get();
            if (order.getOrderStatus().canTransitionTo(OrderStatus.COMPLETED)) {
                order.setOrderStatus(OrderStatus.COMPLETED);
                orderRepository.save(order);
            } else {
                throw new RuntimeException("Cannot complete order in current status: " + order.getOrderStatus());
            }
        } else {
            throw new RuntimeException("Order not found: " + orderId);
        }
    }
    
    // 12. 대량 업데이트
    public int updateOrderStatusByDateAndStatus(OrderStatus newStatus, OrderStatus oldStatus, LocalDateTime beforeDate) {
        return orderRepository.updateOrderStatusByDateAndStatus(newStatus, oldStatus, beforeDate);
    }
    
    public int updateShippingAddress(Long orderId, String address) {
        return orderRepository.updateShippingAddress(orderId, address);
    }
    
    // 13. DTO 프로젝션
    @Transactional(readOnly = true)
    public List<OrderSummaryDto> getOrderSummariesByStatus(OrderStatus status) {
        return orderRepository.findOrderSummariesByStatus(status);
    }
    
    // 14. 비즈니스 로직
    public void updateOrderTotal(Long orderId, BigDecimal newTotal) {
        Optional<Order> orderOpt = orderRepository.findById(orderId);
        if (orderOpt.isPresent()) {
            Order order = orderOpt.get();
            order.setTotalAmount(newTotal);
            orderRepository.save(order);
        } else {
            throw new RuntimeException("Order not found: " + orderId);
        }
    }
    
    public void applyDiscount(Long orderId, BigDecimal discountAmount) {
        Optional<Order> orderOpt = orderRepository.findById(orderId);
        if (orderOpt.isPresent()) {
            Order order = orderOpt.get();
            order.setDiscountAmount(discountAmount);
            orderRepository.save(order);
        } else {
            throw new RuntimeException("Order not found: " + orderId);
        }
    }
    
    @Transactional(readOnly = true)
    public List<Order> getAllOrders() {
        return orderRepository.findAll();
    }
}

