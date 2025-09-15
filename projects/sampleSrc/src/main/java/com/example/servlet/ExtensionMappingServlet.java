package com.example.servlet;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;

/**
 * 확장자 매핑 테스트용 Servlet
 * web.xml에서 *.action, *.process 확장자로 매핑
 * Servlet 분석기에서 확장자 매핑 처리 테스트용
 */
public class ExtensionMappingServlet extends HttpServlet {
    
    private static final long serialVersionUID = 1L;
    
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("text/html; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        out.println("<!DOCTYPE html>");
        out.println("<html><head>");
        out.println("<title>확장자 매핑 Servlet</title>");
        out.println("<style>");
        out.println("body { font-family: Arial, sans-serif; margin: 20px; }");
        out.println(".info { background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 10px 0; }");
        out.println(".success { background: #d4edda; padding: 15px; border-radius: 5px; margin: 10px 0; }");
        out.println("</style>");
        out.println("</head><body>");
        
        out.println("<h1>확장자 매핑 Servlet 테스트</h1>");
        
        // 요청 정보 분석
        String requestURI = request.getRequestURI();
        String servletPath = request.getServletPath();
        String pathInfo = request.getPathInfo();
        String contextPath = request.getContextPath();
        
        out.println("<div class='info'>");
        out.println("<h2>요청 정보</h2>");
        out.println("<p><strong>Request URI:</strong> " + requestURI + "</p>");
        out.println("<p><strong>Servlet Path:</strong> " + servletPath + "</p>");
        out.println("<p><strong>Path Info:</strong> " + (pathInfo != null ? pathInfo : "null") + "</p>");
        out.println("<p><strong>Context Path:</strong> " + contextPath + "</p>");
        out.println("<p><strong>HTTP Method:</strong> " + request.getMethod() + "</p>");
        out.println("</div>");
        
        // 확장자 분석
        String extension = extractExtension(servletPath);
        String action = extractAction(servletPath);
        
        out.println("<div class='success'>");
        out.println("<h2>매핑 분석 결과</h2>");
        out.println("<p><strong>확장자:</strong> " + extension + "</p>");
        out.println("<p><strong>액션:</strong> " + action + "</p>");
        out.println("</div>");
        
        // 액션에 따른 처리
        switch (extension) {
            case "action":
                handleActionRequest(request, response, action);
                break;
            case "process":
                handleProcessRequest(request, response, action);
                break;
            default:
                handleDefaultRequest(request, response);
                break;
        }
        
        out.println("</body></html>");
        out.flush();
    }
    
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        String requestURI = request.getRequestURI();
        String extension = extractExtension(request.getServletPath());
        String action = extractAction(request.getServletPath());
        
        // JSON 응답 생성
        out.println("{");
        out.println("  \"status\": \"success\",");
        out.println("  \"method\": \"POST\",");
        out.println("  \"extension\": \"" + extension + "\",");
        out.println("  \"action\": \"" + action + "\",");
        out.println("  \"requestURI\": \"" + requestURI + "\",");
        out.println("  \"timestamp\": \"" + new java.util.Date().toString() + "\",");
        out.println("  \"message\": \"확장자 매핑 POST 요청 처리 완료\"");
        out.println("}");
        
