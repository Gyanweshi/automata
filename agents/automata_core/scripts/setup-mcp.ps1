$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RootDir

function Fail($Message) {
    Write-Host "FAIL $Message"
    exit 1
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Fail "uv is required. Install it with: powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
}

if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    Fail "npx is required. Install Node.js 20.19+, 22.12+, or 23+ from https://nodejs.org/ and reopen PowerShell."
}

node -e "const [major, minor] = process.versions.node.split('.').map(Number); process.exit(((major === 20 && minor >= 19) || (major === 22 && minor >= 12) || major >= 23) ? 0 : 1)"
if ($LASTEXITCODE -ne 0) {
    Fail "Node.js 20.19+, 22.12+, or 23+ is required for chrome-devtools-mcp. Found: $(node --version)"
}

if (Test-Path ".venv\Scripts\scrapling.exe") {
    Write-Host "==> Checking Scrapling MCP command..."
    .\.venv\Scripts\scrapling.exe --version | Out-Null
} elseif (Get-Command scrapling -ErrorAction SilentlyContinue) {
    Write-Host "==> Checking Scrapling MCP command..."
    scrapling --version | Out-Null
} else {
    Write-Host "WARN Scrapling is not installed yet. Run scripts/bootstrap.ps1 or install the agency-research package first."
}

Write-Host "==> Checking pinned npm MCP packages..."
npm view @perplexity-ai/mcp-server@0.9.0 version | Out-Null
npm view @playwright/mcp@0.0.73 version | Out-Null
npm view chrome-devtools-mcp@0.23.0 version | Out-Null
npm view @roomi-fields/notebooklm-mcp@1.5.9 version | Out-Null
npm view mcp-remote@0.1.38 version | Out-Null
npm view @apify/actors-mcp-server@0.9.20 version | Out-Null

Write-Host "==> Done. Set any API keys you use with commands like:"
Write-Host '    [Environment]::SetEnvironmentVariable("PERPLEXITY_API_KEY", "your_key_here", "User")'
Write-Host '    [Environment]::SetEnvironmentVariable("CAPSULEHUB_API_KEY", "your_key_here", "User")'
Write-Host '    [Environment]::SetEnvironmentVariable("APIFY_API_TOKEN", "your_token_here", "User")'
Write-Host "Then close and reopen PowerShell."
