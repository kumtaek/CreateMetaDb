package com.example.jpa.config;

import com.example.jpa.entity.*;
import com.example.jpa.repository.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * JPA 테스트 데이터 초기화 클래스
 * JPA Entity -> Repository -> Service -> Controller -> Vue 연결 구조 테스트를 위한 샘플 데이터 생성
 */
@Component
public class JpaTestDataInitializer implements CommandLineRunner {
    
    private final boolean enabled;
    
    @Autowired(required = false)
    private UserRepository userRepository;
    
    @Autowired(required = false)
    private ProductRepository productRepository;
    
    @Autowired(required = false)
    private CategoryRepository categoryRepository;
    
    @Autowired(required = false)
    private OrderRepository orderRepository;
    
    @Value("${app.jpa.test.sample-data.enabled:false}")
    private boolean sampleDataEnabled;
    
    @Value("${app.jpa.test.sample-data.user-count:10}")
    private int userCount;
    
    @Value("${app.jpa.test.sample-data.product-count:20}")
    private int productCount;
    
    @Value("${app.jpa.test.sample-data.order-count:30}")
    private int orderCount;
    
    private final Random random = new Random();
    
    public JpaTestDataInitializer(boolean enabled) {
        this.enabled = enabled;
    }
    
    @Override
    @Transactional
    public void run(String... args) throws Exception {
        if (!enabled || !sampleDataEnabled) {
            System.out.println("JPA 테스트 데이터 초기화가 비활성화되어 있습니다.");
            return;
        }
        
        if (userRepository == null || productRepository == null || 
            categoryRepository == null || orderRepository == null) {
            System.out.println("JPA Repository들이 초기화되지 않았습니다. 테스트 데이터 생성을 건너뜁니다.");
            return;
        }
        
        System.out.println("JPA 테스트 데이터 초기화를 시작합니다...");
        
        try {
            // 기존 데이터 확인
            if (userRepository.count() > 0) {
                System.out.println("이미 데이터가 존재합니다. 테스트 데이터 생성을 건너뜁니다.");
                return;
            }
            
            // 1. 카테고리 생성
            List<Category> categories = createCategories();
            System.out.println("카테고리 " + categories.size() + "개 생성 완료");
            
            // 2. 사용자 생성
            List<User> users = createUsers();
            System.out.println("사용자 " + users.size() + "개 생성 완료");
            
            // 3. 상품 생성
            List<Product> products = createProducts(categories);
            System.out.println("상품 " + products.size() + "개 생성 완료");
            
            // 4. 주문 생성
            List<Order> orders = createOrders(users, products);
            System.out.println("주문 " + orders.size() + "개 생성 완료");
            
            System.out.println("JPA 테스트 데이터 초기화가 완료되었습니다!");
            
        } catch (Exception e) {
            System.err.println("JPA 테스트 데이터 초기화 중 오류 발생: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    private List<Category> createCategories() {
        List<Category> categories = new ArrayList<>();
        
        String[] categoryNames = {
            "전자제품", "의류", "도서", "생활용품", "스포츠용품",
            "식품", "화장품", "가구", "자동차용품", "완구"
        };
        
        String[] categoryCodes = {
            "ELECTRONICS", "CLOTHING", "BOOKS", "HOUSEHOLD", "SPORTS",
            "FOOD", "COSMETICS", "FURNITURE", "AUTO", "TOYS"
        };
        
        for (int i = 0; i < categoryNames.length; i++) {
            Category category = new Category(categoryNames[i], categoryCodes[i]);
            category.setDescription(categoryNames[i] + " 관련 상품들");
            category.setDisplayOrder(i + 1);
            categories.add(categoryRepository.save(category));
        }
        
        return categories;
    }
    
    private List<User> createUsers() {
        List<User> users = new ArrayList<>();
        
        String[] firstNames = {"김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"};
        String[] lastNames = {"민수", "영희", "철수", "영수", "미영", "수진", "동현", "지은", "현우", "소영"};
        String[] domains = {"gmail.com", "naver.com", "daum.net", "hanmail.net", "yahoo.com"};
        
        UserStatus[] statuses = UserStatus.values();
        UserType[] types = UserType.values();
        
        for (int i = 0; i < userCount; i++) {
            String firstName = firstNames[random.nextInt(firstNames.length)];
            String lastName = lastNames[random.nextInt(lastNames.length)];
            String username = "user" + (i + 1);
            String email = username + "@" + domains[random.nextInt(domains.length)];
            
            User user = new User(username, email, "password123");
            user.setFullName(firstName + lastName);
            user.setPhoneNumber("010-" + String.format("%04d", random.nextInt(10000)) + "-" + String.format("%04d", random.nextInt(10000)));
            user.setStatus(statuses[random.nextInt(statuses.length)]);
            user.setUserType(types[random.nextInt(types.length)]);
            
            // 일부 사용자에게 로그인 이력 추가
            if (random.nextBoolean()) {
                user.setLastLoginAt(LocalDateTime.now().minusDays(random.nextInt(30)));
            }
            
            users.add(userRepository.save(user));
        }
        
        return users;
    }
    
    private List<Product> createProducts(List<Category> categories) {
        List<Product> products = new ArrayList<>();
        
        String[] productPrefixes = {
            "프리미엄", "스마트", "고급", "베이직", "프로", "울트라", "슈퍼", "메가", "미니", "맥스"
        };
        
        String[] productSuffixes = {
            "제품", "상품", "아이템", "기기", "도구", "용품", "세트", "키트", "패키지", "솔루션"
        };
        
        ProductStatus[] statuses = ProductStatus.values();
        
        for (int i = 0; i < productCount; i++) {
            String productName = productPrefixes[random.nextInt(productPrefixes.length)] + " " +
                               productSuffixes[random.nextInt(productSuffixes.length)] + " " + (i + 1);
            String productCode = "PRD" + String.format("%05d", i + 1);
            BigDecimal price = BigDecimal.valueOf(1000 + random.nextInt(99000));
            
            Product product = new Product(productName, productCode, price);
            product.setDescription(productName + "에 대한 상세 설명입니다.");
            product.setStockQuantity(random.nextInt(100) + 10);
            product.setMinStockLevel(5 + random.nextInt(15));
            product.setStatus(statuses[random.nextInt(statuses.length)]);
            
            // 랜덤하게 카테고리 할당
            if (!categories.isEmpty()) {
                product.setCategory(categories.get(random.nextInt(categories.size())));
            }
            
            products.add(productRepository.save(product));
        }
        
        return products;
    }
    
    private List<Order> createOrders(List<User> users, List<Product> products) {
        List<Order> orders = new ArrayList<>();
        
        OrderStatus[] statuses = OrderStatus.values();
        String[] paymentMethods = {"신용카드", "계좌이체", "무통장입금", "페이팔", "카카오페이"};
        String[] addresses = {
            "서울시 강남구 역삼동 123-45",
            "서울시 종로구 종로1가 67-89",
            "부산시 해운대구 우동 234-56",
            "대구시 중구 동성로 345-67",
            "인천시 연수구 송도동 456-78"
        };
        
        for (int i = 0; i < orderCount && !users.isEmpty(); i++) {
            String orderNumber = "ORD" + String.format("%08d", i + 1);
            User user = users.get(random.nextInt(users.size()));
            
            Order order = new Order(orderNumber, user);
            order.setOrderStatus(statuses[random.nextInt(statuses.length)]);
            order.setPaymentMethod(paymentMethods[random.nextInt(paymentMethods.length)]);
            order.setShippingAddress(addresses[random.nextInt(addresses.length)]);
            
            // 주문 금액 설정 (실제로는 OrderItem에서 계산되어야 함)
            BigDecimal totalAmount = BigDecimal.valueOf(10000 + random.nextInt(90000));
            order.setTotalAmount(totalAmount);
            
            // 할인 금액 (20% 확률)
            if (random.nextInt(5) == 0) {
                BigDecimal discountAmount = totalAmount.multiply(BigDecimal.valueOf(0.1));
                order.setDiscountAmount(discountAmount);
            }
            
            // 배송비 (50% 확률)
            if (random.nextBoolean()) {
                order.setShippingFee(BigDecimal.valueOf(3000));
            }
            
            // 주문일을 과거 30일 내 랜덤 설정
            order.setOrderDate(LocalDateTime.now().minusDays(random.nextInt(30)));
            
            orders.add(orderRepository.save(order));
            
            // OrderItem 생성 (간단하게 1-3개)
            createOrderItems(order, products);
        }
        
        return orders;
    }
    
    private void createOrderItems(Order order, List<Product> products) {
        if (products.isEmpty()) return;
        
        int itemCount = 1 + random.nextInt(3); // 1-3개 아이템
        
        for (int i = 0; i < itemCount; i++) {
            Product product = products.get(random.nextInt(products.size()));
            int quantity = 1 + random.nextInt(5); // 1-5개 수량
            
            OrderItem orderItem = new OrderItem(order, product, quantity, product.getPrice());
            
            // 할인 적용 (30% 확률)
            if (random.nextInt(10) < 3) {
                BigDecimal discountAmount = orderItem.getTotalPrice().multiply(BigDecimal.valueOf(0.05));
                orderItem.setDiscountAmount(discountAmount);
            }
            
            // OrderItem은 별도 Repository가 없으므로 Order의 cascade로 저장됨
            if (order.getOrderItems() == null) {
                order.setOrderItems(new ArrayList<>());
            }
            order.getOrderItems().add(orderItem);
        }
    }
}

