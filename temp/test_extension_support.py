"""
확장자 지원 테스트 스크립트
- .xml, .dbio 등 다양한 MyBatis 파일 확장자 지원 확인
- 설정 파일 기반 확장자 로딩 테스트
"""

import sys
import os

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parser.xml_parser import XmlParser
from util import ConfigUtils, PathUtils, info, error

def test_xml_parser_extensions():
    """XML 파서 확장자 설정 테스트"""
    print("=" * 80)
    print("XML 파서 확장자 설정 테스트")
    print("=" * 80)
    
    try:
        # XML 파서 초기화
        parser = XmlParser()
        
        # 설정에서 확장자 목록 가져오기
        mybatis_extensions = parser.config.get('xml_file_filtering', {}).get('mybatis_file_extensions', [])
        
        print(f"\n✓ XML 파서 초기화 성공")
        print(f"✓ 설정된 MyBatis 파일 확장자: {mybatis_extensions}")
        
        # 기대값 확인
        expected_extensions = ['.xml', '.dbio']
        for ext in expected_extensions:
            if ext in mybatis_extensions:
                print(f"  ✓ {ext} 확장자 지원 확인")
            else:
                print(f"  ✗ {ext} 확장자 미지원 (설정 확인 필요)")
                return False
        
        return True
        
    except Exception as e:
        error(f"XML 파서 테스트 실패: {str(e)}")
        return False


def test_file_utils_extensions():
    """FileUtils 확장자 설정 테스트"""
    print("\n" + "=" * 80)
    print("FileUtils 확장자 설정 테스트")
    print("=" * 80)
    
    try:
        from util import FileUtils
        
        # XML 타입 확장자 확인
        xml_extensions = FileUtils.SUPPORTED_EXTENSIONS.get('xml', [])
        
        print(f"\n✓ FileUtils 로드 성공")
        print(f"✓ XML 타입 확장자: {xml_extensions}")
        
        # 기대값 확인
        expected_extensions = ['.xml', '.dbio']
        for ext in expected_extensions:
            if ext in xml_extensions:
                print(f"  ✓ {ext} 확장자 지원 확인")
            else:
                print(f"  ✗ {ext} 확장자 미지원 (설정 확인 필요)")
                return False
        
        # 파일 타입 감지 테스트
        test_files = [
            'test.xml',
            'test.dbio',
            'UserMapper.xml',
            'UserMapper.dbio'
        ]
        
        print(f"\n파일 타입 감지 테스트:")
        for test_file in test_files:
            file_type = FileUtils.get_file_type(test_file)
            print(f"  {test_file} -> {file_type}")
            if file_type != 'xml':
                print(f"    ✗ 예상: xml, 실제: {file_type}")
                return False
        
        return True
        
    except Exception as e:
        error(f"FileUtils 테스트 실패: {str(e)}")
        return False


def test_config_file():
    """설정 파일 로딩 테스트"""
    print("\n" + "=" * 80)
    print("설정 파일 로딩 테스트")
    print("=" * 80)
    
    try:
        path_utils = PathUtils()
        config_utils = ConfigUtils()
        
        # XML 파서 설정 파일 로드
        xml_config_path = path_utils.get_config_path("parser/xml_parser_config.yaml")
        xml_config = config_utils.load_yaml_config(xml_config_path)
        
        print(f"\n✓ XML 파서 설정 파일 로드 성공: {xml_config_path}")
        
        # mybatis_file_extensions 확인
        mybatis_extensions = xml_config.get('xml_file_filtering', {}).get('mybatis_file_extensions', [])
        print(f"✓ mybatis_file_extensions: {mybatis_extensions}")
        
        if not mybatis_extensions:
            print("  ✗ mybatis_file_extensions 설정이 없습니다")
            return False
        
        # include_patterns 확인
        include_patterns = xml_config.get('xml_file_filtering', {}).get('include_patterns', [])
        print(f"✓ include_patterns: {include_patterns}")
        
        # .dbio 패턴 확인
        dbio_patterns = [p for p in include_patterns if '.dbio' in p]
        if dbio_patterns:
            print(f"  ✓ .dbio 패턴 발견: {dbio_patterns}")
        else:
            print(f"  ✗ .dbio 패턴이 include_patterns에 없습니다")
            return False
        
        # target_source_config.yaml 확인
        target_config_path = path_utils.get_config_path("target_source_config.yaml")
        target_config = config_utils.load_yaml_config(target_config_path)
        
        print(f"\n✓ target_source_config.yaml 로드 성공: {target_config_path}")
        
        # supported_extensions 확인
        supported_extensions = target_config.get('supported_extensions', [])
        print(f"✓ supported_extensions: {supported_extensions}")
        
        if '.dbio' in supported_extensions:
            print(f"  ✓ .dbio 확장자 지원 확인")
        else:
            print(f"  ✗ .dbio 확장자가 supported_extensions에 없습니다")
            return False
        
        return True
        
    except Exception as e:
        error(f"설정 파일 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 실행"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "확장자 지원 테스트 시작" + " " * 36 + "║")
    print("╚" + "=" * 78 + "╝")
    
    results = []
    
    # 테스트 실행
    results.append(("설정 파일 로딩", test_config_file()))
    results.append(("XML 파서 확장자", test_xml_parser_extensions()))
    results.append(("FileUtils 확장자", test_file_utils_extensions()))
    
    # 결과 출력
    print("\n" + "=" * 80)
    print("테스트 결과 요약")
    print("=" * 80)
    
    all_passed = True
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
        if not result:
            all_passed = False
    
    print("=" * 80)
    
    if all_passed:
        print("\n✓ 모든 테스트 통과!")
        print("\n다음 확장자가 정상적으로 지원됩니다:")
        print("  - .xml (기본)")
        print("  - .dbio (운영 환경)")
        return 0
    else:
        print("\n✗ 일부 테스트 실패")
        print("\n설정 파일을 확인하세요:")
        print("  - config/parser/xml_parser_config.yaml")
        print("  - config/target_source_config.yaml")
        print("  - util/file_utils.py")
        return 1


if __name__ == '__main__':
    sys.exit(main())
