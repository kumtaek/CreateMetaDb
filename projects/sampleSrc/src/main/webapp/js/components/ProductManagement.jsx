import React, { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * 상품 관리 컴포넌트
 * FRONTEND_API: ProductManagement -> API_ENTRY: ProductController의 여러 상품 관리 API들
 */
const ProductManagement = () => {
    const [products, setProducts] = useState([]);
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [updateResult, setUpdateResult] = useState(null);
    
    // 기본 검색 파라미터
    const [searchParams, setSearchParams] = useState({
        name: '',
        category: '',
        status: ''
    });
    
    // 고급 검색 파라미터
    const [advancedSearch, setAdvancedSearch] = useState({
        categoryId: '',
        minPrice: '',
        maxPrice: '',
        minStock: '',
        maxStock: ''
    });
    
    // 재고 업데이트 파라미터
    const [stockUpdate, setStockUpdate] = useState({
        productId: '',
        quantity: ''
    });
    
    const [selectedCategoryId, setSelectedCategoryId] = useState('');

    /**
     * 상품 목록 조회
     * FRONTEND_API: GET /product/list -> API_ENTRY: ProductController.getProductList()
     */
    const fetchProductList = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const params = new URLSearchParams();
            if (searchParams.name) params.append('name', searchParams.name);
            if (searchParams.category) params.append('category', searchParams.category);
            if (searchParams.status) params.append('status', searchParams.status);
            
            const response = await axios.get(`/product/list?${params.toString()}`);
            
            // Spring MVC에서 Model 데이터를 JSON으로 받는다고 가정
            if (response.data.products) {
                setProducts(response.data.products);
            } else if (Array.isArray(response.data)) {
                setProducts(response.data);
            }
        } catch (error) {
            setError('상품 목록 조회 중 오류가 발생했습니다: ' + error.message);
            console.error('상품 목록 조회 실패:', error);
        } finally {
            setLoading(false);
        }
    };

    /**
     * 고급 상품 검색
     * FRONTEND_API: POST /product/search -> API_ENTRY: ProductController.searchProducts()
     */
    const executeAdvancedSearch = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const searchData = new FormData();
            
            // 고급 검색 파라미터 추가
            if (advancedSearch.categoryId) searchData.append('categoryId', advancedSearch.categoryId);
            if (advancedSearch.minPrice) searchData.append('minPrice', advancedSearch.minPrice);
            if (advancedSearch.maxPrice) searchData.append('maxPrice', advancedSearch.maxPrice);
            if (advancedSearch.minStock) searchData.append('minStock', advancedSearch.minStock);
            if (advancedSearch.maxStock) searchData.append('maxStock', advancedSearch.maxStock);
            
            const response = await axios.post('/product/search', searchData, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });
            
            if (response.data.products) {
                setProducts(response.data.products);
            } else if (Array.isArray(response.data)) {
                setProducts(response.data);
            }
        } catch (error) {
            setError('고급 검색 중 오류가 발생했습니다: ' + error.message);
            console.error('고급 검색 실패:', error);
        } finally {
            setLoading(false);
        }
    };

    /**
     * 카테고리별 상품 조회
     * FRONTEND_API: GET /product/category/{categoryId} -> API_ENTRY: ProductController.getProductsByCategory()
     */
    const fetchProductsByCategory = async (categoryId) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await axios.get(`/product/category/${categoryId}`);
            
            if (response.data.products) {
                setProducts(response.data.products);
            } else if (Array.isArray(response.data)) {
                setProducts(response.data);
            }
        } catch (error) {
            setError(`카테고리별 상품 조회 중 오류가 발생했습니다: ${error.message}`);
            console.error('카테고리별 상품 조회 실패:', error);
        } finally {
            setLoading(false);
        }
    };

    /**
     * 상품 재고 업데이트
     * FRONTEND_API: POST /product/updateStock -> API_ENTRY: ProductController.updateProductStock()
     */
    const updateProductStock = async () => {
        if (!stockUpdate.productId || !stockUpdate.quantity) {
            setError('상품 ID와 수량을 모두 입력해주세요.');
            return;
        }
        
        setLoading(true);
        setError(null);
        setUpdateResult(null);
        
        try {
            const updateData = new FormData();
            updateData.append('productId', stockUpdate.productId);
            updateData.append('quantity', stockUpdate.quantity);
            
            const response = await axios.post('/product/updateStock', updateData, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });
            
            if (response.data.result !== undefined) {
                setUpdateResult({
                    success: response.data.result > 0,
                    message: response.data.result > 0 
                        ? `상품 ${stockUpdate.productId}의 재고가 성공적으로 업데이트되었습니다.`
                        : '재고 업데이트에 실패했습니다.',
                    productId: stockUpdate.productId,
                    result: response.data.result
                });
                
                // 성공시 상품 목록 새로고침
                if (response.data.result > 0) {
                    fetchProductList();
                }
            }
        } catch (error) {
            setError('재고 업데이트 중 오류가 발생했습니다: ' + error.message);
            console.error('재고 업데이트 실패:', error);
        } finally {
            setLoading(false);
        }
    };

    // 컴포넌트 마운트 시 기본 데이터 로드
    useEffect(() => {
        fetchProductList();
        // 카테고리 목록도 초기화 (실제로는 별도 API에서 가져와야 함)
        setCategories([
            { id: 'ELECTRONICS', name: '전자제품' },
            { id: 'CLOTHING', name: '의류' },
            { id: 'BOOKS', name: '도서' },
            { id: 'HOME', name: '생활용품' },
            { id: 'SPORTS', name: '스포츠' }
        ]);
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

    // 재고 업데이트 파라미터 변경 핸들러
    const handleStockUpdateChange = (field, value) => {
        setStockUpdate(prev => ({
            ...prev,
            [field]: value
        }));
    };

    // 기본 검색 실행
    const handleBasicSearch = () => {
        fetchProductList();
    };

    // 카테고리별 검색 실행
    const handleCategorySearch = () => {
        if (selectedCategoryId) {
            fetchProductsByCategory(selectedCategoryId);
        }
    };

    // 검색 초기화
    const resetSearch = () => {
        setSearchParams({
            name: '',
            category: '',
            status: ''
        });
        setAdvancedSearch({
            categoryId: '',
            minPrice: '',
            maxPrice: '',
            minStock: '',
            maxStock: ''
        });
        setError(null);
        setUpdateResult(null);
        fetchProductList();
    };

    return (
        <div className="product-management">
            <h2>상품 관리 시스템</h2>
            
            {error && (
                <div className="error-message" style={{color: 'red', marginBottom: '10px'}}>
                    {error}
                </div>
            )}
            
            {updateResult && (
                <div className={`update-result ${updateResult.success ? 'success' : 'failure'}`}
                     style={{color: updateResult.success ? 'green' : 'red', marginBottom: '10px'}}>
                    {updateResult.message}
                </div>
            )}
            
            {/* 기본 검색 섹션 */}
            <div className="basic-search-section">
                <h3>기본 상품 검색</h3>
                <div className="search-form">
                    <input
                        type="text"
                        placeholder="상품명"
                        value={searchParams.name}
                        onChange={(e) => handleSearchParamChange('name', e.target.value)}
                    />
                    <select
                        value={searchParams.category}
                        onChange={(e) => handleSearchParamChange('category', e.target.value)}
                    >
                        <option value="">전체 카테고리</option>
                        {categories.map(category => (
                            <option key={category.id} value={category.id}>
                                {category.name}
                            </option>
                        ))}
                    </select>
                    <select
                        value={searchParams.status}
                        onChange={(e) => handleSearchParamChange('status', e.target.value)}
                    >
                        <option value="">전체 상태</option>
                        <option value="ACTIVE">판매중</option>
                        <option value="INACTIVE">판매중지</option>
                        <option value="OUT_OF_STOCK">품절</option>
                    </select>
                    <button onClick={handleBasicSearch} disabled={loading}>
                        {loading ? '검색 중...' : '기본 검색'}
                    </button>
                    <button onClick={resetSearch} disabled={loading}>
                        초기화
                    </button>
                </div>
            </div>

            {/* 고급 검색 섹션 */}
            <div className="advanced-search-section">
                <h3>고급 상품 검색</h3>
                <div className="advanced-search-form">
                    <select
                        value={advancedSearch.categoryId}
                        onChange={(e) => handleAdvancedSearchChange('categoryId', e.target.value)}
                    >
                        <option value="">전체 카테고리</option>
                        {categories.map(category => (
                            <option key={category.id} value={category.id}>
                                {category.name}
                            </option>
                        ))}
                    </select>
                    <input
                        type="number"
                        placeholder="최소 가격"
                        value={advancedSearch.minPrice}
                        onChange={(e) => handleAdvancedSearchChange('minPrice', e.target.value)}
                        min="0"
                    />
                    <input
                        type="number"
                        placeholder="최대 가격"
                        value={advancedSearch.maxPrice}
                        onChange={(e) => handleAdvancedSearchChange('maxPrice', e.target.value)}
                        min="0"
                    />
                    <input
                        type="number"
                        placeholder="최소 재고"
                        value={advancedSearch.minStock}
                        onChange={(e) => handleAdvancedSearchChange('minStock', e.target.value)}
                        min="0"
                    />
                    <input
                        type="number"
                        placeholder="최대 재고"
                        value={advancedSearch.maxStock}
                        onChange={(e) => handleAdvancedSearchChange('maxStock', e.target.value)}
                        min="0"
                    />
                    <button onClick={executeAdvancedSearch} disabled={loading}>
                        {loading ? '검색 중...' : '고급 검색'}
                    </button>
                </div>
            </div>

            {/* 카테고리별 검색 섹션 */}
            <div className="category-search-section">
                <h3>카테고리별 상품 조회</h3>
                <div className="category-search-form">
                    <select
                        value={selectedCategoryId}
                        onChange={(e) => setSelectedCategoryId(e.target.value)}
                    >
                        <option value="">카테고리 선택</option>
                        {categories.map(category => (
                            <option key={category.id} value={category.id}>
                                {category.name}
                            </option>
                        ))}
                    </select>
                    <button onClick={handleCategorySearch} disabled={loading || !selectedCategoryId}>
                        {loading ? '조회 중...' : '카테고리별 조회'}
                    </button>
                </div>
            </div>

            {/* 재고 업데이트 섹션 */}
            <div className="stock-update-section">
                <h3>상품 재고 업데이트</h3>
                <div className="stock-update-form">
                    <input
                        type="text"
                        placeholder="상품 ID"
                        value={stockUpdate.productId}
                        onChange={(e) => handleStockUpdateChange('productId', e.target.value)}
                    />
                    <input
                        type="number"
                        placeholder="수량"
                        value={stockUpdate.quantity}
                        onChange={(e) => handleStockUpdateChange('quantity', e.target.value)}
                    />
                    <button onClick={updateProductStock} disabled={loading || !stockUpdate.productId || !stockUpdate.quantity}>
                        {loading ? '업데이트 중...' : '재고 업데이트'}
                    </button>
                </div>
            </div>

            {/* 상품 목록 */}
            <div className="products-list-section">
                <h3>상품 목록 ({products.length}개)</h3>
                {loading ? (
                    <div className="loading">데이터를 불러오는 중...</div>
                ) : (
                    <div className="products-grid">
                        {products.map((product, index) => (
                            <div key={product.id || index} className="product-card">
                                <h4>{product.name || '상품명 없음'}</h4>
                                <p>카테고리: {product.category || '카테고리 없음'}</p>
                                <p>가격: {product.price ? `${product.price.toLocaleString()}원` : '가격 정보 없음'}</p>
                                <p>재고: {product.stock !== undefined ? `${product.stock}개` : '재고 정보 없음'}</p>
                                <p>상태: {product.status || '상태 없음'}</p>
                                {product.description && <p>설명: {product.description}</p>}
                            </div>
                        ))}
                        
                        {products.length === 0 && !loading && (
                            <div className="no-products">
                                검색 결과가 없습니다.
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* 통계 정보 */}
            <div className="statistics-section">
                <h3>상품 통계</h3>
                <div className="statistics-grid">
                    <div className="stat-item">
                        <span className="stat-label">전체 상품 수:</span>
                        <span className="stat-value">{products.length}</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">평균 가격:</span>
                        <span className="stat-value">
                            {products.length > 0 
                                ? `${Math.round(products.reduce((sum, p) => sum + (p.price || 0), 0) / products.length).toLocaleString()}원`
                                : '0원'
                            }
                        </span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">총 재고:</span>
                        <span className="stat-value">
                            {products.reduce((sum, p) => sum + (p.stock || 0), 0)}개
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProductManagement;
