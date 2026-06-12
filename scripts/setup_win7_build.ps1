$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot

$toolsDir = Join-Path $repoRoot ".tools\win7-build"
$pythonDir = Join-Path $toolsDir "python38"
$pythonExe = Join-Path $pythonDir "python.exe"
$installer = Join-Path $toolsDir "python-3.8.10-amd64.exe"
$downloadUrl = "https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe"

New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null

if (-not (Test-Path $pythonExe)) {
    Write-Host "Downloading the official Python 3.8.10 x64 installer..."
    Invoke-WebRequest -Uri $downloadUrl -OutFile $installer

    Write-Host "Installing an isolated build interpreter..."
    $arguments = @(
        "/quiet",
        "InstallAllUsers=0",
        "TargetDir=$pythonDir",
        "Include_launcher=0",
        "Include_test=0",
        "Include_doc=0",
        "Include_debug=0",
        "Include_symbols=0",
        "PrependPath=0",
        "Shortcuts=0"
    )
    $process = Start-Process -FilePath $installer -ArgumentList $arguments -Wait -PassThru
    if ($process.ExitCode -ne 0 -or -not (Test-Path $pythonExe)) {
        throw "Python 3.8.10 installation failed with exit code $($process.ExitCode)."
    }
}

$version = & $pythonExe -c "import platform,sys; print(platform.architecture()[0], sys.version.split()[0])"
if ($LASTEXITCODE -ne 0 -or $version -ne "64bit 3.8.10") {
    throw "The Win7 build interpreter is invalid: $version"
}

Write-Host "Installing the frozen Windows 7 dependency set..."
& $pythonExe -m pip install --upgrade "pip==24.0" "setuptools==65.5.1" "wheel==0.43.0"
if ($LASTEXITCODE -ne 0) { throw "Failed to prepare pip." }

& $pythonExe -m pip install --upgrade --force-reinstall -r (Join-Path $repoRoot "requirements-win7.txt")
if ($LASTEXITCODE -ne 0) { throw "Failed to install Win7 dependencies." }

& $pythonExe -m pip install --upgrade --force-reinstall --no-deps "rapidocr-onnxruntime==1.3.24"
if ($LASTEXITCODE -ne 0) { throw "Failed to install RapidOCR." }

Write-Host ""
Write-Host "Windows 7 build environment is ready:"
Write-Host "  $pythonExe"
Write-Host "Run scripts\build-win7-folder.bat for the folder release."
