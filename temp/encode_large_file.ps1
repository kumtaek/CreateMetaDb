# 대용량 파일 인코딩 스크립트 (청크 단위 처리)
# 사용법: .\encode_large_file.ps1 -InputFile "large.zip" -OutputFile "output.txt"

param(
    [Parameter(Mandatory = $true)]
    [string]$InputFile,
    
    [Parameter(Mandatory = $true)]
    [string]$OutputFile,
    
    [int]$ChunkSizeKB = 1024  # 1MB 청크
)

try {
    Write-Host "대용량 파일 인코딩 시작: $InputFile" -ForegroundColor Green
    
    # 파일 존재 확인
    if (-not (Test-Path $InputFile)) {
        Write-Host "오류: 입력 파일을 찾을 수 없습니다: $InputFile" -ForegroundColor Red
        exit 1
    }
    
    # 파일 크기 확인
    $fileInfo = Get-Item $InputFile
    $fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
    Write-Host "파일 크기: $fileSizeMB MB" -ForegroundColor Cyan
    
    # 출력 파일 초기화
    if (Test-Path $OutputFile) {
        Remove-Item $OutputFile -Force
    }
    
    # 청크 크기 (바이트)
    $chunkSize = $ChunkSizeKB * 1024
    $buffer = New-Object byte[] $chunkSize
    
    # 파일 스트림 열기
    $inputStream = [System.IO.File]::OpenRead($InputFile)
    $outputWriter = [System.IO.StreamWriter]::new($OutputFile)
    
    $totalBytes = $inputStream.Length
    $bytesRead = 0
    $chunkCount = 0
    
    Write-Host "청크 단위 인코딩 시작 (청크 크기: $ChunkSizeKB KB)..." -ForegroundColor Cyan
    
    # 청크 단위로 읽고 인코딩
    while (($read = $inputStream.Read($buffer, 0, $chunkSize)) -gt 0) {
        $chunkCount++
        $bytesRead += $read
        
        # 실제 읽은 크기만큼 배열 생성
        $actualBuffer = New-Object byte[] $read
        [Array]::Copy($buffer, $actualBuffer, $read)
        
        # Base64 인코딩
        $base64Chunk = [System.Convert]::ToBase64String($actualBuffer)
        $outputWriter.Write($base64Chunk)
        
        # 진행률 표시
        $progress = [math]::Round(($bytesRead / $totalBytes) * 100, 1)
        Write-Progress -Activity "파일 인코딩 중" -Status "$progress% 완료" -PercentComplete $progress
    }
    
    # 스트림 닫기
    $inputStream.Close()
    $outputWriter.Close()
    
    Write-Progress -Activity "파일 인코딩 중" -Completed
    
    # 결과 확인
    $outputInfo = Get-Item $OutputFile
    $outputSizeMB = [math]::Round($outputInfo.Length / 1MB, 2)
    
    Write-Host "`n인코딩 완료!" -ForegroundColor Green
    Write-Host "  입력 파일: $InputFile ($fileSizeMB MB)" -ForegroundColor Cyan
    Write-Host "  출력 파일: $OutputFile ($outputSizeMB MB)" -ForegroundColor Cyan
    Write-Host "  처리된 청크: $chunkCount 개" -ForegroundColor Cyan
    
}
catch {
    Write-Host "오류 발생: $_" -ForegroundColor Red
    Write-Host $_.Exception.StackTrace -ForegroundColor Red
    exit 1
}
finally {
    if ($inputStream) { $inputStream.Dispose() }
    if ($outputWriter) { $outputWriter.Dispose() }
}
