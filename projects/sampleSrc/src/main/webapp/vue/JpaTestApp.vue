<template>
  <div id="jpa-test-app">
    <header class="app-header">
      <h1>JPA & Vue.js 테스트 애플리케이션</h1>
      <p>프론트엔드에서 테이블까지 완전 연결 구조 테스트케이스</p>
      <nav class="main-nav">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="['nav-button', { active: activeTab === tab.id }]"
        >
          {{ tab.label }}
        </button>
      </nav>
    </header>

    <main class="app-main">
      <!-- 연결 구조 다이어그램 -->
      <div v-if="activeTab === 'overview'" class="overview-section">
        <h2>시스템 아키텍처 개요</h2>
        <div class="architecture-diagram">
          <div class="layer frontend-layer">
            <h3>Frontend Layer</h3>
            <div class="components">
              <div class="component vue-component">
                <strong>Vue.js Components</strong>
                <ul>
                  <li>JpaUserManagement.vue</li>
                  <li>JpaProductManagement.vue</li>
                  <li>JpaOrderManagement.vue</li>
                </ul>
              </div>
              <div class="component api-service">
                <strong>API Services</strong>
                <ul>
                  <li>UserApiService.js</li>
                  <li>ProductApiService.js</li>
                  <li>OrderApiService.js</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="arrow">↓ HTTP REST API</div>

          <div class="layer controller-layer">
            <h3>Controller Layer</h3>
            <div class="components">
              <div class="component">
                <strong>REST Controllers</strong>
                <ul>
                  <li>JpaUserController</li>
                  <li>JpaProductController</li>
                  <li>JpaOrderController</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="arrow">↓ Service Method Calls</div>

          <div class="layer service-layer">
            <h3>Service Layer</h3>
            <div class="components">
              <div class="component">
                <strong>Business Services</strong>
                <ul>
                  <li>JpaUserService</li>
                  <li>JpaProductService</li>
                  <li>JpaOrderService</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="arrow">↓ Repository Method Calls</div>

          <div class="layer repository-layer">
            <h3>Repository Layer</h3>
            <div class="components">
              <div class="component">
                <strong>JPA Repositories</strong>
                <ul>
                  <li>UserRepository</li>
                  <li>ProductRepository</li>
                  <li>OrderRepository</li>
                  <li>CategoryRepository</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="arrow">↓ JPA/Hibernate ORM</div>

          <div class="layer database-layer">
            <h3>Database Layer</h3>
            <div class="components">
              <div class="component">
                <strong>Oracle Database Tables</strong>
                <ul>
                  <li>USERS</li>
                  <li>USER_PROFILES</li>
                  <li>PRODUCTS</li>
                  <li>CATEGORIES</li>
                  <li>ORDERS</li>
                  <li>ORDER_ITEMS</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div class="connection-flow">
          <h3>연결 흐름 예시</h3>
          <div class="flow-example">
            <div class="flow-step">
              <strong>1. Vue Component</strong>
              <code>JpaUserManagement.vue</code>
              <p>사용자가 "사용자 목록 조회" 버튼 클릭</p>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-step">
              <strong>2. API Service</strong>
              <code>UserApiService.getAllUsers()</code>
              <p>axios.get('/api/jpa/users') 호출</p>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-step">
              <strong>3. REST Controller</strong>
              <code>JpaUserController.getAllUsers()</code>
              <p>@GetMapping 어노테이션으로 매핑</p>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-step">
              <strong>4. Service</strong>
              <code>JpaUserService.getAllUsers()</code>
              <p>비즈니스 로직 처리</p>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-step">
              <strong>5. Repository</strong>
              <code>UserRepository.findAll()</code>
              <p>JPA 쿼리 메서드 실행</p>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-step">
              <strong>6. Database</strong>
              <code>SELECT * FROM USERS</code>
              <p>Oracle 테이블에서 데이터 조회</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 사용자 관리 -->
      <div v-if="activeTab === 'users'" class="tab-content">
        <JpaUserManagement />
      </div>

      <!-- 상품 관리 -->
      <div v-if="activeTab === 'products'" class="tab-content">
        <JpaProductManagement />
      </div>

      <!-- API 테스트 -->
      <div v-if="activeTab === 'api-test'" class="api-test-section">
        <h2>API 연결 테스트</h2>
        
        <div class="test-section">
          <h3>연결 상태 확인</h3>
          <div class="connection-tests">
            <div class="test-item">
              <button @click="testUserConnection" :disabled="testing">
                사용자 API 연결 테스트
              </button>
              <span :class="['status', connectionStatus.users]">
                {{ getStatusText(connectionStatus.users) }}
              </span>
            </div>
            
            <div class="test-item">
              <button @click="testProductConnection" :disabled="testing">
                상품 API 연결 테스트
              </button>
              <span :class="['status', connectionStatus.products]">
                {{ getStatusText(connectionStatus.products) }}
              </span>
            </div>
            
            <div class="test-item">
              <button @click="testOrderConnection" :disabled="testing">
                주문 API 연결 테스트
              </button>
              <span :class="['status', connectionStatus.orders]">
                {{ getStatusText(connectionStatus.orders) }}
              </span>
            </div>
          </div>
        </div>

        <div class="test-results" v-if="testResults.length > 0">
          <h3>테스트 결과</h3>
          <div class="results-list">
            <div 
              v-for="(result, index) in testResults" 
              :key="index"
              :class="['result-item', result.success ? 'success' : 'error']"
            >
              <div class="result-header">
                <strong>{{ result.test }}</strong>
                <span class="result-time">{{ result.timestamp }}</span>
              </div>
              <div class="result-details">
                <p><strong>요청:</strong> {{ result.request }}</p>
                <p><strong>응답:</strong> {{ result.response }}</p>
                <p v-if="result.error"><strong>오류:</strong> {{ result.error }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 기술 정보 -->
      <div v-if="activeTab === 'tech-info'" class="tech-info-section">
        <h2>사용된 기술 스택</h2>
        
        <div class="tech-stack">
          <div class="tech-category">
            <h3>Frontend</h3>
            <ul>
              <li><strong>Vue.js 2.x</strong> - 프론트엔드 프레임워크</li>
              <li><strong>Axios</strong> - HTTP 클라이언트 라이브러리</li>
              <li><strong>Vue Components</strong> - 컴포넌트 기반 UI</li>
              <li><strong>ES6+ JavaScript</strong> - 모던 자바스크립트</li>
              <li><strong>CSS3</strong> - 스타일링</li>
            </ul>
          </div>
          
          <div class="tech-category">
            <h3>Backend</h3>
            <ul>
              <li><strong>Spring Boot</strong> - 백엔드 프레임워크</li>
              <li><strong>Spring Data JPA</strong> - ORM 및 데이터 액세스</li>
              <li><strong>Spring Web MVC</strong> - REST API 개발</li>
              <li><strong>Hibernate</strong> - JPA 구현체</li>
              <li><strong>Java 8+</strong> - 프로그래밍 언어</li>
            </ul>
          </div>
          
          <div class="tech-category">
            <h3>Database</h3>
            <ul>
              <li><strong>Oracle Database</strong> - 관계형 데이터베이스</li>
              <li><strong>HikariCP</strong> - 커넥션 풀</li>
              <li><strong>JPA Entities</strong> - 객체-관계 매핑</li>
              <li><strong>JPA Repositories</strong> - 데이터 액세스 레이어</li>
            </ul>
          </div>
          
          <div class="tech-category">
            <h3>Architecture Patterns</h3>
            <ul>
              <li><strong>MVC Pattern</strong> - Model-View-Controller</li>
              <li><strong>Repository Pattern</strong> - 데이터 액세스 추상화</li>
              <li><strong>Service Layer Pattern</strong> - 비즈니스 로직 분리</li>
              <li><strong>DTO Pattern</strong> - 데이터 전송 객체</li>
              <li><strong>RESTful API</strong> - REST 아키텍처 스타일</li>
            </ul>
          </div>
        </div>

        <div class="features">
          <h3>구현된 주요 기능</h3>
          <div class="feature-list">
            <div class="feature-item">
              <h4>JPA 기능</h4>
              <ul>
                <li>다양한 쿼리 메서드 패턴</li>
                <li>@Query 어노테이션 활용</li>
                <li>Native SQL 쿼리</li>
                <li>동적 쿼리 지원</li>
                <li>페이징 및 정렬</li>
                <li>엔티티 연관관계 매핑</li>
                <li>트랜잭션 관리</li>
              </ul>
            </div>
            
            <div class="feature-item">
              <h4>Vue.js 기능</h4>
              <ul>
                <li>컴포넌트 기반 구조</li>
                <li>반응형 데이터 바인딩</li>
                <li>이벤트 핸들링</li>
                <li>조건부 렌더링</li>
                <li>리스트 렌더링</li>
                <li>폼 처리</li>
                <li>API 서비스 모듈화</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
/**
 * JPA & Vue.js 테스트 메인 애플리케이션
 * 프론트엔드에서 테이블까지 완전 연결 구조 테스트케이스
 */
import JpaUserManagement from './components/JpaUserManagement.vue'
import JpaProductManagement from './components/JpaProductManagement.vue'
import { UserApiService, ProductApiService, OrderApiService } from './services/JpaApiService.js'

export default {
  name: 'JpaTestApp',
  components: {
    JpaUserManagement,
    JpaProductManagement
  },
  data() {
    return {
      activeTab: 'overview',
      testing: false,
      tabs: [
        { id: 'overview', label: '시스템 개요' },
        { id: 'users', label: '사용자 관리' },
        { id: 'products', label: '상품 관리' },
        { id: 'api-test', label: 'API 연결 테스트' },
        { id: 'tech-info', label: '기술 정보' }
      ],
      connectionStatus: {
        users: 'unknown',
        products: 'unknown',
        orders: 'unknown'
      },
      testResults: []
    }
  },
  
  mounted() {
    console.log('JPA & Vue.js 테스트 애플리케이션이 시작되었습니다.')
    console.log('연결 구조: Vue Component → API Service → REST Controller → Service → Repository → Database Table')
  },
  
  methods: {
    async testUserConnection() {
      this.testing = true
      const testName = '사용자 API 연결 테스트'
      
      try {
        const startTime = Date.now()
        const response = await UserApiService.getAllUsers()
        const endTime = Date.now()
        
        this.connectionStatus.users = 'success'
        this.addTestResult({
          test: testName,
          success: true,
          request: 'GET /api/jpa/users',
          response: `${response.data.length}개 사용자 조회 성공 (${endTime - startTime}ms)`,
          timestamp: new Date().toLocaleTimeString()
        })
      } catch (error) {
        this.connectionStatus.users = 'error'
        this.addTestResult({
          test: testName,
          success: false,
          request: 'GET /api/jpa/users',
          response: '연결 실패',
          error: error.message,
          timestamp: new Date().toLocaleTimeString()
        })
      } finally {
        this.testing = false
      }
    },
    
    async testProductConnection() {
      this.testing = true
      const testName = '상품 API 연결 테스트'
      
      try {
        const startTime = Date.now()
        const response = await ProductApiService.getAllProducts()
        const endTime = Date.now()
        
        this.connectionStatus.products = 'success'
        this.addTestResult({
          test: testName,
          success: true,
          request: 'GET /api/jpa/products',
          response: `${response.data.length}개 상품 조회 성공 (${endTime - startTime}ms)`,
          timestamp: new Date().toLocaleTimeString()
        })
      } catch (error) {
        this.connectionStatus.products = 'error'
        this.addTestResult({
          test: testName,
          success: false,
          request: 'GET /api/jpa/products',
          response: '연결 실패',
          error: error.message,
          timestamp: new Date().toLocaleTimeString()
        })
      } finally {
        this.testing = false
      }
    },
    
    async testOrderConnection() {
      this.testing = true
      const testName = '주문 API 연결 테스트'
      
      try {
        const startTime = Date.now()
        const response = await OrderApiService.getAllOrders()
        const endTime = Date.now()
        
        this.connectionStatus.orders = 'success'
        this.addTestResult({
          test: testName,
          success: true,
          request: 'GET /api/jpa/orders',
          response: `${response.data.length}개 주문 조회 성공 (${endTime - startTime}ms)`,
          timestamp: new Date().toLocaleTimeString()
        })
      } catch (error) {
        this.connectionStatus.orders = 'error'
        this.addTestResult({
          test: testName,
          success: false,
          request: 'GET /api/jpa/orders',
          response: '연결 실패',
          error: error.message,
          timestamp: new Date().toLocaleTimeString()
        })
      } finally {
        this.testing = false
      }
    },
    
    addTestResult(result) {
      this.testResults.unshift(result)
      // 최대 10개 결과만 유지
      if (this.testResults.length > 10) {
        this.testResults = this.testResults.slice(0, 10)
      }
    },
    
    getStatusText(status) {
      switch (status) {
        case 'success': return '연결 성공'
        case 'error': return '연결 실패'
        default: return '테스트 안함'
      }
    }
  }
}
</script>

<style scoped>
#jpa-test-app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  background-color: #f5f5f5;
}

