package com.example.performance;

import org.springframework.stereotype.Repository;
import org.springframework.beans.factory.annotation.Autowired;
import javax.sql.DataSource;
import java.util.*;
import java.sql.*;
import java.math.BigDecimal;

/**
 * 복합 SQL 패턴 DAO - 연관관계 도출 테스트용
 * 목적: String.format + StringBuilder 혼합, 조건부 JOIN, 동적 테이블명 패턴
 * 연관관계 중심: 복잡한 테이블 관계를 다양한 SQL 패턴으로 표현
 */
@Repository
public class HybridSqlPatternDao {

    @Autowired
    private DataSource dataSource;
    
    @Autowired
    private SqlMetricsCollector metricsCollector;

    /**
     * 패턴 1: StringBuilder + String.format 혼합 (사용자-주문-상품 관계)
     * 연관 테이블: users_{env}, orders_{env}, order_items_{env}, products_{env}, categories_{env}
     */
    public List<Map<String, Object>> findUserOrdersWithHybridPattern(String environment, 
                                                                    Map<String, Object> filters,
                                                                    List<String> includeOptions) {
        // StringBuilder로 기본 구조 구성
        StringBuilder queryBuilder = new StringBuilder();
        queryBuilder.append("SELECT u.user_id, u.username, u.email, u.status, ");
        queryBuilder.append("       o.order_id, o.order_date, o.total_amount, o.status as order_status ");
        
        // String.format으로 환경별 테이블명 처리
        String baseFromClause = String.format(
            "FROM users_%s u " +
            "LEFT JOIN orders_%s o ON u.user_id = o.user_id ",
            environment, environment
        );
        
        queryBuilder.append(baseFromClause);
        
        // 조건부 JOIN 추가 (StringBuilder + String.format 혼합)
        if (includeOptions.contains("PRODUCT_INFO")) {
            String productJoin = String.format(
                "LEFT JOIN order_items_%s oi ON o.order_id = oi.order_id " +
                "LEFT JOIN products_%s p ON oi.product_id = p.product_id ",
                environment, environment
            );
            queryBuilder.append(productJoin);
            
            // SELECT 절에 상품 정보 추가
            queryBuilder.insert(queryBuilder.indexOf("FROM") - 1, 
                              ", p.product_name, p.price, p.category_id ");
        }
        
        if (includeOptions.contains("CATEGORY_INFO")) {
            String categoryJoin = String.format(
                "LEFT JOIN categories_%s c ON p.category_id = c.category_id ",
                environment
            );
            queryBuilder.append(categoryJoin);
            queryBuilder.insert(queryBuilder.indexOf("FROM") - 1, ", c.category_name ");
        }
        
        // 동적 WHERE 조건 구성
        StringBuilder whereClause = new StringBuilder("WHERE 1=1 ");
        
        if (filters.containsKey("userStatus")) {
            whereClause.append("AND u.status = '").append(filters.get("userStatus")).append("' ");
        }
        
        if (filters.containsKey("dateFrom")) {
            whereClause.append("AND o.order_date >= '").append(filters.get("dateFrom")).append("' ");
        }
        
        if (filters.containsKey("minAmount")) {
            whereClause.append("AND o.total_amount >= ").append(filters.get("minAmount")).append(" ");
        }
        
        // 최종 쿼리 조합
        String finalQuery = queryBuilder.toString() + whereClause.toString() + 
                           "ORDER BY o.order_date DESC, o.total_amount DESC";
        
        return executeHybridQuery(finalQuery);
    }

