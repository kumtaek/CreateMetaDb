package com.example.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;
import java.util.List;

@Repository
public interface JoinQueryRepository extends JpaRepository<Object, Long> {

    /**
     * INSERT with JOIN condition
     * Insert user order statistics by joining users and orders
     */
    @Modifying
    @Transactional
    @Query(value = "INSERT INTO user_order_statistics (user_id, total_orders, total_amount, last_order_date) " +
                  "SELECT u.user_id, COUNT(o.order_id), SUM(o.total_amount), MAX(o.order_date) " +
                  "FROM users u, orders o " +
                  "WHERE u.user_id = o.user_id " +
                  "AND u.status = 'ACTIVE' " +
                  "AND o.order_status = 'COMPLETED' " +
                  "AND u.created_date > :fromDate " +
                  "GROUP BY u.user_id", nativeQuery = true)
    void insertUserOrderStatisticsWithJoin(@Param("fromDate") Date fromDate);

    /**
     * UPDATE with EXISTS subquery
     * Update user status based on order history
     */
    @Modifying
    @Transactional
    @Query(value = "UPDATE users u " +
                  "SET u.status = 'INACTIVE', u.updated_date = SYSDATE " +
                  "WHERE EXISTS (" +
                  "    SELECT 'X' FROM orders o " +
                  "    WHERE u.user_id = o.user_id " +
                  "    AND o.order_date < :cutoffDate " +
                  "    AND o.order_status = 'CANCELLED'" +
                  ") " +
                  "AND u.status = 'ACTIVE'", nativeQuery = true)
    void updateUserStatusWithExists(@Param("cutoffDate") Date cutoffDate);

    /**
     * DELETE with EXISTS subquery
     * Delete users who have no recent activity
     */
    @Modifying
    @Transactional
    @Query(value = "DELETE FROM users u " +
                  "WHERE EXISTS (" +
                  "    SELECT 'X' FROM user_activities ua " +
                  "    WHERE u.user_id = ua.user_id " +
                  "    AND ua.last_login_date < :cutoffDate " +
                  "    AND ua.activity_count = 0" +
                  ") " +
                  "AND u.status = 'INACTIVE'", nativeQuery = true)
    void deleteInactiveUsersWithExists(@Param("cutoffDate") Date cutoffDate);

    /**
     * Complex INSERT with multiple JOIN conditions
     * Insert product recommendations based on user purchase history
     */
    @Modifying
    @Transactional
    @Query(value = "INSERT INTO product_recommendations (user_id, product_id, recommendation_score, created_date) " +
                  "SELECT u.user_id, p.product_id, " +
                  "       (COUNT(oi.quantity) * AVG(oi.unit_price)) as score, " +
                  "       SYSDATE " +
                  "FROM users u, orders o, order_items oi, products p " +
                  "WHERE u.user_id = o.user_id " +
                  "AND o.order_id = oi.order_id " +
                  "AND oi.product_id = p.product_id " +
                  "AND u.status = 'ACTIVE' " +
                  "AND o.order_status = 'COMPLETED' " +
                  "AND p.status = 'ACTIVE' " +
                  "GROUP BY u.user_id, p.product_id " +
                  "HAVING COUNT(oi.quantity) > 1", nativeQuery = true)
    void insertProductRecommendationsWithJoin();

    /**
     * Complex UPDATE with multiple JOIN conditions
     * Update product prices based on category and brand analysis
     */
    @Modifying
    @Transactional
    @Query(value = "UPDATE products p " +
                  "SET p.price = p.price * 1.1, p.updated_date = SYSDATE " +
                  "WHERE EXISTS (" +
                  "    SELECT 'X' FROM categories c, brands b " +
                  "    WHERE p.category_id = c.category_id " +
                  "    AND p.brand_id = b.brand_id " +
                  "    AND c.category_name = 'Electronics' " +
                  "    AND b.brand_name IN ('Samsung', 'Apple', 'LG')" +
                  ") " +
                  "AND p.status = 'ACTIVE'", nativeQuery = true)
    void updateProductPricesWithJoin();

    /**
     * Complex DELETE with multiple JOIN conditions
     * Delete old order items that are no longer needed
     */
    @Modifying
    @Transactional
    @Query(value = "DELETE FROM order_items oi " +
                  "WHERE EXISTS (" +
                  "    SELECT 'X' FROM orders o, users u " +
                  "    WHERE oi.order_id = o.order_id " +
                  "    AND o.user_id = u.user_id " +
                  "    AND o.order_date < :cutoffDate " +
                  "    AND u.status = 'INACTIVE'" +
                  ") " +
                  "AND oi.created_date < :cutoffDate", nativeQuery = true)
    void deleteOldOrderItemsWithJoin(@Param("cutoffDate") Date cutoffDate);

    /**
     * JPQL INSERT with JOIN condition
     * Insert user statistics using JPQL
     */
    @Modifying
    @Transactional
    @Query("INSERT INTO UserStatistics u (u.userId, u.totalOrders, u.totalAmount) " +
           "SELECT u.userId, COUNT(o.orderId), SUM(o.totalAmount) " +
           "FROM User u JOIN u.orders o " +
           "WHERE u.status = 'ACTIVE' " +
           "AND o.orderStatus = 'COMPLETED' " +
           "GROUP BY u.userId")
    void insertUserStatisticsWithJpql();

    /**
     * JPQL UPDATE with JOIN condition
     * Update user status using JPQL
     */
    @Modifying
    @Transactional
    @Query("UPDATE User u SET u.status = 'INACTIVE' " +
           "WHERE EXISTS (" +
           "    SELECT 1 FROM Order o " +
           "    WHERE u.userId = o.userId " +
           "    AND o.orderDate < :cutoffDate " +
           "    AND o.orderStatus = 'CANCELLED'" +
           ") " +
           "AND u.status = 'ACTIVE'")
    void updateUserStatusWithJpql(@Param("cutoffDate") Date cutoffDate);

    /**
     * JPQL DELETE with JOIN condition
     * Delete inactive users using JPQL
     */
    @Modifying
    @Transactional
    @Query("DELETE FROM User u " +
           "WHERE EXISTS (" +
           "    SELECT 1 FROM UserActivity ua " +
           "    WHERE u.userId = ua.userId " +
           "    AND ua.lastLoginDate < :cutoffDate " +
           "    AND ua.activityCount = 0" +
           ") " +
           "AND u.status = 'INACTIVE'")
    void deleteInactiveUsersWithJpql(@Param("cutoffDate") Date cutoffDate);
}
