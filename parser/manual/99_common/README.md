# 기술 메뉴얼 저장소

SourceAnalyzer 프로젝트에서 참조하는 기술 메뉴얼들을 저장하는 폴더입니다.

## 저장할 메뉴얼 목록

### 1. Oracle 관련

- **Oracle SQL Reference Manual** - SQL 문법 및 함수 참조
- **Oracle Database SQL Language Reference** - 데이터베이스 SQL 언어 참조
- **Oracle PL/SQL User's Guide and Reference** - PL/SQL 프로그래밍 가이드

### 2. MyBatis 관련

- **MyBatis 3 User Guide** - MyBatis 사용법 가이드
- **MyBatis Dynamic SQL** - 동적 SQL 처리 가이드
- **MyBatis Spring Integration** - Spring 통합 가이드

### 3. JPA 관련

- **Jakarta Persistence API Specification** - JPA 스펙 문서
- **Hibernate User Guide** - Hibernate 사용법 가이드
- **Spring Data JPA Reference** - Spring Data JPA 참조

### 4. Java 관련

- **Java SE Documentation** - Java 표준 에디션 문서
- **Java EE Documentation** - Java 엔터프라이즈 에디션 문서
- **Java Language Specification** - Java 언어 스펙

### 5. JSP 관련

- **Jakarta Server Pages Specification** - JSP 스펙 문서
- **JSP Tag Library Reference** - JSP 태그 라이브러리 참조
- **JSTL Reference** - JSTL 참조

## 다운로드 방법

### Oracle 메뉴얼

1. [Oracle Documentation](https://docs.oracle.com/) 접속
2. Database → Oracle Database → SQL Language Reference 선택
3. PDF 다운로드

### MyBatis 메뉴얼

1. [MyBatis Documentation](https://mybatis.org/mybatis-3/) 접속
2. User Guide 섹션에서 HTML 저장
3. Dynamic SQL 섹션 별도 저장

### JPA 메뉴얼

1. [Jakarta EE Documentation](https://jakarta.ee/specifications/persistence/) 접속
2. Jakarta Persistence API Specification 다운로드

### Java 메뉴얼

1. [Oracle Java Documentation](https://docs.oracle.com/en/java/) 접속
2. Java SE Documentation 다운로드

### JSP 메뉴얼

1. [Jakarta EE Documentation](https://jakarta.ee/specifications/pages/) 접속
2. Jakarta Server Pages Specification 다운로드

## 파일 구조

```
docs/메뉴얼,도움자/
├── oracle/
│   ├── sql-reference-manual.pdf
│   ├── plsql-user-guide.pdf
│   └── database-sql-language-reference.pdf
├── mybatis/
│   ├── user-guide.html
│   ├── dynamic-sql.html
│   └── spring-integration.html
├── jpa/
│   ├── jakarta-persistence-spec.pdf
│   ├── hibernate-user-guide.pdf
│   └── spring-data-jpa-reference.pdf
├── java/
│   ├── java-se-documentation.pdf
│   ├── java-ee-documentation.pdf
│   └── java-language-specification.pdf
└── jsp/
    ├── jakarta-server-pages-spec.pdf
    ├── jsp-tag-library-reference.pdf
    └── jstl-reference.pdf
```

## 활용 방법

1. **SQL 파서 개선**: Oracle SQL Reference Manual을 참조하여 정확한 SQL 문법 파싱
2. **MyBatis 동적 SQL 처리**: MyBatis Dynamic SQL 가이드를 참조하여 복잡한 동적 쿼리 처리
3. **JPA 쿼리 분석**: JPA 스펙을 참조하여 JPQL 쿼리 분석
4. **Java 코드 분석**: Java Language Specification을 참조하여 정확한 Java 코드 파싱
5. **JSP 태그 분석**: JSP 스펙을 참조하여 JSP 태그 및 스크립틀릿 분석

## 주의사항

- 메뉴얼은 정기적으로 업데이트하여 최신 버전 유지
- 저작권을 준수하여 사용
- 오프라인 환경에서도 참조 가능하도록 로컬 저장
