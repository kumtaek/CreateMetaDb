/**
 * TypeScript React 상품 대시보드 컴포넌트
 * 1차 개발 범위: TypeScript JSX 파일 분석 테스트케이스
 * 
 * 백엔드 호출 패턴:
 * - React Hooks를 통한 API 호출
 * - 실시간 데이터 스트리밍
 * - 타입 안전성을 갖춘 컴포넌트
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios, { AxiosResponse } from 'axios';
import { Product, ApiResponse, ProductSearchParams, apiService } from '../services/ApiService';

// 컴포넌트 Props 타입 정의
interface TypeScriptProductDashboardProps {
  initialProducts?: Product[];
  onProductSelect?: (product: Product) => void;
  onProductUpdate?: (product: Product) => void;
  refreshInterval?: number;
}

// 대시보드 State 타입 정의
interface DashboardState {
  products: Product[];
  loading: boolean;
  error: string | null;
  selectedProduct: Product | null;
  searchParams: ProductSearchParams;
  statistics: {
    totalProducts: number;
    activeProducts: number;
    outOfStockProducts: number;
    averagePrice: number;
  };
  realtimeData: any;
}

// 차트 데이터 타입 정의
interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor: string[];
  }[];
}

/**
 * TypeScript React 상품 대시보드 컴포넌트
 * 백엔드 API 호출을 통한 상품 관리 및 실시간 모니터링
 */
