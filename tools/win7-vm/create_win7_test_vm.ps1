param(
    [Parameter(Mandatory = $true)]
    [string]$IsoPath
)

$ErrorActionPreference = "Stop"

$vmName = "PDF2WORD-Win7-SP1"
$vmRoot = "D:\VirtualMachines\$vmName"
$vhdPath = Join-Path $vmRoot "$vmName.vhdx"
$switchName = "Default Switch"

if (-not (Test-Path -LiteralPath $IsoPath -PathType Leaf)) {
    throw "ISO not found: $IsoPath"
}

Import-Module Hyper-V

if (-not (Get-VMSwitch -Name $switchName -ErrorAction SilentlyContinue)) {
    $switchName = (Get-VMSwitch | Select-Object -First 1 -ExpandProperty Name)
}
if (-not $switchName) {
    throw "No Hyper-V virtual switch is available."
}

New-Item -ItemType Directory -Force -Path $vmRoot | Out-Null

if (-not (Get-VM -Name $vmName -ErrorAction SilentlyContinue)) {
    New-VM `
        -Name $vmName `
        -Generation 1 `
        -MemoryStartupBytes 4GB `
        -NewVHDPath $vhdPath `
        -NewVHDSizeBytes 50GB `
        -SwitchName $switchName | Out-Null

    Set-VMProcessor -VMName $vmName -Count 2
    Set-VMMemory -VMName $vmName -DynamicMemoryEnabled $false
    Set-VM -Name $vmName -AutomaticCheckpointsEnabled $false
}

$dvd = Get-VMDvdDrive -VMName $vmName -ErrorAction SilentlyContinue
if (-not $dvd) {
    Add-VMDvdDrive -VMName $vmName -Path $IsoPath | Out-Null
    $dvd = Get-VMDvdDrive -VMName $vmName
} else {
    Set-VMDvdDrive -VMName $vmName -Path $IsoPath
    $dvd = Get-VMDvdDrive -VMName $vmName
}

$disk = Get-VMHardDiskDrive -VMName $vmName | Select-Object -First 1
Set-VMBios -VMName $vmName -StartupOrder @($dvd, $disk)

Checkpoint-VM -Name $vmName -SnapshotName "Before-Win7-install"
Start-VM -Name $vmName | Out-Null
vmconnect.exe localhost $vmName
