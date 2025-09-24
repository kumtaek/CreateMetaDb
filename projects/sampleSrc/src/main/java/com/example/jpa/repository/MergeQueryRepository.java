package com.example.jpa.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;

@Repository
public interface MergeQueryRepository extends JpaRepository<Object, Long> {

    /**
     * MERGE 쿼리 - 사용자 통계 업데이트/삽입
     * JPA @Query를 사용한 MERGE 쿼리
     */
    @Modifying
    @Transactional
    @Query(value = "MERGE INTO user_statistics us " +
                  "USING ( " +
                  "    SELECT " +
                  "        u.user_id, " +
                  "        COUNT(o.order_id) as total_orders, " +
                  "        SUM(o.total_amount) as total_amount, " +
                  "        MAX(o.order_date) as last_order_date " +
                  "    FROM users u " +
                  "    LEFT JOIN orders o ON u.user_id = o.user_id " +
                  "    WHERE u.status = 'ACTIVE' " +
                  "    AND o.order_status = 'COMPLETED' " +
                  "    GROUP BY u.user_id " +
                  ") src ON us.user_id = src.user_id " +
                  "WHEN MATCHED THEN " +
                  "    UPDATE SET " +
                  "        us.total_orders = src.total_orders, " +
                  "        us.total_amount = src.total_amount, " +
                  "        us.last_order_date = src.last_order_date, " +
                  "        us.updated_date = SYSDATE " +
                  "WHEN NOT MATCHED THEN " +
                  "    INSERT (user_id, total_orders, total_amount, last_order_date, created_date, updated_date) " +
                  "    VALUES (src.user_id, src.total_orders, src.total_amount, src.last_order_date, SYSDATE, SYSDATE)", 
                  nativeQuery = true)
    void mergeUserStatisticsWithJpa();

    /**
     * MERGE 쿼리 - 상품 재고 업데이트/삽입
     * JPA @Query를 사용한 MERGE 쿼리
     */
    @Modifying
    @Transactional
    @Query(value = "MERGE INTO product_inventory pi " +
                  "USING ( " +
                  "    SELECT " +
                  "        p.product_id, " +
                  "        p.product_name, " +
                  "        p.stock_quantity, " +
                  "        p.price, " +
                  "        c.category_name, " +
                  "        b.brand_name " +
                  "    FROM products p " +
                  "    LEFT JOIN categories c ON p.category_id = c.category_id " +
                  "    LEFT JOIN brands b ON p.brand_id = b.brand_id " +
                  "    WHERE p.status = 'ACTIVE' " +
                  ") src ON pi.product_id = src.product_id " +
                  "WHEN MATCHED THEN " +
                  "    UPDATE SET " +
                  "        pi.current_stock = src.stock_quantity, " +
                  "        pi.current_price = src.price, " +
                  "        pi.category_name = src.category_name, " +
                  "        pi.brand_name = src.brand_name, " +
                  "        pi.updated_date = SYSDATE " +
                  "WHEN NOT MATCHED THEN " +
                  "    INSERT (product_id, product_name, current_stock, current_price, category_name, brand_name, created_date, updated_date) " +
                  "    VALUES (src.product_id, src.product_name, src.stock_quantity, src.price, src.category_name, src.brand_name, SYSDATE, SYSDATE)", 
                  nativeQuery = true)
    void mergeProductInventoryWithJpa();

    /**
     * MERGE 쿼리 - 주문 요약 통계 업데이트/삽입
     * JPA @Query를 사용한 MERGE 쿼리
     */
    @Modifying
    @Transactional
    @Query(value = "MERGE INTO order_summary os " +
                  "USING ( " +
                  "    SELECT " +
                  "        o.user_id, " +
                  "        DATE(o.order_date) as order_date, " +
                  "        COUNT(o.order_id) as daily_orders, " +
                  "        SUM(o.total_amount) as daily_amount, " +
                  "        AVG(o.total_amount) as avg_order_amount " +
                  "    FROM orders o " +
                  "    WHERE o.order_status = 'COMPLETED' " +
                  "    AND o.order_date >= :fromDate " +
                  "    GROUP BY o.user_id, DATE(o.order_date) " +
                  ") src ON os.user_id = src.user_id AND os.order_date = src.order_date " +
                  "WHEN MATCHED THEN " +
                  "    UPDATE SET " +
                  "        os.daily_orders = src.daily_orders, " +
                  "        os.daily_amount = src.daily_amount, " +
                  "        os.avg_order_amount = src.avg_order_amount, " +
                  "        os.updated_date = SYSDATE " +
                  "WHEN NOT MATCHED THEN " +
                  "    INSERT (user_id, order_date, daily_orders, daily_amount, avg_order_amount, created_date, updated_date) " +
                  "    VALUES (src.user_id, src.order_date, src.daily_orders, src.daily_amount, src.avg_order_amount, SYSDATE, SYSDATE)", 
                  nativeQuery = true)
    void mergeOrderSummaryWithJpa(@Param("fromDate") Date fromDate);

