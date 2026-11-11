# Dependencies

Everything this repo needs from outside itself, how each piece is pinned and installed on the Linux and the
Windows machine, how to update it, and what to do when it breaks.

The source of truth is [`dependencies.toml`](../dependencies.toml). The register at the bottom of this page is
generated from it (`python scripts/deps.py docs`), and CI fails if the two disagree, so edit the TOML, not the
tables.

## The tool

One cross-platform script handles every dependency the same way on both machines:

| Command | What it does |
|---|---|
| `python scripts/deps.py list` | Every dependency, its kind, whether it is required, and its pin |
| `python scripts/deps.py check` | Is each one installed, at an acceptable version, and does every file that pins it agree? Required ones fail; optional ones warn with the install command |
| `python scripts/deps.py check --pins-only` | Only the pin agreement (what CI and the bootstrap run) |
| `python scripts/deps.py install ID` | Installs one dependency the right way for this OS (winget on Windows, apt/fnm on Linux, a checksum-verified download for GitHub releases such as raea) |
| `python scripts/deps.py outdated` | Newest upstream version of every pinned dependency next to our pin |
| `python scripts/deps.py set-pin ID VERSION` | Moves a pin in every file that writes it (MCP configs, manifest) in one step |
| `python scripts/deps.py docs` | Regenerates the register below |

On Linux use `python3`; on Windows `python` or `py`. Make shortcuts: `make deps`, `make deps-install ID=raea`,
`make deps-outdated`, `make bootstrap`.

A fresh machine, or one that has drifted, runs `python scripts/bootstrap.py` (Windows: `py scripts\bootstrap.py`).
It creates the venv, installs the locked Python and Node packages, installs the Playwright browsers, checks
the pins, and ends with `deps.py check` so anything optional that is missing shows up as a warning with its
install command.

## How dependencies are managed

| Kind | Pinned where | Installed by |
|---|---|---|
| Python libraries | `uv.lock` (exact), ranges in each `pyproject.toml`; `requirements.txt` mirrors the root pyproject for CI | `uv sync --locked` |
| Node libraries | `package-lock.json` files | `npm ci` |
| npm MCP servers | `@pkg@version` in `.mcp.json` and `mcp/agents/*.json`, mirrored in the manifest | `npx` on demand, through `scripts/mcp-npx.mjs` |
| uvx MCP servers | `pkg@version` or a git commit in the same configs | `uvx` on demand |
| Remote MCP servers | URL only; hosted by the vendor | nothing local; OAuth through `/mcp` |
| GitHub-release tools (raea) | `pin` in the manifest + `[releases.ID]` asset names | `deps.py install ID` (download, SHA-256 check, PATH link) |
| uv tools (browser-act) | `pin` in the manifest | `uv tool install pkg==pin` |
| System tools and apps | not pinned (OS package manager versions) | `deps.py install ID` runs the per-OS command, or prints the manual step |
| Third-party skills | content hashes in `skills-lock.json` | the `skills` CLI that wrote the lock file |

**Machine roles.** Optional tools are tagged with the roles that need them (`research`, `video`, `slides`,
`images`, `3d`). Each machine records its roles in `.env` as `AUTOMATA_ROLES` (the bootstrap asks once, or
`--roles video,research`, or `all`); the bootstrap installs those tools (`python scripts/deps.py install-roles`),
and `deps.py check` and the doctor only expect them. Tools that cannot be checked automatically (GIMP, Chrome,
Blender, Cairo) are listed with their install command, never reinstalled blindly.

**No vault.** The Obsidian vault is optional too: with `OBSIDIAN_VAULT_PATH` empty, notes, drafts and session logs
live in `workspace/vault/` in the same layout (git-ignored, never cleaned by the housekeeper). A configured vault
that is missing (drive not mounted) stops the agents instead of silently writing to the local folder.

Rules that keep the two machines identical:

- **Pin exactly** anything fetched at run time (`npx`, `uvx`, GitHub releases). An unpinned `uvx blender-mcp`
  can give each machine a different version on the same day.
