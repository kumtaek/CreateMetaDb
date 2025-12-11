package com.example.sqltext;

/**
 * SQLTEXT 샘플 2: 변수/파라미터로 받은 SQL ID를 실행하고 배치 호출까지 포함한 예제.
 */
public class SqlManagerVariableBatchSample {

    private final SqlManagerSupport sqlManager;

    public SqlManagerVariableBatchSample(SqlManagerSupport sqlManager) {
        this.sqlManager = sqlManager;
    }

    /** 변수에 담긴 SQL ID 실행 */
    public void runVariableSamples() {
        String sqlId = "AC_SQL_1002";
        sqlManager.execute(sqlId);

        String batchId = buildBatchId("AC_SQL_", "1003");
        sqlManager.executeBatch(batchId);
    }

    /**
     * 외부 입력을 받아 정규화 후 실행 (예: 요청 파라미터 등).
     * @param rawSqlId 입력받은 SQL ID
     */
    public void handleRequest(String rawSqlId) {
        if (rawSqlId == null) {
            return;
        }
        String normalized = normalize(rawSqlId);
        if (normalized.isEmpty()) {
            return;
        }

        sqlManager.execute(normalized);
        if (shouldRunBatch(normalized)) {
            sqlManager.executeBatch(normalized);
        }
    }

    private String buildBatchId(String prefix, String suffix) {
        return (prefix == null ? "" : prefix) + (suffix == null ? "" : suffix);
    }

    private String normalize(String sqlId) {
        return sqlId.trim().toUpperCase();
    }

    private boolean shouldRunBatch(String sqlId) {
        return sqlId.startsWith("AC_SQL_") || sqlId.startsWith("NP_SQL_");
    }
}
