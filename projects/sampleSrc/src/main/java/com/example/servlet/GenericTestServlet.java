package com.example.servlet;

import javax.servlet.GenericServlet;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import java.io.IOException;
import java.io.PrintWriter;

/**
 * GenericServlet을 상속받은 테스트용 Servlet
 * web.xml에서 매핑을 통해 URL 패턴을 정의
 * HttpServlet과 달리 HTTP 프로토콜에 특화되지 않은 범용 Servlet
 */
public class GenericTestServlet extends GenericServlet {
    
    private static final long serialVersionUID = 1L;
    
    @Override
    public void init() throws ServletException {
        super.init();
        
        String testMode = getInitParameter("testMode");
        System.out.println("GenericTestServlet 초기화 완료 - 테스트 모드: " + testMode);
    }
    
    @Override
    public void service(ServletRequest request, ServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("text/html; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        out.println("<!DOCTYPE html>");
        out.println("<html><head>");
        out.println("<title>GenericServlet 테스트</title>");
        out.println("<style>");
        out.println("body { font-family: Arial, sans-serif; margin: 20px; }");
        out.println("table { border-collapse: collapse; width: 100%; margin: 20px 0; }");
        out.println("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }");
        out.println("th { background-color: #f2f2f2; }");
        out.println("</style>");
        out.println("</head><body>");
        
        out.println("<h1>GenericServlet 테스트 페이지</h1>");
        out.println("<p>이 Servlet은 GenericServlet을 상속받아 구현되었습니다.</p>");
        
        // 요청 정보 표시
        out.println("<h2>요청 정보</h2>");
        out.println("<table>");
        out.println("<tr><th>속성</th><th>값</th></tr>");
        out.println("<tr><td>서블릿 이름</td><td>" + getServletName() + "</td></tr>");
        out.println("<tr><td>서블릿 컨텍스트</td><td>" + getServletContext().getServletContextName() + "</td></tr>");
        out.println("<tr><td>서블릿 정보</td><td>" + getServletInfo() + "</td></tr>");
        out.println("<tr><td>프로토콜</td><td>" + request.getProtocol() + "</td></tr>");
        out.println("<tr><td>원격 주소</td><td>" + request.getRemoteAddr() + "</td></tr>");
        out.println("<tr><td>원격 포트</td><td>" + request.getRemotePort() + "</td></tr>");
        out.println("<tr><td>서버 이름</td><td>" + request.getServerName() + "</td></tr>");
        out.println("<tr><td>서버 포트</td><td>" + request.getServerPort() + "</td></tr>");
        out.println("</table>");
        
        // 초기화 파라미터 표시
        out.println("<h2>초기화 파라미터</h2>");
        out.println("<table>");
        out.println("<tr><th>파라미터명</th><th>값</th></tr>");
        
        String testMode = getInitParameter("testMode");
        out.println("<tr><td>testMode</td><td>" + (testMode != null ? testMode : "설정되지 않음") + "</td></tr>");
        
        // 모든 초기화 파라미터 출력
        java.util.Enumeration<String> initParams = getInitParameterNames();
        while (initParams.hasMoreElements()) {
            String paramName = initParams.nextElement();
            String paramValue = getInitParameter(paramName);
            out.println("<tr><td>" + paramName + "</td><td>" + paramValue + "</td></tr>");
        }
        out.println("</table>");
        
        // 컨텍스트 파라미터 표시
        out.println("<h2>컨텍스트 파라미터</h2>");
        out.println("<table>");
        out.println("<tr><th>파라미터명</th><th>값</th></tr>");
        
        String appName = getServletContext().getInitParameter("appName");
        String appVersion = getServletContext().getInitParameter("appVersion");
        String debugMode = getServletContext().getInitParameter("debugMode");
        
        out.println("<tr><td>appName</td><td>" + (appName != null ? appName : "설정되지 않음") + "</td></tr>");
        out.println("<tr><td>appVersion</td><td>" + (appVersion != null ? appVersion : "설정되지 않음") + "</td></tr>");
        out.println("<tr><td>debugMode</td><td>" + (debugMode != null ? debugMode : "설정되지 않음") + "</td></tr>");
        out.println("</table>");
        
        // 요청 파라미터 표시
        out.println("<h2>요청 파라미터</h2>");
        java.util.Map<String, String[]> paramMap = request.getParameterMap();
        
        if (paramMap.isEmpty()) {
            out.println("<p>요청 파라미터가 없습니다.</p>");
        } else {
            out.println("<table>");
            out.println("<tr><th>파라미터명</th><th>값</th></tr>");
            for (java.util.Map.Entry<String, String[]> entry : paramMap.entrySet()) {
                String paramName = entry.getKey();
                String[] paramValues = entry.getValue();
                StringBuilder values = new StringBuilder();
                for (int i = 0; i < paramValues.length; i++) {
                    if (i > 0) values.append(", ");
                    values.append(paramValues[i]);
                }
                out.println("<tr><td>" + paramName + "</td><td>" + values.toString() + "</td></tr>");
            }
            out.println("</table>");
        }
        
        // 테스트 링크
        out.println("<h2>테스트 링크</h2>");
        out.println("<ul>");
        out.println("<li><a href='?test=parameter1'>파라미터 테스트 1</a></li>");
        out.println("<li><a href='?test=parameter2&value=123'>파라미터 테스트 2</a></li>");
        out.println("<li><a href='?action=info&detail=full'>상세 정보 테스트</a></li>");
        out.println("</ul>");
        
        // 현재 시간
        out.println("<p><strong>현재 시간:</strong> " + new java.util.Date().toString() + "</p>");
        
        out.println("</body></html>");
        out.flush();
    }
    
    @Override
    public String getServletInfo() {
        return "GenericServlet 테스트용 Servlet - Servlet 분석기 테스트용";
    }
    
    @Override
    public void destroy() {
        super.destroy();
        System.out.println("GenericTestServlet 종료");
    }
}
