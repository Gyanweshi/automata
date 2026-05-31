param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("research", "storyboard", "content", "pipeline", "dry-run", "status")]
    [string]$Command,

    [string]$Brand = "example-brand",
    [string]$Type = "carousel",
    [string]$Topic = "5 tips for entrepreneurs",
    [string]$Workspace = "./workspace",
    [string]$BrandsDir = "./brands",
    [string]$Platforms = "",
    [ValidateSet("apify", "playwright", "browser-act")]
    [string]$Scraper = "apify",
    [ValidateSet("auto", "manual")]
    [string]$InstagramLoginMode = "auto",
    [ValidateSet("stealth", "session")]
    [string]$BrowserActMode = "stealth",
    [string]$BrowserActSessionName = "",
    [switch]$Parallel,
    [int]$MaxWorkers = 4
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RootDir

if ($IsWindows) {
    $Research = Join-Path $RootDir ".venv\Scripts\agency-research.exe"
    $Storyboard = Join-Path $RootDir ".venv\Scripts\agency-storyboard.exe"
    $Content = Join-Path $RootDir ".venv\Scripts\agency-content.exe"
    $Pip = Join-Path $RootDir ".venv\Scripts\pip.exe"
} else {
    $Research = Join-Path $RootDir ".venv/bin/agency-research"
    $Storyboard = Join-Path $RootDir ".venv/bin/agency-storyboard"
    $Content = Join-Path $RootDir ".venv/bin/agency-content"
    $Pip = Join-Path $RootDir ".venv/bin/pip"
}

if (-not (Test-Path $Pip)) {
    Write-Host "Agency CLIs are not installed. Run: powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1"
    exit 1
}

if (-not (Test-Path $Research) -and $Command -ne "status") {
    Write-Host "Agency CLIs are not installed. Run: powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1"
    exit 1
}

$ResearchParallelArgs = @()
if ($Parallel) {
    $ResearchParallelArgs = @("--parallel", "--max-workers", "$MaxWorkers")
}
$ResearchPlatformArgs = @()
if ($Platforms) {
    $ResearchPlatformArgs = @("--platforms", $Platforms)
}

switch ($Command) {
    "status" {
        & $Pip show agency-common agency-research agency-storyboard agency-content
    }
    "dry-run" {
        & $Research --brand $Brand --workspace $Workspace --brands-dir $BrandsDir --dry-run
        & $Content --brand $Brand --platform instagram --type caption --topic "test" --workspace $Workspace --brands-dir $BrandsDir --format summary
    }
    "research" {
        & $Research --brand $Brand --workspace $Workspace --brands-dir $BrandsDir --scraper $Scraper --instagram-login-mode $InstagramLoginMode --browser-act-mode $BrowserActMode --browser-act-session-name $BrowserActSessionName @ResearchPlatformArgs @ResearchParallelArgs
    }
    "storyboard" {
        & $Storyboard --brand $Brand --type $Type --topic $Topic --workspace $Workspace --brands-dir $BrandsDir
    }
    "content" {
        & $Content --brand $Brand --platform instagram --type $Type --topic $Topic --workspace $Workspace --brands-dir $BrandsDir
    }
    "pipeline" {
        & $Research --brand $Brand --workspace $Workspace --brands-dir $BrandsDir --scraper $Scraper --instagram-login-mode $InstagramLoginMode --browser-act-mode $BrowserActMode --browser-act-session-name $BrowserActSessionName @ResearchPlatformArgs @ResearchParallelArgs
        & $Storyboard --brand $Brand --type $Type --topic $Topic --workspace $Workspace --brands-dir $BrandsDir
        & $Content --brand $Brand --platform instagram --type $Type --topic $Topic --workspace $Workspace --brands-dir $BrandsDir
    }
}
