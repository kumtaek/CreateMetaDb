package com.example.dao;

import com.example.model.User;
import com.example.model.Product;
import java.util.*;

/**
 * 핵심 SQL 패턴 테스트용 DAO 클래스
 * 파서가 지원해야 하는 핵심 패턴들만 집중 구현
 * 목표: 테이블명과 조인 관계 추출
 */
public class CoreSqlPatternDao {
    
    /**
     * ========================================
     * 패턴 1: + 연산자를 사용한 SQL 문자열 조합
     * ========================================
     */
    
    /**
     * SELECT: + 연산자로 테이블명과 JOIN 절 동적 구성
     */
    public List<Map<String, Object>> selectWithPlusOperatorJoin(String mainTable, List<String> joinTables, Map<String, Object> conditions) {
        try {
            // 기본 SELECT 절 (+ 연산자)
            String selectClause = "SELECT " + mainTable.substring(0, 1) + ".* ";
            String fromClause = "FROM " + mainTable + " " + mainTable.substring(0, 1) + " ";
            String joinClause = "";
            String whereClause = "WHERE 1=1 ";
            
            // 동적 JOIN 절 추가 (+ 연산자로 테이블 조인)
            for (String joinTable : joinTables) {
                String alias = joinTable.substring(0, 1);
                selectClause = selectClause + ", " + alias + ".* ";
                
                if (joinTable.equals("user_profiles")) {
                    joinClause = joinClause + "LEFT JOIN " + joinTable + " " + alias + " ON " + mainTable.substring(0, 1) + ".user_id = " + alias + ".user_id ";
                } else if (joinTable.equals("orders")) {
                    joinClause = joinClause + "LEFT JOIN " + joinTable + " " + alias + " ON " + mainTable.substring(0, 1) + ".user_id = " + alias + ".user_id ";
                } else if (joinTable.equals("products")) {
                    joinClause = joinClause + "INNER JOIN " + joinTable + " " + alias + " ON " + mainTable.substring(0, 1) + ".product_id = " + alias + ".product_id ";
                } else if (joinTable.equals("categories")) {
                    joinClause = joinClause + "LEFT JOIN " + joinTable + " " + alias + " ON p.category_id = " + alias + ".category_id ";
                }
            }
            
            // 동적 WHERE 조건 (+ 연산자)
            if (conditions.get("status") != null) {
                whereClause = whereClause + "AND " + mainTable.substring(0, 1) + ".status = '" + conditions.get("status") + "' ";
            }
            
            if (conditions.get("dateFrom") != null) {
                whereClause = whereClause + "AND " + mainTable.substring(0, 1) + ".created_date >= '" + conditions.get("dateFrom") + "' ";
            }
            
            // 최종 쿼리 조합 (+ 연산자로 모든 테이블 연결)
            String finalQuery = selectClause + fromClause + joinClause + whereClause + "ORDER BY " + mainTable.substring(0, 1) + ".created_date DESC";
            
            System.out.println("Plus Operator JOIN SELECT: " + finalQuery);
            return generateSampleResults(10);
            
        } catch (Exception e) {
            System.err.println("+ 연산자 JOIN SELECT 오류: " + e.getMessage());
            throw new RuntimeException("+ 연산자 JOIN SELECT 실패", e);
        }
    }
    
    /**
     * INSERT: + 연산자로 동적 테이블명 구성
     */
    public int insertWithPlusOperatorTable(String baseTable, String tableSuffix, Map<String, Object> data) {
        try {
            // 동적 테이블명 구성 (+ 연산자)
            String targetTable = baseTable;
            if (tableSuffix != null && !tableSuffix.isEmpty()) {
                targetTable = targetTable + "_" + tableSuffix;
            }
            
            // INSERT 쿼리 구성 (+ 연산자)
            String insertQuery = "INSERT INTO " + targetTable + " ";
            String columnClause = "(";
            String valueClause = "VALUES (";
            
            // 동적 컬럼과 값 추가 (+ 연산자)
            boolean first = true;
            for (Map.Entry<String, Object> entry : data.entrySet()) {
                if (!first) {
                    columnClause = columnClause + ", ";
                    valueClause = valueClause + ", ";
                }
                columnClause = columnClause + entry.getKey();
                valueClause = valueClause + "'" + entry.getValue() + "'";
                first = false;
            }
            
            columnClause = columnClause + ")";
            valueClause = valueClause + ")";
            
            // 최종 INSERT 쿼리 (+ 연산자로 테이블명 포함)
            String finalQuery = insertQuery + columnClause + " " + valueClause;
            
            System.out.println("Plus Operator INSERT: " + finalQuery);
            return 1;
            
        } catch (Exception e) {
            System.err.println("+ 연산자 INSERT 오류: " + e.getMessage());
            throw new RuntimeException("+ 연산자 INSERT 실패", e);
        }
    }
    
