package com.example.servlet;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebInitParam;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;
import java.text.SimpleDateFormat;
import java.util.*;

/**
 * 혼합 방식 Servlet - @WebServlet 어노테이션 + doXXX 메서드 + service() 메서드 오버라이드
 * 다양한 Servlet 패턴을 모두 포함한 고급 리포트 생성 Servlet
 * 
 * 특징:
 * 1. @WebServlet 어노테이션으로 기본 URL 패턴 정의
 * 2. @WebInitParam으로 초기화 파라미터 설정
 * 3. doGet, doPost 메서드로 일반적인 HTTP 요청 처리
 * 4. service() 메서드 오버라이드로 특별한 요청 처리
 * 5. 복잡한 비즈니스 로직과 다양한 응답 형식 지원
 */
@WebServlet(
    urlPatterns = {"/reports/*", "/api/v1/reports", "/admin/report-management"},
    initParams = {
        @WebInitParam(name = "reportCacheSize", value = "1000"),
        @WebInitParam(name = "defaultFormat", value = "json"),
        @WebInitParam(name = "maxRecords", value = "10000"),
        @WebInitParam(name = "enableCache", value = "true")
    },
    loadOnStartup = 1
)
public class AdvancedReportServlet extends HttpServlet {
    
    private static final long serialVersionUID = 1L;
    
    // 초기화 파라미터
    private int reportCacheSize;
    private String defaultFormat;
    private int maxRecords;
    private boolean enableCache;
    
    // 리포트 캐시
    private Map<String, Object> reportCache;
    
    @Override
    public void init() throws ServletException {
        super.init();
        
        // 초기화 파라미터 로드
        reportCacheSize = Integer.parseInt(getInitParameter("reportCacheSize"));
        defaultFormat = getInitParameter("defaultFormat");
        maxRecords = Integer.parseInt(getInitParameter("maxRecords"));
        enableCache = Boolean.parseBoolean(getInitParameter("enableCache"));
        
        // 리포트 캐시 초기화
        if (enableCache) {
            reportCache = new HashMap<>();
            System.out.println("AdvancedReportServlet: 리포트 캐시 활성화 (크기: " + reportCacheSize + ")");
        }
        
        System.out.println("AdvancedReportServlet 초기화 완료");
        System.out.println("기본 형식: " + defaultFormat + ", 최대 레코드: " + maxRecords);
    }
    
    @Override
    protected void service(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        // 특별한 요청 헤더나 조건에 따른 커스텀 처리
        String customHeader = request.getHeader("X-Custom-Report-Format");
        String userAgent = request.getHeader("User-Agent");
        
        // 모바일 디바이스 감지
        if (userAgent != null && userAgent.toLowerCase().contains("mobile")) {
            // 모바일용 간소화된 응답
            handleMobileRequest(request, response);
            return;
        }
        
        // 커스텀 형식 요청 처리
        if ("xml".equals(customHeader)) {
            handleCustomFormatRequest(request, response, "xml");
            return;
        } else if ("csv".equals(customHeader)) {
            handleCustomFormatRequest(request, response, "csv");
            return;
        }
        
        // 일반적인 service() 호출
        super.service(request, response);
    }
    
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String action = request.getParameter("action");
        String format = request.getParameter("format");
        if (format == null) format = defaultFormat;
        
        // 캐시 확인
        String cacheKey = generateCacheKey(request);
        if (enableCache && reportCache.containsKey(cacheKey)) {
            serveCachedResponse(response, cacheKey);
            return;
        }
        
        Map<String, Object> reportData = new HashMap<>();
        
        switch (action) {
            case "summary":
                reportData = generateSummaryReport(request);
                break;
            case "detailed":
                reportData = generateDetailedReport(request);
                break;
            case "analytics":
                reportData = generateAnalyticsReport(request);
                break;
            case "export":
                reportData = generateExportReport(request);
                break;
            default:
                reportData = generateMainReport(request);
                break;
        }
        
