@echo off
REM Neo4j 간단 설치 스크립트 (Docker 없이)
REM Neo4j Desktop 사용 방식

echo ========================================
echo Neo4j 간단 설치 가이드 (Docker 없이)
echo ========================================

REM 1. Python 패키지 설치
echo [1/3] Python 패키지 설치 중...
pip install neo4j pandas
if %errorlevel% neq 0 (
    echo ❌ Python 패키지 설치 실패
    pause
    exit /b 1
) else (
    echo ✅ Python 패키지 설치 완료
)

REM 2. Neo4j Desktop 다운로드 안내
echo.
echo [2/3] Neo4j Desktop 설치 안내
echo.
echo 📥 다음 링크에서 Neo4j Desktop을 다운로드하세요:
echo    https://neo4j.com/download/
echo.
echo 📋 설치 후 다음 단계를 따르세요:
echo    1. Neo4j Desktop 실행
echo    2. "New Project" 클릭
echo    3. "Create a Local DBMS" 클릭
echo    4. 이름: analyzer-db
echo    5. 비밀번호: password123
echo    6. "Create" 클릭
echo    7. "Start" 버튼으로 데이터베이스 시작
echo.
echo ⏳ Neo4j Desktop 설치가 완료되면 아무 키나 누르세요...
pause

REM 3. 연결 테스트
echo.
echo [3/3] Neo4j 연결 테스트 중...
python -c "
from neo4j import GraphDatabase
import time

print('Neo4j 연결 테스트 중...')
max_retries = 5
for i in range(max_retries):
    try:
        driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password123'))
        with driver.session() as session:
            result = session.run('RETURN 1')
            result.single()
        driver.close()
        print('✅ Neo4j 연결 테스트 성공')
        break
    except Exception as e:
        print(f'⏳ 연결 시도 {i+1}/{max_retries} 실패: {e}')
        if i < max_retries - 1:
            print('   5초 후 재시도...')
            time.sleep(5)
        else:
            print('❌ Neo4j 연결 실패')
            print('   Neo4j Desktop에서 데이터베이스가 시작되었는지 확인하세요.')
            exit(1)
"

if %errorlevel% neq 0 (
    echo.
    echo ❌ 연결 실패. 다음을 확인하세요:
    echo    1. Neo4j Desktop이 실행 중인지 확인
    echo    2. 데이터베이스가 시작되었는지 확인
    echo    3. 비밀번호가 'password123'인지 확인
    echo    4. 포트 7687이 사용 중인지 확인
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ 설치 완료!
echo ========================================
echo.
echo 📌 Neo4j Browser: http://localhost:7474
echo    사용자명: neo4j
echo    비밀번호: password123
echo.
echo 🚀 마이그레이션 실행:
echo    python ./temp/migration_runner.py sampleSrc
echo.
pause