    /**
     * UPDATE: + 연산자로 JOIN을 포함한 UPDATE
     */
    public int updateWithPlusOperatorJoin(String mainTable, String joinTable, String joinCondition, Map<String, Object> updateData, Map<String, Object> whereConditions) {
        try {
            // UPDATE with JOIN 구성 (+ 연산자)
            String updateClause = "UPDATE " + mainTable + " m ";
            String joinClause = "INNER JOIN " + joinTable + " j ON " + joinCondition + " ";
            String setClause = "SET ";
            String whereClause = "WHERE 1=1 ";
            
            // SET 절 구성 (+ 연산자)
            boolean first = true;
            for (Map.Entry<String, Object> entry : updateData.entrySet()) {
                if (!first) {
                    setClause = setClause + ", ";
                }
                setClause = setClause + "m." + entry.getKey() + " = '" + entry.getValue() + "'";
                first = false;
            }
            
            // WHERE 절 구성 (+ 연산자)
            for (Map.Entry<String, Object> entry : whereConditions.entrySet()) {
                whereClause = whereClause + "AND m." + entry.getKey() + " = '" + entry.getValue() + "' ";
            }
            
            // 최종 UPDATE 쿼리 (+ 연산자로 테이블들 연결)
            String finalQuery = updateClause + joinClause + setClause + " " + whereClause;
            
            System.out.println("Plus Operator JOIN UPDATE: " + finalQuery);
            return 1;
            
        } catch (Exception e) {
            System.err.println("+ 연산자 JOIN UPDATE 오류: " + e.getMessage());
            throw new RuntimeException("+ 연산자 JOIN UPDATE 실패", e);
        }
    }
    
    /**
     * DELETE: + 연산자로 다중 테이블 DELETE
     */
    public int deleteWithPlusOperatorMultiTable(String mainTable, List<String> relatedTables, String keyColumn, String keyValue) {
        try {
            String deleteQuery = "";
            
            // 관련 테이블들 순서대로 DELETE (+ 연산자)
            for (String relatedTable : relatedTables) {
                deleteQuery = deleteQuery + "DELETE FROM " + relatedTable + " WHERE " + keyColumn + " = '" + keyValue + "'; ";
            }
            
            // 메인 테이블 DELETE (+ 연산자)
            deleteQuery = deleteQuery + "DELETE FROM " + mainTable + " WHERE " + keyColumn + " = '" + keyValue + "'";
            
            System.out.println("Plus Operator Multi-table DELETE: " + deleteQuery);
            return 1;
            
        } catch (Exception e) {
            System.err.println("+ 연산자 다중 테이블 DELETE 오류: " + e.getMessage());
            throw new RuntimeException("+ 연산자 다중 테이블 DELETE 실패", e);
        }
    }
    
