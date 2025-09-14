<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>정상적인 JSP 페이지</title>
    <style>
        .user-info { margin: 10px 0; padding: 10px; border: 1px solid #ccc; }
        .success { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>정상적인 JSP 페이지</h1>
    
    <!-- 정상적인 JSP 태그 -->
    <c:if test="${not empty user}">
        <div class="user-info">
            <p>사용자: ${user.name}</p>
            <p>이메일: ${user.email}</p>
            <p>생성일: <fmt:formatDate value="${user.createDate}" pattern="yyyy-MM-dd HH:mm:ss"/></p>
        </div>
    </c:if>
    
    <!-- 정상적인 EL 표현식 -->
    <c:if test="${empty user}">
        <p class="error">사용자 정보가 없습니다.</p>
    </c:if>
    
    <!-- 정상적인 스크립틀릿 -->
    <%
        String currentTime = new java.util.Date().toString();
        out.println("<p>현재 시간: " + currentTime + "</p>");
        
        // 정상적인 조건문
        if (request.getAttribute("message") != null) {
            out.println("<p class='success'>" + request.getAttribute("message") + "</p>");
        }
    %>
    
    <!-- 정상적인 표현식 -->
    <c:if test="${not empty users}">
        <h2>사용자 목록</h2>
        <table border="1">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>이름</th>
                    <th>이메일</th>
                    <th>생성일</th>
                </tr>
            </thead>
            <tbody>
                <c:forEach var="user" items="${users}">
                    <tr>
                        <td>${user.id}</td>
                        <td>${user.name}</td>
                        <td>${user.email}</td>
                        <td><fmt:formatDate value="${user.createDate}" pattern="yyyy-MM-dd"/></td>
                    </tr>
                </c:forEach>
            </tbody>
        </table>
    </c:if>
    
    <!-- 정상적인 링크 -->
    <div>
        <a href="/user/add">새 사용자 추가</a>
        <a href="/user/list">사용자 목록</a>
        <a href="/user/search">사용자 검색</a>
    </div>
    
</body>
</html>
