<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<!DOCTYPE html>
<html>
<head>
    <title>Test JSP - Phase 1 MVP</title>
</head>
<body>
    <h1>User List</h1>
    
    <%
        // 스크립틀릿: Java 코드
        List<User> users = userService.getUserList();
        String message = userController.getMessage();
        int count = dataService.getCount();
    %>
    
    <p>Total Users: <%= userService.getUserCount() %></p>
    <p>Message: <%= userController.getCurrentMessage() %></p>
    
    <table>
        <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
        </tr>
        <%
            for (User user : users) {
                String userName = userService.getUserName(user);
                String userEmail = userService.getUserEmail(user);
        %>
        <tr>
            <td><%= user.getId() %></td>
            <td><%= userName %></td>
            <td><%= userEmail %></td>
        </tr>
        <%
            }
        %>
    </table>
    
    <%
        // 추가 스크립틀릿
        boolean isValid = validationService.validateUsers(users);
        if (isValid) {
            String result = orderService.processOrder();
        }
    %>
    
    <p>Status: <%= orderService.getOrderStatus() %></p>
</body>
</html>
