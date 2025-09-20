package com.example.modern;

import javax.validation.constraints.*;
import java.time.LocalDateTime;
import java.math.BigDecimal;
import java.util.List;
import java.util.Set;

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
    @Pattern(regexp = "^[a-zA-Z0-9_]+$", message = "사용자명은 영문, 숫자, 언더스코어만 가능합니다")
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
    
    @Valid
    private UserProfileDto profileData;
    
    @Valid
    private UserSettingsDto settingsData;
    
    private Set<@Min(1) Long> roleIds;
    
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
    public UserProfileDto getProfileData() { return profileData; }
    public void setProfileData(UserProfileDto profileData) { this.profileData = profileData; }
    public UserSettingsDto getSettingsData() { return settingsData; }
    public void setSettingsData(UserSettingsDto settingsData) { this.settingsData = settingsData; }
    public Set<Long> getRoleIds() { return roleIds; }
    public void setRoleIds(Set<Long> roleIds) { this.roleIds = roleIds; }
}

// 사용자 프로필 DTO
class UserProfileDto {
    @Pattern(regexp = "^[0-9-+()\\s]+$", message = "올바른 전화번호 형식이 아닙니다")
    private String phone;
    
    @Size(max = 500, message = "주소는 500자를 초과할 수 없습니다")
    private String address;
    
    @Past(message = "생년월일은 과거 날짜여야 합니다")
    private LocalDate birthDate;
    
    @Pattern(regexp = "^(M|F|OTHER)$", message = "유효하지 않은 성별입니다")
    private String gender;
    
    @URL(message = "올바른 URL 형식이 아닙니다")
    private String profileImageUrl;
    
    // Getters and Setters
    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }
    public String getAddress() { return address; }
    public void setAddress(String address) { this.address = address; }
    public LocalDate getBirthDate() { return birthDate; }
    public void setBirthDate(LocalDate birthDate) { this.birthDate = birthDate; }
    public String getGender() { return gender; }
    public void setGender(String gender) { this.gender = gender; }
    public String getProfileImageUrl() { return profileImageUrl; }
    public void setProfileImageUrl(String profileImageUrl) { this.profileImageUrl = profileImageUrl; }
}

// 사용자 설정 DTO
class UserSettingsDto {
    @Pattern(regexp = "^(LIGHT|DARK|AUTO)$", message = "유효하지 않은 테마입니다")
    private String theme;
    
    @Pattern(regexp = "^(ko|en|ja|zh)$", message = "지원하지 않는 언어입니다")
    private String language;
    
    @Pattern(regexp = "^[A-Za-z]+/[A-Za-z_]+$", message = "올바른 타임존 형식이 아닙니다")
    private String timezone;
    
    private Boolean emailNotifications;
    private Boolean smsNotifications;
    private Boolean pushNotifications;
    
    // Getters and Setters
    public String getTheme() { return theme; }
    public void setTheme(String theme) { this.theme = theme; }
    public String getLanguage() { return language; }
    public void setLanguage(String language) { this.language = language; }
    public String getTimezone() { return timezone; }
    public void setTimezone(String timezone) { this.timezone = timezone; }
    public Boolean getEmailNotifications() { return emailNotifications; }
    public void setEmailNotifications(Boolean emailNotifications) { this.emailNotifications = emailNotifications; }
    public Boolean getSmsNotifications() { return smsNotifications; }
    public void setSmsNotifications(Boolean smsNotifications) { this.smsNotifications = smsNotifications; }
    public Boolean getPushNotifications() { return pushNotifications; }
    public void setPushNotifications(Boolean pushNotifications) { this.pushNotifications = pushNotifications; }
}

// 주문 관련 DTO들
class OrderResponseDto {
    private Long id;
    private Long userId;
    private LocalDateTime orderDate;
    private String status;
    private BigDecimal totalAmount;
    private String paymentMethod;
    private Integer itemCount;
    private List<OrderItemDto> orderItems;
    private PaymentInfoDto paymentInfo;
    private ShippingInfoDto shippingInfo;
    
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
        public Builder orderItems(List<OrderItemDto> orderItems) { dto.orderItems = orderItems; return this; }
        public Builder paymentInfo(PaymentInfoDto paymentInfo) { dto.paymentInfo = paymentInfo; return this; }
        public Builder shippingInfo(ShippingInfoDto shippingInfo) { dto.shippingInfo = shippingInfo; return this; }
        
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
    public List<OrderItemDto> getOrderItems() { return orderItems; }
    public PaymentInfoDto getPaymentInfo() { return paymentInfo; }
    public ShippingInfoDto getShippingInfo() { return shippingInfo; }
}

// 주문 아이템 DTO
class OrderItemDto {
    private Long productId;
    private String productName;
    private Integer quantity;
    private BigDecimal unitPrice;
    private BigDecimal totalPrice;
    private String productCategory;
    private String brandName;
    
