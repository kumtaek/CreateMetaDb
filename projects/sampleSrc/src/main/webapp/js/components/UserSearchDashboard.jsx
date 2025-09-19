import React, { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * 사용자 검색 대시보드 컴포넌트
 * FRONTEND_API: UserSearchDashboard -> API_ENTRY: UserController의 여러 검색 API들
 */
const UserSearchDashboard = () => {
    const [users, setUsers] = useState([]);
    const [statistics, setStatistics] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    // 기본 검색 파라미터
    const [searchParams, setSearchParams] = useState({
        name: '',
        email: '',
        status: '',
        page: 0,
        size: 10
    });
    
    // 고급 검색 파라미터
    const [advancedSearch, setAdvancedSearch] = useState({
        userType: '',
        minAge: '',
        maxAge: '',
        startDate: '',
        endDate: '',
        statusList: '',
        page: 0,
        size: 20
    });
    
    const [selectedUserType, setSelectedUserType] = useState('NORMAL');

    /**
     * 기본 사용자 목록 조회
     * FRONTEND_API: GET /user/list -> API_ENTRY: UserController.getUserList()
     */
    const fetchUserList = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const params = new URLSearchParams();
            if (searchParams.name) params.append('name', searchParams.name);
            if (searchParams.email) params.append('email', searchParams.email);
            if (searchParams.status) params.append('status', searchParams.status);
            params.append('page', searchParams.page);
            params.append('size', searchParams.size);
            
            const response = await axios.get(`/user/list?${params.toString()}`);
            
            // Spring MVC에서 Model 데이터를 JSON으로 받는다고 가정
            if (response.data.users) {
                setUsers(response.data.users);
                setStatistics(response.data.statistics || {});
            }
        } catch (error) {
            setError('사용자 목록 조회 중 오류가 발생했습니다: ' + error.message);
            console.error('사용자 목록 조회 실패:', error);
        } finally {
            setLoading(false);
        }
    };

    /**
     * 고급 검색 실행
     * FRONTEND_API: POST /user/search -> API_ENTRY: UserController.searchUsers()
     */
    const executeAdvancedSearch = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const searchData = new FormData();
            
            // 고급 검색 파라미터 추가
            if (advancedSearch.userType) searchData.append('userType', advancedSearch.userType);
            if (advancedSearch.minAge) searchData.append('minAge', advancedSearch.minAge);
            if (advancedSearch.maxAge) searchData.append('maxAge', advancedSearch.maxAge);
            if (advancedSearch.startDate) searchData.append('startDate', advancedSearch.startDate);
            if (advancedSearch.endDate) searchData.append('endDate', advancedSearch.endDate);
            if (advancedSearch.statusList) searchData.append('statusList', advancedSearch.statusList);
            searchData.append('page', advancedSearch.page);
            searchData.append('size', advancedSearch.size);
            
            const response = await axios.post('/user/search', searchData, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });
            
            if (response.data.users) {
                setUsers(response.data.users);
                setStatistics(response.data.searchAnalysis || {});
            }
        } catch (error) {
            setError('고급 검색 중 오류가 발생했습니다: ' + error.message);
            console.error('고급 검색 실패:', error);
        } finally {
            setLoading(false);
        }
    };

    /**
     * 타입별 사용자 조회
     * FRONTEND_API: GET /user/dynamic/{type} -> API_ENTRY: UserController.getUsersByType()
     */
    const fetchUsersByType = async (userType) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await axios.get(`/user/dynamic/${userType}?page=0&size=15`);
            
            if (response.data.users) {
                setUsers(response.data.users);
                setStatistics(response.data.typeStatistics || {});
            }
        } catch (error) {
            setError(`타입별 사용자 조회 중 오류가 발생했습니다: ${error.message}`);
            console.error('타입별 사용자 조회 실패:', error);
        } finally {
            setLoading(false);
        }
    };

    // 컴포넌트 마운트 시 기본 데이터 로드
    useEffect(() => {
        fetchUserList();
    }, []);

    // 검색 파라미터 변경 핸들러
    const handleSearchParamChange = (field, value) => {
        setSearchParams(prev => ({
            ...prev,
            [field]: value
        }));
    };

    // 고급 검색 파라미터 변경 핸들러
    const handleAdvancedSearchChange = (field, value) => {
        setAdvancedSearch(prev => ({
            ...prev,
            [field]: value
        }));
    };

    // 페이지 변경 핸들러
    const handlePageChange = (newPage) => {
        setSearchParams(prev => ({
            ...prev,
            page: newPage
        }));
    };

    // 기본 검색 실행
    const handleBasicSearch = () => {
        fetchUserList();
    };

    // 타입별 검색 실행
    const handleTypeSearch = () => {
        fetchUsersByType(selectedUserType);
    };

    return (
        <div className="user-search-dashboard">
            <h2>사용자 검색 대시보드</h2>
            
            {error && (
                <div className="error-message" style={{color: 'red', marginBottom: '10px'}}>
                    {error}
                </div>
            )}
            
            {/* 기본 검색 섹션 */}
            <div className="basic-search-section">
                <h3>기본 검색</h3>
                <div className="search-form">
                    <input
                        type="text"
                        placeholder="이름"
                        value={searchParams.name}
                        onChange={(e) => handleSearchParamChange('name', e.target.value)}
                    />
                    <input
                        type="email"
                        placeholder="이메일"
                        value={searchParams.email}
                        onChange={(e) => handleSearchParamChange('email', e.target.value)}
                    />
                    <select
                        value={searchParams.status}
                        onChange={(e) => handleSearchParamChange('status', e.target.value)}
                    >
                        <option value="">전체 상태</option>
                        <option value="ACTIVE">활성</option>
                        <option value="INACTIVE">비활성</option>
                    </select>
                    <input
                        type="number"
                        placeholder="페이지 크기"
                        value={searchParams.size}
                        onChange={(e) => handleSearchParamChange('size', parseInt(e.target.value) || 10)}
                        min="1"
                        max="100"
                    />
                    <button onClick={handleBasicSearch} disabled={loading}>
                        {loading ? '검색 중...' : '기본 검색'}
                    </button>
                </div>
            </div>

            {/* 고급 검색 섹션 */}
            <div className="advanced-search-section">
                <h3>고급 검색</h3>
                <div className="advanced-search-form">
                    <select
                        value={advancedSearch.userType}
                        onChange={(e) => handleAdvancedSearchChange('userType', e.target.value)}
                    >
                        <option value="">전체 타입</option>
                        <option value="NORMAL">일반</option>
                        <option value="PREMIUM">프리미엄</option>
                        <option value="ADMIN">관리자</option>
                        <option value="GUEST">게스트</option>
                    </select>
                    <input
                        type="number"
                        placeholder="최소 나이"
                        value={advancedSearch.minAge}
                        onChange={(e) => handleAdvancedSearchChange('minAge', e.target.value)}
                        min="0"
                        max="150"
                    />
                    <input
                        type="number"
                        placeholder="최대 나이"
                        value={advancedSearch.maxAge}
                        onChange={(e) => handleAdvancedSearchChange('maxAge', e.target.value)}
                        min="0"
                        max="150"
                    />
                    <input
                        type="date"
                        placeholder="시작일"
                        value={advancedSearch.startDate}
                        onChange={(e) => handleAdvancedSearchChange('startDate', e.target.value)}
                    />
                    <input
                        type="date"
                        placeholder="종료일"
                        value={advancedSearch.endDate}
                        onChange={(e) => handleAdvancedSearchChange('endDate', e.target.value)}
                    />
                    <input
                        type="text"
                        placeholder="상태 목록 (콤마 구분)"
                        value={advancedSearch.statusList}
                        onChange={(e) => handleAdvancedSearchChange('statusList', e.target.value)}
                    />
                    <button onClick={executeAdvancedSearch} disabled={loading}>
                        {loading ? '검색 중...' : '고급 검색'}
                    </button>
                </div>
            </div>

            {/* 타입별 검색 섹션 */}
            <div className="type-search-section">
                <h3>타입별 검색</h3>
                <div className="type-search-form">
                    <select
                        value={selectedUserType}
                        onChange={(e) => setSelectedUserType(e.target.value)}
                    >
                        <option value="NORMAL">일반 사용자</option>
                        <option value="PREMIUM">프리미엄 사용자</option>
                        <option value="ADMIN">관리자</option>
                        <option value="GUEST">게스트</option>
                    </select>
                    <button onClick={handleTypeSearch} disabled={loading}>
                        {loading ? '조회 중...' : '타입별 조회'}
                    </button>
                </div>
            </div>

            {/* 통계 정보 */}
            {Object.keys(statistics).length > 0 && (
                <div className="statistics-section">
                    <h3>검색 통계</h3>
                    <div className="statistics-grid">
                        {statistics.totalCount !== undefined && (
                            <div className="stat-item">
                                <span className="stat-label">전체 수:</span>
                                <span className="stat-value">{statistics.totalCount}</span>
                            </div>
                        )}
                        {statistics.activeCount !== undefined && (
                            <div className="stat-item">
                                <span className="stat-label">활성 사용자:</span>
                                <span className="stat-value">{statistics.activeCount}</span>
                            </div>
                        )}
                        {statistics.inactiveCount !== undefined && (
                            <div className="stat-item">
                                <span className="stat-label">비활성 사용자:</span>
                                <span className="stat-value">{statistics.inactiveCount}</span>
                            </div>
                        )}
                        {statistics.averageAge !== undefined && (
                            <div className="stat-item">
                                <span className="stat-label">평균 나이:</span>
                                <span className="stat-value">{statistics.averageAge}</span>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* 사용자 목록 */}
            <div className="users-list-section">
                <h3>검색 결과 ({users.length}명)</h3>
                {loading ? (
                    <div className="loading">데이터를 불러오는 중...</div>
                ) : (
                    <div className="users-grid">
                        {users.map((user, index) => (
                            <div key={user.id || index} className="user-card">
                                <h4>{user.name || '이름 없음'}</h4>
                                <p>이메일: {user.email || '이메일 없음'}</p>
                                <p>상태: {user.status || '상태 없음'}</p>
                                {user.age && <p>나이: {user.age}세</p>}
                                {user.userType && <p>타입: {user.userType}</p>}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* 페이징 */}
            <div className="pagination-section">
                <button 
                    onClick={() => handlePageChange(Math.max(0, searchParams.page - 1))}
                    disabled={searchParams.page === 0 || loading}
                >
                    이전 페이지
                </button>
                <span className="page-info">
                    페이지 {searchParams.page + 1}
                </span>
                <button 
                    onClick={() => handlePageChange(searchParams.page + 1)}
                    disabled={users.length < searchParams.size || loading}
                >
                    다음 페이지
                </button>
            </div>
        </div>
    );
};

export default UserSearchDashboard;
