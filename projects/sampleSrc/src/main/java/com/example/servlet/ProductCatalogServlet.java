package com.example.servlet;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;

/**
 * HttpServlet을 상속받은 상품 카탈로그 관리 Servlet
 * @WebServlet 어노테이션 없이 상속만으로 구현된 레거시 스타일
 * web.xml에서 매핑을 통해 URL 패턴을 정의해야 함
 */
public class ProductCatalogServlet extends HttpServlet {
    
    private static final long serialVersionUID = 1L;
    
    // 상품 데이터를 시뮬레이션하기 위한 간단한 리스트
    private List<Product> products;
    
    @Override
    public void init() throws ServletException {
        super.init();
        // Servlet 초기화 시 상품 데이터 초기화
        initializeProductData();
        System.out.println("ProductCatalogServlet 초기화 완료");
    }
    
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("text/html; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        String action = request.getParameter("action");
        
        out.println("<!DOCTYPE html>");
        out.println("<html><head><title>상품 카탈로그</title></head><body>");
        out.println("<h1>상품 카탈로그 관리</h1>");
        
        if ("list".equals(action)) {
            displayProductList(out);
        } else if ("detail".equals(action)) {
            String productId = request.getParameter("id");
            displayProductDetail(out, productId);
        } else {
            displayMainMenu(out);
        }
        
        out.println("</body></html>");
        out.flush();
    }
    
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("text/html; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        String action = request.getParameter("action");
        
        out.println("<!DOCTYPE html>");
        out.println("<html><head><title>상품 처리 결과</title></head><body>");
        out.println("<h1>상품 처리 결과</h1>");
        
        if ("add".equals(action)) {
            addProduct(request, out);
        } else if ("update".equals(action)) {
            updateProduct(request, out);
        } else if ("delete".equals(action)) {
            deleteProduct(request, out);
        } else {
            out.println("<p>알 수 없는 작업입니다.</p>");
        }
        
        out.println("<br><a href='?action=list'>상품 목록으로 돌아가기</a>");
        out.println("</body></html>");
        out.flush();
    }
    
    @Override
    protected void doPut(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        // PUT 메서드로 상품 정보 수정
        String productId = request.getParameter("id");
        String name = request.getParameter("name");
        String price = request.getParameter("price");
        
        out.println("{");
        out.println("  \"status\": \"success\",");
        out.println("  \"method\": \"PUT\",");
        out.println("  \"productId\": \"" + productId + "\",");
        out.println("  \"name\": \"" + name + "\",");
        out.println("  \"price\": \"" + price + "\",");
        out.println("  \"message\": \"상품 정보가 REST API로 수정되었습니다.\"");
        out.println("}");
        
        out.flush();
    }
    
    @Override
    protected void doDelete(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        
        String productId = request.getParameter("id");
        
        out.println("{");
        out.println("  \"status\": \"success\",");
        out.println("  \"method\": \"DELETE\",");
        out.println("  \"productId\": \"" + productId + "\",");
        out.println("  \"message\": \"상품이 REST API로 삭제되었습니다.\"");
        out.println("}");
        
        out.flush();
    }
    
    private void initializeProductData() {
        products = new ArrayList<>();
        products.add(new Product("P001", "노트북", 1500000, "전자제품"));
        products.add(new Product("P002", "마우스", 50000, "전자제품"));
        products.add(new Product("P003", "키보드", 80000, "전자제품"));
        products.add(new Product("P004", "모니터", 300000, "전자제품"));
        products.add(new Product("P005", "책상", 200000, "가구"));
    }
    
    private void displayMainMenu(PrintWriter out) {
        out.println("<h2>메인 메뉴</h2>");
        out.println("<ul>");
        out.println("<li><a href='?action=list'>상품 목록 보기</a></li>");
        out.println("<li><a href='add-product.html'>새 상품 추가</a></li>");
        out.println("</ul>");
    }
    
