[CmdletBinding()]
param(
    [ValidateRange(1024, 65535)]
    [int]$Port = 8002
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$venvPython = Join-Path $backend '.venv\Scripts\python.exe'

if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    throw "Port $Port is already in use."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw 'npm was not found. Install Node.js 20 or newer.'
}

$assets = @(
    @{ Path = (Join-Path $frontend 'public\vendor\geetest\gt.0.4.9.js'); Hash = '69295620348ceb9e52d96e23bf22e5daef1cc81c109b3e049465c9343528df17' },
    @{ Path = (Join-Path $frontend 'public\vendor\geetest\gt4.js'); Hash = '449261e14e6b2880fe8711561e7c3cbfa79db3ed393117068ef2e403e03c0b1f' }
)
foreach ($asset in $assets) {
    if (-not (Test-Path -LiteralPath $asset.Path)) { throw "Missing reviewed asset: $($asset.Path)" }
    $actual = (Get-FileHash -LiteralPath $asset.Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $asset.Hash) { throw "Asset checksum mismatch: $($asset.Path)" }
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    $launcher = Get-Command python -ErrorAction SilentlyContinue
    if (-not $launcher) { throw 'Python 3.10 or newer was not found.' }
    & $launcher.Source -m venv (Join-Path $backend '.venv')
    & $venvPython -m pip install -e "${backend}[dev]"
}
else {
    & $venvPython -c "import aigis_bridge, fastapi, uvicorn" 2>$null
    if ($LASTEXITCODE -ne 0) { & $venvPython -m pip install -e "${backend}[dev]" }
}

Push-Location $frontend
try {
    if (-not (Test-Path -LiteralPath (Join-Path $frontend 'node_modules'))) { npm ci }
    npm run build:mock
}
finally { Pop-Location }

Write-Host "Mock demo ready at http://127.0.0.1:$Port/"
Write-Host 'This mode uses explicit test doubles and does not contact GeeTest or an account provider.'
Write-Host 'Press Ctrl+C to stop.'
Push-Location $backend
try { & $venvPython -m uvicorn aigis_bridge.demo:app --host 127.0.0.1 --port $Port } finally { Pop-Location }
