import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import axios from 'axios';

/**
 * React Hooks 패턴 컴포넌트 - 연관관계 도출 테스트용
 * 목적: useState, useEffect, useCallback, useMemo 등 React Hooks 패턴 테스트
 * 연관관계 중심: React Component -> API -> Backend Service 연결
 */

// 커스텀 Hook: 사용자 데이터 관리
const useUserData = () => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    /**
     * 사용자 목록 조회
     * API 호출: GET /api/v2/users
     */
    const fetchUsers = useCallback(async (searchParams = {}) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await axios.get('/api/v2/users', {
                params: {
                    page: searchParams.page || 0,
                    size: searchParams.size || 20,
                    search: searchParams.search,
                    status: searchParams.status,
                    userType: searchParams.userType,
                    sortBy: searchParams.sortBy || 'createdDate',
                    sortDir: searchParams.sortDir || 'desc'
                }
            });
            
            if (response.data.success) {
                setUsers(response.data.data.content || []);
            } else {
                throw new Error(response.data.message);
            }
            
        } catch (err) {
            setError('사용자 데이터 조회 중 오류가 발생했습니다: ' + err.message);
            console.error('User fetch error:', err);
        } finally {
            setLoading(false);
        }
    }, []);
    
    /**
     * 사용자 생성
     * API 호출: POST /api/v2/users
     */
    const createUser = useCallback(async (userData) => {
        try {
            const response = await axios.post('/api/v2/users', userData);
            
            if (response.data.success) {
                setUsers(prevUsers => [response.data.data, ...prevUsers]);
                return response.data.data;
            } else {
                throw new Error(response.data.message);
            }
            
        } catch (err) {
            setError('사용자 생성 중 오류가 발생했습니다: ' + err.message);
            throw err;
        }
    }, []);
    
    /**
     * 사용자 업데이트
     * API 호출: PATCH /api/v2/users/{userId}
     */
    const updateUser = useCallback(async (userId, userData) => {
        try {
            const response = await axios.patch(`/api/v2/users/${userId}`, userData);
            
            if (response.data.success) {
                setUsers(prevUsers => 
                    prevUsers.map(user => 
                        user.id === userId ? response.data.data : user
                    )
                );
                return response.data.data;
            } else {
                throw new Error(response.data.message);
            }
            
        } catch (err) {
            setError('사용자 업데이트 중 오류가 발생했습니다: ' + err.message);
            throw err;
        }
    }, []);
    
    /**
     * 사용자 삭제
     * API 호출: DELETE /api/v2/users/{userId}
     */
    const deleteUser = useCallback(async (userId) => {
        try {
            const response = await axios.delete(`/api/v2/users/${userId}`);
            
            if (response.data.success) {
                setUsers(prevUsers => prevUsers.filter(user => user.id !== userId));
                return true;
            } else {
                throw new Error(response.data.message);
            }
            
        } catch (err) {
            setError('사용자 삭제 중 오류가 발생했습니다: ' + err.message);
            throw err;
        }
    }, []);
    
    return {
        users,
        loading,
        error,
        fetchUsers,
        createUser,
        updateUser,
        deleteUser,
        setError
    };
};

// 커스텀 Hook: 주문 데이터 관리
const useOrderData = () => {
    const [orders, setOrders] = useState([]);
    const [orderLoading, setOrderLoading] = useState(false);
    const [orderError, setOrderError] = useState(null);
    
    /**
     * 사용자별 주문 조회
     * API 호출: GET /api/v2/users/{userId}/orders
     */
    const fetchUserOrders = useCallback(async (userId) => {
        setOrderLoading(true);
        setOrderError(null);
        
        try {
            const response = await axios.get(`/api/v2/users/${userId}/orders`);
            
            if (response.data.success) {
                setOrders(response.data.data || []);
                return response.data.data;
            } else {
                throw new Error(response.data.message);
            }
            
        } catch (err) {
            setOrderError('주문 데이터 조회 중 오류가 발생했습니다: ' + err.message);
            console.error('Order fetch error:', err);
            return [];
        } finally {
            setOrderLoading(false);
        }
    }, []);
    
    /**
     * 주문 생성
     * API 호출: POST /api/v2/orders
     */
    const createOrder = useCallback(async (orderData) => {
        try {
            const response = await axios.post('/api/v2/orders', orderData);
            
            if (response.data.success) {
                setOrders(prevOrders => [response.data.data, ...prevOrders]);
                return response.data.data;
            } else {
                throw new Error(response.data.message);
            }
            
        } catch (err) {
            setOrderError('주문 생성 중 오류가 발생했습니다: ' + err.message);
            throw err;
        }
    }, []);
    
    return {
        orders,
        orderLoading,
        orderError,
        fetchUserOrders,
        createOrder,
        setOrderError
    };
};

