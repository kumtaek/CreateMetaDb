package com.example.sqltext;

/**
 * SQLTEXT 샘플 1: 리터럴 SQL ID를 그대로 실행하는 예제.
 * - 실제로 존재하는 sqltext 파일명(확장자 제외)을 사용한다.
 */
public class SqlManagerLiteralSample {

    private final SqlManagerSupport sqlManager;

    public SqlManagerLiteralSample(SqlManagerSupport sqlManager) {
        this.sqlManager = sqlManager;
    }

    /** 정해진 ID를 직접 실행 */
    public void runLiteralSamples() {
        sqlManager.execute("AC_SQL_1001");
        sqlManager.execute("AC_SQL_1002");
        sqlManager.executeBatch("NP_SQL_1001");
    }

    /** 배열로 묶어서 순회 실행 */
    public void runLoopSamples() {
        String[] ids = new String[] { "AC_SQL_1003", "NP_SQL_1002", "NP_SQL_1003" };
        for (String id : ids) {
            sqlManager.execute(id);
        }
    }
}
