<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>오류 케이스 페이지</title>
    <style>
        .error-section { margin: 20px 0; padding: 15px; background: #ffebee; border-left: 4px solid #f44336; }
        .warning { color: #f44336; font-weight: bold; }
    </style>
</head>
<body>
    <h1>오류 케이스 테스트 페이지</h1>
    
    <!-- 오류 1: 잘못된 JSTL 태그 사용 -->
    <div class="error-section">
        <h3>오류 1: 잘못된 JSTL 태그</h3>
        <c:if test="${not empty users}">
            <c:forEach var="user" items="${users}">
                <p>사용자: ${user.name}</p>
                <!-- 오류: 잘못된 태그 닫기 -->
                </c:if>  <!-- c:forEach가 아닌 c:if로 닫음 -->
            </c:forEach>
        </c:if>
    </div>
    
    <!-- 오류 2: 잘못된 EL 표현식 -->
    <div class="error-section">
        <h3>오류 2: 잘못된 EL 표현식</h3>
        <p>사용자 수: ${users.size()}</p>  <!-- List에 size() 메소드 직접 호출 불가 -->
        <p>첫 번째 사용자: ${users[0].name}</p>  <!-- 인덱스 접근 시 null 체크 없음 -->
    </div>
    
    <!-- 오류 3: 잘못된 날짜 포맷 -->
    <div class="error-section">
        <h3>오류 3: 잘못된 날짜 포맷</h3>
        <c:forEach var="user" items="${users}">
            <p>생성일: <fmt:formatDate value="${user.createdDate}" pattern="invalid-pattern"/></p>
        </c:forEach>
    </div>
    
    <!-- 오류 4: 잘못된 JavaScript -->
    <div class="error-section">
        <h3>오류 4: JavaScript 오류</h3>
        <script>
            // 오류: 선언되지 않은 변수 사용
            console.log(undefinedVariable);
            
            // 오류: 잘못된 함수 호출
            nonExistentFunction();
            
            // 오류: 잘못된 객체 접근
            var obj = null;
            obj.property.value;  // NullPointerException
            
            // 오류: 무한 루프
            while (true) {
                // break 문 없음
                console.log("Infinite loop");
            }
        </script>
    </div>
    
    <!-- 오류 5: 잘못된 CSS -->
    <div class="error-section">
        <h3>오류 5: CSS 오류</h3>
        <style>
            .error-class {
                color: invalid-color;  /* 잘못된 색상 값 */
                font-size: 20px;
                background-color: #invalid-hex;  /* 잘못된 16진수 */
                border: 1px solid;  /* border-style 누락 */
            }
        </style>
        <div class="error-class">CSS 오류 테스트</div>
    </div>
    
    <!-- 오류 6: 잘못된 HTML 구조 -->
    <div class="error-section">
        <h3>오류 6: HTML 구조 오류</h3>
        <table>
            <tr>
                <td>셀 1</td>
                <td>셀 2</td>
            </tr>
            <!-- 오류: 닫히지 않은 tr 태그 -->
            <tr>
                <td>셀 3</td>
                <td>셀 4</td>
            <!-- </tr> 누락 -->
        </table>
    </div>
    
    <!-- 오류 7: 잘못된 폼 처리 -->
    <div class="error-section">
        <h3>오류 7: 폼 처리 오류</h3>
        <form method="post" action="<c:url value='/error/search'/>">
            <input type="text" name="name" placeholder="이름">
            <input type="text" name="age" placeholder="나이">
            <button type="submit">검색</button>
        </form>
        
        <!-- 오류: 폼 데이터 검증 없이 사용 -->
        <c:if test="${not empty param.age}">
            <p>나이: ${param.age}</p>
            <c:set var="ageInt" value="${param.age}" />
            <p>나이 + 10: ${ageInt + 10}</p>  <!-- 문자열을 숫자로 변환하지 않고 연산 -->
        </c:if>
    </div>
    
    <!-- 오류 8: 잘못된 조건문 -->
    <div class="error-section">
        <h3>오류 8: 조건문 오류</h3>
        <c:choose>
            <c:when test="${user.status == 'ACTIVE'}">
                <p class="warning">활성 사용자</p>
            </c:when>
            <c:when test="${user.status == 'INACTIVE'}">
                <p class="warning">비활성 사용자</p>
            </c:when>
            <!-- 오류: c:otherwise 태그 누락 -->
        </c:choose>
    </div>
    
    <script>
        // 오류 9: 잘못된 이벤트 처리
        document.addEventListener('DOMContentLoaded', function() {
            // 오류: 존재하지 않는 요소에 이벤트 리스너 추가
            document.getElementById('nonExistentElement').addEventListener('click', function() {
                alert('This will cause an error');
            });
            
            // 오류: 잘못된 AJAX 요청
            fetch('/non-existent-endpoint')
                .then(response => response.json())
                .then(data => {
                    // 오류: data가 null일 수 있음
                    console.log(data.property.value);
                });
        });
    </script>
</body>
</html>

