@echo off
REM 파일 인코딩 배치 스크립트 (certutil 사용)
REM 사용법: encode_file.bat input.bin output.txt

setlocal

if "%~1"=="" (
    echo 사용법: %~nx0 [입력파일] [출력파일]
    echo 예시: %~nx0 input.bin output.txt
    exit /b 1
)

if "%~2"=="" (
    echo 사용법: %~nx0 [입력파일] [출력파일]
    echo 예시: %~nx0 input.bin output.txt
    exit /b 1
)

set INPUT_FILE=%~1
set OUTPUT_FILE=%~2

if not exist "%INPUT_FILE%" (
    echo 오류: 입력 파일을 찾을 수 없습니다: %INPUT_FILE%
    exit /b 1
)

echo 파일 인코딩 시작: %INPUT_FILE%
certutil -encode "%INPUT_FILE%" "%OUTPUT_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo 인코딩 완료: %OUTPUT_FILE%
) else (
    echo 인코딩 실패
    exit /b 1
)

endlocal
