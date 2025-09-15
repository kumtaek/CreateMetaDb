package com.example.servlet;

import javax.servlet.*;
import javax.servlet.http.*;
import java.io.IOException;

/**
 * @WebServlet 어노테이션이 없는 테스트용 Servlet 클래스
 * web.xml에서 매핑되어야 함
 */
public class LegacyServlet extends HttpServlet {
    
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        // GET 요청 처리
        response.getWriter().println("Legacy GET Data");
    }
    
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        // POST 요청 처리
        response.getWriter().println("Legacy POST Data");
    }
}
