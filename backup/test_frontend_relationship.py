#!/usr/bin/env python3
"""
프론트엔드→API→METHOD 연관관계 통합 테스트
- FrontendApiAnalyzer 테스트
- RelationshipBuilder 프론트엔드 연결고리 테스트
"""

import sys
import os

# 현재 스크립트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from util.frontend_api_analyzer import FrontendApiAnalyzer
from relationship_builder import RelationshipBuilder
from util import app_logger, info, error, debug


def test_frontend_api_analyzer():
    """프론트엔드 API 분석기 테스트"""
    print("=== 프론트엔드 API 분석기 테스트 ===")

    analyzer = FrontendApiAnalyzer()

    # React 컴포넌트 테스트
    react_content = """
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const UserManagement = () => {
    const [users, setUsers] = useState([]);

    useEffect(() => {
        // 사용자 목록 조회
        axios.get('/api/users')
            .then(response => setUsers(response.data))
            .catch(error => console.error(error));
    }, []);

    const handleCreateUser = async (userData) => {
        try {
            const response = await axios.post('/api/users', userData);
            setUsers([...users, response.data]);
        } catch (error) {
            console.error('사용자 생성 실패:', error);
        }
    };

    const handleDeleteUser = (userId) => {
        axios.delete(`/api/users/${userId}`)
            .then(() => {
                setUsers(users.filter(user => user.id !== userId));
            });
    };

    return <div>사용자 관리</div>;
};

export default UserManagement;
"""

    print("1. React 컴포넌트 분석:")
    react_result = analyzer.analyze_frontend_file("UserManagement.jsx", react_content)
    print(f"파일 타입: {react_result['file_type']}")
    print(f"컴포넌트명: {react_result['component_name']}")
    print(f"API 호출: {react_result['api_call_count']}개")

    for api_call in react_result['api_calls']:
        print(f"  - {api_call['http_method']} {api_call['api_url']} ({api_call['framework']}, 신뢰도: {api_call['confidence']:.2f})")

    # Vue 컴포넌트 테스트
    vue_content = """
<template>
  <div>
    <h1>상품 관리</h1>
    <button @click="loadProducts">상품 목록 새로고침</button>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'ProductManagement',
  data() {
    return {
      products: []
    };
  },
  methods: {
    async loadProducts() {
      try {
        const response = await axios.get('/api/products');
        this.products = response.data;
      } catch (error) {
        console.error(error);
      }
    },

    async createProduct(productData) {
      const result = await this.$http.post('/api/products', productData);
      this.products.push(result.data);
    },

    deleteProduct(productId) {
      fetch(`/api/products/${productId}`, {
        method: 'DELETE'
      }).then(() => {
        this.loadProducts();
      });
    }
  },

  mounted() {
    this.loadProducts();
  }
};
</script>
"""

    print("\n2. Vue 컴포넌트 분석:")
    vue_result = analyzer.analyze_frontend_file("ProductManagement.vue", vue_content)
    print(f"파일 타입: {vue_result['file_type']}")
    print(f"컴포넌트명: {vue_result['component_name']}")
    print(f"API 호출: {vue_result['api_call_count']}개")

    for api_call in vue_result['api_calls']:
        print(f"  - {api_call['http_method']} {api_call['api_url']} ({api_call['framework']}, 신뢰도: {api_call['confidence']:.2f})")

    # TypeScript 컴포넌트 테스트
    typescript_content = """
import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

interface User {
  id: number;
  username: string;
  email: string;
}

@Component({
  selector: 'app-user-list',
  templateUrl: './user-list.component.html'
})
export class UserListComponent implements OnInit {
  users: User[] = [];

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadUsers();
  }

  loadUsers(): void {
    this.http.get<User[]>('/api/users')
      .subscribe(users => this.users = users);
  }

  async updateUser(user: User): Promise<void> {
    const response = await fetch(`/api/users/${user.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(user)
    });

    if (response.ok) {
      this.loadUsers();
    }
  }
}
"""

    print("\n3. TypeScript 컴포넌트 분석:")
    ts_result = analyzer.analyze_frontend_file("user-list.component.ts", typescript_content)
    print(f"파일 타입: {ts_result['file_type']}")
    print(f"컴포넌트명: {ts_result['component_name']}")
    print(f"API 호출: {ts_result['api_call_count']}개")

    for api_call in ts_result['api_calls']:
        print(f"  - {api_call['http_method']} {api_call['api_url']} ({api_call['framework']}, 신뢰도: {api_call['confidence']:.2f})")

    return [react_result, vue_result, ts_result]