    /**
     * 패턴 2: 조건부 복합 JOIN (고객-사용자-주문-결제 관계)
     * 연관 테이블: customers_{env}, users_{env}, orders_{env}, payments_{env}, shipments_{env}
     */
    public List<Map<String, Object>> analyzeCustomerOrderPaymentFlow(String environment,
                                                                    String analysisType,
                                                                    Map<String, Object> criteria) {
        // 기본 SELECT 절
        StringBuilder selectBuilder = new StringBuilder();
        selectBuilder.append("SELECT c.customer_id, c.company_name, c.industry, c.credit_rating, ");
        selectBuilder.append("       u.user_id, u.username, u.user_type, ");
        selectBuilder.append("       COUNT(DISTINCT o.order_id) as total_orders, ");
        selectBuilder.append("       SUM(o.total_amount) as total_spent ");
        
        // 환경별 기본 FROM 절
        String baseFrom = String.format(
            "FROM customers_%s c " +
            "INNER JOIN users_%s u ON c.customer_id = u.customer_id " +
            "LEFT JOIN orders_%s o ON u.user_id = o.user_id ",
            environment, environment, environment
        );
        
        StringBuilder joinBuilder = new StringBuilder(baseFrom);
        
        // 분석 타입에 따른 조건부 JOIN
        switch (analysisType) {
            case "PAYMENT_ANALYSIS":
                // 결제 정보 포함
                String paymentJoin = String.format(
                    "LEFT JOIN payments_%s p ON o.order_id = p.order_id ",
                    environment
                );
                joinBuilder.append(paymentJoin);
                selectBuilder.append(", COUNT(DISTINCT p.payment_id) as payment_count, ");
                selectBuilder.append("SUM(p.amount) as total_payments, ");
                selectBuilder.append("AVG(p.amount) as avg_payment_amount ");
                break;
                
            case "SHIPPING_ANALYSIS":
                // 배송 정보 포함
                String shippingJoin = String.format(
                    "LEFT JOIN shipments_%s s ON o.order_id = s.order_id ",
                    environment
                );
                joinBuilder.append(shippingJoin);
                selectBuilder.append(", COUNT(DISTINCT s.shipment_id) as shipment_count, ");
                selectBuilder.append("AVG(DATEDIFF(s.delivered_date, s.ship_date)) as avg_delivery_days ");
                break;
                
            case "COMPREHENSIVE":
                // 결제 + 배송 모두 포함
                String comprehensiveJoin = String.format(
                    "LEFT JOIN payments_%s p ON o.order_id = p.order_id " +
                    "LEFT JOIN shipments_%s s ON o.order_id = s.order_id ",
                    environment, environment
                );
                joinBuilder.append(comprehensiveJoin);
                selectBuilder.append(", COUNT(DISTINCT p.payment_id) as payment_count, ");
                selectBuilder.append("COUNT(DISTINCT s.shipment_id) as shipment_count, ");
                selectBuilder.append("SUM(p.amount) as total_payments ");
                break;
        }
        
        // WHERE 조건 구성
        StringBuilder whereBuilder = new StringBuilder("WHERE c.status = 'ACTIVE' ");
        
        if (criteria.containsKey("industry")) {
            whereBuilder.append("AND c.industry = '").append(criteria.get("industry")).append("' ");
        }
        
        if (criteria.containsKey("creditRating")) {
            whereBuilder.append("AND c.credit_rating >= '").append(criteria.get("creditRating")).append("' ");
        }
        
        if (criteria.containsKey("orderDateFrom")) {
            whereBuilder.append("AND o.order_date >= '").append(criteria.get("orderDateFrom")).append("' ");
        }
        
        // GROUP BY 절
        String groupBy = "GROUP BY c.customer_id, c.company_name, c.industry, c.credit_rating, " +
                        "u.user_id, u.username, u.user_type ";
        
        // 최종 쿼리 조합
        String finalQuery = selectBuilder.toString() + " " + joinBuilder.toString() + " " + 
                           whereBuilder.toString() + " " + groupBy + 
                           "HAVING total_orders > 0 ORDER BY total_spent DESC";
        
        return executeComplexAnalysisQuery(finalQuery);
    }

