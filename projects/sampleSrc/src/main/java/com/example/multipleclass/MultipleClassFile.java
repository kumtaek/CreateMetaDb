package com.example.multipleclass;

/**
 * 테스트 케이스: 한 파일에 여러 클래스
 * - 하나의 .java 파일에 여러 클래스 정의 테스트
 * - 각 클래스가 개별적으로 추출되는지 테스트
 * - public 클래스와 package-private 클래스 혼재 테스트
 */

/**
 * 첫 번째 클래스 - public 클래스
 */
public class MultipleClassFile {

    private String mainData;

    public MultipleClassFile(String mainData) {
        this.mainData = mainData;
    }

    public String getMainData() {
        return mainData;
    }

    public void processMainData() {
        System.out.println("메인 데이터 처리: " + mainData);
    }
}

/**
 * 두 번째 클래스 - package-private 클래스
 */
class HelperClass {

    private String helperData;

    public HelperClass(String helperData) {
        this.helperData = helperData;
    }

    public String getHelperData() {
        return helperData;
    }

    /**
     * 비즈니스 로직이 포함된 헬퍼 메서드 - business 복잡도
     */
    public String processWithPrefix(String prefix) {
        if (prefix == null || prefix.isEmpty()) {
            return helperData;
        }
        return prefix + ": " + helperData.toUpperCase();
    }
}

/**
 * 세 번째 클래스 - 유틸리티 클래스
 */
class UtilityClass {

    /**
     * 정적 유틸리티 메서드 - simple 복잡도
     */
    public static String formatString(String input) {
        return input != null ? input.trim() : "";
    }

    /**
     * 복잡한 정적 메서드 - business 복잡도
     */
    public static boolean validateData(Object data) {
        if (data == null) {
            return false;
        }

        if (data instanceof String) {
            String str = (String) data;
            return !str.trim().isEmpty() && str.length() <= 100;
        }

        return true;
    }
}

/**
 * 네 번째 클래스 - final 클래스
 */
final class FinalHelperClass {

    private final String immutableData;

    public FinalHelperClass(String immutableData) {
        this.immutableData = immutableData;
    }

    public String getImmutableData() {
        return immutableData;
    }
}