    /**
     * MERGE: + 연산자로 테이블 간 MERGE
     */
    public int mergeWithPlusOperator(String targetTable, String sourceTable, String joinCondition, Map<String, String> updateColumns, Map<String, String> insertColumns) {
        try {
            // MERGE 기본 구조 (+ 연산자)
            String mergeQuery = "MERGE INTO " + targetTable + " t ";
            String usingClause = "USING " + sourceTable + " s ON (" + joinCondition + ") ";
            String whenMatched = "";
            String whenNotMatched = "";
            
            // WHEN MATCHED 절 (+ 연산자)
            if (!updateColumns.isEmpty()) {
                whenMatched = whenMatched + "WHEN MATCHED THEN UPDATE SET ";
                boolean first = true;
                for (Map.Entry<String, String> entry : updateColumns.entrySet()) {
                    if (!first) {
                        whenMatched = whenMatched + ", ";
                    }
                    whenMatched = whenMatched + "t." + entry.getKey() + " = s." + entry.getValue();
                    first = false;
                }
                whenMatched = whenMatched + " ";
            }
            
            // WHEN NOT MATCHED 절 (+ 연산자)
            if (!insertColumns.isEmpty()) {
                whenNotMatched = whenNotMatched + "WHEN NOT MATCHED THEN INSERT (";
                String valueClause = "VALUES (";
                boolean first = true;
                for (Map.Entry<String, String> entry : insertColumns.entrySet()) {
                    if (!first) {
                        whenNotMatched = whenNotMatched + ", ";
                        valueClause = valueClause + ", ";
                    }
                    whenNotMatched = whenNotMatched + entry.getKey();
                    valueClause = valueClause + "s." + entry.getValue();
                    first = false;
                }
                whenNotMatched = whenNotMatched + ") " + valueClause + ") ";
            }
            
            // 최종 MERGE 쿼리 (+ 연산자로 테이블들 연결)
            String finalQuery = mergeQuery + usingClause + whenMatched + whenNotMatched;
            
            System.out.println("Plus Operator MERGE: " + finalQuery);
            return 1;
            
        } catch (Exception e) {
            System.err.println("+ 연산자 MERGE 오류: " + e.getMessage());
            throw new RuntimeException("+ 연산자 MERGE 실패", e);
        }
    }
    
    /**
     * ========================================
     * 패턴 2: String.format을 사용한 동적 테이블명/컬럼명 삽입
     * ========================================
     */
    
    /**
     * SELECT: String.format으로 동적 테이블명과 JOIN 구성
     */
    public List<Map<String, Object>> selectWithStringFormat(String tablePrefix, String environment, List<String> joinTypes, Map<String, Object> filters) {
        try {
            // String.format으로 동적 테이블명과 JOIN 구성
            String selectQuery = String.format(
                "SELECT u.user_id, u.username, u.email, p.product_name, o.order_date " +
                "FROM users_%s u " +
                "%s JOIN products_%s p ON u.user_id = p.created_by " +
                "%s JOIN orders_%s o ON u.user_id = o.user_id ",
                environment,
                joinTypes.get(0),
                environment, 
                joinTypes.get(1),
                environment
            );
            
            // 추가 테이블 조인 (String.format)
            if (filters.get("includePayments") != null) {
                String paymentJoin = String.format(
                    "LEFT JOIN payments_%s pm ON o.order_id = pm.order_id ",
                    environment
                );
                selectQuery = selectQuery + paymentJoin;
            }
            
            // WHERE 절 (String.format)
            String whereClause = String.format(
                "WHERE u.status = '%s' AND o.order_date >= '%s' ",
                filters.getOrDefault("status", "ACTIVE"),
                filters.getOrDefault("dateFrom", "2024-01-01")
            );
            
            String finalQuery = selectQuery + whereClause + "ORDER BY o.order_date DESC";
            
            System.out.println("String.format SELECT: " + finalQuery);
            return generateSampleResults(15);
            
        } catch (Exception e) {
            System.err.println("String.format SELECT 오류: " + e.getMessage());
            throw new RuntimeException("String.format SELECT 실패", e);
        }
    }
    
    /**
     * INSERT: String.format으로 환경별 테이블 INSERT
     */
    public int insertWithStringFormat(String entityType, String environment, Map<String, Object> data) {
        try {
            // String.format으로 환경별 테이블명 구성
            String insertQuery = String.format(
                "INSERT INTO %s_%s (id, name, status, created_date) " +
                "VALUES ('%s', '%s', '%s', SYSDATE)",
                entityType,
                environment,
                data.get("id"),
                data.get("name"),
                data.get("status")
            );
            
            // 관련 테이블에도 INSERT (String.format)
            if (data.get("createAudit") != null) {
                String auditInsert = String.format(
                    "INSERT INTO %s_audit_%s (entity_id, action, created_date) " +
                    "VALUES ('%s', 'INSERT', SYSDATE)",
                    entityType,
                    environment,
                    data.get("id")
                );
                insertQuery = insertQuery + "; " + auditInsert;
            }
            
            System.out.println("String.format INSERT: " + insertQuery);
            return 1;
            
        } catch (Exception e) {
            System.err.println("String.format INSERT 오류: " + e.getMessage());
            throw new RuntimeException("String.format INSERT 실패", e);
        }
    }
    
