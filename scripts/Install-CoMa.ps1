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
$updateSource = Join-Path $PSScriptRoot 'actualizar.ps1'
$oauthSource = Join-Path $PSScriptRoot 'oauth-clients.json'
New-Item -ItemType Directory -Path $installDir -Force | Out-Null
$targets = @('CoMa.exe', 'Uninstall-CoMa.ps1', 'actualizar.ps1')
if (Test-Path -LiteralPath $oauthSource -PathType Leaf) { $targets += 'oauth-clients.json' }
$backups = @{}
$previous = @{}
$suffix = [Guid]::NewGuid().ToString('N')
$copiesStarted = $false
try {
    foreach ($name in $targets) {
        $destination = Join-Path $installDir $name
        $previous[$name] = Test-Path -LiteralPath $destination -PathType Leaf
        if ($previous[$name]) {
            $backup = Join-Path $installDir ($name + '.backup-' + $suffix)
            Copy-Item -LiteralPath $destination -Destination $backup
            $backups[$name] = $backup
        }
    }
    $copiesStarted = $true
    Copy-Item -LiteralPath $sourceExe -Destination $exePath -Force
    Copy-Item -LiteralPath $uninstallSource -Destination (Join-Path $installDir 'Uninstall-CoMa.ps1') -Force
    if (Test-Path -LiteralPath $updateSource -PathType Leaf) {
        Copy-Item -LiteralPath $updateSource -Destination (Join-Path $installDir 'actualizar.ps1') -Force
    }
    if (Test-Path -LiteralPath $oauthSource -PathType Leaf) {
        Copy-Item -LiteralPath $oauthSource -Destination (Join-Path $installDir 'oauth-clients.json') -Force
    }
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
} catch {
    $reason = $_.Exception.Message
    $restoreErrors = @()
    if ($copiesStarted) {
        foreach ($name in $targets) {
            $destination = Join-Path $installDir $name
            try {
                if ($previous[$name]) {
                    Copy-Item -LiteralPath $backups[$name] -Destination $destination -Force
                } elseif (Test-Path -LiteralPath $destination -PathType Leaf) {
                    Remove-Item -LiteralPath $destination -Force
                }
            } catch { $restoreErrors += $name }
        }
    }
    if ($restoreErrors.Count -gt 0) {
        throw "La instalación falló ($reason) y no se pudieron restaurar: $($restoreErrors -join ', ')."
    }
    throw
} finally {
    foreach ($backup in $backups.Values) {
        if (Test-Path -LiteralPath $backup -PathType Leaf) {
            try { Remove-Item -LiteralPath $backup -Force } catch { }
        }
    }
}
