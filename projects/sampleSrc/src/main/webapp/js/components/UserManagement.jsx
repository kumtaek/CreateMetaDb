import React, { useState, useEffect } from 'react';
import axios from 'axios';

const UserManagement = () => {
    const [users, setUsers] = useState([]);
    const [orders, setOrders] = useState([]);
    const [products, setProducts] = useState([]);
    const [statistics, setStatistics] = useState({});
    const [loading, setLoading] = useState(false);

    // Load all users
    const loadUsers = async () => {
        setLoading(true);
        try {
            const response = await axios.get('/api/users');
            setUsers(response.data);
        } catch (error) {
            console.error('Error loading users:', error);
        } finally {
            setLoading(false);
        }
    };

    // Search users by criteria
    const searchUsers = async (keyword, type) => {
        setLoading(true);
        try {
            const response = await axios.get('/api/users/search', {
                params: { keyword, type }
            });
            setUsers(response.data);
        } catch (error) {
            console.error('Error searching users:', error);
        } finally {
            setLoading(false);
        }
    };

    // Load user statistics
    const loadUserStatistics = async () => {
        setLoading(true);
        try {
            const response = await axios.get('/api/users/statistics');
            setStatistics(response.data);
        } catch (error) {
            console.error('Error loading statistics:', error);
        } finally {
            setLoading(false);
        }
    };

    // Load orders
    const loadOrders = async () => {
        setLoading(true);
        try {
            const response = await axios.get('/api/orders');
            setOrders(response.data);
        } catch (error) {
            console.error('Error loading orders:', error);
        } finally {
            setLoading(false);
        }
    };

    // Load order statistics
    const loadOrderStatistics = async () => {
        setLoading(true);
        try {
            const response = await axios.get('/api/orders/statistics');
            setStatistics(response.data);
        } catch (error) {
            console.error('Error loading order statistics:', error);
        } finally {
            setLoading(false);
        }
    };

    // Load products
    const loadProducts = async () => {
        setLoading(true);
        try {
            const response = await axios.get('/api/products');
            setProducts(response.data);
        } catch (error) {
            console.error('Error loading products:', error);
        } finally {
            setLoading(false);
        }
    };

    // Load product recommendations
    const loadProductRecommendations = async () => {
        setLoading(true);
        try {
            const response = await axios.get('/api/products/recommendations');
            setProducts(response.data);
        } catch (error) {
            console.error('Error loading recommendations:', error);
        } finally {
            setLoading(false);
        }
    };

    // Update user status
    const updateUserStatus = async (userId, newStatus) => {
        setLoading(true);
        try {
            await axios.put(`/api/users/${userId}/status`, { status: newStatus });
            loadUsers(); // Refresh user list
        } catch (error) {
            console.error('Error updating user status:', error);
        } finally {
            setLoading(false);
        }
    };

    // Delete inactive users
    const deleteInactiveUsers = async () => {
        setLoading(true);
        try {
            await axios.delete('/api/users/inactive');
            loadUsers(); // Refresh user list
        } catch (error) {
            console.error('Error deleting inactive users:', error);
        } finally {
            setLoading(false);
        }
    };

    // Update product prices
    const updateProductPrices = async () => {
        setLoading(true);
        try {
            await axios.put('/api/products/prices/update');
            loadProducts(); // Refresh product list
        } catch (error) {
            console.error('Error updating product prices:', error);
        } finally {
            setLoading(false);
        }
    };

    // Insert user order statistics
    const insertUserOrderStatistics = async () => {
        setLoading(true);
        try {
            await axios.post('/api/users/order-statistics');
            loadUserStatistics(); // Refresh statistics
        } catch (error) {
            console.error('Error inserting user order statistics:', error);
        } finally {
            setLoading(false);
        }
    };

    // Insert product recommendations
    const insertProductRecommendations = async () => {
        setLoading(true);
        try {
            await axios.post('/api/products/recommendations/insert');
            loadProductRecommendations(); // Refresh recommendations
        } catch (error) {
            console.error('Error inserting product recommendations:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadUsers();
        loadUserStatistics();
    }, []);

    return (
        <div className="user-management">
            <h1>User Management System</h1>
            
            {/* User Management Section */}
            <div className="user-section">
                <h2>User Management</h2>
                <div className="controls">
                    <button onClick={loadUsers} disabled={loading}>Load Users</button>
                    <button onClick={loadUserStatistics} disabled={loading}>Load Statistics</button>
                    <button onClick={deleteInactiveUsers} disabled={loading}>Delete Inactive Users</button>
                    <button onClick={insertUserOrderStatistics} disabled={loading}>Insert Order Statistics</button>
                </div>
                
                <div className="user-list">
                    <h3>Users</h3>
                    {loading ? (
                        <p>Loading...</p>
                    ) : (
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Username</th>
                                    <th>Email</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users.map(user => (
                                    <tr key={user.userId}>
                                        <td>{user.userId}</td>
                                        <td>{user.username}</td>
                                        <td>{user.email}</td>
                                        <td>{user.status}</td>
                                        <td>
                                            <button onClick={() => updateUserStatus(user.userId, 'ACTIVE')}>
                                                Activate
                                            </button>
                                            <button onClick={() => updateUserStatus(user.userId, 'INACTIVE')}>
                                                Deactivate
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

            {/* Order Management Section */}
            <div className="order-section">
                <h2>Order Management</h2>
                <div className="controls">
                    <button onClick={loadOrders} disabled={loading}>Load Orders</button>
                    <button onClick={loadOrderStatistics} disabled={loading}>Load Order Statistics</button>
                </div>
                
                <div className="order-list">
                    <h3>Orders</h3>
                    {loading ? (
                        <p>Loading...</p>
                    ) : (
                        <table>
                            <thead>
                                <tr>
                                    <th>Order ID</th>
                                    <th>User ID</th>
                                    <th>Total Amount</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {orders.map(order => (
                                    <tr key={order.orderId}>
                                        <td>{order.orderId}</td>
                                        <td>{order.userId}</td>
                                        <td>{order.totalAmount}</td>
                                        <td>{order.orderStatus}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

            {/* Product Management Section */}
            <div className="product-section">
                <h2>Product Management</h2>
                <div className="controls">
                    <button onClick={loadProducts} disabled={loading}>Load Products</button>
                    <button onClick={loadProductRecommendations} disabled={loading}>Load Recommendations</button>
                    <button onClick={updateProductPrices} disabled={loading}>Update Prices</button>
                    <button onClick={insertProductRecommendations} disabled={loading}>Insert Recommendations</button>
                </div>
                
                <div className="product-list">
                    <h3>Products</h3>
                    {loading ? (
                        <p>Loading...</p>
                    ) : (
                        <table>
                            <thead>
                                <tr>
                                    <th>Product ID</th>
                                    <th>Name</th>
                                    <th>Price</th>
                                    <th>Stock</th>
                                </tr>
                            </thead>
                            <tbody>
                                {products.map(product => (
                                    <tr key={product.productId}>
                                        <td>{product.productId}</td>
                                        <td>{product.productName}</td>
                                        <td>{product.price}</td>
                                        <td>{product.stockQuantity}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

            {/* Statistics Section */}
            <div className="statistics-section">
                <h2>Statistics</h2>
                <div className="stats">
                    {Object.keys(statistics).map(key => (
                        <div key={key} className="stat-item">
                            <span className="stat-label">{key}:</span>
                            <span className="stat-value">{statistics[key]}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default UserManagement;
