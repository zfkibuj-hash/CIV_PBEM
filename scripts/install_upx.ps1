# Download UPX into tools/upx/ for local PyInstaller builds (no system PATH needed).
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$UpxDir = Join-Path $Root "tools\upx"
$UpxExe = Join-Path $UpxDir "upx.exe"
$Version = "5.0.2"
$ZipName = "upx-$Version-win64.zip"
$Url = "https://github.com/upx/upx/releases/download/v$Version/$ZipName"
$ZipPath = Join-Path $env:TEMP $ZipName

if (Test-Path $UpxExe) {
    Write-Host "[OK] UPX already installed: $UpxExe"
    & $UpxExe --version
    exit 0
}

Write-Host "Downloading UPX $Version..."
New-Item -ItemType Directory -Force -Path $UpxDir | Out-Null
Invoke-WebRequest -Uri $Url -OutFile $ZipPath -UseBasicParsing

$ExtractRoot = Join-Path $env:TEMP "upx-extract-$Version"
if (Test-Path $ExtractRoot) {
    Remove-Item -Recurse -Force $ExtractRoot
}
Expand-Archive -Path $ZipPath -DestinationPath $ExtractRoot -Force

$InnerDir = Get-ChildItem -Path $ExtractRoot -Directory | Select-Object -First 1
if (-not $InnerDir) {
    throw "UPX archive layout unexpected"
}

Copy-Item -Path (Join-Path $InnerDir.FullName "upx.exe") -Destination $UpxExe -Force
Remove-Item -Recurse -Force $ExtractRoot
Remove-Item -Force $ZipPath

Write-Host "[OK] UPX installed to $UpxExe"
& $UpxExe --version