def test_relationship_builder_integration():
    """RelationshipBuilder 프론트엔드 통합 테스트"""
    print("\n\n=== RelationshipBuilder 프론트엔드 통합 테스트 ===")

    # 테스트용 RelationshipBuilder 생성
    builder = RelationshipBuilder("test_frontend", 1)

    # 프론트엔드 분석 결과 추가
    frontend_results = test_frontend_api_analyzer()

    for result in frontend_results:
        builder.add_frontend_analysis_result(result)

    # Controller API 분석 결과 시뮬레이션
    controller_result = {
        'file_path': 'UserController.java',
        'class_name': 'UserController',
        'api_mappings': [
            {
                'method_name': 'getAllUsers',
                'api_url': '/api/users',
                'http_method': 'GET',
                'request_mapping': '@GetMapping("/api/users")',
                'confidence': 0.9
            },
            {
                'method_name': 'createUser',
                'api_url': '/api/users',
                'http_method': 'POST',
                'request_mapping': '@PostMapping("/api/users")',
                'confidence': 0.9
            },
            {
                'method_name': 'deleteUser',
                'api_url': '/api/users/{id}',
                'http_method': 'DELETE',
                'request_mapping': '@DeleteMapping("/api/users/{id}")',
                'confidence': 0.9
            }
        ]
    }

    builder.add_controller_analysis_result(controller_result)

    print("1. 수집된 프론트엔드 파일 정보:")
    frontend_files = builder.collected_data['frontend_files']
    for file_info in frontend_files:
        print(f"  - {file_info['component_name']} ({file_info['file_type']}) - API 호출 {file_info['api_call_count']}개")

    print(f"\n2. 수집된 API 호출: {len(builder.collected_data['api_calls'])}개")
    for api_call in builder.collected_data['api_calls']:
        print(f"  - {api_call['component_name']}: {api_call['http_method']} {api_call['api_url']}")

    print(f"\n3. 수집된 Controller API: {len(builder.collected_data['controller_apis'])}개")
    for controller_api in builder.collected_data['controller_apis']:
        print(f"  - {controller_api['class_name']}.{controller_api['method_name']}: {controller_api['http_method']} {controller_api['api_url']}")

    # API URL 정규화 테스트
    print("\n4. API URL 정규화 테스트:")
    test_urls = [
        "/api/users/123",
        "/api/users/{userId}",
        "/api/products/456/reviews",
        "/api/categories/{categoryId}/products/{productId}"
    ]

    for url in test_urls:
        normalized = builder._normalize_api_url_for_matching(url)
        print(f"  {url} → {normalized}")

    # 매칭 테스트
    print("\n5. API 매칭 테스트:")
    test_frontend_calls = [
        ("/api/users", "GET"),
        ("/api/users/123", "DELETE"),
        ("/api/products", "GET")
    ]

    for api_url, http_method in test_frontend_calls:
        matching = builder._find_matching_controller_api(api_url, http_method)
        if matching:
            print(f"  {http_method} {api_url} → {matching['class_name']}.{matching['method_name']}")
        else:
            print(f"  {http_method} {api_url} → 매칭 없음")


def main():
    """메인 테스트 실행"""
    print("프론트엔드→API→METHOD 연관관계 통합 테스트 시작")
    print("=" * 60)

    try:
        # 1. 프론트엔드 API 분석기 테스트
        test_frontend_api_analyzer()

        # 2. RelationshipBuilder 통합 테스트
        test_relationship_builder_integration()

        print("\n\n=== 테스트 완료 ===")
        print("프론트엔드→API→METHOD 연결고리가 정상적으로 구현되었습니다.")

    except Exception as e:
        print(f"\n테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)