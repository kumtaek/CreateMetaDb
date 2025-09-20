/**
 * TypeScript 유틸리티 모듈
 * 1차 개발 범위: TypeScript 파일 분석 테스트케이스
 * 
 * 백엔드 호출 패턴:
 * - axios를 통한 유틸리티 API 호출
 * - 타입 안전성을 갖춘 유틸리티 함수
 * - HTTP 클라이언트 래퍼
 */

import axios, { AxiosResponse, AxiosRequestConfig } from 'axios';

// 유틸리티 함수들을 위한 타입 정의
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

export interface ApiConfig {
  baseURL: string;
  timeout: number;
  retries: number;
  retryDelay: number;
}

export interface CacheConfig {
  ttl: number; // Time To Live (seconds)
  maxSize: number;
}

// API 응답 타입
export interface UtilityApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  timestamp: string;
  requestId: string;
}

/**
 * HTTP 클라이언트 유틸리티 클래스
 * 백엔드 API 호출을 위한 타입 안전한 HTTP 클라이언트
 */
export class HttpClient {
  private axiosInstance;
  private config: ApiConfig;

  constructor(config: Partial<ApiConfig> = {}) {
    this.config = {
      baseURL: '/api/v2',
      timeout: 10000,
      retries: 3,
      retryDelay: 1000,
      ...config
    };

    this.axiosInstance = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // 요청 인터셉터
    this.axiosInstance.interceptors.request.use(
      (config) => {
        console.log(`Making request to: ${config.url}`);
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 응답 인터셉터
    this.axiosInstance.interceptors.response.use(
      (response) => {
        console.log(`Received response from: ${response.config.url}`);
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          // 토큰 갱신 로직 (구현 예시)
          return this.axiosInstance(originalRequest);
        }

        return Promise.reject(error);
      }
    );
  }

  /**
   * GET 요청
   * FRONTEND_API: GET /api/v2/utils/* -> API_ENTRY: TypeScriptUtilityController.*()
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<UtilityApiResponse<T>> {
    try {
      const response: AxiosResponse<UtilityApiResponse<T>> = await this.axiosInstance.get(url, config);
      return response.data;
    } catch (error) {
      console.error(`GET request failed for ${url}:`, error);
      throw error;
    }
  }

  /**
   * POST 요청
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<UtilityApiResponse<T>> {
    try {
      const response: AxiosResponse<UtilityApiResponse<T>> = await this.axiosInstance.post(url, data, config);
      return response.data;
    } catch (error) {
      console.error(`POST request failed for ${url}:`, error);
      throw error;
    }
  }

  /**
   * PUT 요청
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<UtilityApiResponse<T>> {
    try {
      const response: AxiosResponse<UtilityApiResponse<T>> = await this.axiosInstance.put(url, data, config);
      return response.data;
    } catch (error) {
      console.error(`PUT request failed for ${url}:`, error);
      throw error;
    }
  }

  /**
   * DELETE 요청
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<UtilityApiResponse<T>> {
    try {
      const response: AxiosResponse<UtilityApiResponse<T>> = await this.axiosInstance.delete(url, config);
      return response.data;
    } catch (error) {
      console.error(`DELETE request failed for ${url}:`, error);
      throw error;
    }
  }
}

// 싱글톤 HTTP 클라이언트 인스턴스
export const httpClient = new HttpClient();

/**
 * 데이터 검증 유틸리티
 * FRONTEND_API: POST /api/v2/utils/validate -> API_ENTRY: TypeScriptUtilityController.validateData()
 */
export class ValidationUtils {
  /**
   * 서버 사이드 데이터 검증
   */
  static async validateData<T>(data: T, validationRules: any): Promise<ValidationResult> {
    try {
      const response = await httpClient.post('/utils/validate', {
        data,
        rules: validationRules
      });

      return response.data;
    } catch (error) {
      console.error('Data validation failed:', error);
      return {
        isValid: false,
        errors: ['서버 검증 실패']
      };
    }
  }

  /**
   * 클라이언트 사이드 이메일 검증
   */
  static validateEmail(email: string): ValidationResult {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailRegex.test(email);
    
    return {
      isValid,
      errors: isValid ? [] : ['올바른 이메일 형식이 아닙니다.']
    };
  }

  /**
   * 클라이언트 사이드 비밀번호 검증
   */
  static validatePassword(password: string): ValidationResult {
    const errors: string[] = [];
    
    if (password.length < 8) {
      errors.push('비밀번호는 8자 이상이어야 합니다.');
    }
    
    if (!/[A-Z]/.test(password)) {
      errors.push('대문자를 포함해야 합니다.');
    }
    
    if (!/[a-z]/.test(password)) {
      errors.push('소문자를 포함해야 합니다.');
    }
    
    if (!/\d/.test(password)) {
      errors.push('숫자를 포함해야 합니다.');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }
}

/**
 * 파일 업로드 유틸리티
 * FRONTEND_API: POST /api/v2/utils/upload -> API_ENTRY: TypeScriptUtilityController.uploadFile()
 */
export class FileUploadUtils {
  /**
   * 파일 업로드
   */
  static async uploadFile(file: File, options?: {
    onProgress?: (progress: number) => void;
    onSuccess?: (response: any) => void;
    onError?: (error: any) => void;
  }): Promise<UtilityApiResponse> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await httpClient.post('/utils/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (options?.onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            options.onProgress(progress);
          }
        },
      });

