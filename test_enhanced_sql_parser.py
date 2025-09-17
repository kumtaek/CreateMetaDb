#!/usr/bin/env python3
"""
SQL 파서 테스트 스크립트
- 파싱불가쿼리.md의 케이스들을 검증
- 기존 파서와 성능 비교
"""

import sys
import os
from typing import Dict, List, Set

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parser.sql_parser import SqlParser
from util.logger import app_logger, info, debug


class SqlParserTestCase:
    """SQL 파서 테스트 케이스"""

    def __init__(self):
        """테스트 케이스 초기화"""
        self.sql_parser = SqlParser()
        self.test_cases = self._create_test_cases()

    def _create_test_cases(self) -> List[Dict]:
        """파싱불가쿼리.md 기반 테스트 케이스 생성"""
        return [
            {
                'name': '서브쿼리 케이스 - selectDashboardData',
                'description': '여러 서브쿼리가 포함된 SELECT 문',
                'sql': '''
                    SELECT
                        (SELECT COUNT(*) FROM users WHERE del_yn = 'N') as total_users,
                        (SELECT COUNT(*) FROM products WHERE del_yn = 'N' AND status = 'ACTIVE') as total_products,
                        (SELECT COUNT(*) FROM orders WHERE del_yn = 'N') as total_orders,
                        (SELECT SUM(total_amount) FROM orders WHERE del_yn = 'N' AND status = 'COMPLETED') as total_revenue,
                        (SELECT COUNT(*) FROM notifications WHERE del_yn = 'N' AND is_read = 'N') as unread_notifications,
                        (SELECT COUNT(*) FROM recommendations WHERE del_yn = 'N' AND status = 'ACTIVE') as active_recommendations
                ''',
                'expected_tables': {'USERS', 'PRODUCTS', 'ORDERS', 'NOTIFICATIONS', 'RECOMMENDATIONS'},
                'legacy_result': {'USERS WHERE', 'PRODUCTS WHERE', 'ORDERS WHERE', 'NOTIFICATIONS WHERE', 'RECOMMENDATIONS WHERE'}
            },
            {
                'name': 'UNION 케이스 - selectGlobalSearch',
                'description': 'UNION ALL로 결합된 다중 쿼리',
                'sql': '''
                    SELECT 'user' as type, user_id as id, username as name, email as description, created_at
                    FROM users
                    WHERE (username LIKE CONCAT('%', #{query}, '%') OR email LIKE CONCAT('%', #{query}, '%'))
                      AND del_yn = 'N'

                    UNION ALL

                    SELECT 'product' as type, product_id as id, product_name as name, description, created_at
                    FROM products
                    WHERE (product_name LIKE CONCAT('%', #{query}, '%') OR description LIKE CONCAT('%', #{query}, '%'))
                      AND del_yn = 'N'
                      AND status = 'ACTIVE'

                    UNION ALL

                    SELECT 'order' as type, order_id as id, CONCAT('Order #', order_id) as name,
                           CONCAT('Total: $', total_amount) as description, order_date as created_at
                    FROM orders
                    WHERE order_id LIKE CONCAT('%', #{query}, '%')
                      AND del_yn = 'N'

                    ORDER BY created_at DESC
                    LIMIT 50
                ''',
                'expected_tables': {'USERS', 'PRODUCTS', 'ORDERS'},
                'legacy_result': {'USERS WHERE', 'PRODUCTS WHERE', 'ORDERS WHERE'}
            },
            {
                'name': '동적 SQL 케이스 - selectOrdersV2',
                'description': 'MyBatis 동적 태그가 포함된 JOIN 쿼리',
                'sql': '''
                    SELECT o.order_id, o.user_id, o.order_date, o.total_amount, o.status, o.created_at,
                           u.username, u.email, COUNT(oi.order_item_id) as item_count
                    FROM orders o
                    JOIN users u ON o.user_id = u.user_id
                    LEFT JOIN order_items oi ON o.order_id = oi.order_id AND oi.del_yn = 'N'
                    WHERE o.del_yn = 'N'
                    <if test="status != null and status != ''">
                        AND o.status = #{status}
                    </if>
                    <if test="dateFrom != null and dateFrom != ''">
                        AND o.order_date >= #{dateFrom}
                    </if>
                    <if test="dateTo != null and dateTo != ''">
                        AND o.order_date <= #{dateTo}
                    </if>
                    GROUP BY o.order_id
                    ORDER BY o.order_date DESC
                ''',
                'expected_tables': {'ORDERS', 'USERS', 'ORDER_ITEMS'},
                'legacy_result': {'ORDERS O', 'USERS U', 'ORDER_ITEMS OI'}
            },
            {
                'name': '시스템 함수 케이스 - insertUserToV1',
                'description': '시스템 함수(NOW)가 포함된 INSERT 문',
                'sql': '''
                    INSERT INTO users_v1 (
                        username, email, status, created_at, del_yn
                    ) VALUES (
                        #{userData.username}, #{userData.email}, #{userData.status}, NOW(), 'N'
                    )
                ''',
                'expected_tables': {'USERS_V1'},
                'legacy_result': {'USERS_V1'}
            },
            {
                'name': '복합 서브쿼리 케이스',
                'description': 'EXISTS와 IN 서브쿼리가 모두 포함된 복합 쿼리',
                'sql': '''
                    SELECT u.user_id, u.username, u.email
                    FROM users u
                    WHERE EXISTS (
                        SELECT 1 FROM orders o
                        WHERE o.user_id = u.user_id
                        AND o.status = 'COMPLETED'
                    )
                    AND u.user_id IN (
                        SELECT DISTINCT customer_id
                        FROM purchases p
                        WHERE p.purchase_date >= '2024-01-01'
                    )
                    AND u.department_id IN (
                        SELECT dept_id FROM departments WHERE active = 'Y'
                    )
                ''',
                'expected_tables': {'USERS', 'ORDERS', 'PURCHASES', 'DEPARTMENTS'},
                'legacy_result': {'USERS U'}
            },
            {
                'name': '중첩 서브쿼리 케이스',
                'description': '서브쿼리 안에 또 다른 서브쿼리가 있는 경우',
                'sql': '''
                    SELECT customer_id,
                           (SELECT COUNT(*)
                            FROM orders o1
                            WHERE o1.customer_id = c.customer_id
                            AND o1.order_date >= (
                                SELECT MIN(promotion_start_date)
                                FROM promotions
                                WHERE status = 'ACTIVE'
                            )) as order_count
                    FROM customers c
                    WHERE c.status = 'ACTIVE'
                ''',
                'expected_tables': {'CUSTOMERS', 'ORDERS', 'PROMOTIONS'},
                'legacy_result': {'CUSTOMERS C'}
            },
            {
                'name': '다중 JOIN과 서브쿼리 조합',
                'description': 'JOIN과 서브쿼리가 복합적으로 사용된 케이스',
                'sql': '''
                    SELECT p.product_id, p.product_name, c.category_name, s.supplier_name,
                           (SELECT AVG(rating) FROM reviews r WHERE r.product_id = p.product_id) as avg_rating
                    FROM products p
                    INNER JOIN categories c ON p.category_id = c.category_id
                    LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
                    WHERE p.status = 'ACTIVE'
                    AND EXISTS (
                        SELECT 1 FROM inventory i
                        WHERE i.product_id = p.product_id
                        AND i.quantity > 0
                    )
                ''',
                'expected_tables': {'PRODUCTS', 'CATEGORIES', 'SUPPLIERS', 'REVIEWS', 'INVENTORY'},
                'legacy_result': {'PRODUCTS P', 'CATEGORIES C', 'SUPPLIERS S'}
            }
        ]

    def run_all_tests(self) -> None:
        """모든 테스트 케이스 실행"""
        try:
            info("=== 향상된 SQL 파서 테스트 시작 ===")

            passed_tests = 0
            total_tests = len(self.test_cases)

            for i, test_case in enumerate(self.test_cases, 1):
                info(f"\n[테스트 {i}/{total_tests}] {test_case['name']}")
                info(f"설명: {test_case['description']}")

                if self._run_single_test(test_case):
                    passed_tests += 1

            # 결과 요약
            info(f"\n=== 테스트 결과 요약 ===")
            info(f"전체 테스트: {total_tests}개")
            info(f"통과: {passed_tests}개")
            info(f"실패: {total_tests - passed_tests}개")
            info(f"성공률: {(passed_tests / total_tests * 100):.1f}%")

            if passed_tests == total_tests:
                info("모든 테스트가 통과했습니다!")
            else:
                info(f"{total_tests - passed_tests}개의 테스트가 실패했습니다.")

        except Exception as e:
            from util.logger import handle_error
            handle_error(e, "SQL 파서 테스트 실행 중 오류 발생")

    def _run_single_test(self, test_case: Dict) -> bool:
        """단일 테스트 케이스 실행"""
        try:
            sql_content = test_case['sql']
            expected_tables = test_case['expected_tables']
            legacy_result = test_case.get('legacy_result', set())

            # SQL 파서 실행
            sql_result = self.sql_parser.extract_table_names(sql_content)

            # 결과 출력
            info(f"예상 결과: {expected_tables}")
            info(f"기존 파서: {legacy_result}")
            info(f"SQL 파서: {sql_result}")

            # 정확도 계산
            if expected_tables:
                # 정확히 매칭되는 테이블 수
                correct_matches = len(sql_result.intersection(expected_tables))
                # 전체 예상 테이블 수
                total_expected = len(expected_tables)
                # 잘못 추출된 테이블 수 (false positive)
                false_positives = len(sql_result - expected_tables)
                # 놓친 테이블 수 (false negative)
                false_negatives = len(expected_tables - sql_result)

                accuracy = (correct_matches / total_expected * 100) if total_expected > 0 else 0

                info(f"정확도: {accuracy:.1f}% ({correct_matches}/{total_expected})")

                if false_positives > 0:
                    info(f"잘못 추출된 테이블: {sql_result - expected_tables}")

                if false_negatives > 0:
                    info(f"놓친 테이블: {expected_tables - sql_result}")

                # 기존 파서와 비교
                if legacy_result:
                    legacy_correct = len(set(table.split()[0] for table in legacy_result if table.split()).intersection(expected_tables))
                    legacy_accuracy = (legacy_correct / total_expected * 100) if total_expected > 0 else 0
                    improvement = accuracy - legacy_accuracy

                    info(f"기존 파서 정확도: {legacy_accuracy:.1f}%")
                    info(f"개선도: {improvement:+.1f}%p")

                # 성공 기준: 80% 이상 정확도
                success = accuracy >= 80.0

                if success:
                    info("O 테스트 통과")
                else:
                    info("X 테스트 실패 (정확도 80% 미만)")

                return success
            else:
                info("! 예상 결과가 없어 통과 여부를 판단할 수 없습니다")
                return True

        except Exception as e:
            info(f"X 테스트 실행 중 오류: {str(e)}")
            return False

    def test_specific_case(self, case_name: str) -> None:
        """특정 테스트 케이스만 실행"""
        try:
            for test_case in self.test_cases:
                if test_case['name'] == case_name:
                    info(f"=== 특정 테스트 실행: {case_name} ===")
                    self._run_single_test(test_case)
                    return

            info(f"테스트 케이스를 찾을 수 없습니다: {case_name}")
            info("사용 가능한 테스트 케이스:")
            for test_case in self.test_cases:
                info(f"  - {test_case['name']}")

        except Exception as e:
            from util.logger import handle_error
            handle_error(e, f"특정 테스트 케이스 실행 중 오류: {case_name}")

    def test_custom_sql(self, sql_content: str, expected_tables: Set[str] = None) -> None:
        """사용자 정의 SQL 테스트"""
        try:
            info("=== 사용자 정의 SQL 테스트 ===")
            info(f"SQL: {sql_content}")

            sql_result = self.sql_parser.extract_table_names(sql_content)
            info(f"추출된 테이블: {sql_result}")

            if expected_tables:
                correct_matches = len(sql_result.intersection(expected_tables))
                total_expected = len(expected_tables)
                accuracy = (correct_matches / total_expected * 100) if total_expected > 0 else 0

                info(f"예상 테이블: {expected_tables}")
                info(f"정확도: {accuracy:.1f}% ({correct_matches}/{total_expected})")

                if sql_result - expected_tables:
                    info(f"추가로 추출된 테이블: {sql_result - expected_tables}")

                if expected_tables - sql_result:
                    info(f"놓친 테이블: {expected_tables - sql_result}")

        except Exception as e:
            from util.logger import handle_error
            handle_error(e, "사용자 정의 SQL 테스트 중 오류")


