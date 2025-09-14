<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>상품 검색 결과</title>
</head>
<body>
    <h1>상품 검색 결과</h1>
    
    <!-- 검색 조건 표시 -->
    <div>
        <h3>검색 조건</h3>
        <c:if test="${not empty searchParams.categoryId}">
            <p>카테고리: ${searchParams.categoryId}</p>
        </c:if>
        <c:if test="${not empty searchParams.minPrice}">
            <p>최소 가격: ${searchParams.minPrice}</p>
        </c:if>
        <c:if test="${not empty searchParams.maxPrice}">
            <p>최대 가격: ${searchParams.maxPrice}</p>
        </c:if>
        <c:if test="${not empty searchParams.minStock}">
            <p>최소 재고: ${searchParams.minStock}</p>
        </c:if>
        <c:if test="${not empty searchParams.maxStock}">
            <p>최대 재고: ${searchParams.maxStock}</p>
        </c:if>
    </div>
    
    <!-- 검색 결과 테이블 -->
    <table border="1">
        <thead>
            <tr>
                <th>상품ID</th>
                <th>상품명</th>
                <th>설명</th>
                <th>가격</th>
                <th>재고</th>
                <th>상태</th>
                <th>카테고리</th>
                <th>브랜드</th>
            </tr>
        </thead>
        <tbody>
            <c:forEach var="product" items="${products}">
                <tr>
                    <td>${product.productId}</td>
                    <td>${product.productName}</td>
                    <td>${product.description}</td>
                    <td>${product.price}</td>
                    <td>${product.stockQuantity}</td>
                    <td>${product.status}</td>
                    <td>${product.categoryId}</td>
                    <td>${product.brandId}</td>
                </tr>
            </c:forEach>
        </tbody>
    </table>
    
    <c:if test="${empty products}">
        <p>검색 조건에 맞는 상품이 없습니다.</p>
    </c:if>
    
    <a href="/product/list">목록으로</a>
</body>
</html>
