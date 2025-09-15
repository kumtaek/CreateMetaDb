#!/usr/bin/env python3
"""
Servlet 분석기 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser.servlet_entry_analyzer import ServletEntryAnalyzer
from parser.base_entry_analyzer import FileInfo
from util.logger import app_logger

class MockStats:
    """Mock 통계 수집기"""
    def log_file_result(self, **kwargs):
        print(f"Stats: {kwargs}")

def test_servlet_with_annotation():
    """@WebServlet 어노테이션이 있는 Servlet 테스트"""
    print("=== @WebServlet 어노테이션 테스트 ===")
    
    # 테스트 파일 내용
    content = '''
package com.example.servlet;

import javax.servlet.*;
import javax.servlet.http.*;
import javax.servlet.annotation.*;
import java.io.IOException;

@WebServlet(urlPatterns = {"/api/user/*", "/user/list"})
public class UserServlet extends HttpServlet {
    
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        response.getWriter().println("GET User Data");
    }
    
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        response.getWriter().println("POST User Data");
    }
    
    @Override
    protected void doPut(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        response.getWriter().println("PUT User Data");
    }
    
    @Override
    protected void doDelete(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        response.getWriter().println("DELETE User Data");
    }
}
'''
    
    # FileInfo 객체 생성
    file_info = FileInfo(
        file_id=1,
        file_path="UserServlet.java",
        file_name="UserServlet.java",
        file_type="java",
        content=content,
        hash_value="test_hash"
    )
    
    # Servlet 분석기 생성
    analyzer = ServletEntryAnalyzer()
    
    # 분석 실행
    results = analyzer.analyze_backend_entry(file_info, MockStats())
    
    print(f"분석 결과: {len(results)}개 진입점 발견")
    for result in results:
        print(f"  {result.http_method} {result.url_pattern} - {result.class_name}.{result.method_name}")
    
    return len(results) > 0

def test_servlet_with_service():
    """service() 메서드를 사용하는 Servlet 테스트"""
    print("\n=== service() 메서드 테스트 ===")
    
    # 테스트 파일 내용
    content = '''
package com.example.servlet;

import javax.servlet.*;
import javax.servlet.http.*;
import javax.servlet.annotation.*;
import java.io.IOException;

@WebServlet("/admin/*")
public class AdminServlet extends HttpServlet {
    
    @Override
    protected void service(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        String method = request.getMethod();
        response.getWriter().println("Service method handling: " + method);
    }
}
'''
    
    # FileInfo 객체 생성
    file_info = FileInfo(
        file_id=2,
        file_path="AdminServlet.java",
        file_name="AdminServlet.java",
        file_type="java",
        content=content,
        hash_value="test_hash2"
    )
    
    # Servlet 분석기 생성
    analyzer = ServletEntryAnalyzer()
    
    # 분석 실행
    results = analyzer.analyze_backend_entry(file_info, MockStats())
    
    print(f"분석 결과: {len(results)}개 진입점 발견")
    for result in results:
        print(f"  {result.http_method} {result.url_pattern} - {result.class_name}.{result.method_name}")
    
    return len(results) > 0

def test_servlet_with_web_xml():
    """web.xml 매핑이 있는 Servlet 테스트"""
    print("\n=== web.xml 매핑 테스트 ===")
    
    # 테스트 파일 내용
    content = '''
package com.example.servlet;

import javax.servlet.*;
import javax.servlet.http.*;
import java.io.IOException;

public class LegacyServlet extends HttpServlet {
    
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        response.getWriter().println("Legacy GET Data");
    }
    
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        response.getWriter().println("Legacy POST Data");
    }
}
'''
    
    # FileInfo 객체 생성
    file_info = FileInfo(
        file_id=3,
        file_path="LegacyServlet.java",
        file_name="LegacyServlet.java",
        file_type="java",
        content=content,
        hash_value="test_hash3"
    )
    
    # web.xml 매핑 정보
    servlet_url_map = {
        "com.example.servlet.LegacyServlet": "/legacy/*"
    }
    
    # Servlet 분석기 생성 (web.xml 맵 전달)
    analyzer = ServletEntryAnalyzer(servlet_url_map=servlet_url_map)
    
    # 분석 실행
    results = analyzer.analyze_backend_entry(file_info, MockStats())
    
    print(f"분석 결과: {len(results)}개 진입점 발견")
    for result in results:
        print(f"  {result.http_method} {result.url_pattern} - {result.class_name}.{result.method_name}")
    
    return len(results) > 0

def main():
    """메인 테스트 함수"""
    print("Servlet 분석기 테스트 시작")
    
    try:
        # 테스트 실행
        test1_result = test_servlet_with_annotation()
        test2_result = test_servlet_with_service()
        test3_result = test_servlet_with_web_xml()
        
        # 결과 요약
        print("\n=== 테스트 결과 요약 ===")
        print(f"@WebServlet 어노테이션 테스트: {'PASS' if test1_result else 'FAIL'}")
        print(f"service() 메서드 테스트: {'PASS' if test2_result else 'FAIL'}")
        print(f"web.xml 매핑 테스트: {'PASS' if test3_result else 'FAIL'}")
        
        all_passed = test1_result and test2_result and test3_result
        print(f"\n전체 테스트 결과: {'PASS' if all_passed else 'FAIL'}")
        
        return all_passed
        
    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
