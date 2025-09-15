package com.example.dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.Map;

/**
 * 버전별 DAO - 버전 관리 예시
 */
@Mapper
public interface VersionedDao {

    /**
     * 사용자 조회 - v1 API
     */
    Map<String, Object> selectUsersV1();

    /**
     * 사용자 조회 - v2 API (개선된 버전)
     */
    Map<String, Object> selectUsersV2();

    /**
     * 제품 조회 - v1 API
     */
    Map<String, Object> selectProductsV1();

    /**
     * 제품 조회 - v2 API (페이징 지원)
     */
    Map<String, Object> selectProductsV2(@Param("page") int page, @Param("size") int size);

    /**
     * 주문 조회 - v1 API
     */
    Map<String, Object> selectOrdersV1();

    /**
     * 주문 조회 - v2 API (필터링 지원)
     */
    Map<String, Object> selectOrdersV2(@Param("status") String status, 
                                      @Param("dateFrom") String dateFrom, 
                                      @Param("dateTo") String dateTo);
}
