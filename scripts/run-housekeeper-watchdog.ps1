param(
    [ValidateRange(1, 365)]
    [int]$RetentionDays = 7
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RootDir ".venv\Scripts\python.exe"
$SourceDir = Join-Path $RootDir "packages\agency-common\src"
$LogDir = Join-Path $RootDir ".housekeeper\logs"
$LogPath = Join-Path $LogDir "watchdog.log"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Automata virtualenv is missing: $Python"
}

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
$ExistingPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = if ($ExistingPythonPath) {
    "$SourceDir;$ExistingPythonPath"
} else {
    $SourceDir
}

$started = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
$output = & $Python -m agency_common.housekeeping purge `
    --repo $RootDir `
    --older-than-days $RetentionDays `
    --confirm delete 2>&1
$exitCode = $LASTEXITCODE

Add-Content -LiteralPath $LogPath -Encoding UTF8 -Value "[$started] exit=$exitCode"
foreach ($line in $output) {
    Add-Content -LiteralPath $LogPath -Encoding UTF8 -Value $line
}

if ($exitCode -ne 0) {
    throw "Housekeeper watchdog failed with exit code $exitCode. See $LogPath"
}