- **One pin, many files:** when a version is written in several configs, list every file in the manifest's
  `pin_files`. `deps.py check --pins-only` fails if any of them disagree, and `set-pin` changes them together.
- **No machine paths** in configs. MCP arguments use `~/...`, which `scripts/mcp-npx.mjs` expands per user
  (so the Playwright profile is `~/.agency/chrome-instagram-cdp` on both machines).
- **One implementation:** installers and launchers are Python (or Node for MCP launch), never a `.sh` + `.ps1`
  pair. See the Cross-Platform Rule in `AGENTS.md`.

## Quarterly update routine

Dependencies are updated on a schedule, not ad hoc. The `Dependency update` workflow
(`.github/workflows/dependency-update.yml`) runs at 03:00 UTC on 1 January, April, July and October, and on
demand from GitHub (Actions -> Dependency update -> Run workflow). It:

1. computes safe updates (`python scripts/deps.py update`, also runnable by hand on Linux or Windows, or
   `make deps-update`);
2. tests them on Ubuntu **and** Windows: the cross-platform checks, the pinned-build check, the test suite and the
   security audit of the updated `uv.lock`;
3. pushes them to a `deps/update-YYYY-MM-DD` branch and opens an issue with the report and a one-click link to
   create the pull request. **Nothing reaches `main` until you merge it.** After merging, every machine updates
   itself on its next `git pull`.

What it will and will not do:

| Rule | Why |
|---|---|
| Only versions published at least **14 days** ago (`--cooldown-days`) | brand-new releases are where broken and malicious versions show up |
| **Never a major version** (or a 0.x minor, where minors break): listed under *Needs a person* | majors change APIs; they need a changelog read and a deliberate update |
| **MCP servers are started and handshaken** before and after; a bump that removes a tool is reverted | skills, hooks and settings call MCP tools by name |
| **Never downgrades**; a package already newer than the cool-down (a recent security fix) keeps its version | the cool-down must not undo a security bump |
| Node libraries are held back as a group if any changed package is too new | npm cannot exempt one package |
| GIMP, Blender and raea are **report-only** | they need the app or a GPU to verify |

What you do each quarter: open the issue, read *Needs a person*, merge the pull request if CI is green. The
majors it lists are the manual work for that quarter (one per commit, with the steps below).

## Updating a dependency

1. `python scripts/deps.py outdated` to see what is behind.
2. Read the upstream changelog for breaking changes.
3. Change the pin, then install:
   - pinned tools and MCP servers: `python scripts/deps.py set-pin ID NEW`, then `python scripts/deps.py install ID`
     (or restart the MCP client for npx/uvx servers);
   - Python libraries: `uv lock --upgrade-package NAME && uv sync --locked`;
   - Node libraries: `npm install NAME@NEW` (in the folder that owns the `package-lock.json`).
4. Check: `python scripts/deps.py check ID`, run the feature that uses it once (each entry's
   *Update* line below says how), and `make test`. For an MCP server, run
   `python scripts/mcp-smoke.py NAME --save before.txt` *before* moving the pin and
   `python scripts/mcp-smoke.py NAME --compare before.txt` after: it starts the server as configured, does the MCP
   handshake and fails if any tool disappeared (skills, hooks and settings refer to tools by name).
5. Commit the pin change on its own (`chore(deps): bump ID to NEW`). The `Cross-platform` workflow then
   checks the pins, the install resolution and the tests on Linux and Windows before you switch machines.
6. On the other machine: `git pull`, then `python scripts/deps.py install ID` (or re-run the bootstrap).

Update one dependency per commit, so a break points at exactly one change.

## When something breaks

1. **Find out what changed.** `python scripts/deps.py check` shows anything missing, too old, or pinned
   inconsistently. `git log -p dependencies.toml uv.lock package-lock.json .mcp.json mcp/` shows recent pin moves.
