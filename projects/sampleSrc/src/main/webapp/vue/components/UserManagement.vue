<template>
  <div class="user-management">
    <h1>User Management System</h1>
    
    <!-- User Management Section -->
    <div class="user-section">
      <h2>User Management</h2>
      <div class="controls">
        <button @click="loadUsers" :disabled="loading">Load Users</button>
        <button @click="loadUserStatistics" :disabled="loading">Load Statistics</button>
        <button @click="deleteInactiveUsers" :disabled="loading">Delete Inactive Users</button>
        <button @click="insertUserOrderStatistics" :disabled="loading">Insert Order Statistics</button>
      </div>
      
      <div class="user-list">
        <h3>Users</h3>
        <div v-if="loading">Loading...</div>
        <table v-else>
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
            <tr v-for="user in users" :key="user.userId">
              <td>{{ user.userId }}</td>
              <td>{{ user.username }}</td>
              <td>{{ user.email }}</td>
              <td>{{ user.status }}</td>
              <td>
                <button @click="updateUserStatus(user.userId, 'ACTIVE')">Activate</button>
                <button @click="updateUserStatus(user.userId, 'INACTIVE')">Deactivate</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Order Management Section -->
    <div class="order-section">
      <h2>Order Management</h2>
      <div class="controls">
        <button @click="loadOrders" :disabled="loading">Load Orders</button>
        <button @click="loadOrderStatistics" :disabled="loading">Load Order Statistics</button>
      </div>
      
      <div class="order-list">
        <h3>Orders</h3>
        <div v-if="loading">Loading...</div>
        <table v-else>
          <thead>
            <tr>
              <th>Order ID</th>
              <th>User ID</th>
              <th>Total Amount</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in orders" :key="order.orderId">
              <td>{{ order.orderId }}</td>
              <td>{{ order.userId }}</td>
              <td>{{ order.totalAmount }}</td>
              <td>{{ order.orderStatus }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Product Management Section -->
    <div class="product-section">
      <h2>Product Management</h2>
      <div class="controls">
        <button @click="loadProducts" :disabled="loading">Load Products</button>
        <button @click="loadProductRecommendations" :disabled="loading">Load Recommendations</button>
        <button @click="updateProductPrices" :disabled="loading">Update Prices</button>
        <button @click="insertProductRecommendations" :disabled="loading">Insert Recommendations</button>
      </div>
      
      <div class="product-list">
        <h3>Products</h3>
        <div v-if="loading">Loading...</div>
        <table v-else>
          <thead>
            <tr>
              <th>Product ID</th>
              <th>Name</th>
              <th>Price</th>
              <th>Stock</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="product in products" :key="product.productId">
              <td>{{ product.productId }}</td>
              <td>{{ product.productName }}</td>
              <td>{{ product.price }}</td>
              <td>{{ product.stockQuantity }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Statistics Section -->
    <div class="statistics-section">
      <h2>Statistics</h2>
      <div class="stats">
        <div v-for="(value, key) in statistics" :key="key" class="stat-item">
          <span class="stat-label">{{ key }}:</span>
          <span class="stat-value">{{ value }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'UserManagement',
  data() {
    return {
      users: [],
      orders: [],
      products: [],
      statistics: {},
      loading: false
    };
  },
  mounted() {
    this.loadUsers();
    this.loadUserStatistics();
  },
  methods: {
    // Load all users
    async loadUsers() {
      this.loading = true;
      try {
        const response = await axios.get('/api/users');
        this.users = response.data;
      } catch (error) {
        console.error('Error loading users:', error);
      } finally {
        this.loading = false;
      }
    },

    // Search users by criteria
    async searchUsers(keyword, type) {
      this.loading = true;
      try {
        const response = await axios.get('/api/users/search', {
          params: { keyword, type }
        });
        this.users = response.data;
      } catch (error) {
        console.error('Error searching users:', error);
      } finally {
        this.loading = false;
      }
    },

    // Load user statistics
    async loadUserStatistics() {
      this.loading = true;
      try {
        const response = await axios.get('/api/users/statistics');
        this.statistics = response.data;
      } catch (error) {
        console.error('Error loading statistics:', error);
      } finally {
        this.loading = false;
      }
    },

    // Load orders
    async loadOrders() {
      this.loading = true;
      try {
        const response = await axios.get('/api/orders');
        this.orders = response.data;
      } catch (error) {
        console.error('Error loading orders:', error);
      } finally {
        this.loading = false;
      }
    },

    // Load order statistics
    async loadOrderStatistics() {
      this.loading = true;
      try {
        const response = await axios.get('/api/orders/statistics');
        this.statistics = response.data;
      } catch (error) {
        console.error('Error loading order statistics:', error);
      } finally {
        this.loading = false;
      }
    },

    // Load products
    async loadProducts() {
      this.loading = true;
      try {
        const response = await axios.get('/api/products');
        this.products = response.data;
      } catch (error) {
        console.error('Error loading products:', error);
      } finally {
        this.loading = false;
      }
    },

    // Load product recommendations
    async loadProductRecommendations() {
      this.loading = true;
      try {
        const response = await axios.get('/api/products/recommendations');
        this.products = response.data;
      } catch (error) {
        console.error('Error loading recommendations:', error);
      } finally {
        this.loading = false;
      }
    },

    // Update user status
    async updateUserStatus(userId, newStatus) {
      this.loading = true;
      try {
        await axios.put(`/api/users/${userId}/status`, { status: newStatus });
        this.loadUsers(); // Refresh user list
      } catch (error) {
        console.error('Error updating user status:', error);
      } finally {
        this.loading = false;
      }
    },

    // Delete inactive users
    async deleteInactiveUsers() {
      this.loading = true;
      try {
        await axios.delete('/api/users/inactive');
        this.loadUsers(); // Refresh user list
      } catch (error) {
        console.error('Error deleting inactive users:', error);
      } finally {
        this.loading = false;
      }
    },

    // Update product prices
    async updateProductPrices() {
      this.loading = true;
      try {
        await axios.put('/api/products/prices/update');
        this.loadProducts(); // Refresh product list
      } catch (error) {
        console.error('Error updating product prices:', error);
      } finally {
        this.loading = false;
      }
    },

    // Insert user order statistics
    async insertUserOrderStatistics() {
      this.loading = true;
      try {
        await axios.post('/api/users/order-statistics');
        this.loadUserStatistics(); // Refresh statistics
      } catch (error) {
        console.error('Error inserting user order statistics:', error);
      } finally {
        this.loading = false;
      }
    },

    // Insert product recommendations
    async insertProductRecommendations() {
      this.loading = true;
      try {
        await axios.post('/api/products/recommendations/insert');
        this.loadProductRecommendations(); // Refresh recommendations
      } catch (error) {
        console.error('Error inserting product recommendations:', error);
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.controls {
  margin-bottom: 20px;
}

.controls button {
  margin-right: 10px;
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.controls button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

th {
  background-color: #f2f2f2;
}

.stats {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.stat-label {
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 1.2em;
  color: #007bff;
}
</style>
