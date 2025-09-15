package com.example.servlet;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.*;

/**
 * 직접 쿼리 조합 Servlet
 * MyBatis를 사용하지 않고 Java에서 직접 SQL 쿼리를 조합하여 실행
 * 동적 쿼리 생성과 실행을 테스트하기 위한 샘플
 */
@WebServlet(urlPatterns = {"/direct-query/*", "/api/v1/direct-query"})
public class DirectQueryServlet extends HttpServlet {
    
    private static final long serialVersionUID = 1L;
    
    // 데이터베이스 연결 정보 (실제로는 설정 파일에서 읽어야 함)
    private static final String DB_URL = "jdbc:oracle:thin:@localhost:1521:XE";
    private static final String DB_USER = "sample_user";
    private static final String DB_PASSWORD = "sample_password";
    
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        String action = request.getParameter("action");
        Map<String, Object> result = new HashMap<>();
        
        try {
            switch (action) {
                case "users":
                    result = queryUsersDirectly(request);
                    break;
                case "orders":
                    result = queryOrdersDirectly(request);
                    break;
                case "products":
                    result = queryProductsDirectly(request);
                    break;
                case "statistics":
                    result = queryStatisticsDirectly(request);
                    break;
                case "complex":
                    result = queryComplexDataDirectly(request);
                    break;
                default:
                    result.put("success", false);
                    result.put("error", "알 수 없는 액션: " + action);
                    result.put("availableActions", Arrays.asList("users", "orders", "products", "statistics", "complex"));
            }
            
            result.put("timestamp", new Date().toString());
            result.put("method", "GET");
            result.put("action", action);
            
        } catch (Exception e) {
            result.put("success", false);
            result.put("error", "쿼리 실행 중 오류 발생: " + e.getMessage());
            result.put("timestamp", new Date().toString());
        }
        
