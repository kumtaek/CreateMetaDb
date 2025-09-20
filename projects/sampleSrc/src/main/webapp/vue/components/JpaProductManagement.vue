<template>
  <div class="jpa-product-management">
    <h2>JPA 상품 관리 시스템</h2>
    
    <!-- 에러 메시지 -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
    
    <!-- 성공 메시지 -->
    <div v-if="successMessage" class="success-message">
      {{ successMessage }}
    </div>
    
    <!-- 상품 생성/수정 폼 -->
    <div class="product-form-section">
      <h3>{{ editingProduct ? '상품 수정' : '상품 생성' }}</h3>
      <form @submit.prevent="saveProduct" class="product-form">
        <div class="form-group">
          <label>상품명:</label>
          <input 
            v-model="productForm.productName" 
            type="text" 
            required 
            placeholder="상품명 입력"
          />
        </div>
        
        <div class="form-group">
          <label>상품 코드:</label>
          <input 
            v-model="productForm.productCode" 
            type="text" 
            required 
            placeholder="상품 코드 입력"
          />
        </div>
        
        <div class="form-group">
          <label>설명:</label>
          <textarea 
            v-model="productForm.description" 
            placeholder="상품 설명 입력"
            rows="3"
          ></textarea>
        </div>
        
        <div class="form-group">
          <label>가격:</label>
          <input 
            v-model.number="productForm.price" 
            type="number" 
            step="0.01" 
            required 
            placeholder="가격 입력"
          />
        </div>
        
        <div class="form-group">
          <label>재고 수량:</label>
          <input 
            v-model.number="productForm.stockQuantity" 
            type="number" 
            placeholder="재고 수량 입력"
          />
        </div>
        
        <div class="form-group">
          <label>최소 재고 수준:</label>
          <input 
            v-model.number="productForm.minStockLevel" 
            type="number" 
            placeholder="최소 재고 수준"
          />
        </div>
        
        <div class="form-group">
          <label>상태:</label>
          <select v-model="productForm.status" required>
            <option value="ACTIVE">판매중</option>
            <option value="INACTIVE">판매중지</option>
            <option value="OUT_OF_STOCK">품절</option>
            <option value="DISCONTINUED">단종</option>
            <option value="PENDING">승인대기</option>
          </select>
        </div>
        
        <div class="form-actions">
          <button type="submit" :disabled="loading">
            {{ loading ? '처리중...' : (editingProduct ? '수정' : '생성') }}
          </button>
          <button type="button" @click="resetForm" :disabled="loading">
            초기화
          </button>
        </div>
      </form>
    </div>
    
    <!-- 검색 섹션 -->
    <div class="search-section">
      <h3>상품 검색</h3>
      
      <!-- 기본 검색 -->
      <div class="basic-search">
        <h4>기본 검색</h4>
        <div class="search-form">
          <input 
            v-model="basicSearch.productName" 
            type="text" 
            placeholder="상품명 검색"
          />
          <input 
            v-model="basicSearch.productCode" 
            type="text" 
            placeholder="상품 코드 검색"
          />
          <input 
            v-model="basicSearch.description" 
            type="text" 
            placeholder="설명 검색"
          />
          <button @click="performBasicSearch" :disabled="loading">
            기본 검색
          </button>
        </div>
      </div>
      
      <!-- 고급 검색 -->
      <div class="advanced-search">
        <h4>고급 검색</h4>
        <div class="search-form">
          <select v-model="advancedSearch.status">
            <option value="">전체 상태</option>
            <option value="ACTIVE">판매중</option>
            <option value="INACTIVE">판매중지</option>
            <option value="OUT_OF_STOCK">품절</option>
            <option value="DISCONTINUED">단종</option>
            <option value="PENDING">승인대기</option>
          </select>
          
          <input 
            v-model.number="advancedSearch.minPrice" 
            type="number" 
            step="0.01" 
            placeholder="최소 가격"
          />
          
          <input 
            v-model.number="advancedSearch.maxPrice" 
            type="number" 
            step="0.01" 
            placeholder="최대 가격"
          />
          
          <input 
            v-model.number="advancedSearch.minStock" 
            type="number" 
            placeholder="최소 재고"
          />
          
          <button @click="performAdvancedSearch" :disabled="loading">
            고급 검색
          </button>
          
          <button @click="loadAllProducts" :disabled="loading">
            전체 조회
          </button>
        </div>
      </div>
      
      <!-- 특수 검색 -->
      <div class="special-search">
        <h4>특수 검색</h4>
        <div class="search-form">
          <button @click="searchLowStockProducts" :disabled="loading">
            재고 부족 상품
          </button>
          <button @click="searchOutOfStockProducts" :disabled="loading">
            품절 상품
          </button>
          <button @click="searchPopularProducts" :disabled="loading">
            인기 상품
          </button>
          <button @click="searchNeverOrderedProducts" :disabled="loading">
            주문된 적 없는 상품
          </button>
        </div>
      </div>
    </div>
    
    <!-- 재고 관리 섹션 -->
    <div class="stock-management-section">
      <h3>재고 관리</h3>
      <div class="stock-form">
        <input 
          v-model.number="stockForm.productId" 
          type="number" 
          placeholder="상품 ID"
          required
        />
        <input 
          v-model.number="stockForm.quantity" 
          type="number" 
          placeholder="수량"
          required
        />
        <button @click="addStock" :disabled="loading">
          재고 추가
        </button>
        <button @click="reduceStock" :disabled="loading">
          재고 감소
        </button>
        <button @click="updateStock" :disabled="loading">
          재고 설정
        </button>
      </div>
    </div>
    
    <!-- 통계 섹션 -->
    <div class="statistics-section">
      <h3>상품 통계</h3>
      <div class="stats-grid">
        <div class="stat-item" v-for="stat in productStatistics" :key="stat.label">
          <span class="stat-label">{{ stat.label }}:</span>
          <span class="stat-value">{{ stat.value }}</span>
        </div>
      </div>
      <button @click="loadStatistics" :disabled="loading">
        통계 새로고침
      </button>
    </div>
    
    <!-- 상품 목록 -->
    <div class="products-list-section">
      <h3>상품 목록 ({{ products.length }}개)</h3>
      
      <div v-if="loading" class="loading">
        데이터를 불러오는 중...
      </div>
      
      <div v-else-if="products.length === 0" class="no-data">
        검색 결과가 없습니다.
      </div>
      
      <div v-else class="products-table">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>상품명</th>
              <th>상품 코드</th>
              <th>가격</th>
              <th>재고</th>
              <th>최소재고</th>
              <th>상태</th>
              <th>등록일</th>
              <th>작업</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="product in products" :key="product.productId">
              <td>{{ product.productId }}</td>
              <td>{{ product.productName }}</td>
              <td>{{ product.productCode }}</td>
              <td>{{ formatCurrency(product.price) }}</td>
              <td>
                <span :class="getStockClass(product)">
                  {{ product.stockQuantity || 0 }}
                </span>
              </td>
              <td>{{ product.minStockLevel || 0 }}</td>
              <td>
                <span :class="'status-' + product.status.toLowerCase()">
                  {{ getStatusText(product.status) }}
                </span>
              </td>
              <td>{{ formatDate(product.createdAt) }}</td>
              <td class="actions">
                <button @click="editProduct(product)" class="btn-edit">수정</button>
                <button @click="viewProductDetails(product)" class="btn-view">상세보기</button>
                <button 
                  v-if="product.status === 'ACTIVE'" 
                  @click="deactivateProduct(product.productId)" 
                  class="btn-deactivate"
                >
                  판매중지
                </button>
                <button 
                  v-else 
                  @click="activateProduct(product.productId)" 
                  class="btn-activate"
                >
                  판매시작
                </button>
                <button @click="showPriceUpdateModal(product)" class="btn-price">
                  가격수정
                </button>
                <button @click="deleteProduct(product.productId)" class="btn-delete">삭제</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- 상품 상세 정보 모달 -->
    <div v-if="selectedProduct" class="modal-overlay" @click="closeProductModal">
      <div class="modal-content" @click.stop>
        <h3>상품 상세 정보</h3>
        <div class="product-details">
          <p><strong>상품 ID:</strong> {{ selectedProduct.productId }}</p>
          <p><strong>상품명:</strong> {{ selectedProduct.productName }}</p>
          <p><strong>상품 코드:</strong> {{ selectedProduct.productCode }}</p>
          <p><strong>설명:</strong> {{ selectedProduct.description || '-' }}</p>
          <p><strong>가격:</strong> {{ formatCurrency(selectedProduct.price) }}</p>
          <p><strong>재고 수량:</strong> {{ selectedProduct.stockQuantity || 0 }}</p>
          <p><strong>최소 재고 수준:</strong> {{ selectedProduct.minStockLevel || 0 }}</p>
          <p><strong>상태:</strong> {{ getStatusText(selectedProduct.status) }}</p>
          <p><strong>등록일:</strong> {{ formatDate(selectedProduct.createdAt) }}</p>
          <p><strong>수정일:</strong> {{ formatDate(selectedProduct.updatedAt) }}</p>
          
          <div class="stock-status">
            <h4>재고 상태</h4>
            <p v-if="isOutOfStock(selectedProduct)" class="stock-warning">
              ⚠️ 품절 상태입니다.
            </p>
            <p v-else-if="isLowStock(selectedProduct)" class="stock-warning">
              ⚠️ 재고가 부족합니다.
            </p>
            <p v-else class="stock-ok">
              ✅ 재고 충분합니다.
            </p>
          </div>
        </div>
        <button @click="closeProductModal" class="btn-close">닫기</button>
      </div>
    </div>
    
    <!-- 가격 수정 모달 -->
    <div v-if="priceUpdateModal.show" class="modal-overlay" @click="closePriceUpdateModal">
      <div class="modal-content" @click.stop>
        <h3>가격 수정</h3>
        <p><strong>상품:</strong> {{ priceUpdateModal.product.productName }}</p>
        <p><strong>현재 가격:</strong> {{ formatCurrency(priceUpdateModal.product.price) }}</p>
        
        <div class="form-group">
          <label>새 가격:</label>
          <input 
            v-model.number="priceUpdateModal.newPrice" 
            type="number" 
            step="0.01" 
            required 
            placeholder="새 가격 입력"
          />
        </div>
        
        <div class="modal-actions">
          <button @click="updateProductPrice" :disabled="loading">
            {{ loading ? '처리중...' : '가격 수정' }}
          </button>
          <button @click="closePriceUpdateModal" :disabled="loading">
            취소
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * JPA Product Management Vue Component
 * FRONTEND_API -> API_ENTRY -> JPA Repository -> TABLE 연결 구조 테스트케이스
 * 
 * 연결 구조:
 * Vue Component -> axios API calls -> JpaProductController -> JpaProductService -> ProductRepository -> PRODUCTS TABLE
 */
