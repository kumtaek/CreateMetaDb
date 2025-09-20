/**
 * TypeScript API 서비스 모듈
 * 1차 개발 범위: TypeScript 파일 분석 테스트케이스
 * 
 * 백엔드 호출 패턴:
 * - axios를 통한 REST API 호출
 * - 타입 안전성을 갖춘 API 호출
 * - 인터페이스를 통한 데이터 타입 정의
 */

import axios, { AxiosResponse } from 'axios';

// API 응답 데이터 타입 정의
export interface User {
  id: number;
  username: string;
  email: string;
  fullName: string;
  status: 'ACTIVE' | 'INACTIVE' | 'PENDING';
  userType: 'ADMIN' | 'USER' | 'GUEST';
  createdAt: Date;
  lastLoginAt?: Date;
}

export interface Product {
  productId: number;
  productCode: string;
  productName: string;
  description: string;
  price: number;
  stock: number;
  status: 'ACTIVE' | 'INACTIVE' | 'OUT_OF_STOCK';
  categoryId: number;
}

export interface Order {
  orderId: number;
  orderNumber: string;
  userId: number;
  totalAmount: number;
  status: 'PENDING' | 'CONFIRMED' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED';
  orderDate: Date;
  items: OrderItem[];
}

export interface OrderItem {
  itemId: number;
  productId: number;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
}

// API 응답 래퍼 타입
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  timestamp: string;
}

// API 요청 파라미터 타입
export interface UserSearchParams {
  username?: string;
  email?: string;
  status?: string;
  userType?: string;
  page?: number;
  size?: number;
}

export interface ProductSearchParams {
  productName?: string;
  categoryId?: number;
  minPrice?: number;
  maxPrice?: number;
  status?: string;
  page?: number;
  size?: number;
}

export interface OrderSearchParams {
  userId?: number;
  status?: string;
  startDate?: Date;
  endDate?: Date;
  minAmount?: number;
  maxAmount?: number;
  page?: number;
  size?: number;
}

/**
 * TypeScript API 서비스 클래스
 * 백엔드 API 호출을 위한 타입 안전한 서비스
 */
export class ApiService {
  private baseURL: string;
  private axiosInstance;

