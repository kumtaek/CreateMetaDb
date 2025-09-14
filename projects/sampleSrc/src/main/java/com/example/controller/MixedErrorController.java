package com.example.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.RequestParam;
import com.example.model.User;
import com.example.service.UserService;
import java.util.List;

// 일부 오류가 있는 컨트롤러 - 정상 부분과 오류 부분이 섞여있음
@Controller
@RequestMapping("/mixed-error")
public class MixedErrorController {
    
    private UserService userService;
    
    // 정상적인 메서드
    @RequestMapping(value = "/users", method = RequestMethod.GET)
    @ResponseBody
    public List<User> getAllUsers() {
        return userService.getAllUsers();
    }
    
    // 정상적인 메서드
    @RequestMapping(value = "/user/{id}", method = RequestMethod.GET)
    @ResponseBody
    public User getUserById(@RequestParam Long id) {
        return userService.getUserById(id);
    }
    
    // 일부 오류가 있는 메서드 - 정상적인 부분과 오류 부분이 섞여있음
    @RequestMapping(value = "/user", method = RequestMethod.POST)
    @ResponseBody
    public String createUser(@RequestParam String name, @RequestParam String email) {
        // 정상적인 부분
        if (name == null || name.trim().isEmpty()) {
            return "이름은 필수입니다.";
        }
        
        // 정상적인 부분
        if (email == null || !email.contains("@")) {
            return "올바른 이메일을 입력해주세요.";
        }
        
        // 오류 부분: 세미콜론 누락
        User user = new User()
        user.setName(name);
        user.setEmail(email);
        
        // 정상적인 부분
        try {
            userService.createUser(user);
            return "사용자가 생성되었습니다.";
        } catch (Exception e) {
            return "사용자 생성 중 오류가 발생했습니다.";
        }
    }
    
    // 일부 오류가 있는 메서드
    @RequestMapping(value = "/user/{id}", method = RequestMethod.PUT)
    @ResponseBody
    public String updateUser(@RequestParam Long id, @RequestParam String name) {
        // 정상적인 부분
        if (id == null || id <= 0) {
            return "유효하지 않은 ID입니다.";
        }
        
        // 정상적인 부분
        User existingUser = userService.getUserById(id);
        if (existingUser == null) {
            return "사용자를 찾을 수 없습니다.";
        }
        
        // 오류 부분: 잘못된 메서드 호출
        existingUser.setName(name);
        existingUser.setUpdateDate(new Date());  // Date import 누락으로 컴파일 오류
        
        // 정상적인 부분
        try {
            userService.updateUser(existingUser);
            return "사용자 정보가 업데이트되었습니다.";
        } catch (Exception e) {
            return "업데이트 중 오류가 발생했습니다.";
        }
    }
    
    // 정상적인 메서드
    @RequestMapping(value = "/user/{id}", method = RequestMethod.DELETE)
    @ResponseBody
    public String deleteUser(@RequestParam Long id) {
        try {
            userService.deleteUser(id);
            return "사용자가 삭제되었습니다.";
        } catch (Exception e) {
            return "삭제 중 오류가 발생했습니다.";
        }
    }
}
