package com.example.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Map;

/**
 * 사용자 관리 서비스 - 1:N 관계 예시
 */
@Service
public class UserManagementService {

    @Autowired
    private UserManagementDao userManagementDao;

    /**
     * 사용자 목록 조회
     */
    public List<Map<String, Object>> getUsers() {
        return userManagementDao.selectUsers();
    }

    /**
     * 사용자 상세 조회
     */
    public Map<String, Object> getUserDetail(Long userId) {
        return userManagementDao.selectUserById(userId);
    }

    /**
     * 사용자 생성
     */
    public int createUser(Map<String, Object> userData) {
        return userManagementDao.insertUser(userData);
    }

    /**
     * 사용자 수정
     */
    public int updateUser(Long userId, Map<String, Object> userData) {
        return userManagementDao.updateUser(userId, userData);
    }

    /**
     * 사용자 삭제
     */
    public int deleteUser(Long userId) {
        return userManagementDao.deleteUser(userId);
    }

    /**
     * 사용자 통계 조회
     */
    public Map<String, Object> getUserStatistics() {
        return userManagementDao.selectUserStatistics();
    }
}
