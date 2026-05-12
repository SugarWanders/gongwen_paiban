$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$distFolderName = "dist_release"
$distPath = Join-Path $projectRoot $distFolderName
$workPath = Join-Path ([System.IO.Path]::GetTempPath()) ("gongwen_paiban_build_" + [guid]::NewGuid().ToString("N"))

if (Test-Path $distPath) {
    Get-ChildItem -Path $distPath -Directory -Filter "*V1_3" | Remove-Item -Recurse -Force
}

try {
    python -m PyInstaller --noconfirm --clean --distpath $distFolderName --workpath $workPath portable_build.spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed with exit code $LASTEXITCODE"
    }

    $appDistPath = Get-ChildItem -Path $distPath -Directory -Filter "*V1_3" | Select-Object -First 1
    if ($null -eq $appDistPath) {
        throw "Portable app directory was not produced under: $distPath"
    }

    $exe = Get-ChildItem -Path $appDistPath.FullName -Filter *.exe | Select-Object -First 1
    if ($null -eq $exe) {
        throw "Portable EXE was not produced: $($appDistPath.FullName)"
    }
}
finally {
    if (Test-Path $workPath) {
        Remove-Item -LiteralPath $workPath -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "Portable build completed." -ForegroundColor Green

Write-Host $exe.FullName
