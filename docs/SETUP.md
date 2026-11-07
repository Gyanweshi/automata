# Setting Up a Machine

Read this before setting up a new laptop or helping someone else set one up. Every problem listed under
Troubleshooting has actually happened on a fresh Windows or Linux machine, and each one has a known fix.

The short version: **paste one block, answer three questions, read the summary at the end.**

---

## 1. Fresh machine (nothing installed, not even Python)

Open a terminal: **PowerShell** on Windows (Start menu, then "PowerShell"; not the old Command Prompt) or
**Terminal** on Linux. `cd` to the folder where the repo should live, e.g. `cd D:\` on Windows, then paste the
block for your OS.

**Windows**
```powershell
foreach ($id in "Git.Git", "GitHub.cli", "astral-sh.uv") { winget install -e --id $id --accept-source-agreements --accept-package-agreements }
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User") + ";$env:LOCALAPPDATA\Microsoft\WinGet\Links"
gh auth status 2>$null; if ($LASTEXITCODE) { gh auth login --web --git-protocol https }; gh auth setup-git
if (-not (Test-Path automata)) { gh repo clone Gyanweshi/automata }; Set-Location automata
uv run --no-project --python 3.12 scripts\bootstrap.py --yes
```

**Linux** (Ubuntu, Mint, Debian; on macOS replace the first line with `xcode-select --install; brew install gh`)
```bash
sudo apt-get update && sudo apt-get install -y git curl gh
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh; export PATH="$HOME/.local/bin:$PATH"
gh auth status >/dev/null 2>&1 || gh auth login --web --git-protocol https; gh auth setup-git
[ -d automata ] || gh repo clone Gyanweshi/automata; cd automata
uv run --no-project --python 3.12 scripts/bootstrap.py --yes
```

A browser opens once for the GitHub login: approve it. The rest takes about 5–10 minutes, longer with all the
optional tools (LibreOffice alone is a large download). Running the block again is safe; it skips what is
already there.

### What the setup does
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

### After setup

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
| `OBSIDIAN_VAULT_PATH points to a path that does not exist` | A vault is configured but its drive is not mounted | Plug in or mount the drive. To work without a vault, leave `OBSIDIAN_VAULT_PATH=` empty in `.env`. |
| Vault drive gives I/O errors on Linux | NTFS drive marked dirty by Windows | Run `chkdsk /f` on it from Windows. |
| Nightly jobs are missing | You answered no, or the setup ran with `--no-schedules` (the vault watchdog is only set up when a vault is configured) | `python scripts/schedule.py install vault-index` (also `housekeeper`, `vault-watchdog`). |
| A commit is blocked with "pre-commit: FAILED …" | The commit breaks a repo rule (one-OS script, machine path, pins, register out of date) | Fix what it prints; `python scripts/deps.py docs` regenerates the register. |

### Still stuck
Run `python scripts/doctor.py` and send the **Summary** section. `docs/DEPENDENCIES.md` lists every tool, what
it is for, how to update it and what to do when it breaks.

---

## For maintainers: how this stays fixed

- **Fresh setup CI** (`.github/workflows/fresh-setup.yml`) runs this guide's steps on clean Windows and Ubuntu
  runners: the paste-block tools, the bootstrap with every role, then the checks from a new terminal
  (`deps.py check --strict`, the doctor). It runs weekly and whenever a setup file changes. If it goes red,
  a fresh laptop would have failed the same way.
- **Cross-platform CI** runs the tests on both OSes on every push.
- When a new setup problem turns up, fix it in the setup scripts (not on the one machine), and add a row here.
