# XML 파서 재귀 깊이 오류 문제점 분석

## 📋 질의 개요
- **질의일시**: 2025-09-14 14:55:00
- **질의자**: 시스템 분석
- **질의유형**: 오류 분석 및 해결방안
- **관련파일**: xml_parser.py, sax_fallback_parser.py, main.py

## 🚨 발생한 오류 현상

### 오류 메시지
```
RecursionError: maximum recursion depth exceeded
File "D:\Analyzer\CreateMetaDb\main.py", line 124, in main
    from xml_loading import XmlLoadingEngine
File "D:\Analyzer\CreateMetaDb\xml_loading.py", line 22, in <module>
    from parser.xml_parser import XmlParser
File "D:\Analyzer\CreateMetaDb\parser\__init__.py", line 12, in <module>
    from .xml_parser import XmlParser
File "D:\Analyzer\CreateMetaDb\parser\xml_parser.py", line 23, in <module>
    from .sax_fallback_parser import MyBatisSaxParser
File "D:\Analyzer\CreateMetaDb\parser\sax_fallback_parser.py", line 14, in <module>
    import xml.sax
```

### 오류 발생 위치
- **3단계 실행 시점**: XML 분석 및 SQL 컴포넌트 등록 단계
- **구체적 위치**: `xml.sax` 모듈 임포트 시점
- **영향 범위**: 전체 메타데이터 생성 프로세스 중단

## 🔍 문제점 분석

### 1. 재귀 깊이 설정 문제
```python
# main.py에서 설정된 재귀 깊이
sys.setrecursionlimit(50)  # 너무 낮은 값
```

**문제점**:
- Python 기본 재귀 깊이(1000)보다 훨씬 낮게 설정됨
- XML 파싱 과정에서 복잡한 중첩 구조 처리 시 부족
- SAX 파서의 내부 재귀 호출과 충돌

### 2. XML 파서 의존성 문제
```python
# xml_parser.py
from .sax_fallback_parser import MyBatisSaxParser

# sax_fallback_parser.py  
import xml.sax  # 여기서 재귀 깊이 초과
```

**문제점**:
- `xml.sax` 모듈 자체가 내부적으로 재귀 호출 사용
- 복잡한 XML 구조 파싱 시 재귀 깊이 증가
- SAX 파서의 이벤트 기반 처리 방식과 충돌

### 3. 모듈 임포트 순환 참조 가능성
```python
# 의존성 체인
main.py → xml_loading.py → parser/__init__.py → xml_parser.py → sax_fallback_parser.py → xml.sax
```

**문제점**:
- 긴 임포트 체인으로 인한 메모리 사용량 증가
- 각 모듈의 초기화 과정에서 재귀 호출 누적
- Python의 모듈 로딩 메커니즘과 충돌

## 🎯 근본 원인

### 1. 재귀 깊이 설정 부적절
- **현재값**: 50 (너무 낮음)
- **권장값**: 2000-5000 (XML 파싱 고려)
- **영향**: XML 파싱 중 중첩된 태그 구조 처리 불가

### 2. XML 파서 아키텍처 문제
- **SAX 파서**: 이벤트 기반으로 메모리 효율적이지만 재귀 사용
- **DOM 파서**: 트리 구조로 재귀 깊이 문제 적음
- **현재 선택**: SAX 파서 사용으로 재귀 깊이 제약 발생

### 3. 복잡한 XML 구조 처리 한계
- **MyBatis XML**: 중첩된 `<if>`, `<choose>`, `<foreach>` 태그
- **동적 SQL**: 복잡한 조건문과 반복문 구조
- **재귀 깊이**: XML 구조의 깊이만큼 재귀 호출 증가

## 💡 해결방안 제안

### 1. 재귀 깊이 조정 (즉시 적용 가능)
```python
# main.py 수정
sys.setrecursionlimit(2000)  # 50 → 2000으로 증가
```

### 2. XML 파서 전략 변경 (중기 해결)
```python
# DOM 파서 사용으로 변경
from xml.dom import minidom
# 또는 lxml 사용
from lxml import etree
```

### 3. 파서 아키텍처 개선 (장기 해결)
- **비재귀 파싱**: 스택 기반 파싱으로 변경
- **청크 단위 처리**: 대용량 XML을 작은 단위로 분할
- **스트리밍 파싱**: 메모리 효율적인 파싱 방식

## 🔧 즉시 적용 가능한 해결책

### 1단계: 재귀 깊이 증가
```python
# main.py 수정
import sys
sys.setrecursionlimit(2000)  # 50 → 2000
```

### 2단계: XML 파서 안전성 강화
```python
# sax_fallback_parser.py 수정
try:
    import xml.sax
    # 파싱 로직
except RecursionError:
    # 대체 파싱 방식 사용
    pass
```

### 3단계: 오류 처리 개선
```python
# xml_loading.py 수정
try:
    from parser.xml_parser import XmlParser
except RecursionError as e:
    logger.error(f"XML 파서 재귀 깊이 오류: {e}")
    # 대체 파싱 방식 또는 오류 보고
```

## 📊 영향도 분석

### 현재 영향
- **3단계 완전 중단**: XML 분석 불가
- **4단계 진행 불가**: Java 분석도 중단
- **전체 프로세스 실패**: 메타데이터 생성 불가

### 해결 후 예상 효과
- **3단계 정상 진행**: XML 분석 완료
- **4단계 정상 진행**: Java 분석 완료
- **전체 프로세스 성공**: 메타데이터 생성 완료

## 🎯 권장 조치사항

### 즉시 조치 (우선순위: 높음)
1. **재귀 깊이 증가**: 50 → 2000
2. **오류 처리 강화**: RecursionError 예외 처리
3. **로깅 개선**: 상세한 오류 정보 기록

### 중기 조치 (우선순위: 중간)
1. **XML 파서 전략 검토**: SAX → DOM 또는 lxml
2. **파싱 성능 최적화**: 메모리 사용량 모니터링
3. **테스트 케이스 확장**: 복잡한 XML 구조 테스트

### 장기 조치 (우선순위: 낮음)
1. **파서 아키텍처 재설계**: 비재귀 파싱 방식
2. **대용량 XML 처리**: 스트리밍 파싱 구현
3. **성능 벤치마크**: 다양한 XML 크기별 성능 측정

## 📝 결론

현재 발생한 재귀 깊이 오류는 **재귀 깊이 설정 부적절**이 주원인이며, **즉시 재귀 깊이를 2000으로 증가**시키면 해결 가능합니다. 

장기적으로는 **XML 파서 전략을 DOM 기반으로 변경**하여 재귀 깊이 문제를 근본적으로 해결하는 것이 권장됩니다.

---

*질의 작성일: 2025-09-14 14:55:00*
*분석자: 시스템 자동 분석*
*상태: 해결방안 제시 완료*
