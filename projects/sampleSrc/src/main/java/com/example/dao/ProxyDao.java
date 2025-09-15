package com.example.dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.Map;

/**
 * 프록시 DAO - 다른 URL 매핑 예시
 */
@Mapper
public interface ProxyDao {

    /**
     * v1 API에서 사용자 조회
     */
    Map<String, Object> selectUsersFromV1();

    /**
     * v1 API에 사용자 생성
     */
    int insertUserToV1(@Param("userData") Map<String, Object> userData);

    /**
     * 내부 제품 서비스에서 제품 조회
     */
    Map<String, Object> selectProductsFromInternalService();

    /**
     * 내부 주문 서비스에서 주문 조회
     */
    Map<String, Object> selectOrdersFromInternalService();

    /**
     * 외부 결제 게이트웨이에서 결제 처리
     */
    Map<String, Object> processPaymentExternal(@Param("paymentData") Map<String, Object> paymentData);
}