    /**
     * UPDATE: String.format으로 다중 환경 테이블 UPDATE
     */
    public int updateWithStringFormat(String entityType, List<String> environments, String entityId, Map<String, Object> updateData) {
        try {
            String updateQuery = "";
            
            // 여러 환경의 테이블 동시 UPDATE (String.format)
            for (String env : environments) {
                String envUpdate = String.format(
                    "UPDATE %s_%s SET name = '%s', status = '%s', updated_date = SYSDATE WHERE id = '%s'",
                    entityType,
                    env,
                    updateData.get("name"),
                    updateData.get("status"),
                    entityId
                );
                
                if (!updateQuery.isEmpty()) {
                    updateQuery = updateQuery + "; ";
                }
                updateQuery = updateQuery + envUpdate;
                
                // 관련 통계 테이블도 UPDATE (String.format)
                String statsUpdate = String.format(
                    "UPDATE %s_stats_%s SET updated_count = updated_count + 1, last_updated = SYSDATE WHERE entity_type = '%s'",
                    entityType,
                    env,
                    entityType
                );
                updateQuery = updateQuery + "; " + statsUpdate;
            }
            
            System.out.println("String.format Multi-env UPDATE: " + updateQuery);
            return environments.size();
            
        } catch (Exception e) {
            System.err.println("String.format UPDATE 오류: " + e.getMessage());
            throw new RuntimeException("String.format UPDATE 실패", e);
        }
    }
    
    /**
     * DELETE: String.format으로 환경별 CASCADE DELETE
     */
    public int deleteWithStringFormat(String entityType, String environment, String entityId, boolean cascadeDelete) {
        try {
            String deleteQuery = "";
            
            if (cascadeDelete) {
                // 관련 테이블들 CASCADE DELETE (String.format)
                String[] relatedTables = {"audit", "stats", "history", "cache"};
                
                for (String relatedTable : relatedTables) {
                    String cascadeDelete1 = String.format(
                        "DELETE FROM %s_%s_%s WHERE entity_id = '%s'",
                        entityType, relatedTable, environment, entityId
                    );
                    
                    if (!deleteQuery.isEmpty()) {
                        deleteQuery = deleteQuery + "; ";
                    }
                    deleteQuery = deleteQuery + cascadeDelete1;
                }
            }
            
            // 메인 테이블 DELETE (String.format)
            String mainDelete = String.format(
                "DELETE FROM %s_%s WHERE id = '%s'",
                entityType, environment, entityId
            );
            
            if (!deleteQuery.isEmpty()) {
                deleteQuery = deleteQuery + "; ";
            }
            deleteQuery = deleteQuery + mainDelete;
            
            System.out.println("String.format CASCADE DELETE: " + deleteQuery);
            return 1;
            
        } catch (Exception e) {
            System.err.println("String.format DELETE 오류: " + e.getMessage());
            throw new RuntimeException("String.format DELETE 실패", e);
        }
    }
    
    /**
     * MERGE: String.format으로 환경 간 데이터 MERGE
     */
    public int mergeWithStringFormat(String entityType, String sourceEnv, String targetEnv, Map<String, Object> options) {
        try {
            // String.format으로 환경 간 MERGE 구성
            String mergeQuery = String.format(
                "MERGE INTO %s_%s t " +
                "USING %s_%s s ON (t.id = s.id) ",
                entityType, targetEnv,
                entityType, sourceEnv
            );
            
            // WHEN MATCHED 절 (String.format)
            String whenMatched = String.format(
                "WHEN MATCHED THEN " +
                "UPDATE SET t.name = s.name, t.status = s.status, t.updated_date = SYSDATE "
            );
            
            // WHEN NOT MATCHED 절 (String.format)
            String whenNotMatched = String.format(
                "WHEN NOT MATCHED THEN " +
                "INSERT (id, name, status, created_date) " +
                "VALUES (s.id, s.name, s.status, SYSDATE) "
            );
            
            String finalMerge = mergeQuery + whenMatched + whenNotMatched;
            
            // 관련 테이블도 MERGE (String.format)
            if (options.get("mergeAudit") != null) {
                String auditMerge = String.format(
                    "MERGE INTO %s_audit_%s t " +
                    "USING %s_audit_%s s ON (t.entity_id = s.entity_id) " +
                    "WHEN NOT MATCHED THEN INSERT (entity_id, action, created_date) " +
                    "VALUES (s.entity_id, 'MERGE', SYSDATE)",
                    entityType, targetEnv,
                    entityType, sourceEnv
                );
                finalMerge = finalMerge + "; " + auditMerge;
            }
            
            System.out.println("String.format MERGE: " + finalMerge);
            return 1;
            
        } catch (Exception e) {
            System.err.println("String.format MERGE 오류: " + e.getMessage());
            throw new RuntimeException("String.format MERGE 실패", e);
        }
    }
    
