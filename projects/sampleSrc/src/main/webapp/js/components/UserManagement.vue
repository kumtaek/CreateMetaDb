<template>
  <div class="user-management">
    <div class="header">
      <h2>사용자 관리 시스템</h2>
      <div class="actions">
        <button @click="refreshUserList" :disabled="loading">새로고침</button>
        <button @click="showCreateModal = true">사용자 추가</button>
      </div>
    </div>
    
    <!-- 검색 필터 -->
    <div class="search-filters">
      <input 
        v-model="searchKeyword" 
        @input="onSearchChange"
        placeholder="이름, 이메일로 검색"
        class="search-input"
      />
      
      <select v-model="statusFilter" @change="onFilterChange">
        <option value="">모든 상태</option>
        <option value="ACTIVE">활성</option>
        <option value="INACTIVE">비활성</option>
        <option value="PENDING">대기</option>
      </select>
      
      <select v-model="typeFilter" @change="onFilterChange">
        <option value="">모든 타입</option>
        <option value="ADMIN">관리자</option>
        <option value="USER">일반사용자</option>
        <option value="MANAGER">매니저</option>
      </select>
    </div>
    
    <!-- 사용자 목록 -->
    <div class="user-list" v-if="!loading">
      <div 
        v-for="user in users" 
        :key="user.id"
        class="user-card"
        @click="selectUser(user)"
        :class="{ active: selectedUser && selectedUser.id === user.id }"
      >
        <div class="user-info">
          <h4>{{ user.fullName }} ({{ user.username }})</h4>
          <p>{{ user.email }}</p>
          <span :class="'status-' + user.status.toLowerCase()">{{ user.status }}</span>
          <span :class="'type-' + user.userType.toLowerCase()">{{ user.userType }}</span>
        </div>
        <div class="user-stats">
          <div>주문: {{ user.orderCount }}건</div>
          <div>총 구매: {{ formatCurrency(user.totalSpent) }}</div>
        </div>
      </div>
    </div>
    
    <!-- 로딩 상태 -->
    <div v-if="loading" class="loading">
      <p>데이터를 불러오는 중...</p>
    </div>
    
    <!-- 에러 상태 -->
    <div v-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="clearError">확인</button>
    </div>
    
    <!-- 사용자 상세 정보 모달 -->
    <div v-if="selectedUser" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h3>{{ selectedUser.fullName }} 상세 정보</h3>
        <div class="user-details">
          <div class="detail-section">
            <h4>기본 정보</h4>
            <p><strong>사용자명:</strong> {{ selectedUser.username }}</p>
            <p><strong>이메일:</strong> {{ selectedUser.email }}</p>
            <p><strong>타입:</strong> {{ selectedUser.userType }}</p>
            <p><strong>상태:</strong> {{ selectedUser.status }}</p>
          </div>
          
          <div class="detail-section" v-if="selectedUser.profile">
            <h4>프로필 정보</h4>
            <p><strong>전화번호:</strong> {{ selectedUser.profile.phone }}</p>
            <p><strong>주소:</strong> {{ selectedUser.profile.address }}</p>
            <p><strong>생년월일:</strong> {{ formatDate(selectedUser.profile.birthDate) }}</p>
          </div>
          
          <div class="detail-section" v-if="selectedUser.department">
            <h4>부서 정보</h4>
            <p><strong>부서명:</strong> {{ selectedUser.department.deptName }}</p>
            <p><strong>매니저:</strong> {{ selectedUser.department.managerName }}</p>
          </div>
          
          <div class="detail-section">
            <h4>활동 통계</h4>
            <p><strong>총 주문 수:</strong> {{ selectedUser.orderCount }}건</p>
            <p><strong>총 구매 금액:</strong> {{ formatCurrency(selectedUser.totalSpent) }}</p>
            <p><strong>마지막 주문:</strong> {{ formatDate(selectedUser.lastOrderDate) }}</p>
            <p><strong>가입일:</strong> {{ formatDate(selectedUser.createdDate) }}</p>
          </div>
        </div>
        
        <div class="modal-actions">
          <button @click="editUser(selectedUser)">수정</button>
          <button @click="viewUserOrders(selectedUser)">주문 내역</button>
          <button @click="closeModal">닫기</button>
        </div>
      </div>
    </div>
    
    <!-- 사용자 생성/수정 모달 -->
    <div v-if="showCreateModal" class="modal-overlay" @click="closeCreateModal">
      <div class="modal-content" @click.stop>
        <h3>{{ editingUser ? '사용자 수정' : '새 사용자 생성' }}</h3>
        <form @submit.prevent="saveUser">
          <div class="form-group">
            <label>사용자명:</label>
            <input v-model="userForm.username" required :disabled="editingUser" />
          </div>
          
          <div class="form-group">
            <label>이메일:</label>
            <input type="email" v-model="userForm.email" required />
          </div>
          
          <div class="form-group">
            <label>전체 이름:</label>
            <input v-model="userForm.fullName" required />
          </div>
          
          <div class="form-group">
            <label>사용자 타입:</label>
            <select v-model="userForm.userType" required>
              <option value="USER">일반사용자</option>
              <option value="MANAGER">매니저</option>
              <option value="ADMIN">관리자</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>부서:</label>
            <select v-model="userForm.departmentId">
              <option value="">부서 선택</option>
              <option v-for="dept in departments" :key="dept.id" :value="dept.id">
                {{ dept.deptName }}
              </option>
            </select>
          </div>
          
          <div class="form-actions">
            <button type="submit" :disabled="saving">{{ editingUser ? '수정' : '생성' }}</button>
            <button type="button" @click="closeCreateModal">취소</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'UserManagement',
  
  data() {
    return {
      users: [],
      departments: [],
      selectedUser: null,
      showCreateModal: false,
      editingUser: null,
      loading: false,
      saving: false,
      error: null,
      
      // 검색 및 필터
      searchKeyword: '',
      statusFilter: '',
      typeFilter: '',
      
      // 페이징
      currentPage: 0,
      pageSize: 20,
      totalElements: 0,
      
      // 사용자 폼
      userForm: {
        username: '',
        email: '',
        fullName: '',
        userType: 'USER',
        departmentId: null
      }
    };
  },
  
  computed: {
    filteredUsers() {
      let filtered = this.users;
      
      if (this.searchKeyword) {
        const keyword = this.searchKeyword.toLowerCase();
        filtered = filtered.filter(user => 
          user.username.toLowerCase().includes(keyword) ||
          user.email.toLowerCase().includes(keyword) ||
          user.fullName.toLowerCase().includes(keyword)
        );
      }
      
      if (this.statusFilter) {
        filtered = filtered.filter(user => user.status === this.statusFilter);
      }
      
      if (this.typeFilter) {
        filtered = filtered.filter(user => user.userType === this.typeFilter);
      }
      
      return filtered;
    }
  },
  
  mounted() {
    this.loadInitialData();
  },
  
  methods: {
    /**
     * 초기 데이터 로드
     * API 호출: GET /api/v2/users, GET /api/v2/departments
     */
    async loadInitialData() {
      this.loading = true;
      this.error = null;
      
      try {
        // 병렬로 사용자 목록과 부서 목록 조회
        const [usersResponse, departmentsResponse] = await Promise.all([
          this.fetchUsers(),
          this.fetchDepartments()
        ]);
        
        this.users = usersResponse.data.content || [];
        this.totalElements = usersResponse.data.totalElements || 0;
        this.departments = departmentsResponse.data || [];
        
      } catch (error) {
        this.error = '데이터 로드 중 오류가 발생했습니다: ' + error.message;
        console.error('Initial data load error:', error);
      } finally {
        this.loading = false;
      }
    },
    
    /**
     * 사용자 목록 조회
     * API 호출: GET /api/v2/users
     */
    async fetchUsers() {
      const params = {
        page: this.currentPage,
        size: this.pageSize
      };
      
      if (this.searchKeyword) {
        params.search = this.searchKeyword;
      }
      
      if (this.statusFilter) {
        params.status = this.statusFilter;
      }
      
      if (this.typeFilter) {
        params.userType = this.typeFilter;
      }
      
      return await axios.get('/api/v2/users', { params });
    },
    
    /**
     * 부서 목록 조회
     * API 호출: GET /api/v2/departments
     */
    async fetchDepartments() {
      return await axios.get('/api/v2/departments');
    },
    
    /**
     * 사용자 목록 새로고침
     */
    async refreshUserList() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await this.fetchUsers();
        this.users = response.data.content || [];
        this.totalElements = response.data.totalElements || 0;
      } catch (error) {
        this.error = '사용자 목록 새로고침 중 오류가 발생했습니다: ' + error.message;
      } finally {
        this.loading = false;
      }
    },
    
    /**
     * 사용자 생성
     * API 호출: POST /api/v2/users
     */
    async createUser(userData) {
      try {
        const response = await axios.post('/api/v2/users', userData);
        
        if (response.data.success) {
          this.users.unshift(response.data.data);
          this.showCreateModal = false;
          this.resetUserForm();
          this.$emit('user-created', response.data.data);
        } else {
          throw new Error(response.data.message);
        }
        
      } catch (error) {
        this.error = '사용자 생성 중 오류가 발생했습니다: ' + error.message;
        throw error;
      }
    },
    
    /**
     * 사용자 수정
     * API 호출: PATCH /api/v2/users/{userId}
     */
    async updateUser(userId, userData) {
      try {
        const response = await axios.patch(`/api/v2/users/${userId}`, userData);
        
        if (response.data.success) {
          const userIndex = this.users.findIndex(u => u.id === userId);
          if (userIndex !== -1) {
            this.users.splice(userIndex, 1, response.data.data);
          }
          this.showCreateModal = false;
          this.editingUser = null;
          this.resetUserForm();
          this.$emit('user-updated', response.data.data);
        } else {
          throw new Error(response.data.message);
        }
        
      } catch (error) {
        this.error = '사용자 수정 중 오류가 발생했습니다: ' + error.message;
        throw error;
      }
    },
    
    /**
     * 사용자 상세 조회
     * API 호출: GET /api/v2/users/{userId}/details
     */
    async fetchUserDetails(userId) {
      try {
        const response = await axios.get(`/api/v2/users/${userId}/details`);
        return response.data.data;
      } catch (error) {
        this.error = '사용자 상세 정보 조회 중 오류가 발생했습니다: ' + error.message;
        throw error;
      }
    },
    
    /**
     * 사용자 주문 내역 조회
     * API 호출: GET /api/v2/users/{userId}/orders
     */
    async fetchUserOrders(userId) {
      try {
        const response = await axios.get(`/api/v2/users/${userId}/orders`);
        return response.data.data;
      } catch (error) {
        this.error = '사용자 주문 내역 조회 중 오류가 발생했습니다: ' + error.message;
        throw error;
      }
    },
    
    // 이벤트 핸들러들
    
    async selectUser(user) {
      this.selectedUser = user;
      
      // 상세 정보 로드
      try {
        const detailedUser = await this.fetchUserDetails(user.id);
        this.selectedUser = { ...user, ...detailedUser };
      } catch (error) {
        console.error('Failed to load user details:', error);
      }
    },
    
    closeModal() {
      this.selectedUser = null;
    },
    
    editUser(user) {
      this.editingUser = user;
      this.userForm = {
        username: user.username,
        email: user.email,
        fullName: user.fullName,
        userType: user.userType,
        departmentId: user.departmentId
      };
      this.showCreateModal = true;
      this.closeModal();
    },
    
    async viewUserOrders(user) {
      try {
        const orders = await this.fetchUserOrders(user.id);
        this.$emit('show-user-orders', { user, orders });
        this.closeModal();
      } catch (error) {
        console.error('Failed to load user orders:', error);
      }
    },
    
    async saveUser() {
      this.saving = true;
      this.error = null;
      
      try {
        if (this.editingUser) {
          await this.updateUser(this.editingUser.id, this.userForm);
        } else {
          await this.createUser(this.userForm);
        }
      } catch (error) {
        console.error('Save user error:', error);
      } finally {
        this.saving = false;
      }
    },
    
    closeCreateModal() {
      this.showCreateModal = false;
      this.editingUser = null;
      this.resetUserForm();
    },
    
    resetUserForm() {
      this.userForm = {
        username: '',
        email: '',
        fullName: '',
        userType: 'USER',
        departmentId: null
      };
    },
    
    onSearchChange() {
      // 디바운싱을 위한 검색 지연
      clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(() => {
        this.refreshUserList();
      }, 500);
    },
    
    onFilterChange() {
      this.currentPage = 0;
      this.refreshUserList();
    },
    
    clearError() {
      this.error = null;
    },
    
    // 유틸리티 메서드들
    
    formatCurrency(amount) {
      if (!amount) return '₩0';
      return '₩' + amount.toLocaleString();
    },
    
    formatDate(dateString) {
      if (!dateString) return '-';
      const date = new Date(dateString);
      return date.toLocaleDateString('ko-KR');
    }
  },
  
  // 컴포넌트 이벤트 정의
  emits: ['user-created', 'user-updated', 'show-user-orders'],
  
  // 컴포넌트 정리
  beforeUnmount() {
    if (this.searchTimeout) {
      clearTimeout(this.searchTimeout);
    }
  }
};
</script>

<style scoped>
.user-management {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e0e0e0;
}

.actions {
  display: flex;
  gap: 10px;
}

.search-filters {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.user-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 15px;
}

.user-card {
  padding: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.user-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.user-card.active {
  border-color: #2196F3;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
}

.user-info h4 {
  margin: 0 0 5px 0;
  color: #333;
}

.user-info p {
  margin: 0 0 10px 0;
  color: #666;
  font-size: 14px;
}

.status-active { background: #4caf50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }
.status-inactive { background: #f44336; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }
.status-pending { background: #ff9800; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }

.type-admin { background: #9c27b0; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px; }
.type-manager { background: #2196f3; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px; }
.type-user { background: #607d8b; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px; }

.user-stats {
  margin-top: 10px;
  font-size: 12px;
  color: #888;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 8px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  width: 90%;
}

.user-details {
  margin: 20px 0;
}

.detail-section {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.detail-section h4 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 16px;
}

.detail-section p {
  margin: 5px 0;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #333;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

button:not(:disabled):hover {
  opacity: 0.9;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

button[type="submit"] {
  background: #2196f3;
  color: white;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error {
  background: #ffebee;
  color: #c62828;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
  border-left: 4px solid #f44336;
}
</style>



