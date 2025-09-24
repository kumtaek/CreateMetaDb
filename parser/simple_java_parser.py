"""
심플 Java 파서 - public/protected 클래스와 메서드만 추출
목표: files → classes → methods 순서로 components 테이블에 등록
"""

import re
import os
from typing import List, Dict, Set, Optional, Tuple, Any
from util import debug, info, warning, handle_error

class SimpleJavaParser:
    """심플한 Java 파서 - public/protected만 추출"""

    def __init__(self):
        """Java 파서 초기화"""
        # 클래스 패턴 - public/protected만
        self.class_pattern = re.compile(
            r'(?:^|\n)\s*(?:public|protected)\s+(?:static\s+)?(?:abstract\s+)?class\s+(\w+)',
            re.MULTILINE | re.IGNORECASE
        )

        # 메서드 패턴 - public/protected만
        self.method_pattern = re.compile(
            r'(?:^|\n)\s*(?:public|protected)\s+(?:static\s+)?(?:final\s+)?(?:abstract\s+)?'
            r'(?:\w+(?:<[^>]*>)?\s+)*(\w+)\s*\([^)]*\)\s*(?:throws\s+[^{]*)?{',
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
        """public/protected 클래스 추출"""
        classes = []
        try:
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                match = self.class_pattern.search(line)
                if match:
                    class_name = match.group(1)
                    classes.append({
                        'name': class_name,
                        'line': i
                    })
                    debug(f"클래스 발견: {class_name} at line {i}")

        except Exception as e:
            warning(f"클래스 추출 실패: {e}")

        return classes

    def _extract_methods(self, content: str, classes: List[Dict]) -> List[Dict[str, Any]]:
        """public/protected 메서드 추출"""
        methods = []
        try:
            lines = content.split('\n')
            current_class = None

            for i, line in enumerate(lines, 1):
                # 현재 클래스 찾기
                for cls in classes:
                    if cls['line'] == i:
                        current_class = cls['name']
                        break

                # 메서드 찾기
                match = self.method_pattern.search(line)
                if match and current_class:
                    method_name = match.group(1)

                    # 생성자는 제외 (클래스명과 동일한 메서드)
                    if method_name != current_class:
                        methods.append({
                            'name': method_name,
                            'class': current_class,
                            'line': i
                        })
                        debug(f"메서드 발견: {current_class}.{method_name} at line {i}")

        except Exception as e:
            warning(f"메서드 추출 실패: {e}")

        return methods

    def get_component_data(self, parse_result: Dict, file_id: int, project_id: int) -> List[Dict]:
        """
        파싱 결과를 components 테이블 형태로 변환

        Returns:
            components 테이블에 등록할 데이터 리스트
        """
        components = []

        try:
            # 클래스 컴포넌트 생성
            for cls in parse_result['classes']:
                components.append({
                    'project_id': project_id,
                    'file_id': file_id,
                    'component_name': cls['name'],
                    'component_type': 'CLASS',
                    'layer_type': 'UNKNOWN',
                    'line_number': cls['line'],
                    'has_error': 'N',
                    'error_message': None
                })

            # 메서드 컴포넌트 생성
            for method in parse_result['methods']:
                components.append({
                    'project_id': project_id,
                    'file_id': file_id,
                    'component_name': f"{method['class']}.{method['name']}",
                    'component_type': 'METHOD',
                    'layer_type': 'UNKNOWN',
                    'line_number': method['line'],
                    'has_error': 'N',
                    'error_message': None
                })

        except Exception as e:
            handle_error(e, f"컴포넌트 데이터 생성 실패")

        return components


def parse_java_file(file_path: str) -> Dict[str, Any]:
    """편의 함수 - Java 파일 파싱"""
    parser = SimpleJavaParser()
    return parser.parse_java_file(file_path)


def get_java_components(file_path: str, file_id: int, project_id: int) -> List[Dict]:
    """편의 함수 - Java 파일에서 컴포넌트 데이터 추출"""
    parser = SimpleJavaParser()
    parse_result = parser.parse_java_file(file_path)
    return parser.get_component_data(parse_result, file_id, project_id)