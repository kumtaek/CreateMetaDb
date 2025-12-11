package com.example.sqltext;

/**
 * SQLTEXT 샘플 공통 인터페이스.
 * 실제 환경에서는 프로젝트의 SqlManager 구현체를 주입해 사용한다.
 */
public interface SqlManagerSupport {
    /**
     * 단일 SQL ID 실행 (예: sqlManager.execute("AC_SQL_1001")).
     * @param sqlId 실행할 SQL ID
     */
    void execute(String sqlId);

    /**
     * 배치 SQL ID 실행 (예: sqlManager.executeBatch("NP_SQL_1001")).
     * @param sqlId 실행할 SQL ID
     */
    void executeBatch(String sqlId);
}
