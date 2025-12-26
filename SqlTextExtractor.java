package com.analyzer.loading;

import java.io.*;
import java.sql.*;
import java.util.Properties;

/**
 * Oracle DB의 dp_sql_data 테이블에서 SQL 텍스트를 추출하여 파일로 저장하는 유틸리티 (Java 1.5 호환)
 * 
 * 주요 기능:
 * - Oracle JDBC 접속 (SID 또는 Service Name 지원)
 * - dp_sql_data 테이블의 job_type별 폴더 생성 및 sql_id 기반 파일 저장
 * - CLOB 데이터 읽기 처리
 * - Java 1.5 기반 구현 (제네릭 최소화, try-with-resources 미사용)
 * 
 * java com.analyzer.loading.SqlTextExtractor --id [유저] --password [암호] --ip [IP] --sid [SID] --output-dir [경로]
 * 
 */
public class SqlTextExtractor {

    /**
     * 메인 실행 메서드
     */
    public static void main(String[] args) {
        if (args.length < 5) {
            printUsage();
            return;
        }

        String user = "";
        String password = "";
        String host = "";
        String port = "1521";
        String sid = null;
        String serviceName = null;
        String outputDir = "projects/sampleSrc/sqltext_extracted";

        // 인자 파싱 (간이 방식)
        for (int i = 0; i < args.length; i++) {
            if (args[i].equals("--id")) user = args[++i];
            else if (args[i].equals("--password")) password = args[++i];
            else if (args[i].equals("--ip")) host = args[++i];
            else if (args[i].equals("--port")) port = args[++i];
            else if (args[i].equals("--sid")) sid = args[++i];
            else if (args[i].equals("--service-name")) serviceName = args[++i];
            else if (args[i].equals("--output-dir")) outputDir = args[++i];
        }

        execute(user, password, host, port, sid, serviceName, outputDir);
    }

    private static void printUsage() {
        System.out.println("Usage: java com.analyzer.loading.SqlTextExtractor --id [user] --password [pass] --ip [ip] --sid [sid] [options]");
        System.out.println("Options:");
        System.out.println("  --port [port]          (Default: 1521)");
        System.out.println("  --service-name [name]  (Alternative to --sid)");
        System.out.println("  --output-dir [dir]     (Default: projects/sampleSrc/sqltext_extracted)");
    }

    /**
     * SQL 추출 실행
     */
    public static void execute(String user, String password, String host, String port, String sid, String serviceName, String outputDir) {
        Connection conn = null;
        Statement stmt = null;
        ResultSet rs = null;

        try {
            // 1. 드라이브 로드 및 연결
            Class.forName("oracle.jdbc.driver.OracleDriver");
            
            String url;
            if (sid != null) {
                url = "jdbc:oracle:thin:@" + host + ":" + port + ":" + sid;
            } else {
                url = "jdbc:oracle:thin:@//" + host + ":" + port + "/" + serviceName;
            }

            System.out.println("[*] 연결 시도: " + url);
            Properties props = new Properties();
            props.setProperty("user", user);
            props.setProperty("password", password);
            
            conn = DriverManager.getConnection(url, props);
            System.out.println("[*] DB 접속 성공");

            // 2. 쿼리 실행
            stmt = conn.createStatement();
            String sql = "SELECT job_type, id, sql_text FROM dp_sql_data";
            rs = stmt.executeQuery(sql);

            int count = 0;
            File baseDir = new File(outputDir);
            if (!baseDir.exists()) baseDir.mkdirs();

            // 3. 결과 처리
            while (rs.next()) {
                String jobType = rs.getString("job_type");
                String sqlId = rs.getString("id");
                Clob clob = rs.getClob("sql_text");

                if (jobType == null || sqlId == null) continue;

                jobType = jobType.trim();
                sqlId = sqlId.trim();

                // CLOB 읽기
                String sqlContent = readClob(clob);

                // 폴더 생성
                File targetDir = new File(baseDir, jobType);
                if (!targetDir.exists()) targetDir.mkdirs();

                // 파일 써기 (UTF-8)
                File sqlFile = new File(targetDir, sqlId + ".sql");
                writeStringToFile(sqlFile, sqlContent);

                count++;
                if (count % 100 == 0) {
                    System.out.println("[*] " + count + "개 파일 추출 완료...");
                }
            }

            System.out.println("[*] 총 " + count + "개의 SQL 파일이 추출되었습니다.");
            System.out.println("[*] 저장 위치: " + baseDir.getAbsolutePath());

        } catch (Exception e) {
            System.err.println("[!] 오류 발생: " + e.getMessage());
            e.printStackTrace();
        } finally {
            // 리소스 닫기 (Java 1.5 수동 방식)
            if (rs != null) try { rs.close(); } catch (SQLException e) {}
            if (stmt != null) try { stmt.close(); } catch (SQLException e) {}
            if (conn != null) try { conn.close(); } catch (SQLException e) {}
        }
    }

    /**
     * CLOB 데이터를 문자열로 변환
     */
    private static String readClob(Clob clob) throws SQLException, IOException {
        if (clob == null) return "";
        
        StringBuilder sb = new StringBuilder();
        Reader reader = clob.getCharacterStream();
        char[] buffer = new char[8192];
        int read;
        try {
            while ((read = reader.read(buffer)) != -1) {
                sb.append(buffer, 0, read);
            }
        } finally {
            if (reader != null) reader.close();
        }
        return sb.toString();
    }

    /**
     * 문자열을 파일로 저장 (UTF-8)
     */
    private static void writeStringToFile(File file, String text) throws IOException {
        BufferedWriter writer = null;
        try {
            writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(file), "UTF-8"));
            writer.write(text);
        } finally {
            if (writer != null) writer.close();
        }
    }
}