def main():
    """메인 함수"""
    try:
        tester = SqlParserTestCase()

        if len(sys.argv) > 1:
            command = sys.argv[1]

            if command == '--all':
                # 모든 테스트 실행
                tester.run_all_tests()

            elif command == '--case' and len(sys.argv) > 2:
                # 특정 테스트 케이스 실행
                case_name = sys.argv[2]
                tester.test_specific_case(case_name)

            elif command == '--sql' and len(sys.argv) > 2:
                # 사용자 정의 SQL 테스트
                sql_content = sys.argv[2]
                expected = set(sys.argv[3:]) if len(sys.argv) > 3 else None
                tester.test_custom_sql(sql_content, expected)

            elif command == '--help':
                print("사용법:")
                print("  python test_enhanced_sql_parser.py --all                    # 모든 테스트 실행")
                print("  python test_enhanced_sql_parser.py --case <케이스명>        # 특정 테스트 실행")
                print("  python test_enhanced_sql_parser.py --sql <SQL> [테이블...]  # 사용자 정의 SQL 테스트")
                print("  python test_enhanced_sql_parser.py --help                   # 도움말")

            else:
                print("알 수 없는 명령어입니다. --help를 참조하세요.")

        else:
            # 기본: 모든 테스트 실행
            tester.run_all_tests()

    except KeyboardInterrupt:
        info("사용자에 의해 중단되었습니다.")
    except Exception as e:
        from util.logger import handle_error
        handle_error(e, "SQL 파서 테스트 메인 실행 중 오류")


if __name__ == '__main__':
    main()