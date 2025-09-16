<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>마이크로서비스 대시보드</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
    <h2>마이크로서비스 대시보드</h2>
    
    <div id="microservice-dashboard">
        <!-- 통합 사용자 정보 조회 -->
        <div class="section">
            <h3>통합 사용자 정보</h3>
            <input type="number" id="userId" placeholder="사용자 ID">
            <button onclick="getUserProfile()">사용자 프로필 조회</button>
            <div id="user-profile"></div>
        </div>
        
        <!-- 통합 주문 정보 조회 -->
        <div class="section">
            <h3>통합 주문 정보</h3>
            <input type="number" id="orderId" placeholder="주문 ID">
            <button onclick="getOrderDetails()">주문 상세 조회</button>
            <div id="order-details"></div>
        </div>
        
        <!-- 통합 대시보드 데이터 -->
        <div class="section">
            <h3>통합 대시보드</h3>
            <button onclick="getDashboardData()">대시보드 데이터 조회</button>
            <div id="dashboard-data"></div>
        </div>
        
        <!-- 통합 검색 -->
        <div class="section">
            <h3>통합 검색</h3>
            <input type="text" id="searchQuery" placeholder="검색어">
            <button onclick="globalSearch()">전역 검색</button>
            <div id="search-results"></div>
        </div>
        
        <!-- 통합 알림 발송 -->
        <div class="section">
            <h3>통합 알림 발송</h3>
            <form id="notification-form">
                <input type="text" name="title" placeholder="알림 제목" required>
                <textarea name="message" placeholder="알림 내용" required></textarea>
                <select name="type">
                    <option value="EMAIL">이메일</option>
                    <option value="SMS">SMS</option>
                    <option value="PUSH">푸시</option>
                </select>
                <button type="submit">알림 발송</button>
            </form>
            <div id="notification-result"></div>
        </div>
    </div>

    <script>
        /**
         * 통합 사용자 정보 조회
         * FRONTEND_API: MicroserviceDashboard -> API_ENTRY: GET /internal/user-service/profile
         */
        function getUserProfile() {
            const userId = document.getElementById('userId').value;
            if (!userId) {
                alert('사용자 ID를 입력하세요.');
                return;
            }
            
            $.ajax({
                url: '/api/user-profile',
                method: 'GET',
                data: { userId: userId },
                success: function(data) {
                    displayUserProfile(data);
                },
                error: function(xhr, status, error) {
                    console.error('사용자 프로필 조회 실패:', error);
                }
            });
        }

        /**
         * 통합 주문 정보 조회
         * FRONTEND_API: MicroserviceDashboard -> API_ENTRY: GET /internal/order-service/details
         */
        function getOrderDetails() {
            const orderId = document.getElementById('orderId').value;
            if (!orderId) {
                alert('주문 ID를 입력하세요.');
                return;
            }
            
            $.ajax({
                url: '/api/order-details',
                method: 'GET',
                data: { orderId: orderId },
                success: function(data) {
                    displayOrderDetails(data);
                },
                error: function(xhr, status, error) {
                    console.error('주문 상세 조회 실패:', error);
                }
            });
        }

        /**
         * 통합 대시보드 데이터 조회
         * FRONTEND_API: MicroserviceDashboard -> API_ENTRY: GET /internal/analytics-service/dashboard
         */
        function getDashboardData() {
            $.ajax({
                url: '/api/dashboard',
                method: 'GET',
                success: function(data) {
                    displayDashboardData(data);
                },
                error: function(xhr, status, error) {
                    console.error('대시보드 데이터 조회 실패:', error);
                }
            });
        }

        /**
         * 통합 검색
         * FRONTEND_API: MicroserviceDashboard -> API_ENTRY: GET /internal/search-service/global
         */
        function globalSearch() {
            const query = document.getElementById('searchQuery').value;
            if (!query) {
                alert('검색어를 입력하세요.');
                return;
            }
            
            $.ajax({
                url: '/api/search',
                method: 'GET',
                data: { query: query },
                success: function(data) {
                    displaySearchResults(data);
                },
                error: function(xhr, status, error) {
                    console.error('검색 실패:', error);
                }
            });
        }

        /**
         * 통합 알림 발송
         * FRONTEND_API: MicroserviceDashboard -> API_ENTRY: POST /internal/notification-service/send
         */
        $('#notification-form').on('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                title: $(this).find('input[name="title"]').val(),
                message: $(this).find('textarea[name="message"]').val(),
                type: $(this).find('select[name="type"]').val()
            };
            
            $.ajax({
                url: '/api/notify',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(formData),
                success: function(data) {
                    displayNotificationResult(data);
                },
                error: function(xhr, status, error) {
                    console.error('알림 발송 실패:', error);
                }
            });
        });

        // 화면 표시 함수들
        function displayUserProfile(profile) {
            let html = '<div class="user-profile">';
            html += '<h4>사용자 프로필</h4>';
            html += '<p>ID: ' + profile.userId + '</p>';
            html += '<p>이름: ' + profile.name + '</p>';
            html += '<p>이메일: ' + profile.email + '</p>';
            html += '<p>전화번호: ' + profile.phone + '</p>';
            html += '<p>주소: ' + profile.address + '</p>';
            html += '<p>총 주문 수: ' + profile.totalOrders + '</p>';
            html += '<p>총 구매 금액: ' + profile.totalSpent + '</p>';
            html += '</div>';
            document.getElementById('user-profile').innerHTML = html;
        }

        function displayOrderDetails(order) {
            let html = '<div class="order-details">';
            html += '<h4>주문 상세</h4>';
            html += '<p>주문 ID: ' + order.orderId + '</p>';
            html += '<p>상품명: ' + order.productName + '</p>';
            html += '<p>가격: ' + order.price + '</p>';
            html += '<p>주문자: ' + order.userName + '</p>';
            html += '<p>주문일: ' + order.orderDate + '</p>';
            html += '</div>';
            document.getElementById('order-details').innerHTML = html;
        }

        function displayDashboardData(dashboard) {
            let html = '<div class="dashboard-data">';
            html += '<h4>대시보드 데이터</h4>';
            html += '<p>총 사용자 수: ' + dashboard.totalUsers + '</p>';
            html += '<p>총 상품 수: ' + dashboard.totalProducts + '</p>';
            html += '<p>총 주문 수: ' + dashboard.totalOrders + '</p>';
            html += '<p>총 매출: ' + dashboard.totalRevenue + '</p>';
            html += '<p>읽지 않은 알림: ' + dashboard.unreadNotifications + '</p>';
            html += '</div>';
            document.getElementById('dashboard-data').innerHTML = html;
        }

        function displaySearchResults(results) {
            let html = '<div class="search-results">';
            html += '<h4>검색 결과</h4>';
            
            if (results.users && results.users.length > 0) {
                html += '<h5>사용자</h5><ul>';
                results.users.forEach(function(user) {
                    html += '<li>' + user.name + ' - ' + user.email + '</li>';
                });
                html += '</ul>';
            }
            
            if (results.products && results.products.length > 0) {
                html += '<h5>상품</h5><ul>';
                results.products.forEach(function(product) {
                    html += '<li>' + product.name + ' - ' + product.price + '</li>';
                });
                html += '</ul>';
            }
            
            if (results.orders && results.orders.length > 0) {
                html += '<h5>주문</h5><ul>';
                results.orders.forEach(function(order) {
                    html += '<li>' + order.orderId + ' - ' + order.status + '</li>';
                });
                html += '</ul>';
            }
            
            html += '</div>';
            document.getElementById('search-results').innerHTML = html;
        }

        function displayNotificationResult(result) {
            let html = '<div class="notification-result">';
            html += '<h4>알림 발송 결과</h4>';
            html += '<p>상태: ' + result.status + '</p>';
            html += '<p>발송 ID: ' + result.notificationId + '</p>';
            html += '<p>발송 시간: ' + result.sentAt + '</p>';
            html += '</div>';
            document.getElementById('notification-result').innerHTML = html;
        }

        // 페이지 로드 시 초기 데이터 조회
        $(document).ready(function() {
            getDashboardData();
        });
    </script>
</body>
</html>
