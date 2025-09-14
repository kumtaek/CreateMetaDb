package com.example.inheritance;

/**
 * 테스트 케이스: 상속 관계 - 자식 클래스
 * - extends 키워드 테스트
 * - 상속 관계 추출 및 relationships 테이블 저장 테스트
 * - 메서드 오버라이드 테스트
 */
public class ConcreteService extends BaseService {

    private String additionalInfo;

    public ConcreteService(String serviceName, String additionalInfo) {
        super(serviceName);
        this.additionalInfo = additionalInfo;
    }

    /**
     * 추상 메서드 구현 - 상속 관계에서 메서드 구현 테스트
     */
    @Override
    public void executeService() {
        System.out.println("서비스 실행: " + serviceName + " - " + additionalInfo);
    }

    /**
     * 추가 메서드 - 자식 클래스 고유 기능
     */
    public void performAdditionalTask() {
        System.out.println("추가 작업 수행: " + additionalInfo);
    }

    /**
     * getter 메서드
     */
    public String getAdditionalInfo() {
        return additionalInfo;
    }
}