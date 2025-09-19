package com.example.testcase;

import com.example.model.User;
import java.util.*;

/**
 * Enhanced SQL 추출 테스트용 DAO 클래스
 * Java 정규식 패턴 매칭 테스트 케이스
 */
public class TestEnhancedSqlDao {
    
    /**
     * 테스트 1: 단순 + 연산자 패턴
     * 예상 테이블: users
     */
    public List<User> testSimpleConcatenation() {
        String sql = "SELECT u.user_id, u.username, u.email ";
        sql = sql + "FROM users u ";
        sql = sql + "WHERE u.status = 'ACTIVE' ";
        sql = sql + "ORDER BY u.created_date DESC";
        
        System.out.println("Simple Concat SQL: " + sql);
        return new ArrayList<>();
    }
    
    /**
     * 테스트 2: 조건부 + 연산자 패턴
     * 예상 테이블: users, orders (조건부), products (조건부)
     */
    public List<Map<String, Object>> testConditionalConcatenation(boolean includeOrders, boolean includeProducts) {
        String sql = "SELECT u.user_id, u.username ";
        sql = sql + "FROM users u ";
        
        if (includeOrders) {
            sql = sql + "LEFT JOIN orders o ON u.user_id = o.user_id ";
        }
        
        if (includeProducts && includeOrders) {
            sql = sql + "LEFT JOIN products p ON o.product_id = p.product_id ";
        }
        
        sql = sql + "WHERE u.status = 'ACTIVE'";
        
        System.out.println("Conditional Concat SQL: " + sql);
        return new ArrayList<>();
    }
    
    /**
     * 테스트 3: 반복문 + 연산자 패턴
     * 예상 테이블: users + 동적 테이블들
     */
    public List<Map<String, Object>> testLoopConcatenation(List<String> joinTables) {
        String sql = "SELECT u.user_id, u.username ";
        sql = sql + "FROM users u ";
        
        for (String table : joinTables) {
            sql = sql + "LEFT JOIN " + table + " t ON u.user_id = t.user_id ";
        }
        
        sql = sql + "WHERE u.status = 'ACTIVE'";
        
        System.out.println("Loop Concat SQL: " + sql);
        return new ArrayList<>();
    }
    
    /**
     * 테스트 4: INSERT + 연산자 패턴
     * 예상 테이블: user_audit_logs
     */
    public int testInsertConcatenation(String userId, String action) {
        String sql = "INSERT INTO user_audit_logs ";
        sql = sql + "(user_id, action_type, action_details, created_date) ";
        sql = sql + "VALUES ";
        sql = sql + "('" + userId + "', '" + action + "', 'Auto generated log', SYSDATE)";
        
        System.out.println("Insert Concat SQL: " + sql);
        return 1;
    }
    
    /**
     * 테스트 5: UPDATE + 연산자 패턴
     * 예상 테이블: users
     */
    public int testUpdateConcatenation(String userId, Map<String, Object> updateFields) {
        String sql = "UPDATE users ";
        sql = sql + "SET last_modified_date = SYSDATE ";
        
        if (updateFields.containsKey("email")) {
            sql = sql + ", email = '" + updateFields.get("email") + "' ";
        }
        
        if (updateFields.containsKey("status")) {
            sql = sql + ", status = '" + updateFields.get("status") + "' ";
        }
        
        sql = sql + "WHERE user_id = '" + userId + "'";
        
        System.out.println("Update Concat SQL: " + sql);
        return 1;
    }
    
    /**
     * 테스트 6: DELETE + 연산자 패턴
     * 예상 테이블: user_sessions
     */
    public int testDeleteConcatenation(String userId, String sessionType) {
        String sql = "DELETE FROM user_sessions ";
        sql = sql + "WHERE user_id = '" + userId + "' ";
        
        if (sessionType != null) {
            sql = sql + "AND session_type = '" + sessionType + "' ";
        }
        
        sql = sql + "AND created_date < SYSDATE - 7";
        
        System.out.println("Delete Concat SQL: " + sql);
        return 1;
    }
    