.app-header {
  text-align: center;
  margin-bottom: 30px;
  padding: 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.app-header h1 {
  margin: 0 0 10px 0;
  font-size: 2.5em;
  font-weight: 300;
}

.app-header p {
  margin: 0 0 30px 0;
  font-size: 1.2em;
  opacity: 0.9;
}

.main-nav {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.nav-button {
  padding: 12px 24px;
  border: 2px solid rgba(255,255,255,0.3);
  background: rgba(255,255,255,0.1);
  color: white;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 16px;
  font-weight: 500;
}

.nav-button:hover {
  background: rgba(255,255,255,0.2);
  transform: translateY(-2px);
}

.nav-button.active {
  background: white;
  color: #667eea;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.app-main {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.overview-section {
  max-width: 1200px;
  margin: 0 auto;
}

.architecture-diagram {
  margin: 30px 0;
}

.layer {
  margin: 20px 0;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.frontend-layer { background: #e3f2fd; border-left: 5px solid #2196f3; }
.controller-layer { background: #f3e5f5; border-left: 5px solid #9c27b0; }
.service-layer { background: #e8f5e8; border-left: 5px solid #4caf50; }
.repository-layer { background: #fff3e0; border-left: 5px solid #ff9800; }
.database-layer { background: #fce4ec; border-left: 5px solid #e91e63; }

.layer h3 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 1.3em;
}

.components {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.component {
  flex: 1;
  min-width: 200px;
  padding: 15px;
  background: rgba(255,255,255,0.7);
  border-radius: 6px;
  border: 1px solid rgba(0,0,0,0.1);
}

.component strong {
  display: block;
  margin-bottom: 10px;
  color: #333;
}

.component ul {
  margin: 0;
  padding-left: 20px;
  list-style-type: disc;
}

.component li {
  margin: 5px 0;
  font-size: 14px;
  color: #666;
}

.arrow {
  text-align: center;
  font-size: 18px;
  font-weight: bold;
  color: #666;
  margin: 15px 0;
}

.connection-flow {
  margin: 40px 0;
  padding: 30px;
  background: #f8f9fa;
  border-radius: 8px;
}

.flow-example {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.flow-step {
  flex: 1;
  min-width: 150px;
  text-align: center;
  padding: 15px;
  background: white;
  border-radius: 8px;
  border: 2px solid #e0e0e0;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.flow-step strong {
  display: block;
  color: #333;
  margin-bottom: 5px;
}

.flow-step code {
  display: block;
  background: #f5f5f5;
  padding: 5px;
  border-radius: 4px;
  font-size: 12px;
  margin: 5px 0;
  color: #d63384;
}

.flow-step p {
  font-size: 11px;
  color: #666;
  margin: 5px 0 0 0;
}

.flow-arrow {
  font-size: 20px;
  font-weight: bold;
  color: #666;
  margin: 0 5px;
}

.api-test-section, .tech-info-section {
  max-width: 1000px;
  margin: 0 auto;
}

.test-section {
  margin: 30px 0;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.connection-tests {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.test-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.test-item button {
  padding: 10px 20px;
  border: none;
  background: #2196f3;
  color: white;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
}

.test-item button:hover:not(:disabled) {
  background: #1976d2;
}

.test-item button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.status {
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
}

.status.success {
  background: #c8e6c9;
  color: #2e7d32;
}

.status.error {
  background: #ffcdd2;
  color: #c62828;
}

.status.unknown {
  background: #e0e0e0;
  color: #666;
}

.test-results {
  margin: 30px 0;
}

.results-list {
  max-height: 400px;
  overflow-y: auto;
}

.result-item {
  margin: 10px 0;
  padding: 15px;
  border-radius: 6px;
  border-left: 4px solid #ccc;
}

.result-item.success {
  background: #f1f8e9;
  border-left-color: #4caf50;
}

.result-item.error {
  background: #fdf2f2;
  border-left-color: #f44336;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.result-time {
  font-size: 12px;
  color: #666;
}

.result-details p {
  margin: 5px 0;
  font-size: 14px;
}

.tech-stack {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin: 30px 0;
}

.tech-category {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #2196f3;
}

.tech-category h3 {
  margin: 0 0 15px 0;
  color: #333;
}

.tech-category ul {
  margin: 0;
  padding-left: 20px;
}

.tech-category li {
  margin: 8px 0;
  line-height: 1.5;
}

.tech-category strong {
  color: #2196f3;
}

.features {
  margin: 40px 0;
}

.feature-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.feature-item {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #4caf50;
}

.feature-item h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.feature-item ul {
  margin: 0;
  padding-left: 20px;
}

.feature-item li {
  margin: 5px 0;
  font-size: 14px;
}

.tab-content {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .flow-example {
    flex-direction: column;
  }
  
  .flow-arrow {
    transform: rotate(90deg);
  }
  
  .components {
    flex-direction: column;
  }
  
  .tech-stack {
    grid-template-columns: 1fr;
  }
  
  .feature-list {
    grid-template-columns: 1fr;
  }
}
</style>

