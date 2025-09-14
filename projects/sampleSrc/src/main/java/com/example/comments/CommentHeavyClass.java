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