    /**
     * 패턴 3: 동적 테이블명 + 환경별 분기 (재고-판매 관계)
     * 연관 테이블: products_{env}, inventory_{env}, order_items_{env}, suppliers_{env}
     */
    public Map<String, Object> calculateInventoryMetrics(List<String> environments,
                                                        String reportType,
                                                        Date calculationDate) {
        Map<String, Object> inventoryMetrics = new HashMap<>();
        
        for (String env : environments) {
            // 환경별 재고 분석 쿼리
            StringBuilder inventoryQuery = new StringBuilder();
            
            // String.format으로 환경별 테이블명 구성
            String baseQuery = String.format(
                "SELECT p.product_id, p.product_name, p.category_id, " +
                "       i.current_stock, i.reserved_stock, i.available_stock, " +
                "       s.supplier_id, s.supplier_name, s.lead_time_days ",
                env
            );
            
            inventoryQuery.append(baseQuery);
            
            // FROM 절 구성
            String fromClause = String.format(
                "FROM products_%s p " +
                "LEFT JOIN inventory_%s i ON p.product_id = i.product_id " +
                "LEFT JOIN suppliers_%s s ON p.supplier_id = s.supplier_id ",
                env, env, env
            );
            
            inventoryQuery.append(fromClause);
            
            // 리포트 타입에 따른 추가 JOIN
            if ("SALES_IMPACT".equals(reportType)) {
                // 판매 영향 분석을 위한 주문 아이템 JOIN
                String salesJoin = String.format(
                    "LEFT JOIN order_items_%s oi ON p.product_id = oi.product_id " +
                    "LEFT JOIN orders_%s o ON oi.order_id = o.order_id ",
                    env, env
                );
                inventoryQuery.append(salesJoin);
                
                // SELECT 절에 판매 데이터 추가
                inventoryQuery.insert(inventoryQuery.indexOf("FROM") - 1,
                                    ", COUNT(oi.item_id) as sales_count, " +
                                    "SUM(oi.quantity) as total_sold, " +
                                    "SUM(oi.quantity * oi.unit_price) as sales_revenue ");
                
                // GROUP BY 추가
                inventoryQuery.append("WHERE o.order_date >= DATE_SUB(?, INTERVAL 30 DAY) ");
                inventoryQuery.append("GROUP BY p.product_id, p.product_name, p.category_id, ");
                inventoryQuery.append("         i.current_stock, i.reserved_stock, i.available_stock, ");
                inventoryQuery.append("         s.supplier_id, s.supplier_name, s.lead_time_days ");
            }
            
            // 재고 부족 경고 조건
            inventoryQuery.append("HAVING i.available_stock < 10 OR ");
            inventoryQuery.append("       (i.available_stock / NULLIF(total_sold, 0)) < s.lead_time_days ");
            inventoryQuery.append("ORDER BY i.available_stock ASC, sales_revenue DESC");
            
            List<Map<String, Object>> envResults = executeInventoryQuery(inventoryQuery.toString(), calculationDate);
            inventoryMetrics.put(env + "_inventory", envResults);
        }
        
        return inventoryMetrics;
    }

