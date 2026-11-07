# Legacy entry point for scheduled tasks installed before scripts/schedule.py existed; the job itself is Python.
# Re-schedule with `python scripts\schedule.py install housekeeper`, after which this file is unused.
param([int]$RetentionDays = 7)
& (Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe") (Join-Path $PSScriptRoot "schedule.py") run housekeeper --retention-days $RetentionDays
exit $LASTEXITCODE
