$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $root 'backend\.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) { throw 'Run scripts/start_demo.ps1 once to create the local environment.' }

Push-Location (Join-Path $root 'backend')
try { & $python -m pytest -q } finally { Pop-Location }

Push-Location (Join-Path $root 'frontend')
try {
    npm ci
    npm run build
    npm run build:mock
}
finally { Pop-Location }

Write-Host 'VERIFY_OK: Python tests, TypeScript, official production build, and mock build passed.'