        out.println(formatJsonResponse(result));
        out.flush();
    }
    
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        String action = request.getParameter("action");
        Map<String, Object> result = new HashMap<>();
        
        try {
            switch (action) {
                case "insert":
                    result = insertDataDirectly(request);
                    break;
                case "update":
                    result = updateDataDirectly(request);
                    break;
                case "delete":
                    result = deleteDataDirectly(request);
                    break;
                case "batch":
                    result = batchOperationDirectly(request);
                    break;
                default:
                    result.put("success", false);
                    result.put("error", "알 수 없는 액션: " + action);
                    result.put("availableActions", Arrays.asList("insert", "update", "delete", "batch"));
            }
            
            result.put("timestamp", new Date().toString());
            result.put("method", "POST");
            result.put("action", action);
            
        } catch (Exception e) {
            result.put("success", false);
            result.put("error", "쿼리 실행 중 오류 발생: " + e.getMessage());
            result.put("timestamp", new Date().toString());
        }
        
        out.println(formatJsonResponse(result));
        out.flush();
    }
    
    /**
     * 직접 쿼리로 사용자 조회
     */
    private Map<String, Object> queryUsersDirectly(HttpServletRequest request) throws SQLException {
        Map<String, Object> result = new HashMap<>();
        
        // 동적 쿼리 생성
        StringBuilder query = new StringBuilder();
        List<Object> parameters = new ArrayList<>();
        
        query.append("SELECT u.user_id, u.username, u.full_name, u.email, u.phone, ");
        query.append("u.status, u.user_type, u.created_date, u.last_login_date ");
        query.append("FROM users u WHERE u.del_yn = 'N' ");
        
        // 검색 조건 추가
        String searchKeyword = request.getParameter("searchKeyword");
        String searchType = request.getParameter("searchType");
        
        if (searchKeyword != null && !searchKeyword.trim().isEmpty()) {
            switch (searchType) {
                case "username":
                    query.append("AND u.username LIKE ? ");
                    parameters.add("%" + searchKeyword + "%");
                    break;
                case "email":
                    query.append("AND u.email LIKE ? ");
                    parameters.add("%" + searchKeyword + "%");
                    break;
                case "name":
                    query.append("AND u.full_name LIKE ? ");
                    parameters.add("%" + searchKeyword + "%");
                    break;
                default:
                    query.append("AND (u.username LIKE ? OR u.email LIKE ? OR u.full_name LIKE ?) ");
                    parameters.add("%" + searchKeyword + "%");
                    parameters.add("%" + searchKeyword + "%");
                    parameters.add("%" + searchKeyword + "%");
                    break;
            }
        }
        
        // 상태 필터
        String status = request.getParameter("status");
        if (status != null && !status.trim().isEmpty()) {
            query.append("AND u.status = ? ");
            parameters.add(status);
        }
        
        // 사용자 타입 필터
        String userType = request.getParameter("userType");
        if (userType != null && !userType.trim().isEmpty()) {
            query.append("AND u.user_type = ? ");
            parameters.add(userType);
        }
        
        // 날짜 범위 필터
        String startDate = request.getParameter("startDate");
        String endDate = request.getParameter("endDate");
        if (startDate != null && !startDate.trim().isEmpty()) {
            query.append("AND u.created_date >= ? ");
            parameters.add(startDate);
        }
        if (endDate != null && !endDate.trim().isEmpty()) {
            query.append("AND u.created_date <= ? ");
            parameters.add(endDate);
        }
        
        // 정렬
        String orderBy = request.getParameter("orderBy");
        String orderDirection = request.getParameter("orderDirection");
        if (orderBy != null && !orderBy.trim().isEmpty()) {
            query.append("ORDER BY u.").append(orderBy).append(" ");
            query.append("DESC".equals(orderDirection) ? "DESC" : "ASC");
        } else {
            query.append("ORDER BY u.created_date DESC");
        }
        
        // 페이징
        int page = Integer.parseInt(request.getParameter("page") != null ? request.getParameter("page") : "1");
        int pageSize = Integer.parseInt(request.getParameter("pageSize") != null ? request.getParameter("pageSize") : "10");
        int offset = (page - 1) * pageSize;
        
        query.append(" LIMIT ? OFFSET ?");
        parameters.add(pageSize);
        parameters.add(offset);
        
        System.out.println("생성된 쿼리: " + query.toString());
        System.out.println("파라미터: " + parameters);
        
        // 실제로는 데이터베이스에 연결하여 쿼리 실행
        // List<Map<String, Object>> users = executeQuery(query.toString(), parameters);
        
        // 임시 샘플 데이터 반환
        result.put("success", true);
        result.put("query", query.toString());
        result.put("parameters", parameters);
        result.put("users", generateSampleUserData());
        result.put("totalCount", 150);
        result.put("currentPage", page);
        result.put("pageSize", pageSize);
        
        return result;
    }
    
    /**
     * 직접 쿼리로 주문 조회
     */
    private Map<String, Object> queryOrdersDirectly(HttpServletRequest request) throws SQLException {
        Map<String, Object> result = new HashMap<>();
        
        StringBuilder query = new StringBuilder();
        List<Object> parameters = new ArrayList<>();
        
        query.append("SELECT o.order_id, o.user_id, u.username, u.full_name, ");
        query.append("o.order_date, o.total_amount, o.status, o.payment_method ");
        query.append("FROM orders o ");
        query.append("JOIN users u ON o.user_id = u.user_id ");
        query.append("WHERE o.del_yn = 'N' AND u.del_yn = 'N' ");
        
        // 사용자 ID 필터
        String userId = request.getParameter("userId");
        if (userId != null && !userId.trim().isEmpty()) {
            query.append("AND o.user_id = ? ");
            parameters.add(userId);
        }
        
        // 주문 상태 필터
        String status = request.getParameter("status");
        if (status != null && !status.trim().isEmpty()) {
            query.append("AND o.status = ? ");
            parameters.add(status);
        }
        
        // 결제 방법 필터
        String paymentMethod = request.getParameter("paymentMethod");
        if (paymentMethod != null && !paymentMethod.trim().isEmpty()) {
            query.append("AND o.payment_method = ? ");
            parameters.add(paymentMethod);
        }
        
        // 금액 범위 필터
        String minAmount = request.getParameter("minAmount");
        String maxAmount = request.getParameter("maxAmount");
        if (minAmount != null && !minAmount.trim().isEmpty()) {
            query.append("AND o.total_amount >= ? ");
            parameters.add(Double.parseDouble(minAmount));
        }
        if (maxAmount != null && !maxAmount.trim().isEmpty()) {
            query.append("AND o.total_amount <= ? ");
            parameters.add(Double.parseDouble(maxAmount));
        }
        
        query.append("ORDER BY o.order_date DESC");
        
        System.out.println("생성된 주문 쿼리: " + query.toString());
        
        result.put("success", true);
        result.put("query", query.toString());
        result.put("parameters", parameters);
        result.put("orders", generateSampleOrderData());
        
        return result;
    }
    
    /**
     * 직접 쿼리로 상품 조회
     */
    private Map<String, Object> queryProductsDirectly(HttpServletRequest request) throws SQLException {
        Map<String, Object> result = new HashMap<>();
        
        StringBuilder query = new StringBuilder();
        List<Object> parameters = new ArrayList<>();
        
        query.append("SELECT p.product_id, p.product_name, p.category, p.price, ");
        query.append("p.stock_quantity, p.status, p.created_date, ");
        query.append("c.category_name ");
        query.append("FROM products p ");
        query.append("LEFT JOIN categories c ON p.category_id = c.category_id ");
        query.append("WHERE p.del_yn = 'N' ");
        
        // 상품명 검색
        String productName = request.getParameter("productName");
        if (productName != null && !productName.trim().isEmpty()) {
            query.append("AND p.product_name LIKE ? ");
            parameters.add("%" + productName + "%");
        }
        
        // 카테고리 필터
        String category = request.getParameter("category");
        if (category != null && !category.trim().isEmpty()) {
            query.append("AND p.category = ? ");
            parameters.add(category);
        }
        
        // 가격 범위 필터
        String minPrice = request.getParameter("minPrice");
        String maxPrice = request.getParameter("maxPrice");
        if (minPrice != null && !minPrice.trim().isEmpty()) {
            query.append("AND p.price >= ? ");
            parameters.add(Double.parseDouble(minPrice));
        }
        if (maxPrice != null && !maxPrice.trim().isEmpty()) {
            query.append("AND p.price <= ? ");
            parameters.add(Double.parseDouble(maxPrice));
        }
        
        // 재고 필터
        String inStock = request.getParameter("inStock");
        if ("true".equals(inStock)) {
            query.append("AND p.stock_quantity > 0 ");
        }
        
        query.append("ORDER BY p.product_name ASC");
        
        System.out.println("생성된 상품 쿼리: " + query.toString());
        
        result.put("success", true);
        result.put("query", query.toString());
        result.put("parameters", parameters);
        result.put("products", generateSampleProductData());
        
        return result;
    }
    
    /**
     * 직접 쿼리로 통계 조회
     */
    private Map<String, Object> queryStatisticsDirectly(HttpServletRequest request) throws SQLException {
        Map<String, Object> result = new HashMap<>();
        
        String statType = request.getParameter("statType");
        
        switch (statType) {
            case "userStats":
                result = getUserStatisticsDirectly();
                break;
            case "orderStats":
                result = getOrderStatisticsDirectly();
                break;
            case "productStats":
                result = getProductStatisticsDirectly();
                break;
            case "salesStats":
                result = getSalesStatisticsDirectly();
                break;
            default:
                result.put("success", false);
                result.put("error", "알 수 없는 통계 타입: " + statType);
        }
        
        return result;
    }
    
    /**
     * 복잡한 조인 쿼리 실행
     */
    private Map<String, Object> queryComplexDataDirectly(HttpServletRequest request) throws SQLException {
        Map<String, Object> result = new HashMap<>();
        
        StringBuilder query = new StringBuilder();
        List<Object> parameters = new ArrayList<>();
        
        query.append("SELECT u.user_id, u.username, u.full_name, u.email, ");
        query.append("COUNT(o.order_id) as order_count, ");
        query.append("COALESCE(SUM(o.total_amount), 0) as total_spent, ");
        query.append("MAX(o.order_date) as last_order_date, ");
        query.append("COUNT(DISTINCT p.product_id) as unique_products_purchased ");
        query.append("FROM users u ");
        query.append("LEFT JOIN orders o ON u.user_id = o.user_id AND o.del_yn = 'N' ");
        query.append("LEFT JOIN order_items oi ON o.order_id = oi.order_id ");
        query.append("LEFT JOIN products p ON oi.product_id = p.product_id AND p.del_yn = 'N' ");
        query.append("WHERE u.del_yn = 'N' ");
        
        // 그룹핑 조건 추가
        String groupBy = request.getParameter("groupBy");
        if ("userType".equals(groupBy)) {
            query.append("GROUP BY u.user_type, u.user_id, u.username, u.full_name, u.email ");
        } else {
            query.append("GROUP BY u.user_id, u.username, u.full_name, u.email ");
        }
        
        // 필터링 조건
        String minOrderCount = request.getParameter("minOrderCount");
        if (minOrderCount != null && !minOrderCount.trim().isEmpty()) {
            query.append("HAVING order_count >= ? ");
            parameters.add(Integer.parseInt(minOrderCount));
        }
        
        String minTotalSpent = request.getParameter("minTotalSpent");
        if (minTotalSpent != null && !minTotalSpent.trim().isEmpty()) {
            if (minOrderCount != null) {
                query.append("AND total_spent >= ? ");
            } else {
                query.append("HAVING total_spent >= ? ");
            }
            parameters.add(Double.parseDouble(minTotalSpent));
        }
        
        query.append("ORDER BY total_spent DESC");
        
        System.out.println("생성된 복잡한 쿼리: " + query.toString());
        
        result.put("success", true);
        result.put("query", query.toString());
        result.put("parameters", parameters);
        result.put("complexData", generateSampleComplexData());
        
        return result;
    }
    
    /**
     * 직접 INSERT 쿼리 실행
     */
    private Map<String, Object> insertDataDirectly(HttpServletRequest request) throws SQLException {
        Map<String, Object> result = new HashMap<>();
        
        String tableName = request.getParameter("tableName");
        
        switch (tableName) {
            case "users":
                result = insertUserDirectly(request);
                break;
            case "orders":
                result = insertOrderDirectly(request);
                break;
            case "products":
                result = insertProductDirectly(request);
                break;
            default:
                result.put("success", false);
                result.put("error", "지원하지 않는 테이블: " + tableName);
        }
        
        return result;
    }
    
    private Map<String, Object> insertUserDirectly(HttpServletRequest request) throws SQLException {
        Map<String, Object> result = new HashMap<>();
        
        StringBuilder query = new StringBuilder();
        List<Object> parameters = new ArrayList<>();
        
        query.append("INSERT INTO users (username, full_name, email, phone, password, status, user_type, created_date) ");
        query.append("VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
        
        parameters.add(request.getParameter("username"));
        parameters.add(request.getParameter("fullName"));
        parameters.add(request.getParameter("email"));
        parameters.add(request.getParameter("phone"));
        parameters.add(hashPassword(request.getParameter("password")));
        parameters.add(request.getParameter("status") != null ? request.getParameter("status") : "ACTIVE");
        parameters.add(request.getParameter("userType") != null ? request.getParameter("userType") : "NORMAL");
        parameters.add(new Date());
        
        System.out.println("생성된 INSERT 쿼리: " + query.toString());
        
        // 실제로는 데이터베이스에 INSERT 실행
        // int rowsAffected = executeUpdate(query.toString(), parameters);
        
        result.put("success", true);
        result.put("query", query.toString());
        result.put("parameters", parameters);
        result.put("message", "사용자 생성 완료");
        result.put("userId", "USER" + System.currentTimeMillis());
        
        return result;
    }
    
    // 기타 메서드들...
    
    private Map<String, Object> getUserStatisticsDirectly() {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("totalUsers", 150);
        result.put("activeUsers", 120);
        result.put("newUsersToday", 8);
        result.put("premiumUsers", 25);
        return result;
    }
    
    private Map<String, Object> getOrderStatisticsDirectly() {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("totalOrders", 450);
        result.put("totalRevenue", 1250000);
        result.put("averageOrderValue", 2777);
        result.put("ordersToday", 12);
        return result;
    }
    
    private Map<String, Object> getProductStatisticsDirectly() {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("totalProducts", 85);
        result.put("activeProducts", 78);
        result.put("outOfStockProducts", 7);
        result.put("totalCategories", 12);
        return result;
    }
    
    private Map<String, Object> getSalesStatisticsDirectly() {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("todaySales", 150000);
        result.put("thisMonthSales", 450000);
        result.put("topSellingProduct", "노트북");
        result.put("topCategory", "전자제품");
        return result;
    }
    
    private Map<String, Object> insertOrderDirectly(HttpServletRequest request) {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("message", "주문 생성 완료");
        result.put("orderId", "ORDER" + System.currentTimeMillis());
        return result;
    }
    
    private Map<String, Object> insertProductDirectly(HttpServletRequest request) {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("message", "상품 생성 완료");
        result.put("productId", "PRODUCT" + System.currentTimeMillis());
        return result;
    }
    
    private Map<String, Object> updateDataDirectly(HttpServletRequest request) {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("message", "데이터 수정 완료");
        return result;
    }
    
    private Map<String, Object> deleteDataDirectly(HttpServletRequest request) {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("message", "데이터 삭제 완료");
        return result;
    }
    
    private Map<String, Object> batchOperationDirectly(HttpServletRequest request) {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("message", "배치 작업 완료");
        result.put("processedCount", 25);
        return result;
    }
    
    // 샘플 데이터 생성 메서드들
    
    private List<Map<String, Object>> generateSampleUserData() {
        List<Map<String, Object>> users = new ArrayList<>();
        for (int i = 1; i <= 10; i++) {
            Map<String, Object> user = new HashMap<>();
            user.put("userId", "USER" + String.format("%03d", i));
            user.put("username", "user" + i);
            user.put("fullName", "사용자" + i);
            user.put("email", "user" + i + "@example.com");
            user.put("phone", "010-1234-" + String.format("%04d", 1000 + i));
            user.put("status", i % 4 == 0 ? "INACTIVE" : "ACTIVE");
            user.put("userType", i % 5 == 0 ? "PREMIUM" : "NORMAL");
            user.put("createdDate", new Date().toString());
            users.add(user);
        }
        return users;
    }
    
    private List<Map<String, Object>> generateSampleOrderData() {
        List<Map<String, Object>> orders = new ArrayList<>();
        for (int i = 1; i <= 5; i++) {
            Map<String, Object> order = new HashMap<>();
            order.put("orderId", "ORDER" + String.format("%03d", i));
            order.put("userId", "USER" + String.format("%03d", i));
            order.put("username", "user" + i);
            order.put("totalAmount", 100000 + (i * 50000));
            order.put("status", "COMPLETED");
            order.put("orderDate", new Date().toString());
            orders.add(order);
        }
        return orders;
    }
    
    private List<Map<String, Object>> generateSampleProductData() {
        List<Map<String, Object>> products = new ArrayList<>();
        String[] productNames = {"노트북", "마우스", "키보드", "모니터", "스피커"};
        String[] categories = {"전자제품", "컴퓨터", "오디오", "모니터", "입력장치"};
        
        for (int i = 0; i < productNames.length; i++) {
            Map<String, Object> product = new HashMap<>();
            product.put("productId", "PRODUCT" + String.format("%03d", i + 1));
            product.put("productName", productNames[i]);
            product.put("category", categories[i]);
            product.put("price", 50000 + (i * 30000));
            product.put("stockQuantity", 100 - (i * 10));
            product.put("status", "ACTIVE");
            products.add(product);
        }
        return products;
    }
    
    private List<Map<String, Object>> generateSampleComplexData() {
        List<Map<String, Object>> complexData = new ArrayList<>();
        for (int i = 1; i <= 5; i++) {
            Map<String, Object> data = new HashMap<>();
            data.put("userId", "USER" + String.format("%03d", i));
            data.put("username", "user" + i);
            data.put("orderCount", 5 + i);
            data.put("totalSpent", 200000 + (i * 100000));
            data.put("lastOrderDate", new Date().toString());
            data.put("uniqueProductsPurchased", 3 + i);
            complexData.add(data);
        }
        return complexData;
    }
    
    private String hashPassword(String password) {
        // 실제로는 BCrypt 등 안전한 해싱 알고리즘 사용
        return "hashed_" + password.hashCode();
    }
    
    private String formatJsonResponse(Map<String, Object> data) {
        StringBuilder json = new StringBuilder();
        json.append("{\n");
        
        boolean first = true;
        for (Map.Entry<String, Object> entry : data.entrySet()) {
            if (!first) json.append(",\n");
            json.append("  \"").append(entry.getKey()).append("\": ");
            
            Object value = entry.getValue();
            if (value instanceof String) {
                json.append("\"").append(value).append("\"");
            } else if (value instanceof Number || value instanceof Boolean) {
                json.append(value);
            } else if (value instanceof List) {
                json.append(formatList((List<?>) value));
            } else {
                json.append("\"").append(value.toString()).append("\"");
            }
            first = false;
        }
        
        json.append("\n}");
        return json.toString();
    }
    
    private String formatList(List<?> list) {
        StringBuilder sb = new StringBuilder();
        sb.append("[");
        for (int i = 0; i < list.size(); i++) {
            if (i > 0) sb.append(", ");
            if (list.get(i) instanceof Map) {
                sb.append(formatMap((Map<?, ?>) list.get(i)));
            } else {
                sb.append("\"").append(list.get(i)).append("\"");
            }
        }
        sb.append("]");
        return sb.toString();
    }
    
    private String formatMap(Map<?, ?> map) {
        StringBuilder sb = new StringBuilder();
        sb.append("{");
        boolean first = true;
        for (Map.Entry<?, ?> entry : map.entrySet()) {
            if (!first) sb.append(", ");
            sb.append("\"").append(entry.getKey()).append("\": \"").append(entry.getValue()).append("\"");
            first = false;
        }
        sb.append("}");
        return sb.toString();
    }
}
