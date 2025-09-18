package com.example.dao;

import com.example.model.User;
import com.example.model.Product;
import java.util.*;
import java.sql.*;

/**
 * 미지원 SQL 패턴들을 보여주는 DAO 클래스
 * 이 클래스의 메서드들은 현재 파서에서 지원하지 않는 패턴들을 보여줍니다
 */
public class UnsupportedPatternDao {
    
    // JDBC Connection (실제로는 의존성 주입으로 받아야 함)
    // private Connection connection;
    
    public UnsupportedPatternDao() {
        // 실제로는 Connection을 의존성 주입으로 받음
        // this.connection = dataSource.getConnection();
    }
    
    /**
     * 문자열 concat 함수와 + 연산자를 혼합한 패턴 (현재 미지원)
     */
    public List<User> findUsersByConcatPattern(String firstName, String lastName, String domain) {
        try {
            // concat 함수와 + 연산자를 혼합한 쿼리 (현재 미지원)
            String baseQuery = "SELECT u.user_id, ";
            baseQuery = baseQuery + "CONCAT(u.first_name, ' ', u.last_name) as full_name, ";
            baseQuery = baseQuery + "CONCAT(u.username, '@', '" + domain + "') as email_address, ";
            baseQuery = baseQuery + "u.status, u.created_date ";
            baseQuery = baseQuery + "FROM users u WHERE 1=1 ";
            
            String whereConditions = "";
            
            // 동적 조건 추가 (+ 연산자와 함수 혼합)
            if (firstName != null && !firstName.isEmpty()) {
                whereConditions = whereConditions + "AND UPPER(u.first_name) LIKE UPPER('%" + firstName + "%') ";
            }
            
            if (lastName != null && !lastName.isEmpty()) {
                whereConditions = whereConditions + "AND LOWER(u.last_name) = LOWER('" + lastName + "') ";
            }
            
            // CASE 문과 + 연산자 혼합 (현재 미지원)
            String caseClause = "AND CASE ";
            caseClause = caseClause + "WHEN u.user_type = 'ADMIN' THEN u.status = 'ACTIVE' ";
            caseClause = caseClause + "WHEN u.user_type = 'PREMIUM' THEN u.status IN ('ACTIVE', 'PENDING') ";
            caseClause = caseClause + "ELSE u.status != 'DELETED' END ";
            
            // 최종 쿼리 조합
            String finalQuery = baseQuery + whereConditions + caseClause;
            finalQuery = finalQuery + "ORDER BY u.created_date DESC, u.last_name ASC ";
            finalQuery = finalQuery + "LIMIT 50";
            
            System.out.println("Concat Pattern SQL: " + finalQuery);
            
            // 실제로는 JDBC를 통해 쿼리 실행
            // return executeUserQuery(finalQuery);
            
            // 임시 샘플 데이터 반환
            return generateSampleUsers(10);
            
        } catch (Exception e) {
            System.err.println("Concat 패턴 쿼리 중 오류: " + e.getMessage());
            throw new RuntimeException("Concat 패턴 쿼리 실패", e);
        }
    }
    
