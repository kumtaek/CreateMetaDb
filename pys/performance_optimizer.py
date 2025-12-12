"""
성능 최적화를 위한 공통 유틸리티
- 메모리 사용량 최적화
- 파일 I/O 최적화
- 데이터베이스 쿼리 최적화
- 캐싱 메커니즘
"""
import os
import gc
import sys
import psutil
import threading
import time
from typing import Dict, Any, Optional, Callable, Set
from functools import wraps, lru_cache
from pathlib import Path
import hashlib

class PerformanceOptimizer:
    """성능 최적화 매니저"""

    def __init__(self):
        self.cache = {}
        self.file_cache = {}
        self.lock = threading.RLock()
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'memory_optimizations': 0,
            'gc_collections': 0
        }

    def get_memory_usage(self) -> Dict[str, float]:
        """현재 메모리 사용량 반환"""
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # 실제 사용 메모리
            'vms_mb': memory_info.vms / 1024 / 1024,  # 가상 메모리
            'percent': process.memory_percent()  # 시스템 메모리 대비 사용률
        }

    def optimize_memory(self, threshold_mb: float = 500.0) -> bool:
        """메모리 사용량이 임계값을 초과하면 최적화 수행"""
        try:
            memory_usage = self.get_memory_usage()

            if memory_usage['rss_mb'] > threshold_mb:
                # 캐시 정리
                with self.lock:
                    self.cache.clear()
                    self.file_cache.clear()

                # 가비지 컬렉션 강제 실행
                collected = gc.collect()

                self.stats['memory_optimizations'] += 1
                self.stats['gc_collections'] += collected

                return True

        except Exception:
            pass  # 메모리 최적화 실패는 무시

        return False

    def cached_file_read(self, file_path: str, max_cache_size: int = 100) -> Optional[str]:
        """파일 내용을 캐시하여 중복 읽기 방지"""
        try:
            file_path = str(Path(file_path).resolve())

            with self.lock:
                # 캐시 크기 제한
                if len(self.file_cache) >= max_cache_size:
                    # LRU 방식으로 가장 오래된 항목 제거
                    oldest_key = next(iter(self.file_cache))
                    del self.file_cache[oldest_key]

                # 파일 수정 시간을 포함한 키 생성
                if os.path.exists(file_path):
                    mtime = os.path.getmtime(file_path)
                    cache_key = f"{file_path}:{mtime}"

                    if cache_key in self.file_cache:
                        self.stats['cache_hits'] += 1
                        return self.file_cache[cache_key]

                    # 파일 읽기
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    self.file_cache[cache_key] = content
                    self.stats['cache_misses'] += 1
                    return content

        except Exception:
            pass  # 파일 읽기 실패

        return None

    def batch_file_operations(self, file_paths: list, operation: Callable, batch_size: int = 50):
        """파일 작업을 배치로 처리하여 I/O 최적화"""
        results = []

        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i:i + batch_size]
            batch_results = []

            for file_path in batch:
                try:
                    result = operation(file_path)
                    batch_results.append(result)
                except Exception as e:
                    batch_results.append(None)

            results.extend(batch_results)

            # 배치 처리 후 메모리 최적화 확인
            self.optimize_memory()

        return results

    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        memory_usage = self.get_memory_usage()

        cache_hit_rate = 0
        if self.stats['cache_hits'] + self.stats['cache_misses'] > 0:
            cache_hit_rate = self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses'])

        return {
            'memory_usage': memory_usage,
            'cache_stats': {
                'hits': self.stats['cache_hits'],
                'misses': self.stats['cache_misses'],
                'hit_rate': cache_hit_rate,
                'cache_size': len(self.cache) + len(self.file_cache)
            },
            'optimization_stats': {
                'memory_optimizations': self.stats['memory_optimizations'],
                'gc_collections': self.stats['gc_collections']
            }
        }

    def clear_caches(self):
        """모든 캐시 정리"""
        with self.lock:
            self.cache.clear()
            self.file_cache.clear()


# 싱글톤 성능 최적화 인스턴스
_performance_optimizer: Optional[PerformanceOptimizer] = None

def get_performance_optimizer() -> PerformanceOptimizer:
    """성능 최적화 인스턴스 반환"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer


def memory_efficient(threshold_mb: float = 500.0):
    """메모리 효율적인 함수 실행을 위한 데코레이터"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            optimizer = get_performance_optimizer()

            # 함수 실행 전 메모리 확인
            optimizer.optimize_memory(threshold_mb)

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # 함수 실행 후 메모리 정리
                optimizer.optimize_memory(threshold_mb)

        return wrapper
    return decorator


def cached_function(max_cache_size: int = 1000):
    """함수 결과를 캐시하는 데코레이터"""
    def decorator(func: Callable):
        cache = {}
        cache_lock = threading.RLock()

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = str(args) + str(sorted(kwargs.items()))
            cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()

            with cache_lock:
                if cache_key_hash in cache:
                    return cache[cache_key_hash]

                # 캐시 크기 제한
                if len(cache) >= max_cache_size:
                    # 첫 번째 항목 제거 (FIFO)
                    oldest_key = next(iter(cache))
                    del cache[oldest_key]

                result = func(*args, **kwargs)
                cache[cache_key_hash] = result
                return result

        return wrapper
    return decorator


def batch_process(batch_size: int = 50):
    """리스트를 배치 단위로 처리하는 데코레이터"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(items: list, *args, **kwargs):
            if not isinstance(items, list):
                return func(items, *args, **kwargs)

            results = []
            optimizer = get_performance_optimizer()

            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                batch_result = func(batch, *args, **kwargs)

                if isinstance(batch_result, list):
                    results.extend(batch_result)
                else:
                    results.append(batch_result)

                # 배치 처리 후 메모리 최적화
                optimizer.optimize_memory()

            return results

        return wrapper
    return decorator


# 성능 모니터링 유틸리티
class PerformanceMonitor:
    """성능 모니터링 클래스"""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None

    def __enter__(self):
        optimizer = get_performance_optimizer()
        self.start_time = time.time()
        self.start_memory = optimizer.get_memory_usage()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        optimizer = get_performance_optimizer()
        self.end_time = time.time()
        self.end_memory = optimizer.get_memory_usage()

        duration = self.end_time - self.start_time
        memory_diff = self.end_memory['rss_mb'] - self.start_memory['rss_mb']

        print(f"[PERF] {self.name}: {duration:.2f}s, Memory: {memory_diff:+.2f}MB")


def performance_monitor(name: str):
    """성능 모니터링 컨텍스트 매니저 생성"""
    return PerformanceMonitor(name)


# 편의 함수들
def optimize_memory_now(threshold_mb: float = 500.0) -> bool:
    """즉시 메모리 최적화 실행"""
    return get_performance_optimizer().optimize_memory(threshold_mb)

def get_memory_stats() -> Dict[str, float]:
    """현재 메모리 사용량 반환"""
    return get_performance_optimizer().get_memory_usage()

def clear_all_caches():
    """모든 캐시 정리"""
    get_performance_optimizer().clear_caches()

def get_perf_stats() -> Dict[str, Any]:
    """성능 통계 반환"""
    return get_performance_optimizer().get_performance_stats()