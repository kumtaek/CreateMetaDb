package com.example.servlet;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

/**
 * web.xml에서 매핑을 정의하는 레거시 스타일 Servlet
 * @WebServlet 어노테이션을 사용하지 않고 web.xml의 servlet-mapping을 통해 URL 패턴 정의
 * 레거시 시스템에서 많이 사용되는 방식
 */
public class LegacyPaymentServlet extends HttpServlet {
    
    private static final long serialVersionUID = 1L;
    
    // 결제 상태 상수
    private static final String STATUS_PENDING = "PENDING";
    private static final String STATUS_PROCESSING = "PROCESSING";
    private static final String STATUS_SUCCESS = "SUCCESS";
    private static final String STATUS_FAILED = "FAILED";
    private static final String STATUS_CANCELLED = "CANCELLED";
    
    // 결제 방법 상수
    private static final String METHOD_CARD = "CARD";
    private static final String METHOD_BANK = "BANK";
    private static final String METHOD_CASH = "CASH";
    
    @Override
    public void init() throws ServletException {
        super.init();
        // Servlet 초기화 시 로그 출력
        System.out.println("LegacyPaymentServlet 초기화 시작");
        System.out.println("결제 서비스가 준비되었습니다.");
    }
    
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("text/html; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        String action = request.getParameter("action");
        
        out.println("<!DOCTYPE html>");
        out.println("<html><head>");
        out.println("<title>레거시 결제 시스템</title>");
        out.println("<style>");
        out.println("body { font-family: Arial, sans-serif; margin: 20px; }");
        out.println("table { border-collapse: collapse; width: 100%; margin: 20px 0; }");
        out.println("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }");
        out.println("th { background-color: #f2f2f2; }");
        out.println(".success { color: green; }");
        out.println(".error { color: red; }");
        out.println(".warning { color: orange; }");
        out.println("</style>");
        out.println("</head><body>");
        
        out.println("<h1>레거시 결제 시스템</h1>");
        out.println("<p><strong>Servlet 경로:</strong> " + request.getServletPath() + "</p>");
        out.println("<p><strong>요청 URI:</strong> " + request.getRequestURI() + "</p>");
        
        switch (action) {
            case "status":
                showPaymentStatus(request, out);
                break;
            case "history":
                showPaymentHistory(request, out);
                break;
            case "methods":
                showPaymentMethods(request, out);
                break;
            default:
                showMainMenu(request, out);
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
        
        String action = request.getParameter("action");
        Map<String, Object> result = new HashMap<>();
        
        try {
            switch (action) {
                case "process":
                    result = processPayment(request);
                    break;
                case "cancel":
                    result = cancelPayment(request);
                    break;
                case "refund":
                    result = refundPayment(request);
                    break;
                case "verify":
                    result = verifyPayment(request);
                    break;
                default:
                    result.put("success", false);
                    result.put("error", "알 수 없는 액션: " + action);
                    result.put("availableActions", new String[]{"process", "cancel", "refund", "verify"});
            }
            
            result.put("timestamp", new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()));
            result.put("servletPath", request.getServletPath());
            result.put("requestURI", request.getRequestURI());
            
        } catch (Exception e) {
            result.put("success", false);
            result.put("error", "결제 처리 중 오류 발생: " + e.getMessage());
            result.put("timestamp", new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()));
        }
        