import axios from 'axios'

export default {
  name: 'JpaProductManagement',
  data() {
    return {
      loading: false,
      error: null,
      successMessage: null,
      products: [],
      editingProduct: null,
      selectedProduct: null,
      
      // 상품 폼 데이터
      productForm: {
        productName: '',
        productCode: '',
        description: '',
        price: null,
        stockQuantity: null,
        minStockLevel: 10,
        status: 'ACTIVE'
      },
      
      // 검색 폼들
      basicSearch: {
        productName: '',
        productCode: '',
        description: ''
      },
      
      advancedSearch: {
        status: '',
        minPrice: null,
        maxPrice: null,
        minStock: null
      },
      
      // 재고 관리 폼
      stockForm: {
        productId: null,
        quantity: null
      },
      
      // 가격 수정 모달
      priceUpdateModal: {
        show: false,
        product: null,
        newPrice: null
      },
      
      // 통계 데이터
      productStatistics: []
    }
  },
  
  mounted() {
    this.loadAllProducts()
    this.loadStatistics()
  },
  
  methods: {
    // API 호출 메서드들
    
    /**
     * 전체 상품 조회
     * FRONTEND_API: GET /api/jpa/products -> API_ENTRY: JpaProductController.getAllProducts()
     */
    async loadAllProducts() {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get('/api/jpa/products')
        this.products = response.data
      } catch (error) {
        this.error = '상품 목록 조회 중 오류가 발생했습니다: ' + error.message
        console.error('상품 목록 조회 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 상품 생성/수정
     * FRONTEND_API: POST /api/jpa/products (생성) 또는 PUT /api/jpa/products/{id} (수정) -> API_ENTRY: JpaProductController.createProduct() / updateProduct()
     */
    async saveProduct() {
      this.loading = true
      this.error = null
      this.successMessage = null
      
      try {
        if (this.editingProduct) {
          // 수정
          await axios.put(`/api/jpa/products/${this.editingProduct.productId}`, this.productForm)
          this.successMessage = '상품이 성공적으로 수정되었습니다.'
        } else {
          // 생성
          await axios.post('/api/jpa/products', this.productForm)
          this.successMessage = '상품이 성공적으로 생성되었습니다.'
        }
        
        this.resetForm()
        this.loadAllProducts()
      } catch (error) {
        this.error = '상품 저장 중 오류가 발생했습니다: ' + error.message
        console.error('상품 저장 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 기본 검색 수행
     * FRONTEND_API: GET /api/jpa/products/search/name, /api/jpa/products/by-code/{code} -> API_ENTRY: JpaProductController.searchProducts*()
     */
    async performBasicSearch() {
      this.loading = true
      this.error = null
      
      try {
        let searchResults = []
        
        if (this.basicSearch.productName) {
          const response = await axios.get('/api/jpa/products/search/name', {
            params: { q: this.basicSearch.productName }
          })
          searchResults = [...searchResults, ...response.data]
        }
        
        if (this.basicSearch.productCode) {
          try {
            const response = await axios.get(`/api/jpa/products/by-code/${this.basicSearch.productCode}`)
            if (response.data) {
              searchResults = [...searchResults, response.data]
            }
          } catch (error) {
            // 상품 코드로 찾지 못한 경우는 무시
          }
        }
        
        if (this.basicSearch.description) {
          const response = await axios.get('/api/jpa/products/search/description', {
            params: { q: this.basicSearch.description }
          })
          searchResults = [...searchResults, ...response.data]
        }
        
        // 중복 제거
        const uniqueProducts = searchResults.filter((product, index, self) => 
          index === self.findIndex(p => p.productId === product.productId)
        )
        
        this.products = uniqueProducts
      } catch (error) {
        this.error = '기본 검색 중 오류가 발생했습니다: ' + error.message
        console.error('기본 검색 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 고급 검색 수행
     * FRONTEND_API: GET /api/jpa/products/by-status/{status}, /api/jpa/products/price-range -> API_ENTRY: JpaProductController.getProductsByStatus(), getProductsByPriceRange()
     */
    async performAdvancedSearch() {
      this.loading = true
      this.error = null
      
      try {
        if (this.advancedSearch.status) {
          const response = await axios.get(`/api/jpa/products/by-status/${this.advancedSearch.status}`)
          this.products = response.data
        } else if (this.advancedSearch.minPrice && this.advancedSearch.maxPrice) {
          const response = await axios.get('/api/jpa/products/price-range', {
            params: {
              minPrice: this.advancedSearch.minPrice,
              maxPrice: this.advancedSearch.maxPrice
            }
          })
          this.products = response.data
        } else if (this.advancedSearch.minPrice) {
          const response = await axios.get(`/api/jpa/products/price-above/${this.advancedSearch.minPrice}`)
          this.products = response.data
        } else {
          this.loadAllProducts()
          return
        }
      } catch (error) {
        this.error = '고급 검색 중 오류가 발생했습니다: ' + error.message
        console.error('고급 검색 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 재고 부족 상품 검색
     * FRONTEND_API: GET /api/jpa/products/low-stock -> API_ENTRY: JpaProductController.getLowStockProducts()
     */
    async searchLowStockProducts() {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get('/api/jpa/products/low-stock')
        this.products = response.data
      } catch (error) {
        this.error = '재고 부족 상품 검색 중 오류가 발생했습니다: ' + error.message
        console.error('재고 부족 상품 검색 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 품절 상품 검색
     * FRONTEND_API: GET /api/jpa/products/out-of-stock -> API_ENTRY: JpaProductController.getOutOfStockProducts()
     */
    async searchOutOfStockProducts() {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get('/api/jpa/products/out-of-stock')
        this.products = response.data
      } catch (error) {
        this.error = '품절 상품 검색 중 오류가 발생했습니다: ' + error.message
        console.error('품절 상품 검색 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 인기 상품 검색
     * FRONTEND_API: GET /api/jpa/products/popular -> API_ENTRY: JpaProductController.getPopularProducts()
     */
    async searchPopularProducts() {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get('/api/jpa/products/popular', {
          params: { minOrderCount: 5 }
        })
        this.products = response.data
      } catch (error) {
        this.error = '인기 상품 검색 중 오류가 발생했습니다: ' + error.message
        console.error('인기 상품 검색 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 주문된 적 없는 상품 검색
     * FRONTEND_API: GET /api/jpa/products/never-ordered -> API_ENTRY: JpaProductController.getNeverOrderedProducts()
     */
    async searchNeverOrderedProducts() {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get('/api/jpa/products/never-ordered')
        this.products = response.data
      } catch (error) {
        this.error = '주문된 적 없는 상품 검색 중 오류가 발생했습니다: ' + error.message
        console.error('주문된 적 없는 상품 검색 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 재고 추가
     * FRONTEND_API: PUT /api/jpa/products/{id}/add-stock -> API_ENTRY: JpaProductController.addStock()
     */
    async addStock() {
      if (!this.stockForm.productId || !this.stockForm.quantity) {
        this.error = '상품 ID와 수량을 모두 입력해주세요.'
        return
      }
      
      this.loading = true
      this.error = null
      
      try {
        await axios.put(`/api/jpa/products/${this.stockForm.productId}/add-stock`, null, {
          params: { quantity: this.stockForm.quantity }
        })
        this.successMessage = `상품 ${this.stockForm.productId}의 재고가 ${this.stockForm.quantity}개 추가되었습니다.`
        this.loadAllProducts()
        this.stockForm = { productId: null, quantity: null }
      } catch (error) {
        this.error = '재고 추가 중 오류가 발생했습니다: ' + error.message
        console.error('재고 추가 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 재고 감소
     * FRONTEND_API: PUT /api/jpa/products/{id}/reduce-stock -> API_ENTRY: JpaProductController.reduceStock()
     */
    async reduceStock() {
      if (!this.stockForm.productId || !this.stockForm.quantity) {
        this.error = '상품 ID와 수량을 모두 입력해주세요.'
        return
      }
      
      this.loading = true
      this.error = null
      
      try {
        await axios.put(`/api/jpa/products/${this.stockForm.productId}/reduce-stock`, null, {
          params: { quantity: this.stockForm.quantity }
        })
        this.successMessage = `상품 ${this.stockForm.productId}의 재고가 ${this.stockForm.quantity}개 감소되었습니다.`
        this.loadAllProducts()
        this.stockForm = { productId: null, quantity: null }
      } catch (error) {
        this.error = '재고 감소 중 오류가 발생했습니다: ' + error.message
        console.error('재고 감소 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 재고 설정
     * FRONTEND_API: PUT /api/jpa/products/{id}/stock -> API_ENTRY: JpaProductController.updateProductStock()
     */
    async updateStock() {
      if (!this.stockForm.productId || this.stockForm.quantity === null) {
        this.error = '상품 ID와 수량을 모두 입력해주세요.'
        return
      }
      
      this.loading = true
      this.error = null
      
      try {
        await axios.put(`/api/jpa/products/${this.stockForm.productId}/stock`, null, {
          params: { stock: this.stockForm.quantity }
        })
        this.successMessage = `상품 ${this.stockForm.productId}의 재고가 ${this.stockForm.quantity}개로 설정되었습니다.`
        this.loadAllProducts()
        this.stockForm = { productId: null, quantity: null }
      } catch (error) {
        this.error = '재고 설정 중 오류가 발생했습니다: ' + error.message
        console.error('재고 설정 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 상품 활성화
     * FRONTEND_API: PUT /api/jpa/products/{id}/activate -> API_ENTRY: JpaProductController.activateProduct()
     */
    async activateProduct(productId) {
      this.loading = true
      this.error = null
      
      try {
        await axios.put(`/api/jpa/products/${productId}/activate`)
        this.successMessage = '상품이 활성화되었습니다.'
        this.loadAllProducts()
      } catch (error) {
        this.error = '상품 활성화 중 오류가 발생했습니다: ' + error.message
        console.error('상품 활성화 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 상품 비활성화
     * FRONTEND_API: PUT /api/jpa/products/{id}/deactivate -> API_ENTRY: JpaProductController.deactivateProduct()
     */
    async deactivateProduct(productId) {
      this.loading = true
      this.error = null
      
      try {
        await axios.put(`/api/jpa/products/${productId}/deactivate`)
        this.successMessage = '상품이 비활성화되었습니다.'
        this.loadAllProducts()
      } catch (error) {
        this.error = '상품 비활성화 중 오류가 발생했습니다: ' + error.message
        console.error('상품 비활성화 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 가격 수정
     * FRONTEND_API: PUT /api/jpa/products/{id}/price -> API_ENTRY: JpaProductController.updateProductPrice()
     */
    async updateProductPrice() {
      if (!this.priceUpdateModal.newPrice) {
        this.error = '새 가격을 입력해주세요.'
        return
      }
      
      this.loading = true
      this.error = null
      
      try {
        await axios.put(`/api/jpa/products/${this.priceUpdateModal.product.productId}/price`, null, {
          params: { price: this.priceUpdateModal.newPrice }
        })
        this.successMessage = `상품 가격이 ${this.formatCurrency(this.priceUpdateModal.newPrice)}로 수정되었습니다.`
        this.closePriceUpdateModal()
        this.loadAllProducts()
      } catch (error) {
        this.error = '가격 수정 중 오류가 발생했습니다: ' + error.message
        console.error('가격 수정 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 상품 삭제
     * FRONTEND_API: DELETE /api/jpa/products/{id} -> API_ENTRY: JpaProductController.deleteProduct()
     */
    async deleteProduct(productId) {
      if (!confirm('정말로 이 상품을 삭제하시겠습니까?')) {
        return
      }
      
      this.loading = true
      this.error = null
      
      try {
        await axios.delete(`/api/jpa/products/${productId}`)
        this.successMessage = '상품이 삭제되었습니다.'
        this.loadAllProducts()
      } catch (error) {
        this.error = '상품 삭제 중 오류가 발생했습니다: ' + error.message
        console.error('상품 삭제 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 통계 정보 로드
     * FRONTEND_API: GET /api/jpa/products/count/by-status/{status}, /api/jpa/products/total-active-stock -> API_ENTRY: JpaProductController.getProductCountByStatus() 등
     */
    async loadStatistics() {
      try {
        // 상태별 통계
        const activeCountResponse = await axios.get('/api/jpa/products/count/by-status/ACTIVE')
        const inactiveCountResponse = await axios.get('/api/jpa/products/count/by-status/INACTIVE')
        const outOfStockCountResponse = await axios.get('/api/jpa/products/count/by-status/OUT_OF_STOCK')
        
        // 총 재고
        const totalStockResponse = await axios.get('/api/jpa/products/total-active-stock')
        
        // 평균 가격
        const avgPriceResponse = await axios.get('/api/jpa/products/average-price/by-status/ACTIVE')
        
        this.productStatistics = [
          { label: '판매중 상품', value: activeCountResponse.data },
          { label: '판매중지 상품', value: inactiveCountResponse.data },
          { label: '품절 상품', value: outOfStockCountResponse.data },
          { label: '총 활성 재고', value: totalStockResponse.data || 0 },
          { label: '평균 가격', value: this.formatCurrency(avgPriceResponse.data || 0) }
        ]
      } catch (error) {
        console.error('통계 로드 실패:', error)
      }
    },
    
    // 유틸리티 메서드들
    editProduct(product) {
      this.editingProduct = product
      this.productForm = {
        productName: product.productName,
        productCode: product.productCode,
        description: product.description || '',
        price: product.price,
        stockQuantity: product.stockQuantity,
        minStockLevel: product.minStockLevel,
        status: product.status
      }
    },
    
    resetForm() {
      this.editingProduct = null
      this.productForm = {
        productName: '',
        productCode: '',
        description: '',
        price: null,
        stockQuantity: null,
        minStockLevel: 10,
        status: 'ACTIVE'
      }
    },
    
    viewProductDetails(product) {
      this.selectedProduct = product
    },
    
    closeProductModal() {
      this.selectedProduct = null
    },
    
    showPriceUpdateModal(product) {
      this.priceUpdateModal = {
        show: true,
        product: product,
        newPrice: product.price
      }
    },
    
    closePriceUpdateModal() {
      this.priceUpdateModal = {
        show: false,
        product: null,
        newPrice: null
      }
    },
    
    getStatusText(status) {
      const statusMap = {
        'ACTIVE': '판매중',
        'INACTIVE': '판매중지',
        'OUT_OF_STOCK': '품절',
        'DISCONTINUED': '단종',
        'PENDING': '승인대기'
      }
      return statusMap[status] || status
    },
    
    getStockClass(product) {
      if (this.isOutOfStock(product)) {
        return 'stock-out'
      } else if (this.isLowStock(product)) {
        return 'stock-low'
      } else {
        return 'stock-ok'
      }
    },
    
    isOutOfStock(product) {
      return !product.stockQuantity || product.stockQuantity <= 0
    },
    
    isLowStock(product) {
      return product.stockQuantity && product.minStockLevel && 
             product.stockQuantity <= product.minStockLevel
    },
    
    formatDate(dateString) {
      if (!dateString) return '-'
      return new Date(dateString).toLocaleString('ko-KR')
    },
    
    formatCurrency(amount) {
      if (!amount) return '0원'
      return new Intl.NumberFormat('ko-KR', {
        style: 'currency',
        currency: 'KRW'
      }).format(amount)
    }
  }
}
</script>

<style scoped>
.jpa-product-management {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.error-message {
  color: #d32f2f;
  background-color: #ffebee;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.success-message {
  color: #2e7d32;
  background-color: #e8f5e8;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.product-form-section, .search-section, .stock-management-section, .statistics-section, .products-list-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.product-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: bold;
  margin-bottom: 5px;
}

.form-group input, .form-group select, .form-group textarea {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.form-actions {
  grid-column: 1 / -1;
  display: flex;
  gap: 10px;
  justify-content: flex-start;
}

.search-form, .stock-form {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}

.search-form input, .search-form select, .stock-form input {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  min-width: 150px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 15px;
}

.stat-item {
  padding: 10px;
  background-color: white;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.stat-label {
  font-weight: bold;
}

.stat-value {
  color: #1976d2;
  font-size: 1.2em;
}

.products-table {
  overflow-x: auto;
}

.products-table table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
}

.products-table th, .products-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.products-table th {
  background-color: #f5f5f5;
  font-weight: bold;
}

.actions {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.actions button {
  padding: 4px 8px;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
}

.btn-edit { background-color: #2196F3; color: white; }
.btn-view { background-color: #FF9800; color: white; }
.btn-activate { background-color: #4CAF50; color: white; }
.btn-deactivate { background-color: #FFC107; color: black; }
.btn-price { background-color: #9C27B0; color: white; }
.btn-delete { background-color: #F44336; color: white; }

.status-active { color: #4CAF50; font-weight: bold; }
.status-inactive { color: #FF9800; font-weight: bold; }
.status-out_of_stock { color: #F44336; font-weight: bold; }
.status-discontinued { color: #9E9E9E; font-weight: bold; }
.status-pending { color: #2196F3; font-weight: bold; }

.stock-ok { color: #4CAF50; font-weight: bold; }
.stock-low { color: #FF9800; font-weight: bold; }
.stock-out { color: #F44336; font-weight: bold; }

.stock-warning { color: #FF9800; }
.stock-ok { color: #4CAF50; }

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 30px;
  border-radius: 8px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  width: 90%;
}

.product-details p {
  margin: 10px 0;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.loading, .no-data {
  text-align: center;
  padding: 20px;
  color: #666;
}

button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  background-color: #1976d2;
  color: white;
}

button:hover:not(:disabled) {
  opacity: 0.8;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

