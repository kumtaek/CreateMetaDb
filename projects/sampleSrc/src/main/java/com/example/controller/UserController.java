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
@RequestMapping("/user")
public class UserController {
    
    @Autowired
    private UserService userService;
    
    @GetMapping("/list")
    public String getUserList(@RequestParam(required = false) String name,
                             @RequestParam(required = false) String email,
                             @RequestParam(required = false) String status,
                             @RequestParam(defaultValue = "0") int page,
                             @RequestParam(defaultValue = "10") int size,
                             Model model) {
        
        try {
            // 입력 파라미터 검증
            validateSearchParameters(name, email, status);
            
            // 다이나믹 쿼리 파라미터 구성
            Map<String, Object> params = new java.util.HashMap<>();
            if (name != null && !name.trim().isEmpty()) {
                params.put("name", "%" + name.trim() + "%");
            }
            if (email != null && !email.trim().isEmpty()) {
                params.put("email", "%" + email.trim() + "%");
            }
            if (status != null && !status.trim().isEmpty()) {
                params.put("status", status.toUpperCase());
            }
            
            // 페이징 파라미터 추가
            params.put("offset", page * size);
            params.put("limit", size);
            
            // 비즈니스 로직: 사용자 목록 조회
            List<User> users = userService.getUsersByCondition(params);
            
            // 비즈니스 로직: 통계 정보 계산
            Map<String, Object> statistics = calculateUserStatistics(users);
            
            // 모델에 데이터 추가
            model.addAttribute("users", users);
            model.addAttribute("searchParams", params);
            model.addAttribute("statistics", statistics);
            model.addAttribute("currentPage", page);
            model.addAttribute("pageSize", size);
            model.addAttribute("totalUsers", users.size());
            
            // 로그 기록
            logUserListAccess(name, email, status, users.size());
            
            return "user/list";
            
        } catch (Exception e) {
            model.addAttribute("error", "사용자 목록 조회 중 오류가 발생했습니다: " + e.getMessage());
            return "user/error";
        }
    }
    
    @PostMapping("/search")
    public String searchUsers(@RequestParam Map<String, String> searchParams, 
                             @RequestParam(defaultValue = "0") int page,
                             @RequestParam(defaultValue = "20") int size,
                             Model model) {
        
        try {
            // 입력 파라미터 검증
            validateAdvancedSearchParameters(searchParams);
            
            // 복잡한 다이나믹 쿼리 조건 구성
            Map<String, Object> params = new java.util.HashMap<>();
            
            if (searchParams.get("userType") != null && !searchParams.get("userType").trim().isEmpty()) {
                params.put("userType", searchParams.get("userType").toUpperCase());
            }
            
            if (searchParams.get("minAge") != null && !searchParams.get("minAge").trim().isEmpty()) {
                int minAge = Integer.parseInt(searchParams.get("minAge"));
                if (minAge >= 0 && minAge <= 150) {
                    params.put("minAge", minAge);
                }
            }
            
            if (searchParams.get("maxAge") != null && !searchParams.get("maxAge").trim().isEmpty()) {
                int maxAge = Integer.parseInt(searchParams.get("maxAge"));
                if (maxAge >= 0 && maxAge <= 150) {
                    params.put("maxAge", maxAge);
                }
            }
            
            // 날짜 범위 검색
            if (searchParams.get("startDate") != null && !searchParams.get("startDate").trim().isEmpty()) {
                params.put("startDate", searchParams.get("startDate"));
            }
            
            if (searchParams.get("endDate") != null && !searchParams.get("endDate").trim().isEmpty()) {
                params.put("endDate", searchParams.get("endDate"));
            }
            
            // 상태별 필터링
            if (searchParams.get("statusList") != null && !searchParams.get("statusList").trim().isEmpty()) {
                String[] statusArray = searchParams.get("statusList").split(",");
                List<String> statusList = Arrays.asList(statusArray);
                params.put("statusList", statusList);
            }
            
            // 페이징 파라미터
            params.put("offset", page * size);
            params.put("limit", size);
            
            // 비즈니스 로직: 고급 검색 실행
            List<User> users = userService.getUsersByAdvancedCondition(params);
            
            // 비즈니스 로직: 검색 결과 분석
            Map<String, Object> searchAnalysis = analyzeSearchResults(users, params);
            
            // 모델에 데이터 추가
            model.addAttribute("users", users);
            model.addAttribute("searchParams", searchParams);
            model.addAttribute("searchAnalysis", searchAnalysis);
            model.addAttribute("currentPage", page);
            model.addAttribute("pageSize", size);
            model.addAttribute("totalResults", users.size());
            
            // 검색 로그 기록
            logAdvancedSearch(searchParams, users.size());
            
            return "user/searchResult";
            
        } catch (NumberFormatException e) {
            model.addAttribute("error", "나이 입력이 올바르지 않습니다.");
            return "user/error";
        } catch (Exception e) {
            model.addAttribute("error", "고급 검색 중 오류가 발생했습니다: " + e.getMessage());
            return "user/error";
        }
    }
    