        // 캐시 저장
        if (enableCache && reportData != null) {
            reportCache.put(cacheKey, reportData);
        }
        
        // 응답 형식에 따른 처리
        switch (format.toLowerCase()) {
            case "json":
                sendJsonResponse(response, reportData);
                break;
            case "xml":
                sendXmlResponse(response, reportData);
                break;
            case "csv":
                sendCsvResponse(response, reportData);
                break;
            case "html":
                sendHtmlResponse(response, reportData);
                break;
            default:
                sendJsonResponse(response, reportData);
                break;
        }
    }
    
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String action = request.getParameter("action");
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        Map<String, Object> result = new HashMap<>();
        
        switch (action) {
            case "generate":
                result = generateCustomReport(request);
                break;
            case "schedule":
                result = scheduleReport(request);
                break;
            case "export":
                result = exportReport(request);
                break;
            case "validate":
                result = validateReportRequest(request);
                break;
            default:
                result.put("success", false);
                result.put("error", "알 수 없는 액션: " + action);
        }
        
        out.println(formatJsonResponse(result));
        out.flush();
    }
    
    @Override
    protected void doPut(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String reportId = request.getParameter("reportId");
        String config = request.getParameter("config");
        
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        Map<String, Object> result = new HashMap<>();
        result.put("method", "PUT");
        result.put("action", "리포트 설정 업데이트");
        result.put("reportId", reportId);
        result.put("config", config);
        result.put("success", true);
        result.put("message", "리포트 설정이 성공적으로 업데이트되었습니다.");
        
        // 캐시 무효화
        if (enableCache) {
            clearRelatedCache(reportId);
        }
        
        out.println(formatJsonResponse(result));
        out.flush();
    }
    
    @Override
    protected void doDelete(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String reportId = request.getParameter("reportId");
        
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        Map<String, Object> result = new HashMap<>();
        result.put("method", "DELETE");
        result.put("action", "리포트 삭제");
        result.put("reportId", reportId);
        result.put("success", true);
        result.put("message", "리포트가 성공적으로 삭제되었습니다.");
        
        // 캐시 무효화
        if (enableCache) {
            clearRelatedCache(reportId);
        }
        
        out.println(formatJsonResponse(result));
        out.flush();
    }
    
    private void handleMobileRequest(HttpServletRequest request, HttpServletResponse response) 
            throws IOException {
        
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        Map<String, Object> mobileData = new HashMap<>();
        mobileData.put("platform", "mobile");
        mobileData.put("optimized", true);
        mobileData.put("summary", generateMobileSummary(request));
        mobileData.put("timestamp", new Date().toString());
        
        out.println(formatJsonResponse(mobileData));
        out.flush();
    }
    
    private void handleCustomFormatRequest(HttpServletRequest request, HttpServletResponse response, String format) 
            throws IOException {
        
        switch (format) {
            case "xml":
                response.setContentType("application/xml; charset=UTF-8");
                break;
            case "csv":
                response.setContentType("text/csv; charset=UTF-8");
                break;
        }
        
        PrintWriter out = response.getWriter();
        Map<String, Object> data = generateCustomFormatData(request);
        
        switch (format) {
            case "xml":
                out.println(formatXmlResponse(data));
                break;
            case "csv":
                out.println(formatCsvResponse(data));
                break;
        }
        
        out.flush();
    }
    
    private Map<String, Object> generateSummaryReport(HttpServletRequest request) {
        Map<String, Object> report = new HashMap<>();
        report.put("type", "summary");
        report.put("title", "요약 리포트");
        report.put("generatedAt", new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()));
        report.put("totalRecords", 1500);
        report.put("activeUsers", 890);
        report.put("totalRevenue", 2500000);
        report.put("growthRate", "+12.5%");
        return report;
    }
    
    private Map<String, Object> generateDetailedReport(HttpServletRequest request) {
        Map<String, Object> report = new HashMap<>();
        report.put("type", "detailed");
        report.put("title", "상세 리포트");
        report.put("generatedAt", new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()));
        report.put("sections", Arrays.asList("사용자 분석", "매출 분석", "성능 분석", "오류 분석"));
        report.put("totalPages", 25);
        report.put("dataPoints", 5000);
        return report;
    }
    
    private Map<String, Object> generateAnalyticsReport(HttpServletRequest request) {
        Map<String, Object> report = new HashMap<>();
        report.put("type", "analytics");
        report.put("title", "분석 리포트");
        report.put("generatedAt", new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()));
        report.put("metrics", createAnalyticsMetrics());
        report.put("charts", Arrays.asList("라인 차트", "파이 차트", "바 차트"));
        return report;
    }
    
    private Map<String, Object> generateExportReport(HttpServletRequest request) {
        Map<String, Object> report = new HashMap<>();
        report.put("type", "export");
        report.put("title", "내보내기 리포트");
        report.put("generatedAt", new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()));
        report.put("exportFormats", Arrays.asList("PDF", "Excel", "CSV", "JSON"));
        report.put("fileSize", "2.5MB");
        report.put("downloadUrl", "/downloads/report_" + System.currentTimeMillis() + ".pdf");
        return report;
    }
    
    private Map<String, Object> generateMainReport(HttpServletRequest request) {
        Map<String, Object> report = new HashMap<>();
        report.put("type", "main");
        report.put("title", "메인 대시보드");
        report.put("generatedAt", new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()));
        report.put("availableReports", Arrays.asList("summary", "detailed", "analytics", "export"));
        report.put("userRole", "admin");
        return report;
    }
    
    private Map<String, Object> generateCustomReport(HttpServletRequest request) {
        Map<String, Object> result = new HashMap<>();
        result.put("action", "generate");
        result.put("reportId", generateReportId());
        result.put("status", "generating");
        result.put("estimatedTime", "2-3분");
        result.put("success", true);
        return result;
    }
    
    private Map<String, Object> scheduleReport(HttpServletRequest request) {
        Map<String, Object> result = new HashMap<>();
        result.put("action", "schedule");
        result.put("scheduleId", generateScheduleId());
        result.put("nextRun", "2025-09-16 09:00:00");
        result.put("frequency", "daily");
        result.put("success", true);
        return result;
    }
    
    private Map<String, Object> exportReport(HttpServletRequest request) {
        Map<String, Object> result = new HashMap<>();
        result.put("action", "export");
        result.put("exportId", generateExportId());
        result.put("format", request.getParameter("format"));
        result.put("downloadUrl", "/exports/" + generateExportId() + ".zip");
        result.put("success", true);
        return result;
    }
    
    private Map<String, Object> validateReportRequest(HttpServletRequest request) {
        Map<String, Object> result = new HashMap<>();
        result.put("action", "validate");
        result.put("valid", true);
        result.put("warnings", Arrays.asList("대용량 데이터로 인해 처리 시간이 길어질 수 있습니다."));
        result.put("success", true);
        return result;
    }
    
    private Map<String, Object> generateMobileSummary(HttpServletRequest request) {
        Map<String, Object> summary = new HashMap<>();
        summary.put("totalUsers", 890);
        summary.put("activeToday", 245);
        summary.put("revenue", 125000);
        return summary;
    }
    
    private Map<String, Object> generateCustomFormatData(HttpServletRequest request) {
        Map<String, Object> data = new HashMap<>();
        data.put("customFormat", true);
        data.put("timestamp", new Date().toString());
        data.put("requestInfo", request.getParameterMap());
        return data;
    }
    
    private Map<String, Object> createAnalyticsMetrics() {
        Map<String, Object> metrics = new HashMap<>();
        metrics.put("pageViews", 15000);
        metrics.put("uniqueVisitors", 3500);
        metrics.put("conversionRate", "3.2%");
        metrics.put("bounceRate", "45%");
        metrics.put("avgSessionDuration", "4분 30초");
        return metrics;
    }
    
    private String generateCacheKey(HttpServletRequest request) {
        StringBuilder key = new StringBuilder();
        key.append(request.getParameter("action"));
        key.append("_").append(request.getParameter("format"));
        key.append("_").append(request.getParameterMap().hashCode());
        return key.toString();
    }
    
    private void serveCachedResponse(HttpServletResponse response, String cacheKey) throws IOException {
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        out.println(formatJsonResponse((Map<String, Object>) reportCache.get(cacheKey)));
        out.flush();
    }
    
    private void clearRelatedCache(String reportId) {
        if (reportCache != null) {
            reportCache.entrySet().removeIf(entry -> 
                entry.getKey().contains(reportId));
        }
    }
    
    private String generateReportId() {
        return "RPT" + String.format("%06d", (int)(Math.random() * 1000000));
    }
    
    private String generateScheduleId() {
        return "SCH" + String.format("%06d", (int)(Math.random() * 1000000));
    }
    
    private String generateExportId() {
        return "EXP" + String.format("%06d", (int)(Math.random() * 1000000));
    }
    
    private void sendJsonResponse(HttpServletResponse response, Map<String, Object> data) throws IOException {
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        out.println(formatJsonResponse(data));
        out.flush();
    }
    
    private void sendXmlResponse(HttpServletResponse response, Map<String, Object> data) throws IOException {
        response.setContentType("application/xml; charset=UTF-8");
        PrintWriter out = response.getWriter();
        out.println(formatXmlResponse(data));
        out.flush();
    }
    
    private void sendCsvResponse(HttpServletResponse response, Map<String, Object> data) throws IOException {
        response.setContentType("text/csv; charset=UTF-8");
        PrintWriter out = response.getWriter();
        out.println(formatCsvResponse(data));
        out.flush();
    }
    
    private void sendHtmlResponse(HttpServletResponse response, Map<String, Object> data) throws IOException {
        response.setContentType("text/html; charset=UTF-8");
        PrintWriter out = response.getWriter();
        out.println(formatHtmlResponse(data));
        out.flush();
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
            } else if (value instanceof Map) {
                json.append(formatMap((Map<?, ?>) value));
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
            sb.append("\"").append(list.get(i)).append("\"");
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
    
    private String formatXmlResponse(Map<String, Object> data) {
        StringBuilder xml = new StringBuilder();
        xml.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
        xml.append("<report>\n");
        
        for (Map.Entry<String, Object> entry : data.entrySet()) {
            xml.append("  <").append(entry.getKey()).append(">");
            xml.append(entry.getValue());
            xml.append("</").append(entry.getKey()).append(">\n");
        }
        
        xml.append("</report>");
        return xml.toString();
    }
    
    private String formatCsvResponse(Map<String, Object> data) {
        StringBuilder csv = new StringBuilder();
        
        // 헤더
        csv.append("Key,Value\n");
        
        // 데이터
        for (Map.Entry<String, Object> entry : data.entrySet()) {
            csv.append(entry.getKey()).append(",").append(entry.getValue()).append("\n");
        }
        
        return csv.toString();
    }
    
    private String formatHtmlResponse(Map<String, Object> data) {
        StringBuilder html = new StringBuilder();
        html.append("<!DOCTYPE html><html><head><title>리포트</title></head><body>");
        html.append("<h1>리포트 결과</h1>");
        html.append("<table border='1'><tr><th>항목</th><th>값</th></tr>");
        
        for (Map.Entry<String, Object> entry : data.entrySet()) {
            html.append("<tr><td>").append(entry.getKey()).append("</td><td>").append(entry.getValue()).append("</td></tr>");
        }
        
        html.append("</table></body></html>");
        return html.toString();
    }
}
