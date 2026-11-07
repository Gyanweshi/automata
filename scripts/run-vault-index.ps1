# Legacy entry point for scheduled tasks installed before scripts/schedule.py existed; the job itself is Python.
# Re-schedule with `python scripts\schedule.py install vault-index`, after which this file is unused.
& (Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe") (Join-Path $PSScriptRoot "schedule.py") run vault-index @args
exit $LASTEXITCODE
