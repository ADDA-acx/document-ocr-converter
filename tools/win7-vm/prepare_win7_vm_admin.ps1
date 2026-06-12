$ErrorActionPreference = "Stop"

$workspace = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$vmName = "PDF2WORD-Win7-SP1"
$vmRoot = "D:\VirtualMachines\$vmName"
$systemVhd = Join-Path $vmRoot "$vmName-System.vhdx"
$testVhd = Join-Path $vmRoot "$vmName-TestData.vhdx"
$statusPath = Join-Path $PSScriptRoot "win7_vm_prepare_status.txt"
$logPath = Join-Path $PSScriptRoot "win7_vm_prepare.log"

Start-Transcript -Path $logPath -Force
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "This script must run as administrator."
    }

    Import-Module Hyper-V
    New-Item -ItemType Directory -Force -Path $vmRoot | Out-Null

    $switch = Get-VMSwitch -Name "Default Switch" -ErrorAction SilentlyContinue
    if (-not $switch) {
        $switch = Get-VMSwitch | Select-Object -First 1
    }

    if (-not (Get-VM -Name $vmName -ErrorAction SilentlyContinue)) {
        $newVmArgs = @{
            Name = $vmName
            Generation = 1
            MemoryStartupBytes = 4GB
            NewVHDPath = $systemVhd
            NewVHDSizeBytes = 50GB
            Path = $vmRoot
        }
        if ($switch) {
            $newVmArgs.SwitchName = $switch.Name
        }
        New-VM @newVmArgs | Out-Null
        Set-VMProcessor -VMName $vmName -Count 2
        Set-VMMemory -VMName $vmName -DynamicMemoryEnabled $false
        Set-VM -Name $vmName -AutomaticCheckpointsEnabled $false
    }

    $vm = Get-VM -Name $vmName
    if ($vm.State -ne "Off") {
        Stop-VM -Name $vmName -TurnOff -Force
    }

    if (-not (Test-Path -LiteralPath $testVhd)) {
        New-VHD -Path $testVhd -Dynamic -SizeBytes 8GB | Out-Null
        $mounted = Mount-VHD -Path $testVhd -Passthru
        try {
            $disk = $mounted | Get-Disk
            Initialize-Disk -Number $disk.Number -PartitionStyle MBR
            $partition = New-Partition -DiskNumber $disk.Number -UseMaximumSize -AssignDriveLetter
            $volume = Format-Volume `
                -Partition $partition `
                -FileSystem NTFS `
                -NewFileSystemLabel "PDF2WORD_TEST" `
                -Confirm:$false
            $drive = "$($volume.DriveLetter):\"

            New-Item -ItemType Directory -Force -Path (Join-Path $drive "folder") | Out-Null
            New-Item -ItemType Directory -Force -Path (Join-Path $drive "onefile") | Out-Null
            New-Item -ItemType Directory -Force -Path (Join-Path $drive "samples") | Out-Null

            Copy-Item `
                -Path (Join-Path $workspace "release\DocumentOCRTool-Win7\*") `
                -Destination (Join-Path $drive "folder") `
                -Recurse `
                -Force
            Copy-Item `
                -LiteralPath (Join-Path $workspace "release\DocumentOCRTool-Win7-x64.exe") `
                -Destination (Join-Path $drive "onefile") `
                -Force
            Copy-Item `
                -Path (Join-Path $workspace "tools\win7-vm\assets\*") `
                -Destination (Join-Path $drive "samples") `
                -Recurse `
                -Force
        } finally {
            Dismount-VHD -Path $testVhd
        }
    }

    $alreadyAttached = Get-VMHardDiskDrive -VMName $vmName |
        Where-Object { $_.Path -eq $testVhd }
    if (-not $alreadyAttached) {
        Add-VMHardDiskDrive -VMName $vmName -ControllerType IDE -ControllerNumber 0 -ControllerLocation 1 -Path $testVhd
    }

    if (-not (Get-VMDvdDrive -VMName $vmName -ErrorAction SilentlyContinue)) {
        Add-VMDvdDrive -VMName $vmName | Out-Null
    }

    if (-not (Get-LocalGroupMember -Group "Hyper-V Administrators" -Member $env:USERNAME -ErrorAction SilentlyContinue)) {
        Add-LocalGroupMember -Group "Hyper-V Administrators" -Member $env:USERNAME
    }

    Checkpoint-VM -Name $vmName -SnapshotName "Empty-VM-before-Win7-install"

    @(
        "SUCCESS"
        "VMName=$vmName"
        "VMRoot=$vmRoot"
        "SystemVHD=$systemVhd"
        "TestVHD=$testVhd"
        "Switch=$($switch.Name)"
        "Time=$(Get-Date -Format o)"
    ) | Set-Content -LiteralPath $statusPath -Encoding UTF8
} catch {
    @(
        "FAILED"
        ($_ | Out-String)
        "Time=$(Get-Date -Format o)"
    ) | Set-Content -LiteralPath $statusPath -Encoding UTF8
    throw
} finally {
    Stop-Transcript
}
