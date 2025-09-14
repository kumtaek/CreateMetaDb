# A_20250914_170000_xml_parser_recursion_fallback.md

## 문제점 분석

`parser/xml_parser.py`의 `XmlParser` 클래스에서 DOM 기반 파싱 중 `RecursionError`가 발생했을 때의 처리 흐름이 비효율적으로 구현되어 있습니다.

- **현재 구조**: `_parse_with_dom` 메소드가 내부적으로 `RecursionError`를 잡아서 `has_error='Y'`가 포함된 딕셔너리를 반환합니다. 이 때문에 상위 메소드인 `extract_sql_queries_and_analyze_relationships`에 있는 전용 `except RecursionError` 블록이 실행되지 않고, 일반적인 DOM 파싱 실패로 간주되어 SAX 파서로 넘어갑니다.
- **요구사항**: `RecursionError` 발생 시, 이를 명시적으로 처리하고 SAX 파서로 fallback하는 흐름을 원하셨습니다. `MybatisParser`에는 이미 재귀 깊이를 10으로 제한하는 로직이 있으므로, 이 로직을 그대로 활용하는 것이 효율적입니다.

## 해결 방안

`_parse_with_dom` 메소드에서 `RecursionError`를 직접 처리하지 않고, 예외를 상위 호출자인 `extract_sql_queries_and_analyze_relationships` 메소드로 보내어 한 곳에서 일관되게 처리하도록 수정합니다.

이렇게 하면 `extract_sql_queries_and_analyze_relationships`에 이미 구현된 로직에 따라 다음과 같이 정상적으로 처리됩니다.

1.  DOM 파싱 중 `RecursionError` 발생
2.  `extract_sql_queries_and_analyze_relationships`의 `except RecursionError` 블록에서 예외를 잡음
3.  "Recursion depth exceeded... SAX 파서로 Fallback" info 로그 출력
4.  SAX 파서 실행
5.  SAX 파서마저 실패하면, `has_error='Y'`와 에러 메시지를 기록하고 다음 파일 처리를 계속 진행

## 수정 대상 파일 및 내용

### 1. 파일 경로

- `parser/xml_parser.py`

### 2. 수정 코드

`XmlParser` 클래스의 `_parse_with_dom` 메소드에서 `except RecursionError` 블록을 삭제합니다.

#### AS-IS (수정 전)

```python
# parser/xml_parser.py

    def _parse_with_dom(self, xml_file: str) -> Optional[Dict[str, Any]]:
        """
        (신규) DOM 기반으로 MyBatis XML을 파싱하고 SQL을 재구성합니다.
        """
        try:
            # XML 파일을 DOM으로 파싱
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # ... (중략) ...

            return {
                'sql_queries': sql_queries,
                'join_relationships': join_relationships,
                'file_path': xml_file
            }

        except RecursionError as e:
            # 재귀 depth 초과시 에러로 처리하되 계속 진행
            error_message = f"Recursion depth exceeded in DOM parsing: {str(e)}"
            warning(f"{error_message} - {xml_file}")
            return {'has_error': 'Y', 'error_message': error_message}
        except Exception as e:
            # 파싱 오류로 처리 - has_error='Y'로 저장하고 계속 진행
            error_message = f"DOM 파싱 중 예외 발생: {str(e)}"
            warning(f"{error_message} - {xml_file}")
            return {'has_error': 'Y', 'error_message': error_message}
```

#### TO-BE (수정 후)

```python
# parser/xml_parser.py

    def _parse_with_dom(self, xml_file: str) -> Optional[Dict[str, Any]]:
        """
        (신규) DOM 기반으로 MyBatis XML을 파싱하고 SQL을 재구성합니다.
        """
        try:
            # XML 파일을 DOM으로 파싱
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # ... (중략) ...

            return {
                'sql_queries': sql_queries,
                'join_relationships': join_relationships,
                'file_path': xml_file
            }

        # except RecursionError as e:  <-- 이 부분을 삭제합니다.
        #     # 재귀 depth 초과시 에러로 처리하되 계속 진행
        #     error_message = f"Recursion depth exceeded in DOM parsing: {str(e)}"
        #     warning(f"{error_message} - {xml_file}")
        #     return {'has_error': 'Y', 'error_message': error_message}
        except Exception as e:
            # 파싱 오류로 처리 - has_error='Y'로 저장하고 계속 진행
            # RecursionError가 아닌 다른 모든 예외는 여기서 처리합니다.
            error_message = f"DOM 파싱 중 예외 발생: {str(e)}"
            warning(f"{error_message} - {xml_file}")
            return {'has_error': 'Y', 'error_message': error_message}
```
