package com.example.jpa.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;
import java.util.List;

/**
 * JPA 조인 조건이 포함된 INSERT, UPDATE, DELETE 쿼리 샘플
 */
@Repository
public interface JoinConditionRepository extends JpaRepository<Object, Long> {

    /**
     * INSERT with JOIN condition - 사용자 타입과 조인하여 프로필 생성
     */
    @Modifying
    @Transactional
    @Query(value = """
        INSERT INTO USER_PROFILES (PROFILE_ID, USER_ID, FIRST_NAME, LAST_NAME, PHONE, ADDRESS)
        SELECT 
            USER_PROFILES_SEQ.NEXTVAL,
            u.ID,
            :firstName,
            :lastName,
            :phone,
            :address
        FROM USERS u, USER_TYPES ut
        WHERE u.ID = ut.TYPE_ID 
        AND u.USERNAME = :username
        AND ut.TYPE_NAME = :userType
        """, nativeQuery = true)
    int insertUserProfileWithUserType(@Param("username") String username, 
                                     @Param("userType") String userType,
                                     @Param("firstName") String firstName,
                                     @Param("lastName") String lastName,
                                     @Param("phone") String phone,
                                     @Param("address") String address);

    /**
     * UPDATE with JOIN condition - 고객과 주문 아이템 조인하여 주문 상태 업데이트
     */
    @Modifying
    @Transactional
    @Query(value = """
        UPDATE ORDERS o
        SET o.STATUS = :newStatus,
            o.UPDATED_AT = CURRENT_TIMESTAMP
        WHERE EXISTS (
            SELECT 'X' 
            FROM CUSTOMERS c, ORDER_ITEMS oi
            WHERE o.CUSTOMER_ID = c.CUSTOMER_ID 
            AND o.ORDER_ID = oi.ORDER_ID
            AND c.CUSTOMER_NAME = :customerName
            AND oi.QUANTITY > :minQuantity
        )
        """, nativeQuery = true)
    int updateOrderStatusWithCustomer(@Param("customerName") String customerName,
                                     @Param("minQuantity") int minQuantity,
                                     @Param("newStatus") String newStatus);

    /**
     * DELETE with JOIN condition - 역할과 조인하여 비활성 사용자 삭제
     */
    @Modifying
    @Transactional
    @Query(value = """
        DELETE FROM USERS u
        WHERE EXISTS (
            SELECT 'X' 
            FROM USER_ROLES ur, ROLES r
            WHERE u.ID = ur.USER_ID 
            AND ur.ROLE_ID = r.ROLE_ID
            AND u.STATUS = 'INACTIVE'
            AND r.ROLE_NAME = :roleName
            AND u.CREATED_AT < :cutoffDate
        )
        """, nativeQuery = true)
    int deleteInactiveUsersWithRoles(@Param("roleName") String roleName,
                                     @Param("cutoffDate") Date cutoffDate);

    /**
     * INSERT with JOIN condition - 카테고리와 조인하여 상품 등록
     */
    @Modifying
    @Transactional
    @Query(value = """
        INSERT INTO PRODUCTS (PRODUCT_ID, PRODUCT_NAME, CATEGORY_ID, PRICE, STOCK_QUANTITY, DESCRIPTION)
        SELECT 
            PRODUCTS_SEQ.NEXTVAL,
            :productName,
            c.CATEGORY_ID,
            :price,
            :stockQuantity,
            :description
        FROM CATEGORIES c, DEPARTMENTS d
        WHERE c.CATEGORY_ID = d.DEPT_ID
        AND c.CATEGORY_NAME = :categoryName
        AND d.DEPT_NAME = :departmentName
        """, nativeQuery = true)
    int insertProductWithCategory(@Param("productName") String productName,
                                 @Param("categoryName") String categoryName,
                                 @Param("departmentName") String departmentName,
                                 @Param("price") double price,
                                 @Param("stockQuantity") int stockQuantity,
                                 @Param("description") String description);

