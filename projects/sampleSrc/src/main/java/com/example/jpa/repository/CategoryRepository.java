package com.example.jpa.repository;

import com.example.jpa.entity.Category;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * JPA Category Repository
 * 카테고리 관련 JPA 쿼리 패턴 테스트케이스
 */
@Repository
public interface CategoryRepository extends JpaRepository<Category, Long> {
    
    // 1. 기본 메서드명 기반 쿼리
    Optional<Category> findByCategoryCode(String categoryCode);
    
    List<Category> findByIsActive(Boolean isActive);
    
    List<Category> findByParentCategory(Category parentCategory);
    
    List<Category> findByParentCategoryIsNull(); // 최상위 카테고리
    
    List<Category> findByParentCategoryIsNotNull(); // 하위 카테고리
    
    // 2. 카테고리명 검색
    List<Category> findByCategoryNameContaining(String name);
    
    List<Category> findByCategoryNameContainingIgnoreCase(String name);
    
    // 3. 정렬 쿼리
    List<Category> findByIsActiveTrueOrderByDisplayOrderAsc();
    
    List<Category> findByParentCategoryCategoryIdOrderByDisplayOrderAsc(Long parentCategoryId);
    
    // 4. Count 쿼리
    long countByIsActive(Boolean isActive);
    
    long countByParentCategory(Category parentCategory);
    
    long countByParentCategoryIsNull();
    
    // 5. @Query - JPQL 쿼리
    @Query("SELECT c FROM Category c LEFT JOIN FETCH c.products WHERE c.categoryId = :categoryId")
    Optional<Category> findByIdWithProducts(@Param("categoryId") Long categoryId);
    
    @Query("SELECT c FROM Category c LEFT JOIN FETCH c.subCategories WHERE c.parentCategory IS NULL")
    List<Category> findRootCategoriesWithSubCategories();
    
    @Query("SELECT c FROM Category c WHERE c.parentCategory.categoryId = :parentId AND c.isActive = true")
    List<Category> findActiveSubCategories(@Param("parentId") Long parentId);
    
    // 6. 계층 구조 쿼리
    @Query("SELECT c FROM Category c WHERE c.parentCategory.categoryId = :parentId ORDER BY c.displayOrder")
    List<Category> findSubCategoriesByParentId(@Param("parentId") Long parentId);
    
    @Query("SELECT c FROM Category c WHERE c.categoryId IN " +
           "(SELECT sc.categoryId FROM Category sc WHERE sc.parentCategory.categoryId = :categoryId)")
    List<Category> findDirectSubCategories(@Param("categoryId") Long categoryId);
    
    // 7. 상품이 있는 카테고리 조회
    @Query("SELECT DISTINCT c FROM Category c JOIN c.products p WHERE p.status = 'ACTIVE'")
    List<Category> findCategoriesWithActiveProducts();
    
    @Query("SELECT c FROM Category c WHERE SIZE(c.products) > 0")
    List<Category> findCategoriesWithProducts();
    
    @Query("SELECT c FROM Category c WHERE SIZE(c.products) = 0")
    List<Category> findEmptyCategories();
    
    // 8. 집계 쿼리
    @Query("SELECT c.categoryName, COUNT(p) FROM Category c LEFT JOIN c.products p GROUP BY c.categoryId, c.categoryName")
    List<Object[]> getCategoryProductCounts();
    
    @Query("SELECT c, SIZE(c.products) FROM Category c WHERE c.isActive = true")
    List<Object[]> getActiveCategoriesWithProductCount();
    
    // 9. Native SQL 쿼리
    @Query(value = "SELECT * FROM CATEGORIES c WHERE c.IS_ACTIVE = true ORDER BY c.DISPLAY_ORDER", 
           nativeQuery = true)
    List<Category> findActiveCategoriesOrderedNative();
    
    // 10. 복잡한 계층 쿼리 (재귀 CTE는 JPA에서 제한적이므로 간단한 형태로)
    @Query("SELECT c FROM Category c WHERE c.parentCategory IS NULL OR c.parentCategory.categoryId = :rootId")
    List<Category> findCategoryHierarchy(@Param("rootId") Long rootId);
}