    @GetMapping("/dynamic/{type}")
    public String getUsersByType(@PathVariable String type, 
                                @RequestParam(defaultValue = "0") int page,
                                @RequestParam(defaultValue = "15") int size,
                                Model model) {
        
        try {
            // 타입 검증
            if (!isValidUserType(type)) {
                model.addAttribute("error", "유효하지 않은 사용자 타입입니다: " + type);
                return "user/error";
            }
            
            // 타입별 다이나믹 쿼리
            List<User> users = userService.getUsersByType(type);
            
            // 비즈니스 로직: 페이징 처리
            List<User> pagedUsers = applyPaging(users, page, size);
            
            // 비즈니스 로직: 타입별 통계 계산
            Map<String, Object> typeStatistics = calculateTypeStatistics(users, type);
            
            // 모델에 데이터 추가
            model.addAttribute("users", pagedUsers);
            model.addAttribute("userType", type);
            model.addAttribute("typeStatistics", typeStatistics);
            model.addAttribute("currentPage", page);
            model.addAttribute("pageSize", size);
            model.addAttribute("totalUsers", users.size());
            model.addAttribute("totalPages", (int) Math.ceil((double) users.size() / size));
            
            // 타입별 조회 로그
            logTypeBasedAccess(type, users.size());
            
            return "user/typeList";
            
        } catch (Exception e) {
            model.addAttribute("error", "타입별 사용자 조회 중 오류가 발생했습니다: " + e.getMessage());
            return "user/error";
        }
    }
    
    // 비즈니스 로직 메서드들
    private void validateSearchParameters(String name, String email, String status) {
        if (name != null && name.length() > 100) {
            throw new IllegalArgumentException("이름은 100자를 초과할 수 없습니다.");
        }
        if (email != null && email.length() > 200) {
            throw new IllegalArgumentException("이메일은 200자를 초과할 수 없습니다.");
        }
    }
    
    private void validateAdvancedSearchParameters(Map<String, String> searchParams) {
        if (searchParams.get("minAge") != null && searchParams.get("maxAge") != null) {
            try {
                int minAge = Integer.parseInt(searchParams.get("minAge"));
                int maxAge = Integer.parseInt(searchParams.get("maxAge"));
                if (minAge > maxAge) {
                    throw new IllegalArgumentException("최소 나이는 최대 나이보다 클 수 없습니다.");
                }
            } catch (NumberFormatException e) {
                throw new IllegalArgumentException("나이 입력이 올바르지 않습니다.");
            }
        }
    }
    
