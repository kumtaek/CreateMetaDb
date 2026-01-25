param(
    [string]$Root = $null,
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

function Resolve-RootPath {
    param(
        [string]$RootArg,
        [string]$ScriptDir
    )

    if ([string]::IsNullOrWhiteSpace($RootArg)) {
        return (Resolve-Path -LiteralPath $ScriptDir).Path
    }

    $candidates = @($RootArg, (Join-Path $ScriptDir $RootArg))
    foreach ($candidate in $candidates) {
        try {
            if (Test-Path -LiteralPath $candidate) {
                return (Resolve-Path -LiteralPath $candidate).Path
            }
        } catch {
            continue
        }
    }

    throw "Root path not found (or invalid): $RootArg (script_dir=$ScriptDir)"
}

$Root = Resolve-RootPath -RootArg $Root -ScriptDir $PSScriptRoot

function Get-Utf8TextAndBomState {
    param([byte[]]$Bytes)

    $hasBom = $Bytes.Length -ge 3 -and $Bytes[0] -eq 0xEF -and $Bytes[1] -eq 0xBB -and $Bytes[2] -eq 0xBF
    $offset = if ($hasBom) { 3 } else { 0 }
    $text = [System.Text.Encoding]::UTF8.GetString($Bytes, $offset, $Bytes.Length - $offset)

    return [pscustomobject]@{
        HasBom = $hasBom
        Text   = $text
    }
}

function To-BytesUtf8WithOptionalBom {
    param(
        [string]$Text,
        [bool]$HasBom
    )

    $payload = [System.Text.Encoding]::UTF8.GetBytes($Text)
    if (-not $HasBom) {
        return $payload
    }

    $bom = [byte[]](0xEF, 0xBB, 0xBF)
    $out = New-Object byte[] ($bom.Length + $payload.Length)
    [System.Array]::Copy($bom, 0, $out, 0, $bom.Length)
    [System.Array]::Copy($payload, 0, $out, $bom.Length, $payload.Length)
    return $out
}

$mdFiles = Get-ChildItem -LiteralPath $Root -Recurse -File -Filter *.md
$changed = 0

foreach ($file in $mdFiles) {
    $path = $file.FullName
    $bytes = [System.IO.File]::ReadAllBytes($path)
    $decoded = Get-Utf8TextAndBomState -Bytes $bytes

    $normalized = $decoded.Text
    $normalized = $normalized -replace "`r`n", "`n"
    $normalized = $normalized -replace "`r", "`n"
    $normalized = $normalized -replace "`n", "`r`n"

    $outBytes = To-BytesUtf8WithOptionalBom -Text $normalized -HasBom $decoded.HasBom

    $isDifferent = $bytes.Length -ne $outBytes.Length
    if (-not $isDifferent) {
        for ($i = 0; $i -lt $bytes.Length; $i++) {
            if ($bytes[$i] -ne $outBytes[$i]) {
                $isDifferent = $true
                break
            }
        }
    }

    if ($isDifferent) {
        if (-not $WhatIf) {
            [System.IO.File]::WriteAllBytes($path, $outBytes)
        }
        $changed++
        Write-Host ("CRLF normalized: {0}" -f (Resolve-Path -LiteralPath $path))
    }
}

Write-Host ("Done. Normalized CRLF in {0} file(s) under {1}" -f $changed, (Resolve-Path -LiteralPath $Root))
