# A_20250914_173000_circular_import_resolution.md

## 문제점 분석: 순환 참조 (Circular Import)

프로그램이 `RecursionError`와 함께 비정상 종료되는 이유는 XML 파싱 로직의 문제가 아니라, 파이썬 모듈 간의 **순환 참조(Circular Import)** 때문입니다.

스택 트레이스를 분석한 결과, 오류는 프로그램을 실행하고 모듈을 불러오는 `import` 시점에 발생했습니다. 이는 `xml_parser.py`와 `sax_fallback_parser.py`가 서로를 직접 또는 간접적으로 `import` 하면서 무한 루프에 빠졌기 때문입니다.

-   `xml_parser.py` -> `sax_fallback_parser.py` -> ... -> `xml_parser.py`

이러한 순환 구조 때문에 파이썬의 모듈 로더가 재귀 깊이 한계를 초과하여 프로그램을 강제 종료시킨 것입니다. 따라서 파싱 로직 내에 위치한 `try...except` 블록은 실행될 기회조차 없었습니다.

## 해결 방안: 로컬 임포트 (Local Import)

순환 참조를 해결하는 가장 효과적인 방법 중 하나는 **로컬 임포트**입니다. 모듈을 파일 최상단에서 한 번에 불러오는 대신, 해당 모듈이 실제로 필요한 함수나 메소드 내부에서 `import` 하는 방식입니다.

`xml_parser.py`는 DOM 파싱이 실패하거나 `RecursionError`가 발생했을 때만 `sax_fallback_parser.py`가 필요합니다. 따라서 `extract_sql_queries_and_analyze_relationships` 메소드 내에서 필요할 때만 `import` 하도록 수정하여 순환 참조의 고리를 끊겠습니다.

## 수정 대상 파일 및 내용

### 1. 파일 경로

- `parser/xml_parser.py`

### 2. 수정 코드

#### AS-IS (수정 전)

```python
# parser/xml_parser.py

# ... (다른 import 구문들) ...
from .sax_fallback_parser import MyBatisSaxParser  # <-- 문제의 원인 (파일 상단에서 import)

class XmlParser:
    # ... (클래스 내용) ...

    def extract_sql_queries_and_analyze_relationships(self, xml_file: str) -> Dict[str, Any]:
        """
        XML 파일에서 SQL 쿼리를 추출하고 관계를 분석합니다.
        DOM 기반 파싱을 먼저 시도하고, 실패 시 기존 정규식 기반 파서로 Fallback합니다.
        """
        try:
            # ... (DOM 파싱 시도) ...
            else:
                info(f"DOM 기반 파싱 실패 또는 결과 없음, SAX 파서로 Fallback: {xml_file}")
                # ...

            # 2단계: SAX 파서로 Fallback
            info(f"SAX 파서로 Fallback: {xml_file}")
            sax_parser = MyBatisSaxParser() # <-- 여기서 사용
            sax_result = sax_parser.parse_file(xml_file)
            # ...

        except RecursionError as e:
            # 재귀 depth 초과시 SAX 파서로 Fallback
            info(f"Recursion depth exceeded in DOM parsing, SAX 파서로 Fallback: {xml_file} - {str(e)}")
            
            try:
                # SAX 파서로 Fallback
                info(f"SAX 파서로 Fallback (RecursionError): {xml_file}")
                sax_parser = MyBatisSaxParser() # <-- 여기서도 사용
                sax_result = sax_parser.parse_file(xml_file)
                # ...
```

#### TO-BE (수정 후)

```python
# parser/xml_parser.py

# ... (다른 import 구문들) ...
# from .sax_fallback_parser import MyBatisSaxParser  <-- 이 라인을 삭제합니다.

class XmlParser:
    # ... (클래스 내용) ...

    def extract_sql_queries_and_analyze_relationships(self, xml_file: str) -> Dict[str, Any]:
        """
        XML 파일에서 SQL 쿼리를 추출하고 관계를 분석합니다.
        DOM 기반 파싱을 먼저 시도하고, 실패 시 기존 정규식 기반 파서로 Fallback합니다.
        """
        try:
            # ... (DOM 파싱 시도) ...
            else:
                info(f"DOM 기반 파싱 실패 또는 결과 없음, SAX 파서로 Fallback: {xml_file}")
                # ...

            # 2단계: SAX 파서로 Fallback
            info(f"SAX 파서로 Fallback: {xml_file}")
            from .sax_fallback_parser import MyBatisSaxParser  # <-- 필요한 시점에 여기서 import 합니다.
            sax_parser = MyBatisSaxParser()
            sax_result = sax_parser.parse_file(xml_file)
            # ...

        except RecursionError as e:
            # 재귀 depth 초과시 SAX 파서로 Fallback
            info(f"Recursion depth exceeded in DOM parsing, SAX 파서로 Fallback: {xml_file} - {str(e)}")
            
            try:
                # SAX 파서로 Fallback
                info(f"SAX 파서로 Fallback (RecursionError): {xml_file}")
                from .sax_fallback_parser import MyBatisSaxParser  # <-- 필요한 시점에 여기서도 import 합니다.
                sax_parser = MyBatisSaxParser()
                sax_result = sax_parser.parse_file(xml_file)
                # ...
```
