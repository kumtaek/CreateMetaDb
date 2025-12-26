# 파일 인코딩 스크립트 (Base64)
# 사용법: .\encode_file.ps1 -InputFile "input.bin" -OutputFile "output.txt"

param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile,
    
    [Parameter(Mandatory=$true)]
    [string]$OutputFile
)

try {
    Write-Host "파일 인코딩 시작: $InputFile" -ForegroundColor Green
    
    # 파일 존재 확인
    if (-not (Test-Path $InputFile)) {
        Write-Host "오류: 입력 파일을 찾을 수 없습니다: $InputFile" -ForegroundColor Red
        exit 1
    }
    
    # 파일 크기 확인
    $fileInfo = Get-Item $InputFile
    $fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
    Write-Host "파일 크기: $fileSizeMB MB" -ForegroundColor Cyan
    
    # Base64 인코딩
    $fileContent = [System.IO.File]::ReadAllBytes($InputFile)
    $base64String = [System.Convert]::ToBase64String($fileContent)
    
    # 결과 저장
    [System.IO.File]::WriteAllText($OutputFile, $base64String)
    
    Write-Host "인코딩 완료: $OutputFile" -ForegroundColor Green
    Write-Host "인코딩된 크기: $([math]::Round($base64String.Length / 1MB, 2)) MB" -ForegroundColor Cyan
    
} catch {
    Write-Host "오류 발생: $_" -ForegroundColor Red
    exit 1
}