  constructor(baseURL: string = '/api/v2') {
    this.baseURL = baseURL;
    this.axiosInstance = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * 사용자 관련 API 호출
   * FRONTEND_API: GET /api/v2/users -> API_ENTRY: TypeScriptUserController.getAllUsers()
   */
  async getAllUsers(params?: UserSearchParams): Promise<ApiResponse<User[]>> {
    try {
      const response: AxiosResponse<ApiResponse<User[]>> = await this.axiosInstance.get('/users', {
        params
      });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch users:', error);
      throw error;
    }
  }

  /**
   * FRONTEND_API: GET /api/v2/users/{id} -> API_ENTRY: TypeScriptUserController.getUserById()
   */
  async getUserById(userId: number): Promise<ApiResponse<User>> {
    try {
      const response: AxiosResponse<ApiResponse<User>> = await this.axiosInstance.get(`/users/${userId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch user ${userId}:`, error);
      throw error;
    }
  }

  /**
   * FRONTEND_API: POST /api/v2/users -> API_ENTRY: TypeScriptUserController.createUser()
   */
  async createUser(userData: Partial<User>): Promise<ApiResponse<User>> {
    try {
      const response: AxiosResponse<ApiResponse<User>> = await this.axiosInstance.post('/users', userData);
      return response.data;
    } catch (error) {
      console.error('Failed to create user:', error);
      throw error;
    }
  }

  /**
   * FRONTEND_API: PUT /api/v2/users/{id} -> API_ENTRY: TypeScriptUserController.updateUser()
   */
  async updateUser(userId: number, userData: Partial<User>): Promise<ApiResponse<User>> {
    try {
      const response: AxiosResponse<ApiResponse<User>> = await this.axiosInstance.put(`/users/${userId}`, userData);
      return response.data;
    } catch (error) {
      console.error(`Failed to update user ${userId}:`, error);
      throw error;
    }
  }

  /**
   * FRONTEND_API: DELETE /api/v2/users/{id} -> API_ENTRY: TypeScriptUserController.deleteUser()
   */
  async deleteUser(userId: number): Promise<ApiResponse<void>> {
    try {
      const response: AxiosResponse<ApiResponse<void>> = await this.axiosInstance.delete(`/users/${userId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to delete user ${userId}:`, error);
      throw error;
    }
  }

  /**
   * 상품 관련 API 호출
   * FRONTEND_API: GET /api/v2/products -> API_ENTRY: TypeScriptProductController.getAllProducts()
   */
  async getAllProducts(params?: ProductSearchParams): Promise<ApiResponse<Product[]>> {
    try {
      const response: AxiosResponse<ApiResponse<Product[]>> = await this.axiosInstance.get('/products', {
        params
      });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch products:', error);
      throw error;
    }
  }

  /**
   * FRONTEND_API: GET /api/v2/products/{id} -> API_ENTRY: TypeScriptProductController.getProductById()
   */
  async getProductById(productId: number): Promise<ApiResponse<Product>> {
    try {
      const response: AxiosResponse<ApiResponse<Product>> = await this.axiosInstance.get(`/products/${productId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch product ${productId}:`, error);
      throw error;
    }
  }

  /**
   * FRONTEND_API: POST /api/v2/products -> API_ENTRY: TypeScriptProductController.createProduct()
   */
  async createProduct(productData: Partial<Product>): Promise<ApiResponse<Product>> {
    try {
      const response: AxiosResponse<ApiResponse<Product>> = await this.axiosInstance.post('/products', productData);
      return response.data;
    } catch (error) {
      console.error('Failed to create product:', error);
      throw error;
    }
  }

  /**
   * 주문 관련 API 호출
   * FRONTEND_API: GET /api/v2/orders -> API_ENTRY: TypeScriptOrderController.getAllOrders()
   */
  async getAllOrders(params?: OrderSearchParams): Promise<ApiResponse<Order[]>> {
    try {
      const response: AxiosResponse<ApiResponse<Order[]>> = await this.axiosInstance.get('/orders', {
        params
      });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch orders:', error);
      throw error;
    }
  }

  /**
   * FRONTEND_API: GET /api/v2/orders/{id} -> API_ENTRY: TypeScriptOrderController.getOrderById()
   */
  async getOrderById(orderId: number): Promise<ApiResponse<Order>> {
    try {
      const response: AxiosResponse<ApiResponse<Order>> = await this.axiosInstance.get(`/orders/${orderId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch order ${orderId}:`, error);
      throw error;
    }
  }

  /**
   * FRONTEND_API: POST /api/v2/orders -> API_ENTRY: TypeScriptOrderController.createOrder()
   */
  async createOrder(orderData: Partial<Order>): Promise<ApiResponse<Order>> {
    try {
      const response: AxiosResponse<ApiResponse<Order>> = await this.axiosInstance.post('/orders', orderData);
      return response.data;
    } catch (error) {
      console.error('Failed to create order:', error);
      throw error;
    }
  }

  /**
   * 통계 및 분석 API 호출
   * FRONTEND_API: GET /api/v2/analytics/user-stats -> API_ENTRY: TypeScriptAnalyticsController.getUserStatistics()
   */
  async getUserStatistics(): Promise<ApiResponse<any>> {
    try {
      const response: AxiosResponse<ApiResponse<any>> = await this.axiosInstance.get('/analytics/user-stats');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch user statistics:', error);
      throw error;
    }
  }

  /**
   * FRONTEND_API: GET /api/v2/analytics/product-stats -> API_ENTRY: TypeScriptAnalyticsController.getProductStatistics()
   */
  async getProductStatistics(): Promise<ApiResponse<any>> {
    try {
      const response: AxiosResponse<ApiResponse<any>> = await this.axiosInstance.get('/analytics/product-stats');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch product statistics:', error);
      throw error;
    }
  }

  /**
   * FRONTEND_API: GET /api/v2/analytics/order-stats -> API_ENTRY: TypeScriptAnalyticsController.getOrderStatistics()
   */
  async getOrderStatistics(): Promise<ApiResponse<any>> {
    try {
      const response: AxiosResponse<ApiResponse<any>> = await this.axiosInstance.get('/analytics/order-stats');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch order statistics:', error);
      throw error;
    }
  }

  /**
   * 실시간 데이터 스트리밍
   * FRONTEND_API: GET /api/v2/stream/realtime -> API_ENTRY: TypeScriptStreamController.getRealtimeData()
   */
  async getRealtimeData(): Promise<EventSource> {
    try {
      const eventSource = new EventSource(`${this.baseURL}/stream/realtime`);
      return eventSource;
    } catch (error) {
      console.error('Failed to connect to realtime stream:', error);
      throw error;
    }
  }
}

// 싱글톤 인스턴스 생성
export const apiService = new ApiService();

// 유틸리티 함수들
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW'
  }).format(amount);
};

export const formatDate = (date: Date): string => {
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
};

export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const generateOrderNumber = (): string => {
  const timestamp = Date.now().toString();
  const random = Math.random().toString(36).substring(2, 8).toUpperCase();
  return `ORD-${timestamp}-${random}`;
};
