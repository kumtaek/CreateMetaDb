package com.example.dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;
import java.util.Map;

/**
 * 사용자 관리 DAO - 1:N 관계 예시
 */
@Mapper
public interface UserManagementDao {

    /**
     * 사용자 목록 조회
     */
    List<Map<String, Object>> selectUsers();

    /**
     * 사용자 상세 조회
     */
    Map<String, Object> selectUserById(@Param("userId") Long userId);

    /**
     * 사용자 생성
     */
    int insertUser(@Param("userData") Map<String, Object> userData);

    /**
     * 사용자 수정
     */
    int updateUser(@Param("userId") Long userId, @Param("userData") Map<String, Object> userData);

    /**
     * 사용자 삭제
     */
    int deleteUser(@Param("userId") Long userId);

    /**
     * 사용자 통계 조회
     */
    Map<String, Object> selectUserStatistics();
}