2. **Read that dependency's *If it breaks* line** in the register below; most failures are a missing app, an
   expired login, or a version mismatch between two halves (an MCP server and its app plugin).
3. **Roll back the pin** if a recent update caused it:
   `python scripts/deps.py set-pin ID OLD && python scripts/deps.py install ID`
   (Python: `git checkout HEAD~1 -- uv.lock && uv sync --locked`). Commit the rollback so the other machine
   gets it too.
4. **Works on one machine only?** Run `python scripts/deps.py check` on both and compare; check the latest
   `Cross-platform` workflow run on GitHub, which shows which OS failed and at which step.
5. **Record it:** if the fix is not obvious, add it to that dependency's `on_break` in `dependencies.toml`
   and regenerate this page, so the next person finds it here.

## Security audits

The `Security and quality` workflow audits, on every push: a fresh install of `requirements.txt`, **`uv.lock`**
(what the machines actually install), and `npm audit` in each Node package. Until 2026-11-07 it audited only the
fresh install, so the lockfile had quietly collected 107 known vulnerabilities; those were cleared with targeted
`uv lock --upgrade-package` bumps.

To check locally before pushing:
```bash
uv export --frozen --no-hashes --no-emit-project --no-header | grep -v '^-e \|^\./' > /tmp/locked.txt
uvx pip-audit -r /tmp/locked.txt --no-deps --disable-pip   # plus the --ignore-vuln list from security.yml
```
Fix a finding with `uv lock --upgrade-package NAME`, run `make test`, commit `uv.lock`.

### Accepted security advisories

Ignored in `.github/workflows/security.yml` only because they do not apply to how this repo uses the package.
Review each one whenever the package is upgraded, and remove the ignore once a fixed version is locked.

| Package | Advisories | Why it does not apply | Revisit when |
|---|---|---|---|
| chromadb 1.5.9 | PYSEC-2026-311, -3813, -3814, -3815 | All are in the Chroma **server** (pre-auth code injection, tenant permissions). We only use the embedded `PersistentClient`; no server is started. No fixed release exists. | the next chromadb release |

## Known gaps

- **notebooklm-mcp** is pinned at 4.4.0, two weeks behind latest on purpose (newer releases were days old); its
  Google login has expired and needs a one-time re-login (see its entry below).
- **Three Playwright versions** coexist: Node 1.61 (package-lock), Python 1.59 (uv.lock), and the MCP server's
  own. Each needs its own Chromium build; the bootstrap installs both library builds.
- **npm overrides:** `image-size` is forced to `^2.1.0` in `package.json` because pptxgenjs still asks
  for the vulnerable 1.x; the slide exporters were tested with it. Drop the override once pptxgenjs requires 2.x.

## Register

<!-- deps:start (generated by scripts/deps.py docs) -->

### Runtimes

| Dependency | Needed for | Required | Roles | Version | Pinned in |
|---|---|---|---|---|---|
| **Python** (`python`) | Runs every agent package, script and test. | yes | all | >= 3.12 | - |
| **uv** (`uv`) | Installs the locked Python environment (uv sync) and runs uvx MCP servers and uv tools. | yes | all | OS package manager | - |
| **Node.js** (`node`) | Runs npm MCP servers through scripts/mcp-npx.mjs, the HTML-to-PPTX tool and the ig-research scraper. | yes | all | >= 22.12 | - |
| **Homebrew (macOS)** (`brew`) | macOS package manager: installs Node.js, gh and the optional tools (ffmpeg, LibreOffice, ...). | yes | all | OS package manager | - |
| **Git** (`git`) | Repo sync between the two machines; the cross-platform checker lists files with it. | yes | all | OS package manager | - |
| **GitHub CLI (gh)** (`gh`) | Browser login to GitHub for cloning and pushing the private repo; lets agents read CI results. | no | - | OS package manager | - |

### Libraries

