package com.example.comments;

/*
 * 테스트 케이스: 주석이 많은 클래스
 * - 다양한 형태의 주석 처리 테스트
 * - 주석 내부의 코드와 실제 코드 구분 테스트
 * - 복잡한 주석 패턴 파싱 테스트
 */
public class CommentHeavyClass {

    // 단일 라인 주석
    private String simpleField;

    /*
     * 블록 주석
     * 여러 라인에 걸친 주석
     */
    private String blockCommentField;

    /**
     * JavaDoc 주석
     * @param simpleField 간단한 필드
     */
    public CommentHeavyClass(String simpleField) {
        this.simpleField = simpleField;
    }

    // getter 메서드 - simple 복잡도
    public String getSimpleField() {
        return simpleField;
    }

    /*
     * 주석 내부에 코드처럼 보이는 텍스트
     * public class FakeClass {
     *     public void fakeMethod() {
     *         System.out.println("이것은 주석입니다");
     *     }
     * }
     * 위의 코드는 주석이므로 파싱되지 않아야 함
     */
    public void methodWithFakeCodeInComment() {
        System.out.println("실제 메서드입니다");
    }

    /**
     * 복잡한 JavaDoc 주석을 가진 메서드 - business 복잡도
     *
     * @param input 입력 데이터
     * @param options 처리 옵션
     * @return 처리 결과
     * @throws IllegalArgumentException 잘못된 입력 시
     * @since 1.0
     * @deprecated 이 메서드는 deprecated 됨
     * @see #newProcessMethod(String, String)
     */
    @Deprecated
    public String processWithComplexJavaDoc(String input, String options) {
        if (input == null) {
            throw new IllegalArgumentException("입력이 null입니다");
        }

        // 처리 로직
        return input + " processed with " + options;
    }

    // 새로운 처리 메서드
    public String newProcessMethod(String input, String options) {
        if (input == null || input.trim().isEmpty()) {
            return "빈 입력값입니다";
        }
        
        if (options == null) {
            options = "default";
        }
        
        // 옵션에 따른 다양한 처리
        switch (options.toLowerCase()) {
            case "uppercase":
                return input.toUpperCase();
            case "lowercase":
                return input.toLowerCase();
            case "reverse":
                return new StringBuilder(input).reverse().toString();
            case "trim":
                return input.trim();
            default:
                return input + " [processed with " + options + "]";
        }
    }
    
    /**
     * 복잡한 데이터 처리 메서드 - complex 복잡도
     * 여러 단계의 처리와 예외 처리를 포함
     */
    public Map<String, Object> complexDataProcessing(List<String> inputList, 
                                                   Map<String, String> processingOptions) {
        Map<String, Object> result = new HashMap<>();
        
        if (inputList == null || inputList.isEmpty()) {
            result.put("error", "입력 리스트가 비어있습니다");
            return result;
        }
        
        try {
            // 1단계: 데이터 정제
            List<String> cleanedData = new ArrayList<>();
            for (String data : inputList) {
                if (data != null && !data.trim().isEmpty()) {
                    cleanedData.add(data.trim());
                }
            }
            
            // 2단계: 옵션에 따른 변환
            List<String> processedData = new ArrayList<>();
            String transformOption = processingOptions.getOrDefault("transform", "none");
            
            for (String data : cleanedData) {
                switch (transformOption) {
                    case "uppercase":
                        processedData.add(data.toUpperCase());
                        break;
                    case "lowercase":
                        processedData.add(data.toLowerCase());
                        break;
                    case "capitalize":
                        processedData.add(capitalizeFirst(data));
                        break;
                    default:
                        processedData.add(data);
                }
            }
            
            // 3단계: 통계 계산
            Map<String, Object> statistics = new HashMap<>();
            statistics.put("originalCount", inputList.size());
            statistics.put("cleanedCount", cleanedData.size());
            statistics.put("processedCount", processedData.size());
            statistics.put("averageLength", processedData.stream()
                .mapToInt(String::length)
                .average()
                .orElse(0.0));
            
            // 4단계: 결과 구성
            result.put("success", true);
            result.put("processedData", processedData);
            result.put("statistics", statistics);
            result.put("processingOptions", processingOptions);
            result.put("timestamp", new Date());
            
        } catch (Exception e) {
            result.put("error", "데이터 처리 중 오류 발생: " + e.getMessage());
            result.put("success", false);
        }
        
        return result;
    }
    
    /**
     * 첫 글자 대문자 변환 헬퍼 메서드
     */
    private String capitalizeFirst(String input) {
        if (input == null || input.isEmpty()) {
            return input;
        }
        
        return input.substring(0, 1).toUpperCase() + 
               (input.length() > 1 ? input.substring(1).toLowerCase() : "");
    }
    
    /**
     * 데이터 검증 메서드 - business 복잡도
     */
    public boolean validateComplexData(Object data, Map<String, Object> validationRules) {
        if (data == null) {
            return false;
        }
        
        // 타입별 검증
        if (data instanceof String) {
            String strData = (String) data;
            
            // 길이 검증
            if (validationRules.containsKey("minLength")) {
                int minLength = (Integer) validationRules.get("minLength");
                if (strData.length() < minLength) {
                    return false;
                }
            }
            
            if (validationRules.containsKey("maxLength")) {
                int maxLength = (Integer) validationRules.get("maxLength");
                if (strData.length() > maxLength) {
                    return false;
                }
            }
            
            // 패턴 검증
            if (validationRules.containsKey("pattern")) {
                String pattern = (String) validationRules.get("pattern");
                if (!strData.matches(pattern)) {
                    return false;
                }
            }
            
            // 금지 단어 검증
            if (validationRules.containsKey("forbiddenWords")) {
                @SuppressWarnings("unchecked")
                List<String> forbiddenWords = (List<String>) validationRules.get("forbiddenWords");
                String lowerData = strData.toLowerCase();
                
                for (String forbidden : forbiddenWords) {
                    if (lowerData.contains(forbidden.toLowerCase())) {
                        return false;
                    }
                }
            }
        }
        
        return true;
    } {
        return processWithComplexJavaDoc(input, options);
    }

    /*
     * 중첩된 블록 주석 테스트
     * /* 내부 블록 주석 시작
     *    이것은 중첩된 주석입니다
     *    public void shouldNotBeParsed() {}
     * */ // 내부 블록 주석 끝
     * 외부 블록 주석 계속...
     */
    public void methodAfterNestedComment() {
        System.out.println("중첩 주석 이후의 실제 메서드");
    }

    // public void commentedOutMethod() {
    //     System.out.println("이 메서드는 주석 처리됨");
    // }

    /**
     * 주석과 문자열이 혼재된 메서드 - business 복잡도
     */
    public void methodWithMixedCommentsAndStrings() {
        String codeInString = "public class StringClass { /* 주석 */ }";
        System.out.println(codeInString); // 문자열 출력

        /*
         * 블록 주석 내부
         * String fake = "/* 가짜 문자열 */";
         */

        String realString = "실제 문자열 /* 이것은 문자열 내부 */";
        System.out.println(realString);
    }

    // TODO: 이 메서드는 구현 예정
    // FIXME: 버그 수정 필요
    // NOTE: 중요한 참고사항
    public void methodWithTodoComments() {
        // 구현 예정
    }
}