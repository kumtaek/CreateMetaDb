import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

interface User {
  userId: number;
  username: string;
  email: string;
  status: string;
}

interface Order {
  orderId: number;
  userId: number;
  totalAmount: number;
  orderStatus: string;
}

interface Product {
  productId: number;
  productName: string;
  price: number;
  stockQuantity: number;
}

interface Statistics {
  [key: string]: number;
}

@Component({
  selector: 'app-user-management',
  templateUrl: './user-management.component.html',
  styleUrls: ['./user-management.component.css']
})
export class UserManagementComponent implements OnInit {
  users: User[] = [];
  orders: Order[] = [];
  products: Product[] = [];
  statistics: Statistics = {};
  loading: boolean = false;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadUsers();
    this.loadUserStatistics();
  }

  // Load all users
  loadUsers(): void {
    this.loading = true;
    this.http.get<User[]>('/api/users').subscribe({
      next: (data) => {
        this.users = data;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading users:', error);
        this.loading = false;
      }
    });
  }

  // Search users by criteria
  searchUsers(keyword: string, type: string): void {
    this.loading = true;
    this.http.get<User[]>('/api/users/search', {
      params: { keyword, type }
    }).subscribe({
      next: (data) => {
        this.users = data;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error searching users:', error);
        this.loading = false;
      }
    });
  }

  // Load user statistics
  loadUserStatistics(): void {
    this.loading = true;
    this.http.get<Statistics>('/api/users/statistics').subscribe({
      next: (data) => {
        this.statistics = data;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading statistics:', error);
        this.loading = false;
      }
    });
  }

  // Load orders
  loadOrders(): void {
    this.loading = true;
    this.http.get<Order[]>('/api/orders').subscribe({
      next: (data) => {
        this.orders = data;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading orders:', error);
        this.loading = false;
      }
    });
  }

  // Load order statistics
  loadOrderStatistics(): void {
    this.loading = true;
    this.http.get<Statistics>('/api/orders/statistics').subscribe({
      next: (data) => {
        this.statistics = data;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading order statistics:', error);
        this.loading = false;
      }
    });
  }

  // Load products
  loadProducts(): void {
    this.loading = true;
    this.http.get<Product[]>('/api/products').subscribe({
      next: (data) => {
        this.products = data;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading products:', error);
        this.loading = false;
      }
    });
  }

  // Load product recommendations
  loadProductRecommendations(): void {
    this.loading = true;
    this.http.get<Product[]>('/api/products/recommendations').subscribe({
      next: (data) => {
        this.products = data;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading recommendations:', error);
        this.loading = false;
      }
    });
  }

  // Update user status
  updateUserStatus(userId: number, newStatus: string): void {
    this.loading = true;
    this.http.put(`/api/users/${userId}/status`, { status: newStatus }).subscribe({
      next: () => {
        this.loadUsers(); // Refresh user list
        this.loading = false;
      },
      error: (error) => {
        console.error('Error updating user status:', error);
        this.loading = false;
      }
    });
  }

  // Delete inactive users
  deleteInactiveUsers(): void {
    this.loading = true;
    this.http.delete('/api/users/inactive').subscribe({
      next: () => {
        this.loadUsers(); // Refresh user list
        this.loading = false;
      },
      error: (error) => {
        console.error('Error deleting inactive users:', error);
        this.loading = false;
      }
    });
  }

  // Update product prices
  updateProductPrices(): void {
    this.loading = true;
    this.http.put('/api/products/prices/update', {}).subscribe({
      next: () => {
        this.loadProducts(); // Refresh product list
        this.loading = false;
      },
      error: (error) => {
        console.error('Error updating product prices:', error);
        this.loading = false;
      }
    });
  }

  // Insert user order statistics
  insertUserOrderStatistics(): void {
    this.loading = true;
    this.http.post('/api/users/order-statistics', {}).subscribe({
      next: () => {
        this.loadUserStatistics(); // Refresh statistics
        this.loading = false;
      },
      error: (error) => {
        console.error('Error inserting user order statistics:', error);
        this.loading = false;
      }
    });
  }

  // Insert product recommendations
  insertProductRecommendations(): void {
    this.loading = true;
    this.http.post('/api/products/recommendations/insert', {}).subscribe({
      next: () => {
        this.loadProductRecommendations(); // Refresh recommendations
        this.loading = false;
      },
      error: (error) => {
        console.error('Error inserting product recommendations:', error);
        this.loading = false;
      }
    });
  }
}