    /**
     * ========================================
     * 패턴 3: 조건부 JOIN 절 추가
     * ========================================
     */
    
    /**
     * 조건부 JOIN을 사용한 복합 데이터 조회
     */
    public List<Map<String, Object>> selectWithConditionalJoin(String baseTable, Map<String, Boolean> joinOptions, Map<String, Object> filters) {
        try {
            // 기본 쿼리 구성
            String selectClause = "SELECT b.* ";
            String fromClause = "FROM " + baseTable + " b ";
            String joinClause = "";
            String whereClause = "WHERE b.status = 'ACTIVE' ";
            
            // 조건부 JOIN 절들 (각 옵션에 따라 테이블 조인)
            if (joinOptions.getOrDefault("includeUserInfo", false)) {
                selectClause = selectClause + ", u.username, u.email ";
                joinClause = joinClause + "LEFT JOIN users u ON b.user_id = u.user_id ";
            }
            
            if (joinOptions.getOrDefault("includeProductInfo", false)) {
                selectClause = selectClause + ", p.product_name, p.price ";
                joinClause = joinClause + "LEFT JOIN products p ON b.product_id = p.product_id ";
            }
            
            if (joinOptions.getOrDefault("includeOrderInfo", false)) {
                selectClause = selectClause + ", o.order_date, o.total_amount ";
                joinClause = joinClause + "LEFT JOIN orders o ON b.order_id = o.order_id ";
            }
            
            if (joinOptions.getOrDefault("includeCategoryInfo", false)) {
                selectClause = selectClause + ", c.category_name ";
                joinClause = joinClause + "LEFT JOIN categories c ON p.category_id = c.category_id ";
            }
            
            if (joinOptions.getOrDefault("includePaymentInfo", false)) {
                selectClause = selectClause + ", pm.payment_method, pm.payment_status ";
                joinClause = joinClause + "LEFT JOIN payments pm ON o.order_id = pm.order_id ";
            }
            
            // 동적 WHERE 조건
            if (filters.get("dateFrom") != null) {
                whereClause = whereClause + "AND b.created_date >= '" + filters.get("dateFrom") + "' ";
            }
            
            if (filters.get("userType") != null) {
                whereClause = whereClause + "AND u.user_type = '" + filters.get("userType") + "' ";
            }
            
            // 최종 쿼리 조합 (조건부 JOIN으로 필요한 테이블들만 연결)
            String finalQuery = selectClause + fromClause + joinClause + whereClause + "ORDER BY b.created_date DESC";
            
            System.out.println("Conditional JOIN SELECT: " + finalQuery);
            return generateSampleResults(20);
            
        } catch (Exception e) {
            System.err.println("조건부 JOIN SELECT 오류: " + e.getMessage());
            throw new RuntimeException("조건부 JOIN SELECT 실패", e);
        }
    }
    
