<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>사용자 유형별 목록</title>
    <style>
        .type-header { margin: 20px 0; padding: 15px; background: #f3e5f5; }
        .user-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .user-table th, .user-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .user-table th { background-color: #7b1fa2; color: white; }
        .type-badge { padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; }
        .type-normal { background-color: #2196f3; }
        .type-admin { background-color: #f44336; }
        .type-vip { background-color: #ff9800; }
    </style>
</head>
<body>
    <h1>사용자 유형별 목록</h1>
    
    <!-- 유형 정보 헤더 -->
    <div class="type-header">
        <h2>유형: ${userType}</h2>
        <p>이 유형에 속한 사용자 목록입니다.</p>
    </div>
    
    <!-- 사용자 목록 테이블 -->
    <table class="user-table">
        <thead>
            <tr>
                <th>ID</th>
                <th>사용자명</th>
                <th>이메일</th>
                <th>이름</th>
                <th>나이</th>
                <th>상태</th>
                <th>전화번호</th>
                <th>주소</th>
                <th>생성일</th>
            </tr>
        </thead>
        <tbody>
            <c:choose>
                <c:when test="${empty users}">
                    <tr>
                        <td colspan="9" style="text-align: center;">해당 유형의 사용자가 없습니다.</td>
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
                            <td>${user.phone}</td>
                            <td>${user.address}</td>
                            <td><fmt:formatDate value="${user.createdDate}" pattern="yyyy-MM-dd HH:mm"/></td>
                        </tr>
                    </c:forEach>
                </c:otherwise>
            </c:choose>
        </tbody>
    </table>
    
    <!-- 유형별 통계 -->
    <div style="margin: 20px 0; padding: 15px; background: #e8f5e9;">
        <h3>유형별 통계</h3>
        <p>총 사용자 수: ${users.size()}명</p>
        <c:if test="${not empty users}">
            <c:set var="activeCount" value="0" />
            <c:set var="inactiveCount" value="0" />
            <c:forEach var="user" items="${users}">
                <c:choose>
                    <c:when test="${user.status == 'ACTIVE'}">
                        <c:set var="activeCount" value="${activeCount + 1}" />
                    </c:when>
                    <c:otherwise>
                        <c:set var="inactiveCount" value="${inactiveCount + 1}" />
                    </c:otherwise>
                </c:choose>
            </c:forEach>
            <p>활성 사용자: ${activeCount}명</p>
            <p>비활성 사용자: ${inactiveCount}명</p>
        </c:if>
    </div>
    
    <!-- 네비게이션 -->
    <div style="margin: 20px 0;">
        <a href="<c:url value='/user/list'/>">전체 목록</a> |
        <a href="<c:url value='/user/advanced-search'/>">고급 검색</a> |
        <a href="<c:url value='/user/dynamic/NORMAL'/>">일반 사용자</a> |
        <a href="<c:url value='/user/dynamic/ADMIN'/>">관리자</a> |
        <a href="<c:url value='/user/dynamic/VIP'/>">VIP 사용자</a>
    </div>
    
    <script>
        // 테이블 행 클릭 시 상세 정보 표시
        document.querySelectorAll('.user-table tbody tr').forEach(function(row) {
            row.style.cursor = 'pointer';
            row.addEventListener('click', function() {
                var userId = this.cells[0].textContent;
                if (confirm('사용자 ID ' + userId + '의 상세 정보를 보시겠습니까?')) {
                    // 실제 구현에서는 상세 페이지로 이동
                    alert('사용자 상세 정보 기능은 구현 예정입니다.');
                }
            });
        });
        
        // 테이블 행 호버 효과
        document.querySelectorAll('.user-table tbody tr').forEach(function(row) {
            row.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#f5f5f5';
            });
            row.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
        });
    </script>
</body>
</html>

