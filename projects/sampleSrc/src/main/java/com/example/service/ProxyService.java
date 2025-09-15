package com.example.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.Map;

/**
 * 프록시 서비스 - 다른 URL 매핑 예시
 */
@Service
public class ProxyService {

    @Autowired
    private ProxyDao proxyDao;

    /**
     * 사용자 조회 - 프록시 패턴
     */
    public Map<String, Object> getUsers() {
        return proxyDao.selectUsersFromV1();
    }

    /**
     * 사용자 생성 - 프록시 패턴
     */
    public int createUser(Map<String, Object> userData) {
        return proxyDao.insertUserToV1(userData);
    }

    /**
     * 제품 조회 - 게이트웨이 패턴
     */
    public Map<String, Object> getProducts() {
        return proxyDao.selectProductsFromInternalService();
    }

    /**
     * 주문 조회 - 마이크로서비스 패턴
     */
    public Map<String, Object> getOrders() {
        return proxyDao.selectOrdersFromInternalService();
    }

    /**
     * 결제 처리 - 외부 서비스 연동
     */
    public Map<String, Object> processPayment(Map<String, Object> paymentData) {
        return proxyDao.processPaymentExternal(paymentData);
    }
}
