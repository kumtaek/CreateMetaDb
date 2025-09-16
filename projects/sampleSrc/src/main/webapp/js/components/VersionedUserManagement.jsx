import React, { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * 버전별 사용자 관리 컴포넌트
 * FRONTEND_API: VersionedUserManagement -> API_ENTRY: VersionedController의 여러 API들
 */
const VersionedUserManagement = () => {
    const [users, setUsers] = useState([]);
    const [products, setProducts] = useState([]);
    const [orders, setOrders] = useState([]);
    const [version, setVersion] = useState('v1');

    /**
     * 사용자 목록 조회 - 버전별 API 호출
     * FRONTEND_API: GET /api/users -> API_ENTRY: GET /api/v1/users 또는 GET /api/v2/users
     */
    const fetchUsers = async () => {
        try {
            // 프론트엔드에서는 단순한 경로 사용
            const response = await axios.get('/api/users', {
                params: { version: version }
            });
            setUsers(response.data);
        } catch (error) {
            console.error('사용자 조회 실패:', error);
        }
    };

    /**
     * 제품 목록 조회 - 버전별 API 호출
     * FRONTEND_API: GET /api/products -> API_ENTRY: GET /api/v1/products 또는 GET /api/v2/products
     */
    const fetchProducts = async () => {
        try {
            // 프론트엔드에서는 단순한 경로 사용
            const response = await axios.get('/api/products', {
                params: { 
                    version: version,
                    page: 0,
                    size: 10
                }
            });
            setProducts(response.data);
        } catch (error) {
            console.error('제품 조회 실패:', error);
        }
    };

    /**
     * 주문 목록 조회 - 버전별 API 호출
     * FRONTEND_API: GET /api/orders -> API_ENTRY: GET /api/v1/orders 또는 GET /api/v2/orders
     */
    const fetchOrders = async () => {
        try {
            // 프론트엔드에서는 단순한 경로 사용
            const response = await axios.get('/api/orders', {
                params: { 
                    version: version,
                    status: 'ACTIVE',
                    dateFrom: '2024-01-01',
                    dateTo: '2024-12-31'
                }
            });
            setOrders(response.data);
        } catch (error) {
            console.error('주문 조회 실패:', error);
        }
    };

    useEffect(() => {
        fetchUsers();
        fetchProducts();
        fetchOrders();
    }, [version]);

    return (
        <div className="versioned-user-management">
            <h2>버전별 사용자 관리</h2>
            
            <div className="version-selector">
                <label>API 버전:</label>
                <select value={version} onChange={(e) => setVersion(e.target.value)}>
                    <option value="v1">v1 (기본 버전)</option>
                    <option value="v2">v2 (개선된 버전)</option>
                </select>
            </div>

            <div className="data-sections">
                <div className="users-section">
                    <h3>사용자 목록</h3>
                    <button onClick={fetchUsers}>사용자 새로고침</button>
                    <ul>
                        {users.map(user => (
                            <li key={user.id}>{user.name} - {user.email}</li>
                        ))}
                    </ul>
                </div>

                <div className="products-section">
                    <h3>제품 목록</h3>
                    <button onClick={fetchProducts}>제품 새로고침</button>
                    <ul>
                        {products.map(product => (
                            <li key={product.id}>{product.name} - {product.price}</li>
                        ))}
                    </ul>
                </div>

                <div className="orders-section">
                    <h3>주문 목록</h3>
                    <button onClick={fetchOrders}>주문 새로고침</button>
                    <ul>
                        {orders.map(order => (
                            <li key={order.id}>{order.id} - {order.status}</li>
                        ))}
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default VersionedUserManagement;