    private Map<String, Object> calculateUserStatistics(List<User> users) {
        Map<String, Object> stats = new HashMap<>();
        
        long activeCount = users.stream().filter(u -> "ACTIVE".equals(u.getStatus())).count();
        long inactiveCount = users.stream().filter(u -> "INACTIVE".equals(u.getStatus())).count();
        
        double avgAge = users.stream()
                .filter(u -> u.getAge() != null)
                .mapToInt(User::getAge)
                .average()
                .orElse(0.0);
        
        stats.put("totalCount", users.size());
        stats.put("activeCount", activeCount);
        stats.put("inactiveCount", inactiveCount);
        stats.put("averageAge", Math.round(avgAge * 100.0) / 100.0);
        
        return stats;
    }
    
    private Map<String, Object> analyzeSearchResults(List<User> users, Map<String, Object> params) {
        Map<String, Object> analysis = new HashMap<>();
        
        analysis.put("searchCriteria", params.keySet().size());
        analysis.put("resultCount", users.size());
        analysis.put("hasResults", !users.isEmpty());
        
        if (!users.isEmpty()) {
            analysis.put("ageRange", calculateAgeRange(users));
            analysis.put("statusDistribution", calculateStatusDistribution(users));
        }
        
        return analysis;
    }
    
    private Map<String, Object> calculateTypeStatistics(List<User> users, String type) {
        Map<String, Object> stats = new HashMap<>();
        
        stats.put("type", type);
        stats.put("totalCount", users.size());
        
        if (!users.isEmpty()) {
            double avgAge = users.stream()
                    .filter(u -> u.getAge() != null)
                    .mapToInt(User::getAge)
                    .average()
                    .orElse(0.0);
            stats.put("averageAge", Math.round(avgAge * 100.0) / 100.0);
            
            long activeCount = users.stream().filter(u -> "ACTIVE".equals(u.getStatus())).count();
            stats.put("activePercentage", Math.round((double) activeCount / users.size() * 100));
        }
        
        return stats;
    }
    
    private List<User> applyPaging(List<User> users, int page, int size) {
        int start = page * size;
        int end = Math.min(start + size, users.size());
        
        if (start >= users.size()) {
            return new ArrayList<>();
        }
        
        return users.subList(start, end);
    }
    
    private boolean isValidUserType(String type) {
        return Arrays.asList("NORMAL", "PREMIUM", "ADMIN", "GUEST").contains(type.toUpperCase());
    }
    
    private Map<String, Integer> calculateAgeRange(List<User> users) {
        Map<String, Integer> ageRange = new HashMap<>();
        
        int minAge = users.stream()
                .filter(u -> u.getAge() != null)
                .mapToInt(User::getAge)
                .min()
                .orElse(0);
        
        int maxAge = users.stream()
                .filter(u -> u.getAge() != null)
                .mapToInt(User::getAge)
                .max()
                .orElse(0);
        
        ageRange.put("min", minAge);
        ageRange.put("max", maxAge);
        
        return ageRange;
    }
    
    private Map<String, Long> calculateStatusDistribution(List<User> users) {
        return users.stream()
                .collect(java.util.stream.Collectors.groupingBy(
                    u -> u.getStatus() != null ? u.getStatus() : "UNKNOWN",
                    java.util.stream.Collectors.counting()
                ));
    }
    
    private void logUserListAccess(String name, String email, String status, int resultCount) {
        System.out.println("User list accessed: name=" + name + 
                          ", email=" + email + 
                          ", status=" + status + 
                          ", results=" + resultCount + 
                          ", time=" + new java.util.Date());
    }
    
    private void logAdvancedSearch(Map<String, String> searchParams, int resultCount) {
        System.out.println("Advanced search executed: " + searchParams + 
                          ", results=" + resultCount + 
                          ", time=" + new java.util.Date());
    }
    
    private void logTypeBasedAccess(String type, int resultCount) {
        System.out.println("Type-based access: type=" + type + 
                          ", results=" + resultCount + 
                          ", time=" + new java.util.Date());
    }
}