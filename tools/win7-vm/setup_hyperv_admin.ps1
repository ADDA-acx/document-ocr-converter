$ErrorActionPreference = "Stop"

$logPath = Join-Path $PSScriptRoot "hyperv_setup.log"
$statusPath = Join-Path $PSScriptRoot "hyperv_setup_status.txt"

Start-Transcript -Path $logPath -Force
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "This script must run as administrator."
    }

    Write-Host "Enabling Hyper-V and management tools..."
    $result = Enable-WindowsOptionalFeature `
        -Online `
        -FeatureName Microsoft-Hyper-V `
        -All `
        -NoRestart

    "SUCCESS`nRestartNeeded=$($result.RestartNeeded)`nTime=$(Get-Date -Format o)" |
        Set-Content -LiteralPath $statusPath -Encoding UTF8

    Write-Host "Hyper-V setup completed."
    if ($result.RestartNeeded) {
        Write-Host "A Windows restart is required before creating the VM."
    }
} catch {
    "FAILED`n$($_ | Out-String)`nTime=$(Get-Date -Format o)" |
        Set-Content -LiteralPath $statusPath -Encoding UTF8
    throw
} finally {
    Stop-Transcript
}
