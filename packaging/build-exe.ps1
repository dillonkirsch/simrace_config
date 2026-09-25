# Build the same standalone Windows executable produced by GitHub Actions.
# Output: the windowed app, optional CLI, and SHA-256 checksum files.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Invoke-CheckedPython {
    param([string[]] $PythonArguments)

    & $script:python @PythonArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE`: python $($PythonArguments -join ' ')"
    }
}

$systemPython = (Get-Command python -ErrorAction Stop).Source
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "Creating isolated build environment: $root\.venv"
    & $systemPython -m venv (Join-Path $root ".venv")
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the build environment (exit code $LASTEXITCODE)."
    }
}
$python = $venvPython

Invoke-CheckedPython @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")
Invoke-CheckedPython @("-m", "pip", "install", "-e", ".[build]")

# CI replaces this with the release tag.
Set-Content -Path "src/sim_controls_manager/_buildinfo.py" `
    -Value 'VERSION = "v0.0.0-dev"' -Encoding utf8

$exe = "dist\SimControlsManager.exe"
$cliExe = "dist\SimControlsManagerCLI.exe"
$icon = Join-Path $root "packaging\assets\sim-controls-manager.ico"
if (-not (Test-Path -LiteralPath $icon)) {
    throw "Application icon not found: $icon"
}
$pyInstallerWork = Join-Path $root ("build\pyinstaller-" + [guid]::NewGuid().ToString("N"))
if (Test-Path -LiteralPath $exe) {
    Remove-Item -LiteralPath $exe -Force
}
if (Test-Path -LiteralPath "$exe.sha256") {
    Remove-Item -LiteralPath "$exe.sha256" -Force
}
if (Test-Path -LiteralPath $cliExe) {
    Remove-Item -LiteralPath $cliExe -Force
}
if (Test-Path -LiteralPath "$cliExe.sha256") {
    Remove-Item -LiteralPath "$cliExe.sha256" -Force
}

Invoke-CheckedPython @(
    "-m", "PyInstaller",
    "--noconfirm", "--clean",
    "--onefile", "--windowed",
    "--name", "SimControlsManager",
    "--icon", $icon,
    "--paths", "src",
    "--workpath", $pyInstallerWork,
    "--specpath", $pyInstallerWork,
    "--distpath", "dist",
    "packaging\launcher.py"
)

Invoke-CheckedPython @(
    "-m", "PyInstaller",
    "--noconfirm", "--clean",
    "--onefile", "--console",
    "--name", "SimControlsManagerCLI",
    "--icon", $icon,
    "--paths", "src",
    "--workpath", ($pyInstallerWork + "-cli"),
    "--specpath", ($pyInstallerWork + "-cli"),
    "--distpath", "dist",
    "packaging\cli_launcher.py"
)

if (-not (Test-Path -LiteralPath $exe)) {
    throw "PyInstaller exited successfully but did not create $exe."
}
if (-not (Test-Path -LiteralPath $cliExe)) {
    throw "PyInstaller exited successfully but did not create $cliExe."
}

# The GUI executable uses the Windows subsystem and intentionally has no console.
# Build its widget tree once so layout errors fail the build instead of the user.
$guiProcess = Start-Process -FilePath $exe -ArgumentList "--smoke-test" `
    -WindowStyle Hidden -Wait -PassThru
if ($guiProcess.ExitCode -ne 0) {
    throw "The GUI executable failed its startup smoke test (exit code $($guiProcess.ExitCode))."
}

# Smoke-test the separate console entry point.
& $cliExe --version
if ($LASTEXITCODE -ne 0) {
    throw "The CLI executable failed its smoke test (exit code $LASTEXITCODE)."
}

$checksum = (Get-FileHash $exe -Algorithm SHA256).Hash.ToLower()
"$checksum  SimControlsManager.exe" | Out-File -Encoding ascii "$exe.sha256"
$cliChecksum = (Get-FileHash $cliExe -Algorithm SHA256).Hash.ToLower()
"$cliChecksum  SimControlsManagerCLI.exe" | Out-File -Encoding ascii "$cliExe.sha256"

Write-Host ""
Write-Host "Built: $root\$exe"
Write-Host "Checksum: $root\$exe.sha256"
Write-Host "Built: $root\$cliExe"
Write-Host "Checksum: $root\$cliExe.sha256"
