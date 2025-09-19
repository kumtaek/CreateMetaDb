package com.example.testcase;

import java.util.*;

/**
 * 복잡한 Java SQL 패턴 테스트용 DAO 클래스
 * Enhanced Java SQL 추출 기능의 한계 테스트
 */
public class TestComplexJavaPatternDao {
    
    /**
     * 테스트 1: StringBuilder 패턴 (기존 지원)
     * 예상 테이블: users, orders
     */
    public List<Map<String, Object>> testStringBuilderPattern() {
        StringBuilder sql = new StringBuilder();
        sql.append("SELECT u.user_id, u.username, o.order_date ");
        sql.append("FROM users u ");
        sql.append("LEFT JOIN orders o ON u.user_id = o.user_id ");
        sql.append("WHERE u.status = 'ACTIVE' ");
        sql.append("ORDER BY o.order_date DESC");
        
        System.out.println("StringBuilder SQL: " + sql.toString());
        return new ArrayList<>();
    }
    
    /**
     * 테스트 2: String.format 패턴 (Enhanced 지원 목표)
     * 예상 테이블: users_dev, products_dev, orders_dev
     */
    public List<Map<String, Object>> testStringFormatPattern(String environment) {
        String sql = String.format(
            "SELECT u.user_id, u.username, p.product_name, o.order_date " +
            "FROM users_%s u " +
            "INNER JOIN orders_%s o ON u.user_id = o.user_id " +
            "INNER JOIN products_%s p ON o.product_id = p.product_id " +
            "WHERE u.status = 'ACTIVE' " +
            "ORDER BY o.order_date DESC",
            environment, environment, environment
        );
        
        System.out.println("String.format SQL: " + sql);
        return new ArrayList<>();
    }
    
    /**
     * 테스트 3: 변수 참조 패턴 (Enhanced 미지원 - 복잡도 높음)
     * 예상 결과: 추출되지 않아야 함 (의도적 제외)
     */
    public List<Map<String, Object>> testVariableReferencePattern() {
        String baseTable = "users";
        String joinTable = "orders";
        String condition = "u.user_id = o.user_id";
        
        // 변수 참조로 SQL 구성 (복잡한 패턴)
        String sql = "SELECT * FROM " + baseTable + " u ";
        sql = sql + "LEFT JOIN " + joinTable + " o ON " + condition;
        
        System.out.println("Variable Reference SQL: " + sql);
        return new ArrayList<>();
    }
    
    /**
     * 테스트 4: 메서드 호출 결과 패턴 (Enhanced 미지원 - 복잡도 높음)
     * 예상 결과: 추출되지 않아야 함 (의도적 제외)
     */
    public List<Map<String, Object>> testMethodCallPattern() {
        String sql = buildBaseQuery();
        sql = sql + buildJoinClause();
        sql = sql + buildWhereClause();
        
        System.out.println("Method Call SQL: " + sql);
        return new ArrayList<>();
    }
    
    private String buildBaseQuery() {
        return "SELECT u.user_id, u.username FROM users u ";
    }
    
    private String buildJoinClause() {
        return "LEFT JOIN orders o ON u.user_id = o.user_id ";
    }
    
    private String buildWhereClause() {
        return "WHERE u.status = 'ACTIVE'";
    }
    
    /**
     * 테스트 5: += 연산자 패턴 (Enhanced 지원 목표)
     * 예상 테이블: users, user_profiles, orders
     */
    public List<Map<String, Object>> testPlusEqualsPattern() {
        String sql = "SELECT u.user_id, u.username ";
        sql += "FROM users u ";
        sql += "LEFT JOIN user_profiles up ON u.user_id = up.user_id ";
        sql += "LEFT JOIN orders o ON u.user_id = o.user_id ";
        sql += "WHERE u.status = 'ACTIVE'";
        
        System.out.println("Plus Equals SQL: " + sql);
        return new ArrayList<>();
    }
    
