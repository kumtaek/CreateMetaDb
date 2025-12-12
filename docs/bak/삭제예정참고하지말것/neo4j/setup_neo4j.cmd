@echo off
REM Neo4j 마이그레이션 환경 설정 스크립트 (Windows)
REM 사용법: setup_neo4j.cmd

echo ========================================
echo Neo4j 마이그레이션 환경 설정
echo ========================================

REM 1. Docker 설치 확인
echo [1/6] Docker 설치 확인 중...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker가 설치되지 않았습니다.
    echo    Docker Desktop을 설치하세요: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
) else (
    echo ✅ Docker 설치 확인됨
)

REM 2. Python 패키지 설치
echo.
echo [2/6] Python 패키지 설치 중...
pip install neo4j pandas >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 패키지 설치 실패
    echo    수동으로 설치하세요: pip install neo4j pandas
    pause
    exit /b 1
) else (
    echo ✅ Python 패키지 설치 완료
)

REM 3. Neo4j 컨테이너 중지 및 제거 (기존 것이 있다면)
echo.
echo [3/6] 기존 Neo4j 컨테이너 정리 중...
docker stop neo4j-analyzer >nul 2>&1
docker rm neo4j-analyzer >nul 2>&1
echo ✅ 기존 컨테이너 정리 완료

REM 4. Neo4j 컨테이너 실행
echo.
echo [4/6] Neo4j 컨테이너 시작 중...
docker run -d ^
    --name neo4j-analyzer ^
    -p 7474:7474 -p 7687:7687 ^
    -e NEO4J_AUTH=neo4j/password123 ^
    -v neo4j_data:/data ^
    -v neo4j_logs:/logs ^
    neo4j:latest

if %errorlevel% neq 0 (
    echo ❌ Neo4j 컨테이너 시작 실패
    pause
    exit /b 1
) else (
    echo ✅ Neo4j 컨테이너 시작 완료
)

REM 5. Neo4j 시작 대기
echo.
echo [5/6] Neo4j 시작 대기 중...
timeout /t 30 >nul
echo ✅ Neo4j 시작 대기 완료

REM 6. 연결 테스트
echo.
echo [6/6] Neo4j 연결 테스트 중...
python -c "
from neo4j import GraphDatabase
try:
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password123'))
    with driver.session() as session:
        result = session.run('RETURN 1')
        result.single()
    driver.close()
    print('✅ Neo4j 연결 테스트 성공')
except Exception as e:
    print(f'❌ Neo4j 연결 테스트 실패: {e}')
    exit(1)
"

if %errorlevel% neq 0 (
    echo.
    echo ❌ Neo4j 연결 실패. 다음을 확인하세요:
    echo    1. Docker 컨테이너 상태: docker ps
    echo    2. Neo4j 로그: docker logs neo4j-analyzer
    echo    3. 포트 사용 여부: netstat -an ^| findstr 7474
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ Neo4j 환경 설정 완료!
echo ========================================
echo.
echo 📌 Neo4j Browser 접속: http://localhost:7474
echo    사용자명: neo4j
echo    비밀번호: password123
echo.
echo 🚀 마이그레이션 실행:
echo    python ./temp/migration_runner.py sampleSrc
echo.
echo 🔍 컨테이너 관리:
echo    시작: docker start neo4j-analyzer
echo    중지: docker stop neo4j-analyzer
echo    로그: docker logs neo4j-analyzer
echo.
pause
