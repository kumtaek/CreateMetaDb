"""
Enhanced MyBatis Parser 테스트 스크립트
- include 태그 지원 테스트
- SQL 조각 캐시 테스트

USER RULES:
- Exception은 handle_error()로 처리
- 공통함수 사용 지향
"""

import os
import sys
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from util import info, warning, error, handle_error
from util.cache_utils import get_sql_fragment_cache
from util.config_utils import ConfigUtils
from util.path_utils import PathUtils
from parser.xml_parser import EnhancedMybatisParser


def test_sql_fragment_cache():
    """SQL 조각 캐시 테스트"""
    try:
        info("=== SQL 조각 캐시 테스트 시작 ===")

        # 설정 로드
        path_utils = PathUtils()
        target_config_path = path_utils.get_config_path('target_source_config.yaml')
        config_utils = ConfigUtils()
        target_config = config_utils.load_yaml_config(target_config_path)

        if not target_config:
            warning("설정 파일 로드 실패, 기본 설정 사용")
            target_config = {
                'file_type_settings': {
                    'xml': {
                        'include_patterns': ["**/*.xml"],
                        'exclude_patterns': []
                    }
                }
            }

        # 캐시 초기화
        sql_cache = get_sql_fragment_cache()
        sql_cache.load_all_fragments('sampleSrc', target_config)

        info(f"로드된 SQL 조각 수: {len(sql_cache.fragments)}")

        # 조각 확인
        for fragment_id, fragment_node in sql_cache.fragments.items():
            info(f"SQL 조각: {fragment_id}")

        info("=== SQL 조각 캐시 테스트 완료 ===")
        return True

    except Exception as e:
        error(f"SQL 조각 캐시 테스트 실패: {e}")
        return False


def test_enhanced_parser():
    """Enhanced 파서 테스트"""
    try:
        info("=== Enhanced 파서 테스트 시작 ===")

        # sampleSrc 프로젝트에서 XML 파일 찾기
        path_utils = PathUtils()
        sample_src_path = path_utils.get_project_source_path('sampleSrc')

        xml_files = []
        for root, dirs, files in os.walk(sample_src_path):
            for file in files:
                if file.endswith('.xml'):
                    xml_files.append(os.path.join(root, file))

        info(f"찾은 XML 파일 수: {len(xml_files)}")

        # Enhanced 파서 생성
        enhanced_parser = EnhancedMybatisParser()

        # 각 XML 파일 분석
        total_sqls = 0
        for xml_file in xml_files[:5]:  # 처음 5개만 테스트
            try:
                info(f"분석 중: {xml_file}")

                tree = ET.parse(xml_file)
                root = tree.getroot()

                if root.tag == 'mapper':
                    reconstructed_sqls = enhanced_parser.parse_sql_mapper(root)
                    info(f"추출된 SQL 수: {len(reconstructed_sqls)}")

                    for sql_info in reconstructed_sqls:
                        info(f"  - SQL ID: {sql_info['sql_id']}")
                        info(f"  - 태그: {sql_info['tag_name']}")
                        info(f"  - SQL 길이: {len(sql_info['sql_content'])} 문자")

                    total_sqls += len(reconstructed_sqls)

            except Exception as e:
                warning(f"파일 분석 실패: {xml_file}, 사유: {e}")

        info(f"총 추출된 SQL 수: {total_sqls}")
        info("=== Enhanced 파서 테스트 완료 ===")
        return True

    except Exception as e:
        error(f"Enhanced 파서 테스트 실패: {e}")
        return False


def create_test_xml():
    """테스트용 XML 생성"""
    try:
        info("=== 테스트 XML 생성 ===")

        test_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN" "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="test.TestMapper">

    <!-- SQL 조각 정의 -->
    <sql id="baseColumns">
        user_id, username, email, created_date
    </sql>

    <sql id="userJoinClause">
        LEFT JOIN user_profiles up ON u.user_id = up.user_id
        LEFT JOIN user_settings us ON u.user_id = us.user_id
    </sql>

    <!-- include 태그 사용 쿼리 -->
    <select id="getUserWithDetails">
        SELECT
            <include refid="baseColumns"/>,
            up.profile_data,
            us.settings_data
        FROM users u
        <include refid="userJoinClause"/>
        WHERE u.user_id = #{userId}
    </select>

    <!-- 동적 SQL -->
    <select id="searchUsers">
        SELECT <include refid="baseColumns"/>
        FROM users u
        <if test="includeProfiles != null">
            LEFT JOIN user_profiles up ON u.user_id = up.user_id
        </if>
        WHERE 1=1
        <if test="username != null">
            AND u.username LIKE #{username}
        </if>
    </select>

