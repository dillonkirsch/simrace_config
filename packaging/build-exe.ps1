# Build the same standalone Windows executable produced by GitHub Actions.
# Output: dist\SimControlsManager.exe and its SHA-256 checksum file.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = if (Test-Path ".venv\Scripts\python.exe") {
    ".venv\Scripts\python.exe"
} else {
    "python"
}

& $python -m pip install --upgrade pip
& $python -m pip install -e ".[build]"

# CI replaces this with the release tag.
Set-Content -Path "src/sim_controls_manager/_buildinfo.py" `
    -Value 'VERSION = "v0.0.0-dev"' -Encoding utf8

& $python -m PyInstaller --noconfirm --clean `
    --onefile --console `
    --name SimControlsManager `
    packaging\launcher.py

$exe = "dist\SimControlsManager.exe"
$checksum = (Get-FileHash $exe -Algorithm SHA256).Hash.ToLower()
"$checksum  SimControlsManager.exe" | Out-File -Encoding ascii "$exe.sha256"

Write-Host ""
Write-Host "Built: $root\$exe"
Write-Host "Checksum: $root\$exe.sha256"
