@echo off
setlocal

:: Check if a commit message was provided as an argument
if "%~1"=="" (
    set /p "CommitMessage=Enter commit message: "
) else (
    set "CommitMessage=%*"
)

:: If still empty, exit
if "%CommitMessage%"=="" (
    echo Error: Commit message is required.
    pause
    exit /b 1
)

d:
cd D:\Analyzer\CreateMetaDb

:: Add changes (excluding temp and backup directories using double quotes for Windows CMD)
git add . -- ":!temp/"

:: Commit with the message
git commit -m "%CommitMessage%"

:: Push to main
git push -u origin main

pause
endlocal