| Dependency | Needed for | Required | Roles | Version | Pinned in |
|---|---|---|---|---|---|
| **Python packages (root project)** (`python-packages`) | All Python libraries for the four agency packages and the root tooling, locked exactly in uv.lock. | yes | all | lockfile | `uv.lock` |
| **Node packages (root)** (`node-packages`) | playwright (HTML-to-PPTX screenshots), pptxgenjs, animate.css. | no | - | lockfile | `package-lock.json` |
| **Node packages (ig-research scraper)** (`ig-research-packages`) | puppeteer-core for the CDP Instagram scraper. | no | - | lockfile | `agents/automata_core/ig-research/package-lock.json` |
| **Playwright Chromium builds** (`playwright-browsers`) | Headless Chromium for the Node playwright (1.61) and the Python playwright (1.59); each version needs its own browser build. | no | - | per playwrig | - |

### MCP servers

| Dependency | Needed for | Required | Roles | Version | Pinned in |
|---|---|---|---|---|---|
| **@playwright/mcp** (`playwright-mcp`) | Browser automation MCP for research; reuses the ~/.agency/chrome-instagram-cdp profile. | no | - | 0.0.84 | `.mcp.json`, `mcp/agents/research.json`, `dependencies.toml` |
| **chrome-devtools-mcp** (`chrome-devtools-mcp`) | Console, network and screenshot inspection for research. | no | - | 1.12.0 | `mcp/agents/research.json`, `dependencies.toml` |
| **@roomi-fields/notebooklm-mcp** (`notebooklm-mcp`) | Grounded Q&A against NotebookLM sources. | no | - | 4.4.0 | `mcp/agents/research.json`, `dependencies.toml` |
| **Earshot audio analysis and sound design** (`earshot`) | CPU audio analysis, soundtrack review and procedural SFX for Codex and Claude. | no | video | 4ac3d2ac2b15 | `dependencies.toml` |
| **blender-mcp** (`blender-mcp`) | Drive Blender from the storyboard agent (asset prep, Blender-only shots). | no | 3d | 2.0.0 | `.mcp.json`, `mcp/agents/storyboard.json`, `dependencies.toml` |
| **gimp-mcp (server + GIMP plugin)** (`gimp-mcp`) | Local non-generative image editing through GIMP 3.2. | no | images | 732586538554 | `.mcp.json`, `mcp/agents/storyboard.json`, `dependencies.toml` |
| **Higgsfield MCP (remote)** (`higgsfield-mcp`) | Image and video generation. | no | - | hosted by vendor | `.mcp.json` |
| **Magnific MCP (remote)** (`magnific-mcp`) | Upscaling, restyling, generation history. | no | - | hosted by vendor | `.mcp.json` |
| **Figma desktop MCP** (`figma-mcp`) | Read/write Figma frames for editable final assets. | no | - | hosted by vendor | `.mcp.json` |

### Tools

| Dependency | Needed for | Required | Roles | Version | Pinned in |
|---|---|---|---|---|---|
| **raea (Render Anything Engine)** (`raea`) | Local GPU renderer for 3D previz (greybox keyframes and camera-move clips). | no | video, 3d | 0.1.0-canary.3 | `dependencies.toml` |
| **browser-act CLI** (`browser-act`) | Stealth browser extraction for research (--scraper browser-act). | no | research | 1.6.2 | `dependencies.toml` |

### System tools

| Dependency | Needed for | Required | Roles | Version | Pinned in |
|---|---|---|---|---|---|
| **ffmpeg / ffprobe** (`ffmpeg`) | Upscale and crop-to-motion b-roll, video agent edits, raea media. | no | video | OS package manager | - |
| **Poppler (pdftoppm)** (`poppler`) | PDF page rendering for slide checks and pdf2image. | no | slides | OS package manager | - |
| **ImageMagick (magick)** (`imagemagick`) | Raster image conversion for slide work and the Higgsfield brand kit. | no | slides, images | OS package manager | - |
| **LibreOffice (soffice)** (`libreoffice`) | PPTX to PDF/thumbnail rendering for slide work. | no | slides | OS package manager | - |
| **Cairo / Pango libraries** (`cairo-pango`) | Native libraries behind weasyprint and cairosvg (PDF and SVG rendering). | no | slides | OS package manager | - |
| **Motiscope motion analysis** (`motiscope`) | Optional screen-recording timing analysis for agency-motion-design. | no | - | c0ce3ddedfbe | `dependencies.toml` |
| **Android platform-tools (adb)** (`adb`) | Mobile-only Instagram search through redroid/BlueStacks. | no | research | OS package manager | - |

