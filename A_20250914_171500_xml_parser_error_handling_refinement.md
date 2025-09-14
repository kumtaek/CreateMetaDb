# A_20250914_171500_xml_parser_error_handling_refinement.md

## 문제점 재분석

이전 수정(`A_20250914_170000`)은 `RecursionError`만 상위로 전달하도록 했으나, 지적해주신 대로 DOM 파싱에서 발생하는 **모든 예외**는 최종 오류가 아닌 SAX 파서로의 전환 트리거가 되어야 합니다.

- **AS-IS**: `_parse_with_dom` 메소드에서 `RecursionError`를 제외한 다른 `Exception`이 발생하면, `{'has_error': 'Y', 'error_message': ...}`를 반환했습니다. 이 때문에 DOM 파싱이 실패했다는 사실만으로 최종 에러처럼 처리될 여지가 있었습니다.
- **TO-BE**: DOM 파서가 어떤 이유로든 실패하면(능력 부족), 최종 에러 처리를 하지 않고 그저 `None`을 반환하여 호출자가 다음 파싱 방법(SAX)을 시도하도록 해야 합니다. 최종 에러(`has_error='Y'`)는 모든 파싱 방법이 실패했을 때만 설정되어야 합니다.

## 해결 방안

`parser/xml_parser.py`의 `_parse_with_dom` 메소드 내 `except Exception` 블록이 `has_error='Y'`를 포함한 딕셔너리 대신 `None`을 반환하도록 수정합니다.

## 수정 대상 파일 및 내용

### 1. 파일 경로

- `parser/xml_parser.py`

### 2. 수정 코드

`XmlParser` 클래스의 `_parse_with_dom` 메소드에서 `except Exception` 블록의 반환 값을 수정합니다.

#### AS-IS (수정 전)

```python
# parser/xml_parser.py in _parse_with_dom

        except Exception as e:
            # 파싱 오류로 처리 - has_error='Y'로 저장하고 계속 진행
            error_message = f"DOM 파싱 중 예외 발생: {str(e)}"
            warning(f"{error_message} - {xml_file}")
            return {'has_error': 'Y', 'error_message': error_message}
```

#### TO-BE (수정 후)

```python
# parser/xml_parser.py in _parse_with_dom

        except Exception as e:
            # 파싱 오류로 처리 - has_error='Y'로 저장하고 계속 진행
            error_message = f"DOM 파싱 중 예외 발생: {str(e)}"
            warning(f"{error_message} - {xml_file}")
            # None을 반환하여 상위 메소드가 SAX 파서로 fallback 하도록 유도
            return None
```

## 재귀 깊이 설정에 대한 부연 설명

**"재귀 깊이를 늘리는 것이 근본적인 해결책이 아닌데 왜 그런 시도를 하는가?"** 라는 질문에 대한 답변입니다.

말씀하신 대로, 재귀 깊이를 무작정 늘리는 것은 근본적인 해결책이 아닐 수 있으며, 오히려 스택 오버플로우의 위험을 증가시킬 수 있습니다. 그럼에도 불구하고 재귀 깊이 조절을 시도하는 이유는 다음과 같습니다.

1.  **정상적으로 깊은 구조의 XML 대응**: MyBatis의 `<include>`처럼 XML 구조가 합법적으로 매우 깊어지는 경우가 있습니다. 이럴 때 기본 재귀 깊이(보통 1000)가 부족할 수 있어, 제한을 풀어주는 것이 가장 간단한 해결책일 수 있습니다.
2.  **임시방편(Quick Fix)**: 복잡한 재귀 알고리즘을 반복문 기반의 스택 방식으로 바꾸는 것은 공수가 많이 듭니다. 반면, 재귀 깊이를 늘리는 것은 단 한 줄의 코드로 가능하므로, 급한 불을 끄기 위한 임시방편으로 사용되곤 합니다.

하지만 지적하신 대로 이 방법은 다음과 같은 명확한 한계가 있습니다.

-   **무한 재귀**: XML 내부에 순환 참조(`A -> B -> A`)가 있는 경우, 재귀 깊이를 아무리 늘려도 결국 스택 오버플로우로 프로그램이 비정상 종료됩니다.
-   **메모리 문제**: 재귀가 깊어질수록 콜 스택에 많은 메모리를 사용하게 됩니다.

**결론적으로, 현재 우리 프로젝트가 채택한 방식이 더 우수합니다.**

-   `MybatisParser`에서 재귀 깊이를 `10` 정도로 **의도적으로 낮게 설정**합니다.
-   `RecursionError`가 발생하면, 이는 "이 XML은 DOM 파서로 처리하기에 너무 복잡하다"는 신호로 간주합니다.
-   그 후, 재귀 방식이 아닌 스트림 기반의 **SAX 파서로 안전하게 전환(fallback)**합니다.

이것이 바로 복잡성에 대응하는 가장 안정적이고 효율적인 아키텍처입니다. 의문을 가져주신 덕분에 더 견고한 시스템을 설계하고 검토할 수 있게 되었습니다.