    /**
     * UPDATE with JOIN condition - 부서와 조인하여 사용자 정보 업데이트
     */
    @Modifying
    @Transactional
    @Query(value = """
        UPDATE USERS u
        SET u.STATUS = :newStatus,
            u.UPDATED_AT = CURRENT_TIMESTAMP
        WHERE EXISTS (
            SELECT 'X' 
            FROM USER_PROFILES up, DEPARTMENTS d
            WHERE u.ID = up.USER_ID 
            AND up.ADDRESS LIKE '%' || d.LOCATION || '%'
            AND d.DEPT_NAME = :departmentName
            AND u.STATUS = :currentStatus
        )
        """, nativeQuery = true)
    int updateUserWithDepartment(@Param("departmentName") String departmentName,
                                @Param("currentStatus") String currentStatus,
                                @Param("newStatus") String newStatus);

    /**
     * DELETE with JOIN condition - 주문과 조인하여 고객 삭제
     */
    @Modifying
    @Transactional
    @Query(value = """
        DELETE FROM CUSTOMERS c
        WHERE EXISTS (
            SELECT 'X' 
            FROM ORDERS o, ORDER_ITEMS oi, PRODUCTS p
            WHERE c.CUSTOMER_ID = o.CUSTOMER_ID 
            AND o.ORDER_ID = oi.ORDER_ID
            AND oi.PRODUCT_ID = p.PRODUCT_ID
            AND c.CUSTOMER_NAME = :customerName
            AND p.PRODUCT_NAME = :productName
            AND o.ORDER_DATE < :cutoffDate
        )
        """, nativeQuery = true)
    int deleteCustomerWithOrders(@Param("customerName") String customerName,
                                @Param("productName") String productName,
                                @Param("cutoffDate") Date cutoffDate);

    /**
     * INSERT with JOIN condition - 상품과 주문 조인하여 주문 아이템 생성
     */
    @Modifying
    @Transactional
    @Query(value = """
        INSERT INTO ORDER_ITEMS (ITEM_ID, ORDER_ID, PRODUCT_ID, QUANTITY, UNIT_PRICE)
        SELECT 
            ORDER_ITEMS_SEQ.NEXTVAL,
            o.ORDER_ID,
            p.PRODUCT_ID,
            :quantity,
            p.PRICE
        FROM ORDERS o, PRODUCTS p, CUSTOMERS c
        WHERE o.CUSTOMER_ID = c.CUSTOMER_ID
        AND p.PRODUCT_NAME = :productName
        AND c.CUSTOMER_NAME = :customerName
        AND o.ORDER_DATE = :orderDate
        """, nativeQuery = true)
    int insertOrderItemWithProduct(@Param("productName") String productName,
                                  @Param("customerName") String customerName,
                                  @Param("orderDate") Date orderDate,
                                  @Param("quantity") int quantity);

    /**
     * UPDATE with JOIN condition - 사용자 프로필과 조인하여 사용자 정보 업데이트
     */
    @Modifying
    @Transactional
    @Query(value = """
        UPDATE USERS u
        SET u.EMAIL = :newEmail,
            u.UPDATED_AT = CURRENT_TIMESTAMP
        WHERE EXISTS (
            SELECT 'X' 
            FROM USER_PROFILES up, USER_ROLES ur, ROLES r
            WHERE u.ID = up.USER_ID 
            AND u.ID = ur.USER_ID
            AND ur.ROLE_ID = r.ROLE_ID
            AND up.FIRST_NAME = :firstName
            AND up.LAST_NAME = :lastName
            AND r.ROLE_NAME = :roleName
        )
        """, nativeQuery = true)
    int updateUserWithProfile(@Param("firstName") String firstName,
                             @Param("lastName") String lastName,
                             @Param("roleName") String roleName,
                             @Param("newEmail") String newEmail);

    /**
     * DELETE with JOIN condition - 상품과 카테고리 조인하여 상품 삭제
     */
    @Modifying
    @Transactional
    @Query(value = """
        DELETE FROM PRODUCTS p
        WHERE EXISTS (
            SELECT 'X' 
            FROM CATEGORIES c, ORDER_ITEMS oi, ORDERS o
            WHERE p.CATEGORY_ID = c.CATEGORY_ID 
            AND p.PRODUCT_ID = oi.PRODUCT_ID
            AND oi.ORDER_ID = o.ORDER_ID
            AND c.CATEGORY_NAME = :categoryName
            AND o.STATUS = :orderStatus
            AND p.STOCK_QUANTITY = 0
        )
        """, nativeQuery = true)
    int deleteProductWithCategory(@Param("categoryName") String categoryName,
                                  @Param("orderStatus") String orderStatus);
}