    /**
     * 테스트 7: MERGE + 연산자 패턴  
     * 예상 테이블: user_statistics, users (참조)
     */
    public int testMergeConcatenation(String tablePrefix) {
        String sql = "MERGE INTO user_statistics us ";
        sql = sql + "USING (SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id) o ";
        sql = sql + "ON (us.user_id = o.user_id) ";
        sql = sql + "WHEN MATCHED THEN ";
        sql = sql + "UPDATE SET us.total_orders = o.order_count, us.last_updated = SYSDATE ";
        sql = sql + "WHEN NOT MATCHED THEN ";
        sql = sql + "INSERT (user_id, total_orders, last_updated) ";
        sql = sql + "VALUES (o.user_id, o.order_count, SYSDATE)";
        
        System.out.println("Merge Concat SQL: " + sql);
        return 1;
    }
    
    /**
     * 테스트 8: 복잡한 서브쿼리 + 연산자 패턴
     * 예상 테이블: users, orders, products, categories
     */
    public List<Map<String, Object>> testComplexSubqueryConcatenation() {
        String sql = "SELECT u.user_id, u.username, ";
        sql = sql + "(SELECT COUNT(*) FROM orders o WHERE o.user_id = u.user_id) as order_count, ";
        sql = sql + "(SELECT COUNT(DISTINCT p.category_id) ";
        sql = sql + "FROM orders o2 ";
        sql = sql + "INNER JOIN order_items oi ON o2.order_id = oi.order_id ";
        sql = sql + "INNER JOIN products p ON oi.product_id = p.product_id ";
        sql = sql + "WHERE o2.user_id = u.user_id) as category_diversity ";
        sql = sql + "FROM users u ";
        sql = sql + "WHERE u.status = 'ACTIVE' ";
        sql = sql + "ORDER BY order_count DESC";
        
        System.out.println("Complex Subquery Concat SQL: " + sql);
        return new ArrayList<>();
    }
    
    /**
     * 테스트 9: 문자열 리터럴 내 SQL (정규식 매칭 테스트)
     * 예상 테이블: users, user_profiles
     */
    public void testStringLiteralSQL() {
        // 단순 문자열 리터럴 SQL
        String simpleSQL = "SELECT u.user_id, u.username FROM users u WHERE u.status = 'ACTIVE'";
        
        // 복잡한 문자열 리터럴 SQL  
        String complexSQL = "SELECT u.user_id, u.username, up.full_name " +
                           "FROM users u " +
                           "LEFT JOIN user_profiles up ON u.user_id = up.user_id " +
                           "WHERE u.status = 'ACTIVE' " +
                           "ORDER BY u.created_date DESC";
        
        // INSERT 문자열 리터럴
        String insertSQL = "INSERT INTO user_audit_logs (user_id, action_type, created_date) " +
                          "VALUES (1001, 'LOGIN', SYSDATE)";
        
        // UPDATE 문자열 리터럴
        String updateSQL = "UPDATE users SET last_login_date = SYSDATE " +
                          "WHERE user_id = 1001";
        
        // DELETE 문자열 리터럴
        String deleteSQL = "DELETE FROM user_sessions " +
                          "WHERE user_id = 1001 AND session_expired = 'Y'";
        
        // MERGE 문자열 리터럴
        String mergeSQL = "MERGE INTO user_statistics us " +
                         "USING (SELECT user_id FROM users WHERE status = 'ACTIVE') u " +
                         "ON (us.user_id = u.user_id) " +
                         "WHEN MATCHED THEN UPDATE SET last_updated = SYSDATE";
        
        System.out.println("String Literal SQLs created for regex testing");
    }
    
    /**
     * 테스트 10: 경계 케이스 - SQL이 아닌 문자열
     * 예상 결과: SQL로 인식되지 않아야 함
     */
    public void testNonSQLStrings() {
        String notSQL1 = "This is just a regular string with SELECT word";
        String notSQL2 = "Log message: FROM user action completed";
        String notSQL3 = "Configuration: UPDATE_INTERVAL = 5000";
        String notSQL4 = "Error: INSERT operation failed";
        
        // SQL 키워드가 있지만 실제 SQL이 아닌 케이스들
        String falsePositive1 = "SELECT your option FROM the menu";
        String falsePositive2 = "Please UPDATE your profile information";
        
        System.out.println("Non-SQL strings for false positive testing");
    }
}
