param(
    [switch]$SkipPlaywrightBrowser
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RootDir

function Ok($Message) {
    Write-Host "OK  $Message"
}

function Warn($Message) {
    Write-Host "WARN $Message"
}

function Fail($Message) {
    Write-Host "FAIL $Message"
    exit 1
}

function Require-Command($Command, $Hint) {
    $Found = Get-Command $Command -ErrorAction SilentlyContinue
    if (-not $Found) {
        Fail "$Command is missing. $Hint"
    }
    Ok "$Command found: $($Found.Source)"
}

function Test-PythonVersion {
    $VersionText = python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    $Parts = $VersionText.Split(".")
    $Major = [int]$Parts[0]
    $Minor = [int]$Parts[1]
    if ($Major -lt 3 -or ($Major -eq 3 -and $Minor -lt 11)) {
        Fail "Python 3.11+ is required. Found: $VersionText"
    }
    Ok "Python $VersionText"
}

function Test-NodeVersion {
    $Major = [int](node -p "process.versions.node.split('.')[0]")
    if ($Major -lt 18) {
        Fail "Node.js 18+ is required. Found: $(node --version)"
    }
    Ok "Node $(node --version)"
}

Write-Host "==> Checking required tools"
Require-Command python "Install Python 3.11+ from https://www.python.org/downloads/ and select 'Add python.exe to PATH'."
Require-Command uv "Install uv with: powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
Require-Command node "Install Node.js 18+ from https://nodejs.org/"
Require-Command npm "Install npm with Node.js."
Require-Command npx "Install npx with Node.js/npm."
Test-PythonVersion
Test-NodeVersion

Write-Host ""
Write-Host "==> Creating Python virtual environment"
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Ok "created .venv"
} else {
    Ok ".venv already exists"
}

$PythonExe = Join-Path $RootDir ".venv\Scripts\python.exe"
$PipExe = Join-Path $RootDir ".venv\Scripts\pip.exe"

Write-Host ""
Write-Host "==> Installing agency packages into .venv"
& $PythonExe -m pip install --upgrade pip
& $PipExe install -e .\packages\agency-common
& $PipExe install -e .\packages\agency-research
& $PipExe install -e .\packages\agency-storyboard
& $PipExe install -e .\packages\agency-content
Ok "agency CLIs installed"

Write-Host ""
Write-Host "==> Preparing vendored Freepik FastMCP"
uv sync --directory packages/freepik-fastmcp
Ok "Freepik FastMCP dependencies ready"

Write-Host ""
Write-Host "==> Validating MCP JSON files"
python -m json.tool .mcp.json | Out-Null
python -m json.tool mcp/agents/research.json | Out-Null
python -m json.tool mcp/agents/storyboard.json | Out-Null
Ok "MCP configs are valid JSON"

Write-Host ""
Write-Host "==> Checking npm MCP packages"
npm view @perplexity-ai/mcp-server@0.9.0 version | Out-Null
npm view @playwright/mcp@0.0.73 version | Out-Null
npm view firecrawl-mcp@3.14.1 version | Out-Null
npm view chrome-devtools-mcp@0.23.0 version | Out-Null
npm view @glifxyz/glif-mcp-server@0.9.9 version | Out-Null
Ok "pinned npm MCP packages are available"

if (-not $SkipPlaywrightBrowser) {
    Write-Host ""
    Write-Host "==> Installing Playwright Chromium browser"
    npx -y playwright@1.56.1 install chromium
    Ok "Playwright Chromium ready"
} else {
    Warn "skipped Playwright browser install"
}

Write-Host ""
Write-Host "==> Checking API key environment variables"
foreach ($Var in @("FREEPIK_API_KEY", "PERPLEXITY_API_KEY", "FIRECRAWL_API_KEY", "GLIF_API_TOKEN")) {
    if ([Environment]::GetEnvironmentVariable($Var)) {
        Ok "$Var is set"
    } else {
        Warn "$Var is not set"
    }
}

Write-Host ""
Write-Host "Bootstrap complete."
Write-Host "Activate the Python environment with:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "If any API key showed WARN, set it in PowerShell with:"
Write-Host '  [Environment]::SetEnvironmentVariable("PERPLEXITY_API_KEY", "your_key_here", "User")'
Write-Host "Then close and reopen PowerShell."
