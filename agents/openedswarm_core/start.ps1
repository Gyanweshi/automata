# OpenSwarm Permanent Starter
# Runs the Agency Swarm FastAPI server on a FIXED port 8080 with auto-restart,
# then connects the TUI to it. This avoids the random-port disconnect issue.

$ErrorActionPreference = "SilentlyContinue"
$venv    = "$PSScriptRoot\.venv\Scripts\python.exe"
$server  = "$PSScriptRoot\server.py"
$port    = 8080
$config  = "$env:USERPROFILE\.config\agentswarm\openswarm.jsonc"

# ── 1. Kill any leftover processes on port 8080 ──────────────────────────────
$old = (netstat -ano | Select-String ":$port ") -replace '.*LISTENING\s+', '' | Select-Object -First 1
if ($old) { Stop-Process -Id $old.Trim() -Force }

# ── 2. Start FastAPI server in background with auto-restart ──────────────────
$serverJob = Start-Job -Name "AgencySwarmServer" -ScriptBlock {
    param($py, $script, $cwd)
    Set-Location $cwd
    while ($true) {
        & $py $script *>> "$cwd\server_background.log"
        Start-Sleep -Seconds 3   # brief pause before restart
    }
} -ArgumentList $venv, $server, $PSScriptRoot

Write-Host ""
Write-Host "Starting Agency Swarm server on port $port..." -ForegroundColor Cyan

# ── 3. Wait until port 8080 is ready (up to 3 min) ──────────────────────────
$ready = $false
for ($i = 0; $i -lt 90; $i++) {
    Start-Sleep -Seconds 2
    try {
        $r = Invoke-WebRequest "http://127.0.0.1:$port/open-swarm/get_metadata" -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    Write-Host "." -NoNewline
}

if (-not $ready) {
    Write-Host "`nServer did not start in time. Check for errors above." -ForegroundColor Red
    Stop-Job $serverJob; Remove-Job $serverJob
    exit 1
}

Write-Host "`nServer ready! Launching OpenSwarm UI..." -ForegroundColor Green

# ── 4. Patch the config to lock in the correct port ─────────────────────────
if (Test-Path $config) {
    $json = Get-Content $config -Raw
    # Replace whatever baseURL is set with our fixed port
    $json = $json -replace '"baseURL"\s*:\s*"http://127\.0\.0\.1:\d+"', "`"baseURL`": `"http://127.0.0.1:$port`""
    Set-Content $config $json
}

# ── 5. Launch the openswarm TUI (this blocks until the user exits) ───────────
openswarm

# ── 6. Clean up server job on exit ──────────────────────────────────────────
Write-Host "Stopping background server..." -ForegroundColor Yellow
Stop-Job $serverJob
Remove-Job $serverJob
