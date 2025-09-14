import os
import sys
sys.path.append('.')

from parser.jsp_parser import JspParser
import re

def debug_jsp_method_extraction():
    print("=== JSP 메서드 호출 추출 디버깅 (1건 샘플) ===")
    
    try:
        # JSP 파서 초기화
        jsp_parser = JspParser()
        print("JSP 파서 초기화 성공")
        
        # JSP 파일 수집
        jsp_files = jsp_parser.get_filtered_jsp_files('projects/sampleSrc')
        if not jsp_files:
            print("JSP 파일이 없습니다.")
            return
        
        # 정답지5 기준: list.jsp에 JavaScript 함수 있음
        test_file = "projects/sampleSrc/src/main/webapp/user/list.jsp"
        print(f"분석 대상: {test_file}")
        
        # JSP 파일 내용 읽기
        with open(test_file, 'r', encoding='utf-8') as f:
            jsp_content = f.read()
        
        print(f"파일 크기: {len(jsp_content)} 문자")
        
        # 1. JavaScript 함수 추출 테스트 (정답지5 기준: JSP_SCRIPTLET = JavaScript 함수명)
        print("\n=== 1. JavaScript 함수 추출 테스트 ===")
        scriptlet_patterns = jsp_parser.config.get('javascript_function_patterns', [])
        print(f"JavaScript 함수 패턴: {scriptlet_patterns}")
        
        for i, pattern in enumerate(scriptlet_patterns):
            print(f"\n패턴 {i+1}: {pattern}")
            matches = re.finditer(pattern, jsp_content, re.IGNORECASE | re.DOTALL)
            match_count = 0
            for match in matches:
                match_count += 1
                content = match.group(1) if match.groups() else match.group(0)
                print(f"  JavaScript 함수 {match_count}: {content[:100]}...")
                
                # 2. 스크립틀릿 내 메서드 호출 추출 테스트
                print(f"    메서드 호출 추출 테스트:")
                method_patterns = jsp_parser.config.get('java_method_call_patterns', [])
                for j, method_pattern in enumerate(method_patterns):
                    method_matches = re.finditer(method_pattern, content)
                    method_count = 0
                    for method_match in method_matches:
                        method_count += 1
                        print(f"      패턴 {j+1} 매치 {method_count}: {method_match.groups()}")
                    if method_count == 0:
                        print(f"      패턴 {j+1}: 매치 없음")
            
            if match_count == 0:
                print("  스크립틀릿 매치 없음")
        
        # 3. 표현식 추출 테스트
        print("\n=== 2. 표현식 추출 테스트 ===")
        expression_patterns = jsp_parser.config.get('jsp_scripting_patterns', [])
        
        for i, pattern in enumerate(expression_patterns):
            if '=' in pattern:  # 표현식 패턴만
                print(f"\n패턴 {i+1}: {pattern}")
                matches = re.finditer(pattern, jsp_content, re.IGNORECASE | re.DOTALL)
                match_count = 0
                for match in matches:
                    match_count += 1
                    content = match.group(1) if match.groups() else match.group(0)
                    print(f"  표현식 {match_count}: {content}")
                    
                    # 4. 표현식 내 메서드 호출 추출 테스트
                    print(f"    메서드 호출 추출 테스트:")
                    method_patterns = jsp_parser.config.get('java_method_call_patterns', [])
                    for j, method_pattern in enumerate(method_patterns):
                        method_matches = re.finditer(method_pattern, content)
                        method_count = 0
                        for method_match in method_matches:
                            method_count += 1
                            print(f"      패턴 {j+1} 매치 {method_count}: {method_match.groups()}")
                        if method_count == 0:
                            print(f"      패턴 {j+1}: 매치 없음")
                
                if match_count == 0:
                    print("  표현식 매치 없음")
        
        # 5. JSP 파서 실제 호출 테스트
        print("\n=== 3. JSP 파서 실제 호출 테스트 ===")
        result = jsp_parser.parse_jsp_file(test_file)
        print(f"파싱 결과:")
        print(f"  has_error: {result.get('has_error')}")
        print(f"  error_message: {result.get('error_message')}")
        
        java_relationships = result.get('java_method_relationships', [])
        print(f"  Java 메서드 관계: {len(java_relationships)}개")
        for rel in java_relationships:
            print(f"    - {rel}")
        
    except Exception as e:
        print(f"디버깅 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_jsp_method_extraction()
