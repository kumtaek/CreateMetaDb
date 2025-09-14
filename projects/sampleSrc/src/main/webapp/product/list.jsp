<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>상품 목록</title>
</head>
<body>
    <h1>상품 목록</h1>
    
    <!-- 검색 폼 -->
    <form method="get" action="/product/list">
        <input type="text" name="name" placeholder="상품명" value="${searchParams.name}">
        <select name="category">
            <option value="">전체 카테고리</option>
            <option value="CAT001" ${searchParams.category == 'CAT001' ? 'selected' : ''}>전자제품</option>
            <option value="CAT002" ${searchParams.category == 'CAT002' ? 'selected' : ''}>의류</option>
            <option value="CAT003" ${searchParams.category == 'CAT003' ? 'selected' : ''}>도서</option>
        </select>
        <select name="status">
            <option value="">전체 상태</option>
            <option value="ACTIVE" ${searchParams.status == 'ACTIVE' ? 'selected' : ''}>활성</option>
            <option value="INACTIVE" ${searchParams.status == 'INACTIVE' ? 'selected' : ''}>비활성</option>
        </select>
        <button type="submit">검색</button>
    </form>
    
    <!-- 상품 목록 테이블 -->
    <table border="1">
        <thead>
            <tr>
                <th>상품ID</th>
                <th>상품명</th>
                <th>가격</th>
                <th>재고</th>
                <th>상태</th>
                <th>생성일</th>
            </tr>
        </thead>
        <tbody>
            <c:forEach var="product" items="${products}">
                <tr>
                    <td>${product.productId}</td>
                    <td>${product.productName}</td>
                    <td>${product.price}</td>
                    <td>${product.stockQuantity}</td>
                    <td>${product.status}</td>
                    <td>${product.createdDate}</td>
                </tr>
            </c:forEach>
        </tbody>
    </table>
    
    <c:if test="${empty products}">
        <p>검색된 상품이 없습니다.</p>
    </c:if>
    
    <a href="/product/search">고급 검색</a>
</body>
</html>
