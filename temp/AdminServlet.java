package com.example.servlet;

import javax.servlet.*;
import javax.servlet.http.*;
import javax.servlet.annotation.*;
import java.io.IOException;

/**
 * service() 메서드를 사용하는 테스트용 Servlet 클래스
 */
@WebServlet("/admin/*")
public class AdminServlet extends HttpServlet {
    
    @Override
    protected void service(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        // 모든 HTTP 메서드를 한 곳에서 처리
        String method = request.getMethod();
        response.getWriter().println("Service method handling: " + method);
    }
}