    private void displayProductList(PrintWriter out) {
        out.println("<h2>상품 목록</h2>");
        out.println("<table border='1' style='border-collapse: collapse; width: 100%;'>");
        out.println("<tr><th>상품ID</th><th>상품명</th><th>가격</th><th>카테고리</th><th>작업</th></tr>");
        
        for (Product product : products) {
            out.println("<tr>");
            out.println("<td>" + product.getId() + "</td>");
            out.println("<td>" + product.getName() + "</td>");
            out.println("<td>" + String.format("%,d원", product.getPrice()) + "</td>");
            out.println("<td>" + product.getCategory() + "</td>");
            out.println("<td>");
            out.println("<a href='?action=detail&id=" + product.getId() + "'>상세보기</a> | ");
            out.println("<a href='edit-product.html?id=" + product.getId() + "'>수정</a>");
            out.println("</td>");
            out.println("</tr>");
        }
        
        out.println("</table>");
    }
    
    private void displayProductDetail(PrintWriter out, String productId) {
        Product product = findProductById(productId);
        
        if (product != null) {
            out.println("<h2>상품 상세 정보</h2>");
            out.println("<table border='1' style='border-collapse: collapse;'>");
            out.println("<tr><td><strong>상품ID:</strong></td><td>" + product.getId() + "</td></tr>");
            out.println("<tr><td><strong>상품명:</strong></td><td>" + product.getName() + "</td></tr>");
            out.println("<tr><td><strong>가격:</strong></td><td>" + String.format("%,d원", product.getPrice()) + "</td></tr>");
            out.println("<tr><td><strong>카테고리:</strong></td><td>" + product.getCategory() + "</td></tr>");
            out.println("</table>");
        } else {
            out.println("<p>해당 상품을 찾을 수 없습니다.</p>");
        }
    }
    
    private void addProduct(HttpServletRequest request, PrintWriter out) {
        String id = request.getParameter("id");
        String name = request.getParameter("name");
        String priceStr = request.getParameter("price");
        String category = request.getParameter("category");
        
        try {
            int price = Integer.parseInt(priceStr);
            Product newProduct = new Product(id, name, price, category);
            products.add(newProduct);
            out.println("<p>새 상품이 성공적으로 추가되었습니다.</p>");
        } catch (NumberFormatException e) {
            out.println("<p>가격은 숫자로 입력해주세요.</p>");
        }
    }
    
    private void updateProduct(HttpServletRequest request, PrintWriter out) {
        String id = request.getParameter("id");
        String name = request.getParameter("name");
        String priceStr = request.getParameter("price");
        String category = request.getParameter("category");
        
        Product product = findProductById(id);
        if (product != null) {
            try {
                int price = Integer.parseInt(priceStr);
                product.setName(name);
                product.setPrice(price);
                product.setCategory(category);
                out.println("<p>상품 정보가 성공적으로 수정되었습니다.</p>");
            } catch (NumberFormatException e) {
                out.println("<p>가격은 숫자로 입력해주세요.</p>");
            }
        } else {
            out.println("<p>해당 상품을 찾을 수 없습니다.</p>");
        }
    }
    
    private void deleteProduct(HttpServletRequest request, PrintWriter out) {
        String id = request.getParameter("id");
        Product product = findProductById(id);
        
        if (product != null) {
            products.remove(product);
            out.println("<p>상품이 성공적으로 삭제되었습니다.</p>");
        } else {
            out.println("<p>해당 상품을 찾을 수 없습니다.</p>");
        }
    }
    
    private Product findProductById(String id) {
        for (Product product : products) {
            if (product.getId().equals(id)) {
                return product;
            }
        }
        return null;
    }
    
    // 간단한 Product 클래스
    private static class Product {
        private String id;
        private String name;
        private int price;
        private String category;
        
        public Product(String id, String name, int price, String category) {
            this.id = id;
            this.name = name;
            this.price = price;
            this.category = category;
        }
        
        // Getters and Setters
        public String getId() { return id; }
        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public int getPrice() { return price; }
        public void setPrice(int price) { this.price = price; }
        public String getCategory() { return category; }
        public void setCategory(String category) { this.category = category; }
    }
}