    /**
     * 극도로 복잡한 현실적 패턴 - 실제 대형 프로젝트에서 볼 수 있는 패턴
     */
    public Map<String, Object> executeEnterpriseComplexQuery(String operationType, 
                                                            Map<String, Object> businessParams,
                                                            List<String> datacenters) {
        try {
            Map<String, Object> results = new HashMap<>();
            String masterQuerySet = "";
            
            for (String datacenter : datacenters) {
                String dcPrefix = datacenter.toLowerCase();
                String dcQueries = "";
                
                if ("financial_reconciliation".equals(operationType)) {
                    // 금융 정산 쿼리 (실제 기업에서 사용할 법한 복잡도)
                    String reconciliationQuery = 
                        "WITH daily_transactions AS (" +
                        String.format("SELECT t.transaction_date, t.user_id, t.product_id, ") +
                        "SUM(CASE WHEN t.transaction_type = 'PURCHASE' THEN t.amount ELSE 0 END) as purchase_amount, " +
                        "SUM(CASE WHEN t.transaction_type = 'REFUND' THEN t.amount ELSE 0 END) as refund_amount, " +
                        "COUNT(DISTINCT t.payment_method) as payment_method_count " +
                        String.format("FROM transactions_%s_%s t ", dcPrefix, businessParams.get("year")) +
                        String.format("INNER JOIN users_%s u ON t.user_id = u.user_id ", dcPrefix) +
                        String.format("INNER JOIN products_%s p ON t.product_id = p.product_id ", dcPrefix) +
                        "WHERE t.transaction_date BETWEEN " +
                        String.format("TO_DATE('%s', 'YYYY-MM-DD') ", businessParams.get("dateFrom")) +
                        "AND " + String.format("TO_DATE('%s', 'YYYY-MM-DD') ", businessParams.get("dateTo")) +
                        "AND t.status IN ('COMPLETED', 'SETTLED') " +
                        "AND u.account_status = 'VERIFIED' " +
                        "GROUP BY t.transaction_date, t.user_id, t.product_id" +
                        "), " +
                        // 복잡한 정산 로직
                        "settlement_calculation AS (" +
                        String.format("SELECT dt.transaction_date, ") +
                        "SUM(dt.purchase_amount) as daily_revenue, " +
                        "SUM(dt.refund_amount) as daily_refunds, " +
                        "SUM(dt.purchase_amount - dt.refund_amount) as net_revenue, " +
                        "COUNT(DISTINCT dt.user_id) as unique_customers, " +
                        "AVG(dt.purchase_amount) as avg_transaction_amount " +
                        "FROM daily_transactions dt " +
                        String.format("INNER JOIN user_tiers_%s ut ON dt.user_id = ut.user_id ", dcPrefix) +
                        "WHERE ut.tier_level IN ('GOLD', 'PLATINUM', 'DIAMOND') " +
                        "GROUP BY dt.transaction_date" +
                        ") " +
                        // 최종 정산 리포트
                        "SELECT " +
                        "sc.transaction_date, sc.daily_revenue, sc.daily_refunds, sc.net_revenue, " +
                        "sc.unique_customers, sc.avg_transaction_amount, " +
                        String.format("ROUND(sc.net_revenue * %s, 2) as platform_fee, ", "0.03") + // 3% 수수료
                        String.format("ROUND(sc.net_revenue * %s, 2) as tax_amount, ", "0.10") + // 10% 세금
                        "ROUND(sc.net_revenue * " + String.format("%s", "0.87") + ", 2) as final_settlement " + // 87% 정산
                        "FROM settlement_calculation sc " +
                        "ORDER BY sc.transaction_date DESC";
                    
                    dcQueries = reconciliationQuery;
                    
                } else if ("customer_segmentation".equals(operationType)) {
                    // 고객 세분화 분석 (머신러닝 스타일의 복잡한 쿼리)
                    String segmentationQuery = 
                        "WITH customer_behavior AS (" +
                        String.format("SELECT u.user_id, u.user_type, ") +
                        "COUNT(DISTINCT o.order_id) as order_frequency, " +
                        "AVG(o.total_amount) as avg_order_value, " +
                        "SUM(o.total_amount) as total_lifetime_value, " +
                        "STDDEV(o.total_amount) as order_value_variance, " +
                        "COUNT(DISTINCT DATE(o.order_date)) as active_days, " +
                        "MAX(o.order_date) as last_order_date, " +
                        "MIN(o.order_date) as first_order_date " +
                        String.format("FROM users_%s u ", dcPrefix) +
                        String.format("INNER JOIN orders_%s o ON u.user_id = o.user_id ", dcPrefix) +
                        String.format("LEFT JOIN user_preferences_%s up ON u.user_id = up.user_id ", dcPrefix) +
                        "WHERE o.order_date >= " + String.format("ADD_MONTHS(SYSDATE, -%d) ", 24) + // 2년 데이터
                        "AND o.status = 'COMPLETED' " +
                        "AND u.status = 'ACTIVE' " +
                        "GROUP BY u.user_id, u.user_type" +
                        "), " +
                        // 상품 선호도 분석
                        "product_preferences AS (" +
                        String.format("SELECT cb.user_id, ") +
                        "COUNT(DISTINCT c.category_id) as category_diversity, " +
                        "MODE() WITHIN GROUP (ORDER BY c.category_name) as preferred_category, " +
                        "AVG(pr.rating) as avg_product_rating " +
                        "FROM customer_behavior cb " +
                        String.format("INNER JOIN orders_%s o ON cb.user_id = o.user_id ", dcPrefix) +
                        String.format("INNER JOIN order_items_%s oi ON o.order_id = oi.order_id ", dcPrefix) +
                        String.format("INNER JOIN products_%s p ON oi.product_id = p.product_id ", dcPrefix) +
                        String.format("INNER JOIN categories_%s c ON p.category_id = c.category_id ", dcPrefix) +
                        String.format("LEFT JOIN product_reviews_%s pr ON p.product_id = pr.product_id AND pr.user_id = cb.user_id ", dcPrefix) +
                        "GROUP BY cb.user_id" +
                        ") " +
                        // 최종 세분화 결과
                        "SELECT " +
                        "cb.user_id, cb.user_type, " +
                        "CASE " +
                        "WHEN cb.total_lifetime_value >= " + String.format("%d ", 1000000) + 
                        "AND cb.order_frequency >= " + String.format("%d ", 50) + 
                        "THEN 'VIP_CHAMPION' " +
                        "WHEN cb.total_lifetime_value >= " + String.format("%d ", 500000) + 
                        "AND cb.order_frequency >= " + String.format("%d ", 20) + 
                        "THEN 'PREMIUM_LOYAL' " +
                        "WHEN cb.avg_order_value >= " + String.format("%d ", 100000) + 
                        "THEN 'HIGH_VALUE' " +
                        "WHEN cb.order_frequency >= " + String.format("%d ", 10) + 
                        "THEN 'FREQUENT_BUYER' " +
                        "WHEN MONTHS_BETWEEN(SYSDATE, cb.last_order_date) <= " + String.format("%d ", 3) + 
                        "THEN 'RECENT_ACTIVE' " +
                        "ELSE 'STANDARD' " +
                        "END as customer_segment, " +
                        "cb.order_frequency, cb.avg_order_value, cb.total_lifetime_value, " +
                        "pp.category_diversity, pp.preferred_category, pp.avg_product_rating " +
                        "FROM customer_behavior cb " +
                        "INNER JOIN product_preferences pp ON cb.user_id = pp.user_id " +
                        "ORDER BY cb.total_lifetime_value DESC, cb.order_frequency DESC";
                    
                    dcQueries = segmentationQuery;
                }
                
                if (!masterQuerySet.isEmpty()) {
                    masterQuerySet = masterQuerySet + "; ";
                }
                masterQuerySet = masterQuerySet + dcQueries;
            }
            
            System.out.println("Enterprise Complex Query: " + masterQuerySet);
            
            results.put("operationType", operationType);
            results.put("datacenters", datacenters);
            results.put("masterQuerySet", masterQuerySet);
            results.put("complexity", "ENTERPRISE_LEVEL");
            
            return results;
            
        } catch (Exception e) {
            System.err.println("기업급 복잡 쿼리 오류: " + e.getMessage());
            throw new RuntimeException("기업급 복잡 쿼리 실패", e);
        }
    }
    