    /**
     * String.format과 동적 테이블명을 사용한 패턴 (현재 미지원)
     */
    public Map<String, Object> getAnalyticsByFormatAndDynamicTable(String tableSuffix, String dateFrom, String dateTo, String groupBy) {
        try {
            Map<String, Object> analytics = new HashMap<>();
            
            // 동적 테이블명과 String.format 혼합 (현재 미지원)
            String analyticsQuery = String.format(
                "SELECT %s, COUNT(*) as record_count, " +
                "AVG(CASE WHEN amount IS NOT NULL THEN amount ELSE 0 END) as avg_amount, " +
                "SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_count " +
                "FROM %s_%s " +
                "WHERE created_date BETWEEN '%s' AND '%s' " +
                "GROUP BY %s " +
                "ORDER BY record_count DESC",
                groupBy, "analytics", tableSuffix, dateFrom, dateTo, groupBy
            );
            
            // 추가 통계 쿼리들 (String.format 사용)
            String summaryQuery = String.format(
                "SELECT " +
                "(SELECT COUNT(*) FROM %s_%s WHERE created_date >= '%s') as total_records, " +
                "(SELECT AVG(amount) FROM %s_%s WHERE amount > 0 AND created_date >= '%s') as avg_amount, " +
                "(SELECT MAX(created_date) FROM %s_%s) as latest_record",
                "analytics", tableSuffix, dateFrom,
                "analytics", tableSuffix, dateFrom,
                "analytics", tableSuffix
            );
            
            // 트렌드 분석 쿼리 (+ 연산자와 String.format 혼합)
            String trendBase = String.format("SELECT DATE(%s) as date_key, COUNT(*) as daily_count ", "created_date");
            trendBase = trendBase + String.format("FROM %s_%s ", "analytics", tableSuffix);
            trendBase = trendBase + String.format("WHERE created_date BETWEEN '%s' AND '%s' ", dateFrom, dateTo);
            
            // 추가 조건 (+ 연산자)
            if (groupBy.equals("user_type")) {
                trendBase = trendBase + "AND user_type IS NOT NULL ";
            } else if (groupBy.equals("status")) {
                trendBase = trendBase + "AND status != 'DELETED' ";
            }
            
            String trendQuery = trendBase + "GROUP BY DATE(created_date) ORDER BY date_key ASC";
            
            System.out.println("Analytics Query (String.format + Dynamic Table): " + analyticsQuery);
            System.out.println("Summary Query (String.format): " + summaryQuery);
            System.out.println("Trend Query (Mixed Pattern): " + trendQuery);
            
            // 실제로는 각 쿼리를 실행하여 분석 결과 생성
            // analytics.put("groupedData", executeListQuery(analyticsQuery));
            // analytics.put("summary", executeObjectQuery(summaryQuery));
            // analytics.put("trends", executeListQuery(trendQuery));
            
            // 임시 샘플 분석 데이터
            analytics.put("totalRecords", 1250);
            analytics.put("avgAmount", 85000.0);
            analytics.put("completedCount", 980);
            analytics.put("tableSuffix", tableSuffix);
            analytics.put("period", dateFrom + " ~ " + dateTo);
            analytics.put("groupBy", groupBy);
            
            return analytics;
            
        } catch (Exception e) {
            System.err.println("String.format + 동적 테이블 분석 중 오류: " + e.getMessage());
            throw new RuntimeException("String.format + 동적 테이블 분석 실패", e);
        }
    }
    
    /**
     * 복잡한 CASE 문과 문자열 연결을 사용한 패턴 (현재 미지원)
     */
    public List<Map<String, Object>> getComplexCasePatternData(Map<String, Object> filters) {
        try {
            // 복잡한 CASE 문과 + 연산자 혼합 (현재 미지원)
            String complexQuery = "SELECT ";
            complexQuery = complexQuery + "u.user_id, u.username, ";
            
            // 복잡한 CASE 문 (+ 연산자로 구성)
            String caseExpression = "CASE ";
            caseExpression = caseExpression + "WHEN u.user_type = 'PREMIUM' AND u.status = 'ACTIVE' ";
            caseExpression = caseExpression + "THEN CONCAT('프리미엄 활성 사용자: ', u.username) ";
            caseExpression = caseExpression + "WHEN u.user_type = 'ADMIN' ";
            caseExpression = caseExpression + "THEN CONCAT('관리자: ', u.full_name, ' (', u.department, ')') ";
            caseExpression = caseExpression + "WHEN u.last_login_date < DATE_SUB(NOW(), INTERVAL 30 DAY) ";
            caseExpression = caseExpression + "THEN CONCAT('비활성 사용자: ', u.username, ' - 마지막 로그인: ', DATE_FORMAT(u.last_login_date, '%Y-%m-%d')) ";
            caseExpression = caseExpression + "ELSE CONCAT('일반 사용자: ', u.username) END as user_description, ";
            
            complexQuery = complexQuery + caseExpression;
            
            // 추가 계산 필드들 (+ 연산자 사용)
            String calculatedFields = "DATEDIFF(NOW(), u.created_date) as account_age_days, ";
            calculatedFields = calculatedFields + "CASE WHEN u.last_login_date IS NOT NULL ";
            calculatedFields = calculatedFields + "THEN DATEDIFF(NOW(), u.last_login_date) ";
            calculatedFields = calculatedFields + "ELSE -1 END as days_since_login ";
            
            complexQuery = complexQuery + calculatedFields;
            complexQuery = complexQuery + "FROM users u ";
            
            // 동적 WHERE 절 (혼합 패턴)
            String whereClause = "WHERE 1=1 ";
            
            if (filters.get("userType") != null) {
                whereClause = whereClause + String.format("AND u.user_type = '%s' ", filters.get("userType"));
            }
            
            if (filters.get("minAge") != null) {
                whereClause = whereClause + "AND u.age >= " + filters.get("minAge") + " ";
            }
            
            if (filters.get("department") != null) {
                whereClause = whereClause + "AND u.department = '" + filters.get("department") + "' ";
            }
            
            if (filters.get("includeInactive") == null || !((Boolean) filters.get("includeInactive"))) {
                whereClause = whereClause + "AND u.status != 'INACTIVE' ";
            }
            
            // 정렬 (String.format 사용)
            String orderBy = String.format("ORDER BY %s %s, u.username ASC ",
                                         filters.getOrDefault("sortField", "u.created_date"),
                                         filters.getOrDefault("sortDirection", "DESC"));
            
            // 페이징 (+ 연산자)
            String limit = "LIMIT " + filters.getOrDefault("pageSize", "25") + " ";
            limit = limit + "OFFSET " + filters.getOrDefault("offset", "0");
            
            // 최종 쿼리 조합
            String finalQuery = complexQuery + whereClause + orderBy + limit;
            
            System.out.println("Complex CASE Pattern SQL: " + finalQuery);
            
            // 실제로는 JDBC를 통해 쿼리 실행
            // return executeComplexQuery(finalQuery);
            
            // 임시 샘플 데이터 반환
            List<Map<String, Object>> results = new ArrayList<>();
            for (int i = 1; i <= 10; i++) {
                Map<String, Object> row = new HashMap<>();
                row.put("user_id", "USER" + String.format("%03d", i));
                row.put("username", "user" + i);
                row.put("user_description", "일반 사용자: user" + i);
                row.put("account_age_days", 30 + i * 10);
                row.put("days_since_login", i * 2);
                results.add(row);
            }
            
            return results;
            
        } catch (Exception e) {
            System.err.println("복잡한 CASE 패턴 쿼리 중 오류: " + e.getMessage());
            throw new RuntimeException("복잡한 CASE 패턴 쿼리 실패", e);
        }
    }
    
