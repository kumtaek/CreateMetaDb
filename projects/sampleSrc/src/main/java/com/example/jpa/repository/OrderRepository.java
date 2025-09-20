package com.example.jpa.repository;

import com.example.jpa.entity.Order;
import com.example.jpa.entity.OrderStatus;
import com.example.jpa.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * JPA Order Repository
 * 주문 관련 다양한 JPA 쿼리 패턴 테스트케이스
 */
@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {
    
    // 1. 기본 메서드명 기반 쿼리
    Optional<Order> findByOrderNumber(String orderNumber);
    
    List<Order> findByOrderStatus(OrderStatus orderStatus);
    
    List<Order> findByUser(User user);
    
    List<Order> findByUserUserId(Long userId);
    
    List<Order> findByOrderStatusAndUser(OrderStatus orderStatus, User user);
    
    // 2. 날짜 범위 검색
    List<Order> findByOrderDateBetween(LocalDateTime startDate, LocalDateTime endDate);
    
    List<Order> findByOrderDateAfter(LocalDateTime date);
    
    List<Order> findByCreatedAtBefore(LocalDateTime date);
    
    // 3. 금액 관련 검색
    List<Order> findByTotalAmountGreaterThan(BigDecimal amount);
    
    List<Order> findByTotalAmountBetween(BigDecimal minAmount, BigDecimal maxAmount);
    
    List<Order> findByDiscountAmountGreaterThan(BigDecimal discountAmount);
    
    // 4. 복합 조건 검색
    List<Order> findByOrderStatusAndOrderDateAfter(OrderStatus status, LocalDateTime date);
    
    List<Order> findByUserUserIdAndOrderStatus(Long userId, OrderStatus status);
    
    Page<Order> findByOrderStatusAndTotalAmountGreaterThan(OrderStatus status, BigDecimal amount, Pageable pageable);
    
    // 5. 정렬 쿼리
    List<Order> findByOrderStatusOrderByOrderDateDesc(OrderStatus status);
    
    List<Order> findByUserUserIdOrderByTotalAmountDesc(Long userId);
    
    List<Order> findByOrderDateBetweenOrderByCreatedAtAsc(LocalDateTime start, LocalDateTime end);
    
    // 6. Count 쿼리
    long countByOrderStatus(OrderStatus status);
    
    long countByUserUserId(Long userId);
    
    long countByOrderDateAfter(LocalDateTime date);
    
    long countByTotalAmountGreaterThan(BigDecimal amount);
    
    // 7. @Query - JPQL 쿼리
    @Query("SELECT o FROM Order o JOIN FETCH o.user WHERE o.orderStatus = :status")
    List<Order> findByOrderStatusWithUser(@Param("status") OrderStatus status);
    
    @Query("SELECT o FROM Order o JOIN FETCH o.orderItems WHERE o.orderId = :orderId")
    Optional<Order> findByIdWithOrderItems(@Param("orderId") Long orderId);
    
    @Query("SELECT o FROM Order o JOIN FETCH o.user JOIN FETCH o.orderItems WHERE o.orderNumber = :orderNumber")
    Optional<Order> findByOrderNumberWithDetails(@Param("orderNumber") String orderNumber);
    
    // 8. 사용자별 주문 통계
    @Query("SELECT COUNT(o) FROM Order o WHERE o.user.userId = :userId AND o.orderStatus = :status")
    long countUserOrdersByStatus(@Param("userId") Long userId, @Param("status") OrderStatus status);
    
    @Query("SELECT SUM(o.totalAmount) FROM Order o WHERE o.user.userId = :userId AND o.orderStatus = 'COMPLETED'")
    BigDecimal getTotalAmountByUserId(@Param("userId") Long userId);
    
    @Query("SELECT AVG(o.totalAmount) FROM Order o WHERE o.orderStatus = :status")
    BigDecimal getAverageOrderAmountByStatus(@Param("status") OrderStatus status);
    
    // 9. 집계 쿼리
    @Query("SELECT o.orderStatus, COUNT(o) FROM Order o GROUP BY o.orderStatus")
    List<Object[]> getOrderCountByStatus();
    
    @Query("SELECT DATE(o.orderDate), COUNT(o) FROM Order o WHERE o.orderDate >= :fromDate GROUP BY DATE(o.orderDate)")
    List<Object[]> getDailyOrderCount(@Param("fromDate") LocalDateTime fromDate);
    
    @Query("SELECT o.user.username, COUNT(o), SUM(o.totalAmount) FROM Order o " +
           "WHERE o.orderStatus = 'COMPLETED' GROUP BY o.user.userId, o.user.username " +
           "ORDER BY SUM(o.totalAmount) DESC")
    List<Object[]> getTopCustomersByTotalAmount();
    
    // 10. Native SQL 쿼리
    @Query(value = "SELECT * FROM ORDERS o WHERE o.ORDER_STATUS = ?1 AND o.TOTAL_AMOUNT > ?2 " +
                   "ORDER BY o.ORDER_DATE DESC", nativeQuery = true)
    List<Order> findByStatusAndAmountNative(String status, BigDecimal minAmount);
    
    @Query(value = "SELECT o.*, u.USERNAME FROM ORDERS o " +
                   "JOIN USERS u ON o.USER_ID = u.USER_ID " +
                   "WHERE o.ORDER_DATE BETWEEN ?1 AND ?2", nativeQuery = true)
    List<Order> findOrdersWithUserInDateRangeNative(LocalDateTime startDate, LocalDateTime endDate);
    
    // 11. @Modifying 업데이트 쿼리
    @Modifying
    @Query("UPDATE Order o SET o.orderStatus = :newStatus WHERE o.orderStatus = :oldStatus AND o.orderDate < :beforeDate")
    int updateOrderStatusByDateAndStatus(@Param("newStatus") OrderStatus newStatus, 
                                        @Param("oldStatus") OrderStatus oldStatus, 
                                        @Param("beforeDate") LocalDateTime beforeDate);
    
    @Modifying
    @Query("UPDATE Order o SET o.orderStatus = 'CANCELLED' WHERE o.orderId = :orderId")
    int cancelOrder(@Param("orderId") Long orderId);
    
    @Modifying
    @Query("UPDATE Order o SET o.shippingAddress = :address WHERE o.orderId = :orderId")
    int updateShippingAddress(@Param("orderId") Long orderId, @Param("address") String address);
    
    // 12. 서브쿼리
    @Query("SELECT o FROM Order o WHERE o.user.userId IN " +
           "(SELECT u.userId FROM User u WHERE u.userType = 'PREMIUM')")
    List<Order> findOrdersByPremiumUsers();
    
    @Query("SELECT o FROM Order o WHERE o.orderId IN " +
           "(SELECT oi.order.orderId FROM OrderItem oi WHERE oi.product.category.categoryName = :categoryName)")
    List<Order> findOrdersContainingProductsFromCategory(@Param("categoryName") String categoryName);
    
    // 13. 동적 검색 쿼리
    @Query("SELECT o FROM Order o WHERE " +
           "(:userId IS NULL OR o.user.userId = :userId) AND " +
           "(:status IS NULL OR o.orderStatus = :status) AND " +
           "(:fromDate IS NULL OR o.orderDate >= :fromDate) AND " +
           "(:toDate IS NULL OR o.orderDate <= :toDate) AND " +
           "(:minAmount IS NULL OR o.totalAmount >= :minAmount) AND " +
           "(:maxAmount IS NULL OR o.totalAmount <= :maxAmount)")
    Page<Order> findOrdersByDynamicCriteria(@Param("userId") Long userId,
                                           @Param("status") OrderStatus status,
                                           @Param("fromDate") LocalDateTime fromDate,
                                           @Param("toDate") LocalDateTime toDate,
                                           @Param("minAmount") BigDecimal minAmount,
                                           @Param("maxAmount") BigDecimal maxAmount,
                                           Pageable pageable);
    
    // 14. 복잡한 연관관계 쿼리
    @Query("SELECT DISTINCT o FROM Order o JOIN o.orderItems oi " +
           "WHERE oi.product.productName LIKE %:productName%")
    List<Order> findOrdersContainingProduct(@Param("productName") String productName);
    
    @Query("SELECT o FROM Order o WHERE SIZE(o.orderItems) > :minItemCount")
    List<Order> findOrdersWithMinimumItems(@Param("minItemCount") int minItemCount);
    
    @Query("SELECT o FROM Order o JOIN o.orderItems oi " +
           "GROUP BY o.orderId " +
           "HAVING SUM(oi.totalPrice) != o.totalAmount")
    List<Order> findOrdersWithInconsistentTotals();
    
    // 15. DTO 프로젝션
    @Query("SELECT new com.example.jpa.dto.OrderSummaryDto(o.orderId, o.orderNumber, o.orderDate, o.orderStatus, o.totalAmount, o.user.username) " +
           "FROM Order o WHERE o.orderStatus = :status")
    List<com.example.jpa.dto.OrderSummaryDto> findOrderSummariesByStatus(@Param("status") OrderStatus status);
    
    // 16. 최근 주문 관련 쿼리
    @Query("SELECT o FROM Order o WHERE o.user.userId = :userId ORDER BY o.orderDate DESC")
    List<Order> findRecentOrdersByUserId(@Param("userId") Long userId, Pageable pageable);
    
    @Query("SELECT o FROM Order o WHERE o.orderDate >= :fromDate AND o.orderStatus IN :statuses")
    List<Order> findRecentOrdersByStatuses(@Param("fromDate") LocalDateTime fromDate, 
                                          @Param("statuses") List<OrderStatus> statuses);
}