</mapper>'''

        # 테스트 XML 파일 저장
        test_xml_path = os.path.join('test_enhanced_mapper.xml')
        with open(test_xml_path, 'w', encoding='utf-8') as f:
            f.write(test_xml_content)

        info(f"테스트 XML 생성: {test_xml_path}")
        return test_xml_path

    except Exception as e:
        error(f"테스트 XML 생성 실패: {e}")
        return None


def test_include_resolution():
    """include 태그 해석 테스트"""
    try:
        info("=== include 태그 해석 테스트 시작 ===")

        # 테스트 XML 생성
        test_xml_path = create_test_xml()
        if not test_xml_path:
            return False

        # Enhanced 파서로 분석
        enhanced_parser = EnhancedMybatisParser()

        tree = ET.parse(test_xml_path)
        root = tree.getroot()

        reconstructed_sqls = enhanced_parser.parse_sql_mapper(root, enable_dynamic=False)

        info(f"추출된 SQL 수 (include만): {len(reconstructed_sqls)}")

        for sql_info in reconstructed_sqls:
            info(f"SQL ID: {sql_info['sql_id']}")
            info(f"SQL 내용:")
            print(sql_info['sql_content'])
            print("-" * 50)

        # 테스트 파일 정리
        os.remove(test_xml_path)

        info("=== include 태그 해석 테스트 완료 ===")
        return True

    except Exception as e:
        error(f"include 태그 해석 테스트 실패: {e}")
        return False


def test_dynamic_sql_analysis():
    """동적 SQL 분석 테스트"""
    try:
        info("=== 동적 SQL 분석 테스트 시작 ===")

        # 테스트 XML 생성
        test_xml_path = create_test_xml()
        if not test_xml_path:
            return False

        # Enhanced 파서로 동적 분석
        enhanced_parser = EnhancedMybatisParser()

        tree = ET.parse(test_xml_path)
        root = tree.getroot()

        reconstructed_sqls = enhanced_parser.parse_sql_mapper(root, enable_dynamic=True)

        info(f"추출된 SQL 수 (동적 분석): {len(reconstructed_sqls)}")

        for sql_info in reconstructed_sqls:
            info(f"SQL ID: {sql_info['sql_id']}")
            if sql_info.get('is_dynamic_path'):
                info(f"동적 경로: {sql_info['path_index']}/{sql_info['total_paths']}")
            info(f"SQL 내용:")
            print(sql_info['sql_content'])
            print("-" * 50)

        # 동적 경로가 생성되었는지 확인
        dynamic_count = sum(1 for sql in reconstructed_sqls if sql.get('is_dynamic_path', False))
        info(f"동적 경로로 분석된 SQL 수: {dynamic_count}")

        # 테스트 파일 정리
        os.remove(test_xml_path)

        info("=== 동적 SQL 분석 테스트 완료 ===")
        return True

    except Exception as e:
        error(f"동적 SQL 분석 테스트 실패: {e}")
        return False


def main():
    """메인 함수"""
    try:
        info("Enhanced MyBatis Parser 테스트 시작")

        # 테스트 실행
        tests = [
            ("SQL 조각 캐시", test_sql_fragment_cache),
            ("Enhanced 파서", test_enhanced_parser),
            ("include 태그 해석", test_include_resolution),
            ("동적 SQL 분석", test_dynamic_sql_analysis)
        ]

        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
                info(f"{test_name} 테스트: {'성공' if result else '실패'}")
            except Exception as e:
                error(f"{test_name} 테스트 실행 중 오류: {e}")
                results.append((test_name, False))

        # 결과 요약
        info("\n=== 테스트 결과 요약 ===")
        success_count = sum(1 for _, result in results if result)
        total_count = len(results)

        for test_name, result in results:
            status = "성공" if result else "실패"
            info(f"{status}: {test_name}")

        info(f"전체 테스트: {success_count}/{total_count} 성공")

        if success_count == total_count:
            info("모든 테스트가 성공했습니다!")
        else:
            warning(f"{total_count - success_count}개 테스트가 실패했습니다.")

    except Exception as e:
        handle_error(e, "테스트 실행 실패")


if __name__ == "__main__":
    main()