### Apps

| Dependency | Needed for | Required | Roles | Version | Pinned in |
|---|---|---|---|---|---|
| **Google Chrome or Microsoft Edge** (`chrome`) | Persistent logged-in Instagram profile for CDP research. | no | research | OS package manager | - |
| **GIMP 3.2** (`gimp`) | Host app for the GIMP MCP. | no | images | OS package manager | - |
| **Blender** (`blender`) | Host app for the Blender MCP. | no | 3d | OS package manager | - |
| **Obsidian vault (optional)** (`obsidian-vault`) | Brand notes, drafts and research; source for the vault search index. Optional: without it, notes stay in workspace/vault. | no | - | OS package manager | - |

### Skills and CI

| Dependency | Needed for | Required | Roles | Version | Pinned in |
|---|---|---|---|---|---|
| **Third-party agent skills** (`external-skills`) | browser-act and eight higgsfield-* skills installed from GitHub, hashes recorded in skills-lock.json. | no | - | hashes in lock | `skills-lock.json` |
| **GitHub Actions** (`github-actions`) | actions/checkout, setup-python and setup-node in the Security and Cross-platform workflows. | no | - | tag in workflow | `.github/workflows/security.yml`, `.github/workflows/cross-platform.yml` |

### Install, update, and what to do when it breaks

#### Python (`python`)
- **Install:** linux: `sudo apt-get install -y python3 python3-venv`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id Python.Python.3.12`; macos: `brew install python@3.12`
- **Update:** Install the newer Python, delete .venv, re-run bootstrap. Keep requires-python in pyproject.toml in step.
- **If it breaks:** Recreate the venv: delete .venv and run the bootstrap. On Windows, check the 'python' on PATH is not the Microsoft Store stub.

#### uv (`uv`)
- **Install:** linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id astral-sh.uv`; macos: `brew install uv`
- **Update:** uv self update
- **If it breaks:** uv self update; if uv sync fails, run `uv lock --check` to see whether uv.lock is stale.

#### Node.js (`node`)
- **Install:** linux: `fnm install 22`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id OpenJS.NodeJS.LTS`; macos: `brew install node`
  The default `node` on PATH must be 22.12+ (sharp, the slide exporters). Linux with fnm: `fnm install 22 && fnm default 22`, and load fnm in ~/.bashrc: `export PATH="$HOME/.local/share/fnm:$PATH"; eval "$(fnm env --shell bash)"`. A distro's nodejs 22 package also works.
- **Update:** Install a newer LTS (fnm install 24 / winget upgrade OpenJS.NodeJS.LTS). mcp-npx.mjs picks the newest compatible one automatically.
- **If it breaks:** `node --version` must print v22.12 or newer; if it shows an older system Node, load fnm in your shell (see install note). `node scripts/mcp-npx.mjs --which` shows which Node the MCP servers will use. 'none' = install Node 22+. An older default Node is fine as long as a newer one exists (fnm, nvm, PATH).

#### Homebrew (macOS) (`brew`)
- **Install:** macos: `manual: install Homebrew from https://brew.sh (the docs/SETUP.md macOS block does it; it asks for your Mac password once), then open a new terminal`
- **Update:** brew update && brew upgrade (Homebrew also updates itself before installs).
- **If it breaks:** `brew` not found after installing: run `eval "$(/opt/homebrew/bin/brew shellenv)"` (Intel Macs: /usr/local/bin/brew) and add that line to ~/.zprofile; `brew doctor` explains the rest.

