$ErrorActionPreference = 'Stop'
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\CoMa'
$expected = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs\CoMa'))
$resolved = [IO.Path]::GetFullPath($installDir)
if (-not [string]::Equals($resolved, $expected, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Ruta de desinstalación no válida.'
}
$runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
if (Test-Path $runKey) {
    $current = (Get-ItemProperty -Path $runKey -Name CoMa -ErrorAction SilentlyContinue).CoMa
    if ($current -eq ('"' + (Join-Path $resolved 'CoMa.exe') + '"')) {
        Remove-ItemProperty -Path $runKey -Name CoMa
    }
}
$shortcutPath = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\CoMa.lnk'
if (Test-Path -LiteralPath $shortcutPath) { Remove-Item -LiteralPath $shortcutPath -Force }
if (Test-Path -LiteralPath $resolved) {
    # El ejecutable puede estar abierto; ciérralo antes de desinstalar.
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
Write-Output 'CoMa desinstalado. Los datos locales se conservan para una posible reinstalación.'
