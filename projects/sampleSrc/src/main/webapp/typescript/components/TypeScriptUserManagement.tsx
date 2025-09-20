/**
 * TypeScript React 컴포넌트
 * 1차 개발 범위: TypeScript JSX 파일 분석 테스트케이스
 * 
 * 백엔드 호출 패턴:
 * - React Hooks를 통한 API 호출
 * - 타입 안전성을 갖춘 컴포넌트
 * - axios를 통한 백엔드 API 호출
 */

import React, { useState, useEffect, useCallback } from 'react';
import axios, { AxiosResponse } from 'axios';
import { User, ApiResponse, UserSearchParams } from '../services/ApiService';

// 컴포넌트 Props 타입 정의
interface TypeScriptUserManagementProps {
  initialUsers?: User[];
  onUserSelect?: (user: User) => void;
  onUserUpdate?: (user: User) => void;
  onUserDelete?: (userId: number) => void;
}

// 컴포넌트 State 타입 정의
interface UserManagementState {
  users: User[];
  loading: boolean;
  error: string | null;
  selectedUser: User | null;
  searchParams: UserSearchParams;
  pagination: {
    page: number;
    size: number;
    total: number;
  };
}

/**
 * TypeScript React 사용자 관리 컴포넌트
 * 백엔드 API 호출을 통한 사용자 CRUD 작업
 */
