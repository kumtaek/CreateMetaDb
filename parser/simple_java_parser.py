"""
심플한 Java 파서 - public/protected 메서드만 추출
"""

import re
from typing import List, Dict, Any
from util import FileUtils, warning, debug


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

        # @Entity 클래스의 @Table(name=...) 추출용 패턴
        # 주의: @Table(name="...", indexes={...}) 형태에서 @Index의 name이 아닌
        #       @Table의 직접적인 name 속성만 매칭해야 함
        # 패턴: @Table 직후 괄호 시작 후 첫 번째 name= 속성만 매칭
        self.entity_table_pattern = re.compile(
            r'@Table\s*\(\s*name\s*=\s*["\']([^"\']+)["\']',
            re.IGNORECASE
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
            content = FileUtils.read_file(file_path)
            if content is None:
                return {
                    'file_path': file_path,
                    'classes': [],
                    'methods': [],
                    'entity_table_mapping': {}
                }

            # 원본 보관 (어노테이션 파싱용)
            original_content = content

            # 주석 제거 (// 및 /* */ 형태)
            content = self._remove_comments(content)

            # 클래스 추출
            classes = self._extract_classes(content)

            # 메서드 추출
            methods = self._extract_methods(content, classes)

            # Entity-Table 매핑 추출 (원본에서 어노테이션 파싱)
            entity_table_mapping = self._extract_entity_table_mapping(original_content, classes)

            return {
                'file_path': file_path,
                'classes': classes,
                'methods': methods,
                'entity_table_mapping': entity_table_mapping
            }

        except Exception as e:
            warning(f"Java 파일 파싱 실패: {file_path} - {e}")
            return {
                'file_path': file_path,
                'classes': [],
                'methods': [],
                'entity_table_mapping': {}
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

    def _extract_entity_table_mapping(self, content: str, classes: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        JPA @Entity 클래스에서 @Table(name=...) 매핑 추출

        Args:
            content: Java 소스 파일 원본 내용 (주석 포함)
            classes: 추출된 클래스 목록

        Returns:
            {엔티티클래스명: 테이블명} 형태의 딕셔너리
            예: {'Order': 'ORDERS', 'User': 'USERS'}
        """
        mapping = {}
        try:
            for cls in classes:
                class_name = cls['name']
                class_line = cls['line']

                # 클래스 선언 이전 영역에서 @Entity와 @Table 찾기
                # 클래스 선언 위치까지의 내용에서 어노테이션 검색
                lines = content.split('\n')
                search_start = max(0, class_line - 20)  # 클래스 선언 20줄 전부터 검색
                search_end = class_line
                search_area = '\n'.join(lines[search_start:search_end])

                # @Entity 어노테이션이 있는지 확인
                if '@Entity' not in search_area:
                    continue

                # @Table(name="...") 추출
                table_match = self.entity_table_pattern.search(search_area)
                if table_match:
                    table_name = table_match.group(1).upper()
                    mapping[class_name] = table_name
                    debug(f"Entity-Table 매핑 발견: {class_name} -> {table_name}")
                else:
                    # @Table이 없으면 클래스명을 대문자로 사용 (JPA 기본 규칙)
                    mapping[class_name] = class_name.upper()
                    debug(f"Entity-Table 매핑 (기본): {class_name} -> {class_name.upper()}")

        except Exception as e:
            warning(f"Entity-Table 매핑 추출 실패: {e}")

        return mapping
