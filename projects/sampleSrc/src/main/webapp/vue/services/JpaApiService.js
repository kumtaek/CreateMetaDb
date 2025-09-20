/**
 * JPA API Service Module
 * Vue 컴포넌트에서 사용할 API 호출 서비스들을 모듈화
 * FRONTEND_API -> API_ENTRY -> JPA Repository -> TABLE 연결 구조 테스트케이스
 */
import axios from 'axios'

// Axios 기본 설정
const apiClient = axios.create({
  baseURL: '/api/jpa',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 요청 인터셉터
apiClient.interceptors.request.use(
  config => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, config.params || config.data)
    return config
  },
  error => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// 응답 인터셉터
apiClient.interceptors.response.use(
  response => {
    console.log(`API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data)
    return response
  },
  error => {
    console.error('API Response Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

/**
 * User API Service
 * 사용자 관련 API 호출 서비스
 */
export const UserApiService = {
  /**
   * 전체 사용자 조회
   * FRONTEND_API: GET /api/jpa/users -> API_ENTRY: JpaUserController.getAllUsers()
   */
  getAllUsers() {
    return apiClient.get('/users')
  },

  /**
   * 사용자 조회 (ID)
   * FRONTEND_API: GET /api/jpa/users/{id} -> API_ENTRY: JpaUserController.getUserById()
   */
  getUserById(userId) {
    return apiClient.get(`/users/${userId}`)
  },

  /**
   * 사용자 생성
   * FRONTEND_API: POST /api/jpa/users -> API_ENTRY: JpaUserController.createUser()
   */
  createUser(userData) {
    return apiClient.post('/users', userData)
  },

  /**
   * 사용자 수정
   * FRONTEND_API: PUT /api/jpa/users/{id} -> API_ENTRY: JpaUserController.updateUser()
   */
  updateUser(userId, userData) {
    return apiClient.put(`/users/${userId}`, userData)
  },

  /**
   * 사용자 삭제
   * FRONTEND_API: DELETE /api/jpa/users/{id} -> API_ENTRY: JpaUserController.deleteUser()
   */
  deleteUser(userId) {
    return apiClient.delete(`/users/${userId}`)
  },

  /**
   * 사용자명으로 조회
   * FRONTEND_API: GET /api/jpa/users/by-username/{username} -> API_ENTRY: JpaUserController.getUserByUsername()
   */
  getUserByUsername(username) {
    return apiClient.get(`/users/by-username/${username}`)
  },

  /**
   * 이메일로 조회
   * FRONTEND_API: GET /api/jpa/users/by-email/{email} -> API_ENTRY: JpaUserController.getUserByEmail()
   */
  getUserByEmail(email) {
    return apiClient.get(`/users/by-email/${email}`)
  },

  /**
   * 상태별 사용자 조회
   * FRONTEND_API: GET /api/jpa/users/by-status/{status} -> API_ENTRY: JpaUserController.getUsersByStatus()
   */
  getUsersByStatus(status) {
    return apiClient.get(`/users/by-status/${status}`)
  },

  /**
   * 사용자 타입별 조회
   * FRONTEND_API: GET /api/jpa/users/by-type/{userType} -> API_ENTRY: JpaUserController.getUsersByUserType()
   */
  getUsersByUserType(userType) {
    return apiClient.get(`/users/by-type/${userType}`)
  },

  /**
   * 사용자명 검색
   * FRONTEND_API: GET /api/jpa/users/search/username -> API_ENTRY: JpaUserController.searchUsersByUsername()
   */
  searchUsersByUsername(query) {
    return apiClient.get('/users/search/username', { params: { q: query } })
  },

  /**
   * 이메일 검색
   * FRONTEND_API: GET /api/jpa/users/search/email -> API_ENTRY: JpaUserController.searchUsersByEmail()
   */
  searchUsersByEmail(query) {
    return apiClient.get('/users/search/email', { params: { q: query } })
  },

  /**
   * 전체 이름 검색
   * FRONTEND_API: GET /api/jpa/users/search/fullname -> API_ENTRY: JpaUserController.searchUsersByFullName()
   */
  searchUsersByFullName(query) {
    return apiClient.get('/users/search/fullname', { params: { q: query } })
  },

  /**
   * 동적 조건 검색
   * FRONTEND_API: GET /api/jpa/users/search -> API_ENTRY: JpaUserController.searchUsers()
   */
  searchUsers(searchCriteria, pageable = null) {
    const params = { ...searchCriteria }
    if (pageable) {
      params.page = pageable.page
      params.size = pageable.size
      params.sort = pageable.sort
    }
    return apiClient.get('/users/search', { params })
  },

  /**
   * 기간별 가입 사용자 조회
   * FRONTEND_API: GET /api/jpa/users/created-between -> API_ENTRY: JpaUserController.getUsersCreatedBetween()
   */
  getUsersCreatedBetween(startDate, endDate) {
    return apiClient.get('/users/created-between', {
      params: { startDate, endDate }
    })
  },

  /**
   * 특정 날짜 이후 가입 사용자
   * FRONTEND_API: GET /api/jpa/users/created-after -> API_ENTRY: JpaUserController.getUsersCreatedAfter()
   */
  getUsersCreatedAfter(date) {
    return apiClient.get('/users/created-after', { params: { date } })
  },

  /**
   * 로그인 이력이 없는 사용자
   * FRONTEND_API: GET /api/jpa/users/never-logged-in -> API_ENTRY: JpaUserController.getUsersWithoutLogin()
   */
  getUsersWithoutLogin() {
    return apiClient.get('/users/never-logged-in')
  },

  /**
   * 이메일 도메인별 사용자 조회
   * FRONTEND_API: GET /api/jpa/users/by-email-domain/{domain} -> API_ENTRY: JpaUserController.getUsersByEmailDomain()
   */
  getUsersByEmailDomain(domain) {
    return apiClient.get(`/users/by-email-domain/${domain}`)
  },

  /**
   * 주문 정보와 함께 사용자 조회
   * FRONTEND_API: GET /api/jpa/users/{id}/with-orders -> API_ENTRY: JpaUserController.getUserWithOrders()
   */
  getUserWithOrders(userId) {
    return apiClient.get(`/users/${userId}/with-orders`)
  },

  /**
   * 고액 주문 사용자 조회
   * FRONTEND_API: GET /api/jpa/users/high-value-orders -> API_ENTRY: JpaUserController.getUsersWithHighValueOrders()
   */
  getUsersWithHighValueOrders(minAmount) {
    return apiClient.get('/users/high-value-orders', { params: { minAmount } })
  },

  /**
   * 사용자 활성화
   * FRONTEND_API: PUT /api/jpa/users/{id}/activate -> API_ENTRY: JpaUserController.activateUser()
   */
  activateUser(userId) {
    return apiClient.put(`/users/${userId}/activate`)
  },

  /**
   * 사용자 비활성화
   * FRONTEND_API: PUT /api/jpa/users/{id}/deactivate -> API_ENTRY: JpaUserController.deactivateUser()
   */
  deactivateUser(userId) {
    return apiClient.put(`/users/${userId}/deactivate`)
  },

  /**
   * 프리미엄 사용자로 업그레이드
   * FRONTEND_API: PUT /api/jpa/users/{id}/upgrade-premium -> API_ENTRY: JpaUserController.upgradeUserToPremium()
   */
  upgradeUserToPremium(userId) {
    return apiClient.put(`/users/${userId}/upgrade-premium`)
  },

  /**
   * 로그인 시간 업데이트
   * FRONTEND_API: PUT /api/jpa/users/{id}/login -> API_ENTRY: JpaUserController.updateLastLoginTime()
   */
  updateLastLoginTime(userId) {
    return apiClient.put(`/users/${userId}/login`)
  },

  /**
   * 상태별 사용자 수
   * FRONTEND_API: GET /api/jpa/users/count/by-status/{status} -> API_ENTRY: JpaUserController.getUserCountByStatus()
   */
  getUserCountByStatus(status) {
    return apiClient.get(`/users/count/by-status/${status}`)
  },

  /**
   * 사용자 타입별 통계
   * FRONTEND_API: GET /api/jpa/users/statistics/by-type -> API_ENTRY: JpaUserController.getUserTypeStatistics()
   */
  getUserTypeStatistics() {
    return apiClient.get('/users/statistics/by-type')
  },

  /**
   * 상태별 통계 (기간별)
   * FRONTEND_API: GET /api/jpa/users/statistics/by-status -> API_ENTRY: JpaUserController.getUserStatusStatistics()
   */
  getUserStatusStatistics(fromDate) {
    return apiClient.get('/users/statistics/by-status', { params: { fromDate } })
  },

  /**
   * 사용자명 중복 확인
   * FRONTEND_API: GET /api/jpa/users/check/username/{username} -> API_ENTRY: JpaUserController.checkUsernameAvailability()
   */
  checkUsernameAvailability(username) {
    return apiClient.get(`/users/check/username/${username}`)
  },

  /**
   * 이메일 중복 확인
   * FRONTEND_API: GET /api/jpa/users/check/email/{email} -> API_ENTRY: JpaUserController.checkEmailAvailability()
   */
  checkEmailAvailability(email) {
    return apiClient.get(`/users/check/email/${email}`)
  },

  /**
   * 사용자 요약 정보 조회
   * FRONTEND_API: GET /api/jpa/users/summaries/by-status/{status} -> API_ENTRY: JpaUserController.getUserSummariesByStatus()
   */
  getUserSummariesByStatus(status) {
    return apiClient.get(`/users/summaries/by-status/${status}`)
  }
}

/**
 * Product API Service
 * 상품 관련 API 호출 서비스
 */
export const ProductApiService = {
  /**
   * 전체 상품 조회
   * FRONTEND_API: GET /api/jpa/products -> API_ENTRY: JpaProductController.getAllProducts()
   */
  getAllProducts() {
    return apiClient.get('/products')
  },

  /**
   * 상품 조회 (ID)
   * FRONTEND_API: GET /api/jpa/products/{id} -> API_ENTRY: JpaProductController.getProductById()
   */
  getProductById(productId) {
    return apiClient.get(`/products/${productId}`)
  },

  /**
   * 상품 생성
   * FRONTEND_API: POST /api/jpa/products -> API_ENTRY: JpaProductController.createProduct()
   */
  createProduct(productData) {
    return apiClient.post('/products', productData)
  },

  /**
   * 상품 수정
   * FRONTEND_API: PUT /api/jpa/products/{id} -> API_ENTRY: JpaProductController.updateProduct()
   */
  updateProduct(productId, productData) {
    return apiClient.put(`/products/${productId}`, productData)
  },

  /**
   * 상품 삭제
   * FRONTEND_API: DELETE /api/jpa/products/{id} -> API_ENTRY: JpaProductController.deleteProduct()
   */
  deleteProduct(productId) {
    return apiClient.delete(`/products/${productId}`)
  },

  /**
   * 상품 코드로 조회
   * FRONTEND_API: GET /api/jpa/products/by-code/{code} -> API_ENTRY: JpaProductController.getProductByCode()
   */
  getProductByCode(code) {
    return apiClient.get(`/products/by-code/${code}`)
  },

  /**
   * 상태별 상품 조회
   * FRONTEND_API: GET /api/jpa/products/by-status/{status} -> API_ENTRY: JpaProductController.getProductsByStatus()
   */
  getProductsByStatus(status) {
    return apiClient.get(`/products/by-status/${status}`)
  },

  /**
   * 카테고리별 상품 조회
   * FRONTEND_API: GET /api/jpa/products/by-category/{categoryId} -> API_ENTRY: JpaProductController.getProductsByCategory()
   */
  getProductsByCategory(categoryId) {
    return apiClient.get(`/products/by-category/${categoryId}`)
  },

  /**
   * 상품명 검색
   * FRONTEND_API: GET /api/jpa/products/search/name -> API_ENTRY: JpaProductController.searchProductsByName()
   */
  searchProductsByName(query) {
    return apiClient.get('/products/search/name', { params: { q: query } })
  },

  /**
   * 상품명 검색 (대소문자 무시)
   * FRONTEND_API: GET /api/jpa/products/search/name-ignore-case -> API_ENTRY: JpaProductController.searchProductsByNameIgnoreCase()
   */
  searchProductsByNameIgnoreCase(query) {
    return apiClient.get('/products/search/name-ignore-case', { params: { q: query } })
  },

  /**
   * 설명으로 검색
   * FRONTEND_API: GET /api/jpa/products/search/description -> API_ENTRY: JpaProductController.searchProductsByDescription()
   */
  searchProductsByDescription(query) {
    return apiClient.get('/products/search/description', { params: { q: query } })
  },

  /**
   * 가격 범위 검색
   * FRONTEND_API: GET /api/jpa/products/price-range -> API_ENTRY: JpaProductController.getProductsByPriceRange()
   */
  getProductsByPriceRange(minPrice, maxPrice) {
    return apiClient.get('/products/price-range', {
      params: { minPrice, maxPrice }
    })
  },

  /**
   * 최소 가격 이상 상품
   * FRONTEND_API: GET /api/jpa/products/price-above/{price} -> API_ENTRY: JpaProductController.getProductsAbovePrice()
   */
  getProductsAbovePrice(price) {
    return apiClient.get(`/products/price-above/${price}`)
  },

  /**
   * 최대 가격 이하 상품
   * FRONTEND_API: GET /api/jpa/products/price-below/{price} -> API_ENTRY: JpaProductController.getProductsBelowPrice()
   */
  getProductsBelowPrice(price) {
    return apiClient.get(`/products/price-below/${price}`)
  },

  /**
   * 재고 부족 상품 조회
   * FRONTEND_API: GET /api/jpa/products/low-stock -> API_ENTRY: JpaProductController.getLowStockProducts()
   */
  getLowStockProducts() {
    return apiClient.get('/products/low-stock')
  },

  /**
   * 품절 상품 조회
   * FRONTEND_API: GET /api/jpa/products/out-of-stock -> API_ENTRY: JpaProductController.getOutOfStockProducts()
   */
  getOutOfStockProducts() {
    return apiClient.get('/products/out-of-stock')
  },

  /**
   * 인기 상품 조회
   * FRONTEND_API: GET /api/jpa/products/popular -> API_ENTRY: JpaProductController.getPopularProducts()
   */
  getPopularProducts(minOrderCount) {
    return apiClient.get('/products/popular', { params: { minOrderCount } })
  },

  /**
   * 주문된 적 없는 상품
   * FRONTEND_API: GET /api/jpa/products/never-ordered -> API_ENTRY: JpaProductController.getNeverOrderedProducts()
   */
  getNeverOrderedProducts() {
    return apiClient.get('/products/never-ordered')
  },

  /**
   * 특정 날짜 이후 주문된 상품
   * FRONTEND_API: GET /api/jpa/products/ordered-after -> API_ENTRY: JpaProductController.getProductsOrderedAfterDate()
   */
  getProductsOrderedAfterDate(date) {
    return apiClient.get('/products/ordered-after', { params: { date } })
  },

  /**
   * 동적 조건 검색
   * FRONTEND_API: GET /api/jpa/products/search -> API_ENTRY: JpaProductController.searchProducts()
   */
  searchProducts(searchCriteria, pageable = null) {
    const params = { ...searchCriteria }
    if (pageable) {
      params.page = pageable.page
      params.size = pageable.size
      params.sort = pageable.sort
    }
    return apiClient.get('/products/search', { params })
  },

  /**
   * 재고 추가
   * FRONTEND_API: PUT /api/jpa/products/{id}/add-stock -> API_ENTRY: JpaProductController.addStock()
   */
  addStock(productId, quantity) {
    return apiClient.put(`/products/${productId}/add-stock`, null, {
      params: { quantity }
    })
  },

  /**
   * 재고 감소
   * FRONTEND_API: PUT /api/jpa/products/{id}/reduce-stock -> API_ENTRY: JpaProductController.reduceStock()
   */
  reduceStock(productId, quantity) {
    return apiClient.put(`/products/${productId}/reduce-stock`, null, {
      params: { quantity }
    })
  },

  /**
   * 재고 업데이트
   * FRONTEND_API: PUT /api/jpa/products/{id}/stock -> API_ENTRY: JpaProductController.updateProductStock()
   */
  updateProductStock(productId, stock) {
    return apiClient.put(`/products/${productId}/stock`, null, {
      params: { stock }
    })
  },

  /**
   * 상품 활성화
   * FRONTEND_API: PUT /api/jpa/products/{id}/activate -> API_ENTRY: JpaProductController.activateProduct()
   */
  activateProduct(productId) {
    return apiClient.put(`/products/${productId}/activate`)
  },

  /**
   * 상품 비활성화
   * FRONTEND_API: PUT /api/jpa/products/{id}/deactivate -> API_ENTRY: JpaProductController.deactivateProduct()
   */
  deactivateProduct(productId) {
    return apiClient.put(`/products/${productId}/deactivate`)
  },

  /**
   * 가격 업데이트
   * FRONTEND_API: PUT /api/jpa/products/{id}/price -> API_ENTRY: JpaProductController.updateProductPrice()
   */
  updateProductPrice(productId, price) {
    return apiClient.put(`/products/${productId}/price`, null, {
      params: { price }
    })
  },

  /**
   * 상태별 상품 수
   * FRONTEND_API: GET /api/jpa/products/count/by-status/{status} -> API_ENTRY: JpaProductController.getProductCountByStatus()
   */
  getProductCountByStatus(status) {
    return apiClient.get(`/products/count/by-status/${status}`)
  },

  /**
   * 카테고리별 상품 수
   * FRONTEND_API: GET /api/jpa/products/count/by-category/{categoryId} -> API_ENTRY: JpaProductController.getProductCountByCategory()
   */
  getProductCountByCategory(categoryId) {
    return apiClient.get(`/products/count/by-category/${categoryId}`)
  },

  /**
   * 상태별 평균 가격
   * FRONTEND_API: GET /api/jpa/products/average-price/by-status/{status} -> API_ENTRY: JpaProductController.getAveragePriceByStatus()
   */
  getAveragePriceByStatus(status) {
    return apiClient.get(`/products/average-price/by-status/${status}`)
  },

  /**
   * 전체 활성 재고
   * FRONTEND_API: GET /api/jpa/products/total-active-stock -> API_ENTRY: JpaProductController.getTotalActiveStock()
   */
  getTotalActiveStock() {
    return apiClient.get('/products/total-active-stock')
  },

  /**
   * 카테고리별 상품 수 통계
   * FRONTEND_API: GET /api/jpa/products/statistics/by-category -> API_ENTRY: JpaProductController.getProductCountByCategory()
   */
  getProductCountByCategoryStatistics() {
    return apiClient.get('/products/statistics/by-category')
  },

  /**
   * 카테고리별 상품 요약 정보
   * FRONTEND_API: GET /api/jpa/products/summaries/by-category/{categoryId} -> API_ENTRY: JpaProductController.getProductSummariesByCategory()
   */
  getProductSummariesByCategory(categoryId) {
    return apiClient.get(`/products/summaries/by-category/${categoryId}`)
  }
}

/**
 * Order API Service
 * 주문 관련 API 호출 서비스
 */
export const OrderApiService = {
  /**
   * 전체 주문 조회
   * FRONTEND_API: GET /api/jpa/orders -> API_ENTRY: JpaOrderController.getAllOrders()
   */
  getAllOrders() {
    return apiClient.get('/orders')
  },

  /**
   * 주문 조회 (ID)
   * FRONTEND_API: GET /api/jpa/orders/{id} -> API_ENTRY: JpaOrderController.getOrderById()
   */
  getOrderById(orderId) {
    return apiClient.get(`/orders/${orderId}`)
  },

  /**
   * 주문 생성
   * FRONTEND_API: POST /api/jpa/orders -> API_ENTRY: JpaOrderController.createOrder()
   */
  createOrder(orderData) {
    return apiClient.post('/orders', orderData)
  },

  /**
   * 주문 수정
   * FRONTEND_API: PUT /api/jpa/orders/{id} -> API_ENTRY: JpaOrderController.updateOrder()
   */
  updateOrder(orderId, orderData) {
    return apiClient.put(`/orders/${orderId}`, orderData)
  },

  /**
   * 주문 삭제
   * FRONTEND_API: DELETE /api/jpa/orders/{id} -> API_ENTRY: JpaOrderController.deleteOrder()
   */
  deleteOrder(orderId) {
    return apiClient.delete(`/orders/${orderId}`)
  },

  /**
   * 주문번호로 조회
   * FRONTEND_API: GET /api/jpa/orders/by-number/{orderNumber} -> API_ENTRY: JpaOrderController.getOrderByOrderNumber()
   */
  getOrderByOrderNumber(orderNumber) {
    return apiClient.get(`/orders/by-number/${orderNumber}`)
  },

  /**
   * 주문 상세 정보 조회
   * FRONTEND_API: GET /api/jpa/orders/details/{orderNumber} -> API_ENTRY: JpaOrderController.getOrderWithDetails()
   */
  getOrderWithDetails(orderNumber) {
    return apiClient.get(`/orders/details/${orderNumber}`)
  },

  /**
   * 주문 아이템과 함께 조회
   * FRONTEND_API: GET /api/jpa/orders/{id}/with-items -> API_ENTRY: JpaOrderController.getOrderWithItems()
   */
  getOrderWithItems(orderId) {
    return apiClient.get(`/orders/${orderId}/with-items`)
  },

  /**
   * 상태별 주문 조회
   * FRONTEND_API: GET /api/jpa/orders/by-status/{status} -> API_ENTRY: JpaOrderController.getOrdersByStatus()
   */
  getOrdersByStatus(status) {
    return apiClient.get(`/orders/by-status/${status}`)
  },

  /**
   * 사용자별 주문 조회
   * FRONTEND_API: GET /api/jpa/orders/by-user/{userId} -> API_ENTRY: JpaOrderController.getOrdersByUserId()
   */
  getOrdersByUserId(userId) {
    return apiClient.get(`/orders/by-user/${userId}`)
  },

  /**
   * 기간별 주문 조회
   * FRONTEND_API: GET /api/jpa/orders/between-dates -> API_ENTRY: JpaOrderController.getOrdersBetweenDates()
   */
  getOrdersBetweenDates(startDate, endDate) {
    return apiClient.get('/orders/between-dates', {
      params: { startDate, endDate }
    })
  },

  /**
   * 특정 날짜 이후 주문
   * FRONTEND_API: GET /api/jpa/orders/after-date -> API_ENTRY: JpaOrderController.getOrdersAfterDate()
   */
  getOrdersAfterDate(date) {
    return apiClient.get('/orders/after-date', { params: { date } })
  },

  /**
   * 최소 금액 이상 주문
   * FRONTEND_API: GET /api/jpa/orders/above-amount/{amount} -> API_ENTRY: JpaOrderController.getOrdersAboveAmount()
   */
  getOrdersAboveAmount(amount) {
    return apiClient.get(`/orders/above-amount/${amount}`)
  },

  /**
   * 금액 범위별 주문
   * FRONTEND_API: GET /api/jpa/orders/amount-range -> API_ENTRY: JpaOrderController.getOrdersByAmountRange()
   */
  getOrdersByAmountRange(minAmount, maxAmount) {
    return apiClient.get('/orders/amount-range', {
      params: { minAmount, maxAmount }
    })
  },

  /**
   * 동적 조건 검색
   * FRONTEND_API: GET /api/jpa/orders/search -> API_ENTRY: JpaOrderController.searchOrders()
   */
  searchOrders(searchCriteria, pageable = null) {
    const params = { ...searchCriteria }
    if (pageable) {
      params.page = pageable.page
      params.size = pageable.size
      params.sort = pageable.sort
    }
    return apiClient.get('/orders/search', { params })
  },

  /**
   * 프리미엄 사용자 주문
   * FRONTEND_API: GET /api/jpa/orders/premium-users -> API_ENTRY: JpaOrderController.getOrdersByPremiumUsers()
   */
  getOrdersByPremiumUsers() {
    return apiClient.get('/orders/premium-users')
  },

  /**
   * 특정 상품이 포함된 주문
   * FRONTEND_API: GET /api/jpa/orders/containing-product -> API_ENTRY: JpaOrderController.getOrdersContainingProduct()
   */
  getOrdersContainingProduct(productName) {
    return apiClient.get('/orders/containing-product', {
      params: { productName }
    })
  },

  /**
   * 주문 확인
   * FRONTEND_API: PUT /api/jpa/orders/{id}/confirm -> API_ENTRY: JpaOrderController.confirmOrder()
   */
  confirmOrder(orderId) {
    return apiClient.put(`/orders/${orderId}/confirm`)
  },

  /**
   * 주문 취소
   * FRONTEND_API: PUT /api/jpa/orders/{id}/cancel -> API_ENTRY: JpaOrderController.cancelOrder()
   */
  cancelOrder(orderId) {
    return apiClient.put(`/orders/${orderId}/cancel`)
  },

  /**
   * 주문 처리
   * FRONTEND_API: PUT /api/jpa/orders/{id}/process -> API_ENTRY: JpaOrderController.processOrder()
   */
  processOrder(orderId) {
    return apiClient.put(`/orders/${orderId}/process`)
  },

  /**
   * 주문 배송
   * FRONTEND_API: PUT /api/jpa/orders/{id}/ship -> API_ENTRY: JpaOrderController.shipOrder()
   */
  shipOrder(orderId) {
    return apiClient.put(`/orders/${orderId}/ship`)
  },

  /**
   * 주문 완료
   * FRONTEND_API: PUT /api/jpa/orders/{id}/complete -> API_ENTRY: JpaOrderController.completeOrder()
   */
  completeOrder(orderId) {
    return apiClient.put(`/orders/${orderId}/complete`)
  },

  /**
   * 배송 주소 변경
   * FRONTEND_API: PUT /api/jpa/orders/{id}/shipping-address -> API_ENTRY: JpaOrderController.updateShippingAddress()
   */
  updateShippingAddress(orderId, address) {
    return apiClient.put(`/orders/${orderId}/shipping-address`, null, {
      params: { address }
    })
  },

  /**
   * 주문 총액 업데이트
   * FRONTEND_API: PUT /api/jpa/orders/{id}/total -> API_ENTRY: JpaOrderController.updateOrderTotal()
   */
  updateOrderTotal(orderId, total) {
    return apiClient.put(`/orders/${orderId}/total`, null, {
      params: { total }
    })
  },

  /**
   * 할인 적용
   * FRONTEND_API: PUT /api/jpa/orders/{id}/discount -> API_ENTRY: JpaOrderController.applyDiscount()
   */
  applyDiscount(orderId, discountAmount) {
    return apiClient.put(`/orders/${orderId}/discount`, null, {
      params: { discountAmount }
    })
  },

  /**
   * 상태별 주문 수
   * FRONTEND_API: GET /api/jpa/orders/count/by-status/{status} -> API_ENTRY: JpaOrderController.getOrderCountByStatus()
   */
  getOrderCountByStatus(status) {
    return apiClient.get(`/orders/count/by-status/${status}`)
  },

  /**
   * 사용자별 주문 수
   * FRONTEND_API: GET /api/jpa/orders/count/by-user/{userId} -> API_ENTRY: JpaOrderController.getOrderCountByUserId()
   */
  getOrderCountByUserId(userId) {
    return apiClient.get(`/orders/count/by-user/${userId}`)
  },

  /**
   * 사용자 총 주문 금액
   * FRONTEND_API: GET /api/jpa/orders/total-amount/by-user/{userId} -> API_ENTRY: JpaOrderController.getUserTotalAmount()
   */
  getUserTotalAmount(userId) {
    return apiClient.get(`/orders/total-amount/by-user/${userId}`)
  },

  /**
   * 상태별 평균 주문 금액
   * FRONTEND_API: GET /api/jpa/orders/average-amount/by-status/{status} -> API_ENTRY: JpaOrderController.getAverageOrderAmountByStatus()
   */
  getAverageOrderAmountByStatus(status) {
    return apiClient.get(`/orders/average-amount/by-status/${status}`)
  },

  /**
   * 상태별 주문 통계
   * FRONTEND_API: GET /api/jpa/orders/statistics/by-status -> API_ENTRY: JpaOrderController.getOrderCountByStatus()
   */
  getOrderStatisticsByStatus() {
    return apiClient.get('/orders/statistics/by-status')
  },

  /**
   * 일별 주문 통계
   * FRONTEND_API: GET /api/jpa/orders/statistics/daily -> API_ENTRY: JpaOrderController.getDailyOrderCount()
   */
  getDailyOrderStatistics(fromDate) {
    return apiClient.get('/orders/statistics/daily', { params: { fromDate } })
  },

  /**
   * 최고 고객 통계
   * FRONTEND_API: GET /api/jpa/orders/statistics/top-customers -> API_ENTRY: JpaOrderController.getTopCustomersByTotalAmount()
   */
  getTopCustomersStatistics() {
    return apiClient.get('/orders/statistics/top-customers')
  },

  /**
   * 주문 요약 정보 조회
   * FRONTEND_API: GET /api/jpa/orders/summaries/by-status/{status} -> API_ENTRY: JpaOrderController.getOrderSummariesByStatus()
   */
  getOrderSummariesByStatus(status) {
    return apiClient.get(`/orders/summaries/by-status/${status}`)
  }
}

// 기본 내보내기
export default {
  UserApiService,
  ProductApiService,
  OrderApiService
}