      options?.onSuccess?.(response.data);
      return response;
    } catch (error) {
      options?.onError?.(error);
      throw error;
    }
  }

  /**
   * 다중 파일 업로드
   */
  static async uploadMultipleFiles(files: File[], options?: {
    onProgress?: (progress: number) => void;
    onSuccess?: (response: any) => void;
    onError?: (error: any) => void;
  }): Promise<UtilityApiResponse> {
    const formData = new FormData();
    files.forEach((file, index) => {
      formData.append(`files[${index}]`, file);
    });

    try {
      const response = await httpClient.post('/utils/upload-multiple', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (options?.onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            options.onProgress(progress);
          }
        },
      });

      options?.onSuccess?.(response.data);
      return response;
    } catch (error) {
      options?.onError?.(error);
      throw error;
    }
  }
}

/**
 * 캐시 유틸리티
 * FRONTEND_API: GET/POST /api/v2/utils/cache -> API_ENTRY: TypeScriptUtilityController.*Cache()
 */
export class CacheUtils {
  private static cache = new Map<string, { data: any; expiry: number }>();
  private static config: CacheConfig = {
    ttl: 300, // 5분
    maxSize: 100
  };

  /**
   * 캐시에서 데이터 조회
   */
  static async get<T>(key: string): Promise<T | null> {
    // 메모리 캐시에서 먼저 확인
    const cached = this.cache.get(key);
    if (cached && cached.expiry > Date.now()) {
      return cached.data;
    }

    // 서버 캐시에서 조회
    try {
      const response = await httpClient.get(`/utils/cache/${key}`);
      if (response.success) {
        this.set(key, response.data);
        return response.data;
      }
    } catch (error) {
      console.error(`Cache get failed for key ${key}:`, error);
    }

    return null;
  }

  /**
   * 캐시에 데이터 저장
   */
  static async set(key: string, data: any, ttl?: number): Promise<void> {
    const expiry = Date.now() + (ttl || this.config.ttl) * 1000;
    
    // 메모리 캐시에 저장
    this.cache.set(key, { data, expiry });
    
    // 캐시 크기 제한
    if (this.cache.size > this.config.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }

    // 서버 캐시에도 저장
    try {
      await httpClient.post('/utils/cache', {
        key,
        data,
        ttl: ttl || this.config.ttl
      });
    } catch (error) {
      console.error(`Cache set failed for key ${key}:`, error);
    }
  }

  /**
   * 캐시에서 데이터 삭제
   */
  static async delete(key: string): Promise<void> {
    // 메모리 캐시에서 삭제
    this.cache.delete(key);

    // 서버 캐시에서도 삭제
    try {
      await httpClient.delete(`/utils/cache/${key}`);
    } catch (error) {
      console.error(`Cache delete failed for key ${key}:`, error);
    }
  }

  /**
   * 캐시 전체 초기화
   */
  static async clear(): Promise<void> {
    // 메모리 캐시 초기화
    this.cache.clear();

    // 서버 캐시도 초기화
    try {
      await httpClient.delete('/utils/cache');
    } catch (error) {
      console.error('Cache clear failed:', error);
    }
  }
}

/**
 * 로깅 유틸리티
 * FRONTEND_API: POST /api/v2/utils/log -> API_ENTRY: TypeScriptUtilityController.log()
 */
export class LoggingUtils {
  /**
   * 서버로 로그 전송
   */
  static async log(level: 'info' | 'warn' | 'error', message: string, data?: any): Promise<void> {
    try {
      await httpClient.post('/utils/log', {
        level,
        message,
        data,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      });
    } catch (error) {
      console.error('Failed to send log to server:', error);
    }
  }

  /**
   * 정보 로그
   */
  static info(message: string, data?: any): void {
    console.info(message, data);
    this.log('info', message, data);
  }

  /**
   * 경고 로그
   */
  static warn(message: string, data?: any): void {
    console.warn(message, data);
    this.log('warn', message, data);
  }

  /**
   * 에러 로그
   */
  static error(message: string, data?: any): void {
    console.error(message, data);
    this.log('error', message, data);
  }
}

/**
 * 날짜/시간 유틸리티
 */
export class DateTimeUtils {
  /**
   * 날짜 포맷팅
   */
  static formatDate(date: Date, format: string = 'YYYY-MM-DD'): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    return format
      .replace('YYYY', year.toString())
      .replace('MM', month)
      .replace('DD', day)
      .replace('HH', hours)
      .replace('mm', minutes)
      .replace('ss', seconds);
  }

  /**
   * 상대 시간 표시
   */
  static getRelativeTime(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}일 전`;
    if (hours > 0) return `${hours}시간 전`;
    if (minutes > 0) return `${minutes}분 전`;
    return `${seconds}초 전`;
  }
}

/**
 * 문자열 유틸리티
 */
export class StringUtils {
  /**
   * 문자열 자르기
   */
  static truncate(str: string, length: number, suffix: string = '...'): string {
    if (str.length <= length) return str;
    return str.substring(0, length) + suffix;
  }

  /**
   * 카멜케이스로 변환
   */
  static toCamelCase(str: string): string {
    return str.replace(/-([a-z])/g, (g) => g[1].toUpperCase());
  }

  /**
   * 케밥케이스로 변환
   */
  static toKebabCase(str: string): string {
    return str.replace(/([A-Z])/g, '-$1').toLowerCase().replace(/^-/, '');
  }
}
