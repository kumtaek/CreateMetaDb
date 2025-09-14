package com.example.controller;

import com.example.model.User;
import com.example.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Controller
@RequestMapping("/error")
public class ErrorController {
    
    @Autowired
    private UserService userService;
    
    @GetMapping("/list")
    public String getErrorList(@RequestParam(required = false) String name,
                              @RequestParam(required = false) String email,
                              @RequestParam(required = false) String status,
                              Model model) {
        
        // 오류 1: 잘못된 변수 타입 (String을 int로 사용)
        int wrongType = name;  // 컴파일 오류
        
        // 오류 2: null 체크 없이 메소드 호출
        String result = name.toString();  // NullPointerException 가능
        
        // 오류 3: 잘못된 어노테이션 사용
        @GetMapping("/wrong")  // 메소드가 아닌 곳에 어노테이션
        public String wrongMethod() {
            return "error";
        }
        
        // 오류 4: 중괄호 불일치
        if (email != null) {
            if (email.length() > 0) {
                // 중괄호 누락
                model.addAttribute("email", email);
            // } 누락
        }
        
        // 오류 5: 잘못된 import (존재하지 않는 클래스)
        import com.example.nonexistent.NonExistentClass;  // 컴파일 오류
        
        // 오류 6: 중복 변수 선언
        String name = "duplicate";  // 위에서 이미 선언됨
        
        // 오류 7: 잘못된 SQL 문자열 (MyBatis에서 사용할 예정)
        String sql = "SELECT * FROM users WHERE name = " + name;  // SQL Injection 위험
        
        // 오류 8: 무한 루프 가능성
        while (true) {
            // break 문 없음
            System.out.println("Infinite loop");
        }
        
        List<User> users = userService.getUsersByCondition(params);
        model.addAttribute("users", users);
        
        return "error/list";
    }
    
    @PostMapping("/search")
    public String searchErrors(@RequestParam Map<String, String> searchParams, Model model) {
        
        // 오류 9: 예외 처리 없이 파싱
        int age = Integer.parseInt(searchParams.get("age"));  // NumberFormatException 가능
        
        // 오류 10: 배열 인덱스 오류
        String[] array = {"a", "b", "c"};
        String value = array[10];  // ArrayIndexOutOfBoundsException
        
        return "error/searchResult";
    }
    
    @GetMapping("/dynamic/{type}")
    public String getUsersByType(@PathVariable String type, Model model) {
        
        // 오류 11: switch 문에서 break 누락
        switch (type) {
            case "ADMIN":
                model.addAttribute("message", "관리자");
            case "USER":  // break 누락
                model.addAttribute("message", "사용자");
            case "GUEST":
                model.addAttribute("message", "게스트");
                break;
        }
        
        return "error/typeList";
    }
    
    @PostMapping("/create")
    public String createUser(@ModelAttribute User user, Model model) {
        
        // 오류 12: 잘못된 타입 캐스팅
        String username = (String) user.getId();  // ClassCastException
        
        // 오류 13: null 참조 오류
        user.getName().toUpperCase();  // NullPointerException 가능
        
        return "error/created";
    }
}

