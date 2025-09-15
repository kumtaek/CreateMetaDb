package com.example.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.Map;

/**
 * 버전별 서비스 - 버전 관리 예시
 */
@Service
public class VersionedService {

    @Autowired
    private VersionedDao versionedDao;

    /**
     * 사용자 조회 - v1 API
     */
    public Map<String, Object> getUsersV1() {
        return versionedDao.selectUsersV1();
    }

    /**
     * 사용자 조회 - v2 API (개선된 버전)
     */
    public Map<String, Object> getUsersV2() {
        return versionedDao.selectUsersV2();
    }

    /**
     * 제품 조회 - v1 API
     */
    public Map<String, Object> getProductsV1() {
        return versionedDao.selectProductsV1();
    }

    /**
     * 제품 조회 - v2 API (페이징 지원)
     */
    public Map<String, Object> getProductsV2(int page, int size) {
        return versionedDao.selectProductsV2(page, size);
    }

    /**
     * 주문 조회 - v1 API
     */
    public Map<String, Object> getOrdersV1() {
        return versionedDao.selectOrdersV1();
    }

    /**
     * 주문 조회 - v2 API (필터링 지원)
     */
    public Map<String, Object> getOrdersV2(String status, String dateFrom, String dateTo) {
        return versionedDao.selectOrdersV2(status, dateFrom, dateTo);
    }
}