#### Git (`git`)
- **Install:** linux: `sudo apt-get install -y git`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id Git.Git`; macos: `xcode-select --install`
- **Update:** Package manager upgrade.
- **If it breaks:** Line-ending trouble: .gitattributes pins *.sh/*.py to LF and *.cmd to CRLF; run `git add --renormalize .` once if a script shows CRLF.

#### GitHub CLI (gh) (`gh`)
- **Install:** linux: `sudo apt-get install -y gh`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id GitHub.cli`; macos: `brew install gh`
- **Update:** Package manager upgrade.
- **If it breaks:** `gh auth status`; if logged out: `gh auth login --web --git-protocol https`, then `gh auth setup-git`. Pushing workflow files needs the workflow scope: `gh auth refresh -s workflow`.

#### Python packages (root project) (`python-packages`)
- **Install:** all: `uv sync --locked`
- **Update:** One package: `uv lock --upgrade-package NAME` then `uv sync`. Everything: `uv lock --upgrade`. Run tests, commit uv.lock. Ranges live in pyproject.toml files; requirements.txt mirrors the root pyproject for CI and must be edited with it.
- **If it breaks:** `uv sync --locked` reinstalls exactly what uv.lock says. If a just-upgraded package broke something, `git checkout HEAD~1 -- uv.lock && uv sync --locked` rolls it back.

#### Node packages (root) (`node-packages`)
- **Install:** all: `npm ci`
- **Update:** npm install PKG@VERSION (updates package-lock.json), run the tool once, commit both files. After a playwright bump also run `npx playwright install chromium`.
- **If it breaks:** npm ci restores node_modules exactly from package-lock.json.

#### Node packages (ig-research scraper) (`ig-research-packages`)
- **Install:** all: `npm ci --prefix agents/automata_core/ig-research`
- **Update:** npm install puppeteer-core@VERSION --prefix agents/automata_core/ig-research
- **If it breaks:** npm ci --prefix agents/automata_core/ig-research

#### Playwright Chromium builds (`playwright-browsers`)
- **Install:** all: `npx playwright install chromium && .venv python -m playwright install chromium`
- **Update:** Runs automatically in bootstrap; re-run after bumping either playwright package.
- **If it breaks:** 'Executable doesn't exist at ...ms-playwright...' means the browser for that playwright version is missing: re-run the bootstrap (or the two install commands).

#### @playwright/mcp (`playwright-mcp`)
- **Update:** python scripts/deps.py set-pin playwright-mcp NEW, restart the MCP client, run one browse.
- **If it breaks:** Run `node scripts/mcp-npx.mjs -y @playwright/mcp@PIN --help`. If the profile is locked, close the Chrome window opened by scripts/open-instagram-session.py.

#### chrome-devtools-mcp (`chrome-devtools-mcp`)
- **Update:** python scripts/deps.py set-pin chrome-devtools-mcp NEW
- **If it breaks:** Needs Node ^20.19/^22.12/>=23: check `node scripts/mcp-npx.mjs --which`.

#### @roomi-fields/notebooklm-mcp (`notebooklm-mcp`)
- **Update:** python scripts/deps.py set-pin notebooklm-mcp NEW
- **If it breaks:** Usually an expired Google session (check with its server_health tool: authenticated false). Log in once in a terminal: `node scripts/mcp-npx.mjs -y -p @roomi-fields/notebooklm-mcp@PIN notebooklm-mcp-setup-auth` (a visible Chrome opens). Since 4.x every tool is renamed (ask_question -> notebook_ask, list_notebooks -> notebook_list, ...); the saved library in ~/.local/share/notebooklm-mcp carries over. Needs Node 22.

#### Earshot audio analysis and sound design (`earshot`)
- **Install:** all: `python scripts/earshot.py install`
  Isolated Python 3.12 venv with CPU torch; downloads pinned audio models (~1.1 GB). Requires ffmpeg/ffprobe.
- **Update:** python scripts/deps.py set-pin earshot COMMIT, then python scripts/deps.py install earshot.
- **If it breaks:** Run python scripts/earshot.py doctor --load; model repair: doctor --fetch. Restart both MCP clients after setup.

