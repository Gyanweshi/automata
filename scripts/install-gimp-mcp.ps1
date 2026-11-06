# Installs the GIMP-side plugin for the gimp-mcp server registered in .mcp.json.
# The MCP server itself runs via uvx (pinned commit below); this script only
# places the matching plugin file into GIMP's per-user plug-ins folder.
# Re-run after a GIMP minor upgrade (3.2 -> 3.4), since GIMP moves that folder.
param(
    [string]$Commit = "7325865385541a01aaf336ebc93b00332297f77f",
    [string]$GimpVersion = ""
)
$ErrorActionPreference = "Stop"

$base = Join-Path $env:APPDATA "GIMP"
if (-not $GimpVersion) {
    $existing = @()
    if (Test-Path $base) {
        $existing = Get-ChildItem $base -Directory | Where-Object { $_.Name -match '^3\.\d+$' } |
            Sort-Object { [version]$_.Name }
    }
    if ($existing.Count -gt 0) {
        $GimpVersion = $existing[-1].Name
    } else {
        $exe = Get-ChildItem "C:\Program Files\GIMP 3\bin" -Filter "gimp-3.*.exe" -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '^gimp-(3\.\d+)\.exe$' } | Select-Object -First 1
        if (-not $exe) { throw "Could not detect GIMP 3.x. Pass -GimpVersion 3.2" }
        $GimpVersion = ($exe.Name -replace '^gimp-(3\.\d+)\.exe$', '$1')
    }
}

$dest = Join-Path $base "$GimpVersion\plug-ins\gimp-mcp-plugin"
New-Item -ItemType Directory -Force $dest | Out-Null
$url = "https://raw.githubusercontent.com/gimp-mcp/gimp-mcp/$Commit/gimp-mcp-plugin.py"
Invoke-WebRequest -Uri $url -OutFile (Join-Path $dest "gimp-mcp-plugin.py") -UseBasicParsing
Write-Host "Installed gimp-mcp plugin ($($Commit.Substring(0,7))) into $dest"
Write-Host "Restart GIMP, open an image, then Tools > MCP > Start MCP Server (localhost:9877)."
