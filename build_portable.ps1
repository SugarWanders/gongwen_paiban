$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$distPath = Join-Path $projectRoot "dist"
$buildPath = Join-Path $projectRoot "build"

if (Test-Path $distPath) {
    Remove-Item -LiteralPath $distPath -Recurse -Force
}

if (Test-Path $buildPath) {
    Remove-Item -LiteralPath $buildPath -Recurse -Force
}

python -m PyInstaller --noconfirm --clean --distpath dist --workpath build\portable_build portable_build.spec

$exe = Get-ChildItem -Path (Join-Path $projectRoot "dist") -Recurse -Filter *.exe | Select-Object -First 1

Write-Host ""
Write-Host "Portable build completed." -ForegroundColor Green

if ($null -ne $exe) {
    Write-Host $exe.FullName
}
