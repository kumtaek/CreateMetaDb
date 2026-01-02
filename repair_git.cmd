@echo off
setlocal
chcp 65001 > nul
cd /d "%~dp0"

echo [Git 상태 복구 도구]
echo 1. 멈춰있는 Rebase 프로세스 정리 중...
if exist ".git\rebase-merge" (
    echo - Rebase 폴더 발견. Abort 실행...
    git rebase --abort
) else (
    echo - 진행 중인 Rebase 없음.
)

echo.
echo 2. Main 브랜치로 복귀 중...
git checkout main

echo.
echo 3. 서버와 동기화 (Pull) 시도...
git pull origin main --rebase

echo.
echo 복구가 완료되었습니다. 이제 gitcommit.cmd를 다시 실행해 보세요.
pause
