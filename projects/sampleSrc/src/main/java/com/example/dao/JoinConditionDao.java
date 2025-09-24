package com.example.dao;

import java.util.List;
import java.util.Map;

/**
 * 조인 조건이 포함된 INSERT, UPDATE, DELETE 쿼리 샘플
 */
public interface JoinConditionDao {

    /**
     * INSERT with JOIN condition - 사용자 타입과 조인하여 프로필 생성
     */
    int insertUserProfileWithUserType(Map<String, Object> params);

    /**
     * UPDATE with JOIN condition - 고객과 주문 아이템 조인하여 주문 상태 업데이트
     */
    int updateOrderStatusWithCustomer(Map<String, Object> params);

    /**
     * DELETE with JOIN condition - 역할과 조인하여 비활성 사용자 삭제
     */
    int deleteInactiveUsersWithRoles(Map<String, Object> params);

    /**
     * INSERT with JOIN condition - 카테고리와 조인하여 상품 등록
     */
    int insertProductWithCategory(Map<String, Object> params);

    /**
     * UPDATE with JOIN condition - 부서와 조인하여 사용자 정보 업데이트
     */
    int updateUserWithDepartment(Map<String, Object> params);

    /**
     * DELETE with JOIN condition - 주문과 조인하여 고객 삭제
     */
    int deleteCustomerWithOrders(Map<String, Object> params);

    /**
     * INSERT with JOIN condition - 상품과 주문 조인하여 주문 아이템 생성
     */
    int insertOrderItemWithProduct(Map<String, Object> params);

    /**
     * UPDATE with JOIN condition - 사용자 프로필과 조인하여 사용자 정보 업데이트
     */
    int updateUserWithProfile(Map<String, Object> params);

    /**
     * DELETE with JOIN condition - 상품과 카테고리 조인하여 상품 삭제
     */
    int deleteProductWithCategory(Map<String, Object> params);
}

