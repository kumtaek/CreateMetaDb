<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
<%@ taglib prefix="fn" uri="http://java.sun.com/jsp/jstl/functions" %>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>사용자 목록</title>
    <style>
        .search-form { margin: 20px 0; padding: 15px; background: #f5f5f5; }
        .user-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .user-table th, .user-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .user-table th { background-color: #4CAF50; color: white; }
        .status-active { color: green; font-weight: bold; }
        .status-inactive { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <h1>사용자 목록</h1>
    
    <!-- 검색 폼 -->
    <div class="search-form">
        <form method="get" action="<c:url value='/user/list'/>">
            <label>이름: <input type="text" name="name" value="${searchParams.name}" placeholder="이름으로 검색"></label>
            <label>이메일: <input type="text" name="email" value="${searchParams.email}" placeholder="이메일로 검색"></label>
            <label>상태: 
                <select name="status">
                    <option value="">전체</option>
                    <option value="ACTIVE" ${searchParams.status == 'ACTIVE' ? 'selected' : ''}>활성</option>
                    <option value="INACTIVE" ${searchParams.status == 'INACTIVE' ? 'selected' : ''}>비활성</option>
                </select>
            </label>
            <button type="submit">검색</button>
        </form>
    </div>
    
    <!-- 통계 정보 표시 -->
    <c:if test="${not empty statistics}">
        <div class="statistics-panel" style="background: #e8f5e8; padding: 15px; margin: 20px 0; border-radius: 5px;">
            <h3>📊 사용자 통계</h3>
            <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                <div><strong>총 사용자:</strong> ${statistics.totalCount}명</div>
                <div><strong>활성 사용자:</strong> ${statistics.activeCount}명</div>
                <div><strong>비활성 사용자:</strong> ${statistics.inactiveCount}명</div>
                <div><strong>평균 나이:</strong> ${statistics.averageAge}세</div>
            </div>
        </div>
    </c:if>

    <!-- 사용자 목록 테이블 -->
    <table class="user-table">
        <thead>
            <tr>
                <th>ID</th>
                <th>사용자명</th>
                <th>이메일</th>
                <th>이름</th>
                <th>나이/연령대</th>
                <th>상태</th>
                <th>사용자 유형</th>
                <th>전화번호</th>
                <th>주소</th>
                <th>계정 생성일</th>
                <th>계정 나이</th>
                <th>마지막 업데이트</th>
            </tr>
        </thead>
        <tbody>
            <c:choose>
                <c:when test="${empty users}">
                    <tr>
                        <td colspan="12" style="text-align: center; padding: 20px;">
                            <div style="color: #666;">
                                <i>🔍 검색 결과가 없습니다.</i><br>
                                <small>다른 검색 조건을 시도해보세요.</small>
                            </div>
                        </td>
                    </tr>
                </c:when>
                <c:otherwise>
                    <c:forEach var="user" items="${users}">
                        <tr style="${user.active ? 'background-color: #f8fff8;' : 'background-color: #fff8f8;'}">
                            <td><strong>#${user.id}</strong></td>
                            <td>
                                <div style="display: flex; align-items: center; gap: 5px;">
                                    ${user.username}
                                    <c:if test="${user.admin}">
                                        <span style="background: #ff6b6b; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">ADMIN</span>
                                    </c:if>
                                    <c:if test="${user.premium}">
                                        <span style="background: #4ecdc4; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">PREMIUM</span>
                                    </c:if>
                                </div>
                            </td>
                            <td>
                                <div style="display: flex; align-items: center; gap: 5px;">
                                    ${user.maskedEmail}
                                    <c:if test="${user.hasValidEmail}">
                                        <span style="color: green;" title="유효한 이메일">✓</span>
                                    </c:if>
                                </div>
                            </td>
                            <td><strong>${user.displayName}</strong></td>
                            <td>
                                <div>
                                    <strong>${user.age}세</strong>
                                    <br><small style="color: #666;">${user.ageGroup}</small>
                                </div>
                            </td>
                            <td>
                                <c:choose>
                                    <c:when test="${user.status == 'ACTIVE'}">
                                        <span class="status-active" style="background: #4CAF50; color: white; padding: 4px 8px; border-radius: 4px;">
                                            ${user.statusDisplayName}
                                        </span>
                                    </c:when>
                                    <c:when test="${user.status == 'SUSPENDED'}">
                                        <span style="background: #ff9800; color: white; padding: 4px 8px; border-radius: 4px;">
                                            ${user.statusDisplayName}
                                        </span>
                                    </c:when>
                                    <c:otherwise>
                                        <span class="status-inactive" style="background: #f44336; color: white; padding: 4px 8px; border-radius: 4px;">
                                            ${user.statusDisplayName}
                                        </span>
                                    </c:otherwise>
                                </c:choose>
                            </td>
                            <td>
                                <span style="background: #e3f2fd; color: #1976d2; padding: 4px 8px; border-radius: 4px;">
                                    ${user.userTypeDisplayName}
                                </span>
                            </td>
                            <td>
                                <div style="display: flex; align-items: center; gap: 5px;">
                                    ${user.maskedPhone}
                                    <c:if test="${user.hasValidPhone}">
                                        <span style="color: green;" title="유효한 전화번호">✓</span>
                                    </c:if>
                                </div>
                            </td>
                            <td>
                                <c:choose>
                                    <c:when test="${not empty user.address}">
                                        <span title="${user.address}">${fn:substring(user.address, 0, 20)}${fn:length(user.address) > 20 ? '...' : ''}</span>
                                    </c:when>
                                    <c:otherwise>
                                        <span style="color: #999;">주소 없음</span>
                                    </c:otherwise>
                                </c:choose>
                            </td>
                            <td>
                                <div>
                                    <fmt:formatDate value="${user.createdDate}" pattern="yyyy-MM-dd"/>
                                    <br><small style="color: #666;"><fmt:formatDate value="${user.createdDate}" pattern="HH:mm"/></small>
                                </div>
                            </td>
                            <td>
                                <div style="text-align: center;">
                                    <strong>${user.accountAgeInDays}일</strong>
                                    <br><small style="color: #666;">계정 나이</small>
                                </div>
                            </td>
                            <td>
                                <div style="font-size: 12px; color: #666;">
                                    ${user.lastUpdateInfo}
                                </div>
                            </td>
                        </tr>
                    </c:forEach>
                </c:otherwise>
            </c:choose>
        </tbody>
    </table>
    
    <!-- 페이징 정보 -->
    <c:if test="${not empty users}">
        <div class="pagination-info" style="margin: 20px 0; text-align: center; color: #666;">
            <div>
                <strong>총 ${totalUsers}명</strong> 중 
                <strong>${(currentPage * pageSize) + 1}-${Math.min((currentPage + 1) * pageSize, totalUsers)}번째</strong> 사용자 표시
            </div>
            <div style="margin-top: 10px;">
                <c:if test="${currentPage > 0}">
                    <a href="?page=${currentPage - 1}&size=${pageSize}&name=${searchParams.name}&email=${searchParams.email}&status=${searchParams.status}" 
                       style="margin-right: 10px; padding: 5px 10px; background: #4CAF50; color: white; text-decoration: none; border-radius: 3px;">
                        ← 이전
                    </a>
                </c:if>
                <span style="margin: 0 10px;">페이지 ${currentPage + 1}</span>
                <c:if test="${(currentPage + 1) * pageSize < totalUsers}">
                    <a href="?page=${currentPage + 1}&size=${pageSize}&name=${searchParams.name}&email=${searchParams.email}&status=${searchParams.status}" 
                       style="margin-left: 10px; padding: 5px 10px; background: #4CAF50; color: white; text-decoration: none; border-radius: 3px;">
                        다음 →
                    </a>
                </c:if>
            </div>
        </div>
    </c:if>
    
    <!-- 고급 검색 링크 -->
    <div style="margin: 20px 0;">
        <a href="<c:url value='/user/advanced-search'/>">고급 검색</a>
    </div>
    
    <script>
        // 클라이언트 사이드 검증
        function validateSearch() {
            var name = document.querySelector('input[name="name"]').value;
            var email = document.querySelector('input[name="email"]').value;
            
            if (name.length > 0 && name.length < 2) {
                alert('이름은 2자 이상 입력해주세요.');
                return false;
            }
            
            if (email.length > 0 && !email.includes('@')) {
                alert('올바른 이메일 형식을 입력해주세요.');
                return false;
            }
            
            return true;
        }
        
        // 폼 제출 시 검증
        document.querySelector('form').addEventListener('submit', function(e) {
            if (!validateSearch()) {
                e.preventDefault();
            }
        });
    </script>
</body>
</html>

