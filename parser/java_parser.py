"""
Java 파서 - 클래스와 메서드 추출
목표: Java 파일에서 클래스와 메서드를 추출하여 components 테이블에 등록
"""

import re
import os
from typing import List, Dict, Any, Optional
from util import warning, debug, handle_error


class JavaParser:
    """Java 파일 파서 - 클래스와 메서드 추출"""
    
    def __init__(self):
        # 클래스 및 인터페이스 추출 패턴
        self.class_pattern = re.compile(
            r'(?:public|protected|private)?\s*(?:static\s+)?(?:final\s+)?(?:abstract\s+)?(?:class|interface)\s+(\w+)',
            re.MULTILINE | re.IGNORECASE
        )
        
        # 메서드 추출 패턴 (클래스 메서드 - 중괄호가 있는 메서드)
        self.class_method_pattern = re.compile(
            r'(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?(?:<[^>]+>\s+)?(?:[\w<>[\]]+\s+)*(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{',
            re.MULTILINE | re.IGNORECASE
        )
        
        # 인터페이스 메서드 추출 패턴 (중괄호가 없는 메서드)
        self.interface_method_pattern = re.compile(
            r'(?:public|protected|private)?\s*(?:static\s+)?(?:final\s+)?(?:[\w<>[\]]+\s+)*(\w+)\s*\([^)]*\)\s*;',
            re.MULTILINE | re.IGNORECASE
        )

    def parse_java_file(self, file_path: str) -> Dict[str, Any]:
        """
        Java 파일 파싱 - 클래스와 메서드 추출

        Returns:
            {
                'file_path': str,
                'classes': [{'name': 'ClassName', 'line': 10, 'type': 'class'}],
                'methods': [{'name': 'methodName', 'class': 'ClassName', 'line': 20, 'type': 'class_method'}]
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
            handle_error(e, f"Java 파일 파싱 실패: {file_path}")
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
        except Exception as e:
            handle_error(e, "주석 제거 실패")
            return content

    def _extract_classes(self, content: str) -> List[Dict[str, Any]]:
        """클래스 추출"""
        classes = []
        try:
            for match in self.class_pattern.finditer(content):
                class_name = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                
                # 클래스 타입 결정
                class_type = 'interface' if 'interface' in match.group(0).lower() else 'class'
                
                classes.append({
                    'name': class_name,
                    'line': line_number,
                    'type': class_type
                })

        except Exception as e:
            handle_error(e, "클래스 추출 실패")
            
        return classes

    def _extract_methods(self, content: str, classes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """메서드 추출 (클래스 메서드와 인터페이스 메서드 모두)"""
        methods = []
        try:
            # 1. 클래스 메서드 추출 (중괄호가 있는 메서드)
            for match in self.class_method_pattern.finditer(content):
                method_name = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                
                # 현재 메서드가 속한 클래스 찾기
                current_class = self._find_current_class(classes, line_number)
                
                if current_class:
                    methods.append({
                        'name': method_name,
                        'class': current_class,
                        'line': line_number,
                        'type': 'class_method'
                    })
            
            # 2. 인터페이스 메서드 추출 (중괄호가 없는 메서드)
            for match in self.interface_method_pattern.finditer(content):
                method_name = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                
                # 현재 메서드가 속한 클래스 찾기
                current_class = self._find_current_class(classes, line_number)
                
                if current_class:
                    methods.append({
                        'name': method_name,
                        'class': current_class,
                        'line': line_number,
                        'type': 'interface_method'
                    })

        except Exception as e:
            handle_error(e, "메서드 추출 실패")
            
        return methods

    def _find_current_class(self, classes: List[Dict[str, Any]], line_number: int) -> Optional[str]:
        """현재 라인 번호에 해당하는 클래스 찾기"""
        try:
            current_class = None
            for cls in classes:
                if cls['line'] < line_number:
                    current_class = cls['name']
                else:
                    break
            return current_class
        except Exception as e:
            handle_error(e, "현재 클래스 찾기 실패")
            return None