const TypeScriptUserManagement: React.FC<TypeScriptUserManagementProps> = ({
  initialUsers = [],
  onUserSelect,
  onUserUpdate,
  onUserDelete
}) => {
  // State 초기화
  const [state, setState] = useState<UserManagementState>({
    users: initialUsers,
    loading: false,
    error: null,
    selectedUser: null,
    searchParams: {
      page: 0,
      size: 20
    },
    pagination: {
      page: 0,
      size: 20,
      total: 0
    }
  });

  // 사용자 목록 조회
  /**
   * FRONTEND_API: GET /api/v2/users -> API_ENTRY: TypeScriptUserController.getAllUsers()
   */
  const fetchUsers = useCallback(async (params: UserSearchParams = {}) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response: AxiosResponse<ApiResponse<User[]>> = await axios.get('/api/v2/users', {
        params: {
          ...params,
          page: state.searchParams.page,
          size: state.searchParams.size
        }
      });

      if (response.data.success) {
        setState(prev => ({
          ...prev,
          users: response.data.data,
          loading: false,
          pagination: {
            ...prev.pagination,
            total: response.data.data.length
          }
        }));
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '사용자 목록 조회 실패'
      }));
    }
  }, [state.searchParams.page, state.searchParams.size]);

  // 사용자 상세 조회
  /**
   * FRONTEND_API: GET /api/v2/users/{id} -> API_ENTRY: TypeScriptUserController.getUserById()
   */
  const fetchUserById = useCallback(async (userId: number) => {
    try {
      const response: AxiosResponse<ApiResponse<User>> = await axios.get(`/api/v2/users/${userId}`);
      
      if (response.data.success) {
        setState(prev => ({ ...prev, selectedUser: response.data.data }));
        onUserSelect?.(response.data.data);
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : '사용자 조회 실패'
      }));
    }
  }, [onUserSelect]);

  // 사용자 생성
  /**
   * FRONTEND_API: POST /api/v2/users -> API_ENTRY: TypeScriptUserController.createUser()
   */
  const createUser = useCallback(async (userData: Partial<User>) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response: AxiosResponse<ApiResponse<User>> = await axios.post('/api/v2/users', userData);
      
      if (response.data.success) {
        setState(prev => ({
          ...prev,
          users: [...prev.users, response.data.data],
          loading: false
        }));
        return response.data.data;
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '사용자 생성 실패'
      }));
    }
  }, []);

  // 사용자 수정
  /**
   * FRONTEND_API: PUT /api/v2/users/{id} -> API_ENTRY: TypeScriptUserController.updateUser()
   */
  const updateUser = useCallback(async (userId: number, userData: Partial<User>) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response: AxiosResponse<ApiResponse<User>> = await axios.put(`/api/v2/users/${userId}`, userData);
      
      if (response.data.success) {
        setState(prev => ({
          ...prev,
          users: prev.users.map(user => 
            user.id === userId ? response.data.data : user
          ),
          selectedUser: response.data.data,
          loading: false
        }));
        onUserUpdate?.(response.data.data);
        return response.data.data;
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '사용자 수정 실패'
      }));
    }
  }, [onUserUpdate]);

  // 사용자 삭제
  /**
   * FRONTEND_API: DELETE /api/v2/users/{id} -> API_ENTRY: TypeScriptUserController.deleteUser()
   */
  const deleteUser = useCallback(async (userId: number) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response: AxiosResponse<ApiResponse<void>> = await axios.delete(`/api/v2/users/${userId}`);
      
      if (response.data.success) {
        setState(prev => ({
          ...prev,
          users: prev.users.filter(user => user.id !== userId),
          selectedUser: prev.selectedUser?.id === userId ? null : prev.selectedUser,
          loading: false
        }));
        onUserDelete?.(userId);
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '사용자 삭제 실패'
      }));
    }
  }, [onUserDelete]);

  // 사용자 검색
  /**
   * FRONTEND_API: GET /api/v2/users/search -> API_ENTRY: TypeScriptUserController.searchUsers()
   */
  const searchUsers = useCallback(async (searchParams: UserSearchParams) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response: AxiosResponse<ApiResponse<User[]>> = await axios.get('/api/v2/users/search', {
        params: searchParams
      });
      
      if (response.data.success) {
        setState(prev => ({
          ...prev,
          users: response.data.data,
          searchParams,
          loading: false
        }));
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '사용자 검색 실패'
      }));
    }
  }, []);

  // 사용자 통계 조회
  /**
   * FRONTEND_API: GET /api/v2/analytics/user-stats -> API_ENTRY: TypeScriptAnalyticsController.getUserStatistics()
   */
  const fetchUserStatistics = useCallback(async () => {
    try {
      const response: AxiosResponse<ApiResponse<any>> = await axios.get('/api/v2/analytics/user-stats');
      
      if (response.data.success) {
        console.log('User Statistics:', response.data.data);
        return response.data.data;
      }
    } catch (error) {
      console.error('Failed to fetch user statistics:', error);
    }
  }, []);

  // 사용자 상태 변경
  /**
   * FRONTEND_API: PATCH /api/v2/users/{id}/status -> API_ENTRY: TypeScriptUserController.updateUserStatus()
   */
  const updateUserStatus = useCallback(async (userId: number, status: User['status']) => {
    try {
      const response: AxiosResponse<ApiResponse<User>> = await axios.patch(`/api/v2/users/${userId}/status`, {
        status
      });
      
      if (response.data.success) {
        setState(prev => ({
          ...prev,
          users: prev.users.map(user => 
            user.id === userId ? response.data.data : user
          ),
          selectedUser: prev.selectedUser?.id === userId ? response.data.data : prev.selectedUser
        }));
        return response.data.data;
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : '사용자 상태 변경 실패'
      }));
    }
  }, []);

  // 컴포넌트 마운트 시 사용자 목록 조회
  useEffect(() => {
    fetchUsers();
    fetchUserStatistics();
  }, [fetchUsers, fetchUserStatistics]);

  // 페이지네이션 핸들러
  const handlePageChange = useCallback((page: number) => {
    setState(prev => ({
      ...prev,
      searchParams: { ...prev.searchParams, page }
    }));
  }, []);

  // 검색 핸들러
  const handleSearch = useCallback((searchParams: UserSearchParams) => {
    searchUsers(searchParams);
  }, [searchUsers]);

  // 사용자 선택 핸들러
  const handleUserSelect = useCallback((user: User) => {
    setState(prev => ({ ...prev, selectedUser: user }));
    onUserSelect?.(user);
  }, [onUserSelect]);

  return (
    <div className="typescript-user-management">
      <h2>TypeScript 사용자 관리</h2>
      
      {/* 검색 섹션 */}
      <div className="search-section">
        <input
          type="text"
          placeholder="사용자명 검색"
          onChange={(e) => handleSearch({ username: e.target.value })}
        />
        <select
          onChange={(e) => handleSearch({ status: e.target.value })}
        >
          <option value="">전체 상태</option>
          <option value="ACTIVE">활성</option>
          <option value="INACTIVE">비활성</option>
          <option value="PENDING">대기</option>
        </select>
      </div>

      {/* 사용자 목록 */}
      <div className="user-list">
        {state.loading && <div>로딩 중...</div>}
        {state.error && <div className="error">오류: {state.error}</div>}
        
        {state.users.map((user) => (
          <div
            key={user.id}
            className={`user-item ${state.selectedUser?.id === user.id ? 'selected' : ''}`}
            onClick={() => handleUserSelect(user)}
          >
            <h3>{user.fullName}</h3>
            <p>사용자명: {user.username}</p>
            <p>이메일: {user.email}</p>
            <p>상태: {user.status}</p>
            <p>타입: {user.userType}</p>
            <p>생성일: {user.createdAt.toLocaleDateString()}</p>
            
            <div className="user-actions">
              <button onClick={() => updateUserStatus(user.id, 'ACTIVE')}>
                활성화
              </button>
              <button onClick={() => updateUserStatus(user.id, 'INACTIVE')}>
                비활성화
              </button>
              <button onClick={() => deleteUser(user.id)}>
                삭제
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* 페이지네이션 */}
      <div className="pagination">
        <button
          onClick={() => handlePageChange(state.pagination.page - 1)}
          disabled={state.pagination.page === 0}
        >
          이전
        </button>
        <span>페이지 {state.pagination.page + 1}</span>
        <button
          onClick={() => handlePageChange(state.pagination.page + 1)}
        >
          다음
        </button>
      </div>

      {/* 선택된 사용자 상세 */}
      {state.selectedUser && (
        <div className="user-detail">
          <h3>선택된 사용자 상세</h3>
          <pre>{JSON.stringify(state.selectedUser, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default TypeScriptUserManagement;
