package com.example.errors;

/**
 * 테스트 케이스: 구문 오류가 있는 클래스
 * - 파싱 에러 처리 테스트
 * - has_error='Y', error_message 저장 후 계속 진행 테스트
 * - 잘못된 구문이 포함된 파일 처리 테스트
 */
public class SyntaxErrorClass {

    private String validField;

    // 정상적인 생성자
    public SyntaxErrorClass(String validField) {
        this.validField = validField;
    }

    /**
     * 정상적인 메서드
     */
    public String getValidField() {
        return validField;
    }

    /**
     * 구문 오류가 있는 메서드 - 중괄호 누락
     */
    public void methodWithMissingBrace() {
        System.out.println("이 메서드는 중괄호가 누락되었습니다");
        // } <- 이 중괄호가 누락됨

    /**
     * 또 다른 정상 메서드
     */
    public void anotherValidMethod() {
        System.out.println("이 메서드는 정상입니다");
    }

    // 잘못된 구문 - 세미콜론 누락
    public String invalidSyntax()
        return "세미콜론이 누락된 메서드";
    }

    /**
     * 정상적인 마지막 메서드
     */
    public void finalMethod() {
        System.out.println("마지막 메서드");
    }

// 클래스 끝 중괄호 누락 시뮬레이션을 위해 주석 처리
// }