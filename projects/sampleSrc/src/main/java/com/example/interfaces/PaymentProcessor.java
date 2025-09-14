package com.example.interfaces;

import java.math.BigDecimal;

/**
 * 테스트 케이스: 인터페이스
 * - interface 키워드 테스트
 * - 인터페이스 메서드 선언 테스트
 * - class_type 'interface'로 분류 테스트
 */
public interface PaymentProcessor {

    /**
     * 결제 처리 메서드
     */
    boolean processPayment(BigDecimal amount, String paymentMethod);

    /**
     * 결제 검증 메서드
     */
    boolean validatePayment(String transactionId);

    /**
     * 환불 처리 메서드
     */
    void processRefund(String transactionId, BigDecimal amount);
}