param(
    [switch]$NoLaunch,
    [string]$PackagePath,
    [string]$ExpectedHash,
    [int]$WaitForProcessId = 0,
    [switch]$FromApp
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
$temporary = $null
$ownedPackageDir = $null

function Remove-CoMaTempDirectory([string]$path) {
    if (-not $path -or -not (Test-Path -LiteralPath $path)) { return }
    $full = [IO.Path]::GetFullPath($path).TrimEnd('\')
    $parent = [IO.Path]::GetDirectoryName($full).TrimEnd('\')
    $name = [IO.Path]::GetFileName($full)
    if (-not [string]::Equals($parent, $tempRoot, [StringComparison]::OrdinalIgnoreCase) -or
        $name -notmatch '^CoMa-update-[0-9a-f]{32}$') { return }
    $item = Get-Item -LiteralPath $full -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { return }
    Remove-Item -LiteralPath $full -Recurse -Force
}

try {
    if ($WaitForProcessId -gt 0) {
        $running = Get-Process -Id $WaitForProcessId -ErrorAction SilentlyContinue
        if ($running) {
            try { Wait-Process -Id $WaitForProcessId -Timeout 120 -ErrorAction Stop }
            catch {
                if (Get-Process -Id $WaitForProcessId -ErrorAction SilentlyContinue) {
                    throw 'CoMa no se cerró a tiempo para instalar la actualización.'
                }
            }
        }
    }

    if ($PackagePath) {
        if ($ExpectedHash -notmatch '^[a-fA-F0-9]{64}$') {
            throw 'La huella SHA-256 recibida no es válida.'
        }
        $sourceZip = [IO.Path]::GetFullPath($PackagePath)
        $ownedPackageDir = [IO.Path]::GetDirectoryName($sourceZip)
        if ([IO.Path]::GetFileName($sourceZip) -ne 'CoMa-Windows.zip' -or
            [IO.Path]::GetFileName($ownedPackageDir) -notmatch '^CoMa-update-[0-9a-f]{32}$' -or
            -not [string]::Equals([IO.Path]::GetDirectoryName($ownedPackageDir).TrimEnd('\'), $tempRoot,
                                  [StringComparison]::OrdinalIgnoreCase) -or
            -not (Test-Path -LiteralPath $sourceZip -PathType Leaf)) {
            throw 'El paquete temporal de CoMa no es válido.'
        }
        $expected = $ExpectedHash
    } else {
        $api = 'https://api.github.com/repos/Lord-physics/CoMa/releases/latest'
        $headers = @{ Accept = 'application/vnd.github+json'; 'User-Agent' = 'CoMa-Updater' }
        try { $release = Invoke-RestMethod -Uri $api -Headers $headers }
        catch { throw 'No se pudo consultar la última versión publicada de CoMa en GitHub.' }
        $asset = @($release.assets | Where-Object { $_.name -eq 'CoMa-Windows.zip' -and $_.state -eq 'uploaded' }) | Select-Object -First 1
        if (-not $asset) { throw 'La última versión de CoMa no contiene CoMa-Windows.zip.' }
        if ($asset.digest -notmatch '^sha256:[a-fA-F0-9]{64}$') {
            throw 'GitHub no proporcionó una huella SHA-256 válida para la descarga.'
        }
        $download = [Uri]$asset.browser_download_url
        if ($download.Scheme -ne 'https' -or $download.Host -ne 'github.com' -or
            -not $download.AbsolutePath.StartsWith('/Lord-physics/CoMa/releases/download/', [StringComparison]::OrdinalIgnoreCase) -or
            -not $download.AbsolutePath.EndsWith('/CoMa-Windows.zip', [StringComparison]::OrdinalIgnoreCase)) {
            throw 'La dirección del archivo publicado no es válida.'
        }
        $expected = $asset.digest.Substring(7)
        Write-Output "Descargando CoMa $($release.tag_name)..."
    }

    $temporary = Join-Path $tempRoot ('CoMa-update-' + [Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $temporary | Out-Null
    $zip = Join-Path $temporary 'CoMa-Windows.zip'
    $package = Join-Path $temporary 'package'
    if ($PackagePath) {
        Copy-Item -LiteralPath $sourceZip -Destination $zip
    } else {
        Invoke-WebRequest -Uri $download.AbsoluteUri -OutFile $zip -UseBasicParsing
    }
    $hasher = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($zip)
    try { $actual = [BitConverter]::ToString($hasher.ComputeHash($stream)).Replace('-', '') }
    finally {
        $stream.Dispose()
        $hasher.Dispose()
    }
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
} catch {
    if ($FromApp) {
        $message = 'No se pudo actualizar CoMa: ' + $_.Exception.Message
        try {
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.MessageBox]::Show($message, 'CoMa', 'OK', 'Error') | Out-Null
        } catch { }
        $oldExe = Join-Path (Join-Path $env:LOCALAPPDATA 'Programs\CoMa') 'CoMa.exe'
        $alreadyRunning = @(Get-Process -Name CoMa -ErrorAction SilentlyContinue | Where-Object {
            $_.Path -and [string]::Equals($_.Path, $oldExe, [StringComparison]::OrdinalIgnoreCase)
        })
        if ((Test-Path -LiteralPath $oldExe -PathType Leaf) -and $alreadyRunning.Count -eq 0) {
            try { Start-Process -FilePath $oldExe } catch { }
        }
    }
    throw
} finally {
    try { Remove-CoMaTempDirectory $temporary } catch { }
    try { Remove-CoMaTempDirectory $ownedPackageDir } catch { }
}
