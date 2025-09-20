package com.example.modern;

import javax.validation.constraints.*;
import java.time.LocalDateTime;
import java.math.BigDecimal;
import java.util.List;
import java.util.Set;
import java.util.Map;

/**
 * 사용자 DTO 패턴 모음 - 연관관계 도출 테스트용
 * 목적: DTO 변환 로직에서의 서비스 계층 연결 테스트
 * 연관관계 중심: DTO -> Service -> Repository -> Entity 변환 체인
 */

// 기본 사용자 응답 DTO
public class UserResponseDto {
    private Long id;
    private String username;
    private String email;
    private String fullName;
    private String userType;
    private String status;
    private String departmentName;
    private LocalDateTime createdDate;
    private LocalDateTime lastLoginDate;
    private Integer orderCount;
    private BigDecimal totalSpent;
    
    // Builder 패턴
    public static Builder builder() {
        return new Builder();
    }
    
    public static class Builder {
        private UserResponseDto dto = new UserResponseDto();
        
        public Builder id(Long id) { dto.id = id; return this; }
        public Builder username(String username) { dto.username = username; return this; }
        public Builder email(String email) { dto.email = email; return this; }
        public Builder fullName(String fullName) { dto.fullName = fullName; return this; }
        public Builder userType(String userType) { dto.userType = userType; return this; }
        public Builder status(String status) { dto.status = status; return this; }
        public Builder departmentName(String departmentName) { dto.departmentName = departmentName; return this; }
        public Builder createdDate(LocalDateTime createdDate) { dto.createdDate = createdDate; return this; }
        public Builder lastLoginDate(LocalDateTime lastLoginDate) { dto.lastLoginDate = lastLoginDate; return this; }
        public Builder orderCount(Integer orderCount) { dto.orderCount = orderCount; return this; }
        public Builder totalSpent(BigDecimal totalSpent) { dto.totalSpent = totalSpent; return this; }
        
        public UserResponseDto build() { return dto; }
    }
    
    // Getters
    public Long getId() { return id; }
    public String getUsername() { return username; }
    public String getEmail() { return email; }
    public String getFullName() { return fullName; }
    public String getUserType() { return userType; }
    public String getStatus() { return status; }
    public String getDepartmentName() { return departmentName; }
    public LocalDateTime getCreatedDate() { return createdDate; }
    public LocalDateTime getLastLoginDate() { return lastLoginDate; }
    public Integer getOrderCount() { return orderCount; }
    public BigDecimal getTotalSpent() { return totalSpent; }
}

// 사용자 생성 요청 DTO
class CreateUserRequestDto {
    @NotBlank(message = "사용자명은 필수입니다")
    @Size(min = 3, max = 50, message = "사용자명은 3-50자 사이여야 합니다")
    private String username;
    
    @Email(message = "올바른 이메일 형식이 아닙니다")
    @NotBlank(message = "이메일은 필수입니다")
    private String email;
    
    @NotBlank(message = "전체 이름은 필수입니다")
    @Size(min = 2, max = 100, message = "이름은 2-100자 사이여야 합니다")
    private String fullName;
    
    @NotBlank(message = "사용자 타입은 필수입니다")
    @Pattern(regexp = "^(ADMIN|USER|MANAGER|GUEST)$", message = "유효하지 않은 사용자 타입입니다")
    private String userType;
    
    @Min(value = 1, message = "유효하지 않은 부서 ID입니다")
    private Long departmentId;
    
    private Map<String, Object> profileData;
    
    // Getters and Setters
    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public String getFullName() { return fullName; }
    public void setFullName(String fullName) { this.fullName = fullName; }
    public String getUserType() { return userType; }
    public void setUserType(String userType) { this.userType = userType; }
    public Long getDepartmentId() { return departmentId; }
    public void setDepartmentId(Long departmentId) { this.departmentId = departmentId; }
    public Map<String, Object> getProfileData() { return profileData; }
    public void setProfileData(Map<String, Object> profileData) { this.profileData = profileData; }
}

// 사용자 업데이트 요청 DTO
class UpdateUserRequestDto {
    @Size(min = 2, max = 100)
    private String fullName;
    
