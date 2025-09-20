package com.example.modern;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 주문 엔티티 서비스 - ModernRestController 연결용
 * 연관관계: ModernRestController -> OrderEntityService -> OrderEntityRepository -> orders 테이블
 */
@Service
@Transactional
public class OrderEntityService {

    @Autowired
    private OrderEntityRepository orderRepository;
    
    @Autowired
    private OrderItemEntityRepository orderItemRepository;
    
    @Autowired
    private ProductEntityService productService;
    
    @Autowired
    private PaymentEntityService paymentService;
    
    @Autowired
    private ShipmentEntityService shipmentService;

    /**
     * 주문 아이템과 함께 주문 생성
     * 연관 테이블: orders, order_items, products, inventory (재고 차감), payments (INFERRED)
     */
    @Transactional
    public OrderEntity createOrderWithItems(OrderEntity orderEntity, List<OrderItemDto> orderItems) {
        // 1. 주문 기본 정보 저장
        OrderEntity savedOrder = saveOrder(orderEntity);
        
        // 2. 주문 아이템들 저장 (order_items 테이블)
        List<OrderItemEntity> savedItems = new ArrayList<>();
        for (OrderItemDto itemDto : orderItems) {
            OrderItemEntity itemEntity = createOrderItem(savedOrder.getId(), itemDto);
            savedItems.add(itemEntity);
            
            // 3. 상품 재고 차감 (products, inventory 테이블 연관)
            productService.decreaseInventory(itemDto.getProductId(), itemDto.getQuantity());
        }
        
        savedOrder.setOrderItems(savedItems);
        
        // 4. 결제 정보 생성 (INFERRED payments 테이블)
        createPaymentRecord(savedOrder);
        
        // 5. 배송 정보 생성 (INFERRED shipments 테이블)
        createShipmentRecord(savedOrder);
        
        return savedOrder;
    }

    /**
     * 주문 상태 업데이트
     * 연관 테이블: orders, shipments, payments
     */
    public OrderEntity updateOrderStatus(Long orderId, String newStatus) {
        OrderEntity order = findById(orderId);
        if (order == null) {
            throw new RuntimeException("주문을 찾을 수 없습니다: " + orderId);
        }
        
        String oldStatus = order.getStatus();
        order.setStatus(newStatus);
        order.setUpdatedDate(LocalDateTime.now());
        
        // 상태 변경에 따른 후속 처리
        handleStatusChange(order, oldStatus, newStatus);
        
        return saveOrder(order);
    }

    /**
     * 사용자별 주문 조회
     * 연관 테이블: orders, order_items, products, users
     */
    public List<OrderEntity> findOrdersByUserId(Long userId) {
        // return orderRepository.findByUserIdOrderByOrderDateDesc(userId);
        
        // 시뮬레이션 데이터
        return generateMockOrdersForUser(userId);
    }

    // 헬퍼 메서드들
    
    private OrderEntity saveOrder(OrderEntity orderEntity) {
        // 실제로는 orderRepository.save(orderEntity);
        
        if (orderEntity.getId() == null) {
            orderEntity.setId(generateNewOrderId());
            orderEntity.setOrderDate(LocalDateTime.now());
        }
        
        System.out.println("Order saved: ID=" + orderEntity.getId() + 
                          ", Amount=" + orderEntity.getTotalAmount());
        return orderEntity;
    }
    
    private OrderEntity findById(Long orderId) {
        // 시뮬레이션 주문 조회
        OrderEntity order = new OrderEntity();
        order.setId(orderId);
        order.setUserId(1L);
        order.setOrderDate(LocalDateTime.now().minusDays(1));
        order.setStatus("PENDING");
        order.setTotalAmount(new BigDecimal("50000"));
        order.setPaymentMethod("CARD");
        
        return order;
    }
    
    private OrderItemEntity createOrderItem(Long orderId, OrderItemDto itemDto) {
        // order_items 테이블에 저장 시뮬레이션
        OrderItemEntity item = new OrderItemEntity();
        item.setOrderId(orderId);
        item.setProductId(itemDto.getProductId());
        item.setQuantity(itemDto.getQuantity());
        item.setUnitPrice(itemDto.getUnitPrice());
        item.setTotalPrice(itemDto.getUnitPrice().multiply(BigDecimal.valueOf(itemDto.getQuantity())));
        
        System.out.println("Order item created: Product=" + itemDto.getProductId() + 
                          ", Qty=" + itemDto.getQuantity());
        
        return item;
    }
    
