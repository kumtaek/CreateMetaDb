package com.example.annotations;

import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;

/**
 * 테스트 케이스: 어노테이션이 많은 클래스
 * - 클래스 및 메서드 어노테이션 처리 테스트
 * - 어노테이션이 파싱에 영향을 주지 않는지 테스트
 * - Spring 어노테이션 처리 테스트
 */
@Service
@Deprecated
public class AnnotatedClass {

    @Autowired
    private String injectedDependency;

    /**
     * 어노테이션이 있는 생성자
     */
    @Deprecated
    public AnnotatedClass() {
        // 기본 생성자
    }

    /**
     * 복수 어노테이션이 있는 메서드 - business 복잡도
     */
    @Override
    @SuppressWarnings("unchecked")
    @Deprecated
    public String toString() {
        return "AnnotatedClass{" +
                "injectedDependency='" + injectedDependency + '\'' +
                '}';
    }

    /**
     * 어노테이션 파라미터가 있는 메서드
     */
    @SuppressWarnings({"unchecked", "rawtypes"})
    public void methodWithAnnotationParams() {
        System.out.println("어노테이션 파라미터 테스트");
    }

    /**
     * 커스텀 어노테이션 테스트
     */
    @CustomAnnotation(value = "test", timeout = 5000)
    public void customAnnotatedMethod() {
        System.out.println("커스텀 어노테이션 메서드");
    }

    /**
     * 중첩된 어노테이션 테스트
     */
    @NestedAnnotation(
        primary = @CustomAnnotation(value = "primary", timeout = 1000),
        secondary = @CustomAnnotation(value = "secondary", timeout = 2000)
    )
    public void nestedAnnotationMethod() {
        System.out.println("중첩된 어노테이션 메서드");
    }
}

/**
 * 커스텀 어노테이션 정의
 */
@interface CustomAnnotation {
    String value() default "";
    int timeout() default 0;
}

/**
 * 중첩된 어노테이션 정의
 */
@interface NestedAnnotation {
    CustomAnnotation primary();
    CustomAnnotation secondary();
}