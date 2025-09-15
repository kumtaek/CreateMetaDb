package com.example.servlet;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.HashMap;
import java.util.Map;

/**
 * @WebServlet 어노테이션을 사용한 사용자 관리 Servlet
 * 다양한 HTTP 메서드와 URL 패턴을 테스트하기 위한 샘플
 */
@WebServlet(urlPatterns = {"/user/*", "/api/v1/users", "/admin/user-management"})
public class UserManagementServlet extends HttpServlet {
    
    private static final long serialVersionUID = 1L;
    
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        String pathInfo = request.getPathInfo();
        String servletPath = request.getServletPath();
        
        Map<String, Object> result = new HashMap<>();
        result.put("method", "GET");
        result.put("pathInfo", pathInfo);
        result.put("servletPath", servletPath);
        result.put("timestamp", System.currentTimeMillis());
        result.put("action", "사용자 목록 조회");
        
        // JSON 응답 생성 (간단한 형태)
        out.println("{");
        out.println("  \"status\": \"success\",");
        out.println("  \"data\": " + result.toString() + ",");
        out.println("  \"message\": \"사용자 목록을 성공적으로 조회했습니다.\"");
        out.println("}");
        
        out.flush();
    }
    
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        // 요청 파라미터 처리
        String username = request.getParameter("username");
        String email = request.getParameter("email");
        String role = request.getParameter("role");
        
        Map<String, Object> result = new HashMap<>();
        result.put("method", "POST");
        result.put("username", username);
        result.put("email", email);
        result.put("role", role);
        result.put("timestamp", System.currentTimeMillis());
        result.put("action", "새 사용자 생성");
        
        out.println("{");
        out.println("  \"status\": \"success\",");
        out.println("  \"data\": " + result.toString() + ",");
        out.println("  \"message\": \"새 사용자가 성공적으로 생성되었습니다.\"");
        out.println("}");
        
        out.flush();
    }
    
    @Override
    protected void doPut(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        String userId = request.getParameter("userId");
        String username = request.getParameter("username");
        String email = request.getParameter("email");
        
        Map<String, Object> result = new HashMap<>();
        result.put("method", "PUT");
        result.put("userId", userId);
        result.put("username", username);
        result.put("email", email);
        result.put("timestamp", System.currentTimeMillis());
        result.put("action", "사용자 정보 수정");
        
        out.println("{");
        out.println("  \"status\": \"success\",");
        out.println("  \"data\": " + result.toString() + ",");
        out.println("  \"message\": \"사용자 정보가 성공적으로 수정되었습니다.\"");
        out.println("}");
        
        out.flush();
    }
    
    @Override
    protected void doDelete(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        String userId = request.getParameter("userId");
        
        Map<String, Object> result = new HashMap<>();
        result.put("method", "DELETE");
        result.put("userId", userId);
        result.put("timestamp", System.currentTimeMillis());
        result.put("action", "사용자 삭제");
        
        out.println("{");
        out.println("  \"status\": \"success\",");
        out.println("  \"data\": " + result.toString() + ",");
        out.println("  \"message\": \"사용자가 성공적으로 삭제되었습니다.\"");
        out.println("}");
        
        out.flush();
    }
}
