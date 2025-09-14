<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>일부 오류가 있는 JSP</title>
    <style>
        .error { color: red; }
        .success { color: green; }
    </style>
</head>
<body>
    <h1>사용자 목록</h1>
    
    <!-- 정상적인 부분 -->
    <c:if test="${not empty message}">
        <p class="success">${message}</p>
    </c:if>
    
    <!-- 정상적인 부분 -->
    <c:if test="${not empty errorMessage}">
        <p class="error">${errorMessage}</p>
    </c:if>
    
    <!-- 정상적인 부분 -->
    <table border="1">
        <thead>
            <tr>
                <th>ID</th>
                <th>이름</th>
                <th>이메일</th>
                <th>생성일</th>
                <th>액션</th>
            </tr>
        </thead>
        <tbody>
            <!-- 정상적인 부분 -->
            <c:forEach var="user" items="${users}">
                <tr>
                    <td>${user.id}</td>
                    <td>${user.name}</td>
                    <td>${user.email}</td>
                    <td>
                        <fmt:formatDate value="${user.createDate}" pattern="yyyy-MM-dd HH:mm:ss"/>
                    </td>
                    <td>
                        <a href="/user/edit?id=${user.id}">수정</a>
                        <a href="/user/delete?id=${user.id}" onclick="return confirm('정말 삭제하시겠습니까?')">삭제</a>
                    </td>
                </tr>
            </c:forEach>
        </tbody>
    </table>
    
    <!-- 오류 부분: 잘못된 EL 표현식 -->
    <c:if test="${user.status == 'ACTIVE'}">
        <p>활성 사용자입니다.</p>
    </c:if>
    
    <!-- 정상적인 부분 -->
    <c:if test="${empty users}">
        <p>등록된 사용자가 없습니다.</p>
    </c:if>
    
    <!-- 오류 부분: 잘못된 스크립틀릿 -->
    <%
        String currentTime = new java.util.Date().toString();
        out.println("<p>현재 시간: " + currentTime + "</p>");
        
        // 오류: 잘못된 변수 참조
        if (userList != null) {  // userList 변수가 정의되지 않음
            out.println("<p>사용자 수: " + userList.size() + "</p>");
        }
    %>
    
    <!-- 정상적인 부분 -->
    <div>
        <a href="/user/add">새 사용자 추가</a>
        <a href="/user/search">사용자 검색</a>
    </div>
    
    <!-- 오류 부분: 잘못된 태그 -->
    <c:choose>
        <c:when test="${not empty users}">
            <p>사용자가 있습니다.</p>
        </c:when>
        <c:otherwise>
            <p>사용자가 없습니다.</p>
        <!-- c:choose 태그 닫기 누락 -->
    
</body>
</html>
