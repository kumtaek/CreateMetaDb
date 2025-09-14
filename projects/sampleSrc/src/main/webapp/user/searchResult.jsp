<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>고급 검색 결과</title>
    <style>
        .search-params { margin: 20px 0; padding: 15px; background: #e3f2fd; }
        .result-summary { margin: 10px 0; font-weight: bold; color: #1976d2; }
        .user-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .user-table th, .user-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .user-table th { background-color: #1976d2; color: white; }
        .type-normal { color: blue; }
        .type-admin { color: red; font-weight: bold; }
        .type-vip { color: gold; font-weight: bold; }
    </style>
</head>
<body>
    <h1>고급 검색 결과</h1>
    
    <!-- 검색 조건 표시 -->
    <div class="search-params">
        <h3>검색 조건</h3>
        <c:if test="${not empty searchParams.userType}">
            <p>사용자 유형: ${searchParams.userType}</p>
        </c:if>
        <c:if test="${not empty searchParams.minAge}">
            <p>최소 나이: ${searchParams.minAge}세</p>
        </c:if>
        <c:if test="${not empty searchParams.maxAge}">
            <p>최대 나이: ${searchParams.maxAge}세</p>
        </c:if>
        <c:if test="${not empty searchParams.startDate}">
            <p>시작 날짜: ${searchParams.startDate}</p>
        </c:if>
        <c:if test="${not empty searchParams.endDate}">
            <p>종료 날짜: ${searchParams.endDate}</p>
        </c:if>
    </div>
    
    <!-- 결과 요약 -->
    <div class="result-summary">
        총 ${users.size()}명의 사용자가 검색되었습니다.
    </div>
    
    <!-- 검색 결과 테이블 -->
    <table class="user-table">
        <thead>
            <tr>
                <th>ID</th>
                <th>사용자명</th>
                <th>이메일</th>
                <th>이름</th>
                <th>나이</th>
                <th>상태</th>
                <th>사용자 유형</th>
                <th>전화번호</th>
                <th>생성일</th>
            </tr>
        </thead>
        <tbody>
            <c:choose>
                <c:when test="${empty users}">
                    <tr>
                        <td colspan="9" style="text-align: center;">검색 조건에 맞는 사용자가 없습니다.</td>
                    </tr>
                </c:when>
                <c:otherwise>
                    <c:forEach var="user" items="${users}">
                        <tr>
                            <td>${user.id}</td>
                            <td>${user.username}</td>
                            <td>${user.email}</td>
                            <td>${user.name}</td>
                            <td>${user.age}</td>
                            <td>${user.status}</td>
                            <td>
                                <c:choose>
                                    <c:when test="${user.userType == 'ADMIN'}">
                                        <span class="type-admin">관리자</span>
                                    </c:when>
                                    <c:when test="${user.userType == 'VIP'}">
                                        <span class="type-vip">VIP</span>
                                    </c:when>
                                    <c:otherwise>
                                        <span class="type-normal">일반</span>
                                    </c:otherwise>
                                </c:choose>
                            </td>
                            <td>${user.phone}</td>
                            <td><fmt:formatDate value="${user.createdDate}" pattern="yyyy-MM-dd"/></td>
                        </tr>
                    </c:forEach>
                </c:otherwise>
            </c:choose>
        </tbody>
    </table>
    
    <!-- 네비게이션 -->
    <div style="margin: 20px 0;">
        <a href="<c:url value='/user/list'/>">목록으로 돌아가기</a> |
        <a href="<c:url value='/user/advanced-search'/>">다시 검색</a>
    </div>
    
    <script>
        // 결과 테이블 정렬 기능
        function sortTable(columnIndex) {
            var table = document.querySelector('.user-table');
            var tbody = table.querySelector('tbody');
            var rows = Array.from(tbody.querySelectorAll('tr'));
            
            rows.sort(function(a, b) {
                var aVal = a.cells[columnIndex].textContent.trim();
                var bVal = b.cells[columnIndex].textContent.trim();
                
                // 숫자 정렬
                if (columnIndex === 0 || columnIndex === 4) {
                    return parseInt(aVal) - parseInt(bVal);
                }
                
                // 문자열 정렬
                return aVal.localeCompare(bVal);
            });
            
            rows.forEach(function(row) {
                tbody.appendChild(row);
            });
        }
        
        // 헤더 클릭 시 정렬
        document.querySelectorAll('.user-table th').forEach(function(th, index) {
            th.style.cursor = 'pointer';
            th.addEventListener('click', function() {
                sortTable(index);
            });
        });
    </script>
</body>
</html>

