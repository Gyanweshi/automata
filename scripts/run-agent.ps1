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
    [ValidateSet("apify", "playwright", "browser-act", "cdp")]
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

$IsNativeWindows = ($env:OS -eq "Windows_NT")
if ($IsNativeWindows) {
    $Python = Join-Path $RootDir ".venv\Scripts\python.exe"
    $Research = Join-Path $RootDir ".venv\Scripts\agency-research.exe"
    $Storyboard = Join-Path $RootDir ".venv\Scripts\agency-storyboard.exe"
    $Content = Join-Path $RootDir ".venv\Scripts\agency-content.exe"
} else {
    $Python = Join-Path $RootDir ".venv/bin/python"
    $Research = Join-Path $RootDir ".venv/bin/agency-research"
    $Storyboard = Join-Path $RootDir ".venv/bin/agency-storyboard"
    $Content = Join-Path $RootDir ".venv/bin/agency-content"
}

if (-not (Test-Path $Python)) {
    Write-Host "Python virtualenv is not installed. Run: powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1"
    exit 1
}

$SourcePaths = @(
    (Join-Path $RootDir "packages\agency-common\src"),
    (Join-Path $RootDir "packages\agency-research\src"),
    (Join-Path $RootDir "packages\agency-storyboard\src"),
    (Join-Path $RootDir "packages\agency-content\src")
)
$PathSeparator = if ($IsNativeWindows) { ";" } else { ":" }
$ExistingPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = (($SourcePaths + $ExistingPythonPath) | Where-Object { $_ }) -join $PathSeparator

function Invoke-AgencyCli {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string]$Module,
        [Parameter(Mandatory = $true)][string[]]$CliArgs
    )

    if (Test-Path $Executable) {
        & $Executable @CliArgs
    } else {
        & $Python -m $Module @CliArgs
    }
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
        $Packages = @(
            @{ Name = "agency-common"; Path = "packages\agency-common\pyproject.toml"; Executable = "" },
            @{ Name = "agency-research"; Path = "packages\agency-research\pyproject.toml"; Executable = $Research },
            @{ Name = "agency-storyboard"; Path = "packages\agency-storyboard\pyproject.toml"; Executable = $Storyboard },
            @{ Name = "agency-content"; Path = "packages\agency-content\pyproject.toml"; Executable = $Content }
        )
        foreach ($Package in $Packages) {
            $PyprojectPath = Join-Path $RootDir $Package.Path
            $VersionMatch = Select-String -Path $PyprojectPath -Pattern '^version\s*=\s*"([^"]+)"' | Select-Object -First 1
            $Version = if ($VersionMatch) { $VersionMatch.Matches[0].Groups[1].Value } else { "unknown" }
            $State = if ($Package.Executable -and (Test-Path $Package.Executable)) { "installed entry point" } else { "source fallback" }
            Write-Host "$($Package.Name): $Version ($State)"
        }
    }
    "dry-run" {
        Invoke-AgencyCli $Research "agency_research.cli" @("--brand", $Brand, "--workspace", $Workspace, "--brands-dir", $BrandsDir, "--dry-run")
        Invoke-AgencyCli $Content "agency_content.cli" @("--brand", $Brand, "--platform", "instagram", "--type", "caption", "--topic", "test", "--workspace", $Workspace, "--brands-dir", $BrandsDir, "--format", "summary")
    }
    "research" {
        $Args = @("--brand", $Brand, "--workspace", $Workspace, "--brands-dir", $BrandsDir, "--scraper", $Scraper, "--instagram-login-mode", $InstagramLoginMode, "--browser-act-mode", $BrowserActMode, "--browser-act-session-name", $BrowserActSessionName) + $ResearchPlatformArgs + $ResearchParallelArgs
        Invoke-AgencyCli $Research "agency_research.cli" $Args
    }
    "storyboard" {
        Invoke-AgencyCli $Storyboard "agency_storyboard.cli" @("--brand", $Brand, "--type", $Type, "--topic", $Topic, "--workspace", $Workspace, "--brands-dir", $BrandsDir)
    }
    "content" {
        Invoke-AgencyCli $Content "agency_content.cli" @("--brand", $Brand, "--platform", "instagram", "--type", $Type, "--topic", $Topic, "--workspace", $Workspace, "--brands-dir", $BrandsDir)
    }
    "pipeline" {
        $Args = @("--brand", $Brand, "--workspace", $Workspace, "--brands-dir", $BrandsDir, "--scraper", $Scraper, "--instagram-login-mode", $InstagramLoginMode, "--browser-act-mode", $BrowserActMode, "--browser-act-session-name", $BrowserActSessionName) + $ResearchPlatformArgs + $ResearchParallelArgs
        Invoke-AgencyCli $Research "agency_research.cli" $Args
        Invoke-AgencyCli $Storyboard "agency_storyboard.cli" @("--brand", $Brand, "--type", $Type, "--topic", $Topic, "--workspace", $Workspace, "--brands-dir", $BrandsDir)
        Invoke-AgencyCli $Content "agency_content.cli" @("--brand", $Brand, "--platform", "instagram", "--type", $Type, "--topic", $Topic, "--workspace", $Workspace, "--brands-dir", $BrandsDir)
    }
}