const TypeScriptProductDashboard: React.FC<TypeScriptProductDashboardProps> = ({
  initialProducts = [],
  onProductSelect,
  onProductUpdate,
  refreshInterval = 30000
}) => {
  // State 초기화
  const [state, setState] = useState<DashboardState>({
    products: initialProducts,
    loading: false,
    error: null,
    selectedProduct: null,
    searchParams: {
      page: 0,
      size: 50
    },
    statistics: {
      totalProducts: 0,
      activeProducts: 0,
      outOfStockProducts: 0,
      averagePrice: 0
    },
    realtimeData: null
  });

  // Refs
  const eventSourceRef = useRef<EventSource | null>(null);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // 상품 목록 조회
  /**
   * FRONTEND_API: GET /api/v2/products -> API_ENTRY: TypeScriptProductController.getAllProducts()
   */
  const fetchProducts = useCallback(async (params: ProductSearchParams = {}) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response: AxiosResponse<ApiResponse<Product[]>> = await axios.get('/api/v2/products', {
        params: {
          ...params,
          page: state.searchParams.page,
          size: state.searchParams.size
        }
      });

      if (response.data.success) {
        setState(prev => ({
          ...prev,
          products: response.data.data,
          loading: false
        }));
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '상품 목록 조회 실패'
      }));
    }
  }, [state.searchParams.page, state.searchParams.size]);

  // 상품 상세 조회
  /**
   * FRONTEND_API: GET /api/v2/products/{id} -> API_ENTRY: TypeScriptProductController.getProductById()
   */
  const fetchProductById = useCallback(async (productId: number) => {
    try {
      const response: AxiosResponse<ApiResponse<Product>> = await axios.get(`/api/v2/products/${productId}`);
      
      if (response.data.success) {
        setState(prev => ({ ...prev, selectedProduct: response.data.data }));
        onProductSelect?.(response.data.data);
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : '상품 조회 실패'
      }));
    }
  }, [onProductSelect]);

  // 상품 생성
  /**
   * FRONTEND_API: POST /api/v2/products -> API_ENTRY: TypeScriptProductController.createProduct()
   */
  const createProduct = useCallback(async (productData: Partial<Product>) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response: AxiosResponse<ApiResponse<Product>> = await axios.post('/api/v2/products', productData);
      
      if (response.data.success) {
        setState(prev => ({
          ...prev,
          products: [...prev.products, response.data.data],
          loading: false
        }));
        return response.data.data;
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '상품 생성 실패'
      }));
    }
  }, []);

  // 상품 수정
  /**
   * FRONTEND_API: PUT /api/v2/products/{id} -> API_ENTRY: TypeScriptProductController.updateProduct()
   */
  const updateProduct = useCallback(async (productId: number, productData: Partial<Product>) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response: AxiosResponse<ApiResponse<Product>> = await axios.put(`/api/v2/products/${productId}`, productData);
      
      if (response.data.success) {
        setState(prev => ({
          ...prev,
          products: prev.products.map(product => 
            product.productId === productId ? response.data.data : product
          ),
          selectedProduct: response.data.data,
          loading: false
        }));
        onProductUpdate?.(response.data.data);
        return response.data.data;
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '상품 수정 실패'
      }));
    }
  }, [onProductUpdate]);

  // 상품 삭제
  /**
   * FRONTEND_API: DELETE /api/v2/products/{id} -> API_ENTRY: TypeScriptProductController.deleteProduct()
   */
  const deleteProduct = useCallback(async (productId: number) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response: AxiosResponse<ApiResponse<void>> = await axios.delete(`/api/v2/products/${productId}`);
      
      if (response.data.success) {
        setState(prev => ({
          ...prev,
          products: prev.products.filter(product => product.productId !== productId),
          selectedProduct: prev.selectedProduct?.productId === productId ? null : prev.selectedProduct,
          loading: false
        }));
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '상품 삭제 실패'
      }));
    }
  }, []);

  // 상품 통계 조회
  /**
   * FRONTEND_API: GET /api/v2/analytics/product-stats -> API_ENTRY: TypeScriptAnalyticsController.getProductStatistics()
   */
  const fetchProductStatistics = useCallback(async () => {
    try {
      const response: AxiosResponse<ApiResponse<any>> = await axios.get('/api/v2/analytics/product-stats');
      
      if (response.data.success) {
        setState(prev => ({
          ...prev,
          statistics: {
            totalProducts: response.data.data.totalProducts || 0,
            activeProducts: response.data.data.activeProducts || 0,
            outOfStockProducts: response.data.data.outOfStockProducts || 0,
            averagePrice: response.data.data.averagePrice || 0
          }
        }));
        return response.data.data;
      }
    } catch (error) {
      console.error('Failed to fetch product statistics:', error);
    }
  }, []);

  // 상품 재고 업데이트
  /**
   * FRONTEND_API: PATCH /api/v2/products/{id}/stock -> API_ENTRY: TypeScriptProductController.updateStock()
   */
  const updateStock = useCallback(async (productId: number, newStock: number) => {
    try {
      const response: AxiosResponse<ApiResponse<Product>> = await axios.patch(`/api/v2/products/${productId}/stock`, {
        stock: newStock
      });
      
      if (response.data.success) {
        setState(prev => ({
          ...prev,
          products: prev.products.map(product => 
            product.productId === productId ? response.data.data : product
          ),
          selectedProduct: prev.selectedProduct?.productId === productId ? response.data.data : prev.selectedProduct
        }));
        return response.data.data;
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : '재고 업데이트 실패'
      }));
    }
  }, []);

  // 실시간 데이터 스트리밍
  /**
   * FRONTEND_API: GET /api/v2/stream/realtime -> API_ENTRY: TypeScriptStreamController.getRealtimeData()
   */
  const startRealtimeStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      eventSourceRef.current = apiService.getRealtimeData();
      
      eventSourceRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setState(prev => ({ ...prev, realtimeData: data }));
      };

      eventSourceRef.current.onerror = (error) => {
        console.error('Realtime stream error:', error);
      };
    } catch (error) {
      console.error('Failed to start realtime stream:', error);
    }
  }, []);

  // 상품 검색
  /**
   * FRONTEND_API: GET /api/v2/products/search -> API_ENTRY: TypeScriptProductController.searchProducts()
   */
  const searchProducts = useCallback(async (searchParams: ProductSearchParams) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response: AxiosResponse<ApiResponse<Product[]>> = await axios.get('/api/v2/products/search', {
        params: searchParams
      });
      
      if (response.data.success) {
        setState(prev => ({
          ...prev,
          products: response.data.data,
          searchParams,
          loading: false
        }));
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '상품 검색 실패'
      }));
    }
  }, []);

  // 자동 새로고침 설정
  useEffect(() => {
    if (refreshInterval > 0) {
      refreshIntervalRef.current = setInterval(() => {
        fetchProducts();
        fetchProductStatistics();
      }, refreshInterval);
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [refreshInterval, fetchProducts, fetchProductStatistics]);

  // 실시간 스트림 시작
  useEffect(() => {
    startRealtimeStream();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [startRealtimeStream]);

  // 컴포넌트 마운트 시 초기 데이터 로드
  useEffect(() => {
    fetchProducts();
    fetchProductStatistics();
  }, [fetchProducts, fetchProductStatistics]);

  // 이벤트 핸들러들
  const handleProductSelect = useCallback((product: Product) => {
    setState(prev => ({ ...prev, selectedProduct: product }));
    onProductSelect?.(product);
  }, [onProductSelect]);

  const handleSearch = useCallback((searchParams: ProductSearchParams) => {
    searchProducts(searchParams);
  }, [searchProducts]);

  const handleStockUpdate = useCallback((productId: number, newStock: number) => {
    updateStock(productId, newStock);
  }, [updateStock]);

  return (
    <div className="typescript-product-dashboard">
      <h2>TypeScript 상품 대시보드</h2>
      
      {/* 통계 섹션 */}
      <div className="statistics-section">
        <div className="stat-card">
          <h3>총 상품 수</h3>
          <p>{state.statistics.totalProducts}</p>
        </div>
        <div className="stat-card">
          <h3>활성 상품</h3>
          <p>{state.statistics.activeProducts}</p>
        </div>
        <div className="stat-card">
          <h3>품절 상품</h3>
          <p>{state.statistics.outOfStockProducts}</p>
        </div>
        <div className="stat-card">
          <h3>평균 가격</h3>
          <p>{state.statistics.averagePrice.toLocaleString()}원</p>
        </div>
      </div>

      {/* 검색 섹션 */}
      <div className="search-section">
        <input
          type="text"
          placeholder="상품명 검색"
          onChange={(e) => handleSearch({ productName: e.target.value })}
        />
        <select
          onChange={(e) => handleSearch({ status: e.target.value })}
        >
          <option value="">전체 상태</option>
          <option value="ACTIVE">활성</option>
          <option value="INACTIVE">비활성</option>
          <option value="OUT_OF_STOCK">품절</option>
        </select>
      </div>

      {/* 상품 목록 */}
      <div className="product-list">
        {state.loading && <div>로딩 중...</div>}
        {state.error && <div className="error">오류: {state.error}</div>}
        
        {state.products.map((product) => (
          <div
            key={product.productId}
            className={`product-item ${state.selectedProduct?.productId === product.productId ? 'selected' : ''}`}
            onClick={() => handleProductSelect(product)}
          >
            <h3>{product.productName}</h3>
            <p>코드: {product.productCode}</p>
            <p>가격: {product.price.toLocaleString()}원</p>
            <p>재고: {product.stock}</p>
            <p>상태: {product.status}</p>
            <p>카테고리: {product.categoryId}</p>
            
            <div className="product-actions">
              <input
                type="number"
                placeholder="재고 수량"
                onChange={(e) => handleStockUpdate(product.productId, parseInt(e.target.value))}
              />
              <button onClick={() => deleteProduct(product.productId)}>
                삭제
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* 실시간 데이터 */}
      {state.realtimeData && (
        <div className="realtime-section">
          <h3>실시간 데이터</h3>
          <pre>{JSON.stringify(state.realtimeData, null, 2)}</pre>
        </div>
      )}

      {/* 선택된 상품 상세 */}
      {state.selectedProduct && (
        <div className="product-detail">
          <h3>선택된 상품 상세</h3>
          <pre>{JSON.stringify(state.selectedProduct, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default TypeScriptProductDashboard;
