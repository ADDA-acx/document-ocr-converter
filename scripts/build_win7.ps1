param(
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot

$python = if ($env:WIN7_PYTHON) {
    $env:WIN7_PYTHON
} else {
    Join-Path $repoRoot ".tools\win7-build\python38\python.exe"
}

if (-not (Test-Path $python)) {
    throw "Win7 build Python was not found. Run setup_win7_build.bat first."
}

$runtime = & $python -c "import platform,sys; print('{}.{} {}'.format(sys.version_info[0], sys.version_info[1], platform.architecture()[0]))"
if ($LASTEXITCODE -ne 0 -or $runtime -ne "3.8 64bit") {
    throw "Win7 packages must be built with 64-bit Python 3.8, found: $runtime"
}

Write-Host "Checking source syntax with Python 3.8..."
New-Item -ItemType Directory -Force -Path ".build\win7\pycache" | Out-Null
$env:PYTHONPYCACHEPREFIX = Join-Path $repoRoot ".build\win7\pycache"
Get-ChildItem "src\document_ocr_tool" -Filter *.py | ForEach-Object {
    & $python -m py_compile $_.FullName
}
if ($LASTEXITCODE -ne 0) { throw "Python 3.8 syntax check failed." }

& $python -c "import cv2, fitz, numpy, onnxruntime, openpyxl, pdf2docx, rapidocr_onnxruntime; assert numpy.__version__ == '1.24.4'; assert onnxruntime.__version__ == '1.14.1'"
if ($LASTEXITCODE -ne 0) {
    throw "The Win7 dependency environment is incomplete. Run setup_win7_build.bat again."
}

$asciiName = "DocumentOCRTool"
$workDir = Join-Path $repoRoot ".build\win7"
$distDir = Join-Path $repoRoot ".dist\win7"
$mainScript = Join-Path $repoRoot "src\document_ocr_tool\__main__.py"
$sourceDir = Join-Path $repoRoot "src"
$modelsDir = Join-Path $repoRoot "models"
$assetsDir = Join-Path $repoRoot "assets"
$releaseDir = Join-Path $repoRoot "release"
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
$commonArgs = @(
    "--noconfirm",
    "--clean",
    "--windowed",
    "--noupx",
    "--name", $asciiName,
    "--workpath", $workDir,
    "--distpath", $distDir,
    "--specpath", $workDir,
    "--paths", $sourceDir,
    "--add-data", "$modelsDir;models",
    "--add-data", "$assetsDir;assets",
    "--hidden-import", "rapidocr_onnxruntime",
    "--hidden-import", "onnxruntime",
    "--hidden-import", "cv2",
    "--hidden-import", "numpy",
    "--hidden-import", "PIL",
    "--hidden-import", "fitz",
    "--hidden-import", "docx",
    "--hidden-import", "pdf2docx",
    "--hidden-import", "openpyxl",
    "--hidden-import", "et_xmlfile",
    "--hidden-import", "pkg_resources.extern",
    "--collect-submodules", "pkg_resources",
    "--collect-data", "rapidocr_onnxruntime",
    "--collect-data", "onnxruntime",
    "--collect-binaries", "onnxruntime",
    "--collect-binaries", "cv2",
    "--exclude-module", "scipy",
    "--exclude-module", "pandas",
    "--exclude-module", "matplotlib",
    "--exclude-module", "IPython",
    "--exclude-module", "pytest",
    "--exclude-module", "numpy.tests",
    "--exclude-module", "onnxruntime.tools",
    "--exclude-module", "onnxruntime.transformers"
)
$icon = Join-Path $assetsDir "icon.ico"
if (Test-Path $icon) {
    $commonArgs += @("--icon", $icon)
}

if ($OneFile) {
    Write-Host "Building the Windows 7 onefile package..."
    & $python -m PyInstaller @commonArgs --onefile $mainScript
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller onefile build failed." }

    $source = Join-Path $distDir "$asciiName.exe"
    $target = Join-Path $releaseDir "DocumentOCRTool-Win7-x64.exe"
    Copy-Item -LiteralPath $source -Destination $target -Force
    & $python (Join-Path $PSScriptRoot "check_win7_compat.py") $target
    if ($LASTEXITCODE -ne 0) { throw "The Win7 PE compatibility check failed." }
    Write-Host "Build completed: $target"
} else {
    Write-Host "Building the recommended Windows 7 folder package..."
    & $python -m PyInstaller @commonArgs --onedir $mainScript
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller onedir build failed." }

    $source = Join-Path $distDir $asciiName
    $release = Join-Path $releaseDir "DocumentOCRTool-Win7"
    if (Test-Path $release) {
        Remove-Item -LiteralPath $release -Recurse -Force
    }
    Copy-Item -LiteralPath $source -Destination $release -Recurse
    & $python (Join-Path $PSScriptRoot "check_win7_compat.py") --require-python38 $release
    if ($LASTEXITCODE -ne 0) { throw "The Win7 PE compatibility check failed." }
    Write-Host "Build completed: $release\$asciiName.exe"
    Write-Host "Copy the entire Win7 release folder to the Windows 7 computer."
}
