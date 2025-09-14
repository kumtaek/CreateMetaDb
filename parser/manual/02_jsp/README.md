# JSP 파서용 메뉴얼

## 개요
JSP(JavaServer Pages) 코드 분석을 위한 공식 메뉴얼 및 스펙 문서를 저장하는 폴더입니다.

## 보유 메뉴얼
- `jakarta-server-pages-spec-3.1.pdf` - Jakarta Server Pages 3.1 스펙

## 추가 필요 메뉴얼
- JSP Tag Library Reference
- JSTL (JSP Standard Tag Library) Reference
- JSP Custom Tag Development Guide

## 파서 활용
- JSP 태그 분석
- 스크립틀릿 처리
- 디렉티브 분석
- 액션 태그 처리
- EL(Expression Language) 분석

## 관련 설정 파일
- `path_utils.get_parser_config_path("jsp")` (크로스플랫폼 대응)
- 공통함수 사용으로 하드코딩 금지 및 경로 구분자 문제 해결
- `utils\jsp_keyword_config.py` (추가 권장)
