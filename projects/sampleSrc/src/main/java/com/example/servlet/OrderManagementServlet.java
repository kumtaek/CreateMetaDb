package com.example.servlet;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

/**
 * service() 메서드를 오버라이드한 주문 관리 Servlet
 * 모든 HTTP 메서드를 하나의 service() 메서드에서 처리하는 방식
 * doGet, doPost 등의 개별 메서드 대신 service()에서 HTTP 메서드를 구분하여 처리
 */
public class OrderManagementServlet extends HttpServlet {
    
    private static final long serialVersionUID = 1L;
    
    @Override
    protected void service(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        // HTTP 메서드에 따른 분기 처리
        String method = request.getMethod();
        
        // 응답 타입 설정
        response.setContentType("application/json; charset=UTF-8");
        response.setHeader("Access-Control-Allow-Origin", "*");
        response.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
        response.setHeader("Access-Control-Allow-Headers", "Content-Type");
        
        PrintWriter out = response.getWriter();
        
        try {
            switch (method.toUpperCase()) {
                case "GET":
                    handleGetRequest(request, response, out);
                    break;
                case "POST":
                    handlePostRequest(request, response, out);
                    break;
                case "PUT":
                    handlePutRequest(request, response, out);
                    break;
                case "DELETE":
                    handleDeleteRequest(request, response, out);
                    break;
                case "OPTIONS":
                    handleOptionsRequest(request, response, out);
                    break;
                default:
                    handleUnsupportedMethod(request, response, out, method);
                    break;
            }
        } catch (Exception e) {
            handleError(request, response, out, e);
        }
    }
    
    private void handleGetRequest(HttpServletRequest request, HttpServletResponse response, PrintWriter out) 
            throws IOException {
        
        String action = request.getParameter("action");
        Map<String, Object> result = new HashMap<>();
        
        switch (action) {
            case "list":
                result.put("method", "GET");
                result.put("action", "주문 목록 조회");
                result.put("orders", getOrderList());
                result.put("totalCount", getOrderList().size());
                break;
                
            case "detail":
                String orderId = request.getParameter("orderId");
                result.put("method", "GET");
                result.put("action", "주문 상세 조회");
                result.put("orderId", orderId);
                result.put("order", getOrderDetail(orderId));
                break;
                
            case "status":
                String statusOrderId = request.getParameter("orderId");
                result.put("method", "GET");
                result.put("action", "주문 상태 조회");
                result.put("orderId", statusOrderId);
                result.put("status", getOrderStatus(statusOrderId));
                break;
                
            default:
                result.put("method", "GET");
                result.put("action", "기본 조회");
                result.put("message", "사용 가능한 액션: list, detail, status");
        }
        
        result.put("timestamp", new Date().toString());
        result.put("success", true);
        
        out.println(formatJsonResponse(result));
    }
    
    private void handlePostRequest(HttpServletRequest request, HttpServletResponse response, PrintWriter out) 
            throws IOException {
        
        String action = request.getParameter("action");
        Map<String, Object> result = new HashMap<>();
        
        switch (action) {
            case "create":
                String customerId = request.getParameter("customerId");
                String productId = request.getParameter("productId");
                String quantity = request.getParameter("quantity");
                
                result.put("method", "POST");
                result.put("action", "새 주문 생성");
                result.put("customerId", customerId);
                result.put("productId", productId);
                result.put("quantity", quantity);
                result.put("orderId", generateOrderId());
                result.put("status", "PENDING");
                break;
                
            case "cancel":
                String cancelOrderId = request.getParameter("orderId");
                result.put("method", "POST");
                result.put("action", "주문 취소");
                result.put("orderId", cancelOrderId);
                result.put("newStatus", "CANCELLED");
                break;
                
            default:
                result.put("method", "POST");
                result.put("action", "기본 생성");
                result.put("message", "사용 가능한 액션: create, cancel");
        }
        
        result.put("timestamp", new Date().toString());
        result.put("success", true);
        
        out.println(formatJsonResponse(result));
    }
    
    private void handlePutRequest(HttpServletRequest request, HttpServletResponse response, PrintWriter out) 
            throws IOException {
        
        String action = request.getParameter("action");
        Map<String, Object> result = new HashMap<>();
        
        switch (action) {
            case "update":
                String updateOrderId = request.getParameter("orderId");
                String newQuantity = request.getParameter("quantity");
                String newStatus = request.getParameter("status");
                
                result.put("method", "PUT");
                result.put("action", "주문 정보 수정");
                result.put("orderId", updateOrderId);
                result.put("quantity", newQuantity);
                result.put("status", newStatus);
                break;
                
            case "status":
                String statusOrderId = request.getParameter("orderId");
                String status = request.getParameter("status");
                
                result.put("method", "PUT");
                result.put("action", "주문 상태 변경");
                result.put("orderId", statusOrderId);
                result.put("oldStatus", getOrderStatus(statusOrderId));
                result.put("newStatus", status);
                break;
                
            default:
                result.put("method", "PUT");
                result.put("action", "기본 수정");
                result.put("message", "사용 가능한 액션: update, status");
        }
        
        result.put("timestamp", new Date().toString());
        result.put("success", true);
        
        out.println(formatJsonResponse(result));
    }
    
