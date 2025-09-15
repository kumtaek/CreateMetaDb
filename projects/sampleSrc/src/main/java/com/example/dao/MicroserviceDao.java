package com.example.dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.Map;

/**
 * 마이크로서비스 DAO - 서비스 분리 예시
 */
@Mapper
public interface MicroserviceDao {

    /**
     * 통합 사용자 정보 조회
     */
    Map<String, Object> selectUserProfile(@Param("userId") Long userId);

    /**
     * 통합 주문 정보 조회
     */
    Map<String, Object> selectOrderDetails(@Param("orderId") Long orderId);

    /**
     * 통합 대시보드 데이터
     */
    Map<String, Object> selectDashboardData();

    /**
     * 통합 검색
     */
    Map<String, Object> selectGlobalSearch(@Param("query") String query);

    /**
     * 통합 알림 발송
     */
    Map<String, Object> insertNotification(@Param("notificationData") Map<String, Object> notificationData);
}
