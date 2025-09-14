package com.example.service;

import org.springframework.stereotype.Service;
import com.example.model.User;
import com.example.mapper.UserMapper;
import java.util.List;
import java.util.ArrayList;

// 일부 오류가 있는 서비스 - 정상 부분과 오류 부분이 섞여있음
@Service
public class MixedErrorService {
    
    private UserMapper userMapper;
    
    // 정상적인 메서드
    public List<User> getAllUsers() {
        return userMapper.selectAll();
    }
    
    // 정상적인 메서드
    public User getUserById(Long id) {
        if (id == null || id <= 0) {
            return null;
        }
        return userMapper.selectById(id);
    }
    
    // 일부 오류가 있는 메서드
    public void createUser(User user) {
        // 정상적인 부분
        if (user == null) {
            throw new IllegalArgumentException("사용자 정보가 null입니다.");
        }
        
        // 정상적인 부분
        if (user.getName() == null || user.getName().trim().isEmpty()) {
            throw new IllegalArgumentException("사용자 이름은 필수입니다.");
        }
        
        // 정상적인 부분
        if (user.getEmail() == null || !user.getEmail().contains("@")) {
            throw new IllegalArgumentException("올바른 이메일을 입력해주세요.");
        }
        
        // 오류 부분: 잘못된 메서드 호출
        user.setCreateDate(new Date());  // Date import 누락
        
        // 정상적인 부분
        try {
            userMapper.insert(user);
        } catch (Exception e) {
            throw new RuntimeException("사용자 생성 중 오류가 발생했습니다.", e);
        }
    }
    
    // 일부 오류가 있는 메서드
    public void updateUser(User user) {
        // 정상적인 부분
        if (user == null || user.getId() == null) {
            throw new IllegalArgumentException("사용자 정보 또는 ID가 null입니다.");
        }
        
        // 정상적인 부분
        User existingUser = userMapper.selectById(user.getId());
        if (existingUser == null) {
            throw new IllegalArgumentException("존재하지 않는 사용자입니다.");
        }
        
        // 오류 부분: 잘못된 메서드 호출
        user.setUpdateDate(new Date());  // Date import 누락
        
        // 정상적인 부분
        try {
            userMapper.update(user);
        } catch (Exception e) {
            throw new RuntimeException("사용자 정보 업데이트 중 오류가 발생했습니다.", e);
        }
    }
    
    // 정상적인 메서드
    public void deleteUser(Long id) {
        if (id == null || id <= 0) {
            throw new IllegalArgumentException("유효하지 않은 ID입니다.");
        }
        
        User existingUser = userMapper.selectById(id);
        if (existingUser == null) {
            throw new IllegalArgumentException("존재하지 않는 사용자입니다.");
        }
        
        try {
            userMapper.delete(id);
        } catch (Exception e) {
            throw new RuntimeException("사용자 삭제 중 오류가 발생했습니다.", e);
        }
    }
    
    // 일부 오류가 있는 메서드
    public List<User> searchUsers(String keyword) {
        // 정상적인 부분
        if (keyword == null || keyword.trim().isEmpty()) {
            return new ArrayList<>();
        }
        
        // 정상적인 부분
        String searchKeyword = "%" + keyword.trim() + "%";
        
        // 오류 부분: 잘못된 메서드 호출
        return userMapper.searchByName(searchKeyword);  // 존재하지 않는 메서드 호출
    }
}
