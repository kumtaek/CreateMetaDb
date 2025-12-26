@echo off
setlocal
chcp 65001

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

:: Add changes (excluding temp and backup directories)
git add . -- ":!temp/" ":!backup/"

:: Commit with the message
git commit -m "%CommitMessage%"

:: Push to main
git push -u origin main

pause
endlocal