// 커스텀 Hook: 분석 데이터 관리
const useAnalyticsData = () => {
    const [analyticsData, setAnalyticsData] = useState(null);
    const [analyticsLoading, setAnalyticsLoading] = useState(false);
    const [analyticsError, setAnalyticsError] = useState(null);
    
    /**
     * 종합 분석 실행
     * API 호출: POST /api/v2/analytics/comprehensive
     */
    const runComprehensiveAnalytics = useCallback(async (analyticsRequest) => {
        setAnalyticsLoading(true);
        setAnalyticsError(null);
        
        try {
            const response = await axios.post('/api/v2/analytics/comprehensive', analyticsRequest);
            
            if (response.data.success) {
                setAnalyticsData(response.data.data);
                return response.data.data;
            } else {
                throw new Error(response.data.message);
            }
            
        } catch (err) {
            setAnalyticsError('분석 실행 중 오류가 발생했습니다: ' + err.message);
            console.error('Analytics error:', err);
            return null;
        } finally {
            setAnalyticsLoading(false);
        }
    }, []);
    
    /**
     * 실시간 스트림 설정
     * API 호출: GET /api/v2/stream/realtime
     */
    const configureRealtimeStream = useCallback(async (streamConfig) => {
        try {
            const response = await axios.get('/api/v2/stream/realtime', {
                params: {
                    environment: streamConfig.environment,
                    batchSize: streamConfig.batchSize,
                    intervalMs: streamConfig.intervalMs
                }
            });
            
            if (response.data.success) {
                return response.data.data;
            } else {
                throw new Error(response.data.message);
            }
            
        } catch (err) {
            setAnalyticsError('스트림 설정 중 오류가 발생했습니다: ' + err.message);
            throw err;
        }
    }, []);
    
    return {
        analyticsData,
        analyticsLoading,
        analyticsError,
        runComprehensiveAnalytics,
        configureRealtimeStream,
        setAnalyticsError
    };
};

