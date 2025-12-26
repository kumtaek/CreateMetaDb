@echo off
setlocal
chcp 437 > nul

:: Check if a commit message was provided as an argument
if "%~1"=="" (
    rem No commit message provided, use current timestamp
    set "CommitMessage=%date%_%time%"
    rem Replace spaces with underscores
    set "CommitMessage=%CommitMessage: =_%"
    rem Replace colons with hyphens
    set "CommitMessage=%CommitMessage::=-%"
) else (
    set "CommitMessage=%*"
)

:: Change to project directory
d:
cd /d "D:\Analyzer\CreateMetaDb"

:: Guard: remove stray reserved-name file if present (causes git add failure)
if exist "\\?\%CD%\nul" del "\\?\%CD%\nul"
git add . -- ":!temp/" ":!backup/"
git commit -m "%CommitMessage%"

:: 3. STEP 2: Sync from Server (Pull after Commit is safer)
echo [2/3] Syncing from Server (Pull Rebase)...
git pull origin main --rebase

:: 4. STEP 3: Uploading to server (Push)
echo [3/3] Uploading to Server (Push)...
git push -u origin main

echo.
echo All Done! Clean and Synced.
pause
endlocal