#### blender-mcp (`blender-mcp`)
- **Update:** python scripts/deps.py set-pin blender-mcp NEW, then install the matching addon.py from the blender-mcp repo into Blender.
- **If it breaks:** Blender must be open with the BlenderMCP addon connected (N panel > BlenderMCP > Connect). Server and addon versions must match.

#### gimp-mcp (server + GIMP plugin) (`gimp-mcp`)
- **Install:** all: `python scripts/install-gimp-mcp.py`
  Reads this pin and detects GIMP 3.x, including Flatpak.
- **Update:** python scripts/deps.py set-pin gimp-mcp NEWCOMMIT, re-install the plugin, restart GIMP. Server and plugin must be the same commit.
- **If it breaks:** GIMP running? Tools > MCP > Start MCP Server (localhost:9877). After a GIMP minor upgrade the plug-ins folder moves: re-install the plugin.

#### Higgsfield MCP (remote) (`higgsfield-mcp`)
- **Update:** Hosted by Higgsfield; nothing to update locally.
- **If it breaks:** Re-authenticate with /mcp in Claude Code. Check credits (balance tool).

#### Magnific MCP (remote) (`magnific-mcp`)
- **Update:** Hosted by Magnific; nothing to update locally.
- **If it breaks:** Re-authenticate with /mcp. Never fall back to Zen/Selenium automation for Magnific.

#### Figma desktop MCP (`figma-mcp`)
- **Install:** all: `manual: install Figma desktop and enable its Dev Mode MCP server`
- **Update:** Updates with the Figma desktop app.
- **If it breaks:** ECONNREFUSED = Figma desktop is not running or its MCP server is off.

#### raea (Render Anything Engine) (`raea`)
- **Install:** `python scripts/deps.py install raea`
- **Update:** `python scripts/deps.py outdated` shows the newest engine release; `python scripts/deps.py set-pin raea NEW`, `python scripts/deps.py install raea`, then re-render skills/previz-3d/templates/greybox-shot.tsx and run `raea scene lint` on it. Canary releases sometimes skip a platform: `python scripts/deps.py verify-downloads` checks, and `[releases.raea].platform_pins` keeps that platform on the last release that has a build.
- **If it breaks:** Canary software. Roll back: `python scripts/deps.py set-pin raea OLD && python scripts/deps.py install raea`. Upstream's own installer can pick a web-* release and 404; use deps.py instead.

#### browser-act CLI (`browser-act`)
- **Install:** all: `uv tool install --python 3.12 --force browser-act-cli==1.6.2 && uv tool update-shell`
- **Update:** python scripts/deps.py set-pin browser-act NEW && python scripts/deps.py install browser-act
- **If it breaks:** Reinstall: `uv tool install --python 3.12 --force browser-act-cli==PIN` (1.x ships only Python 3.12 wheels). Session mode needs the saved browser named in BROWSER_ACT_BROWSER (default instagram-research; `browser-act browser list`). Free for local Chrome browsers, stealth-extract and captcha solving; only BrowserAct proxies and more than 5 stealth browsers cost credits, and the scraper uses a proxy only when BROWSER_ACT_PROXY_REGION is set.

#### ffmpeg / ffprobe (`ffmpeg`)
- **Install:** linux: `sudo apt-get install -y ffmpeg`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id Gyan.FFmpeg`; macos: `brew install ffmpeg`
- **Update:** Package manager upgrade.
- **If it breaks:** Not on PATH after a winget install: open a new terminal.

#### Poppler (pdftoppm) (`poppler`)
- **Install:** linux: `sudo apt-get install -y poppler-utils`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id oschwartz10612.Poppler`; macos: `brew install poppler`
- **Update:** Package manager upgrade.
- **If it breaks:** pdf2image 'Unable to get page count' = pdftoppm not on PATH.