    /**
     * 패턴 4: 복합 집계 + 동적 피벗 (부서-사용자-성과 관계)
     * 연관 테이블: departments_{env}, users_{env}, user_performance_{env}, projects_{env}
     */
    public List<Map<String, Object>> generateDepartmentPerformanceMatrix(String environment,
                                                                        List<String> performanceMetrics,
                                                                        String timeframe) {
        // 동적 SELECT 절 구성
        StringBuilder selectBuilder = new StringBuilder();
        selectBuilder.append("SELECT d.dept_id, d.dept_name, d.manager_id, ");
        selectBuilder.append("       COUNT(DISTINCT u.user_id) as employee_count ");
        
        // 성과 지표에 따른 동적 컬럼 추가
        for (String metric : performanceMetrics) {
            switch (metric) {
                case "PROJECT_COUNT":
                    selectBuilder.append(", COUNT(DISTINCT pr.project_id) as project_count ");
                    break;
                case "COMPLETION_RATE":
                    selectBuilder.append(", AVG(up.completion_rate) as avg_completion_rate ");
                    break;
                case "QUALITY_SCORE":
                    selectBuilder.append(", AVG(up.quality_score) as avg_quality_score ");
                    break;
                case "EFFICIENCY_RATING":
                    selectBuilder.append(", AVG(up.efficiency_rating) as avg_efficiency_rating ");
                    break;
            }
        }
        
        // FROM 절 및 기본 JOIN
        String baseJoins = String.format(
            "FROM departments_%s d " +
            "LEFT JOIN users_%s u ON d.dept_id = u.dept_id " +
            "LEFT JOIN user_performance_%s up ON u.user_id = up.user_id ",
            environment, environment, environment
        );
        
        StringBuilder joinBuilder = new StringBuilder(baseJoins);
        
        // 프로젝트 정보가 필요한 경우 추가 JOIN
        if (performanceMetrics.contains("PROJECT_COUNT")) {
            String projectJoin = String.format(
                "LEFT JOIN project_assignments_%s pa ON u.user_id = pa.user_id " +
                "LEFT JOIN projects_%s pr ON pa.project_id = pr.project_id ",
                environment, environment
            );
            joinBuilder.append(projectJoin);
        }
        
        // 시간 프레임에 따른 WHERE 조건
        StringBuilder whereBuilder = new StringBuilder("WHERE d.status = 'ACTIVE' ");
        
        switch (timeframe) {
            case "LAST_MONTH":
                whereBuilder.append("AND up.performance_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH) ");
                break;
            case "LAST_QUARTER":
                whereBuilder.append("AND up.performance_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH) ");
                break;
            case "LAST_YEAR":
                whereBuilder.append("AND up.performance_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) ");
                break;
        }
        
        // GROUP BY 절
        String groupBy = "GROUP BY d.dept_id, d.dept_name, d.manager_id ";
        
        // HAVING 절 (최소 직원 수 조건)
        String having = "HAVING employee_count > 0 ";
        
        // ORDER BY 절 (성과 순으로 정렬)
        String orderBy = "ORDER BY ";
        if (performanceMetrics.contains("COMPLETION_RATE")) {
            orderBy += "avg_completion_rate DESC, ";
        }
        if (performanceMetrics.contains("QUALITY_SCORE")) {
            orderBy += "avg_quality_score DESC, ";
        }
        orderBy += "employee_count DESC";
        
        // 최종 쿼리 조합
        String finalQuery = selectBuilder.toString() + " " + joinBuilder.toString() + " " + 
                           whereBuilder.toString() + " " + groupBy + " " + having + " " + orderBy;
        
        return executePerformanceQuery(finalQuery);
    }