// 메인 React 컴포넌트
const ModernReactComponent = () => {
    // Custom Hooks 사용
    const { 
        users, 
        loading: userLoading, 
        error: userError, 
        fetchUsers, 
        createUser, 
        updateUser, 
        deleteUser 
    } = useUserData();
    
    const { 
        orders, 
        orderLoading, 
        orderError, 
        fetchUserOrders, 
        createOrder 
    } = useOrderData();
    
    const { 
        analyticsData, 
        analyticsLoading, 
        analyticsError, 
        runComprehensiveAnalytics 
    } = useAnalyticsData();
    
    // Local state
    const [selectedUser, setSelectedUser] = useState(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [searchParams, setSearchParams] = useState({
        search: '',
        status: '',
        userType: '',
        page: 0,
        size: 20
    });
    
    // Refs
    const searchInputRef = useRef(null);
    const modalRef = useRef(null);
    
    // Memoized values
    const filteredUsers = useMemo(() => {
        if (!searchParams.search) return users;
        
        const searchLower = searchParams.search.toLowerCase();
        return users.filter(user => 
            user.username.toLowerCase().includes(searchLower) ||
            user.email.toLowerCase().includes(searchLower) ||
            user.fullName.toLowerCase().includes(searchLower)
        );
    }, [users, searchParams.search]);
    
    const userStatistics = useMemo(() => {
        if (!users.length) return null;
        
        return {
            totalUsers: users.length,
            activeUsers: users.filter(u => u.status === 'ACTIVE').length,
            adminUsers: users.filter(u => u.userType === 'ADMIN').length,
            averageOrderCount: users.reduce((sum, u) => sum + (u.orderCount || 0), 0) / users.length
        };
    }, [users]);
    
    // Effects
    useEffect(() => {
        // 컴포넌트 마운트 시 초기 데이터 로드
        fetchUsers(searchParams);
    }, [fetchUsers]);
    
    useEffect(() => {
        // 검색 파라미터 변경 시 사용자 목록 새로고침
        const timeoutId = setTimeout(() => {
            fetchUsers(searchParams);
        }, 500); // 디바운싱
        
        return () => clearTimeout(timeoutId);
    }, [searchParams, fetchUsers]);
    
    useEffect(() => {
        // 선택된 사용자 변경 시 주문 정보 로드
        if (selectedUser) {
            fetchUserOrders(selectedUser.id);
        }
    }, [selectedUser, fetchUserOrders]);
    
    // Event handlers
    const handleSearchChange = useCallback((event) => {
        const value = event.target.value;
        setSearchParams(prev => ({
            ...prev,
            search: value,
            page: 0 // 검색 시 첫 페이지로 리셋
        }));
    }, []);
    
    const handleFilterChange = useCallback((filterType, value) => {
        setSearchParams(prev => ({
            ...prev,
            [filterType]: value,
            page: 0
        }));
    }, []);
    
    const handleUserSelect = useCallback((user) => {
        setSelectedUser(user);
    }, []);
    
    const handleCreateUser = useCallback(async (userData) => {
        try {
            const newUser = await createUser(userData);
            setShowCreateModal(false);
            
            // 성공 알림
            alert('사용자가 성공적으로 생성되었습니다.');
            
            return newUser;
        } catch (error) {
            console.error('Create user error:', error);
        }
    }, [createUser]);
    
    const handleUpdateUser = useCallback(async (userId, userData) => {
        try {
            const updatedUser = await updateUser(userId, userData);
            
            // 선택된 사용자 업데이트
            if (selectedUser && selectedUser.id === userId) {
                setSelectedUser(updatedUser);
            }
            
            alert('사용자 정보가 성공적으로 업데이트되었습니다.');
            
            return updatedUser;
        } catch (error) {
            console.error('Update user error:', error);
        }
    }, [updateUser, selectedUser]);
    
    const handleDeleteUser = useCallback(async (userId) => {
        if (!window.confirm('정말로 이 사용자를 삭제하시겠습니까?')) {
            return;
        }
        
        try {
            await deleteUser(userId);
            
            // 선택된 사용자가 삭제된 경우 선택 해제
            if (selectedUser && selectedUser.id === userId) {
                setSelectedUser(null);
            }
            
            alert('사용자가 성공적으로 삭제되었습니다.');
            
        } catch (error) {
            console.error('Delete user error:', error);
        }
    }, [deleteUser, selectedUser]);
    
    const handleRunAnalytics = useCallback(async () => {
        const analyticsRequest = {
            environment: 'prod',
            startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            endDate: new Date().toISOString().split('T')[0],
            reportTypes: ['USER_ACTIVITY', 'PRODUCT_PERFORMANCE'],
            periodType: 'DAILY',
            periodCount: 30,
            filters: {
                userStatus: 'ACTIVE'
            },
            includeOptions: ['PRODUCT_INFO', 'PAYMENT_INFO']
        };
        
        try {
            const result = await runComprehensiveAnalytics(analyticsRequest);
            
            if (result) {
                alert('분석이 성공적으로 완료되었습니다.');
            }
            
        } catch (error) {
            console.error('Analytics error:', error);
        }
    }, [runComprehensiveAnalytics]);
    
    // 페이지 변경 핸들러
    const handlePageChange = useCallback((newPage) => {
        setSearchParams(prev => ({
            ...prev,
            page: newPage
        }));
    }, []);
    
    // 키보드 이벤트 핸들러
    const handleKeyPress = useCallback((event) => {
        if (event.key === 'Escape') {
            setSelectedUser(null);
            setShowCreateModal(false);
        }
        
        if (event.key === 'Enter' && event.ctrlKey) {
            setShowCreateModal(true);
        }
    }, []);
    
    // 키보드 이벤트 등록
    useEffect(() => {
        document.addEventListener('keydown', handleKeyPress);
        return () => document.removeEventListener('keydown', handleKeyPress);
    }, [handleKeyPress]);
    
    // 포커스 관리
    useEffect(() => {
        if (showCreateModal && modalRef.current) {
            modalRef.current.focus();
        }
    }, [showCreateModal]);
    
    return (
        <div className="modern-react-component">
            <div className="header">
                <h2>사용자 관리 시스템 (React Hooks)</h2>
                <div className="header-actions">
                    <button 
                        onClick={() => fetchUsers(searchParams)}
                        disabled={userLoading}
                        className="btn btn-secondary"
                    >
                        {userLoading ? '로딩 중...' : '새로고침'}
                    </button>
                    
                    <button 
                        onClick={() => setShowCreateModal(true)}
                        className="btn btn-primary"
                    >
                        사용자 추가
                    </button>
                    
                    <button 
                        onClick={handleRunAnalytics}
                        disabled={analyticsLoading}
                        className="btn btn-info"
                    >
                        {analyticsLoading ? '분석 중...' : '종합 분석 실행'}
                    </button>
                </div>
            </div>
            
            {/* 통계 요약 */}
            {userStatistics && (
                <div className="statistics-panel">
                    <div className="stat-card">
                        <h4>전체 사용자</h4>
                        <span className="stat-number">{userStatistics.totalUsers}</span>
                    </div>
                    <div className="stat-card">
                        <h4>활성 사용자</h4>
                        <span className="stat-number">{userStatistics.activeUsers}</span>
                    </div>
                    <div className="stat-card">
                        <h4>관리자</h4>
                        <span className="stat-number">{userStatistics.adminUsers}</span>
                    </div>
                    <div className="stat-card">
                        <h4>평균 주문 수</h4>
                        <span className="stat-number">{userStatistics.averageOrderCount.toFixed(1)}</span>
                    </div>
                </div>
            )}
            
            {/* 검색 및 필터 */}
            <div className="search-filters">
                <input
                    ref={searchInputRef}
                    type="text"
                    placeholder="사용자명, 이메일로 검색..."
                    value={searchParams.search}
                    onChange={handleSearchChange}
                    className="search-input"
                />
                
                <select 
                    value={searchParams.status}
                    onChange={(e) => handleFilterChange('status', e.target.value)}
                    className="filter-select"
                >
                    <option value="">모든 상태</option>
                    <option value="ACTIVE">활성</option>
                    <option value="INACTIVE">비활성</option>
                    <option value="PENDING">대기</option>
                </select>
                
                <select 
                    value={searchParams.userType}
                    onChange={(e) => handleFilterChange('userType', e.target.value)}
                    className="filter-select"
                >
                    <option value="">모든 타입</option>
                    <option value="ADMIN">관리자</option>
                    <option value="MANAGER">매니저</option>
                    <option value="USER">일반사용자</option>
                    <option value="GUEST">게스트</option>
                </select>
            </div>
            
            {/* 에러 표시 */}
            {(userError || orderError || analyticsError) && (
                <div className="error-panel">
                    <p>{userError || orderError || analyticsError}</p>
                    <button onClick={() => {
                        setError(null);
                        setOrderError(null);
                        setAnalyticsError(null);
                    }}>
                        확인
                    </button>
                </div>
            )}
            
            {/* 사용자 목록 */}
            <div className="user-grid">
                {filteredUsers.map(user => (
                    <UserCard
                        key={user.id}
                        user={user}
                        selected={selectedUser && selectedUser.id === user.id}
                        onSelect={() => handleUserSelect(user)}
                        onUpdate={(userData) => handleUpdateUser(user.id, userData)}
                        onDelete={() => handleDeleteUser(user.id)}
                    />
                ))}
            </div>
            
            {/* 로딩 상태 */}
            {userLoading && (
                <div className="loading-overlay">
                    <div className="loading-spinner"></div>
                    <p>데이터를 불러오는 중...</p>
                </div>
            )}
            
            {/* 선택된 사용자의 주문 정보 */}
            {selectedUser && (
                <UserOrdersPanel
                    user={selectedUser}
                    orders={orders}
                    loading={orderLoading}
                    error={orderError}
                    onCreateOrder={createOrder}
                    onClose={() => setSelectedUser(null)}
                />
            )}
            
            {/* 사용자 생성 모달 */}
            {showCreateModal && (
                <UserCreateModal
                    ref={modalRef}
                    onSave={handleCreateUser}
                    onClose={() => setShowCreateModal(false)}
                />
            )}
            
            {/* 분석 결과 패널 */}
            {analyticsData && (
                <AnalyticsResultsPanel
                    data={analyticsData}
                    loading={analyticsLoading}
                    onClose={() => setAnalyticsData(null)}
                />
            )}
        </div>
    );
};

// 하위 컴포넌트들 (React Hooks 패턴 활용)

const UserCard = React.memo(({ user, selected, onSelect, onUpdate, onDelete }) => {
    const [editing, setEditing] = useState(false);
    const [editForm, setEditForm] = useState({
        fullName: user.fullName,
        email: user.email,
        status: user.status
    });
    
    const handleEdit = useCallback(() => {
        setEditing(true);
    }, []);
    
    const handleSave = useCallback(async () => {
        try {
            await onUpdate(editForm);
            setEditing(false);
        } catch (error) {
            console.error('Update error:', error);
        }
    }, [editForm, onUpdate]);
    
    const handleCancel = useCallback(() => {
        setEditForm({
            fullName: user.fullName,
            email: user.email,
            status: user.status
        });
        setEditing(false);
    }, [user]);
    
    return (
        <div className={`user-card ${selected ? 'selected' : ''}`} onClick={onSelect}>
            {editing ? (
                <div className="edit-form">
                    <input
                        value={editForm.fullName}
                        onChange={(e) => setEditForm(prev => ({ ...prev, fullName: e.target.value }))}
                        placeholder="전체 이름"
                    />
                    <input
                        type="email"
                        value={editForm.email}
                        onChange={(e) => setEditForm(prev => ({ ...prev, email: e.target.value }))}
                        placeholder="이메일"
                    />
                    <select
                        value={editForm.status}
                        onChange={(e) => setEditForm(prev => ({ ...prev, status: e.target.value }))}
                    >
                        <option value="ACTIVE">활성</option>
                        <option value="INACTIVE">비활성</option>
                        <option value="PENDING">대기</option>
                    </select>
                    <div className="edit-actions">
                        <button onClick={handleSave}>저장</button>
                        <button onClick={handleCancel}>취소</button>
                    </div>
                </div>
            ) : (
                <div className="user-info">
                    <h4>{user.fullName} ({user.username})</h4>
                    <p>{user.email}</p>
                    <div className="user-badges">
                        <span className={`status-badge status-${user.status.toLowerCase()}`}>
                            {user.status}
                        </span>
                        <span className={`type-badge type-${user.userType.toLowerCase()}`}>
                            {user.userType}
                        </span>
                    </div>
                    <div className="user-stats">
                        <span>주문: {user.orderCount || 0}건</span>
                        <span>구매: ₩{(user.totalSpent || 0).toLocaleString()}</span>
                    </div>
                    <div className="card-actions">
                        <button onClick={(e) => { e.stopPropagation(); handleEdit(); }}>수정</button>
                        <button onClick={(e) => { e.stopPropagation(); onDelete(); }}>삭제</button>
                    </div>
                </div>
            )}
        </div>
    );
});

// 사용자 주문 패널 컴포넌트
const UserOrdersPanel = ({ user, orders, loading, error, onCreateOrder, onClose }) => {
    const [showCreateOrderForm, setShowCreateOrderForm] = useState(false);
    const [orderForm, setOrderForm] = useState({
        items: [],
        paymentMethod: 'CARD',
        shippingAddress: ''
    });
    
    const totalOrderValue = useMemo(() => {
        return orders.reduce((sum, order) => sum + (order.totalAmount || 0), 0);
    }, [orders]);
    
    const handleCreateOrder = useCallback(async () => {
        try {
            const orderData = {
                userId: user.id,
                orderItems: orderForm.items,
                paymentMethod: orderForm.paymentMethod,
                shippingAddress: orderForm.shippingAddress
            };
            
            await onCreateOrder(orderData);
            setShowCreateOrderForm(false);
            setOrderForm({ items: [], paymentMethod: 'CARD', shippingAddress: '' });
            
        } catch (error) {
            console.error('Create order error:', error);
        }
    }, [user.id, orderForm, onCreateOrder]);
    
    return (
        <div className="user-orders-panel">
            <div className="panel-header">
                <h3>{user.fullName}의 주문 내역</h3>
                <div className="panel-actions">
                    <button onClick={() => setShowCreateOrderForm(true)}>새 주문</button>
                    <button onClick={onClose}>닫기</button>
                </div>
            </div>
            
            <div className="orders-summary">
                <p>총 주문 수: {orders.length}건</p>
                <p>총 주문 금액: ₩{totalOrderValue.toLocaleString()}</p>
            </div>
            
            {loading && <div className="loading">주문 정보를 불러오는 중...</div>}
            {error && <div className="error">{error}</div>}
            
            <div className="orders-list">
                {orders.map(order => (
                    <div key={order.id} className="order-item">
                        <div className="order-info">
                            <span>주문 #{order.id}</span>
                            <span>{new Date(order.orderDate).toLocaleDateString()}</span>
                            <span className={`status-${order.status.toLowerCase()}`}>{order.status}</span>
                        </div>
                        <div className="order-amount">
                            ₩{order.totalAmount.toLocaleString()}
                        </div>
                    </div>
                ))}
            </div>
            
            {showCreateOrderForm && (
                <div className="create-order-form">
                    <h4>새 주문 생성</h4>
                    <select
                        value={orderForm.paymentMethod}
                        onChange={(e) => setOrderForm(prev => ({ ...prev, paymentMethod: e.target.value }))}
                    >
                        <option value="CARD">카드</option>
                        <option value="BANK_TRANSFER">계좌이체</option>
                        <option value="CASH">현금</option>
                    </select>
                    
                    <textarea
                        placeholder="배송 주소"
                        value={orderForm.shippingAddress}
                        onChange={(e) => setOrderForm(prev => ({ ...prev, shippingAddress: e.target.value }))}
                    />
                    
                    <div className="form-actions">
                        <button onClick={handleCreateOrder}>주문 생성</button>
                        <button onClick={() => setShowCreateOrderForm(false)}>취소</button>
                    </div>
                </div>
            )}
        </div>
    );
};

// 사용자 생성 모달 컴포넌트
const UserCreateModal = React.forwardRef(({ onSave, onClose }, ref) => {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        fullName: '',
        userType: 'USER',
        departmentId: null,
        profileData: {
            phone: '',
            address: '',
            gender: ''
        },
        settingsData: {
            theme: 'LIGHT',
            language: 'ko',
            timezone: 'Asia/Seoul'
        }
    });
    
    const [validationErrors, setValidationErrors] = useState({});
    
    const validateForm = useCallback(() => {
        const errors = {};
        
        if (!formData.username || formData.username.length < 3) {
            errors.username = '사용자명은 3자 이상이어야 합니다';
        }
        
        if (!formData.email || !/\S+@\S+\.\S+/.test(formData.email)) {
            errors.email = '올바른 이메일 주소를 입력해주세요';
        }
        
        if (!formData.fullName || formData.fullName.length < 2) {
            errors.fullName = '전체 이름은 2자 이상이어야 합니다';
        }
        
        setValidationErrors(errors);
        return Object.keys(errors).length === 0;
    }, [formData]);
    
    const handleSubmit = useCallback(async (e) => {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }
        
        try {
            await onSave(formData);
            setFormData({
                username: '',
                email: '',
                fullName: '',
                userType: 'USER',
                departmentId: null,
                profileData: { phone: '', address: '', gender: '' },
                settingsData: { theme: 'LIGHT', language: 'ko', timezone: 'Asia/Seoul' }
            });
        } catch (error) {
            console.error('Save error:', error);
        }
    }, [formData, validateForm, onSave]);
    
    const handleInputChange = useCallback((field, value) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }));
        
        // 해당 필드의 검증 에러 제거
        if (validationErrors[field]) {
            setValidationErrors(prev => {
                const newErrors = { ...prev };
                delete newErrors[field];
                return newErrors;
            });
        }
    }, [validationErrors]);
    
    const handleNestedInputChange = useCallback((parentField, childField, value) => {
        setFormData(prev => ({
            ...prev,
            [parentField]: {
                ...prev[parentField],
                [childField]: value
            }
        }));
    }, []);
    
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()} ref={ref} tabIndex={-1}>
                <h3>새 사용자 생성</h3>
                
                <form onSubmit={handleSubmit}>
                    <div className="form-section">
                        <h4>기본 정보</h4>
                        
                        <div className="form-group">
                            <label>사용자명:</label>
                            <input
                                type="text"
                                value={formData.username}
                                onChange={(e) => handleInputChange('username', e.target.value)}
                                className={validationErrors.username ? 'error' : ''}
                                required
                            />
                            {validationErrors.username && (
                                <span className="error-message">{validationErrors.username}</span>
                            )}
                        </div>
                        
                        <div className="form-group">
                            <label>이메일:</label>
                            <input
                                type="email"
                                value={formData.email}
                                onChange={(e) => handleInputChange('email', e.target.value)}
                                className={validationErrors.email ? 'error' : ''}
                                required
                            />
                            {validationErrors.email && (
                                <span className="error-message">{validationErrors.email}</span>
                            )}
                        </div>
                        
                        <div className="form-group">
                            <label>전체 이름:</label>
                            <input
                                type="text"
                                value={formData.fullName}
                                onChange={(e) => handleInputChange('fullName', e.target.value)}
                                className={validationErrors.fullName ? 'error' : ''}
                                required
                            />
                            {validationErrors.fullName && (
                                <span className="error-message">{validationErrors.fullName}</span>
                            )}
                        </div>
                        
                        <div className="form-group">
                            <label>사용자 타입:</label>
                            <select
                                value={formData.userType}
                                onChange={(e) => handleInputChange('userType', e.target.value)}
                                required
                            >
                                <option value="USER">일반사용자</option>
                                <option value="MANAGER">매니저</option>
                                <option value="ADMIN">관리자</option>
                                <option value="GUEST">게스트</option>
                            </select>
                        </div>
                    </div>
                    
                    <div className="form-section">
                        <h4>프로필 정보</h4>
                        
                        <div className="form-group">
                            <label>전화번호:</label>
                            <input
                                type="tel"
                                value={formData.profileData.phone}
                                onChange={(e) => handleNestedInputChange('profileData', 'phone', e.target.value)}
                            />
                        </div>
                        
                        <div className="form-group">
                            <label>주소:</label>
                            <textarea
                                value={formData.profileData.address}
                                onChange={(e) => handleNestedInputChange('profileData', 'address', e.target.value)}
                                rows={3}
                            />
                        </div>
                        
                        <div className="form-group">
                            <label>성별:</label>
                            <select
                                value={formData.profileData.gender}
                                onChange={(e) => handleNestedInputChange('profileData', 'gender', e.target.value)}
                            >
                                <option value="">선택 안함</option>
                                <option value="M">남성</option>
                                <option value="F">여성</option>
                                <option value="OTHER">기타</option>
                            </select>
                        </div>
                    </div>
                    
                    <div className="form-section">
                        <h4>설정</h4>
                        
                        <div className="form-group">
                            <label>테마:</label>
                            <select
                                value={formData.settingsData.theme}
                                onChange={(e) => handleNestedInputChange('settingsData', 'theme', e.target.value)}
                            >
                                <option value="LIGHT">라이트</option>
                                <option value="DARK">다크</option>
                                <option value="AUTO">자동</option>
                            </select>
                        </div>
                        
                        <div className="form-group">
                            <label>언어:</label>
                            <select
                                value={formData.settingsData.language}
                                onChange={(e) => handleNestedInputChange('settingsData', 'language', e.target.value)}
                            >
                                <option value="ko">한국어</option>
                                <option value="en">English</option>
                                <option value="ja">日本語</option>
                                <option value="zh">中文</option>
                            </select>
                        </div>
                    </div>
                    
                    <div className="modal-actions">
                        <button type="submit">생성</button>
                        <button type="button" onClick={onClose}>취소</button>
                    </div>
                </form>
            </div>
        </div>
    );
});

