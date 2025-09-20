# Enhanced Parser 안정성 강화를 위한 동적 폴백(Fallback) 개선 방안

## 1. 문서 정보
- **작성일**: 2025년 9월 19일
- **작성자**: Gemini
- **문서 목적**: `enhanced_parser`의 고급 기능을 기본적으로 활성화하되, 순환 참조와 같은 치명적인 오류 발생 시 시스템 전체의 안정성을 해치지 않고 해당 파일에 한해 동적으로 기본 파서로 대체(Fallback)하는 방안을 제시합니다.

---

## 2. 배경 및 문제 정의

### 2.1. 현황
- `enhanced_parser`는 MyBatis의 동적 SQL 및 `<include>` 태그 분석을 위해 개발되었으나, '조합 폭발' 및 '순환 참조'와 같은 문제로 인해 시스템 안정성에 위협이 됨이 확인되었습니다.
- 이로 인해 현재 `enhanced_parser`는 기본적으로 비활성화되어 있으며, 고급 분석 기능의 이점을 활용하지 못하고 있습니다.

### 2.2. 문제점
- `config.yaml` 파일에 문제 소지가 있는 파일을 수동으로 제외시키는 방식은 또 다른 형태의 하드코딩이며, 새로운 문제가 발생할 때마다 유지보수 비용이 발생합니다.
- 단 하나의 문제 파일 때문에 전체 프로젝트가 `enhanced_parser`의 개선된 기능을 사용하지 못하는 것은 비효율적입니다.

### 2.3. 목표
- `enhanced_parser`를 **기본 분석기로 사용**하여 분석 품질을 극대화합니다.
- 순환 참조와 같은 예측 가능한 오류 발생 시, **전체 프로세스를 중단시키지 않고** 해당 파일만 안정적인 기본 파서로 자동 전환하여 처리합니다.
- 이를 통해 **안정성**과 **고급 기능 활용**이라는 두 가지 목표를 동시에 달성합니다.

---

## 3. 해결 방안: '시도-감지-대체 (Try-Detect-Fallback)' 전략

'낙관적 실행(Optimistic Execution)' 원칙에 기반하여, 모든 파일에 대해 `enhanced_parser`를 먼저 시도하고, 특정 예외가 발생했을 때만 이를 감지하여 기본 파서로 대체하는 동적 폴백 메커니즘을 구현합니다.

### 3.1. 전체 실행 흐름

```
[ 시작 ]
   |
   v
[ XML 파일 목록 가져오기 ]
   |
   v
( 루프 시작: 각 XML 파일에 대해 )
   |
   v
[ try 블록 진입 ]
   |
   v
   [ enhanced_parser.parse(파일) 호출 ]
   |
   +------> [ 순환 참조 발생? ] --(예)--> [ CircularReferenceError 발생 ]
   |             |                                  |
   |            (아니오)                             |
   |             |                                  v
   |             v                         [ except CircularReferenceError 블록 ]
   |       [ 파싱 성공 ]                         |
   |             |                                  v
   |             |                         [ 경고 로그 기록 ]
   |             |                                  |
   |             |                                  v
   |             |                         [ old_parser.parse(파일) 호출 ]
   |             |                                  |
   |             +----------------------------------+
   |                                                |
   v                                                v
[ 분석 결과 저장 ]
   |
   v
( 다음 파일로 루프 계속 )
```

---

## 4. 세부 구현 방안

### 4.1. 1단계: `CircularReferenceError` 커스텀 예외 정의

순환 참조 발생을 명확히 식별하기 위한 전용 예외 클래스를 정의합니다.

- **위치**: `util/exceptions.py` 또는 공용 모듈
- **목적**: 일반 `Exception`과 구분하여, 순환 참조에 대한 특화된 처리 로직을 구현하기 위함입니다.

```python
# /util/exceptions.py
class CircularReferenceError(Exception):
    """
    MyBatis XML <include> 처리 중 순환 참조가 발견되었을 때 발생하는 예외입니다.
    """
    def __init__(self, message, path=None):
        super().__init__(message)
        self.path = path or [] # 순환이 발생한 경로를 저장하여 로그에 활용
```

### 4.2. 2단계: `enhanced_parser`가 예외를 발생시키도록 수정

기존 `enhanced_parser`의 순환 참조 탐지 로직을 수정하여, 경고만 기록하는 대신 `CircularReferenceError`를 발생(raise)시킵니다.

