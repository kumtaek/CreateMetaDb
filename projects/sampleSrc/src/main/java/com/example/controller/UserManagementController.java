package com.example.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.util.List;
import java.util.Map;

/**
 * 사용자 관리 컨트롤러 - 1:N 관계 예시
 * 하나의 프론트엔드 페이지에서 여러 API를 호출하는 경우
 */
@RestController
@RequestMapping("/api/user-management")
public class UserManagementController {

    /**
     * 사용자 목록 조회
     * FRONTEND_API: UserManagementPage -> API_ENTRY: GET /api/user-management/users
     */
    @GetMapping("/users")
    public ResponseEntity<List<Map<String, Object>>> getUsers() {
        // 사용자 목록 조회 로직
        return ResponseEntity.ok().build();
    }

    /**
     * 사용자 상세 조회
     * FRONTEND_API: UserManagementPage -> API_ENTRY: GET /api/user-management/users/{id}
     */
    @GetMapping("/users/{id}")
    public ResponseEntity<Map<String, Object>> getUserDetail(@PathVariable Long id) {
        // 사용자 상세 조회 로직
        return ResponseEntity.ok().build();
    }

    /**
     * 사용자 생성
     * FRONTEND_API: UserManagementPage -> API_ENTRY: POST /api/user-management/users
     */
    @PostMapping("/users")
    public ResponseEntity<Map<String, Object>> createUser(@RequestBody Map<String, Object> userData) {
        // 사용자 생성 로직
        return ResponseEntity.ok().build();
    }

    /**
     * 사용자 수정
     * FRONTEND_API: UserManagementPage -> API_ENTRY: PUT /api/user-management/users/{id}
     */
    @PutMapping("/users/{id}")
    public ResponseEntity<Map<String, Object>> updateUser(@PathVariable Long id, @RequestBody Map<String, Object> userData) {
        // 사용자 수정 로직
        return ResponseEntity.ok().build();
    }

    /**
     * 사용자 삭제
     * FRONTEND_API: UserManagementPage -> API_ENTRY: DELETE /api/user-management/users/{id}
     */
    @DeleteMapping("/users/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
        // 사용자 삭제 로직
        return ResponseEntity.ok().build();
    }

    /**
     * 사용자 통계 조회
     * FRONTEND_API: UserManagementPage -> API_ENTRY: GET /api/user-management/statistics
     */
    @GetMapping("/statistics")
    public ResponseEntity<Map<String, Object>> getUserStatistics() {
        // 사용자 통계 조회 로직
        return ResponseEntity.ok().build();
    }
}