    // Getters and Setters
    public Long getProductId() { return productId; }
    public void setProductId(Long productId) { this.productId = productId; }
    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName; }
    public Integer getQuantity() { return quantity; }
    public void setQuantity(Integer quantity) { this.quantity = quantity; }
    public BigDecimal getUnitPrice() { return unitPrice; }
    public void setUnitPrice(BigDecimal unitPrice) { this.unitPrice = unitPrice; }
    public BigDecimal getTotalPrice() { return totalPrice; }
    public void setTotalPrice(BigDecimal totalPrice) { this.totalPrice = totalPrice; }
    public String getProductCategory() { return productCategory; }
    public void setProductCategory(String productCategory) { this.productCategory = productCategory; }
    public String getBrandName() { return brandName; }
    public void setBrandName(String brandName) { this.brandName = brandName; }
}

// 결제 정보 DTO
class PaymentInfoDto {
    private Long paymentId;
    private BigDecimal amount;
    private String currency;
    private String paymentMethod;
    private String status;
    private LocalDateTime paymentDate;
    private String transactionId;
    
    // Getters and Setters
    public Long getPaymentId() { return paymentId; }
    public void setPaymentId(Long paymentId) { this.paymentId = paymentId; }
    public BigDecimal getAmount() { return amount; }
    public void setAmount(BigDecimal amount) { this.amount = amount; }
    public String getCurrency() { return currency; }
    public void setCurrency(String currency) { this.currency = currency; }
    public String getPaymentMethod() { return paymentMethod; }
    public void setPaymentMethod(String paymentMethod) { this.paymentMethod = paymentMethod; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public LocalDateTime getPaymentDate() { return paymentDate; }
    public void setPaymentDate(LocalDateTime paymentDate) { this.paymentDate = paymentDate; }
    public String getTransactionId() { return transactionId; }
    public void setTransactionId(String transactionId) { this.transactionId = transactionId; }
}

// 배송 정보 DTO
class ShippingInfoDto {
    private Long shipmentId;
    private String trackingNumber;
    private String carrier;
    private String status;
    private LocalDateTime shipDate;
    private LocalDateTime estimatedDelivery;
    private LocalDateTime deliveredDate;
    private String shippingAddress;
    
    // Getters and Setters
    public Long getShipmentId() { return shipmentId; }
    public void setShipmentId(Long shipmentId) { this.shipmentId = shipmentId; }
    public String getTrackingNumber() { return trackingNumber; }
    public void setTrackingNumber(String trackingNumber) { this.trackingNumber = trackingNumber; }
    public String getCarrier() { return carrier; }
    public void setCarrier(String carrier) { this.carrier = carrier; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public LocalDateTime getShipDate() { return shipDate; }
    public void setShipDate(LocalDateTime shipDate) { this.shipDate = shipDate; }
    public LocalDateTime getEstimatedDelivery() { return estimatedDelivery; }
    public void setEstimatedDelivery(LocalDateTime estimatedDelivery) { this.estimatedDelivery = estimatedDelivery; }
    public LocalDateTime getDeliveredDate() { return deliveredDate; }
    public void setDeliveredDate(LocalDateTime deliveredDate) { this.deliveredDate = deliveredDate; }
    public String getShippingAddress() { return shippingAddress; }
    public void setShippingAddress(String shippingAddress) { this.shippingAddress = shippingAddress; }
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
    private List<String> validationErrors;
    
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
        public Builder<T> validationErrors(List<String> validationErrors) { response.validationErrors = validationErrors; return this; }
        
        public ApiResponse<T> build() { return response; }
    }
    
    // Getters
    public boolean isSuccess() { return success; }
    public String getMessage() { return message; }
    public T getData() { return data; }
    public LocalDateTime getTimestamp() { return timestamp; }
    public String getErrorCode() { return errorCode; }
    public List<String> getValidationErrors() { return validationErrors; }
}

// 사용자 검색 조건 DTO
class UserSearchCriteria {
    private String search;
    private String status;
    private String userType;
    private Long departmentId;
    private LocalDateTime createdDateFrom;
    private LocalDateTime createdDateTo;
    private Boolean hasOrders;
    private BigDecimal minTotalSpent;
    private BigDecimal maxTotalSpent;
    
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
        public Builder createdDateFrom(LocalDateTime createdDateFrom) { criteria.createdDateFrom = createdDateFrom; return this; }
        public Builder createdDateTo(LocalDateTime createdDateTo) { criteria.createdDateTo = createdDateTo; return this; }
        public Builder hasOrders(Boolean hasOrders) { criteria.hasOrders = hasOrders; return this; }
        public Builder minTotalSpent(BigDecimal minTotalSpent) { criteria.minTotalSpent = minTotalSpent; return this; }
        public Builder maxTotalSpent(BigDecimal maxTotalSpent) { criteria.maxTotalSpent = maxTotalSpent; return this; }
        