    @Email
    private String email;
    
    @Min(1)
    private Long departmentId;
    
    @Pattern(regexp = "^(ACTIVE|INACTIVE|PENDING)$")
    private String status;
    
    private Map<String, Object> profileData;
    
    // Getters and Setters
    public String getFullName() { return fullName; }
    public void setFullName(String fullName) { this.fullName = fullName; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public Long getDepartmentId() { return departmentId; }
    public void setDepartmentId(Long departmentId) { this.departmentId = departmentId; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Map<String, Object> getProfileData() { return profileData; }
    public void setProfileData(Map<String, Object> profileData) { this.profileData = profileData; }
}

// 주문 생성 요청 DTO
class CreateOrderRequestDto {
    @NotNull(message = "사용자 ID는 필수입니다")
    @Min(value = 1, message = "유효하지 않은 사용자 ID입니다")
    private Long userId;
    
    @NotEmpty(message = "주문 항목은 필수입니다")
    @Valid
    private List<OrderItemDto> orderItems;
    
    @NotBlank(message = "결제 방법은 필수입니다")
    @Pattern(regexp = "^(CARD|BANK_TRANSFER|CASH|MOBILE)$", message = "유효하지 않은 결제 방법입니다")
    private String paymentMethod;
    
    @NotBlank(message = "배송 주소는 필수입니다")
    @Size(max = 500, message = "배송 주소는 500자를 초과할 수 없습니다")
    private String shippingAddress;
    
    // Getters and Setters
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public List<OrderItemDto> getOrderItems() { return orderItems; }
    public void setOrderItems(List<OrderItemDto> orderItems) { this.orderItems = orderItems; }
    public String getPaymentMethod() { return paymentMethod; }
    public void setPaymentMethod(String paymentMethod) { this.paymentMethod = paymentMethod; }
    public String getShippingAddress() { return shippingAddress; }
    public void setShippingAddress(String shippingAddress) { this.shippingAddress = shippingAddress; }
}

// 주문 아이템 DTO
class OrderItemDto {
    @NotNull(message = "상품 ID는 필수입니다")
    @Min(value = 1, message = "유효하지 않은 상품 ID입니다")
    private Long productId;
    
    @NotNull(message = "수량은 필수입니다")
    @Min(value = 1, message = "수량은 1 이상이어야 합니다")
    @Max(value = 999, message = "수량은 999를 초과할 수 없습니다")
    private Integer quantity;
    
    @NotNull(message = "단가는 필수입니다")
    @DecimalMin(value = "0.0", inclusive = false, message = "단가는 0보다 커야 합니다")
    private BigDecimal unitPrice;
    
    private String productName;
    private String productCategory;
    private String brandName;
    
    // Getters and Setters
    public Long getProductId() { return productId; }
    public void setProductId(Long productId) { this.productId = productId; }
    public Integer getQuantity() { return quantity; }
    public void setQuantity(Integer quantity) { this.quantity = quantity; }
    public BigDecimal getUnitPrice() { return unitPrice; }
    public void setUnitPrice(BigDecimal unitPrice) { this.unitPrice = unitPrice; }
    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName; }
    public String getProductCategory() { return productCategory; }
    public void setProductCategory(String productCategory) { this.productCategory = productCategory; }
    public String getBrandName() { return brandName; }
    public void setBrandName(String brandName) { this.brandName = brandName; }
}

// 페이징 응답 DTO
class PagedResponse<T> {
    private List<T> content;
    private int page;
    private int size;
    private long totalElements;
    private int totalPages;
    private boolean first;
    private boolean last;
    private String error;
    
    // Builder 패턴
    public static <T> Builder<T> builder() {
        return new Builder<>();
    }
    
    public static class Builder<T> {
        private PagedResponse<T> response = new PagedResponse<>();
        
