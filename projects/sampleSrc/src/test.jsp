<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/functions" prefix="fn" %>
<%@ include file="header.jsp" %>

<!DOCTYPE html>
<html>
<head>
    <title>Test JSP - Phase 2&3 Enhanced</title>
</head>
<body>
    <h1>User Management System</h1>

    <!-- Phase 3: Java Bean 사용 -->
    <jsp:useBean id="userBean" class="com.example.UserBean" scope="session"/>
    <jsp:useBean id="productBean" class="com.example.ProductBean" scope="request"/>

    <%
        // Phase 1: 스크립틀릿 - Java 메서드 호출
        List<User> users = userService.getUserList();
        String message = userController.getMessage();
        int count = dataService.getCount();
    %>

    <!-- Phase 3: EL 표현식 사용 -->
    <p>Welcome, ${sessionScope.userName}!</p>
    <p>Total Users: ${userBean.userCount}</p>
    <p>Current Time: ${currentTime}</p>
    <p>Product Count: ${productBean.totalProducts}</p>

    <!-- Phase 3: JSTL 태그 사용 -->
    <c:if test="${not empty users}">
        <h2>User List</h2>
        <table border="1">
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Status</th>
            </tr>
            <c:forEach var="user" items="${userBean.userList}" varStatus="status">
                <tr>
                    <td>${user.id}</td>
                    <td>${user.name}</td>
                    <td>${user.email}</td>
                    <td>
                        <c:choose>
                            <c:when test="${user.active}">Active</c:when>
                            <c:otherwise>Inactive</c:otherwise>
                        </c:choose>
                    </td>
                </tr>
            </c:forEach>
        </table>
    </c:if>

    <!-- Phase 3: 더 복잡한 EL 표현식 -->
    <c:set var="userCount" value="${fn:length(userBean.userList)}"/>
    <c:if test="${userCount > 0}">
        <p>User statistics: ${userCount} users found</p>
        <p>Average age: ${userBean.averageAge}</p>
    </c:if>

    <!-- Phase 1: 표현식과 스크립틀릿 혼합 사용 -->
    <p>System Status: <%= orderService.getOrderStatus() %></p>
    <p>Last Update: <%= userService.getLastUpdateTime() %></p>

    <%
        // Phase 1: 추가 Java 메서드 호출
        boolean isValid = validationService.validateUsers(users);
        if (isValid) {
            String result = orderService.processOrder();
            int orderId = productService.createOrder();
        }
    %>

    <!-- Phase 3: Java Bean 속성 설정 -->
    <jsp:setProperty name="userBean" property="currentPage" value="1"/>
    <jsp:setProperty name="productBean" property="category" value="electronics"/>

    <!-- Phase 3: Java Bean 속성 가져오기 -->
    <p>Current Page: <jsp:getProperty name="userBean" property="currentPage"/></p>
    <p>Category: <jsp:getProperty name="productBean" property="category"/></p>

    <!-- Phase 2: JSP 포함 및 전달 -->
    <jsp:include page="sidebar.jsp">
        <jsp:param name="section" value="users"/>
    </jsp:include>

    <c:if test="${param.redirect == 'true'}">
        <jsp:forward page="dashboard.jsp"/>
    </c:if>

    <!-- Phase 2: JSP include 디렉티브 -->
    <%@ include file="footer.jsp" %>
</body>
</html>
