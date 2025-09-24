package com.example.dao;

import org.springframework.stereotype.Repository;
import java.util.Date;
import java.util.List;

@Repository
public class JoinQueryDao {

    /**
     * INSERT with JOIN condition
     * Insert user statistics by joining users and orders tables
     */
    public void insertUserOrderStatistics(Date fromDate) {
        String insertQuery = "INSERT INTO user_order_statistics (user_id, total_orders, total_amount, last_order_date) " +
                           "SELECT u.user_id, COUNT(o.order_id), SUM(o.total_amount), MAX(o.order_date) " +
                           "FROM users u, orders o " +
                           "WHERE u.user_id = o.user_id " +
                           "AND u.status = 'ACTIVE' " +
                           "AND o.order_status = 'COMPLETED' " +
                           "AND u.created_date > ? " +
                           "GROUP BY u.user_id";
        
        // Execute query logic here
        System.out.println("Executing insertUserOrderStatistics: " + insertQuery);
    }

    /**
     * UPDATE with EXISTS subquery
     * Update user status based on order history
     */
    public void updateUserStatusBasedOnOrders(Date cutoffDate) {
        String updateQuery = "UPDATE users u " +
                           "SET u.status = 'INACTIVE', u.updated_date = SYSDATE " +
                           "WHERE EXISTS (" +
                           "    SELECT 'X' FROM orders o " +
                           "    WHERE u.user_id = o.user_id " +
                           "    AND o.order_date < ? " +
                           "    AND o.order_status = 'CANCELLED'" +
                           ") " +
                           "AND u.status = 'ACTIVE'";
        
        // Execute query logic here
        System.out.println("Executing updateUserStatusBasedOnOrders: " + updateQuery);
    }

    /**
     * DELETE with EXISTS subquery
     * Delete users who have no recent activity
     */
    public void deleteInactiveUsersWithNoActivity(Date cutoffDate) {
        String deleteQuery = "DELETE FROM users u " +
                           "WHERE EXISTS (" +
                           "    SELECT 'X' FROM user_activities ua " +
                           "    WHERE u.user_id = ua.user_id " +
                           "    AND ua.last_login_date < ? " +
                           "    AND ua.activity_count = 0" +
                           ") " +
                           "AND u.status = 'INACTIVE'";
        
        // Execute query logic here
        System.out.println("Executing deleteInactiveUsersWithNoActivity: " + deleteQuery);
    }

    /**
     * Complex INSERT with multiple JOIN conditions
     * Insert product recommendations based on user purchase history
     */
    public void insertProductRecommendations() {
        String insertQuery = "INSERT INTO product_recommendations (user_id, product_id, recommendation_score, created_date) " +
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
                           "HAVING COUNT(oi.quantity) > 1";
        
        // Execute query logic here
        System.out.println("Executing insertProductRecommendations: " + insertQuery);
    }

    /**
     * Complex UPDATE with multiple JOIN conditions
     * Update product prices based on category and brand analysis
     */
    public void updateProductPricesBasedOnAnalysis() {
        String updateQuery = "UPDATE products p " +
                           "SET p.price = p.price * 1.1, p.updated_date = SYSDATE " +
                           "WHERE EXISTS (" +
                           "    SELECT 'X' FROM categories c, brands b " +
                           "    WHERE p.category_id = c.category_id " +
                           "    AND p.brand_id = b.brand_id " +
                           "    AND c.category_name = 'Electronics' " +
                           "    AND b.brand_name IN ('Samsung', 'Apple', 'LG')" +
                           ") " +
                           "AND p.status = 'ACTIVE'";
        
        // Execute query logic here
        System.out.println("Executing updateProductPricesBasedOnAnalysis: " + updateQuery);
    }

    /**
     * Complex DELETE with multiple JOIN conditions
     * Delete old order items that are no longer needed
     */
    public void deleteOldOrderItems(Date cutoffDate) {
        String deleteQuery = "DELETE FROM order_items oi " +
                           "WHERE EXISTS (" +
                           "    SELECT 'X' FROM orders o, users u " +
                           "    WHERE oi.order_id = o.order_id " +
                           "    AND o.user_id = u.user_id " +
                           "    AND o.order_date < ? " +
                           "    AND u.status = 'INACTIVE'" +
                           ") " +
                           "AND oi.created_date < ?";
        
        // Execute query logic here
        System.out.println("Executing deleteOldOrderItems: " + deleteQuery);
    }
}
