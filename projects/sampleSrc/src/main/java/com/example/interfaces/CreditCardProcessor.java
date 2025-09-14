package com.example.interfaces;

import java.math.BigDecimal;

/**
 * 테스트 케이스: 인터페이스 구현
 * - implements 키워드 테스트
 * - 인터페이스 구현 클래스 테스트
 * - 메타DB에서 implements는 상속 관계로 저장하지 않음 (extends만 저장)
 */
public class CreditCardProcessor implements PaymentProcessor {

    private String merchantId;

    public CreditCardProcessor(String merchantId) {
        this.merchantId = merchantId;
    }

    /**
     * 신용카드 결제 처리
     */
    @Override
    public boolean processPayment(BigDecimal amount, String paymentMethod) {
        System.out.println("신용카드 결제 처리: " + amount + " 원, 방식: " + paymentMethod);
        return true;
    }

    /**
     * 결제 검증
     */
    @Override
    public boolean validatePayment(String transactionId) {
        System.out.println("거래 검증: " + transactionId);
        return true;
    }

    /**
     * 환불 처리
     */
    @Override
    public void processRefund(String transactionId, BigDecimal amount) {
        System.out.println("환불 처리: " + transactionId + ", 금액: " + amount + " 원");
    }

    /**
     * merchant ID getter
     */
    public String getMerchantId() {
        return merchantId;
    }
}