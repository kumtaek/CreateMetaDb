#!/usr/bin/env python3
"""
정규식 매치 디버깅 스크립트
"""

import re

def debug_regex_pattern():
    """정규식 패턴 디버깅"""

    # Spring Entry Analyzer에서 사용하는 정규식
    improved_pattern = r'(@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*(?:\([^)]*\))?|@RequestMapping\s*\([^)]*(?:method\s*=|,\s*method\s*=)[^)]*\))\s*(?:\n\s*@\w+\s*)*\n\s*(?:public|private|protected)\s+(?:[\w\<\>\[\],\s\?]+\s+)(\w+)\s*\('
    improved_regex = re.compile(improved_pattern, re.DOTALL)

    # 실제 SyntaxErrorController 코드 부분
    test_content = '''
    // 정상적인 메서드
    @RequestMapping(value = "/test1", method = RequestMethod.GET)
    @ResponseBody
    public String test1() {
        return "Hello World";
    }

    // 정상적인 메서드
    @RequestMapping(value = "/test2", method = RequestMethod.GET)
    @ResponseBody
    public String test2() {
        if (true) {
            return "Valid syntax";
        }
        return "OK";
    }

    // 정상적인 메서드
    @RequestMapping(value = "/users", method = RequestMethod.GET)
    @ResponseBody
    public List<User> getAllUsers() {
        return userService.getAllUsers();
    }
    '''

    matches = improved_regex.findall(test_content)

    print(f"정규식 매치 결과: {len(matches)}개")
    print("=" * 50)

    for i, match in enumerate(matches, 1):
        if isinstance(match, tuple) and len(match) >= 2:
            annotation_text = match[0]
            method_name = match[1]
            print(f"매치 {i}:")
            print(f"  어노테이션: {annotation_text}")
            print(f"  메서드명: {method_name}")
            print("---")

if __name__ == "__main__":
    debug_regex_pattern()