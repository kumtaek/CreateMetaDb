"""
SourceAnalyzer 통계 수집 유틸리티 모듈
- 분석 성능 통계 수집
- 파일별 분석 결과 통계
- 프레임워크별 분석 통계
- 최종 통계 리포트 생성
"""

import time
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from .logger import app_logger, handle_error


@dataclass
class FileAnalysisStats:
    """파일별 분석 통계"""
    file_path: str
    framework: str
    success: bool
    stage: str  # 'ast', 'regex_fallback', 'full_failure'
    processing_time: float
    error_message: Optional[str] = None
    entries_found: int = 0


@dataclass
class FrameworkStats:
    """프레임워크별 통계"""
    framework_name: str
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    total_entries: int = 0
    total_processing_time: float = 0.0
    stage_stats: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    error_messages: List[str] = field(default_factory=list)


class StatisticsCollector:
    """통계 수집 및 관리 클래스"""
    
    def __init__(self):
        """통계 수집기 초기화"""
        self._lock = threading.RLock()
        self._file_stats: List[FileAnalysisStats] = []
        self._framework_stats: Dict[str, FrameworkStats] = defaultdict(lambda: FrameworkStats(""))
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
    
    def start_analysis(self) -> None:
        """분석 시작 시간 기록"""
        with self._lock:
            self._start_time = time.time()
            app_logger.info("분석 통계 수집 시작")
    
    def end_analysis(self) -> None:
        """분석 종료 시간 기록"""
        with self._lock:
            self._end_time = time.time()
            app_logger.info("분석 통계 수집 종료")
    
    def log_file_result(self, 
                       framework: str, 
                       file_path: str, 
                       success: bool, 
                       stage: str,
                       processing_time: float,
                       entries_found: int = 0,
                       error_message: Optional[str] = None) -> None:
        """
        파일 분석 결과 통계 기록
        
        Args:
            framework: 프레임워크명 (예: 'spring')
            file_path: 파일 경로
            success: 분석 성공 여부
            stage: 분석 단계 ('ast', 'regex_fallback', 'full_failure')
            processing_time: 처리 시간 (초)
            entries_found: 발견된 진입점 수
            error_message: 오류 메시지 (실패시)
        """
        with self._lock:
            # 파일별 통계 기록
            file_stat = FileAnalysisStats(
                file_path=file_path,
                framework=framework,
                success=success,
                stage=stage,
                processing_time=processing_time,
                entries_found=entries_found,
                error_message=error_message
            )
            self._file_stats.append(file_stat)
            
            # 프레임워크별 통계 업데이트
            if framework not in self._framework_stats:
                self._framework_stats[framework] = FrameworkStats(framework)
            
            framework_stat = self._framework_stats[framework]
            framework_stat.total_files += 1
            framework_stat.total_processing_time += processing_time
            framework_stat.stage_stats[stage] += 1
            
            if success:
                framework_stat.successful_files += 1
                framework_stat.total_entries += entries_found
            else:
                framework_stat.failed_files += 1
                if error_message:
                    framework_stat.error_messages.append(error_message)
            
            # 로그 출력
            if success:
                app_logger.debug(f"파일 분석 성공: {file_path} ({framework}, {stage}, {processing_time:.3f}s, {entries_found}개 진입점)")
            else:
                app_logger.debug(f"파일 분석 실패: {file_path} ({framework}, {stage}, {processing_time:.3f}s) - {error_message}")
    
    def get_framework_stats(self, framework: str) -> Optional[FrameworkStats]:
        """
        특정 프레임워크 통계 조회
        
        Args:
            framework: 프레임워크명
            
        Returns:
            프레임워크 통계 또는 None
        """
        with self._lock:
            return self._framework_stats.get(framework)
    
    def get_all_framework_stats(self) -> Dict[str, FrameworkStats]:
        """
        모든 프레임워크 통계 조회
        
        Returns:
            프레임워크별 통계 딕셔너리
        """
        with self._lock:
            return dict(self._framework_stats)
    
    def get_file_stats(self) -> List[FileAnalysisStats]:
        """
        파일별 통계 조회
        
        Returns:
            파일별 통계 리스트
        """
        with self._lock:
            return list(self._file_stats)
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        전체 요약 통계 조회
        
        Returns:
            요약 통계 딕셔너리
        """
        with self._lock:
            total_files = len(self._file_stats)
            total_successful = sum(1 for stat in self._file_stats if stat.success)
            total_failed = total_files - total_successful
            total_entries = sum(stat.entries_found for stat in self._file_stats)
            total_processing_time = sum(stat.processing_time for stat in self._file_stats)
            
            # 전체 분석 시간
            analysis_duration = 0.0
            if self._start_time and self._end_time:
                analysis_duration = self._end_time - self._start_time
            
            # 성공률 계산
            success_rate = (total_successful / total_files * 100) if total_files > 0 else 0
            
            # 평균 처리 시간
            avg_processing_time = (total_processing_time / total_files) if total_files > 0 else 0
            
            return {
                'total_files': total_files,
                'successful_files': total_successful,
                'failed_files': total_failed,
                'success_rate': round(success_rate, 2),
                'total_entries': total_entries,
                'total_processing_time': round(total_processing_time, 3),
                'avg_processing_time': round(avg_processing_time, 3),
                'analysis_duration': round(analysis_duration, 3),
                'frameworks': len(self._framework_stats)
            }
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """
        상세 통계 리포트 생성
        
        Returns:
            상세 통계 리포트 딕셔너리
        """
        with self._lock:
            summary = self.get_summary_stats()
            
            # 프레임워크별 상세 통계
            framework_details = {}
            for framework, stats in self._framework_stats.items():
                success_rate = (stats.successful_files / stats.total_files * 100) if stats.total_files > 0 else 0
                avg_processing_time = (stats.total_processing_time / stats.total_files) if stats.total_files > 0 else 0
                
                framework_details[framework] = {
                    'total_files': stats.total_files,
                    'successful_files': stats.successful_files,
                    'failed_files': stats.failed_files,
                    'success_rate': round(success_rate, 2),
                    'total_entries': stats.total_entries,
                    'total_processing_time': round(stats.total_processing_time, 3),
                    'avg_processing_time': round(avg_processing_time, 3),
                    'stage_breakdown': dict(stats.stage_stats),
                    'error_count': len(stats.error_messages),
                    'unique_errors': len(set(stats.error_messages))
                }
            
            # 실패한 파일 목록
            failed_files = [
                {
                    'file_path': stat.file_path,
                    'framework': stat.framework,
                    'stage': stat.stage,
                    'error_message': stat.error_message,
                    'processing_time': round(stat.processing_time, 3)
                }
                for stat in self._file_stats if not stat.success
            ]
            
            return {
                'summary': summary,
                'framework_details': framework_details,
                'failed_files': failed_files,
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def print_summary(self) -> None:
        """요약 통계 콘솔 출력"""
        with self._lock:
            summary = self.get_summary_stats()
            
            print("\n=== 백엔드 진입점 분석 통계 ===")
            print(f"총 파일 수: {summary['total_files']}")
            print(f"성공한 파일: {summary['successful_files']}")
            print(f"실패한 파일: {summary['failed_files']}")
            print(f"성공률: {summary['success_rate']}%")
            print(f"총 진입점 수: {summary['total_entries']}")
            print(f"총 처리 시간: {summary['total_processing_time']}초")
            print(f"평균 처리 시간: {summary['avg_processing_time']}초")
            print(f"전체 분석 시간: {summary['analysis_duration']}초")
            print(f"분석 프레임워크 수: {summary['frameworks']}")
            
            # 프레임워크별 통계
            if self._framework_stats:
                print("\n=== 프레임워크별 통계 ===")
                for framework, stats in self._framework_stats.items():
                    success_rate = (stats.successful_files / stats.total_files * 100) if stats.total_files > 0 else 0
                    print(f"{framework}: {stats.successful_files}/{stats.total_files} 성공 ({success_rate:.1f}%), {stats.total_entries}개 진입점")
            
            # 오류 요약
            if summary['failed_files'] > 0:
                print(f"\n[WARNING] {summary['failed_files']}개 파일 분석 실패")
            else:
                print("\n[OK] 모든 파일 분석 성공")
    
    def print_detailed_report(self) -> None:
        """상세 통계 리포트 콘솔 출력"""
        with self._lock:
            report = self.get_detailed_report()
            
            print("\n" + "="*60)
            print("백엔드 진입점 분석 상세 리포트")
            print("="*60)
            
            # 요약 정보
            summary = report['summary']
            print(f"\n[요약]")
            print(f"  총 파일 수: {summary['total_files']}")
            print(f"  성공한 파일: {summary['successful_files']}")
            print(f"  실패한 파일: {summary['failed_files']}")
            print(f"  성공률: {summary['success_rate']}%")
            print(f"  총 진입점 수: {summary['total_entries']}")
            print(f"  전체 분석 시간: {summary['analysis_duration']}초")
            
            # 프레임워크별 상세 정보
            if report['framework_details']:
                print(f"\n[프레임워크별 상세]")
                for framework, details in report['framework_details'].items():
                    print(f"  {framework}:")
                    print(f"    파일 수: {details['total_files']} (성공: {details['successful_files']}, 실패: {details['failed_files']})")
                    print(f"    성공률: {details['success_rate']}%")
                    print(f"    진입점 수: {details['total_entries']}")
                    print(f"    평균 처리 시간: {details['avg_processing_time']}초")
                    print(f"    단계별 분석: {details['stage_breakdown']}")
                    if details['error_count'] > 0:
                        print(f"    오류 수: {details['error_count']} (고유 오류: {details['unique_errors']})")
            
            # 실패한 파일 목록
            if report['failed_files']:
                print(f"\n[실패한 파일 목록]")
                for failed_file in report['failed_files']:
                    print(f"  {failed_file['file_path']} ({failed_file['framework']}, {failed_file['stage']})")
                    print(f"    오류: {failed_file['error_message']}")
            
            print(f"\n리포트 생성 시간: {report['generated_at']}")
            print("="*60)
    
    def reset(self) -> None:
        """통계 초기화"""
        with self._lock:
            self._file_stats.clear()
            self._framework_stats.clear()
            self._start_time = None
            self._end_time = None
            app_logger.info("통계 초기화 완료")


# 전역 통계 수집기 인스턴스
_global_collector: Optional[StatisticsCollector] = None
_collector_lock = threading.Lock()


def get_global_collector() -> StatisticsCollector:
    """
    전역 통계 수집기 인스턴스 조회 (싱글톤)
    
    Returns:
        전역 StatisticsCollector 인스턴스
    """
    global _global_collector
    
    if _global_collector is None:
        with _collector_lock:
            if _global_collector is None:
                _global_collector = StatisticsCollector()
    
    return _global_collector


def reset_global_collector() -> None:
    """전역 통계 수집기 초기화"""
    global _global_collector
    
    with _collector_lock:
        if _global_collector:
            _global_collector.reset()


# 편의 함수들
def start_analysis() -> None:
    """분석 시작 편의 함수"""
    get_global_collector().start_analysis()


def end_analysis() -> None:
    """분석 종료 편의 함수"""
    get_global_collector().end_analysis()


def log_file_result(framework: str, 
                   file_path: str, 
                   success: bool, 
                   stage: str,
                   processing_time: float,
                   entries_found: int = 0,
                   error_message: Optional[str] = None) -> None:
    """파일 분석 결과 기록 편의 함수"""
    get_global_collector().log_file_result(
        framework, file_path, success, stage, processing_time, 
        entries_found, error_message
    )


def print_summary() -> None:
    """요약 통계 출력 편의 함수"""
    get_global_collector().print_summary()


def print_detailed_report() -> None:
    """상세 통계 리포트 출력 편의 함수"""
    get_global_collector().print_detailed_report()


def get_summary_stats() -> Dict[str, Any]:
    """요약 통계 조회 편의 함수"""
    return get_global_collector().get_summary_stats()


# 사용 예시
if __name__ == "__main__":
    # 통계 수집기 테스트
    collector = StatisticsCollector()
    
    # 분석 시작
    collector.start_analysis()
    
    # 파일 분석 결과 기록
    collector.log_file_result("spring", "UserController.java", True, "ast", 0.5, 3)
    collector.log_file_result("spring", "OrderController.java", True, "regex_fallback", 1.2, 5)
    collector.log_file_result("spring", "ErrorController.java", False, "full_failure", 0.1, 0, "파싱 오류")
    
    # 분석 종료
    collector.end_analysis()
    
    # 통계 출력
    collector.print_summary()
    collector.print_detailed_report()