    // 유틸리티 메서드
    private List<Map<String, Object>> generateSampleResults(int count) {
        List<Map<String, Object>> results = new ArrayList<>();
        for (int i = 1; i <= count; i++) {
            Map<String, Object> row = new HashMap<>();
            row.put("id", "ID" + String.format("%03d", i));
            row.put("name", "Sample_" + i);
            row.put("status", i % 3 == 0 ? "INACTIVE" : "ACTIVE");
            row.put("created_date", new Date());
            results.add(row);
        }
        return results;
    }
    
    /**
     * Oracle 전용 구문과 IMPLICIT JOIN 패턴 추가 (DAO 레벨)
     * 실제 DBA와 개발자들이 작성할 법한 고급 Oracle 패턴들
     */
    
    /**
     * Oracle IMPLICIT JOIN with 복잡한 서브쿼리 (실제 데이터 웨어하우스 스타일)
     */
    public List<Map<String, Object>> executeOracleDataWarehouseQuery(String environment, Map<String, Object> dwParams) {
        try {
            // Oracle 데이터 웨어하우스 스타일 쿼리 (IMPLICIT JOIN + 윈도우 함수)
            String dwQuery = "SELECT " +
                           "fact_data.date_key, " +
                           "fact_data.user_id, " +
                           "fact_data.product_id, " +
                           "fact_data.category_id, " +
                           "dim_user.username, " +
                           "dim_user.user_type, " +
                           "dim_product.product_name, " +
                           "dim_category.category_name, " +
                           "fact_data.order_amount, " +
                           "fact_data.quantity, " +
                           "SUM(fact_data.order_amount) OVER (PARTITION BY fact_data.user_id) as user_total_spent, " +
                           "SUM(fact_data.order_amount) OVER (PARTITION BY fact_data.category_id) as category_total_revenue, " +
                           "RANK() OVER (PARTITION BY fact_data.date_key ORDER BY fact_data.order_amount DESC) as daily_order_rank, " +
                           "LAG(fact_data.order_amount, 1) OVER (PARTITION BY fact_data.user_id ORDER BY fact_data.date_key) as prev_order_amount, " +
                           "LEAD(fact_data.order_amount, 1) OVER (PARTITION BY fact_data.user_id ORDER BY fact_data.date_key) as next_order_amount, " +
                           "FIRST_VALUE(fact_data.order_amount) OVER (PARTITION BY fact_data.user_id ORDER BY fact_data.date_key " +
                           "ROWS UNBOUNDED PRECEDING) as first_order_amount, " +
                           "LAST_VALUE(fact_data.order_amount) OVER (PARTITION BY fact_data.user_id ORDER BY fact_data.date_key " +
                           "ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as latest_order_amount " +
                           // 팩트 테이블 (IMPLICIT JOIN으로 구성)
                           String.format("FROM (") +
                           String.format("SELECT TO_CHAR(o.order_date, 'YYYY-MM-DD') as date_key, ") +
                           "o.user_id, oi.product_id, p.category_id, " +
                           "SUM(oi.quantity * oi.unit_price) as order_amount, " +
                           "SUM(oi.quantity) as quantity " +
                           String.format("FROM orders_%s o, order_items_%s oi, products_%s p ", environment, environment, environment) +
                           "WHERE o.order_id = oi.order_id " +
                           "AND oi.product_id = p.product_id " +
                           "AND o.order_date >= " + String.format("ADD_MONTHS(SYSDATE, -%d) ", 6) +
                           "AND o.status = 'COMPLETED' " +
                           "GROUP BY TO_CHAR(o.order_date, 'YYYY-MM-DD'), o.user_id, oi.product_id, p.category_id" +
                           ") fact_data, " +
                           // 사용자 차원 테이블 (IMPLICIT JOIN)
                           String.format("(SELECT u.user_id, u.username, u.user_type, u.status, ") +
                           "p.full_name, p.department, p.city " +
                           String.format("FROM users_%s u, user_profiles_%s p ", environment, environment) +
                           "WHERE u.user_id = p.user_id " +
                           "AND u.status = 'ACTIVE') dim_user, " +
                           // 상품 차원 테이블
                           String.format("(SELECT pr.product_id, pr.product_name, pr.price, ") +
                           "pr.category_id, s.supplier_name " +
                           String.format("FROM products_%s pr, suppliers_%s s ", environment, environment) +
                           "WHERE pr.supplier_id = s.supplier_id " +
                           "AND pr.status = 'ACTIVE') dim_product, " +
                           // 카테고리 차원 테이블
                           String.format("(SELECT c.category_id, c.category_name, c.parent_category_id ") +
                           String.format("FROM categories_%s c ", environment) +
                           "WHERE c.status = 'ACTIVE') dim_category " +
                           "WHERE fact_data.user_id = dim_user.user_id " +
                           "AND fact_data.product_id = dim_product.product_id " +
                           "AND fact_data.category_id = dim_category.category_id " +
                           "ORDER BY fact_data.date_key DESC, fact_data.order_amount DESC";
            
            System.out.println("Oracle Data Warehouse Query with IMPLICIT JOIN: " + dwQuery);
            
            // 서비스 계층 호출
            List<User> results = userService.getUsersByAdvancedCondition(dwParams);
            
            model.addAttribute("environment", environment);
            model.addAttribute("dwParams", dwParams);
            model.addAttribute("results", results);
            model.addAttribute("generatedQuery", dwQuery);
            
            return "user/dataWarehouseResult";
            
        } catch (Exception e) {
            model.addAttribute("error", "Oracle 데이터 웨어하우스 분석 중 오류: " + e.getMessage());
            return "user/error";
        }
    }
}
