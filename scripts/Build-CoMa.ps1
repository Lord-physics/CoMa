$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location $root
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { python -m venv .venv }
& $python -m pip install --disable-pip-version-check -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar PyInstaller.' }
& $python -m PyInstaller --noconfirm --clean --onefile --windowed --name CoMa main.py
if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación.' }
$releaseDir = Join-Path $root 'dist\CoMa-Windows'
New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $root 'dist\CoMa.exe') -Destination (Join-Path $releaseDir 'CoMa.exe') -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Install-CoMa.ps1') -Destination $releaseDir -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Uninstall-CoMa.ps1') -Destination $releaseDir -Force
Copy-Item -LiteralPath (Join-Path $root 'README.md') -Destination $releaseDir -Force
Compress-Archive -Path (Join-Path $releaseDir '*') -DestinationPath (Join-Path $root 'dist\CoMa-Windows.zip') -Force
Write-Output (Join-Path $root 'dist\CoMa-Windows.zip')