    /**
     * MERGE 쿼리 - 사용자 활동 로그 업데이트/삽입
     * JPA @Query를 사용한 MERGE 쿼리
     */
    @Modifying
    @Transactional
    @Query(value = "MERGE INTO user_activity_log ual " +
                  "USING ( " +
                  "    SELECT " +
                  "        u.user_id, " +
                  "        u.username, " +
                  "        u.email, " +
                  "        u.last_login_date, " +
                  "        COUNT(o.order_id) as recent_orders, " +
                  "        SUM(o.total_amount) as recent_spending " +
                  "    FROM users u " +
                  "    LEFT JOIN orders o ON u.user_id = o.user_id " +
                  "        AND o.order_date >= DATE_SUB(NOW(), INTERVAL 30 DAY) " +
                  "    WHERE u.status = 'ACTIVE' " +
                  "    GROUP BY u.user_id, u.username, u.email, u.last_login_date " +
                  ") src ON ual.user_id = src.user_id " +
                  "WHEN MATCHED THEN " +
                  "    UPDATE SET " +
                  "        ual.username = src.username, " +
                  "        ual.email = src.email, " +
                  "        ual.last_login_date = src.last_login_date, " +
                  "        ual.recent_orders = src.recent_orders, " +
                  "        ual.recent_spending = src.recent_spending, " +
                  "        ual.updated_date = SYSDATE " +
                  "WHEN NOT MATCHED THEN " +
                  "    INSERT (user_id, username, email, last_login_date, recent_orders, recent_spending, created_date, updated_date) " +
                  "    VALUES (src.user_id, src.username, src.email, src.last_login_date, src.recent_orders, src.recent_spending, SYSDATE, SYSDATE)", 
                  nativeQuery = true)
    void mergeUserActivityLogWithJpa();

    /**
     * MERGE 쿼리 - 상품 카테고리 통계 업데이트/삽입
     * JPA @Query를 사용한 MERGE 쿼리
     */
    @Modifying
    @Transactional
    @Query(value = "MERGE INTO category_statistics cs " +
                  "USING ( " +
                  "    SELECT " +
                  "        c.category_id, " +
                  "        c.category_name, " +
                  "        COUNT(p.product_id) as product_count, " +
                  "        AVG(p.price) as avg_price, " +
                  "        SUM(p.stock_quantity) as total_stock, " +
                  "        COUNT(CASE WHEN p.status = 'ACTIVE' THEN 1 END) as active_products " +
                  "    FROM categories c " +
                  "    LEFT JOIN products p ON c.category_id = p.category_id " +
                  "    WHERE c.is_active = 1 " +
                  "    GROUP BY c.category_id, c.category_name " +
                  ") src ON cs.category_id = src.category_id " +
                  "WHEN MATCHED THEN " +
                  "    UPDATE SET " +
                  "        cs.product_count = src.product_count, " +
                  "        cs.avg_price = src.avg_price, " +
                  "        cs.total_stock = src.total_stock, " +
                  "        cs.active_products = src.active_products, " +
                  "        cs.updated_date = SYSDATE " +
                  "WHEN NOT MATCHED THEN " +
                  "    INSERT (category_id, category_name, product_count, avg_price, total_stock, active_products, created_date, updated_date) " +
                  "    VALUES (src.category_id, src.category_name, src.product_count, src.avg_price, src.total_stock, src.active_products, SYSDATE, SYSDATE)", 
                  nativeQuery = true)
    void mergeCategoryStatisticsWithJpa();
}

