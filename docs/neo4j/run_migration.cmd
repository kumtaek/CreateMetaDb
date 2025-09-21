@echo off
REM Neo4j 마이그레이션 실행 스크립트
REM 사용법: run_migration.cmd [project_name]

if "%1"=="" (
    echo 사용법: run_migration.cmd ^<project_name^>
    echo 예: run_migration.cmd sampleSrc
    pause
    exit /b 1
)

set PROJECT_NAME=%1

echo ========================================
echo Neo4j 마이그레이션 실행: %PROJECT_NAME%
echo ========================================

REM 1. Neo4j 컨테이너 상태 확인
echo [1/5] Neo4j 컨테이너 상태 확인...
docker ps | findstr neo4j-analyzer >nul
if %errorlevel% neq 0 (
    echo ❌ Neo4j 컨테이너가 실행 중이 아닙니다.
    echo    컨테이너를 시작하세요: docker start neo4j-analyzer
    echo    또는 설정 스크립트를 실행하세요: setup_neo4j.cmd
    pause
    exit /b 1
) else (
    echo ✅ Neo4j 컨테이너 실행 중
)

REM 2. 프로젝트 데이터 확인
echo.
echo [2/5] 프로젝트 데이터 확인...
python -c "
import sys
sys.path.append('.')
from util.database_utils import DatabaseUtils
db = DatabaseUtils()
project_id = db.get_project_id_by_name('%PROJECT_NAME%')
if not project_id:
    print('❌ 프로젝트 \\'%PROJECT_NAME%\\'를 찾을 수 없습니다.')
    exit(1)
else:
    print(f'✅ 프로젝트 \\'%PROJECT_NAME%\\' 발견 (ID: {project_id})')
"

if %errorlevel% neq 0 (
    echo.
    echo 사용 가능한 프로젝트 목록:
    python -c "
import sys
sys.path.append('.')
from util.database_utils import DatabaseUtils
db = DatabaseUtils()
projects = db.get_all_projects()
for p in projects:
    print(f'  - {p[\"project_name\"]}')
"
    pause
    exit /b 1
)

REM 3. 백업 디렉토리 생성
echo.
echo [3/5] 백업 디렉토리 확인...
if not exist ".\temp" mkdir ".\temp"
echo ✅ 백업 디렉토리 준비 완료

REM 4. 마이그레이션 실행
echo.
echo [4/5] 마이그레이션 실행 중...
echo ⚠️  이 과정은 몇 분 소요될 수 있습니다.
echo.
python ./temp/migration_runner.py %PROJECT_NAME%

if %errorlevel% neq 0 (
    echo.
    echo ❌ 마이그레이션 실패
    echo 로그를 확인하세요: ./logs/app.log
    pause
    exit /b 1
)

REM 5. 결과 확인
echo.
echo [5/5] 마이그레이션 결과 확인...
python -c "
from temp.neo4j_utils import Neo4jUtils
neo4j = Neo4jUtils()
try:
    project = neo4j.get_project_info('%PROJECT_NAME%')
    if project:
        print(f'✅ 프로젝트 \\'%PROJECT_NAME%\\' Neo4j에서 확인됨')
        print(f'   - 프로젝트 ID: {project[\"project_id\"]}')
        print(f'   - 총 파일 수: {project.get(\"total_files\", \"N/A\")}')
    else:
        print('❌ Neo4j에서 프로젝트를 찾을 수 없습니다')
        exit(1)
finally:
    neo4j.close()
"

echo.
echo ========================================
echo ✅ 마이그레이션 완료!
echo ========================================
echo.
echo 📌 Neo4j Browser에서 확인: http://localhost:7474
echo    로그인: neo4j / password123
echo.
echo 🔍 기본 확인 쿼리:
echo    MATCH (n) RETURN count(n) as total_nodes
echo    MATCH ()-[r]-^>() RETURN count(r) as total_relationships
echo.
echo 📊 호출 체인 확인:
echo    MATCH (p:Project {name: '%PROJECT_NAME%'})
echo    MATCH (p)-[:CONTAINS*]-^>(api:APIEndpoint)
echo    MATCH (api)-[:CALLS]-^>(method:Method)
echo    RETURN api.name, method.name LIMIT 10
echo.
pause