        public UserSearchCriteria build() { return criteria; }
    }
    
    // Getters
    public String getSearch() { return search; }
    public String getStatus() { return status; }
    public String getUserType() { return userType; }
    public Long getDepartmentId() { return departmentId; }
    public LocalDateTime getCreatedDateFrom() { return createdDateFrom; }
    public LocalDateTime getCreatedDateTo() { return createdDateTo; }
    public Boolean getHasOrders() { return hasOrders; }
    public BigDecimal getMinTotalSpent() { return minTotalSpent; }
    public BigDecimal getMaxTotalSpent() { return maxTotalSpent; }
}

// 분석 요청 DTO
class AnalyticsRequestDto {
    @NotBlank(message = "환경은 필수입니다")
    @Pattern(regexp = "^(dev|test|prod)$", message = "유효하지 않은 환경입니다")
    private String environment;
    
    @NotNull(message = "시작 날짜는 필수입니다")
    @Past(message = "시작 날짜는 과거여야 합니다")
    private LocalDate startDate;
    
    @NotNull(message = "종료 날짜는 필수입니다")
    private LocalDate endDate;
    
    @NotEmpty(message = "최소 하나의 리포트 타입을 선택해야 합니다")
    private List<@Pattern(regexp = "^(USER_ACTIVITY|PRODUCT_PERFORMANCE|DEPARTMENT_PERFORMANCE)$") String> reportTypes;
    
    @Pattern(regexp = "^(DAILY|WEEKLY|MONTHLY|QUARTERLY)$", message = "유효하지 않은 기간 타입입니다")
    private String periodType;
    
    @Min(value = 1, message = "기간 수는 1 이상이어야 합니다")
    @Max(value = 365, message = "기간 수는 365를 초과할 수 없습니다")
    private Integer periodCount;
    
    private Map<String, Object> filters;
    private List<String> includeOptions;
    
    // Getters and Setters
    public String getEnvironment() { return environment; }
    public void setEnvironment(String environment) { this.environment = environment; }
    public LocalDate getStartDate() { return startDate; }
    public void setStartDate(LocalDate startDate) { this.startDate = startDate; }
    public LocalDate getEndDate() { return endDate; }
    public void setEndDate(LocalDate endDate) { this.endDate = endDate; }
    public List<String> getReportTypes() { return reportTypes; }
    public void setReportTypes(List<String> reportTypes) { this.reportTypes = reportTypes; }
    public String getPeriodType() { return periodType; }
    public void setPeriodType(String periodType) { this.periodType = periodType; }
    public Integer getPeriodCount() { return periodCount; }
    public void setPeriodCount(Integer periodCount) { this.periodCount = periodCount; }
    public Map<String, Object> getFilters() { return filters; }
    public void setFilters(Map<String, Object> filters) { this.filters = filters; }
    public List<String> getIncludeOptions() { return includeOptions; }
    public void setIncludeOptions(List<String> includeOptions) { this.includeOptions = includeOptions; }
}

// 분석 응답 DTO
class AnalyticsResponseDto {
    private Map<String, Object> reportData;
    private List<Map<String, Object>> hybridAnalysis;
    private List<Map<String, Object>> trendsAnalysis;
    private LocalDateTime generatedAt;
    private Integer recordCount;
    private String processingTimeMs;
    
    // Builder 패턴
    public static Builder builder() {
        return new Builder();
    }
    
    public static class Builder {
        private AnalyticsResponseDto dto = new AnalyticsResponseDto();
        
        public Builder reportData(Map<String, Object> reportData) { dto.reportData = reportData; return this; }
        public Builder hybridAnalysis(List<Map<String, Object>> hybridAnalysis) { dto.hybridAnalysis = hybridAnalysis; return this; }
        public Builder trendsAnalysis(List<Map<String, Object>> trendsAnalysis) { dto.trendsAnalysis = trendsAnalysis; return this; }
        public Builder generatedAt(LocalDateTime generatedAt) { dto.generatedAt = generatedAt; return this; }
        public Builder recordCount(Integer recordCount) { dto.recordCount = recordCount; return this; }
        public Builder processingTimeMs(String processingTimeMs) { dto.processingTimeMs = processingTimeMs; return this; }
        
        public AnalyticsResponseDto build() { return dto; }
    }
    
    // Getters
    public Map<String, Object> getReportData() { return reportData; }
    public List<Map<String, Object>> getHybridAnalysis() { return hybridAnalysis; }
    public List<Map<String, Object>> getTrendsAnalysis() { return trendsAnalysis; }
    public LocalDateTime getGeneratedAt() { return generatedAt; }
    public Integer getRecordCount() { return recordCount; }
    public String getProcessingTimeMs() { return processingTimeMs; }
}
