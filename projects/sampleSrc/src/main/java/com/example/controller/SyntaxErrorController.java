package com.example.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.RequestParam;
import com.example.model.User;
import com.example.service.UserService;
import java.util.List;

// 정상적인 컨트롤러 - 문법 오류 수정됨
@Controller
@RequestMapping("/syntax-fixed")
public class SyntaxErrorController {
    
    private UserService userService;
    
    // 정상적인 메서드
    @RequestMapping(value = "/test1", method = RequestMethod.GET)
    @ResponseBody
    public String test1() {
        return "Hello World";
    }
    
    // 정상적인 메서드
    @RequestMapping(value = "/test2", method = RequestMethod.GET)
    @ResponseBody
    public String test2() {
        if (true) {
            return "Valid syntax";
        }
        return "OK";
    }
    
    // 정상적인 메서드
    @RequestMapping(value = "/users", method = RequestMethod.GET)
    @ResponseBody
    public List<User> getAllUsers() {
        return userService.getAllUsers();
    }
    
    // 정상적인 메서드
    @RequestMapping(value = "/user", method = RequestMethod.GET)
    @ResponseBody
    public User getUserById(@RequestParam Long id) {
        return userService.getUserById(id);
    }
    
    // 정상적인 메서드
    @RequestMapping(value = "/user", method = RequestMethod.POST)
    @ResponseBody
    public String createUser(@RequestParam String name, @RequestParam String email) {
        try {
            User user = new User();
            user.setName(name);
            user.setEmail(email);
            userService.createUser(user);
            return "사용자가 생성되었습니다.";
        } catch (Exception e) {
            return "사용자 생성 중 오류가 발생했습니다.";
        }
    }
}