#### ImageMagick (magick) (`imagemagick`)
- **Install:** linux: `sudo apt-get install -y imagemagick`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id ImageMagick.ImageMagick`; macos: `brew install imagemagick`
  Ubuntu/Mint ship ImageMagick 6 as `convert`; v7 adds `magick`.
- **Update:** Package manager upgrade.
- **If it breaks:** On Linux, ImageMagick 6 has no `magick` command; the tools fall back to `convert`.

#### LibreOffice (soffice) (`libreoffice`)
- **Install:** linux: `sudo apt-get install -y libreoffice`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id TheDocumentFoundation.LibreOffice`; macos: `brew install --cask libreoffice`
- **Update:** Package manager upgrade.
- **If it breaks:** Windows: python scripts/deps.py install-roles adds the LibreOffice program folder to PATH; open a new terminal.

#### Cairo / Pango libraries (`cairo-pango`)
- **Install:** linux: `sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libcairo2`; windows: `manual: install the GTK3 runtime (MSYS2: pacman -S mingw-w64-x86_64-pango) and add its bin to PATH`; macos: `brew install pango cairo`
- **Update:** Package manager upgrade.
- **If it breaks:** 'cannot load library libgobject' / 'no library called cairo' = the native runtime is missing or not on PATH.

#### Motiscope motion analysis (`motiscope`)
- **Install:** all: `python scripts/motiscope.py install`
- **Update:** python scripts/deps.py set-pin motiscope FULL_COMMIT_SHA; install and smoke-test, then regenerate dependency docs.
- **If it breaks:** Use the repo virtualenv with scripts/motiscope.py; install ffmpeg through deps.py if check fails. A modified checkout is refused.

#### Android platform-tools (adb) (`adb`)
- **Install:** linux: `sudo apt-get install -y adb`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id Google.PlatformTools`; macos: `brew install --cask android-platform-tools`
- **Update:** Package manager upgrade.
- **If it breaks:** `adb devices` empty = emulator not running or not connected (adb connect HOST:PORT).

#### Google Chrome or Microsoft Edge (`chrome`)
- **Install:** linux: `manual: install google-chrome or chromium`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id Google.Chrome`; macos: `brew install --cask google-chrome`
- **Update:** Updates itself.
- **If it breaks:** CDP not reachable: run `python scripts/open-instagram-session.py` and keep that window open.

#### GIMP 3.2 (`gimp`)
- **Install:** linux: `flatpak install flathub org.gimp.GIMP`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id GIMP.GIMP.3`; macos: `brew install --cask gimp`
- **Update:** App update; after a minor version change re-install the gimp-mcp plugin.
- **If it breaks:** See gimp-mcp.

#### Blender (`blender`)
- **Install:** linux: `snap install blender --classic`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id BlenderFoundation.Blender`; macos: `brew install --cask blender`
- **Update:** App update; keep the BlenderMCP addon version matched to blender-mcp.
- **If it breaks:** See blender-mcp.

#### Obsidian vault (optional) (`obsidian-vault`)
- **Install:** all: `manual: the bootstrap asks for the vault folder and writes OBSIDIAN_VAULT_PATH to .env (empty = no vault)`
- **Update:** Synced between machines outside git.
- **If it breaks:** `OBSIDIAN_VAULT_PATH ... does not exist`: the drive is not mounted (the agents stop rather than write elsewhere). Linux I/O errors on an NTFS drive: run chkdsk on Windows. Index stale: make vault-index. To work without a vault, set OBSIDIAN_VAULT_PATH to empty.

#### Third-party agent skills (`external-skills`)
- **Update:** Re-install through the `skills` CLI that wrote skills-lock.json (`npx skills --help`), review the diff, commit.
- **If it breaks:** Restore a skill folder from git; skills-lock.json holds the hash of the version that worked.

#### GitHub Actions (`github-actions`)
- **Update:** Bump the @vN tag in both workflow files together.
- **If it breaks:** Read the failing job log on GitHub; the Cross-platform job names the OS that broke.

<!-- deps:end -->
