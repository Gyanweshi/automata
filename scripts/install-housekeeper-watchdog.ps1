param(
    [string]$TaskName = "Automata Housekeeper",
    [ValidatePattern("^([01]\d|2[0-3]):[0-5]\d$")]
    [string]$DailyAt = "03:00",
    [ValidateRange(1, 365)]
    [int]$RetentionDays = 7
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$WatchdogScript = Join-Path $PSScriptRoot "run-housekeeper-watchdog.ps1"
if (-not (Test-Path -LiteralPath $WatchdogScript)) {
    throw "Watchdog script is missing: $WatchdogScript"
}

$PowerShell = (Get-Command powershell.exe -ErrorAction Stop).Source
$Arguments = @(
    "-NoProfile"
    "-ExecutionPolicy Bypass"
    "-File `"$WatchdogScript`""
    "-RetentionDays $RetentionDays"
) -join " "
$action = New-ScheduledTaskAction `
    -Execute $PowerShell `
    -Argument $Arguments `
    -WorkingDirectory $RootDir
$trigger = New-ScheduledTaskTrigger -Daily -At $DailyAt
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Purges Automata quarantine batches after $RetentionDays days." `
    -Force | Out-Null

Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName, State
