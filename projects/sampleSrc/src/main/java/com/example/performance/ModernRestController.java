package com.example.performance;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;

import javax.validation.Valid;
import javax.validation.constraints.*;
import java.util.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 최신 Spring Boot REST API 패턴 - 연관관계 도출 테스트용
 * 목적: @RestController, @RequestMapping, @Valid, ResponseEntity 패턴 테스트
 * 연관관계 중심: 현대적 Spring Boot 패턴에서의 서비스 계층 연결
 */
@RestController
@RequestMapping("/api/v2")
@Validated
@CrossOrigin(origins = "*")
public class ModernRestController {

    @Autowired
    private LargeDataProcessor dataProcessor;
    
    @Autowired
    private HybridSqlPatternDao hybridSqlDao;
    
    @Autowired
    private UserEntityService userEntityService;
    
    @Autowired
    private OrderEntityService orderEntityService;
    
    @Autowired
    private ProductEntityService productEntityService;

    /**
     * 현대적 사용자 조회 API - 페이징 + 검증
     * 연관 서비스: UserEntityService -> UserRepository -> users 테이블
     */
    @GetMapping("/users")
    public ResponseEntity<PagedResponse<UserResponseDto>> getUsers(
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size,
            @RequestParam(required = false) @Size(min = 2, max = 50) String search,
            @RequestParam(required = false) @Pattern(regexp = "^(ACTIVE|INACTIVE|PENDING)$") String status,
            @RequestParam(required = false) @Pattern(regexp = "^(username|email|createdDate)$") String sortBy,
            @RequestParam(required = false) @Pattern(regexp = "^(asc|desc)$") String sortDir) {
        
        try {
            // 정렬 조건 구성
            Sort.Direction direction = "desc".equalsIgnoreCase(sortDir) ? 
                                     Sort.Direction.DESC : Sort.Direction.ASC;
            String sortField = sortBy != null ? sortBy : "createdDate";
            
            Pageable pageable = PageRequest.of(page, size, Sort.by(direction, sortField));
            
            // 검색 조건 구성
            UserSearchCriteria criteria = UserSearchCriteria.builder()
                .search(search)
                .status(status)
                .build();
            
            // 서비스 계층 호출 (JPA Repository 연결)
            Page<UserEntity> userPage = userEntityService.findUsersByCriteria(criteria, pageable);
            
            // DTO 변환
            List<UserResponseDto> userDtos = userPage.getContent().stream()
                .map(this::convertToUserResponseDto)
                .toList();
            
            PagedResponse<UserResponseDto> response = PagedResponse.<UserResponseDto>builder()
                .content(userDtos)
                .page(userPage.getNumber())
                .size(userPage.getSize())
                .totalElements(userPage.getTotalElements())
                .totalPages(userPage.getTotalPages())
                .first(userPage.isFirst())
                .last(userPage.isLast())
                .build();
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(PagedResponse.<UserResponseDto>builder()
                    .error("사용자 조회 중 오류가 발생했습니다: " + e.getMessage())
                    .build());
        }
    }

    /**
     * 사용자 생성 API - 유효성 검증 + 트랜잭션
     * 연관 서비스: UserEntityService -> UserRepository + UserProfileRepository
     */
    @PostMapping("/users")
    public ResponseEntity<ApiResponse<UserResponseDto>> createUser(
            @Valid @RequestBody CreateUserRequestDto request) {
        
        try {
            // DTO to Entity 변환
            UserEntity userEntity = UserEntity.builder()
                .username(request.getUsername())
                .email(request.getEmail())
                .fullName(request.getFullName())
                .userType(request.getUserType())
                .departmentId(request.getDepartmentId())
                .status("ACTIVE")
                .createdDate(LocalDateTime.now())
                .build();
            
            // 서비스 계층에서 사용자 생성 (연관 테이블들 함께 처리)
            UserEntity savedUser = userEntityService.createUserWithProfile(userEntity, request.getProfileData());
            
            // 응답 DTO 변환
            UserResponseDto responseDto = convertToUserResponseDto(savedUser);
            
            ApiResponse<UserResponseDto> response = ApiResponse.<UserResponseDto>builder()
                .success(true)
                .message("사용자가 성공적으로 생성되었습니다")
                .data(responseDto)
                .timestamp(LocalDateTime.now())
                .build();
            
            return ResponseEntity.status(HttpStatus.CREATED).body(response);
            
        } catch (ValidationException e) {
            return ResponseEntity.badRequest()
                .body(ApiResponse.<UserResponseDto>builder()
                    .success(false)
                    .message("유효성 검증 실패: " + e.getMessage())
                    .timestamp(LocalDateTime.now())
                    .build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.<UserResponseDto>builder()
                    .success(false)
                    .message("사용자 생성 중 오류가 발생했습니다: " + e.getMessage())
                    .timestamp(LocalDateTime.now())
                    .build());
        }
    }

