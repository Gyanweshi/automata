param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("research", "storyboard", "content", "pipeline", "dry-run", "status")]
    [string]$Command,

    [string]$Brand = "example-brand",
    [string]$Type = "carousel",
    [string]$Topic = "5 tips for entrepreneurs",
    [string]$Workspace = "./workspace",
    [string]$BrandsDir = "./brands"
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RootDir

$Research = Join-Path $RootDir ".venv\Scripts\agency-research.exe"
$Storyboard = Join-Path $RootDir ".venv\Scripts\agency-storyboard.exe"
$Content = Join-Path $RootDir ".venv\Scripts\agency-content.exe"
$Pip = Join-Path $RootDir ".venv\Scripts\pip.exe"

if (-not (Test-Path $Pip)) {
    Write-Host "Agency CLIs are not installed. Run: powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1"
    exit 1
}

if (-not (Test-Path $Research) -and $Command -ne "status") {
    Write-Host "Agency CLIs are not installed. Run: powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1"
    exit 1
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
        & $Research --brand $Brand --workspace $Workspace --brands-dir $BrandsDir
    }
    "storyboard" {
        & $Storyboard --brand $Brand --type $Type --topic $Topic --workspace $Workspace --brands-dir $BrandsDir
    }
    "content" {
        & $Content --brand $Brand --platform instagram --type $Type --topic $Topic --workspace $Workspace --brands-dir $BrandsDir
    }
    "pipeline" {
        & $Research --brand $Brand --workspace $Workspace --brands-dir $BrandsDir
        & $Storyboard --brand $Brand --type $Type --topic $Topic --workspace $Workspace --brands-dir $BrandsDir
        & $Content --brand $Brand --platform instagram --type $Type --topic $Topic --workspace $Workspace --brands-dir $BrandsDir
    }
}