- **위치**: `parser/enhanced_xml_parser.py` (가칭)
- **변경점**: 순환 참조 감지 시, `logger.warning` 대신 `raise CircularReferenceError(...)`를 호출합니다.

```python
# /parser/enhanced_xml_parser.py (가칭)
from util.exceptions import CircularReferenceError

class EnhancedMyBatisParser:
    # ...
    def _expand_includes(self, element: ET.Element, processing_stack: set):
        # ...
        if unique_fragment_id in processing_stack:
            error_message = f"순환 참조 발견! '{unique_fragment_id}' 처리를 중단합니다."
            # 순환 경로와 함께 예외를 발생시켜 컨텍스트를 전달
            raise CircularReferenceError(error_message, path=list(processing_stack))
        # ...
```

### 4.3. 3단계: 오케스트레이터에 동적 폴백 로직 구현

XML 파일을 실제로 파싱하는 메인 로직(Orchestrator)에서 `try...except` 구문을 사용하여 폴백 로직을 구현합니다.

- **위치**: `xml_loading.py` 또는 `main.py` 등 파서가 호출되는 부분
- **핵심 로직**: `enhanced_parser` 호출을 `try` 블록으로 감싸고, `CircularReferenceError` 발생 시 `except` 블록에서 `old_parser`를 호출합니다.

```python
# /xml_loading.py (예시)

enhanced_parser = EnhancedMyBatisParser()
old_parser = OldMyBatisParser() # 기존의 안정적인 파서

def process_xml_file(file_path):
    try:
        # 1. [시도] enhanced_parser를 우선적으로 시도
        logger.debug(f"'{file_path}' 파일에 대해 Enhanced Parser를 시도합니다.")
        return enhanced_parser.parse(file_path)

    except CircularReferenceError as e:
        # 2. [감지] 순환 참조 예외 발생 시
        logger.warning(f"'{file_path}' 파일에서 순환 참조가 감지되어 기본 파서로 대체합니다. (경로: {e.path})")
        # 3. [대체] old_parser로 폴백하여 처리
        return old_parser.parse(file_path)

    except Exception as e:
        # 순환 참조 외 다른 예외에 대한 추가적인 안전장치
        logger.error(f"'{file_path}' 파일 처리 중 Enhanced Parser에서 예상치 못한 오류 발생. 기본 파서로 대체합니다. 오류: {e}")
        return old_parser.parse(file_path)

# 메인 루프
# for file_path in all_xml_files:
#     analysis_result = process_xml_file(file_path)
#     # ... 결과 후처리 ...
```

### 4.4. 4단계: `enhanced_parser` 기본 활성화

모든 구현이 완료된 후, `config.yaml` 파일에서 `enhanced_parser` 관련 설정을 활성화합니다.

```yaml
# config/enhanced_parser_config.yaml (예시)
enhanced_parser:
  enabled: true # 기본값으로 활성화
  # ... 기타 설정 ...
```

---

## 5. 기대 효과

1.  **안정성 극대화**: 순환 참조와 같은 치명적 오류가 발생해도 전체 분석 프로세스가 중단되지 않으며, 해당 파일은 안정적으로 처리됩니다.
2.  **기능 활용 극대화**: 문제가 없는 모든 파일에 대해 `enhanced_parser`의 향상된 분석 기능(동적 SQL, `<include>` 확장 등)을 적용하여 전반적인 분석 품질을 높입니다.
3.  **유지보수성 향상**: 문제 파일을 수동으로 관리할 필요가 없어지므로, 새로운 유형의 문제가 발생해도 코드 수정 없이 시스템이 동적으로 대응할 수 있습니다.
4.  **'실패의 원자성' 확보**: 분석 실패가 개별 파일 단위로 국한되어 다른 파일의 분석에 영향을 주지 않습니다.

---

## 6. 결론

제안된 '시도-감지-대체' 전략은 `enhanced_parser`의 고급 기능과 시스템 전체의 안정성 사이에서 최적의 균형을 찾는 현실적이고 강력한 해결책입니다. 이 방안을 통해, 이전에 개발이 불가능하다고 판단했던 문제들을 안전하게 우회하고, 시스템의 분석 능력을 한 단계 발전시킬 수 있을 것으로 기대합니다.
