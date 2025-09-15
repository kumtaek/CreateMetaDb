package com.example.servlet;

import javax.servlet.*;
import javax.servlet.http.*;
import javax.servlet.annotation.*;
import java.io.IOException;

/**
 * 테스트용 Servlet 클래스
 */
@WebServlet(urlPatterns = {"/api/user/*", "/user/list"})
public class UserServlet extends HttpServlet {
    
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        // GET 요청 처리
        response.getWriter().println("GET User Data");
    }
    
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        // POST 요청 처리
        response.getWriter().println("POST User Data");
    }
    
    @Override
    protected void doPut(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        // PUT 요청 처리
        response.getWriter().println("PUT User Data");
    }
    
    @Override
    protected void doDelete(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        // DELETE 요청 처리
        response.getWriter().println("DELETE User Data");
    }
}
