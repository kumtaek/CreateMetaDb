import React, { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * 프록시 서비스 관리 컴포넌트
 * FRONTEND_API: ProxyServiceManagement -> API_ENTRY: ProxyController의 여러 API들
 */
const ProxyServiceManagement = () => {
    const [users, setUsers] = useState([]);
    const [products, setProducts] = useState([]);
    const [orders, setOrders] = useState([]);
    const [paymentResult, setPaymentResult] = useState(null);

    /**
     * 사용자 조회 - 프록시 패턴
     * FRONTEND_API: GET /api/users -> API_ENTRY: GET /api/v1/users
     */
    const fetchUsers = async () => {
        try {
            // 프론트엔드에서는 단순한 경로 사용
            const response = await axios.get('/api/users');
            setUsers(response.data);
        } catch (error) {
            console.error('사용자 조회 실패:', error);
        }
    };

    /**
     * 사용자 생성 - 프록시 패턴
     * FRONTEND_API: POST /api/users -> API_ENTRY: POST /api/v1/users
     */
    const createUser = async (userData) => {
        try {
            // 프론트엔드에서는 단순한 경로 사용
            const response = await axios.post('/api/users', userData);
            console.log('사용자 생성 성공:', response.data);
            fetchUsers(); // 목록 새로고침
        } catch (error) {
            console.error('사용자 생성 실패:', error);
        }
    };

    /**
     * 제품 조회 - 게이트웨이 패턴
     * FRONTEND_API: GET /api/products -> API_ENTRY: GET /internal/product-service/products
     */
    const fetchProducts = async () => {
        try {
            // 프론트엔드에서는 단순한 경로 사용
            const response = await axios.get('/api/products');
            setProducts(response.data);
        } catch (error) {
            console.error('제품 조회 실패:', error);
        }
    };

    /**
     * 주문 조회 - 마이크로서비스 패턴
     * FRONTEND_API: GET /api/orders -> API_ENTRY: GET /internal/order-service/orders
     */
    const fetchOrders = async () => {
        try {
            // 프론트엔드에서는 단순한 경로 사용
            const response = await axios.get('/api/orders');
            setOrders(response.data);
        } catch (error) {
            console.error('주문 조회 실패:', error);
        }
    };

    /**
     * 결제 처리 - 외부 서비스 연동
     * FRONTEND_API: POST /api/payment -> API_ENTRY: POST /external/payment-gateway/process
     */
    const processPayment = async (paymentData) => {
        try {
            // 프론트엔드에서는 단순한 경로 사용
            const response = await axios.post('/api/payment', paymentData);
            setPaymentResult(response.data);
        } catch (error) {
            console.error('결제 처리 실패:', error);
        }
    };

    useEffect(() => {
        fetchUsers();
        fetchProducts();
        fetchOrders();
    }, []);

    const handleCreateUser = () => {
        const userData = {
            name: '새 사용자',
            email: 'newuser@example.com',
            status: 'ACTIVE'
        };
        createUser(userData);
    };

    const handlePayment = () => {
        const paymentData = {
            amount: 10000,
            currency: 'KRW',
            method: 'CARD',
            orderId: 'ORDER-123'
        };
        processPayment(paymentData);
    };

    return (
        <div className="proxy-service-management">
            <h2>프록시 서비스 관리</h2>
            
            <div className="service-sections">
                <div className="users-section">
                    <h3>사용자 관리 (프록시 패턴)</h3>
                    <button onClick={fetchUsers}>사용자 조회</button>
                    <button onClick={handleCreateUser}>사용자 생성</button>
                    <ul>
                        {users.map(user => (
                            <li key={user.id}>{user.name} - {user.email}</li>
                        ))}
                    </ul>
                </div>

                <div className="products-section">
                    <h3>제품 관리 (게이트웨이 패턴)</h3>
                    <button onClick={fetchProducts}>제품 조회</button>
                    <ul>
                        {products.map(product => (
                            <li key={product.id}>{product.name} - {product.price}</li>
                        ))}
                    </ul>
                </div>

                <div className="orders-section">
                    <h3>주문 관리 (마이크로서비스 패턴)</h3>
                    <button onClick={fetchOrders}>주문 조회</button>
                    <ul>
                        {orders.map(order => (
                            <li key={order.id}>{order.id} - {order.status}</li>
                        ))}
                    </ul>
                </div>

                <div className="payment-section">
                    <h3>결제 처리 (외부 서비스 연동)</h3>
                    <button onClick={handlePayment}>결제 처리</button>
                    {paymentResult && (
                        <div className="payment-result">
                            <p>결제 결과: {paymentResult.status}</p>
                            <p>거래 ID: {paymentResult.transactionId}</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ProxyServiceManagement;