    /**
     * 패턴 5: 재귀적 관계 + 계층 구조 (조직도-권한 관계)
     * 연관 테이블: departments_{env}, users_{env}, roles_{env}, permissions_{env}
     */
    public List<Map<String, Object>> buildOrganizationHierarchy(String environment,
                                                               int maxDepth,
                                                               String rootDepartmentId) {
        // CTE를 사용한 재귀 쿼리 (MySQL 8.0 이상)
        StringBuilder cteQuery = new StringBuilder();
        cteQuery.append("WITH RECURSIVE dept_hierarchy AS ( ");
        
        // 기본 케이스 (루트 부서)
        String baseCase = String.format(
            "SELECT d.dept_id, d.dept_name, d.parent_dept_id, d.manager_id, " +
            "       u.user_id, u.username, u.title, " +
            "       0 as depth_level, " +
            "       CAST(d.dept_id AS CHAR(1000)) as hierarchy_path " +
            "FROM departments_%s d " +
            "LEFT JOIN users_%s u ON d.manager_id = u.user_id " +
            "WHERE d.dept_id = '%s' ",
            environment, environment, rootDepartmentId
        );
        
        cteQuery.append(baseCase);
        cteQuery.append("UNION ALL ");
        
        // 재귀 케이스 (하위 부서들)
        String recursiveCase = String.format(
            "SELECT d.dept_id, d.dept_name, d.parent_dept_id, d.manager_id, " +
            "       u.user_id, u.username, u.title, " +
            "       dh.depth_level + 1, " +
            "       CONCAT(dh.hierarchy_path, '->', d.dept_id) " +
            "FROM departments_%s d " +
            "LEFT JOIN users_%s u ON d.manager_id = u.user_id " +
            "INNER JOIN dept_hierarchy dh ON d.parent_dept_id = dh.dept_id " +
            "WHERE dh.depth_level < %d ",
            environment, environment, maxDepth
        );
        
        cteQuery.append(recursiveCase);
        cteQuery.append(") ");
        
        // 메인 쿼리 (권한 정보 포함)
        String mainQuery = String.format(
            "SELECT dh.*, " +
            "       COUNT(DISTINCT emp.user_id) as employee_count, " +
            "       GROUP_CONCAT(DISTINCT r.role_name) as manager_roles, " +
            "       COUNT(DISTINCT p.permission_id) as permission_count " +
            "FROM dept_hierarchy dh " +
            "LEFT JOIN users_%s emp ON dh.dept_id = emp.dept_id " +
            "LEFT JOIN user_roles_%s ur ON dh.user_id = ur.user_id " +
            "LEFT JOIN roles_%s r ON ur.role_id = r.role_id " +
            "LEFT JOIN role_permissions_%s rp ON r.role_id = rp.role_id " +
            "LEFT JOIN permissions_%s p ON rp.permission_id = p.permission_id " +
            "GROUP BY dh.dept_id, dh.dept_name, dh.parent_dept_id, dh.manager_id, " +
            "         dh.user_id, dh.username, dh.title, dh.depth_level, dh.hierarchy_path " +
            "ORDER BY dh.depth_level, dh.dept_name",
            environment, environment, environment, environment, environment
        );
        
        String finalQuery = cteQuery.toString() + mainQuery;
        
        return executeHierarchyQuery(finalQuery);
    }

    /**
     * 패턴 6: 시계열 분석 + 윈도우 함수 (매출-트렌드 관계)
     * 연관 테이블: orders_{env}, order_items_{env}, products_{env}, time_periods
     */
    public List<Map<String, Object>> analyzeSalesTrends(String environment,
                                                       String periodType,
                                                       int periodCount) {
        StringBuilder trendsQuery = new StringBuilder();
        
        // 시간 단위에 따른 동적 GROUP BY
        String timeGrouping;
        switch (periodType) {
            case "DAILY":
                timeGrouping = "DATE(o.order_date)";
                break;
            case "WEEKLY":
                timeGrouping = "YEARWEEK(o.order_date)";
                break;
            case "MONTHLY":
                timeGrouping = "DATE_FORMAT(o.order_date, '%Y-%m')";
                break;
            case "QUARTERLY":
                timeGrouping = "CONCAT(YEAR(o.order_date), '-Q', QUARTER(o.order_date))";
                break;
            default:
                timeGrouping = "DATE(o.order_date)";
        }
        
        // 윈도우 함수를 사용한 트렌드 분석
        trendsQuery.append("SELECT ");
        trendsQuery.append(timeGrouping).append(" as time_period, ");
        trendsQuery.append("       COUNT(DISTINCT o.order_id) as order_count, ");
        trendsQuery.append("       SUM(o.total_amount) as total_revenue, ");
        trendsQuery.append("       AVG(o.total_amount) as avg_order_value, ");
        trendsQuery.append("       COUNT(DISTINCT o.user_id) as unique_customers, ");
        
        // 이전 기간 대비 성장률 계산 (윈도우 함수)
        trendsQuery.append("       LAG(SUM(o.total_amount), 1) OVER (ORDER BY ").append(timeGrouping).append(") as prev_revenue, ");
        trendsQuery.append("       ROUND(((SUM(o.total_amount) - LAG(SUM(o.total_amount), 1) OVER (ORDER BY ").append(timeGrouping).append(")) / ");
        trendsQuery.append("              NULLIF(LAG(SUM(o.total_amount), 1) OVER (ORDER BY ").append(timeGrouping).append("), 0)) * 100, 2) as revenue_growth_pct, ");
        
        // 이동 평균 계산
        trendsQuery.append("       AVG(SUM(o.total_amount)) OVER (ORDER BY ").append(timeGrouping);
        trendsQuery.append("                                      ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as moving_avg_revenue ");
        
        // FROM 절
        String fromClause = String.format(
            "FROM orders_%s o " +
            "INNER JOIN order_items_%s oi ON o.order_id = oi.order_id " +
            "INNER JOIN products_%s p ON oi.product_id = p.product_id ",
            environment, environment, environment
        );
        
        trendsQuery.append(fromClause);
        
        // WHERE 절 (최근 N 기간)
        trendsQuery.append("WHERE o.order_date >= DATE_SUB(CURDATE(), INTERVAL ").append(periodCount);
        switch (periodType) {
            case "DAILY":
                trendsQuery.append(" DAY) ");
                break;
            case "WEEKLY":
                trendsQuery.append(" WEEK) ");
                break;
            case "MONTHLY":
                trendsQuery.append(" MONTH) ");
                break;
            case "QUARTERLY":
                trendsQuery.append(" QUARTER) ");
                break;
        }
        
        trendsQuery.append("  AND o.status = 'COMPLETED' ");
        
        // GROUP BY 절
        trendsQuery.append("GROUP BY ").append(timeGrouping).append(" ");
        
        // ORDER BY 절
        trendsQuery.append("ORDER BY time_period DESC");
        
        return executeTrendsQuery(trendsQuery.toString());
    }

