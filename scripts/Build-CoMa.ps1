$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location $root
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { python -m venv .venv }
& $python -m pip install --disable-pip-version-check -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar PyInstaller.' }
& $python -m PyInstaller --noconfirm --clean --onefile --windowed --name CoMa --icon (Join-Path $root 'coma\assets\CoMa.ico') --add-data "$(Join-Path $root 'coma\assets\logo.png');coma\assets" main.py
if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación.' }
$releaseDir = Join-Path $root 'dist\CoMa-Windows'
New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $root 'dist\CoMa.exe') -Destination (Join-Path $releaseDir 'CoMa.exe') -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Install-CoMa.ps1') -Destination $releaseDir -Force
Copy-Item -LiteralPath (Join-Path $root 'actualizar.ps1') -Destination $releaseDir -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Uninstall-CoMa.ps1') -Destination $releaseDir -Force
Copy-Item -LiteralPath (Join-Path $root 'README.md') -Destination $releaseDir -Force
Copy-Item -LiteralPath (Join-Path $root 'LEEME.md') -Destination $releaseDir -Force
$oauthConfig = Join-Path $root 'oauth-clients.json'
if (Test-Path -LiteralPath $oauthConfig -PathType Leaf) {
    $registrations = Get-Content -LiteralPath $oauthConfig -Raw | ConvertFrom-Json
    if ($registrations.gmail.client_id -notmatch '^[A-Za-z0-9_-]+\.apps\.googleusercontent\.com$' -or
        $registrations.microsoft.client_id -notmatch '^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$') {
        throw 'oauth-clients.json no contiene IDs OAuth válidos para Gmail y Microsoft.'
    }
    Copy-Item -LiteralPath $oauthConfig -Destination $releaseDir -Force
} else {
    $oldConfig = Join-Path $releaseDir 'oauth-clients.json'
    if (Test-Path -LiteralPath $oldConfig -PathType Leaf) { Remove-Item -LiteralPath $oldConfig -Force }
}
Compress-Archive -Path (Join-Path $releaseDir '*') -DestinationPath (Join-Path $root 'dist\CoMa-Windows.zip') -Force
Write-Output (Join-Path $root 'dist\CoMa-Windows.zip')
