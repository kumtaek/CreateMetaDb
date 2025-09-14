"""
Parser 모듈 패키지
- 처리플로우 단계별 파싱 기능을 별도 파일로 분리
- 각 단계별로 확정(read-only)하여 안정성 확보

현재 구조 (User Rules 준수):
- xml_parser.py: 3-4단계 통합 XML 파싱 (쿼리 추출 + 관계 분석)
- 향후 step5, step6, step7 파서들 추가 예정
"""

# XML 파서 (3-4단계 통합)
from .xml_parser import XmlParser

__all__ = [
    'XmlParser'
]