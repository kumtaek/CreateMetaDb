# 파일 디코딩 스크립트 (Base64)
# 사용법: .\decode_file.ps1 -InputFile "output.txt" -OutputFile "restored.bin"

param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile,
    
    [Parameter(Mandatory=$true)]
    [string]$OutputFile
)

try {
    Write-Host "파일 디코딩 시작: $InputFile" -ForegroundColor Green
    
    # 파일 존재 확인
    if (-not (Test-Path $InputFile)) {
        Write-Host "오류: 입력 파일을 찾을 수 없습니다: $InputFile" -ForegroundColor Red
        exit 1
    }
    
    # Base64 디코딩
    $base64String = [System.IO.File]::ReadAllText($InputFile)
    $fileContent = [System.Convert]::FromBase64String($base64String)
    
    # 결과 저장
    [System.IO.File]::WriteAllBytes($OutputFile, $fileContent)
    
    $fileInfo = Get-Item $OutputFile
    $fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
    
    Write-Host "디코딩 완료: $OutputFile" -ForegroundColor Green
    Write-Host "복원된 파일 크기: $fileSizeMB MB" -ForegroundColor Cyan
    
} catch {
    Write-Host "오류 발생: $_" -ForegroundColor Red
    exit 1
}
