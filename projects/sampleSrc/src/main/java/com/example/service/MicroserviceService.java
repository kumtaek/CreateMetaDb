package com.example.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.Map;

/**
 * 마이크로서비스 서비스 - 서비스 분리 예시
 */
@Service
public class MicroserviceService {

    @Autowired
    private MicroserviceDao microserviceDao;

    /**
     * 통합 사용자 정보 조회
     */
    public Map<String, Object> getUserProfile(Long userId) {
        return microserviceDao.selectUserProfile(userId);
    }

    /**
     * 통합 주문 정보 조회
     */
    public Map<String, Object> getOrderDetails(Long orderId) {
        return microserviceDao.selectOrderDetails(orderId);
    }

    /**
     * 통합 대시보드 데이터
     */
    public Map<String, Object> getDashboardData() {
        return microserviceDao.selectDashboardData();
    }

    /**
     * 통합 검색
     */
    public Map<String, Object> globalSearch(String query) {
        return microserviceDao.selectGlobalSearch(query);
    }

    /**
     * 통합 알림 발송
     */
    public Map<String, Object> sendNotification(Map<String, Object> notificationData) {
        return microserviceDao.insertNotification(notificationData);
    }
}