        out.flush();
    }
    
    private void handleActionRequest(HttpServletRequest request, HttpServletResponse response, String action) 
            throws IOException {
        
        PrintWriter out = response.getWriter();
        
        switch (action) {
            case "login":
                out.println("<h2>로그인 액션</h2>");
                out.println("<p>로그인 처리 페이지입니다.</p>");
                out.println("<form method='post' action='login.action'>");
                out.println("<p>사용자명: <input type='text' name='username'></p>");
                out.println("<p>비밀번호: <input type='password' name='password'></p>");
                out.println("<p><input type='submit' value='로그인'></p>");
                out.println("</form>");
                break;
                
            case "logout":
                out.println("<h2>로그아웃 액션</h2>");
                out.println("<p>로그아웃 처리 페이지입니다.</p>");
                out.println("<a href='logout.action'>로그아웃 실행</a>");
                break;
                
            case "register":
                out.println("<h2>회원가입 액션</h2>");
                out.println("<p>회원가입 처리 페이지입니다.</p>");
                out.println("<form method='post' action='register.action'>");
                out.println("<p>이름: <input type='text' name='name'></p>");
                out.println("<p>이메일: <input type='email' name='email'></p>");
                out.println("<p>전화번호: <input type='tel' name='phone'></p>");
                out.println("<p><input type='submit' value='가입하기'></p>");
                out.println("</form>");
                break;
                
            default:
                out.println("<h2>기본 액션</h2>");
                out.println("<p>액션: " + action + "</p>");
                out.println("<p>이 액션은 확장자 매핑을 통해 처리되었습니다.</p>");
                break;
        }
    }
    
    private void handleProcessRequest(HttpServletRequest request, HttpServletResponse response, String action) 
            throws IOException {
        
        PrintWriter out = response.getWriter();
        
        switch (action) {
            case "payment":
                out.println("<h2>결제 처리</h2>");
                out.println("<p>결제 처리 페이지입니다.</p>");
                out.println("<form method='post' action='payment.process'>");
                out.println("<p>결제 금액: <input type='number' name='amount'></p>");
                out.println("<p>결제 방법: <select name='method'>");
                out.println("<option value='card'>카드</option>");
                out.println("<option value='bank'>계좌이체</option>");
                out.println("<option value='cash'>현금</option>");
                out.println("</select></p>");
                out.println("<p><input type='submit' value='결제하기'></p>");
                out.println("</form>");
                break;
                
            case "order":
                out.println("<h2>주문 처리</h2>");
                out.println("<p>주문 처리 페이지입니다.</p>");
                out.println("<form method='post' action='order.process'>");
                out.println("<p>상품명: <input type='text' name='product'></p>");
                out.println("<p>수량: <input type='number' name='quantity' min='1'></p>");
                out.println("<p><input type='submit' value='주문하기'></p>");
                out.println("</form>");
                break;
                
            case "data":
                out.println("<h2>데이터 처리</h2>");
                out.println("<p>데이터 처리 페이지입니다.</p>");
                out.println("<form method='post' action='data.process'>");
                out.println("<p>데이터 타입: <select name='type'>");
                out.println("<option value='csv'>CSV</option>");
                out.println("<option value='json'>JSON</option>");
                out.println("<option value='xml'>XML</option>");
                out.println("</select></p>");
                out.println("<p><input type='submit' value='처리하기'></p>");
                out.println("</form>");
                break;
                
            default:
                out.println("<h2>기본 처리</h2>");
                out.println("<p>처리 액션: " + action + "</p>");
                out.println("<p>이 처리는 확장자 매핑을 통해 실행되었습니다.</p>");
                break;
        }
    }
    
    private void handleDefaultRequest(HttpServletRequest request, HttpServletResponse response) 
            throws IOException {
        
        PrintWriter out = response.getWriter();
        
        out.println("<h2>기본 요청 처리</h2>");
        out.println("<p>확장자 매핑이 아닌 일반 요청입니다.</p>");
        out.println("<p>사용 가능한 확장자 매핑:</p>");
        out.println("<ul>");
        out.println("<li>*.action - 액션 기반 요청</li>");
        out.println("<li>*.process - 처리 기반 요청</li>");
        out.println("</ul>");
        
        out.println("<h3>테스트 링크</h3>");
        out.println("<ul>");
        out.println("<li><a href='login.action'>로그인 액션</a></li>");
        out.println("<li><a href='logout.action'>로그아웃 액션</a></li>");
        out.println("<li><a href='register.action'>회원가입 액션</a></li>");
        out.println("<li><a href='payment.process'>결제 처리</a></li>");
        out.println("<li><a href='order.process'>주문 처리</a></li>");
        out.println("<li><a href='data.process'>데이터 처리</a></li>");
        out.println("</ul>");
    }
    
    private String extractExtension(String servletPath) {
        if (servletPath == null || !servletPath.contains(".")) {
            return "none";
        }
        
        int lastDotIndex = servletPath.lastIndexOf('.');
        if (lastDotIndex == -1 || lastDotIndex == servletPath.length() - 1) {
            return "none";
        }
        
        return servletPath.substring(lastDotIndex + 1);
    }
    
    private String extractAction(String servletPath) {
        if (servletPath == null || !servletPath.contains(".")) {
            return "default";
        }
        
        int lastDotIndex = servletPath.lastIndexOf('.');
        if (lastDotIndex <= 1) {
            return "default";
        }
        
        String path = servletPath.substring(0, lastDotIndex);
        int lastSlashIndex = path.lastIndexOf('/');
        
        if (lastSlashIndex == -1) {
            return path;
        } else {
            return path.substring(lastSlashIndex + 1);
        }
    }
}