    private void createPaymentRecord(OrderEntity order) {
        // INFERRED payments 테이블 생성 유도
        Map<String, Object> paymentData = Map.of(
            "orderId", order.getId(),
            "amount", order.getTotalAmount(),
            "paymentMethod", order.getPaymentMethod(),
            "status", "PENDING",
            "paymentDate", LocalDateTime.now()
        );
        
        System.out.println("Payment record created for order: " + order.getId());
        System.out.println("Payment data: " + paymentData);
    }
    
    private void createShipmentRecord(OrderEntity order) {
        // INFERRED shipments 테이블 생성 유도
        Map<String, Object> shipmentData = Map.of(
            "orderId", order.getId(),
            "shippingAddress", order.getShippingAddress(),
            "status", "PREPARING",
            "estimatedDelivery", LocalDateTime.now().plusDays(3)
        );
        
        System.out.println("Shipment record created for order: " + order.getId());
        System.out.println("Shipment data: " + shipmentData);
    }
    
    private void handleStatusChange(OrderEntity order, String oldStatus, String newStatus) {
        System.out.println("Order status changed: " + oldStatus + " -> " + newStatus);
        
        // 상태별 후속 처리
        switch (newStatus) {
            case "CONFIRMED":
                // 재고 최종 확정, 결제 처리 시작
                paymentService.processPayment(order.getId());
                break;
            case "SHIPPED":
                // 배송 시작 처리
                shipmentService.startShipment(order.getId());
                break;
            case "DELIVERED":
                // 배송 완료 처리
                shipmentService.completeDelivery(order.getId());
                break;
            case "CANCELLED":
                // 주문 취소 처리 (재고 복구)
                restoreInventoryForCancelledOrder(order);
                break;
        }
    }
    
    private void restoreInventoryForCancelledOrder(OrderEntity order) {
        // 취소된 주문의 재고 복구 (products, inventory 테이블)
        if (order.getOrderItems() != null) {
            for (OrderItemEntity item : order.getOrderItems()) {
                productService.increaseInventory(item.getProductId(), item.getQuantity());
            }
        }
    }
    
    private List<OrderEntity> generateMockOrdersForUser(Long userId) {
        List<OrderEntity> orders = new ArrayList<>();
        
        for (int i = 1; i <= 5; i++) {
            OrderEntity order = new OrderEntity();
            order.setId((long) (userId * 100 + i));
            order.setUserId(userId);
            order.setOrderDate(LocalDateTime.now().minusDays(i * 7));
            order.setStatus(i % 3 == 0 ? "DELIVERED" : "CONFIRMED");
            order.setTotalAmount(new BigDecimal(10000 + (i * 5000)));
            order.setPaymentMethod("CARD");
            
            orders.add(order);
        }
        
        return orders;
    }
    
    private Long generateNewOrderId() {
        return System.currentTimeMillis() % 1000000;
    }
}

// Mock Repository 인터페이스들
interface OrderEntityRepository {
    OrderEntity save(OrderEntity order);
    Optional<OrderEntity> findById(Long id);
    List<OrderEntity> findByUserIdOrderByOrderDateDesc(Long userId);
}

interface OrderItemEntityRepository {
    OrderItemEntity save(OrderItemEntity item);
    List<OrderItemEntity> findByOrderId(Long orderId);
}

// Mock Entity 클래스 (간단한 형태)
class OrderItemEntity {
    private Long id;
    private Long orderId;
    private Long productId;
    private Integer quantity;
    private BigDecimal unitPrice;
    private BigDecimal totalPrice;
    
    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getOrderId() { return orderId; }
    public void setOrderId(Long orderId) { this.orderId = orderId; }
    public Long getProductId() { return productId; }
    public void setProductId(Long productId) { this.productId = productId; }
    public Integer getQuantity() { return quantity; }
    public void setQuantity(Integer quantity) { this.quantity = quantity; }
    public BigDecimal getUnitPrice() { return unitPrice; }
    public void setUnitPrice(BigDecimal unitPrice) { this.unitPrice = unitPrice; }
    public BigDecimal getTotalPrice() { return totalPrice; }
    public void setTotalPrice(BigDecimal totalPrice) { this.totalPrice = totalPrice; }
}



