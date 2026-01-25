@echo off
setlocal
REM Run relative to this script location (works after copying).
powershell -ExecutionPolicy Bypass -File "%~dp0normalize_doc_md_crlf.ps1" -Root "%~dp0."
pause
