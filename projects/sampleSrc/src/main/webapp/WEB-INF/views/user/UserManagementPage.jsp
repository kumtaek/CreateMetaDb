<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>사용자 관리 페이지</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
    <h2>사용자 관리 페이지</h2>
    
    <div id="user-management-container">
        <!-- 사용자 목록 조회 -->
        <div class="section">
            <h3>사용자 목록</h3>
            <button onclick="fetchUsers()">사용자 조회</button>
            <div id="users-list"></div>
        </div>
        
        <!-- 사용자 상세 조회 -->
        <div class="section">
            <h3>사용자 상세</h3>
            <input type="number" id="userId" placeholder="사용자 ID">
            <button onclick="fetchUserDetail()">상세 조회</button>
            <div id="user-detail"></div>
        </div>
        
        <!-- 사용자 생성 -->
        <div class="section">
            <h3>사용자 생성</h3>
            <form id="create-user-form">
                <input type="text" name="name" placeholder="이름" required>
                <input type="email" name="email" placeholder="이메일" required>
                <button type="submit">사용자 생성</button>
            </form>
        </div>
        
        <!-- 사용자 수정 -->
        <div class="section">
            <h3>사용자 수정</h3>
            <form id="update-user-form">
                <input type="number" name="id" placeholder="사용자 ID" required>
                <input type="text" name="name" placeholder="이름" required>
                <input type="email" name="email" placeholder="이메일" required>
                <button type="submit">사용자 수정</button>
            </form>
        </div>
        
        <!-- 사용자 삭제 -->
        <div class="section">
            <h3>사용자 삭제</h3>
            <input type="number" id="deleteUserId" placeholder="사용자 ID">
            <button onclick="deleteUser()">사용자 삭제</button>
        </div>
        
        <!-- 사용자 통계 -->
        <div class="section">
            <h3>사용자 통계</h3>
            <button onclick="fetchUserStatistics()">통계 조회</button>
            <div id="user-statistics"></div>
        </div>
    </div>

    <script>
        /**
         * 사용자 목록 조회
         * FRONTEND_API: UserManagementPage -> API_ENTRY: GET /api/user-management/users
         */
        function fetchUsers() {
            $.ajax({
                url: '/api/user-management/users',
                method: 'GET',
                success: function(data) {
                    displayUsers(data);
                },
                error: function(xhr, status, error) {
                    console.error('사용자 조회 실패:', error);
                }
            });
        }

        /**
         * 사용자 상세 조회
         * FRONTEND_API: UserManagementPage -> API_ENTRY: GET /api/user-management/users/{id}
         */
        function fetchUserDetail() {
            const userId = document.getElementById('userId').value;
            if (!userId) {
                alert('사용자 ID를 입력하세요.');
                return;
            }
            
            $.ajax({
                url: '/api/user-management/users/' + userId,
                method: 'GET',
                success: function(data) {
                    displayUserDetail(data);
                },
                error: function(xhr, status, error) {
                    console.error('사용자 상세 조회 실패:', error);
                }
            });
        }

        /**
         * 사용자 생성
         * FRONTEND_API: UserManagementPage -> API_ENTRY: POST /api/user-management/users
         */
        $('#create-user-form').on('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                name: $(this).find('input[name="name"]').val(),
                email: $(this).find('input[name="email"]').val()
            };
            
            $.ajax({
                url: '/api/user-management/users',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(formData),
                success: function(data) {
                    alert('사용자 생성 성공');
                    fetchUsers(); // 목록 새로고침
                },
                error: function(xhr, status, error) {
                    console.error('사용자 생성 실패:', error);
                }
            });
        });

        /**
         * 사용자 수정
         * FRONTEND_API: UserManagementPage -> API_ENTRY: PUT /api/user-management/users/{id}
         */
        $('#update-user-form').on('submit', function(e) {
            e.preventDefault();
            
            const userId = $(this).find('input[name="id"]').val();
            const formData = {
                name: $(this).find('input[name="name"]').val(),
                email: $(this).find('input[name="email"]').val()
            };
            
            $.ajax({
                url: '/api/user-management/users/' + userId,
                method: 'PUT',
                contentType: 'application/json',
                data: JSON.stringify(formData),
                success: function(data) {
                    alert('사용자 수정 성공');
                    fetchUsers(); // 목록 새로고침
                },
                error: function(xhr, status, error) {
                    console.error('사용자 수정 실패:', error);
                }
            });
        });

        /**
         * 사용자 삭제
         * FRONTEND_API: UserManagementPage -> API_ENTRY: DELETE /api/user-management/users/{id}
         */
        function deleteUser() {
            const userId = document.getElementById('deleteUserId').value;
            if (!userId) {
                alert('사용자 ID를 입력하세요.');
                return;
            }
            
            if (!confirm('정말로 삭제하시겠습니까?')) {
                return;
            }
            
            $.ajax({
                url: '/api/user-management/users/' + userId,
                method: 'DELETE',
                success: function(data) {
                    alert('사용자 삭제 성공');
                    fetchUsers(); // 목록 새로고침
                },
                error: function(xhr, status, error) {
                    console.error('사용자 삭제 실패:', error);
                }
            });
        }

        /**
         * 사용자 통계 조회
         * FRONTEND_API: UserManagementPage -> API_ENTRY: GET /api/user-management/statistics
         */
        function fetchUserStatistics() {
            $.ajax({
                url: '/api/user-management/statistics',
                method: 'GET',
                success: function(data) {
                    displayUserStatistics(data);
                },
                error: function(xhr, status, error) {
                    console.error('사용자 통계 조회 실패:', error);
                }
            });
        }

        // 화면 표시 함수들
        function displayUsers(users) {
            let html = '<ul>';
            users.forEach(function(user) {
                html += '<li>' + user.name + ' - ' + user.email + '</li>';
            });
            html += '</ul>';
            document.getElementById('users-list').innerHTML = html;
        }

        function displayUserDetail(user) {
            let html = '<div>';
            html += '<p>ID: ' + user.id + '</p>';
            html += '<p>이름: ' + user.name + '</p>';
            html += '<p>이메일: ' + user.email + '</p>';
            html += '<p>상태: ' + user.status + '</p>';
            html += '</div>';
            document.getElementById('user-detail').innerHTML = html;
        }

        function displayUserStatistics(stats) {
            let html = '<div>';
            html += '<p>총 사용자 수: ' + stats.totalUsers + '</p>';
            html += '<p>활성 사용자 수: ' + stats.activeUsers + '</p>';
            html += '<p>비활성 사용자 수: ' + stats.inactiveUsers + '</p>';
            html += '</div>';
            document.getElementById('user-statistics').innerHTML = html;
        }

        // 페이지 로드 시 초기 데이터 조회
        $(document).ready(function() {
            fetchUsers();
            fetchUserStatistics();
        });
    </script>
</body>
</html>
