# 대용량 파일 디코딩 스크립트 (청크 단위 처리)
# 사용법: .\decode_large_file.ps1 -InputFile "output.txt" -OutputFile "restored.zip"

param(
    [Parameter(Mandatory = $true)]
    [string]$InputFile,
    
    [Parameter(Mandatory = $true)]
    [string]$OutputFile
)

try {
    Write-Host "대용량 파일 디코딩 시작: $InputFile" -ForegroundColor Green
    
    # 파일 존재 확인
    if (-not (Test-Path $InputFile)) {
        Write-Host "오류: 입력 파일을 찾을 수 없습니다: $InputFile" -ForegroundColor Red
        exit 1
    }
    
    # 파일 크기 확인
    $fileInfo = Get-Item $InputFile
    $fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
    Write-Host "파일 크기: $fileSizeMB MB" -ForegroundColor Cyan
    
    Write-Host "Base64 디코딩 중..." -ForegroundColor Cyan
    
    # Base64 문자열 읽기
    $base64String = [System.IO.File]::ReadAllText($InputFile)
    
    # 디코딩
    $fileContent = [System.Convert]::FromBase64String($base64String)
    
    # 파일 저장
    [System.IO.File]::WriteAllBytes($OutputFile, $fileContent)
    
    # 결과 확인
    $outputInfo = Get-Item $OutputFile
    $outputSizeMB = [math]::Round($outputInfo.Length / 1MB, 2)
    
    Write-Host "`n디코딩 완료!" -ForegroundColor Green
    Write-Host "  입력 파일: $InputFile ($fileSizeMB MB)" -ForegroundColor Cyan
    Write-Host "  출력 파일: $OutputFile ($outputSizeMB MB)" -ForegroundColor Cyan
    
}
catch {
    Write-Host "오류 발생: $_" -ForegroundColor Red
    Write-Host $_.Exception.StackTrace -ForegroundColor Red
    exit 1
}
