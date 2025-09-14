package com.example.generics;

import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * 테스트 케이스: 제네릭 클래스
 * - 제네릭 타입 파라미터 처리 테스트
 * - 복잡한 제네릭 구문 파싱 테스트
 * - 제네릭 메서드 처리 테스트
 */
public class GenericClass<T, K extends Comparable<K>> {

    private T data;
    private Map<K, List<T>> dataMap;

    /**
     * 제네릭 생성자
     */
    public GenericClass(T data) {
        this.data = data;
    }

    /**
     * 단순 제네릭 getter - simple 복잡도
     */
    public T getData() {
        return data;
    }

    /**
     * 복잡한 제네릭 메서드 - complex 복잡도
     */
    public <V extends Number> Optional<V> processGenericData(
            List<? extends T> inputList,
            Map<? super K, ? extends V> processingMap) {

        if (inputList == null || inputList.isEmpty()) {
            return Optional.empty();
        }

        // 복잡한 제네릭 처리 로직
        return inputList.stream()
            .filter(item -> item != null)
            .findFirst()
            .map(item -> {
                // 제네릭 타입 변환 로직
                for (Map.Entry<? super K, ? extends V> entry : processingMap.entrySet()) {
                    if (entry.getValue() != null) {
                        return entry.getValue();
                    }
                }
                return null;
            });
    }

    /**
     * 와일드카드 제네릭 메서드 - business 복잡도
     */
    public boolean compareWithWildcard(GenericClass<?, ?> other) {
        if (other == null) {
            return false;
        }

        Object otherData = other.getData();
        if (this.data == null && otherData == null) {
            return true;
        }

        return this.data != null && this.data.equals(otherData);
    }

    /**
     * 제네릭 빌더 패턴 - business 복잡도
     */
    public static <T, K extends Comparable<K>> Builder<T, K> builder() {
        return new Builder<>();
    }

    /**
     * 내부 제네릭 빌더 클래스
     */
    public static class Builder<T, K extends Comparable<K>> {
        private T builderData;
        private Map<K, List<T>> builderDataMap;

        public Builder<T, K> withData(T data) {
            this.builderData = data;
            return this;
        }

        public Builder<T, K> withDataMap(Map<K, List<T>> dataMap) {
            this.builderDataMap = dataMap;
            return this;
        }

        public GenericClass<T, K> build() {
            GenericClass<T, K> instance = new GenericClass<>(builderData);
            instance.dataMap = this.builderDataMap;
            return instance;
        }
    }
}