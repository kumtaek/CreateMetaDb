<template>
  <div class="jpa-user-management">
    <h2>JPA 사용자 관리 시스템</h2>
    
    <!-- 에러 메시지 -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
    
    <!-- 성공 메시지 -->
    <div v-if="successMessage" class="success-message">
      {{ successMessage }}
    </div>
    
    <!-- 사용자 생성/수정 폼 -->
    <div class="user-form-section">
      <h3>{{ editingUser ? '사용자 수정' : '사용자 생성' }}</h3>
      <form @submit.prevent="saveUser" class="user-form">
        <div class="form-group">
          <label>사용자명:</label>
          <input 
            v-model="userForm.username" 
            type="text" 
            required 
            :disabled="editingUser"
            placeholder="사용자명 입력"
          />
        </div>
        
        <div class="form-group">
          <label>이메일:</label>
          <input 
            v-model="userForm.email" 
            type="email" 
            required 
            placeholder="이메일 입력"
          />
        </div>
        
        <div class="form-group">
          <label>비밀번호:</label>
          <input 
            v-model="userForm.password" 
            type="password" 
            required 
            placeholder="비밀번호 입력"
          />
        </div>
        
        <div class="form-group">
          <label>전체 이름:</label>
          <input 
            v-model="userForm.fullName" 
            type="text" 
            placeholder="전체 이름 입력"
          />
        </div>
        
        <div class="form-group">
          <label>전화번호:</label>
          <input 
            v-model="userForm.phoneNumber" 
            type="text" 
            placeholder="전화번호 입력"
          />
        </div>
        
        <div class="form-group">
          <label>상태:</label>
          <select v-model="userForm.status" required>
            <option value="ACTIVE">활성</option>
            <option value="INACTIVE">비활성</option>
            <option value="SUSPENDED">일시정지</option>
            <option value="PENDING">승인대기</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>사용자 타입:</label>
          <select v-model="userForm.userType" required>
            <option value="REGULAR">일반회원</option>
            <option value="PREMIUM">프리미엄회원</option>
            <option value="VIP">VIP회원</option>
            <option value="ADMIN">관리자</option>
          </select>
        </div>
        
        <div class="form-actions">
          <button type="submit" :disabled="loading">
            {{ loading ? '처리중...' : (editingUser ? '수정' : '생성') }}
          </button>
          <button type="button" @click="resetForm" :disabled="loading">
            초기화
          </button>
        </div>
      </form>
    </div>
    
    <!-- 검색 섹션 -->
    <div class="search-section">
      <h3>사용자 검색</h3>
      
      <!-- 기본 검색 -->
      <div class="basic-search">
        <h4>기본 검색</h4>
        <div class="search-form">
          <input 
            v-model="basicSearch.username" 
            type="text" 
            placeholder="사용자명 검색"
          />
          <input 
            v-model="basicSearch.email" 
            type="text" 
            placeholder="이메일 검색"
          />
          <input 
            v-model="basicSearch.fullName" 
            type="text" 
            placeholder="전체 이름 검색"
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
            <option value="ACTIVE">활성</option>
            <option value="INACTIVE">비활성</option>
            <option value="SUSPENDED">일시정지</option>
            <option value="PENDING">승인대기</option>
          </select>
          
          <select v-model="advancedSearch.userType">
            <option value="">전체 타입</option>
            <option value="REGULAR">일반회원</option>
            <option value="PREMIUM">프리미엄회원</option>
            <option value="VIP">VIP회원</option>
            <option value="ADMIN">관리자</option>
          </select>
          
          <input 
            v-model="advancedSearch.emailDomain" 
            type="text" 
            placeholder="이메일 도메인 (예: gmail.com)"
          />
          
          <button @click="performAdvancedSearch" :disabled="loading">
            고급 검색
          </button>
          
          <button @click="loadAllUsers" :disabled="loading">
            전체 조회
          </button>
        </div>
      </div>
      
      <!-- 날짜 기반 검색 -->
      <div class="date-search">
        <h4>가입일 기반 검색</h4>
        <div class="search-form">
          <input 
            v-model="dateSearch.fromDate" 
            type="datetime-local" 
            placeholder="시작일"
          />
          <input 
            v-model="dateSearch.toDate" 
            type="datetime-local" 
            placeholder="종료일"
          />
          <button @click="searchByDateRange" :disabled="loading">
            기간별 검색
          </button>
          <button @click="searchUsersWithoutLogin" :disabled="loading">
            로그인 이력 없음
          </button>
        </div>
      </div>
    </div>
    
    <!-- 통계 섹션 -->
    <div class="statistics-section">
      <h3>사용자 통계</h3>
      <div class="stats-grid">
        <div class="stat-item" v-for="stat in userStatistics" :key="stat.label">
          <span class="stat-label">{{ stat.label }}:</span>
          <span class="stat-value">{{ stat.value }}</span>
        </div>
      </div>
      <button @click="loadStatistics" :disabled="loading">
        통계 새로고침
      </button>
    </div>
    
    <!-- 사용자 목록 -->
    <div class="users-list-section">
      <h3>사용자 목록 ({{ users.length }}명)</h3>
      
      <div v-if="loading" class="loading">
        데이터를 불러오는 중...
      </div>
      
      <div v-else-if="users.length === 0" class="no-data">
        검색 결과가 없습니다.
      </div>
      
      <div v-else class="users-table">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>사용자명</th>
              <th>이메일</th>
              <th>전체 이름</th>
              <th>상태</th>
              <th>타입</th>
              <th>가입일</th>
              <th>마지막 로그인</th>
              <th>작업</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.userId">
              <td>{{ user.userId }}</td>
              <td>{{ user.username }}</td>
              <td>{{ user.email }}</td>
              <td>{{ user.fullName || '-' }}</td>
              <td>
                <span :class="'status-' + user.status.toLowerCase()">
                  {{ getStatusText(user.status) }}
                </span>
              </td>
              <td>{{ getUserTypeText(user.userType) }}</td>
              <td>{{ formatDate(user.createdAt) }}</td>
              <td>{{ user.lastLoginAt ? formatDate(user.lastLoginAt) : '없음' }}</td>
              <td class="actions">
                <button @click="editUser(user)" class="btn-edit">수정</button>
                <button @click="viewUserWithOrders(user.userId)" class="btn-view">주문보기</button>
                <button 
                  v-if="user.status === 'ACTIVE'" 
                  @click="deactivateUser(user.userId)" 
                  class="btn-deactivate"
                >
                  비활성화
                </button>
                <button 
                  v-else 
                  @click="activateUser(user.userId)" 
                  class="btn-activate"
                >
                  활성화
                </button>
                <button 
                  v-if="user.userType !== 'PREMIUM'" 
                  @click="upgradeToPremium(user.userId)" 
                  class="btn-upgrade"
                >
                  프리미엄 업그레이드
                </button>
                <button @click="updateLoginTime(user.userId)" class="btn-login">
                  로그인 시간 갱신
                </button>
                <button @click="deleteUser(user.userId)" class="btn-delete">삭제</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- 사용자 상세 정보 모달 -->
    <div v-if="selectedUserWithOrders" class="modal-overlay" @click="closeUserModal">
      <div class="modal-content" @click.stop>
        <h3>사용자 상세 정보</h3>
        <div class="user-details">
          <p><strong>사용자명:</strong> {{ selectedUserWithOrders.username }}</p>
          <p><strong>이메일:</strong> {{ selectedUserWithOrders.email }}</p>
          <p><strong>전체 이름:</strong> {{ selectedUserWithOrders.fullName || '-' }}</p>
          <p><strong>전화번호:</strong> {{ selectedUserWithOrders.phoneNumber || '-' }}</p>
          <p><strong>상태:</strong> {{ getStatusText(selectedUserWithOrders.status) }}</p>
          <p><strong>타입:</strong> {{ getUserTypeText(selectedUserWithOrders.userType) }}</p>
          <p><strong>가입일:</strong> {{ formatDate(selectedUserWithOrders.createdAt) }}</p>
          <p><strong>마지막 로그인:</strong> {{ selectedUserWithOrders.lastLoginAt ? formatDate(selectedUserWithOrders.lastLoginAt) : '없음' }}</p>
          
          <h4>주문 내역 ({{ selectedUserWithOrders.orders ? selectedUserWithOrders.orders.length : 0 }}건)</h4>
          <div v-if="selectedUserWithOrders.orders && selectedUserWithOrders.orders.length > 0" class="orders-list">
            <div v-for="order in selectedUserWithOrders.orders" :key="order.orderId" class="order-item">
              <p><strong>주문번호:</strong> {{ order.orderNumber }}</p>
              <p><strong>주문일:</strong> {{ formatDate(order.orderDate) }}</p>
              <p><strong>상태:</strong> {{ order.orderStatus }}</p>
              <p><strong>총액:</strong> {{ formatCurrency(order.totalAmount) }}</p>
            </div>
          </div>
          <div v-else class="no-orders">
            주문 내역이 없습니다.
          </div>
        </div>
        <button @click="closeUserModal" class="btn-close">닫기</button>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * JPA User Management Vue Component
 * FRONTEND_API -> API_ENTRY -> JPA Repository -> TABLE 연결 구조 테스트케이스
 * 
 * 연결 구조:
 * Vue Component -> axios API calls -> JpaUserController -> JpaUserService -> UserRepository -> USERS TABLE
 */
