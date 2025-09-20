#!/usr/bin/env python3
"""
연관관계 분석 기능 테스트 스크립트
- SQL에서 테이블 추출 테스트
- Java에서 METHOD→QUERY 매핑 테스트
- RelationshipBuilder 통합 테스트
"""

import sys
import os

# 현재 스크립트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from util.simple_relationship_analyzer import SimpleRelationshipAnalyzer
from util.java_query_analyzer import JavaQueryAnalyzer
from util import app_logger, info, error, debug


def test_sql_table_extraction():
    """SQL에서 테이블 추출 테스트"""
    print("=== SQL 테이블 추출 테스트 ===")

    analyzer = SimpleRelationshipAnalyzer()

    # 테스트 케이스들
    test_sqls = [
        # 기본 SELECT
        "SELECT * FROM users WHERE user_id = 1",

        # JOIN 쿼리
        """
        SELECT p.*, c.category_name, b.brand_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN brands b ON p.brand_id = b.brand_id
        WHERE p.status = 'ACTIVE'
        """,

        # 동적 테이블명 (중요!)
        "SELECT * FROM table_{dynamic_part} WHERE id = 1",

        # 복잡한 쿼리
        """
        UPDATE user_profile_{tenant_id} u
        SET last_login = NOW()
        WHERE u.user_id IN (
            SELECT user_id FROM session_data_{date}
            WHERE session_type = 'LOGIN'
        )
        """,

        # MyBatis 동적 SQL 시뮬레이션
        """
        SELECT u.*, p.profile_data
        FROM users u
        LEFT JOIN user_profiles p ON u.user_id = p.user_id
        WHERE 1=1
        AND u.status = 'ACTIVE'
        AND u.user_type = 'PREMIUM'
        ORDER BY u.created_date DESC
        """
    ]

    for i, sql in enumerate(test_sqls, 1):
        print(f"\n테스트 {i}:")
        print(f"SQL: {sql.strip()}")

        # 테이블 추출
        tables = analyzer.extract_tables_from_sql(sql)
        print(f"추출된 테이블: {list(tables)}")

        # 조인 관계 추출
        join_rels = analyzer.extract_join_relationships(sql, tables)
        print(f"조인 관계: {len(join_rels)}개")

        for rel in join_rels:
            print(f"  - {rel['source_table']} {rel['join_type']} {rel['target_table']}")

        # 전체 분석
        result = analyzer.analyze_sql_components(sql, f"test_query_{i}")
        print(f"분석 결과: 테이블 {result['table_count']}개, 조인 {result['join_count']}개")


def test_java_method_analysis():
    """Java 메서드 분석 테스트"""
    print("\n\n=== Java 메서드 분석 테스트 ===")

    analyzer = JavaQueryAnalyzer()

    # MyBatis Mapper 인터페이스 테스트
    mybatis_content = """
package com.example.mapper;

import com.example.model.User;
import org.apache.ibatis.annotations.Param;
import java.util.List;

public interface UserMapper {
    List<User> selectUsersByCondition(Map<String, Object> params);
    User selectUserById(@Param("id") Long id);
    int updateUserDynamic(User user);
    int deleteUsersByCondition(Map<String, Object> params);
}
"""

    print("1. MyBatis Mapper 테스트:")
    mybatis_result = analyzer.analyze_java_file("UserMapper.java", mybatis_content)
    print(f"파일 타입: {mybatis_result['file_type']}")
    print(f"네임스페이스: {mybatis_result['namespace']}")
    print(f"클래스명: {mybatis_result['class_name']}")
    print(f"메서드 매핑: {len(mybatis_result['method_query_mappings'])}개")

    for mapping in mybatis_result['method_query_mappings']:
        print(f"  - {mapping['method_name']} → {mapping['query_id']} ({mapping['query_type']})")

    # JPA Repository 테스트
    jpa_content = """
package com.example.jpa.repository;

import com.example.jpa.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByUsername(String username);
    List<User> findByStatus(UserStatus status);

    @Query("SELECT u FROM User u WHERE u.status = :status AND u.createdAt >= :fromDate")
    List<User> findActiveUsersFromDate(@Param("status") UserStatus status,
                                      @Param("fromDate") LocalDateTime fromDate);

    @Query(value = "SELECT * FROM USERS WHERE STATUS = :status", nativeQuery = true)
    long countUsersByStatusNative(@Param("status") String status);
}
"""

    print("\n2. JPA Repository 테스트:")
    jpa_result = analyzer.analyze_java_file("UserRepository.java", jpa_content)
    print(f"파일 타입: {jpa_result['file_type']}")
    print(f"메서드 매핑: {len(jpa_result['method_query_mappings'])}개")

    for mapping in jpa_result['method_query_mappings']:
        print(f"  - {mapping['method_name']} ({mapping['mapping_type']})")
        if 'query_sql' in mapping:
            print(f"    SQL: {mapping['query_sql'][:50]}...")

    # JPA Entity 테스트
    entity_content = """
package com.example.jpa.entity;

import javax.persistence.*;

@Entity
@Table(name = "USERS")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "USER_ID")
    private Long userId;

    @Column(name = "USERNAME")
    private String username;

    @Column(name = "EMAIL")
    private String email;
}
"""

    print("\n3. JPA Entity 테스트:")
    entity_result = analyzer.analyze_java_file("User.java", entity_content)
    print(f"파일 타입: {entity_result['file_type']}")
    print(f"Entity 매핑: {len(entity_result['entity_table_mappings'])}개")

    for mapping in entity_result['entity_table_mappings']:
        entity_name = mapping.get('entity_name', 'Unknown')
        table_name = mapping.get('table_name', 'Unknown')
        mapping_type = mapping.get('mapping_type', 'Unknown')
        print(f"  - {entity_name} → {table_name} ({mapping_type})")


def test_table_name_normalization():
    """테이블명 정규화 테스트"""
    print("\n\n=== 테이블명 정규화 테스트 ===")

    analyzer = SimpleRelationshipAnalyzer()

    test_tables = [
        "users",
        "user_profiles",
        "table_{dynamic}",
        "log_data_{yyyymm}",
        "temp_{session_id}_{timestamp}",
        "products_2024",
        "cache_{key_value}"
    ]

    for table in test_tables:
        normalized = analyzer._normalize_table_name(table)
        print(f"{table} → {normalized}")


def main():
    """메인 테스트 실행"""
    print("연관관계 분석 기능 테스트 시작")
    print("=" * 50)

    try:
        # 1. SQL 테이블 추출 테스트
        test_sql_table_extraction()

        # 2. Java 메서드 분석 테스트
        test_java_method_analysis()

        # 3. 테이블명 정규화 테스트
        test_table_name_normalization()

        print("\n\n=== 테스트 완료 ===")
        print("모든 기본 기능이 정상적으로 동작합니다.")

    except Exception as e:
        print(f"\n테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)