    private void handleDeleteRequest(HttpServletRequest request, HttpServletResponse response, PrintWriter out) 
            throws IOException {
        
        String orderId = request.getParameter("orderId");
        Map<String, Object> result = new HashMap<>();
        
        result.put("method", "DELETE");
        result.put("action", "주문 삭제");
        result.put("orderId", orderId);
        result.put("timestamp", new Date().toString());
        result.put("success", true);
        result.put("message", "주문이 성공적으로 삭제되었습니다.");
        
        out.println(formatJsonResponse(result));
    }
    
    private void handleOptionsRequest(HttpServletRequest request, HttpServletResponse response, PrintWriter out) 
            throws IOException {
        
        Map<String, Object> result = new HashMap<>();
        result.put("method", "OPTIONS");
        result.put("action", "CORS 프리플라이트 요청");
        result.put("allowedMethods", new String[]{"GET", "POST", "PUT", "DELETE", "OPTIONS"});
        result.put("timestamp", new Date().toString());
        result.put("success", true);
        
        out.println(formatJsonResponse(result));
    }
    
    private void handleUnsupportedMethod(HttpServletRequest request, HttpServletResponse response, PrintWriter out, String method) 
            throws IOException {
        
        response.setStatus(HttpServletResponse.SC_METHOD_NOT_ALLOWED);
        
        Map<String, Object> result = new HashMap<>();
        result.put("method", method);
        result.put("action", "지원하지 않는 HTTP 메서드");
        result.put("error", "Method Not Allowed");
        result.put("message", method + " 메서드는 지원하지 않습니다.");
        result.put("timestamp", new Date().toString());
        result.put("success", false);
        
        out.println(formatJsonResponse(result));
    }
    
    private void handleError(HttpServletRequest request, HttpServletResponse response, PrintWriter out, Exception e) 
            throws IOException {
        
        response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
        
        Map<String, Object> result = new HashMap<>();
        result.put("method", request.getMethod());
        result.put("action", "오류 처리");
        result.put("error", "Internal Server Error");
        result.put("message", "서버 내부 오류가 발생했습니다: " + e.getMessage());
        result.put("timestamp", new Date().toString());
        result.put("success", false);
        
        out.println(formatJsonResponse(result));
    }
    
    // 비즈니스 로직 메서드들 (실제 구현은 DB 연동)
    private Map<String, Object> getOrderList() {
        Map<String, Object> orders = new HashMap<>();
        orders.put("ORDER001", createSampleOrder("ORDER001", "CUST001", "P001", 2, "PENDING"));
        orders.put("ORDER002", createSampleOrder("ORDER002", "CUST002", "P002", 1, "SHIPPED"));
        orders.put("ORDER003", createSampleOrder("ORDER003", "CUST003", "P003", 3, "DELIVERED"));
        return orders;
    }
    
    private Map<String, Object> getOrderDetail(String orderId) {
        if ("ORDER001".equals(orderId)) {
            return createSampleOrder("ORDER001", "CUST001", "P001", 2, "PENDING");
        } else if ("ORDER002".equals(orderId)) {
            return createSampleOrder("ORDER002", "CUST002", "P002", 1, "SHIPPED");
        } else if ("ORDER003".equals(orderId)) {
            return createSampleOrder("ORDER003", "CUST003", "P003", 3, "DELIVERED");
        }
        return null;
    }
    
    private String getOrderStatus(String orderId) {
        Map<String, Object> order = getOrderDetail(orderId);
        return order != null ? (String) order.get("status") : "NOT_FOUND";
    }
    
    private String generateOrderId() {
        return "ORDER" + String.format("%03d", (int)(Math.random() * 1000));
    }
    
    private Map<String, Object> createSampleOrder(String orderId, String customerId, String productId, int quantity, String status) {
        Map<String, Object> order = new HashMap<>();
        order.put("orderId", orderId);
        order.put("customerId", customerId);
        order.put("productId", productId);
        order.put("quantity", quantity);
        order.put("status", status);
        order.put("orderDate", new Date().toString());
        order.put("totalAmount", quantity * 50000); // 샘플 가격
        return order;
    }
    
    private String formatJsonResponse(Map<String, Object> data) {
        StringBuilder json = new StringBuilder();
        json.append("{\n");
        
        boolean first = true;
        for (Map.Entry<String, Object> entry : data.entrySet()) {
            if (!first) {
                json.append(",\n");
            }
            json.append("  \"").append(entry.getKey()).append("\": ");
            
            Object value = entry.getValue();
            if (value instanceof String) {
                json.append("\"").append(value).append("\"");
            } else if (value instanceof Number || value instanceof Boolean) {
                json.append(value);
            } else {
                json.append("\"").append(value.toString()).append("\"");
            }
            first = false;
        }
        
        json.append("\n}");
        return json.toString();
    }
}
