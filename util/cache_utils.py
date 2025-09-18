"""
SourceAnalyzer 분석 결과 캐시 유틸리티 모듈
- 파일 해시값 기반 분석 결과 캐싱
- 메모리 기반 캐시 관리
- 캐시 히트/미스 통계
"""

import threading
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .logger import app_logger, handle_error


@dataclass
class CacheEntry:
    """캐시 엔트리 데이터 클래스"""
    data: Any
    timestamp: float
    access_count: int = 0
    last_access: float = 0.0


class AnalysisCache:
    """분석 결과 캐시 관리 클래스"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        캐시 초기화
        
        Args:
            max_size: 최대 캐시 크기 (기본값: 1000)
            ttl_seconds: 캐시 TTL (Time To Live) 초 단위 (기본값: 3600 = 1시간)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 데이터 조회
        
        Args:
            key: 캐시 키 (파일 해시값 등)
            
        Returns:
            캐시된 데이터 또는 None (캐시 미스)
        """
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            current_time = time.time()
            
            # TTL 확인
            if current_time - entry.timestamp > self.ttl_seconds:
                del self._cache[key]
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                return None
            
            # 접근 통계 업데이트
            entry.access_count += 1
            entry.last_access = current_time
            self._stats['hits'] += 1
            
            return entry.data
    
    def set(self, key: str, data: Any) -> None:
        """
        캐시에 데이터 저장
        
        Args:
            key: 캐시 키
            data: 저장할 데이터
        """
        with self._lock:
            current_time = time.time()
            
            # 캐시 크기 확인 및 LRU 기반 제거
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            # 캐시 엔트리 생성/업데이트
            self._cache[key] = CacheEntry(
                data=data,
                timestamp=current_time,
                access_count=1,
                last_access=current_time
            )
    
    def _evict_lru(self) -> None:
        """LRU(Least Recently Used) 기반 캐시 엔트리 제거"""
        if not self._cache:
            return
        
        # 가장 오래된 접근 시간을 가진 엔트리 찾기
        lru_key = min(self._cache.keys(), 
                     key=lambda k: self._cache[k].last_access)
        
        del self._cache[lru_key]
        self._stats['evictions'] += 1
    
    def clear(self) -> None:
        """캐시 전체 초기화"""
        with self._lock:
            self._cache.clear()
            self._stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'expirations': 0
            }
    
    def cleanup_expired(self) -> int:
        """
        만료된 캐시 엔트리 정리
        
        Returns:
            정리된 엔트리 수
        """
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self._cache.items():
                if current_time - entry.timestamp > self.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self._stats['expirations'] += 1
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 정보 조회
        
        Returns:
            캐시 통계 딕셔너리
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'cache_size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': round(hit_rate, 2),
                'evictions': self._stats['evictions'],
                'expirations': self._stats['expirations'],
                'ttl_seconds': self.ttl_seconds
            }
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        캐시 상세 정보 조회
        
        Returns:
            캐시 상세 정보 딕셔너리
        """
        with self._lock:
            current_time = time.time()
            entries_info = []
            
            for key, entry in self._cache.items():
                age = current_time - entry.timestamp
                time_since_access = current_time - entry.last_access
                
                entries_info.append({
                    'key': key,
                    'age_seconds': round(age, 2),
                    'access_count': entry.access_count,
                    'time_since_access': round(time_since_access, 2),
                    'is_expired': age > self.ttl_seconds
                })
            
            return {
                'total_entries': len(self._cache),
                'entries': entries_info,
                'stats': self.get_stats()
            }


# 전역 캐시 인스턴스
_global_cache: Optional[AnalysisCache] = None
_cache_lock = threading.Lock()


def get_global_cache() -> AnalysisCache:
    """
    전역 캐시 인스턴스 조회 (싱글톤)
    
    Returns:
        전역 AnalysisCache 인스턴스
    """
    global _global_cache
    
    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                _global_cache = AnalysisCache()
    
    return _global_cache


def clear_global_cache() -> None:
    """전역 캐시 초기화"""
    global _global_cache
    
    with _cache_lock:
        if _global_cache:
            _global_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """
    전역 캐시 통계 조회
    
    Returns:
        캐시 통계 딕셔너리
    """
    return get_global_cache().get_stats()


def cleanup_expired_cache() -> int:
    """
    전역 캐시의 만료된 엔트리 정리
    
    Returns:
        정리된 엔트리 수
    """
    return get_global_cache().cleanup_expired()


# 편의 함수들
def cache_get(key: str) -> Optional[Any]:
    """전역 캐시에서 데이터 조회 편의 함수"""
    return get_global_cache().get(key)


def cache_set(key: str, data: Any) -> None:
    """전역 캐시에 데이터 저장 편의 함수"""
    get_global_cache().set(key, data)


# 사용 예시
if __name__ == "__main__":
    # 캐시 테스트
    cache = AnalysisCache(max_size=5, ttl_seconds=10)
    
    # 데이터 저장
    cache.set("file1", {"result": "data1"})
    cache.set("file2", {"result": "data2"})
    
    # 데이터 조회
    result1 = cache.get("file1")
    print(f"Cache hit: {result1}")
    
    result3 = cache.get("file3")
    print(f"Cache miss: {result3}")
    
    # 통계 조회
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")
    
    # 캐시 정보 조회
    info = cache.get_cache_info()
    print(f"Cache info: {info}")


# --- Gemini 추가 시작: MyBatis <sql> 조각 캐시 ---
import xml.etree.ElementTree as ET
from typing import Dict, Optional
from .path_utils import PathUtils
from .logger import info, warning, handle_error

class SqlFragmentCache:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SqlFragmentCache, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.fragments: Dict[str, ET.Element] = {}
            self.initialized: bool = False
            self.path_utils = PathUtils()

    def load_all_fragments(self, project_name: str, target_config: dict):
        if self.initialized:
            return
        
        project_path = self.path_utils.get_project_source_path(project_name)
        
        # target_source_config.yaml 기반으로 파일 검색
        xml_config = target_config.get('file_type_settings', {}).get('xml', {})
        include_patterns = xml_config.get('include_patterns', ["**/*.xml"])
        exclude_patterns = xml_config.get('exclude_patterns', [])
        
        try:
            # PathUtils를 사용하여 파일 목록 가져오기
            xml_files = self.path_utils.find_files_by_patterns(project_path, include_patterns, exclude_patterns)
            info(f"SQL 조각 캐싱을 위해 {len(xml_files)}개의 XML 파일을 스캔합니다.")

            for file_path in xml_files:
                try:
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                    namespace = root.attrib.get('namespace', '')
                    for sql_node in root.findall('sql'):
                        node_id = sql_node.attrib.get('id')
                        if node_id:
                            # 네임스페이스 포함 키와 미포함 키 모두 저장
                            if namespace:
                                self.fragments[f"{namespace}.{node_id}"] = sql_node
                            self.fragments[node_id] = sql_node
                except ET.ParseError as e:
                    warning(f"XML 파싱 오류로 SQL 조각 캐시를 건너뜁니다: {file_path}, 사유: {e}")
                    continue # 파싱 오류는 전체를 중단시키지 않음
        except Exception as e:
            handle_error(e, "SqlFragmentCache 로딩 중 심각한 오류 발생")

        self.initialized = True
        info(f"SqlFragmentCache 초기화 완료. 총 {len(self.fragments)}개의 SQL 조각 로드됨.")

    def get_fragment_node(self, refid: str, current_namespace: str = '') -> Optional[ET.Element]:
        # 1. 네임스페이스.refid 형태로 먼저 조회
        if current_namespace and f"{current_namespace}.{refid}" in self.fragments:
            return self.fragments[f"{current_namespace}.{refid}"]
        # 2. refid 자체로 조회
        if refid in self.fragments:
            return self.fragments[refid]
        return None

# 전역 인스턴스 관리 함수
_sql_fragment_cache_instance = None
def get_sql_fragment_cache() -> SqlFragmentCache:
    global _sql_fragment_cache_instance
    if _sql_fragment_cache_instance is None:
        _sql_fragment_cache_instance = SqlFragmentCache()
    return _sql_fragment_cache_instance
# --- Gemini 추가 끝 ---
