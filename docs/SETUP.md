# Setting Up a Machine

Read this before setting up a new laptop or helping someone else set one up. Every problem listed under
Troubleshooting has actually happened on a fresh Windows or Linux machine, and each one has a known fix.

The short version: **paste one block, answer three questions, read the summary at the end.**

---

## 1. Fresh machine (nothing installed, not even Python)

Open a terminal: **PowerShell** on Windows (Start menu, then "PowerShell"; not the old Command Prompt),
**Terminal** on Linux, or **Terminal** on macOS (Spotlight: Cmd+Space, type Terminal). `cd` to the folder where the repo should live, e.g. `cd D:\` on Windows, then paste the
block for your OS.

**Windows**
```powershell
foreach ($id in "Git.Git", "GitHub.cli", "astral-sh.uv") { winget install -e --id $id --accept-source-agreements --accept-package-agreements }
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User") + ";$env:LOCALAPPDATA\Microsoft\WinGet\Links"
gh auth status 2>$null; if ($LASTEXITCODE) { gh auth login --web --git-protocol https }; gh auth setup-git
if (-not (Test-Path automata)) { gh repo clone Gyanweshi/automata }; Set-Location automata
uv run --no-project --python 3.12 scripts\bootstrap.py --yes
```

**Linux** (Ubuntu, Mint, Debian)
```bash
sudo apt-get update && sudo apt-get install -y git curl gh
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh; export PATH="$HOME/.local/bin:$PATH"
gh auth status >/dev/null 2>&1 || gh auth login --web --git-protocol https; gh auth setup-git
[ -d automata ] || gh repo clone Gyanweshi/automata; cd automata
uv run --no-project --python 3.12 scripts/bootstrap.py --yes
```

**macOS** (Terminal app; Apple silicon or Intel)
```bash
command -v brew >/dev/null || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"; grep -qs 'brew shellenv' ~/.zprofile || echo 'eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"' >> ~/.zprofile
brew install git gh uv
gh auth status >/dev/null 2>&1 || gh auth login --web --git-protocol https; gh auth setup-git
[ -d automata ] || gh repo clone Gyanweshi/automata; cd automata
uv run --no-project --python 3.12 scripts/bootstrap.py --yes
```
The first line installs Homebrew, the Mac's package manager, if it is missing: it asks for the Mac's login
password once (nothing shows while you type) and may install Apple's Command Line Tools. The second line puts
Homebrew on PATH now and for every new terminal.

A browser opens once for the GitHub login: approve it. The rest takes about 5–10 minutes, longer with all the
optional tools (LibreOffice alone is a large download). Running the block again is safe; it skips what is
already there.

### What the setup does

Earshot audio tools are registered for both Claude (`.mcp.json`) and Codex
(`.codex/config.toml`) in this checkout. Install with
`python scripts/deps.py install earshot`, or include the `video` machine role.
The same installer works on Windows and Linux, creates an isolated CPU environment,
and downloads about 1.1 GB of local models. Run
`python scripts/earshot.py doctor --load` and `python scripts/mcp-smoke.py earshot`,
then restart the clients from the trusted repo root. Missing-model errors: run
`python scripts/earshot.py doctor --fetch`; missing FFmpeg: install the registered
`ffmpeg` dependency. See the shared Earshot reference in the video-editing skill.
If Windows reports that the Earshot interpreter is in use during reinstall, keep
the existing environment: the installer skips venv creation when its Python exists.

1. Installs Git, the GitHub CLI and uv; uv brings its own Python 3.12, so a system Python is never needed.
2. Installs Node.js (or picks a version new enough for the MCP servers), builds `.venv` from `uv.lock`, installs
   the Node packages and the Playwright browsers.
3. Asks three things, once:
   - **Obsidian vault folder.** Press Enter if this machine has none: notes, drafts and session logs then go to
     `workspace/vault`, laid out the same way, and everything else works the same.
   - **Machine roles**: what the machine is for. Only those optional tools get installed and checked:

     | Role | Tools |
     |---|---|
     | `research` | Chrome, browser-act, Android platform tools (adb) |
     | `video` | ffmpeg, raea |
     | `slides` | LibreOffice, Poppler, ImageMagick, Cairo/Pango |
     | `images` | GIMP, ImageMagick |
     | `3d` | Blender, raea |
     | `all` | everything above |

   - **Nightly jobs** (vault index, housekeeper, vault watchdog): yes on your own machines.
4. Installs git hooks, so a later `git pull` keeps the machine in step on its own.
5. Runs the **doctor** and prints a `PASS` / `WARN` / `FAIL` summary.

### Done when
- The summary ends with **`All required checks passed.`** `WARN` lines are optional extras; each one says how to
  add it.
- Last step: copy `env.example` to `.env` (the setup may have created `.env` already; keep it) and add the API
  keys you need.

---

## 2. Checking a machine (any time)

Run these from the repo folder. On Windows, write `scripts\...` instead of `scripts/...`.

| Command | What it tells you |
|---|---|
| `python scripts/doctor.py` | Everything, step by step. Read-only; changes nothing. |
| `python scripts/deps.py check` | Every tool: `ok`, `warn` (optional, missing), `FAIL` (required, missing), `-` (cannot be checked automatically), `info` (extra). |
| `python scripts/setup_state.py --check` | Whether this machine is in step with the checkout. |

If `python` is not found on Windows, use the repo's own: `.venv\Scripts\python.exe scripts\doctor.py`.
On macOS, `python` may not exist: use `python3`, or the repo's own `.venv/bin/python scripts/doctor.py`.

## 3. Keeping it up to date

```
git pull
```

That is all. When a pull changes dependencies, MCP config or the setup itself, a git hook re-runs the setup
automatically: it installs what changed, removes leftovers of removed components and re-registers this copy's
scheduled jobs. To repair by hand at any time: `python scripts/bootstrap.py`.

To change a machine's roles later: `python scripts/bootstrap.py --roles research,slides` (or `all`, or `none`).

---

## 4. Troubleshooting

Find the symptom, then apply the fix. If a fix says "open a new terminal", that means **close the terminal
tab and open a new one**. In VS Code, Antigravity or another IDE, the built-in terminal can keep the old
PATH until you **restart the whole IDE**.

### Getting started

| Symptom | Cause | Fix |
|---|---|---|
| `git` is not recognized, but the repo is already cloned | GitHub Desktop or the IDE cloned it with its own private git | Paste the Windows block; it installs the real Git. |
| `winget` is not recognized | Old "App Installer" | Update **App Installer** from the Microsoft Store, then paste the block again. |
| `py` / `python` not recognized, or `python` opens the Microsoft Store | No system Python, which is fine | Never needed: the block uses `uv run --python 3.12`. After setup, use `.venv\Scripts\python.exe` (Linux `.venv/bin/python`). |
| winget says **"Found an existing package already installed"** but the command is still not recognized | The tool *is* installed; this terminal has the old PATH | Open a new terminal (restart the IDE), or run the second line of the Windows block again. |
| `uv` not recognized right after installing it | Same: old PATH | Run the second line of the Windows block, then the last line again. |
| The setup ran on a strange branch, or MCP versions look old | The clone was on another branch | `git switch main`, `git pull`, then the last line of the block again. |
| `gh auth login` fails, or `git push` says permission denied | Not logged in, or the login lacks the `workflow` scope | `gh auth login --web --git-protocol https --scopes workflow`, then `gh auth setup-git`. **Never paste a token into chat or a command**; if one leaked, revoke it on GitHub. |

### macOS

| Symptom | Cause | Fix |
|---|---|---|
| `brew: command not found` right after installing Homebrew | Homebrew is not on this terminal's PATH yet | Run the second line of the macOS block, or open a new terminal. |
| The setup stops with "Homebrew is needed on macOS" | Homebrew was never installed | Paste the macOS block from the top (its first line installs Homebrew). |
| A dialog asks to install "command line developer tools" | `git` is Apple's stub until those tools are installed | Click Install, wait for it to finish, then paste the block again. |
| `raea` shows `-` "no raea build for this machine (macos-x86_64)" | raea only ships an Apple-silicon Mac build | Expected on Intel Macs: 3D previz runs on another machine. |
| "cannot be opened because the developer cannot be verified" for a downloaded tool | macOS quarantines downloaded binaries | `python3 scripts/deps.py install <id>` clears the quarantine flag for tools it downloads; for others: System Settings > Privacy & Security > Open Anyway. |
| Nightly jobs | On macOS they are LaunchAgents | `python scripts/schedule.py install vault-index`; they live in `~/Library/LaunchAgents/com.automata.*.plist`. A job missed while the Mac slept runs when it wakes. |
| An MCP server says no compatible Node | The MCP client was started from the Dock without Homebrew's PATH | Nothing to do: the launcher also looks in `/opt/homebrew/bin` and `/usr/local/bin`; if it persists, `brew install node`. |

### After setup

Agent hooks have separate checks. `python scripts/check-hooks.py` checks launchers
and real context/deny responses. On Windows it also executes Codex launchers through
both cmd and PowerShell, from the root and a subdirectory of a path containing spaces.
Linux reports that native Windows execution was not tested. These checks do not
prove that a client loaded or trusted its hooks.

Codex launchers use Node to find the git root and invoke Python. They contain no
shell expansions or Bash loops. Node is already a required bootstrap dependency.
Claude retains its Git Bash launcher. Both clients configure `repo_guard.py` for
all supported tool events. The guard rejects known obsolete commands and checks
the routing receipt before writes and shell commands outside a discovery allowlist.
Unknown tools require routing by default. External MCP tools pass only when their
operation starts with a read-only name such as `get`, `list`, `search`, or `describe`.
Mixed names such as `get_or_create` still require routing. Publishing, sharing,
GPU rental, presets, upscaling, and other generation tools therefore require routing
even when their names contain neither `generate` nor `create`.

Read-only shell chains can use pipes, `&&`, `||`, semicolons, and newlines.
Each command must independently pass the discovery check. Discovery includes
`grep`, non-mutating `find`, simple `sed -n` print selections, and read-only
`git -C <path>` commands. Quoted punctuation is argument data. Simple variable
references in arguments are allowed. Command substitution, redirection, background
execution, and unknown commands still require routing. A denial identifies the
operator or command segment that failed. This parser supports a conservative
shell subset; it is not a complete shell interpreter.

Each user prompt clears the session's receipt. Before execution, the agent runs
`python scripts/hooks/routing_gate.py --session <hook-session-id> --skill <SKILL.md-path> --reason <task-match>`.
Use the repo interpreter when available. Repeat `--skill` for multiple skills.
This command returns the instructions and records the file hashes and routing reason.
Changed skill files invalidate the receipt. For an unchanged follow-up, route the
same skill again. If no available skill fits, use `--no-skill --reason <explanation>`.
That exception is explicit and recorded, but its correctness still requires judgment.
For a fileless built-in skill, invoke the client's skill tool first, then use
`--builtin-skill <name> --reason <task-match>`. The receipt records `builtin_skills`
separately from file-backed `skills` and `no_skill`. Built-in invocation is an agent
attestation; the hook does not independently verify it or invent a local file hash.

The gate proves delivery of skill text or a stated exception, not comprehension,
reference reading, skill relevance, or output quality. It does not grant permission
to spend, publish, or send. Hosted tools that bypass local hooks remain outside its
coverage. Local receipts are workflow state, not a tamper-proof security boundary.
In Codex, inspect hook trust and execution in `/hooks` after changing hook configuration.
See the [Codex hook documentation](https://learn.chatgpt.com/docs/hooks).

If agents ignore skills despite passing checks, inspect live hook delivery in the
client. A successful launch does not establish compliance with the instructions.
If Codex hooks fail on Windows, check Node and Python availability, then inspect
the actual `/hooks` executions. Native shell checks supplement this live check.

| Symptom | Cause | Fix |
|---|---|---|
| `deps.py check` shows `FAIL uv` / `node` / `python-packages` "not on PATH" although the setup worked | Old checkout: older versions checked against this terminal's stale PATH | `git pull`. The checks now use the PATH a new terminal would see. |
| `warn libreoffice` "soffice not on PATH" | LibreOffice's Windows installer leaves its folder off PATH | `git pull`, `python scripts\deps.py install-roles` (it adds `C:\Program Files\LibreOffice\program` to PATH), then open a new terminal. |
| `install-roles` says "install exited 2316632107" | winget's code for "already installed, nothing newer"; older checkouts counted it as a failure | `git pull`: it now counts as installed. |
| `warn` lines for tools you will not use here | Roles asked for more than this machine needs | `python scripts/bootstrap.py --roles <what you need>`; tools for other roles then show as "not needed here". |
| `-` for chrome, gimp, blender, cairo-pango | These cannot be checked automatically, so they are never installed without asking | Install them by hand only if this machine needs them; `install-roles` prints the exact command for each. |
| `raea` is on `0.1.0-canary.2` on Windows but `canary.3` on Linux | Expected: canary.3 has no Windows build | Nothing to do (`platform_pins` in `dependencies.toml`). |
| Node errors: sharp needs Node ≥ 20, or MCP servers need ≥ 22.12 | The system Node is too old (common on Linux: Node 18) | The setup and the MCP launcher pick a compatible Node themselves. On Linux, add fnm's lines to `~/.bashrc` and `~/.profile` so terminals get it too. |
| Playwright cannot launch a browser | Browsers missing, or Linux system libraries missing | `python scripts/bootstrap.py`; on Linux, run the `apt-get` command Playwright prints. |
| "SETUP OUT OF DATE" at the start of a Claude Code session | The checkout changed since this machine was set up | `python scripts/bootstrap.py --yes`. |
| Bootstrap stops at the schedule question with `EOFError` | Older bootstrap still prompted with `--yes` or without an interactive terminal | Update the checkout; these modes now use automatic schedule handling and preserve jobs owned by another checkout. On older copies, add `--auto-schedules`. |
| `OBSIDIAN_VAULT_PATH points to a path that does not exist` | A vault is configured but its drive is not mounted | Plug in or mount the drive. To work without a vault, leave `OBSIDIAN_VAULT_PATH=` empty in `.env`. |
| Vault drive gives I/O errors on Linux | NTFS drive marked dirty by Windows | Run `chkdsk /f` on it from Windows. |
| Nightly jobs are missing | You answered no, or the setup ran with `--no-schedules` (the vault watchdog is only set up when a vault is configured) | `python scripts/schedule.py install vault-index` (also `housekeeper`, `vault-watchdog`). |
| A commit is blocked with "pre-commit: FAILED …" | The commit breaks a repo rule (one-OS script, machine path, pins, register out of date) | Fix what it prints; `python scripts/deps.py docs` regenerates the register. |

### Still stuck
Run `python scripts/doctor.py` and send the **Summary** section. `docs/DEPENDENCIES.md` lists every tool, what
it is for, how to update it and what to do when it breaks.

---

## For maintainers: how this stays fixed

- **Fresh setup CI** (`.github/workflows/fresh-setup.yml`) runs this guide's steps on clean Windows, Ubuntu and
  macOS (Apple silicon) runners, the only macOS testing the repo gets: the paste-block tools, the bootstrap with every role, then the checks from a new terminal
  (`deps.py check --strict`, the doctor). It runs monthly (on the 1st) and whenever a setup file changes. If it goes red,
  a fresh laptop would have failed the same way.
- **Cross-platform CI** runs the tests on both OSes on every push.
- When a new setup problem turns up, fix it in the setup scripts (not on the one machine), and add a row here.
