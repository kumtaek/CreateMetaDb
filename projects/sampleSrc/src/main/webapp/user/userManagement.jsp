<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>User Management</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
    <h1>User Management System</h1>
    
    <!-- User List Section -->
    <div id="userList">
        <h2>User List</h2>
        <button onclick="loadUsers()">Load Users</button>
        <div id="userTable"></div>
    </div>
    
    <!-- User Search Section -->
    <div id="userSearch">
        <h2>Search Users</h2>
        <form id="searchForm">
            <input type="text" id="searchKeyword" placeholder="Enter search keyword">
            <select id="searchType">
                <option value="username">Username</option>
                <option value="email">Email</option>
                <option value="status">Status</option>
            </select>
            <button type="button" onclick="searchUsers()">Search</button>
        </form>
    </div>
    
    <!-- User Statistics Section -->
    <div id="userStats">
        <h2>User Statistics</h2>
        <button onclick="loadUserStatistics()">Load Statistics</button>
        <div id="statsTable"></div>
    </div>
    
    <!-- Order Management Section -->
    <div id="orderManagement">
        <h2>Order Management</h2>
        <button onclick="loadOrders()">Load Orders</button>
        <button onclick="loadOrderStatistics()">Load Order Statistics</button>
        <div id="orderTable"></div>
    </div>
    
    <!-- Product Management Section -->
    <div id="productManagement">
        <h2>Product Management</h2>
        <button onclick="loadProducts()">Load Products</button>
        <button onclick="loadProductRecommendations()">Load Recommendations</button>
        <div id="productTable"></div>
    </div>

    <script>
        // Load all users
        function loadUsers() {
            $.ajax({
                url: '/api/users',
                method: 'GET',
                success: function(data) {
                    displayUsers(data);
                },
                error: function(xhr, status, error) {
                    console.error('Error loading users:', error);
                }
            });
        }
        
        // Search users by criteria
        function searchUsers() {
            var keyword = $('#searchKeyword').val();
            var type = $('#searchType').val();
            
            $.ajax({
                url: '/api/users/search',
                method: 'GET',
                data: {
                    keyword: keyword,
                    type: type
                },
                success: function(data) {
                    displayUsers(data);
                },
                error: function(xhr, status, error) {
                    console.error('Error searching users:', error);
                }
            });
        }
        
        // Load user statistics
        function loadUserStatistics() {
            $.ajax({
                url: '/api/users/statistics',
                method: 'GET',
                success: function(data) {
                    displayStatistics(data);
                },
                error: function(xhr, status, error) {
                    console.error('Error loading statistics:', error);
                }
            });
        }
        
        // Load orders
        function loadOrders() {
            $.ajax({
                url: '/api/orders',
                method: 'GET',
                success: function(data) {
                    displayOrders(data);
                },
                error: function(xhr, status, error) {
                    console.error('Error loading orders:', error);
                }
            });
        }
        
        // Load order statistics
        function loadOrderStatistics() {
            $.ajax({
                url: '/api/orders/statistics',
                method: 'GET',
                success: function(data) {
                    displayOrderStatistics(data);
                },
                error: function(xhr, status, error) {
                    console.error('Error loading order statistics:', error);
                }
            });
        }
        
        // Load products
        function loadProducts() {
            $.ajax({
                url: '/api/products',
                method: 'GET',
                success: function(data) {
                    displayProducts(data);
                },
                error: function(xhr, status, error) {
                    console.error('Error loading products:', error);
                }
            });
        }
        
        // Load product recommendations
        function loadProductRecommendations() {
            $.ajax({
                url: '/api/products/recommendations',
                method: 'GET',
                success: function(data) {
                    displayProductRecommendations(data);
                },
                error: function(xhr, status, error) {
                    console.error('Error loading recommendations:', error);
                }
            });
        }
        
        // Display functions
        function displayUsers(users) {
            var html = '<table border="1"><tr><th>ID</th><th>Username</th><th>Email</th><th>Status</th></tr>';
            users.forEach(function(user) {
                html += '<tr><td>' + user.userId + '</td><td>' + user.username + '</td><td>' + user.email + '</td><td>' + user.status + '</td></tr>';
            });
            html += '</table>';
            $('#userTable').html(html);
        }
        
        function displayStatistics(stats) {
            var html = '<table border="1"><tr><th>Type</th><th>Count</th></tr>';
            Object.keys(stats).forEach(function(key) {
                html += '<tr><td>' + key + '</td><td>' + stats[key] + '</td></tr>';
            });
            html += '</table>';
            $('#statsTable').html(html);
        }
        
        function displayOrders(orders) {
            var html = '<table border="1"><tr><th>Order ID</th><th>User ID</th><th>Total Amount</th><th>Status</th></tr>';
            orders.forEach(function(order) {
                html += '<tr><td>' + order.orderId + '</td><td>' + order.userId + '</td><td>' + order.totalAmount + '</td><td>' + order.orderStatus + '</td></tr>';
            });
            html += '</table>';
            $('#orderTable').html(html);
        }
        
        function displayOrderStatistics(stats) {
            var html = '<table border="1"><tr><th>Status</th><th>Count</th><th>Total Amount</th></tr>';
            stats.forEach(function(stat) {
                html += '<tr><td>' + stat.status + '</td><td>' + stat.count + '</td><td>' + stat.totalAmount + '</td></tr>';
            });
            html += '</table>';
            $('#orderTable').html(html);
        }
        
        function displayProducts(products) {
            var html = '<table border="1"><tr><th>Product ID</th><th>Name</th><th>Price</th><th>Stock</th></tr>';
            products.forEach(function(product) {
                html += '<tr><td>' + product.productId + '</td><td>' + product.productName + '</td><td>' + product.price + '</td><td>' + product.stockQuantity + '</td></tr>';
            });
            html += '</table>';
            $('#productTable').html(html);
        }
        
        function displayProductRecommendations(recommendations) {
            var html = '<table border="1"><tr><th>User ID</th><th>Product ID</th><th>Score</th></tr>';
            recommendations.forEach(function(rec) {
                html += '<tr><td>' + rec.userId + '</td><td>' + rec.productId + '</td><td>' + rec.score + '</td></tr>';
            });
            html += '</table>';
            $('#productTable').html(html);
        }
    </script>
</body>
</html>
