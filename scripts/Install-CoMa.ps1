param([switch]$NoLaunch)
$ErrorActionPreference = 'Stop'
$sourceExe = Join-Path $PSScriptRoot 'CoMa.exe'
if (-not (Test-Path -LiteralPath $sourceExe -PathType Leaf)) { throw 'Falta CoMa.exe junto al instalador.' }
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\CoMa'
$exePath = Join-Path $installDir 'CoMa.exe'
$isUpdate = Test-Path -LiteralPath $exePath -PathType Leaf
$running = @(Get-Process -Name CoMa -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -and [string]::Equals($_.Path, $exePath, [StringComparison]::OrdinalIgnoreCase)
})
if ($running.Count -gt 0) { throw 'Cierra CoMa antes de instalar o actualizar.' }
$uninstallSource = Join-Path $PSScriptRoot 'Uninstall-CoMa.ps1'
New-Item -ItemType Directory -Path $installDir -Force | Out-Null
Copy-Item -LiteralPath $sourceExe -Destination $exePath -Force
Copy-Item -LiteralPath $uninstallSource -Destination (Join-Path $installDir 'Uninstall-CoMa.ps1') -Force
$startMenu = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
$shortcutPath = Join-Path $startMenu 'CoMa.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = $installDir
$shortcut.Description = 'CoMa: correo no leído y posible spam'
$shortcut.Save()
if (-not $isUpdate) {
    $runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
    New-Item -Path $runKey -Force | Out-Null
    New-ItemProperty -Path $runKey -Name CoMa -PropertyType String -Value ('"' + $exePath + '"') -Force | Out-Null
}
Write-Output "CoMa instalado o actualizado para el usuario actual: $exePath"
if (-not $NoLaunch) { Start-Process -FilePath $exePath }