// 분석 결과 패널 컴포넌트
const AnalyticsResultsPanel = ({ data, loading, onClose }) => {
    const [activeTab, setActiveTab] = useState('overview');
    
    const analysisOverview = useMemo(() => {
        if (!data) return null;
        
        return {
            totalRecords: data.recordCount || 0,
            reportTypes: Object.keys(data.reportData || {}),
            generatedAt: data.generatedAt,
            processingTime: data.processingTimeMs || 'N/A'
        };
    }, [data]);
    
    return (
        <div className="analytics-panel">
            <div className="panel-header">
                <h3>분석 결과</h3>
                <button onClick={onClose}>닫기</button>
            </div>
            
            {loading && <div className="loading">분석을 실행하는 중...</div>}
            
            {data && (
                <>
                    <div className="tab-navigation">
                        <button 
                            className={activeTab === 'overview' ? 'active' : ''}
                            onClick={() => setActiveTab('overview')}
                        >
                            개요
                        </button>
                        <button 
                            className={activeTab === 'details' ? 'active' : ''}
                            onClick={() => setActiveTab('details')}
                        >
                            상세 결과
                        </button>
                        <button 
                            className={activeTab === 'trends' ? 'active' : ''}
                            onClick={() => setActiveTab('trends')}
                        >
                            트렌드 분석
                        </button>
                    </div>
                    
                    <div className="tab-content">
                        {activeTab === 'overview' && analysisOverview && (
                            <div className="overview-content">
                                <div className="overview-stats">
                                    <div className="stat-item">
                                        <label>총 레코드 수:</label>
                                        <span>{analysisOverview.totalRecords.toLocaleString()}</span>
                                    </div>
                                    <div className="stat-item">
                                        <label>리포트 타입:</label>
                                        <span>{analysisOverview.reportTypes.join(', ')}</span>
                                    </div>
                                    <div className="stat-item">
                                        <label>생성 시간:</label>
                                        <span>{new Date(analysisOverview.generatedAt).toLocaleString()}</span>
                                    </div>
                                    <div className="stat-item">
                                        <label>처리 시간:</label>
                                        <span>{analysisOverview.processingTime}</span>
                                    </div>
                                </div>
                            </div>
                        )}
                        
                        {activeTab === 'details' && (
                            <div className="details-content">
                                <pre>{JSON.stringify(data.reportData, null, 2)}</pre>
                            </div>
                        )}
                        
                        {activeTab === 'trends' && data.trendsAnalysis && (
                            <div className="trends-content">
                                <div className="trends-chart">
                                    {data.trendsAnalysis.map((trend, index) => (
                                        <div key={index} className="trend-item">
                                            <span>{trend.time_period}</span>
                                            <span>₩{(trend.total_revenue || 0).toLocaleString()}</span>
                                            <span>{trend.order_count}건</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

export default ModernReactComponent;