    /**
     * 사용자 업데이트 API - 부분 업데이트 지원
     * 연관 서비스: UserEntityService -> 여러 Repository (User, Profile, Roles)
     */
    @PatchMapping("/users/{userId}")
    public ResponseEntity<ApiResponse<UserResponseDto>> updateUser(
            @PathVariable @NotNull @Min(1) Long userId,
            @Valid @RequestBody UpdateUserRequestDto request) {
        
        try {
            // 사용자 존재 확인
            Optional<UserEntity> existingUser = userEntityService.findById(userId);
            if (existingUser.isEmpty()) {
                return ResponseEntity.notFound().build();
            }
            
            // 부분 업데이트 적용
            UserEntity userToUpdate = existingUser.get();
            updateUserFields(userToUpdate, request);
            
            // 서비스 계층에서 업데이트 (연관 데이터 함께 처리)
            UserEntity updatedUser = userEntityService.updateUserWithRelations(userToUpdate, request);
            
            UserResponseDto responseDto = convertToUserResponseDto(updatedUser);
            
            ApiResponse<UserResponseDto> response = ApiResponse.<UserResponseDto>builder()
                .success(true)
                .message("사용자 정보가 성공적으로 업데이트되었습니다")
                .data(responseDto)
                .timestamp(LocalDateTime.now())
                .build();
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.<UserResponseDto>builder()
                    .success(false)
                    .message("사용자 업데이트 중 오류가 발생했습니다: " + e.getMessage())
                    .timestamp(LocalDateTime.now())
                    .build());
        }
    }

    /**
     * 주문 생성 API - 복잡한 비즈니스 로직 + 다중 테이블 연관
     * 연관 서비스: OrderEntityService -> Order, OrderItem, Product, Inventory
     */
    @PostMapping("/orders")
    public ResponseEntity<ApiResponse<OrderResponseDto>> createOrder(
            @Valid @RequestBody CreateOrderRequestDto request) {
        
        try {
            // 주문 유효성 검증
            validateOrderRequest(request);
            
            // 재고 확인 (Product 테이블 연관)
            boolean inventoryAvailable = productEntityService.checkInventoryAvailability(request.getOrderItems());
            if (!inventoryAvailable) {
                return ResponseEntity.badRequest()
                    .body(ApiResponse.<OrderResponseDto>builder()
                        .success(false)
                        .message("일부 상품의 재고가 부족합니다")
                        .timestamp(LocalDateTime.now())
                        .build());
            }
            
            // 주문 엔티티 생성
            OrderEntity orderEntity = OrderEntity.builder()
                .userId(request.getUserId())
                .orderDate(LocalDateTime.now())
                .status("PENDING")
                .totalAmount(calculateTotalAmount(request.getOrderItems()))
                .paymentMethod(request.getPaymentMethod())
                .shippingAddress(request.getShippingAddress())
                .build();
            
            // 서비스 계층에서 주문 생성 (Order + OrderItems + Inventory 업데이트)
            OrderEntity savedOrder = orderEntityService.createOrderWithItems(orderEntity, request.getOrderItems());
            
            // 응답 DTO 변환
            OrderResponseDto responseDto = convertToOrderResponseDto(savedOrder);
            
            ApiResponse<OrderResponseDto> response = ApiResponse.<OrderResponseDto>builder()
                .success(true)
                .message("주문이 성공적으로 생성되었습니다")
                .data(responseDto)
                .timestamp(LocalDateTime.now())
                .build();
            
            return ResponseEntity.status(HttpStatus.CREATED).body(response);
            
        } catch (InsufficientInventoryException e) {
            return ResponseEntity.badRequest()
                .body(ApiResponse.<OrderResponseDto>builder()
                    .success(false)
                    .message("재고 부족: " + e.getMessage())
                    .timestamp(LocalDateTime.now())
                    .build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.<OrderResponseDto>builder()
                    .success(false)
                    .message("주문 생성 중 오류가 발생했습니다: " + e.getMessage())
                    .timestamp(LocalDateTime.now())
                    .build());
        }
    }

    /**
     * 복합 분석 API - 대용량 데이터 처리 연결
     * 연관 서비스: LargeDataProcessor -> HybridSqlPatternDao -> 다중 테이블
     */
    @PostMapping("/analytics/comprehensive")
    public ResponseEntity<ApiResponse<AnalyticsResponseDto>> generateComprehensiveAnalytics(
            @Valid @RequestBody AnalyticsRequestDto request) {
        
        try {
            // 요청 유효성 검증
            validateAnalyticsRequest(request);
            
            // 대용량 데이터 처리기 호출 (다중 환경, 다중 테이블 연관)
            Map<String, Object> analyticsData = dataProcessor.generateComprehensiveReport(
                request.getEnvironment(),
                request.getStartDate(),
                request.getEndDate(),
                request.getReportTypes()
            );
            
            // 하이브리드 SQL 패턴으로 추가 분석
            List<Map<String, Object>> hybridAnalysis = hybridSqlDao.findUserOrdersWithHybridPattern(
                request.getEnvironment(),
                request.getFilters(),
                request.getIncludeOptions()
            );
            
            // 트렌드 분석 추가
            List<Map<String, Object>> trendsData = hybridSqlDao.analyzeSalesTrends(
                request.getEnvironment(),
                request.getPeriodType(),
                request.getPeriodCount()
            );
            
            // 응답 DTO 구성
            AnalyticsResponseDto responseDto = AnalyticsResponseDto.builder()
                .reportData(analyticsData)
                .hybridAnalysis(hybridAnalysis)
                .trendsAnalysis(trendsData)
                .generatedAt(LocalDateTime.now())
                .recordCount(calculateTotalRecords(analyticsData, hybridAnalysis, trendsData))
                .build();
            
            ApiResponse<AnalyticsResponseDto> response = ApiResponse.<AnalyticsResponseDto>builder()
                .success(true)
                .message("종합 분석이 성공적으로 완료되었습니다")
                .data(responseDto)
                .timestamp(LocalDateTime.now())
                .build();
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.<AnalyticsResponseDto>builder()
                    .success(false)
                    .message("분석 처리 중 오류가 발생했습니다: " + e.getMessage())
                    .timestamp(LocalDateTime.now())
                    .build());
        }
    }

    /**
     * 실시간 데이터 스트림 API - WebSocket 연결 시뮬레이션
     * 연관 서비스: LargeDataProcessor -> 실시간 이벤트 테이블들
     */
    @GetMapping("/stream/realtime")
    public ResponseEntity<ApiResponse<StreamConfigDto>> configureRealtimeStream(
            @RequestParam @NotBlank @Size(min = 3, max = 10) String environment,
            @RequestParam(defaultValue = "100") @Min(10) @Max(1000) int batchSize,
            @RequestParam(defaultValue = "1000") @Min(100) @Max(10000) long intervalMs) {
        
        try {
            // 스트림 설정 검증
            validateStreamConfiguration(environment, batchSize, intervalMs);
            
            // 실시간 스트림 처리 시작 (별도 스레드)
            CompletableFuture.runAsync(() -> {
                dataProcessor.processRealTimeDataStream(environment, batchSize, intervalMs);
            });
            
            StreamConfigDto configDto = StreamConfigDto.builder()
                .environment(environment)
                .batchSize(batchSize)
                .intervalMs(intervalMs)
                .status("ACTIVE")
                .startedAt(LocalDateTime.now())
                .build();
            
            ApiResponse<StreamConfigDto> response = ApiResponse.<StreamConfigDto>builder()
                .success(true)
                .message("실시간 스트림이 성공적으로 시작되었습니다")
                .data(configDto)
                .timestamp(LocalDateTime.now())
                .build();
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.<StreamConfigDto>builder()
                    .success(false)
                    .message("스트림 설정 중 오류가 발생했습니다: " + e.getMessage())
                    .timestamp(LocalDateTime.now())
                    .build());
        }
    }

    /**
     * 다중 환경 동기화 API - 환경별 테이블 연관
     * 연관 서비스: LargeDataProcessor -> 모든 환경별 테이블들
     */
    @PostMapping("/sync/environments")
    public ResponseEntity<ApiResponse<SyncResultDto>> synchronizeEnvironments(
            @Valid @RequestBody EnvironmentSyncRequestDto request) {
        
        try {
            // 동기화 권한 확인
            validateSyncPermissions(request);
            
            // 다중 환경 데이터 동기화 실행
            boolean syncResult = dataProcessor.synchronizeMultiEnvironmentData(
                request.getEnvironments(),
                request.getSourceEnvironment(),
                request.getTargetEnvironment(),
                request.getSyncOptions()
            );
            
            SyncResultDto resultDto = SyncResultDto.builder()
                .success(syncResult)
                .sourceEnvironment(request.getSourceEnvironment())
                .targetEnvironment(request.getTargetEnvironment())
                .syncedTables(request.getSyncOptions().keySet())
                .syncStartTime(LocalDateTime.now().minusMinutes(5)) // 실제로는 동기화 시작 시간
                .syncEndTime(LocalDateTime.now())
                .recordsSynced(calculateSyncedRecords(syncResult))
                .build();
            
            ApiResponse<SyncResultDto> response = ApiResponse.<SyncResultDto>builder()
                .success(syncResult)
                .message(syncResult ? "환경 동기화가 성공적으로 완료되었습니다" : "환경 동기화 중 일부 오류가 발생했습니다")
                .data(resultDto)
                .timestamp(LocalDateTime.now())
                .build();
            
            return ResponseEntity.ok(response);
            
        } catch (UnauthorizedException e) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                .body(ApiResponse.<SyncResultDto>builder()
                    .success(false)
                    .message("동기화 권한이 없습니다: " + e.getMessage())
                    .timestamp(LocalDateTime.now())
                    .build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.<SyncResultDto>builder()
                    .success(false)
                    .message("환경 동기화 중 오류가 발생했습니다: " + e.getMessage())
                    .timestamp(LocalDateTime.now())
                    .build());
        }
    }

    // 헬퍼 메서드들 (DTO 변환, 유효성 검증 등)
    
    private UserResponseDto convertToUserResponseDto(UserEntity userEntity) {
        return UserResponseDto.builder()
            .id(userEntity.getId())
            .username(userEntity.getUsername())
            .email(userEntity.getEmail())
            .fullName(userEntity.getFullName())
            .userType(userEntity.getUserType())
            .status(userEntity.getStatus())
            .departmentName(userEntity.getDepartment() != null ? userEntity.getDepartment().getDeptName() : null)
            .createdDate(userEntity.getCreatedDate())
            .lastLoginDate(userEntity.getLastLoginDate())
            .build();
    }
    
    private OrderResponseDto convertToOrderResponseDto(OrderEntity orderEntity) {
        return OrderResponseDto.builder()
            .id(orderEntity.getId())
            .userId(orderEntity.getUserId())
            .orderDate(orderEntity.getOrderDate())
            .status(orderEntity.getStatus())
            .totalAmount(orderEntity.getTotalAmount())
            .paymentMethod(orderEntity.getPaymentMethod())
            .itemCount(orderEntity.getOrderItems() != null ? orderEntity.getOrderItems().size() : 0)
            .build();
    }
    
    private void updateUserFields(UserEntity user, UpdateUserRequestDto request) {
        if (request.getFullName() != null) {
            user.setFullName(request.getFullName());
        }
        if (request.getEmail() != null) {
            user.setEmail(request.getEmail());
        }
        if (request.getDepartmentId() != null) {
            user.setDepartmentId(request.getDepartmentId());
        }
        if (request.getStatus() != null) {
            user.setStatus(request.getStatus());
        }
        user.setUpdatedDate(LocalDateTime.now());
    }
    
    private void validateOrderRequest(CreateOrderRequestDto request) {
        if (request.getOrderItems() == null || request.getOrderItems().isEmpty()) {
            throw new ValidationException("주문 항목이 비어있습니다");
        }
        
        if (request.getUserId() == null || request.getUserId() <= 0) {
            throw new ValidationException("유효하지 않은 사용자 ID입니다");
        }
    }
    
    private BigDecimal calculateTotalAmount(List<OrderItemDto> orderItems) {
        return orderItems.stream()
            .map(item -> item.getUnitPrice().multiply(BigDecimal.valueOf(item.getQuantity())))
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
    
    private void validateAnalyticsRequest(AnalyticsRequestDto request) {
        if (request.getStartDate().isAfter(request.getEndDate())) {
            throw new ValidationException("시작 날짜가 종료 날짜보다 늦을 수 없습니다");
        }
        
        if (request.getReportTypes() == null || request.getReportTypes().isEmpty()) {
            throw new ValidationException("최소 하나의 리포트 타입을 선택해야 합니다");
        }
    }
    
    private void validateStreamConfiguration(String environment, int batchSize, long intervalMs) {
        List<String> validEnvironments = Arrays.asList("dev", "test", "prod");
        if (!validEnvironments.contains(environment)) {
            throw new ValidationException("유효하지 않은 환경입니다: " + environment);
        }
        
        if (batchSize > 1000 && "prod".equals(environment)) {
            throw new ValidationException("운영 환경에서는 배치 크기가 1000을 초과할 수 없습니다");
        }
    }
    
    private void validateSyncPermissions(EnvironmentSyncRequestDto request) {
        // 실제로는 사용자 권한 확인 로직
        if ("prod".equals(request.getTargetEnvironment())) {
            throw new UnauthorizedException("운영 환경으로의 동기화 권한이 없습니다");
        }
    }
    
    private int calculateTotalRecords(Map<String, Object> analyticsData, 
                                    List<Map<String, Object>> hybridAnalysis,
                                    List<Map<String, Object>> trendsData) {
        int total = 0;
        if (analyticsData != null) {
            total += analyticsData.values().stream()
                .mapToInt(v -> v instanceof List ? ((List<?>) v).size() : 1)
                .sum();
        }
        if (hybridAnalysis != null) {
            total += hybridAnalysis.size();
        }
        if (trendsData != null) {
            total += trendsData.size();
        }
        return total;
    }
    
    private long calculateSyncedRecords(boolean syncResult) {
        return syncResult ? 15000L : 8500L; // 실제로는 동기화된 레코드 수 계산
    }
}

