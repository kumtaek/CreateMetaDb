package com.example.complex;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.ArrayList;
import java.util.stream.Collectors;

/**
 * 테스트 케이스: 대용량 복잡한 클래스
 * - 메모리 최적화 스트리밍 처리 테스트
 * - 다양한 메서드 복잡도 분류 테스트
 * - 긴 클래스 본문 파싱 테스트
 * - 중첩된 주석 처리 테스트
 */
public class LargeBusinessClass {

    private Map<String, Object> dataCache = new HashMap<>();
    private List<String> processingQueue = new ArrayList<>();

    /**
     * 단순 getter - simple 복잡도
     */
    public Map<String, Object> getDataCache() {
        return dataCache;
    }

    /**
     * 단순 setter - simple 복잡도
     */
    public void setDataCache(Map<String, Object> dataCache) {
        this.dataCache = dataCache;
    }

    /**
     * 비즈니스 로직이 포함된 getter - business 복잡도
     * 데이터를 가공하여 반환
     */
    public List<String> getProcessedDataKeys() {
        return dataCache.keySet().stream()
            .filter(key -> key.startsWith("processed_"))
            .collect(Collectors.toList());
    }

    /**
     * 복잡한 비즈니스 메서드 - complex 복잡도
     * 다중 조건 분기와 복잡한 로직 포함
     */
    public void processBusinessData(String dataType, Object data, Map<String, String> options) {
        // /* 중첩된 블록 주석 테스트 시작
        //    이 주석은 파싱 시 올바르게 처리되어야 함
        // */ 중첩된 블록 주석 테스트 끝

        if (dataType == null || data == null) {
            throw new IllegalArgumentException("필수 파라미터가 누락되었습니다");
        }

        // 데이터 타입별 처리 분기
        switch (dataType.toLowerCase()) {
            case "user":
                processUserData(data, options);
                break;
            case "order":
                processOrderData(data, options);
                break;
            case "product":
                processProductData(data, options);
                break;
            default:
                processGenericData(data, options);
        }

        // 후처리 작업
        updateProcessingQueue(dataType);
        validateProcessingResult(dataType, data);
    }

    /**
     * 사용자 데이터 처리 - business 복잡도
     */
    private void processUserData(Object data, Map<String, String> options) {
        System.out.println("사용자 데이터 처리: " + data);
        dataCache.put("user_" + System.currentTimeMillis(), data);
    }

    /**
     * 주문 데이터 처리 - business 복잡도
     */
    private void processOrderData(Object data, Map<String, String> options) {
        System.out.println("주문 데이터 처리: " + data);
        dataCache.put("order_" + System.currentTimeMillis(), data);
    }

    /**
     * 상품 데이터 처리 - business 복잡도
     */
    private void processProductData(Object data, Map<String, String> options) {
        System.out.println("상품 데이터 처리: " + data);
        dataCache.put("product_" + System.currentTimeMillis(), data);
    }

    /**
     * 일반 데이터 처리 - simple 복잡도
     */
    private void processGenericData(Object data, Map<String, String> options) {
        dataCache.put("generic_" + System.currentTimeMillis(), data);
    }

    /**
     * 처리 큐 업데이트 - simple 복잡도
     */
    private void updateProcessingQueue(String dataType) {
        processingQueue.add(dataType + "_" + System.currentTimeMillis());
    }

    /**
     * 처리 결과 검증 - business 복잡도
     */
    private void validateProcessingResult(String dataType, Object data) {
        if (dataCache.isEmpty()) {
            throw new RuntimeException("데이터 처리 실패: 캐시가 비어있습니다");
        }

        // 검증 로직
        boolean isValid = dataCache.values().stream()
            .anyMatch(value -> value.equals(data));

        if (!isValid) {
            System.out.println("경고: 데이터 검증 실패 - " + dataType);
        }
    }

    /**
     * 대량 데이터 배치 처리 - complex 복잡도
     * 메모리 최적화가 필요한 대용량 데이터 처리
     */
    public Map<String, Integer> processBatchData(List<Map<String, Object>> batchData) {
        if (batchData == null || batchData.isEmpty()) {
            return new HashMap<>();
        }

        Map<String, Integer> statistics = new HashMap<>();

        // 스트림을 이용한 대용량 데이터 처리
        batchData.parallelStream()
            .filter(item -> item != null && !item.isEmpty())
            .forEach(item -> {
                String category = (String) item.getOrDefault("category", "unknown");
                statistics.merge(category, 1, Integer::sum);

                // 캐시에 저장 (메모리 관리)
                if (dataCache.size() < 1000) {  // 메모리 제한
                    dataCache.put(category + "_" + item.hashCode(), item);
                }
            });

        return statistics;
    }

    /**
     * 캐시 정리 - simple 복잡도
     */
    public void clearCache() {
        dataCache.clear();
        processingQueue.clear();
    }

    /**
     * 상태 정보 반환 - business 복잡도
     */
    public Map<String, Object> getSystemStatus() {
        Map<String, Object> status = new HashMap<>();
        status.put("cache_size", dataCache.size());
        status.put("queue_size", processingQueue.size());
        status.put("memory_usage", Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory());
        status.put("timestamp", System.currentTimeMillis());

        return status;
    }
}