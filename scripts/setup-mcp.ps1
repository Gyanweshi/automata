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
    Fail "npx is required. Install Node.js 18+ from https://nodejs.org/ and reopen PowerShell."
}

Write-Host "==> Preparing Freepik FastMCP dependencies..."
uv sync --directory packages/freepik-fastmcp

Write-Host "==> Checking pinned npm MCP packages..."
npm view @perplexity-ai/mcp-server@0.9.0 version | Out-Null
npm view @playwright/mcp@0.0.73 version | Out-Null
npm view firecrawl-mcp@3.14.1 version | Out-Null
npm view chrome-devtools-mcp@0.23.0 version | Out-Null
npm view @glifxyz/glif-mcp-server@0.9.9 version | Out-Null

Write-Host "==> Done. Set any API keys you use with commands like:"
Write-Host '    [Environment]::SetEnvironmentVariable("FREEPIK_API_KEY", "your_key_here", "User")'
Write-Host '    [Environment]::SetEnvironmentVariable("PERPLEXITY_API_KEY", "your_key_here", "User")'
Write-Host '    [Environment]::SetEnvironmentVariable("FIRECRAWL_API_KEY", "your_key_here", "User")'
Write-Host '    [Environment]::SetEnvironmentVariable("GLIF_API_TOKEN", "your_token_here", "User")'
Write-Host "Then close and reopen PowerShell."