        public Builder<T> content(List<T> content) { response.content = content; return this; }
        public Builder<T> page(int page) { response.page = page; return this; }
        public Builder<T> size(int size) { response.size = size; return this; }
        public Builder<T> totalElements(long totalElements) { response.totalElements = totalElements; return this; }
        public Builder<T> totalPages(int totalPages) { response.totalPages = totalPages; return this; }
        public Builder<T> first(boolean first) { response.first = first; return this; }
        public Builder<T> last(boolean last) { response.last = last; return this; }
        public Builder<T> error(String error) { response.error = error; return this; }
        
        public PagedResponse<T> build() { return response; }
    }
    
    // Getters
    public List<T> getContent() { return content; }
    public int getPage() { return page; }
    public int getSize() { return size; }
    public long getTotalElements() { return totalElements; }
    public int getTotalPages() { return totalPages; }
    public boolean isFirst() { return first; }
    public boolean isLast() { return last; }
    public String getError() { return error; }
}

// API 응답 DTO
class ApiResponse<T> {
    private boolean success;
    private String message;
    private T data;
    private LocalDateTime timestamp;
    private String errorCode;
    
    // Builder 패턴
    public static <T> Builder<T> builder() {
        return new Builder<>();
    }
    
    public static class Builder<T> {
        private ApiResponse<T> response = new ApiResponse<>();
        
        public Builder<T> success(boolean success) { response.success = success; return this; }
        public Builder<T> message(String message) { response.message = message; return this; }
        public Builder<T> data(T data) { response.data = data; return this; }
        public Builder<T> timestamp(LocalDateTime timestamp) { response.timestamp = timestamp; return this; }
        public Builder<T> errorCode(String errorCode) { response.errorCode = errorCode; return this; }
        
        public ApiResponse<T> build() { return response; }
    }
    
    // Getters
    public boolean isSuccess() { return success; }
    public String getMessage() { return message; }
    public T getData() { return data; }
    public LocalDateTime getTimestamp() { return timestamp; }
    public String getErrorCode() { return errorCode; }
}

// 사용자 검색 조건 DTO
class UserSearchCriteria {
    private String search;
    private String status;
    private String userType;
    private Long departmentId;
    
    // Builder 패턴
    public static Builder builder() {
        return new Builder();
    }
    
    public static class Builder {
        private UserSearchCriteria criteria = new UserSearchCriteria();
        
        public Builder search(String search) { criteria.search = search; return this; }
        public Builder status(String status) { criteria.status = status; return this; }
        public Builder userType(String userType) { criteria.userType = userType; return this; }
        public Builder departmentId(Long departmentId) { criteria.departmentId = departmentId; return this; }
        
        public UserSearchCriteria build() { return criteria; }
    }
    
    // Getters
    public String getSearch() { return search; }
    public String getStatus() { return status; }
    public String getUserType() { return userType; }
    public Long getDepartmentId() { return departmentId; }
}

// 주문 응답 DTO
class OrderResponseDto {
    private Long id;
    private Long userId;
    private LocalDateTime orderDate;
    private String status;
    private BigDecimal totalAmount;
    private String paymentMethod;
    private Integer itemCount;
    
    // Builder 패턴
    public static Builder builder() {
        return new Builder();
    }
    
    public static class Builder {
        private OrderResponseDto dto = new OrderResponseDto();
        
        public Builder id(Long id) { dto.id = id; return this; }
        public Builder userId(Long userId) { dto.userId = userId; return this; }
        public Builder orderDate(LocalDateTime orderDate) { dto.orderDate = orderDate; return this; }
        public Builder status(String status) { dto.status = status; return this; }
        public Builder totalAmount(BigDecimal totalAmount) { dto.totalAmount = totalAmount; return this; }
        public Builder paymentMethod(String paymentMethod) { dto.paymentMethod = paymentMethod; return this; }
        public Builder itemCount(Integer itemCount) { dto.itemCount = itemCount; return this; }
        
        public OrderResponseDto build() { return dto; }
    }
    
    // Getters
    public Long getId() { return id; }
    public Long getUserId() { return userId; }
    public LocalDateTime getOrderDate() { return orderDate; }
    public String getStatus() { return status; }
    public BigDecimal getTotalAmount() { return totalAmount; }
    public String getPaymentMethod() { return paymentMethod; }
    public Integer getItemCount() { return itemCount; }
}



