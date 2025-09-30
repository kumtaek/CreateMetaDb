"""
심플한 Java 파서 - public/protected 메서드만 추출
"""

import re
from typing import List, Dict, Any
from util import warning, debug


class SimpleJavaParser:
    """심플한 Java 파서 - public/protected만 추출"""
    
    def __init__(self):
        # 클래스 및 인터페이스 추출 패턴 (어노테이션 무시)
        self.class_pattern = re.compile(
            r'(?:public|protected|private)?\s*(?:static\s+)?(?:final\s+)?(?:abstract\s+)?(?:class|interface)\s+(\w+)',
            re.MULTILINE | re.IGNORECASE
        )
        
        # 메서드 추출 패턴 (public/protected만)
        self.method_pattern = re.compile(
            r'(?:public|protected)\s+(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?(?:<[^>]+>\s+)?(?:[\w<>[\]]+\s+)*(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{',
            re.MULTILINE | re.IGNORECASE
        )

    def parse_java_file(self, file_path: str) -> Dict[str, Any]:
        """
        Java 파일 파싱 - 클래스와 메서드 추출

        Returns:
            {
                'classes': [{'name': 'ClassName', 'line': 10}],
                'methods': [{'name': 'methodName', 'class': 'ClassName', 'line': 20}]
            }
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 주석 제거 (// 및 /* */ 형태)
            content = self._remove_comments(content)

            # 클래스 추출
            classes = self._extract_classes(content)

            # 메서드 추출
            methods = self._extract_methods(content, classes)

            return {
                'file_path': file_path,
                'classes': classes,
                'methods': methods
            }

        except Exception as e:
            warning(f"Java 파일 파싱 실패: {file_path} - {e}")
            return {
                'file_path': file_path,
                'classes': [],
                'methods': []
            }

    def _remove_comments(self, content: str) -> str:
        """주석 제거 (단순하게)"""
        try:
            # 한줄 주석 제거
            content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)

            # 블록 주석 제거
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

            return content
        except:
            return content

    def _extract_classes(self, content: str) -> List[Dict[str, Any]]:
        """클래스 추출"""
        classes = []
        try:
            for match in self.class_pattern.finditer(content):
                class_name = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                
                classes.append({
                    'name': class_name,
                    'line': line_number
                })
                
        except Exception as e:
            warning(f"클래스 추출 실패: {e}")
            
        return classes

    def _extract_methods(self, content: str, classes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """메서드 추출 (public/protected만)"""
        methods = []
        try:
            for match in self.method_pattern.finditer(content):
                method_name = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                
                # 현재 메서드가 속한 클래스 찾기
                current_class = None
                for cls in classes:
                    if cls['line'] < line_number:
                        current_class = cls['name']
                    else:
                        break
                
                if current_class:
                    methods.append({
                        'name': method_name,
                        'class': current_class,
                        'line': line_number
                    })
                    
        except Exception as e:
            warning(f"메서드 추출 실패: {e}")
            
        return methods
