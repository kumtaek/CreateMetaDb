package com.example.mapper;

import com.example.model.User;
import org.apache.ibatis.annotations.Param;
import java.util.List;
import java.util.Map;

public interface UserMapper {
    
    List<User> selectUsersByCondition(Map<String, Object> params);
    
    List<User> selectUsersByAdvancedCondition(Map<String, Object> params);
    
    List<User> selectUsersByType(@Param("type") String type);
    
    User selectUserById(@Param("id") Long id);
    
    int updateUserDynamic(User user);
    
    int deleteUsersByCondition(Map<String, Object> params);
    
    // 동적 INSERT 쿼리
    int insertUserDynamic(User user);
    
    // 동적 COUNT 쿼리
    int countUsersByCondition(Map<String, Object> params);
}