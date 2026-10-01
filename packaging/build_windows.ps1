$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Get-Command python -ErrorAction Stop
$isccCandidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
)
$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $iscc) {
    throw "Inno Setup compiler ISCC.exe was not found."
}

Push-Location $projectRoot
try {
    & $python.Source -m PyInstaller --noconfirm --clean (Join-Path $PSScriptRoot "pacepilot.spec")
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE."
    }

    & $iscc (Join-Path $PSScriptRoot "PacePilot.iss")
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup failed with exit code $LASTEXITCODE."
    }

    $installer = Join-Path $projectRoot "release\PacePilot-1.0.0-Setup.exe"
    if (-not (Test-Path $installer)) {
        throw "Installer output was not created: $installer"
    }

    Get-Item $installer | Select-Object FullName, Length
}
finally {
    Pop-Location
}
