package com.example.jpa.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.domain.AuditorAware;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.transaction.annotation.EnableTransactionManagement;

import javax.persistence.EntityManagerFactory;
import javax.sql.DataSource;
import java.util.Optional;

/**
 * JPA 설정 클래스
 * JPA Entity -> Repository -> Service -> Controller -> Vue 연결 구조를 위한 설정
 */
@Configuration
@EnableJpaRepositories(
    basePackages = "com.example.jpa.repository",
    entityManagerFactoryRef = "entityManagerFactory",
    transactionManagerRef = "transactionManager"
)
@EnableJpaAuditing(auditorAwareRef = "auditorProvider")
@EnableTransactionManagement
public class JpaConfig {
    
    @Value("${app.jpa.test.enabled:true}")
    private boolean jpaTestEnabled;
    
    @Value("${app.pagination.default-page-size:20}")
    private int defaultPageSize;
    
    @Value("${app.pagination.max-page-size:100}")
    private int maxPageSize;
    
    /**
     * JPA Auditing을 위한 Auditor Provider
     * 엔티티의 생성자/수정자 정보를 자동으로 설정
     */
    @Bean
    public AuditorAware<String> auditorProvider() {
        return () -> {
            // 실제 애플리케이션에서는 Security Context에서 사용자 정보를 가져옴
            // 테스트케이스에서는 고정값 사용
            return Optional.of("SYSTEM");
        };
    }
    
    /**
     * JPA 쿼리 메서드 이름 전략 설정
     */
    @Bean
    public org.springframework.data.repository.query.QueryLookupStrategy.Key queryLookupStrategy() {
        return org.springframework.data.repository.query.QueryLookupStrategy.Key.CREATE_IF_NOT_FOUND;
    }
    
    /**
     * 페이징 설정을 위한 Bean
     */
    @Bean
    public org.springframework.data.web.config.PageableHandlerMethodArgumentResolverCustomizer pageableCustomizer() {
        return pageableResolver -> {
            pageableResolver.setOneIndexedParameters(false); // 0-based 페이징
            pageableResolver.setMaxPageSize(maxPageSize);
            pageableResolver.setFallbackPageable(
                org.springframework.data.domain.PageRequest.of(0, defaultPageSize)
            );
        };
    }
    
    /**
     * JPA 메타모델 생성 설정
     */
    @Bean
    public javax.persistence.metamodel.Metamodel jpaMetamodel(EntityManagerFactory entityManagerFactory) {
        return entityManagerFactory.getMetamodel();
    }
    
    /**
     * JPA 테스트 데이터 초기화 설정
     */
    @Bean
    public JpaTestDataInitializer jpaTestDataInitializer() {
        return new JpaTestDataInitializer(jpaTestEnabled);
    }
    
    /**
     * 커스텀 Repository 구현체 설정
     */
    @Bean
    public org.springframework.data.jpa.repository.support.JpaRepositoryFactoryBean jpaRepositoryFactoryBean() {
        return new org.springframework.data.jpa.repository.support.JpaRepositoryFactoryBean();
    }
}

