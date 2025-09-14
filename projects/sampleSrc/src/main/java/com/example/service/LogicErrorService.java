package com.example.service;

import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import com.example.model.User;
import com.example.mapper.UserMapper;
import java.util.List;
import java.util.ArrayList;

// 정상적인 서비스 - 로직 오류 수정됨
@Service
public class LogicErrorService {
    
    @Autowired
    private UserMapper userMapper;
    
    // 정상적인 메서드: null 체크 포함
    public User getUserById(Long id) {
        if (id == null || id <= 0) {
            return null;
        }
        return userMapper.selectById(id);
    }
    
    // 정상적인 메서드: 무한 루프 방지
    public List<User> getAllUsers() {
        List<User> users = userMapper.selectAll();
        if (users == null) {
            return new ArrayList<>();
        }
        return users;
    }
    
    // 정상적인 메서드: 적절한 예외 처리
    public void updateUser(User user) {
        if (user == null || user.getId() == null) {
            throw new IllegalArgumentException("사용자 정보 또는 ID가 null입니다.");
        }
        
        try {
            userMapper.update(user);
        } catch (Exception e) {
            throw new RuntimeException("사용자 정보 업데이트 중 오류가 발생했습니다.", e);
        }
    }
    
    // 정상적인 메서드: 적절한 리소스 관리
    public void processLargeData() {
        List<User> users = userMapper.selectAll();
        if (users != null && !users.isEmpty()) {
            for (User user : users) {
                // 실제 처리 로직
                if (user != null) {
                    // 사용자 데이터 처리
                    processUserData(user);
                }
            }
        }
    }
    
    // 정상적인 메서드: 사용자 데이터 처리
    private void processUserData(User user) {
        // 사용자 데이터 검증 및 처리 로직
        if (user.getName() != null && !user.getName().trim().isEmpty()) {
            // 이름 정규화
            user.setName(user.getName().trim());
        }
        
        if (user.getEmail() != null && user.getEmail().contains("@")) {
            // 이메일 소문자 변환
            user.setEmail(user.getEmail().toLowerCase());
        }
    }
    
    // 정상적인 메서드: 사용자 생성
    public void createUser(User user) {
        if (user == null) {
            throw new IllegalArgumentException("사용자 정보가 null입니다.");
        }
        
        if (user.getName() == null || user.getName().trim().isEmpty()) {
            throw new IllegalArgumentException("사용자 이름은 필수입니다.");
        }
        
        if (user.getEmail() == null || !user.getEmail().contains("@")) {
            throw new IllegalArgumentException("올바른 이메일을 입력해주세요.");
        }
        
        try {
            userMapper.insert(user);
        } catch (Exception e) {
            throw new RuntimeException("사용자 생성 중 오류가 발생했습니다.", e);
        }
    }
}
