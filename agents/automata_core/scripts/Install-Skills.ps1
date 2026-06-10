# Install-Skills.ps1
# Symlinks all skills from the repo into %APPDATA%\Claude\skills\
# Run from the repo root: .\scripts\Install-Skills.ps1
#
# Requires administrator rights to create symlinks on Windows,
# OR Developer Mode must be enabled (Settings → Developer → Developer Mode).

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$SkillsSource = "",
    [string]$SkillsDest   = "$env:APPDATA\Claude\skills"
)

if (-not $SkillsSource) {
    $SkillsSource = Join-Path $PSScriptRoot "..\skills"
}

$SkillsSource = (Resolve-Path $SkillsSource).Path

if (-not (Test-Path $SkillsSource)) {
    Write-Error "skills/ directory not found at $SkillsSource"
    exit 1
}

if (-not (Test-Path $SkillsDest)) {
    if ($PSCmdlet.ShouldProcess($SkillsDest, "Create skills directory")) {
        New-Item -ItemType Directory -Path $SkillsDest -Force | Out-Null
    }
}

$installed = 0
$skipped   = 0

Get-ChildItem -Path $SkillsSource -Directory | ForEach-Object {
    $skillDir  = $_.FullName
    $skillName = $_.Name
    $skillMd   = Join-Path $skillDir "SKILL.md"
    $target    = Join-Path $SkillsDest $skillName

    # Only directories that contain a SKILL.md
    if (-not (Test-Path $skillMd)) { return }

    if (Test-Path $target) {
        $item = Get-Item $target
        if ($item.LinkType -eq "SymbolicLink") {
            if ($PSCmdlet.ShouldProcess($target, "Remove existing symlink")) {
                Remove-Item $target -Force
            }
            Write-Host "  updated: $skillName"
        } else {
            Write-Host "  SKIP: $target exists and is not a symlink (remove manually to reinstall)"
            $skipped++
            return
        }
    } else {
        Write-Host "  installed: $skillName"
    }

    if ($PSCmdlet.ShouldProcess($target, "Create symlink to $skillDir")) {
        New-Item -ItemType SymbolicLink -Path $target -Target $skillDir | Out-Null
        $installed++
    }
}

Write-Host ""
Write-Host "$installed skill(s) installed to $SkillsDest"
if ($skipped -gt 0) {
    Write-Host "$skipped skill(s) skipped (non-symlink directories)"
}
Write-Host ""
Write-Host "Active skills:"
Get-ChildItem -Path $SkillsSource -Directory | ForEach-Object {
    if (Test-Path (Join-Path $_.FullName "SKILL.md")) {
        Write-Host "  /$($_.Name)"
    }
}