import axios from 'axios'

export default {
  name: 'JpaUserManagement',
  data() {
    return {
      loading: false,
      error: null,
      successMessage: null,
      users: [],
      editingUser: null,
      selectedUserWithOrders: null,
      
      // 사용자 폼 데이터
      userForm: {
        username: '',
        email: '',
        password: '',
        fullName: '',
        phoneNumber: '',
        status: 'ACTIVE',
        userType: 'REGULAR'
      },
      
      // 검색 폼들
      basicSearch: {
        username: '',
        email: '',
        fullName: ''
      },
      
      advancedSearch: {
        status: '',
        userType: '',
        emailDomain: ''
      },
      
      dateSearch: {
        fromDate: '',
        toDate: ''
      },
      
      // 통계 데이터
      userStatistics: []
    }
  },
  
  mounted() {
    this.loadAllUsers()
    this.loadStatistics()
  },
  
  methods: {
    // API 호출 메서드들
    
    /**
     * 전체 사용자 조회
     * FRONTEND_API: GET /api/jpa/users -> API_ENTRY: JpaUserController.getAllUsers()
     */
    async loadAllUsers() {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get('/api/jpa/users')
        this.users = response.data
      } catch (error) {
        this.error = '사용자 목록 조회 중 오류가 발생했습니다: ' + error.message
        console.error('사용자 목록 조회 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 사용자 생성/수정
     * FRONTEND_API: POST /api/jpa/users (생성) 또는 PUT /api/jpa/users/{id} (수정) -> API_ENTRY: JpaUserController.createUser() / updateUser()
     */
    async saveUser() {
      this.loading = true
      this.error = null
      this.successMessage = null
      
      try {
        if (this.editingUser) {
          // 수정
          await axios.put(`/api/jpa/users/${this.editingUser.userId}`, this.userForm)
          this.successMessage = '사용자가 성공적으로 수정되었습니다.'
        } else {
          // 생성
          await axios.post('/api/jpa/users', this.userForm)
          this.successMessage = '사용자가 성공적으로 생성되었습니다.'
        }
        
        this.resetForm()
        this.loadAllUsers()
      } catch (error) {
        this.error = '사용자 저장 중 오류가 발생했습니다: ' + error.message
        console.error('사용자 저장 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 기본 검색 수행
     * FRONTEND_API: GET /api/jpa/users/search/username, /api/jpa/users/search/email, /api/jpa/users/search/fullname -> API_ENTRY: JpaUserController.searchUsers*()
     */
    async performBasicSearch() {
      this.loading = true
      this.error = null
      
      try {
        let searchResults = []
        
        if (this.basicSearch.username) {
          const response = await axios.get('/api/jpa/users/search/username', {
            params: { q: this.basicSearch.username }
          })
          searchResults = [...searchResults, ...response.data]
        }
        
        if (this.basicSearch.email) {
          const response = await axios.get('/api/jpa/users/search/email', {
            params: { q: this.basicSearch.email }
          })
          searchResults = [...searchResults, ...response.data]
        }
        
        if (this.basicSearch.fullName) {
          const response = await axios.get('/api/jpa/users/search/fullname', {
            params: { q: this.basicSearch.fullName }
          })
          searchResults = [...searchResults, ...response.data]
        }
        
        // 중복 제거
        const uniqueUsers = searchResults.filter((user, index, self) => 
          index === self.findIndex(u => u.userId === user.userId)
        )
        
        this.users = uniqueUsers
      } catch (error) {
        this.error = '기본 검색 중 오류가 발생했습니다: ' + error.message
        console.error('기본 검색 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 고급 검색 수행
     * FRONTEND_API: GET /api/jpa/users/by-status/{status}, /api/jpa/users/by-type/{userType}, /api/jpa/users/by-email-domain/{domain} -> API_ENTRY: JpaUserController.getUsersByStatus() 등
     */
    async performAdvancedSearch() {
      this.loading = true
      this.error = null
      
      try {
        if (this.advancedSearch.status) {
          const response = await axios.get(`/api/jpa/users/by-status/${this.advancedSearch.status}`)
          this.users = response.data
        } else if (this.advancedSearch.userType) {
          const response = await axios.get(`/api/jpa/users/by-type/${this.advancedSearch.userType}`)
          this.users = response.data
        } else if (this.advancedSearch.emailDomain) {
          const response = await axios.get(`/api/jpa/users/by-email-domain/${this.advancedSearch.emailDomain}`)
          this.users = response.data
        } else {
          this.loadAllUsers()
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
     * 날짜 범위 검색
     * FRONTEND_API: GET /api/jpa/users/created-between -> API_ENTRY: JpaUserController.getUsersCreatedBetween()
     */
    async searchByDateRange() {
      if (!this.dateSearch.fromDate || !this.dateSearch.toDate) {
        this.error = '시작일과 종료일을 모두 입력해주세요.'
        return
      }
      
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get('/api/jpa/users/created-between', {
          params: {
            startDate: this.dateSearch.fromDate,
            endDate: this.dateSearch.toDate
          }
        })
        this.users = response.data
      } catch (error) {
        this.error = '날짜 범위 검색 중 오류가 발생했습니다: ' + error.message
        console.error('날짜 범위 검색 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 로그인 이력 없는 사용자 검색
     * FRONTEND_API: GET /api/jpa/users/never-logged-in -> API_ENTRY: JpaUserController.getUsersWithoutLogin()
     */
    async searchUsersWithoutLogin() {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get('/api/jpa/users/never-logged-in')
        this.users = response.data
      } catch (error) {
        this.error = '로그인 이력 없는 사용자 검색 중 오류가 발생했습니다: ' + error.message
        console.error('로그인 이력 없는 사용자 검색 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 사용자 주문 정보와 함께 조회
     * FRONTEND_API: GET /api/jpa/users/{id}/with-orders -> API_ENTRY: JpaUserController.getUserWithOrders()
     */
    async viewUserWithOrders(userId) {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get(`/api/jpa/users/${userId}/with-orders`)
        this.selectedUserWithOrders = response.data
      } catch (error) {
        this.error = '사용자 상세 정보 조회 중 오류가 발생했습니다: ' + error.message
        console.error('사용자 상세 정보 조회 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 사용자 활성화
     * FRONTEND_API: PUT /api/jpa/users/{id}/activate -> API_ENTRY: JpaUserController.activateUser()
     */
    async activateUser(userId) {
      this.loading = true
      this.error = null
      
      try {
        await axios.put(`/api/jpa/users/${userId}/activate`)
        this.successMessage = '사용자가 활성화되었습니다.'
        this.loadAllUsers()
      } catch (error) {
        this.error = '사용자 활성화 중 오류가 발생했습니다: ' + error.message
        console.error('사용자 활성화 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 사용자 비활성화
     * FRONTEND_API: PUT /api/jpa/users/{id}/deactivate -> API_ENTRY: JpaUserController.deactivateUser()
     */
    async deactivateUser(userId) {
      this.loading = true
      this.error = null
      
      try {
        await axios.put(`/api/jpa/users/${userId}/deactivate`)
        this.successMessage = '사용자가 비활성화되었습니다.'
        this.loadAllUsers()
      } catch (error) {
        this.error = '사용자 비활성화 중 오류가 발생했습니다: ' + error.message
        console.error('사용자 비활성화 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 프리미엄 업그레이드
     * FRONTEND_API: PUT /api/jpa/users/{id}/upgrade-premium -> API_ENTRY: JpaUserController.upgradeUserToPremium()
     */
    async upgradeToPremium(userId) {
      this.loading = true
      this.error = null
      
      try {
        await axios.put(`/api/jpa/users/${userId}/upgrade-premium`)
        this.successMessage = '사용자가 프리미엄으로 업그레이드되었습니다.'
        this.loadAllUsers()
      } catch (error) {
        this.error = '프리미엄 업그레이드 중 오류가 발생했습니다: ' + error.message
        console.error('프리미엄 업그레이드 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 로그인 시간 갱신
     * FRONTEND_API: PUT /api/jpa/users/{id}/login -> API_ENTRY: JpaUserController.updateLastLoginTime()
     */
    async updateLoginTime(userId) {
      this.loading = true
      this.error = null
      
      try {
        await axios.put(`/api/jpa/users/${userId}/login`)
        this.successMessage = '로그인 시간이 갱신되었습니다.'
        this.loadAllUsers()
      } catch (error) {
        this.error = '로그인 시간 갱신 중 오류가 발생했습니다: ' + error.message
        console.error('로그인 시간 갱신 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 사용자 삭제
     * FRONTEND_API: DELETE /api/jpa/users/{id} -> API_ENTRY: JpaUserController.deleteUser()
     */
    async deleteUser(userId) {
      if (!confirm('정말로 이 사용자를 삭제하시겠습니까?')) {
        return
      }
      
      this.loading = true
      this.error = null
      
      try {
        await axios.delete(`/api/jpa/users/${userId}`)
        this.successMessage = '사용자가 삭제되었습니다.'
        this.loadAllUsers()
      } catch (error) {
        this.error = '사용자 삭제 중 오류가 발생했습니다: ' + error.message
        console.error('사용자 삭제 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 통계 정보 로드
     * FRONTEND_API: GET /api/jpa/users/statistics/by-type, /api/jpa/users/count/by-status/{status} -> API_ENTRY: JpaUserController.getUserTypeStatistics() 등
     */
    async loadStatistics() {
      try {
        // 타입별 통계
        const typeStatsResponse = await axios.get('/api/jpa/users/statistics/by-type')
        const typeStats = typeStatsResponse.data.map(stat => ({
          label: `${this.getUserTypeText(stat[0])} 사용자`,
          value: stat[1]
        }))
        
        // 상태별 통계
        const activeCountResponse = await axios.get('/api/jpa/users/count/by-status/ACTIVE')
        const inactiveCountResponse = await axios.get('/api/jpa/users/count/by-status/INACTIVE')
        
        this.userStatistics = [
          ...typeStats,
          { label: '활성 사용자', value: activeCountResponse.data },
          { label: '비활성 사용자', value: inactiveCountResponse.data }
        ]
      } catch (error) {
        console.error('통계 로드 실패:', error)
      }
    },
    
    // 유틸리티 메서드들
    editUser(user) {
      this.editingUser = user
      this.userForm = {
        username: user.username,
        email: user.email,
        password: '', // 보안상 빈 값
        fullName: user.fullName || '',
        phoneNumber: user.phoneNumber || '',
        status: user.status,
        userType: user.userType
      }
    },
    
    resetForm() {
      this.editingUser = null
      this.userForm = {
        username: '',
        email: '',
        password: '',
        fullName: '',
        phoneNumber: '',
        status: 'ACTIVE',
        userType: 'REGULAR'
      }
    },
    
    closeUserModal() {
      this.selectedUserWithOrders = null
    },
    
    getStatusText(status) {
      const statusMap = {
        'ACTIVE': '활성',
        'INACTIVE': '비활성',
        'SUSPENDED': '일시정지',
        'PENDING': '승인대기',
        'DELETED': '삭제됨'
      }
      return statusMap[status] || status
    },
    
    getUserTypeText(userType) {
      const typeMap = {
        'REGULAR': '일반회원',
        'PREMIUM': '프리미엄회원',
        'VIP': 'VIP회원',
        'ADMIN': '관리자',
        'GUEST': '게스트'
      }
      return typeMap[userType] || userType
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
.jpa-user-management {
  padding: 20px;
  max-width: 1400px;
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

.user-form-section, .search-section, .statistics-section, .users-list-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.user-form {
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

.form-group input, .form-group select {
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

.search-form {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}

.search-form input, .search-form select {
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

.users-table {
  overflow-x: auto;
}

.users-table table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
}

.users-table th, .users-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.users-table th {
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
.btn-upgrade { background-color: #9C27B0; color: white; }
.btn-login { background-color: #00BCD4; color: white; }
.btn-delete { background-color: #F44336; color: white; }

.status-active { color: #4CAF50; font-weight: bold; }
.status-inactive { color: #FF9800; font-weight: bold; }
.status-suspended { color: #F44336; font-weight: bold; }
.status-pending { color: #2196F3; font-weight: bold; }

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

.user-details p {
  margin: 10px 0;
}

.orders-list {
  max-height: 300px;
  overflow-y: auto;
}

.order-item {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 10px;
  background-color: #f9f9f9;
}

.loading, .no-data, .no-orders {
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