// DTO 클래스들 (연관관계 테스트용)

class CreateUserRequestDto {
    @NotBlank @Size(min = 3, max = 50)
    private String username;
    
    @Email @NotBlank
    private String email;
    
    @NotBlank @Size(min = 2, max = 100)
    private String fullName;
    
    @NotBlank @Pattern(regexp = "^(ADMIN|USER|MANAGER|GUEST)$")
    private String userType;
    
    @Min(1)
    private Long departmentId;
    
    private Map<String, Object> profileData;
    
    // getters and setters
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

class UpdateUserRequestDto {
    @Size(min = 2, max = 100)
    private String fullName;
    
    @Email
    private String email;
    
    @Min(1)
    private Long departmentId;
    
    @Pattern(regexp = "^(ACTIVE|INACTIVE|PENDING)$")
    private String status;
    
    // getters and setters
    public String getFullName() { return fullName; }
    public void setFullName(String fullName) { this.fullName = fullName; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public Long getDepartmentId() { return departmentId; }
    public void setDepartmentId(Long departmentId) { this.departmentId = departmentId; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}

// 추가 예외 클래스들
class ValidationException extends RuntimeException {
    public ValidationException(String message) {
        super(message);
    }
}

class InsufficientInventoryException extends RuntimeException {
    public InsufficientInventoryException(String message) {
        super(message);
    }
}

class UnauthorizedException extends RuntimeException {
    public UnauthorizedException(String message) {
        super(message);
    }
}
