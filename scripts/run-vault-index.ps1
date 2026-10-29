# Rebuild the chunked Second Brain index in place. Run nightly by install-vault-index.ps1,
# or by hand after big vault edits: powershell -File scripts\run-vault-index.ps1
$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RootDir ".venv\Scripts\python.exe"
$LogDir = Join-Path $RootDir ".housekeeper\logs"
$LogPath = Join-Path $LogDir "vault-index.log"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Automata virtualenv is missing: $Python"
}

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
# The vault path comes from .env, which is looked up from the working directory.
Set-Location -LiteralPath $RootDir

$started = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
$ErrorActionPreference = "Continue"
$output = & $Python -m agency_common.obsidian_vector_index 2>&1 | ForEach-Object { "$_" }
$exitCode = $LASTEXITCODE
$ErrorActionPreference = "Stop"

Add-Content -LiteralPath $LogPath -Encoding UTF8 -Value "[$started] exit=$exitCode"
$output | Where-Object { $_ -match '^(INFO|WARNING|ERROR)' } |
    ForEach-Object { Add-Content -LiteralPath $LogPath -Encoding UTF8 -Value $_ }

if ($exitCode -ne 0) {
    $output | Select-Object -Last 20 | ForEach-Object { Write-Host $_ }
    throw "Vault index rebuild failed with exit code $exitCode. See $LogPath"
}
