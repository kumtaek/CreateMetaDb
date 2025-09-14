package com.example.service;

import com.example.model.User;
import java.util.List;
import java.util.Map;

public interface UserService {
    
    List<User> getUsersByCondition(Map<String, Object> params);
    
    List<User> getUsersByAdvancedCondition(Map<String, Object> params);
    
    List<User> getUsersByType(String type);
    
    User getUserById(Long id);
    
    int updateUserDynamic(User user);
    
    int deleteUsersByCondition(Map<String, Object> params);
}