    /**
     * 서브쿼리와 문자열 조작을 혼합한 패턴 (현재 미지원)
     */
    public List<Map<String, Object>> getSubqueryWithStringManipulation(String operation, Map<String, Object> params) {
        try {
            String complexSubquerySQL = "";
            
            // 연산 타입별 서브쿼리 생성 (현재 미지원 패턴들)
            switch (operation.toLowerCase()) {
                case "user_summary":
                    // 사용자 요약 정보 (서브쿼리 + 문자열 조작)
                    complexSubquerySQL = "SELECT u.user_id, u.username, ";
                    complexSubquerySQL = complexSubquerySQL + "(SELECT COUNT(*) FROM orders o WHERE o.user_id = u.user_id) as order_count, ";
                    complexSubquerySQL = complexSubquerySQL + "(SELECT COALESCE(SUM(o.total_amount), 0) FROM orders o WHERE o.user_id = u.user_id) as total_spent, ";
                    
                    // String.format으로 서브쿼리 추가
                    String userCategorySubquery = String.format(
                        "(SELECT CASE " +
                        "WHEN (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.user_id AND o.total_amount > %d) > 5 THEN 'VIP' " +
                        "WHEN (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.user_id) > 10 THEN 'LOYAL' " +
                        "ELSE 'REGULAR' END) as user_category ",
                        (Integer) params.getOrDefault("vipThreshold", 100000)
                    );
                    
                    complexSubquerySQL = complexSubquerySQL + userCategorySubquery;
                    complexSubquerySQL = complexSubquerySQL + "FROM users u WHERE u.status = 'ACTIVE' ";
                    
                    // 추가 조건 (+ 연산자)
                    if (params.get("minOrders") != null) {
                        complexSubquerySQL = complexSubquerySQL + "HAVING order_count >= " + params.get("minOrders") + " ";
                    }
                    
                    complexSubquerySQL = complexSubquerySQL + "ORDER BY total_spent DESC, order_count DESC";
                    break;
                    
                case "product_analytics":
                    // 상품 분석 정보 (복잡한 서브쿼리 패턴)
                    complexSubquerySQL = "SELECT p.product_id, p.product_name, p.price, ";
                    
                    // 여러 서브쿼리들 (+ 연산자로 조합)
                    String salesSubquery = "(SELECT COUNT(*) FROM order_items oi ";
                    salesSubquery = salesSubquery + "JOIN orders o ON oi.order_id = o.order_id ";
                    salesSubquery = salesSubquery + "WHERE oi.product_id = p.product_id ";
                    salesSubquery = salesSubquery + "AND o.order_date >= '" + params.getOrDefault("dateFrom", "2024-01-01") + "') as sales_count, ";
                    
                    String revenueSubquery = "(SELECT COALESCE(SUM(oi.quantity * oi.unit_price), 0) ";
                    revenueSubquery = revenueSubquery + "FROM order_items oi JOIN orders o ON oi.order_id = o.order_id ";
                    revenueSubquery = revenueSubquery + "WHERE oi.product_id = p.product_id ";
                    revenueSubquery = revenueSubquery + "AND o.order_date >= '" + params.getOrDefault("dateFrom", "2024-01-01") + "') as total_revenue ";
                    
                    complexSubquerySQL = complexSubquerySQL + salesSubquery + revenueSubquery;
                    complexSubquerySQL = complexSubquerySQL + "FROM products p WHERE p.status = 'ACTIVE' ";
                    
                    // String.format으로 HAVING 절 추가
                    if (params.get("minSales") != null) {
                        complexSubquerySQL = complexSubquerySQL + String.format("HAVING sales_count >= %d ", (Integer) params.get("minSales"));
                    }
                    
                    complexSubquerySQL = complexSubquerySQL + "ORDER BY total_revenue DESC, sales_count DESC";
                    break;
                    
                default:
                    // 기본 서브쿼리 패턴
                    complexSubquerySQL = "SELECT u.user_id, u.username, ";
                    complexSubquerySQL = complexSubquerySQL + "(SELECT COUNT(*) FROM user_activities ua WHERE ua.user_id = u.user_id) as activity_count ";
                    complexSubquerySQL = complexSubquerySQL + "FROM users u WHERE u.status = 'ACTIVE' ";
                    complexSubquerySQL = complexSubquerySQL + "ORDER BY activity_count DESC LIMIT 20";
                    break;
            }
            
            System.out.println("Subquery with String Manipulation (" + operation + "): " + complexSubquerySQL);
            
            // 실제로는 JDBC를 통해 쿼리 실행
            // return executeComplexSubquery(complexSubquerySQL);
            
            // 임시 샘플 데이터 반환
            List<Map<String, Object>> results = new ArrayList<>();
            for (int i = 1; i <= 8; i++) {
                Map<String, Object> row = new HashMap<>();
                row.put("id", "ID" + String.format("%03d", i));
                row.put("name", operation + "_item_" + i);
                row.put("count", 10 + i * 5);
                row.put("amount", 50000.0 + i * 15000);
                results.add(row);
            }
            
            return results;
            
        } catch (Exception e) {
            System.err.println("서브쿼리 + 문자열 조작 패턴 중 오류: " + e.getMessage());
            throw new RuntimeException("서브쿼리 + 문자열 조작 패턴 실패", e);
        }
    }
    
    // 유틸리티 메서드들
    
    private List<User> generateSampleUsers(int count) {
        List<User> users = new ArrayList<>();
        Random random = new Random();
        
        for (int i = 1; i <= count; i++) {
            User user = new User();
            user.setUserId("UNSUPPORTED_USER" + String.format("%03d", i));
            user.setUsername("unsupported_user" + i);
            user.setFullName("미지원패턴 사용자" + i);
            user.setEmail("unsupported" + i + "@example.com");
            user.setPhone("010-9999-" + String.format("%04d", 1000 + i));
            user.setStatus(i % 3 == 0 ? "INACTIVE" : "ACTIVE");
            user.setUserType(i % 4 == 0 ? "PREMIUM" : "NORMAL");
            user.setCreatedDate(new Date(System.currentTimeMillis() - random.nextInt(180 * 24 * 60 * 60 * 1000)));
            user.setLastLoginDate(new Date(System.currentTimeMillis() - random.nextInt(7 * 24 * 60 * 60 * 1000)));
            user.setIsAdmin(i == 1);
            user.setIsPremium(i % 4 == 0);
            user.setEmailVerified(i % 2 == 0);
            user.setPhoneVerified(i % 3 == 0);
            
            users.add(user);
        }
        
        return users;
    }
}
