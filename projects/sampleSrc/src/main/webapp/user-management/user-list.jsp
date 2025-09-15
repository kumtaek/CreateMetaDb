<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
<%@ taglib prefix="fn" uri="http://java.sun.com/jsp/jstl/functions" %>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>사용자 관리 시스템</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: #4CAF50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .search-form { background: #e8f5e8; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }
        .btn:hover { background: #45a049; }
        .btn-secondary { background: #6c757d; }
        .btn-secondary:hover { background: #5a6268; }
        .user-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .user-table th, .user-table td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        .user-table th { background-color: #4CAF50; color: white; }
        .user-table tr:nth-child(even) { background-color: #f2f2f2; }
        .user-table tr:hover { background-color: #f5f5f5; }
        .status-active { color: green; font-weight: bold; }
        .status-inactive { color: red; font-weight: bold; }
        .status-pending { color: orange; font-weight: bold; }
        .actions { display: flex; gap: 5px; }
        .actions a { padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px; }
        .edit-link { background: #007bff; color: white; }
        .delete-link { background: #dc3545; color: white; }
        .view-link { background: #28a745; color: white; }
        .pagination { text-align: center; margin: 20px 0; }
        .pagination a { padding: 8px 16px; margin: 0 4px; text-decoration: none; border: 1px solid #ddd; border-radius: 4px; }
        .pagination a:hover { background-color: #4CAF50; color: white; }
        .pagination .current { background-color: #4CAF50; color: white; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-card { background: #e3f2fd; padding: 15px; border-radius: 5px; text-align: center; flex: 1; }
        .stat-number { font-size: 24px; font-weight: bold; color: #1976d2; }
        .stat-label { color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>사용자 관리 시스템</h1>
            <p>UserManagementServlet을 통한 사용자 관리</p>
        </div>

        <!-- 통계 정보 -->
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">${totalUsers}</div>
                <div class="stat-label">총 사용자</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${activeUsers}</div>
                <div class="stat-label">활성 사용자</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${newUsersToday}</div>
                <div class="stat-label">오늘 가입</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${premiumUsers}</div>
                <div class="stat-label">프리미엄 사용자</div>
            </div>
        </div>

        <!-- 검색 폼 -->
        <div class="search-form">
            <h3>사용자 검색</h3>
            <form method="get" action="<c:url value='/user/*'/>">
                <div class="form-group">
                    <label for="searchType">검색 유형:</label>
                    <select name="searchType" id="searchType">
                        <option value="all">전체</option>
                        <option value="username">사용자명</option>
                        <option value="email">이메일</option>
                        <option value="name">실명</option>
                        <option value="phone">전화번호</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="searchKeyword">검색어:</label>
                    <input type="text" name="searchKeyword" id="searchKeyword" placeholder="검색어를 입력하세요">
                </div>
                <div class="form-group">
                    <label for="status">상태:</label>
                    <select name="status" id="status">
                        <option value="">전체</option>
                        <option value="ACTIVE">활성</option>
                        <option value="INACTIVE">비활성</option>
                        <option value="PENDING">대기</option>
                        <option value="SUSPENDED">정지</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="userType">사용자 유형:</label>
                    <select name="userType" id="userType">
                        <option value="">전체</option>
                        <option value="NORMAL">일반</option>
                        <option value="PREMIUM">프리미엄</option>
                        <option value="ADMIN">관리자</option>
                        <option value="GUEST">게스트</option>
                    </select>
                </div>
                <button type="submit" class="btn">검색</button>
                <button type="button" class="btn btn-secondary" onclick="clearForm()">초기화</button>
                <a href="<c:url value='/user/*?action=create'/>" class="btn btn-secondary">새 사용자 추가</a>
            </form>
        </div>

        <!-- 사용자 목록 테이블 -->
        <table class="user-table">
            <thead>
                <tr>
                    <th>사용자ID</th>
                    <th>사용자명</th>
                    <th>실명</th>
                    <th>이메일</th>
                    <th>전화번호</th>
                    <th>상태</th>
                    <th>유형</th>
                    <th>가입일</th>
                    <th>마지막 로그인</th>
                    <th>작업</th>
                </tr>
            </thead>
            <tbody>
                <c:choose>
                    <c:when test="${empty users}">
                        <tr>
                            <td colspan="10" style="text-align: center; padding: 40px;">
                                <p style="color: #666; font-size: 16px;">검색 결과가 없습니다.</p>
                                <p style="color: #999;">다른 검색 조건을 시도해보세요.</p>
                            </td>
                        </tr>
                    </c:when>
                    <c:otherwise>
                        <c:forEach var="user" items="${users}">
                            <tr>
                                <td><strong>#${user.userId}</strong></td>
                                <td>
                                    <div style="display: flex; align-items: center; gap: 5px;">
                                        ${user.username}
                                        <c:if test="${user.isAdmin}">
                                            <span style="background: #ff6b6b; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">ADMIN</span>
                                        </c:if>
                                        <c:if test="${user.isPremium}">
                                            <span style="background: #4ecdc4; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">PREMIUM</span>
                                        </c:if>
                                    </div>
                                </td>
                                <td><strong>${user.fullName}</strong></td>
                                <td>
                                    <div style="display: flex; align-items: center; gap: 5px;">
                                        ${user.email}
                                        <c:if test="${user.emailVerified}">
                                            <span style="color: green;" title="이메일 인증 완료">✓</span>
                                        </c:if>
                                    </div>
                                </td>
                                <td>
                                    <div style="display: flex; align-items: center; gap: 5px;">
                                        ${user.phone}
                                        <c:if test="${user.phoneVerified}">
                                            <span style="color: green;" title="전화번호 인증 완료">✓</span>
                                        </c:if>
                                    </div>
                                </td>
                                <td>
                                    <c:choose>
                                        <c:when test="${user.status == 'ACTIVE'}">
                                            <span class="status-active">활성</span>
                                        </c:when>
                                        <c:when test="${user.status == 'INACTIVE'}">
                                            <span class="status-inactive">비활성</span>
                                        </c:when>
                                        <c:when test="${user.status == 'PENDING'}">
                                            <span class="status-pending">대기</span>
                                        </c:when>
                                        <c:when test="${user.status == 'SUSPENDED'}">
                                            <span style="color: red;">정지</span>
                                        </c:when>
                                        <c:otherwise>
                                            <span style="color: #666;">알 수 없음</span>
                                        </c:otherwise>
                                    </c:choose>
                                </td>
                                <td>
                                    <span style="background: #e3f2fd; color: #1976d2; padding: 4px 8px; border-radius: 4px;">
                                        <c:choose>
                                            <c:when test="${user.userType == 'NORMAL'}">일반</c:when>
                                            <c:when test="${user.userType == 'PREMIUM'}">프리미엄</c:when>
                                            <c:when test="${user.userType == 'ADMIN'}">관리자</c:when>
                                            <c:when test="${user.userType == 'GUEST'}">게스트</c:when>
                                            <c:otherwise>${user.userType}</c:otherwise>
                                        </c:choose>
                                    </span>
                                </td>
                                <td>
                                    <fmt:formatDate value="${user.createdDate}" pattern="yyyy-MM-dd"/>
                                    <br><small style="color: #666;"><fmt:formatDate value="${user.createdDate}" pattern="HH:mm"/></small>
                                </td>
                                <td>
                                    <c:choose>
                                        <c:when test="${not empty user.lastLoginDate}">
                                            <fmt:formatDate value="${user.lastLoginDate}" pattern="yyyy-MM-dd HH:mm"/>
                                        </c:when>
                                        <c:otherwise>
                                            <span style="color: #999;">로그인 기록 없음</span>
                                        </c:otherwise>
                                    </c:choose>
                                </td>
                                <td>
                                    <div class="actions">
                                        <a href="<c:url value='/user/*?action=view&userId=${user.userId}'/>" class="view-link">보기</a>
                                        <a href="<c:url value='/user/*?action=edit&userId=${user.userId}'/>" class="edit-link">수정</a>
                                        <a href="<c:url value='/user/*?action=delete&userId=${user.userId}'/>" class="delete-link" onclick="return confirm('정말 삭제하시겠습니까?')">삭제</a>
                                    </div>
                                </td>
                            </tr>
                        </c:forEach>
                    </c:otherwise>
                </c:choose>
            </tbody>
        </table>

        <!-- 페이징 -->
        <c:if test="${not empty users}">
            <div class="pagination">
                <c:if test="${currentPage > 1}">
                    <a href="?page=${currentPage - 1}&pageSize=${pageSize}&searchType=${searchType}&searchKeyword=${searchKeyword}&status=${status}&userType=${userType}">이전</a>
                </c:if>
                
                <c:forEach begin="1" end="${totalPages}" var="pageNum">
                    <c:choose>
                        <c:when test="${pageNum == currentPage}">
                            <span class="current">${pageNum}</span>
                        </c:when>
                        <c:otherwise>
                            <a href="?page=${pageNum}&pageSize=${pageSize}&searchType=${searchType}&searchKeyword=${searchKeyword}&status=${status}&userType=${userType}">${pageNum}</a>
                        </c:otherwise>
                    </c:choose>
                </c:forEach>
                
                <c:if test="${currentPage < totalPages}">
                    <a href="?page=${currentPage + 1}&pageSize=${pageSize}&searchType=${searchType}&searchKeyword=${searchKeyword}&status=${status}&userType=${userType}">다음</a>
                </c:if>
            </div>
            
            <div style="text-align: center; margin: 20px 0; color: #666;">
                총 ${totalUsers}명 중 ${(currentPage - 1) * pageSize + 1}-${Math.min(currentPage * pageSize, totalUsers)}번째 사용자 표시
            </div>
        </c:if>

        <!-- API 테스트 링크 -->
        <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 5px;">
            <h3>API 테스트</h3>
            <p>다음 링크들을 통해 Servlet API를 테스트할 수 있습니다:</p>
            <ul>
                <li><a href="<c:url value='/user/*'/>" target="_blank">GET /user/* - 사용자 목록 조회</a></li>
                <li><a href="<c:url value='/api/v1/users'/>" target="_blank">GET /api/v1/users - REST API 사용자 목록</a></li>
                <li><a href="<c:url value='/admin/user-management'/>" target="_blank">GET /admin/user-management - 관리자 사용자 관리</a></li>
            </ul>
        </div>
    </div>

    <script>
        function clearForm() {
            document.getElementById('searchKeyword').value = '';
            document.getElementById('status').value = '';
            document.getElementById('userType').value = '';
            document.getElementById('searchType').value = 'all';
        }

        // 폼 검증
        document.querySelector('form').addEventListener('submit', function(e) {
            var searchKeyword = document.getElementById('searchKeyword').value.trim();
            var searchType = document.getElementById('searchType').value;
            
            if (searchType !== 'all' && searchKeyword.length < 2) {
                alert('검색어는 2자 이상 입력해주세요.');
                e.preventDefault();
                return false;
            }
            
            return true;
        });

        // 실시간 검색 결과 하이라이트
        function highlightSearchResults() {
            var searchKeyword = '${searchKeyword}';
            if (searchKeyword && searchKeyword.length > 0) {
                var cells = document.querySelectorAll('.user-table td');
                cells.forEach(function(cell) {
                    if (cell.textContent.toLowerCase().includes(searchKeyword.toLowerCase())) {
                        cell.style.backgroundColor = '#fff3cd';
                    }
                });
            }
        }

        // 페이지 로드 시 실행
        document.addEventListener('DOMContentLoaded', function() {
            highlightSearchResults();
        });
    </script>
</body>
</html>