    // 헬퍼 메서드들 (실제 쿼리 실행 시뮬레이션)
    
    private List<Map<String, Object>> executeHybridQuery(String query) {
        System.out.println("Executing hybrid query: " + query);
        return generateMockResults(50, "hybrid_result");
    }
    
    private List<Map<String, Object>> executeComplexAnalysisQuery(String query) {
        System.out.println("Executing complex analysis: " + query);
        return generateMockResults(100, "analysis_result");
    }
    
    private List<Map<String, Object>> executeInventoryQuery(String query, Date date) {
        System.out.println("Executing inventory query: " + query);
        return generateMockResults(75, "inventory_result");
    }
    
    private List<Map<String, Object>> executePerformanceQuery(String query) {
        System.out.println("Executing performance query: " + query);
        return generateMockResults(25, "performance_result");
    }
    
    private List<Map<String, Object>> executeHierarchyQuery(String query) {
        System.out.println("Executing hierarchy query: " + query);
        return generateMockResults(30, "hierarchy_result");
    }
    
    private List<Map<String, Object>> executeTrendsQuery(String query) {
        System.out.println("Executing trends query: " + query);
        return generateMockResults(60, "trends_result");
    }
    
    private List<Map<String, Object>> generateMockResults(int count, String type) {
        List<Map<String, Object>> results = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            Map<String, Object> row = new HashMap<>();
            row.put("id", i + 1);
            row.put("type", type);
            row.put("data", type + "_data_" + i);
            row.put("value", Math.random() * 1000);
            results.add(row);
        }
        return results;
    }
    
    // 추가 헬퍼 클래스
    private void logQueryExecution(String query, long executionTime) {
        if (metricsCollector != null) {
            metricsCollector.recordQueryMetrics(query, executionTime);
        }
    }
    
    private Connection getConnection() throws SQLException {
        return dataSource.getConnection();
    }
}

// 의존성 클래스
class SqlMetricsCollector {
    public void recordQueryMetrics(String query, long executionTime) {
        System.out.println("Query metrics - Execution time: " + executionTime + "ms");
    }
}
