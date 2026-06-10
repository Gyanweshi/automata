param(
    [ValidateSet("cdp", "browser-act", "playwright")]
    [string]$Mode = "cdp",

    [string]$BrowserActSessionName = "instagram-main",
    [int]$CdpPort = 9224,
    [string]$CdpProfileDir = "$env:USERPROFILE\.agency\chrome-instagram-cdp",
    [switch]$WaitForEnter
)

$ErrorActionPreference = "Stop"

function Write-Step($Message) {
    Write-Host "[instagram-session] $Message"
}

switch ($Mode) {
    "cdp" {
        $chromeCandidates = @(
            "C:\Program Files\Google\Chrome\Application\chrome.exe",
            "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        )
        $browser = $chromeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
        if (-not $browser) {
            throw "Chrome or Edge was not found. Install Chrome, or pass a different CDP setup manually."
        }

        New-Item -ItemType Directory -Force $CdpProfileDir | Out-Null
        Write-Step "Opening persistent CDP browser profile: $CdpProfileDir"
        Write-Step "Remote debugging port: $CdpPort"
        Start-Process -FilePath $browser -ArgumentList @(
            "--remote-debugging-port=$CdpPort",
            "--user-data-dir=$CdpProfileDir",
            "--no-first-run",
            "--disable-default-apps",
            "https://www.instagram.com/accounts/login/"
        )

        Start-Sleep -Seconds 3
        try {
            $version = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$CdpPort/json/version" -TimeoutSec 5
            Write-Step "CDP is reachable at http://127.0.0.1:$CdpPort/json/version"
        } catch {
            Write-Warning "Browser opened, but CDP did not respond yet: $($_.Exception.Message)"
        }

        Write-Step "Please log into Instagram in the opened browser window."
        Write-Step "Leave the browser open while research runs. Future CDP runs can reuse this profile."
        if ($WaitForEnter) {
            Read-Host "Press Enter after Instagram login is complete"
        }
    }

    "browser-act" {
        Write-Step "Opening browser-act session: $BrowserActSessionName"
        Write-Step "Please log into Instagram in the browser-act controlled session."
        browser-act --session $BrowserActSessionName navigate "https://www.instagram.com/accounts/login/"
        browser-act --session $BrowserActSessionName wait stable --timeout 15000
        browser-act --session $BrowserActSessionName state
        Write-Step "After login, reuse with: -Scraper browser-act -BrowserActMode session -BrowserActSessionName $BrowserActSessionName"
        if ($WaitForEnter) {
            Read-Host "Press Enter after Instagram login is complete"
        }
    }

    "playwright" {
        Write-Step "Use the existing Playwright manual login mode. It saves state to $env:USERPROFILE\.agency\ig_session.json"
        Write-Step "Run: .\scripts\run-agent.ps1 research -Brand <brand> -Scraper playwright -InstagramLoginMode manual -Platforms ig"
    }
}
