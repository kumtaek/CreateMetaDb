import React, { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * 마이크로서비스 통합 대시보드 컴포넌트
 * FRONTEND_API: MicroserviceDashboard -> API_ENTRY: MicroserviceController의 여러 통합 API들
 */
const MicroserviceDashboard = () => {
    const [userProfile, setUserProfile] = useState(null);
    const [orderDetails, setOrderDetails] = useState(null);
    const [dashboardData, setDashboardData] = useState(null);
    const [searchResults, setSearchResults] = useState(null);
    const [notificationResult, setNotificationResult] = useState(null);
    const [loading, setLoading] = useState({
        profile: false,
        order: false,
        dashboard: false,
        search: false,
        notification: false
    });
    const [error, setError] = useState(null);
    
    // 폼 상태
    const [userId, setUserId] = useState('1');
    const [orderId, setOrderId] = useState('1');
    const [searchQuery, setSearchQuery] = useState('');
    const [notification, setNotification] = useState({
        type: 'email',
        recipient: '',
        subject: '',
        message: ''
    });

    /**
     * 통합 사용자 프로필 조회
     * FRONTEND_API: GET /api/user-profile -> API_ENTRY: MicroserviceController.getUserProfile()
     */
    const fetchUserProfile = async (targetUserId = userId) => {
        setLoading(prev => ({ ...prev, profile: true }));
        setError(null);
        
        try {
            const response = await axios.get(`/api/user-profile?userId=${targetUserId}`);
            
            // 마이크로서비스에서 통합된 사용자 정보
            if (response.data) {
                setUserProfile(response.data);
            } else {
                // Mock 데이터 (실제 API 구현 전까지)
                setUserProfile({
                    userId: targetUserId,
                    name: '홍길동',
                    email: 'hong@example.com',
                    profile: {
                        avatar: '/images/avatar.jpg',
                        bio: '개발자입니다.',
                        joinDate: '2024-01-01'
                    },
                    preferences: {
                        language: 'ko',
                        theme: 'dark',
                        notifications: true
                    },
                    statistics: {
                        totalOrders: 15,
                        totalSpent: 150000,
                        loyaltyPoints: 1200
                    }
                });
            }
        } catch (error) {
            setError('사용자 프로필 조회 중 오류가 발생했습니다: ' + error.message);
            console.error('사용자 프로필 조회 실패:', error);
        } finally {
            setLoading(prev => ({ ...prev, profile: false }));
        }
    };

    /**
     * 통합 주문 상세 정보 조회
     * FRONTEND_API: GET /api/order-details -> API_ENTRY: MicroserviceController.getOrderDetails()
     */
    const fetchOrderDetails = async (targetOrderId = orderId) => {
        setLoading(prev => ({ ...prev, order: true }));
        setError(null);
        
        try {
            const response = await axios.get(`/api/order-details?orderId=${targetOrderId}`);
            
            if (response.data) {
                setOrderDetails(response.data);
            } else {
                // Mock 데이터
                setOrderDetails({
                    orderId: targetOrderId,
                    orderDate: '2024-09-15',
                    status: 'DELIVERED',
                    customer: {
                        id: 1,
                        name: '홍길동',
                        email: 'hong@example.com'
                    },
                    products: [
                        {
                            id: 101,
                            name: '노트북',
                            price: 1200000,
                            quantity: 1,
                            category: 'ELECTRONICS'
                        },
                        {
                            id: 102,
                            name: '마우스',
                            price: 50000,
                            quantity: 2,
                            category: 'ELECTRONICS'
                        }
                    ],
                    totalAmount: 1300000,
                    shippingAddress: '서울시 강남구',
                    paymentMethod: 'CARD'
                });
            }
        } catch (error) {
            setError('주문 상세 조회 중 오류가 발생했습니다: ' + error.message);
            console.error('주문 상세 조회 실패:', error);
        } finally {
            setLoading(prev => ({ ...prev, order: false }));
        }
    };

    /**
     * 통합 대시보드 데이터 조회
     * FRONTEND_API: GET /api/dashboard -> API_ENTRY: MicroserviceController.getDashboardData()
     */
    const fetchDashboardData = async () => {
        setLoading(prev => ({ ...prev, dashboard: true }));
        setError(null);
        
        try {
            const response = await axios.get('/api/dashboard');
            
            if (response.data) {
                setDashboardData(response.data);
            } else {
                // Mock 데이터
                setDashboardData({
                    statistics: {
                        totalUsers: 1250,
                        totalOrders: 3420,
                        totalRevenue: 45600000,
                        activeProducts: 890
                    },
                    notifications: {
                        unreadCount: 7,
                        recentNotifications: [
                            { id: 1, message: '새 주문이 접수되었습니다.', time: '10분 전' },
                            { id: 2, message: '재고가 부족합니다.', time: '1시간 전' },
                            { id: 3, message: '신규 회원이 가입했습니다.', time: '2시간 전' }
                        ]
                    },
                    recommendations: [
                        { type: 'product', title: '인기 상품 추천', items: ['노트북', '스마트폰', '태블릿'] },
                        { type: 'user', title: '신규 고객 타겟팅', items: ['20대 남성', '30대 여성'] }
                    ],
                    recentActivity: [
                        { action: '상품 등록', user: '관리자', time: '5분 전' },
                        { action: '주문 처리', user: '직원A', time: '15분 전' },
                        { action: '고객 문의 답변', user: '직원B', time: '30분 전' }
                    ]
                });
            }
        } catch (error) {
            setError('대시보드 데이터 조회 중 오류가 발생했습니다: ' + error.message);
            console.error('대시보드 데이터 조회 실패:', error);
        } finally {
            setLoading(prev => ({ ...prev, dashboard: false }));
        }
    };

    /**
     * 통합 검색 실행
     * FRONTEND_API: GET /api/search -> API_ENTRY: MicroserviceController.globalSearch()
     */
    const executeGlobalSearch = async () => {
        if (!searchQuery.trim()) {
            setError('검색어를 입력해주세요.');
            return;
        }
        
        setLoading(prev => ({ ...prev, search: true }));
        setError(null);
        
        try {
            const response = await axios.get(`/api/search?query=${encodeURIComponent(searchQuery)}`);
            
            if (response.data) {
                setSearchResults(response.data);
            } else {
                // Mock 데이터
                setSearchResults({
                    query: searchQuery,
                    totalResults: 25,
                    users: [
                        { id: 1, name: '홍길동', email: 'hong@example.com', type: 'user' },
                        { id: 2, name: '김철수', email: 'kim@example.com', type: 'user' }
                    ],
                    products: [
                        { id: 101, name: '노트북', category: 'ELECTRONICS', price: 1200000 },
                        { id: 102, name: '스마트폰', category: 'ELECTRONICS', price: 800000 }
                    ],
                    orders: [
                        { id: 1001, customerId: 1, status: 'COMPLETED', date: '2024-09-15' },
                        { id: 1002, customerId: 2, status: 'PROCESSING', date: '2024-09-16' }
                    ]
                });
            }
        } catch (error) {
            setError('검색 중 오류가 발생했습니다: ' + error.message);
            console.error('검색 실패:', error);
        } finally {
            setLoading(prev => ({ ...prev, search: false }));
        }
    };

    /**
     * 통합 알림 발송
     * FRONTEND_API: POST /api/notify -> API_ENTRY: MicroserviceController.sendNotification()
     */
    const sendNotification = async () => {
        if (!notification.recipient || !notification.subject || !notification.message) {
            setError('모든 알림 필드를 입력해주세요.');
            return;
        }
        
        setLoading(prev => ({ ...prev, notification: true }));
        setError(null);
        setNotificationResult(null);
        
        try {
            const response = await axios.post('/api/notify', {
                type: notification.type,
                recipient: notification.recipient,
                subject: notification.subject,
                message: notification.message,
                timestamp: new Date().toISOString()
            });
            
            if (response.data) {
                setNotificationResult(response.data);
            } else {
                // Mock 결과
                setNotificationResult({
                    success: true,
                    message: '알림이 성공적으로 발송되었습니다.',
                    details: {
                        type: notification.type,
                        recipient: notification.recipient,
                        sentAt: new Date().toLocaleString(),
                        messageId: 'MSG-' + Date.now()
                    }
                });
            }
        } catch (error) {
            setError('알림 발송 중 오류가 발생했습니다: ' + error.message);
            console.error('알림 발송 실패:', error);
        } finally {
            setLoading(prev => ({ ...prev, notification: false }));
        }
    };

    // 컴포넌트 마운트 시 대시보드 데이터 로드
    useEffect(() => {
        fetchDashboardData();
    }, []);

    // 알림 폼 변경 핸들러
    const handleNotificationChange = (field, value) => {
        setNotification(prev => ({
            ...prev,
            [field]: value
        }));
    };

    return (
        <div className="microservice-dashboard">
            <h2>마이크로서비스 통합 대시보드</h2>
            
            {error && (
                <div className="error-message" style={{color: 'red', marginBottom: '10px'}}>
                    {error}
                </div>
            )}

            {/* 대시보드 통계 섹션 */}
            <div className="dashboard-stats-section">
                <h3>시스템 통계</h3>
                <button onClick={fetchDashboardData} disabled={loading.dashboard}>
                    {loading.dashboard ? '로딩 중...' : '새로고침'}
                </button>
                
                {dashboardData && (
                    <div className="stats-grid">
                        <div className="stat-card">
                            <h4>전체 사용자</h4>
                            <p className="stat-number">{dashboardData.statistics?.totalUsers?.toLocaleString()}</p>
                        </div>
                        <div className="stat-card">
                            <h4>전체 주문</h4>
                            <p className="stat-number">{dashboardData.statistics?.totalOrders?.toLocaleString()}</p>
                        </div>
                        <div className="stat-card">
                            <h4>총 매출</h4>
                            <p className="stat-number">{dashboardData.statistics?.totalRevenue?.toLocaleString()}원</p>
                        </div>
                        <div className="stat-card">
                            <h4>활성 상품</h4>
                            <p className="stat-number">{dashboardData.statistics?.activeProducts?.toLocaleString()}</p>
                        </div>
                    </div>
                )}
            </div>

            {/* 사용자 프로필 조회 섹션 */}
            <div className="user-profile-section">
                <h3>통합 사용자 프로필 조회</h3>
                <div className="profile-form">
                    <input
                        type="number"
                        placeholder="사용자 ID"
                        value={userId}
                        onChange={(e) => setUserId(e.target.value)}
                        min="1"
                    />
                    <button onClick={() => fetchUserProfile(userId)} disabled={loading.profile}>
                        {loading.profile ? '조회 중...' : '프로필 조회'}
                    </button>
                </div>
                
                {userProfile && (
                    <div className="profile-details">
                        <h4>{userProfile.name} ({userProfile.email})</h4>
                        <div className="profile-grid">
                            <div className="profile-info">
                                <h5>기본 정보</h5>
                                <p>가입일: {userProfile.profile?.joinDate}</p>
                                <p>소개: {userProfile.profile?.bio}</p>
                            </div>
                            <div className="profile-preferences">
                                <h5>설정</h5>
                                <p>언어: {userProfile.preferences?.language}</p>
                                <p>테마: {userProfile.preferences?.theme}</p>
                                <p>알림: {userProfile.preferences?.notifications ? '켜짐' : '꺼짐'}</p>
                            </div>
                            <div className="profile-stats">
                                <h5>통계</h5>
                                <p>총 주문: {userProfile.statistics?.totalOrders}회</p>
                                <p>총 구매액: {userProfile.statistics?.totalSpent?.toLocaleString()}원</p>
                                <p>적립 포인트: {userProfile.statistics?.loyaltyPoints?.toLocaleString()}점</p>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* 주문 상세 조회 섹션 */}
            <div className="order-details-section">
                <h3>통합 주문 상세 조회</h3>
                <div className="order-form">
                    <input
                        type="number"
                        placeholder="주문 ID"
                        value={orderId}
                        onChange={(e) => setOrderId(e.target.value)}
                        min="1"
                    />
                    <button onClick={() => fetchOrderDetails(orderId)} disabled={loading.order}>
                        {loading.order ? '조회 중...' : '주문 조회'}
                    </button>
                </div>
                
                {orderDetails && (
                    <div className="order-details">
                        <h4>주문 #{orderDetails.orderId}</h4>
                        <div className="order-info">
                            <p>주문일: {orderDetails.orderDate}</p>
                            <p>상태: {orderDetails.status}</p>
                            <p>고객: {orderDetails.customer?.name} ({orderDetails.customer?.email})</p>
                            <p>총 금액: {orderDetails.totalAmount?.toLocaleString()}원</p>
                            <p>배송지: {orderDetails.shippingAddress}</p>
                            <p>결제 방법: {orderDetails.paymentMethod}</p>
                        </div>
                        <div className="order-products">
                            <h5>주문 상품</h5>
                            {orderDetails.products?.map((product, index) => (
                                <div key={index} className="product-item">
                                    <span>{product.name}</span>
                                    <span>{product.quantity}개</span>
                                    <span>{product.price?.toLocaleString()}원</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* 통합 검색 섹션 */}
            <div className="global-search-section">
                <h3>통합 검색</h3>
                <div className="search-form">
                    <input
                        type="text"
                        placeholder="검색어 입력"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && executeGlobalSearch()}
                    />
                    <button onClick={executeGlobalSearch} disabled={loading.search}>
                        {loading.search ? '검색 중...' : '통합 검색'}
                    </button>
                </div>
                
                {searchResults && (
                    <div className="search-results">
                        <h4>검색 결과: "{searchResults.query}" ({searchResults.totalResults}개)</h4>
                        
                        {searchResults.users?.length > 0 && (
                            <div className="search-category">
                                <h5>사용자 ({searchResults.users.length}명)</h5>
                                {searchResults.users.map(user => (
                                    <div key={user.id} className="search-item">
                                        {user.name} - {user.email}
                                    </div>
                                ))}
                            </div>
                        )}
                        
                        {searchResults.products?.length > 0 && (
                            <div className="search-category">
                                <h5>상품 ({searchResults.products.length}개)</h5>
                                {searchResults.products.map(product => (
                                    <div key={product.id} className="search-item">
                                        {product.name} - {product.price?.toLocaleString()}원
                                    </div>
                                ))}
                            </div>
                        )}
                        
                        {searchResults.orders?.length > 0 && (
                            <div className="search-category">
                                <h5>주문 ({searchResults.orders.length}개)</h5>
                                {searchResults.orders.map(order => (
                                    <div key={order.id} className="search-item">
                                        주문 #{order.id} - {order.status} ({order.date})
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* 통합 알림 발송 섹션 */}
            <div className="notification-section">
                <h3>통합 알림 발송</h3>
                <div className="notification-form">
                    <select
                        value={notification.type}
                        onChange={(e) => handleNotificationChange('type', e.target.value)}
                    >
                        <option value="email">이메일</option>
                        <option value="sms">SMS</option>
                        <option value="push">푸시 알림</option>
                    </select>
                    <input
                        type="text"
                        placeholder="받는 사람"
                        value={notification.recipient}
                        onChange={(e) => handleNotificationChange('recipient', e.target.value)}
                    />
                    <input
                        type="text"
                        placeholder="제목"
                        value={notification.subject}
                        onChange={(e) => handleNotificationChange('subject', e.target.value)}
                    />
                    <textarea
                        placeholder="메시지 내용"
                        value={notification.message}
                        onChange={(e) => handleNotificationChange('message', e.target.value)}
                        rows="3"
                    />
                    <button onClick={sendNotification} disabled={loading.notification}>
                        {loading.notification ? '발송 중...' : '알림 발송'}
                    </button>
                </div>
                
                {notificationResult && (
                    <div className={`notification-result ${notificationResult.success ? 'success' : 'failure'}`}
                         style={{color: notificationResult.success ? 'green' : 'red'}}>
                        <p>{notificationResult.message}</p>
                        {notificationResult.details && (
                            <div className="result-details">
                                <p>발송 시간: {notificationResult.details.sentAt}</p>
                                <p>메시지 ID: {notificationResult.details.messageId}</p>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* 최근 활동 및 알림 */}
            {dashboardData && (
                <div className="activity-notifications-section">
                    <div className="recent-activity">
                        <h3>최근 활동</h3>
                        {dashboardData.recentActivity?.map((activity, index) => (
                            <div key={index} className="activity-item">
                                <span className="activity-action">{activity.action}</span>
                                <span className="activity-user">by {activity.user}</span>
                                <span className="activity-time">{activity.time}</span>
                            </div>
                        ))}
                    </div>
                    
                    <div className="notifications">
                        <h3>알림 ({dashboardData.notifications?.unreadCount})</h3>
                        {dashboardData.notifications?.recentNotifications?.map((notif, index) => (
                            <div key={index} className="notification-item">
                                <span className="notification-message">{notif.message}</span>
                                <span className="notification-time">{notif.time}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default MicroserviceDashboard;