    /**
     * 테스트 6: 혼합 패턴 (+ 연산자 + String.format)
     * 예상 테이블: users_prod, orders_prod
     */
    public List<Map<String, Object>> testMixedPattern(String environment) {
        String sql = "SELECT u.user_id, u.username ";
        sql = sql + String.format("FROM users_%s u ", environment);
        sql = sql + String.format("LEFT JOIN orders_%s o ON u.user_id = o.user_id ", environment);
        sql = sql + "WHERE u.status = 'ACTIVE'";
        
        System.out.println("Mixed Pattern SQL: " + sql);
        return new ArrayList<>();
    }
    
    /**
     * 테스트 7: 다중 라인 문자열 리터럴 (Enhanced 지원 목표)
     * 예상 테이블: users, orders, products, categories
     */
    public List<Map<String, Object>> testMultiLineStringLiteral() {
        String sql = "SELECT u.user_id, u.username, o.order_date, p.product_name, c.category_name " +
                    "FROM users u " +
                    "INNER JOIN orders o ON u.user_id = o.user_id " +
                    "INNER JOIN order_items oi ON o.order_id = oi.order_id " +
                    "INNER JOIN products p ON oi.product_id = p.product_id " +
                    "INNER JOIN categories c ON p.category_id = c.category_id " +
                    "WHERE u.status = 'ACTIVE' " +
                    "AND o.status = 'COMPLETED' " +
                    "ORDER BY o.order_date DESC";
        
        System.out.println("Multi-line String Literal SQL: " + sql);
        return new ArrayList<>();
    }
    
    /**
     * 테스트 8: MERGE 문자열 리터럴 (Enhanced 지원 목표)
     * 예상 테이블: user_statistics, users (참조)
     */
    public int testMergeStringLiteral() {
        String sql = "MERGE INTO user_statistics us " +
                    "USING (SELECT user_id, COUNT(*) as order_count " +
                    "       FROM orders " +
                    "       WHERE status = 'COMPLETED' " +
                    "       GROUP BY user_id) o " +
                    "ON (us.user_id = o.user_id) " +
                    "WHEN MATCHED THEN " +
                    "UPDATE SET us.total_orders = o.order_count, us.last_updated = SYSDATE " +
                    "WHEN NOT MATCHED THEN " +
                    "INSERT (user_id, total_orders, last_updated) " +
                    "VALUES (o.user_id, o.order_count, SYSDATE)";
        
        System.out.println("MERGE String Literal SQL: " + sql);
        return 1;
    }
    
    /**
     * 테스트 9: 경계 케이스 - SQL 키워드가 있지만 실제 SQL이 아닌 경우
     * 예상 결과: SQL로 인식되지 않아야 함
     */
    public void testFalsePositiveCases() {
        String notSQL1 = "Please SELECT your preferred option FROM the dropdown menu";
        String notSQL2 = "Log message: UPDATE operation completed successfully";
        String notSQL3 = "Error: INSERT failed due to constraint violation";
        String notSQL4 = "Configuration: DELETE_BATCH_SIZE = 1000";
        
        // 이런 문자열들은 SQL로 인식되면 안됨
        System.out.println("False positive test strings created");
    }
    
    /**
     * 테스트 10: 성능 테스트용 대용량 SQL
     * 예상 테이블: 다수의 테이블 (성능 측정용)
     */
    public List<Map<String, Object>> testLargeScaleSQL() {
        String sql = "SELECT ";
        
        // 많은 컬럼 추가
        for (int i = 1; i <= 20; i++) {
            sql = sql + "t" + i + ".field" + i + ", ";
        }
        sql = sql + "t1.main_id ";
        sql = sql + "FROM main_table t1 ";
        
        // 많은 JOIN 추가
        for (int i = 2; i <= 20; i++) {
            sql = sql + "LEFT JOIN table" + i + " t" + i + " ON t1.main_id = t" + i + ".main_id ";
        }
        
        sql = sql + "WHERE t1.status = 'ACTIVE'";
        
        System.out.println("Large Scale SQL: " + sql);
        return new ArrayList<>();
    }
}
