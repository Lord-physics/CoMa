param([switch]$NoLaunch)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$api = 'https://api.github.com/repos/Lord-physics/CoMa/releases/latest'
$headers = @{ Accept = 'application/vnd.github+json'; 'User-Agent' = 'CoMa-Updater' }

try {
    $release = Invoke-RestMethod -Uri $api -Headers $headers
} catch {
    throw 'No se pudo consultar la última versión publicada de CoMa en GitHub.'
}

$asset = @($release.assets | Where-Object { $_.name -eq 'CoMa-Windows.zip' -and $_.state -eq 'uploaded' }) | Select-Object -First 1
if (-not $asset) { throw 'La última versión de CoMa no contiene CoMa-Windows.zip.' }
if ($asset.digest -notmatch '^sha256:[a-fA-F0-9]{64}$') {
    throw 'GitHub no proporcionó una huella SHA-256 válida para la descarga.'
}
$download = [Uri]$asset.browser_download_url
if ($download.Scheme -ne 'https' -or $download.Host -ne 'github.com' -or
    -not $download.AbsolutePath.StartsWith('/Lord-physics/CoMa/releases/download/', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'La dirección del archivo publicado no es válida.'
}

$temporary = Join-Path ([IO.Path]::GetTempPath()) ('CoMa-update-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temporary | Out-Null
try {
    $zip = Join-Path $temporary 'CoMa-Windows.zip'
    $package = Join-Path $temporary 'package'
    Write-Output "Descargando CoMa $($release.tag_name)..."
    Invoke-WebRequest -Uri $download.AbsoluteUri -OutFile $zip -UseBasicParsing
    $actual = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash
    $expected = $asset.digest.Substring(7)
    if (-not [string]::Equals($actual, $expected, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'La descarga no coincide con la huella SHA-256 publicada por GitHub.'
    }
    Expand-Archive -LiteralPath $zip -DestinationPath $package
    $installer = Join-Path $package 'Install-CoMa.ps1'
    if (-not (Test-Path -LiteralPath $installer -PathType Leaf) -or
        -not (Test-Path -LiteralPath (Join-Path $package 'CoMa.exe') -PathType Leaf)) {
        throw 'El paquete descargado no contiene el instalador de CoMa.'
    }
    & $installer -NoLaunch:$NoLaunch
} finally {
    if (Test-Path -LiteralPath $temporary) {
        Remove-Item -LiteralPath $temporary -Recurse -Force
    }
}