        out.println(formatJsonResponse(result));
        out.flush();
    }
    
    @Override
    protected void doPut(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        String paymentId = request.getParameter("paymentId");
        String newStatus = request.getParameter("status");
        
        Map<String, Object> result = new HashMap<>();
        result.put("method", "PUT");
        result.put("action", "결제 상태 수정");
        result.put("paymentId", paymentId);
        result.put("oldStatus", getPaymentStatus(paymentId));
        result.put("newStatus", newStatus);
        result.put("success", true);
        result.put("message", "결제 상태가 성공적으로 수정되었습니다.");
        
        out.println(formatJsonResponse(result));
        out.flush();
    }
    
    @Override
    protected void doDelete(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        String paymentId = request.getParameter("paymentId");
        
        Map<String, Object> result = new HashMap<>();
        result.put("method", "DELETE");
        result.put("action", "결제 기록 삭제");
        result.put("paymentId", paymentId);
        result.put("success", true);
        result.put("message", "결제 기록이 성공적으로 삭제되었습니다.");
        result.put("warning", "이 작업은 되돌릴 수 없습니다.");
        
        out.println(formatJsonResponse(result));
        out.flush();
    }
    
    private void showMainMenu(HttpServletRequest request, PrintWriter out) {
        out.println("<h2>메인 메뉴</h2>");
        out.println("<div style='margin: 20px 0;'>");
        out.println("<h3>조회 기능</h3>");
        out.println("<ul>");
        out.println("<li><a href='?action=status'>결제 상태 조회</a></li>");
        out.println("<li><a href='?action=history'>결제 이력 조회</a></li>");
        out.println("<li><a href='?action=methods'>결제 방법 조회</a></li>");
        out.println("</ul>");
        
        out.println("<h3>API 엔드포인트</h3>");
        out.println("<ul>");
        out.println("<li><strong>POST</strong> ?action=process - 결제 처리</li>");
        out.println("<li><strong>POST</strong> ?action=cancel - 결제 취소</li>");
        out.println("<li><strong>POST</strong> ?action=refund - 환불 처리</li>");
        out.println("<li><strong>POST</strong> ?action=verify - 결제 검증</li>");
        out.println("<li><strong>PUT</strong> ?paymentId=xxx&status=yyy - 결제 상태 수정</li>");
        out.println("<li><strong>DELETE</strong> ?paymentId=xxx - 결제 기록 삭제</li>");
        out.println("</ul>");
        out.println("</div>");
    }
    
    private void showPaymentStatus(HttpServletRequest request, PrintWriter out) {
        String paymentId = request.getParameter("paymentId");
        
        out.println("<h2>결제 상태 조회</h2>");
        
        if (paymentId != null && !paymentId.isEmpty()) {
            String status = getPaymentStatus(paymentId);
            out.println("<table>");
            out.println("<tr><th>결제 ID</th><td>" + paymentId + "</td></tr>");
            out.println("<tr><th>상태</th><td class='" + getStatusClass(status) + "'>" + status + "</td></tr>");
            out.println("<tr><th>조회 시간</th><td>" + new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()) + "</td></tr>");
            out.println("</table>");
        } else {
            out.println("<p>결제 ID를 입력하세요: <input type='text' name='paymentId' placeholder='예: PAY001'></p>");
        }
    }
    
    private void showPaymentHistory(HttpServletRequest request, PrintWriter out) {
        out.println("<h2>결제 이력 조회</h2>");
        out.println("<table>");
        out.println("<tr><th>결제 ID</th><th>금액</th><th>방법</th><th>상태</th><th>날짜</th></tr>");
        
        // 샘플 결제 이력 데이터
        String[][] history = {
            {"PAY001", "50,000원", "카드", "SUCCESS", "2025-09-15 10:30:00"},
            {"PAY002", "120,000원", "계좌이체", "SUCCESS", "2025-09-15 11:15:00"},
            {"PAY003", "30,000원", "카드", "FAILED", "2025-09-15 12:00:00"},
            {"PAY004", "75,000원", "카드", "PENDING", "2025-09-15 13:45:00"},
            {"PAY005", "200,000원", "계좌이체", "SUCCESS", "2025-09-15 14:20:00"}
        };
        
        for (String[] record : history) {
            out.println("<tr>");
            out.println("<td>" + record[0] + "</td>");
            out.println("<td>" + record[1] + "</td>");
            out.println("<td>" + record[2] + "</td>");
            out.println("<td class='" + getStatusClass(record[3]) + "'>" + record[3] + "</td>");
            out.println("<td>" + record[4] + "</td>");
            out.println("</tr>");
        }
        
        out.println("</table>");
    }
    
    private void showPaymentMethods(HttpServletRequest request, PrintWriter out) {
        out.println("<h2>결제 방법 조회</h2>");
        out.println("<table>");
        out.println("<tr><th>결제 방법</th><th>상태</th><th>수수료</th><th>설명</th></tr>");
        
        String[][] methods = {
            {"신용카드", "사용가능", "2.5%", "Visa, MasterCard, Amex 지원"},
            {"계좌이체", "사용가능", "무료", "실시간 계좌이체"},
            {"무통장입금", "사용가능", "무료", "가상계좌 입금"},
            {"휴대폰결제", "점검중", "3.5%", "일시적으로 서비스 중단"},
            {"페이팔", "준비중", "2.9%", "해외 결제 서비스"}
        };
        
        for (String[] method : methods) {
            out.println("<tr>");
            out.println("<td>" + method[0] + "</td>");
            out.println("<td class='" + getMethodStatusClass(method[1]) + "'>" + method[1] + "</td>");
            out.println("<td>" + method[2] + "</td>");
            out.println("<td>" + method[3] + "</td>");
            out.println("</tr>");
        }
        
        out.println("</table>");
    }
    
    private Map<String, Object> processPayment(HttpServletRequest request) {
        Map<String, Object> result = new HashMap<>();
        
        String amount = request.getParameter("amount");
        String method = request.getParameter("method");
        String customerId = request.getParameter("customerId");
        
        result.put("method", "POST");
        result.put("action", "결제 처리");
        result.put("paymentId", generatePaymentId());
        result.put("amount", amount);
        result.put("paymentMethod", method);
        result.put("customerId", customerId);
        result.put("status", STATUS_PROCESSING);
        result.put("success", true);
        result.put("message", "결제가 처리 중입니다.");
        
        return result;
    }
    
    private Map<String, Object> cancelPayment(HttpServletRequest request) {
        Map<String, Object> result = new HashMap<>();
        
        String paymentId = request.getParameter("paymentId");
        String reason = request.getParameter("reason");
        
        result.put("method", "POST");
        result.put("action", "결제 취소");
        result.put("paymentId", paymentId);
        result.put("cancelReason", reason);
        result.put("oldStatus", getPaymentStatus(paymentId));
        result.put("newStatus", STATUS_CANCELLED);
        result.put("success", true);
        result.put("message", "결제가 성공적으로 취소되었습니다.");
        
        return result;
    }
    
    private Map<String, Object> refundPayment(HttpServletRequest request) {
        Map<String, Object> result = new HashMap<>();
        
        String paymentId = request.getParameter("paymentId");
        String refundAmount = request.getParameter("refundAmount");
        String reason = request.getParameter("reason");
        
        result.put("method", "POST");
        result.put("action", "환불 처리");
        result.put("paymentId", paymentId);
        result.put("refundAmount", refundAmount);
        result.put("refundReason", reason);
        result.put("status", "REFUNDED");
        result.put("success", true);
        result.put("message", "환불이 성공적으로 처리되었습니다.");
        
        return result;
    }
    
    private Map<String, Object> verifyPayment(HttpServletRequest request) {
        Map<String, Object> result = new HashMap<>();
        
        String paymentId = request.getParameter("paymentId");
        String verificationCode = request.getParameter("verificationCode");
        
        result.put("method", "POST");
        result.put("action", "결제 검증");
        result.put("paymentId", paymentId);
        result.put("verificationCode", verificationCode);
        result.put("verificationResult", "VALID");
        result.put("success", true);
        result.put("message", "결제가 검증되었습니다.");
        
        return result;
    }
    
    private String getPaymentStatus(String paymentId) {
        // 실제로는 DB에서 조회
        if ("PAY001".equals(paymentId)) return STATUS_SUCCESS;
        if ("PAY002".equals(paymentId)) return STATUS_SUCCESS;
        if ("PAY003".equals(paymentId)) return STATUS_FAILED;
        if ("PAY004".equals(paymentId)) return STATUS_PENDING;
        if ("PAY005".equals(paymentId)) return STATUS_SUCCESS;
        return "NOT_FOUND";
    }
    
    private String generatePaymentId() {
        return "PAY" + String.format("%03d", (int)(Math.random() * 1000));
    }
    
    private String getStatusClass(String status) {
        switch (status) {
            case STATUS_SUCCESS: return "success";
            case STATUS_FAILED: return "error";
            case STATUS_PENDING:
            case STATUS_PROCESSING: return "warning";
            default: return "";
        }
    }
    
    private String getMethodStatusClass(String status) {
        switch (status) {
            case "사용가능": return "success";
            case "점검중": return "warning";
            case "준비중": return "error";
            default: return "";
        }
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
            } else if (value instanceof String[]) {
                json.append("[");
                String[] array = (String[]) value;
                for (int i = 0; i < array.length; i++) {
                    if (i > 0) json.append(", ");
                    json.append("\"").append(array[i]).append("\"");
                }
                json.append("]");
            } else {
                json.append("\"").append(value.toString()).append("\"");
            }
            first = false;
        }
        
        json.append("\n}");
        return json.toString();
    }
}
