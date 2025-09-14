package com.example.inheritance;

import java.util.List;

/**
 * 테스트 케이스: 상속 관계 - 부모 클래스
 * - abstract 클래스 테스트
 * - 상속될 기본 메서드 포함
 * - 비즈니스 로직 메서드 복잡도 분류 테스트
 */
public abstract class BaseService {

    protected String serviceName;

    public BaseService(String serviceName) {
        this.serviceName = serviceName;
    }

    /**
     * 단순 getter - simple 복잡도로 분류되어야 함
     */
    public String getServiceName() {
        return serviceName;
    }

    /**
     * 비즈니스 getter - business 복잡도로 분류되어야 함
     */
    public String getServiceNameWithPrefix() {
        return "Service: " + serviceName;
    }

    /**
     * 복잡한 비즈니스 메서드 - complex 복잡도로 분류되어야 함
     */
    public List<String> processDataWithValidation(List<String> inputData) {
        if (inputData == null || inputData.isEmpty()) {
            throw new IllegalArgumentException("입력 데이터가 필요합니다");
        }

        // 복잡한 처리 로직
        return inputData.stream()
            .filter(data -> data != null && !data.trim().isEmpty())
            .map(data -> serviceName + ": " + data.toUpperCase())
            .collect(java.util.stream.Collectors.toList());
    }

    /**
     * 추상 메서드 - 하위 클래스에서 구현해야 함
     */
    public abstract void executeService();
}