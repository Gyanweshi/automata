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

Rules that keep the two machines identical:

- **Pin exactly** anything fetched at run time (`npx`, `uvx`, GitHub releases). An unpinned `uvx blender-mcp`
  can give each machine a different version on the same day.
- **One pin, many files:** when a version is written in several configs, list every file in the manifest's
  `pin_files`. `deps.py check --pins-only` fails if any of them disagree, and `set-pin` changes them together.
- **No machine paths** in configs. MCP arguments use `~/...`, which `scripts/mcp-npx.mjs` expands per user
  (so the Playwright profile is `~/.agency/chrome-instagram-cdp` on both machines).
- **One implementation:** installers and launchers are Python (or Node for MCP launch), never a `.sh` + `.ps1`
  pair. See the Cross-Platform Rule in `AGENTS.md`.

## Updating a dependency

1. `python scripts/deps.py outdated` to see what is behind.
2. Read the upstream changelog for breaking changes.
3. Change the pin, then install:
   - pinned tools and MCP servers: `python scripts/deps.py set-pin ID NEW`, then `python scripts/deps.py install ID`
     (or restart the MCP client for npx/uvx servers);
   - Python libraries: `uv lock --upgrade-package NAME && uv sync --locked`;
   - Node libraries: `npm install NAME@NEW` (in the folder that owns the `package-lock.json`).
4. Check: `python scripts/deps.py check ID`, run the feature that uses it once (each entry's
   *Update* line below says how), and `make test`.
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

## Known gaps (found while building this register)

- **MCP servers are behind upstream** (2026-11-07): chrome-devtools-mcp 0.23.0 (latest 1.12.0),
  notebooklm-mcp 1.5.9 (4.6.0), apify-mcp 0.9.20 (0.21.4), playwright-mcp 0.0.73 (0.0.84), browser-act 0.1.23
  (1.6.2). Update one at a time with the steps above.
- **PyMuPDF** is used by `tools/pdf_utils/extract_furlove_pdf_assets.py` but is not declared in any
  pyproject or lock file.
- **ImageMagick** is not installed on the Linux machine; the slides agent's raster conversion and the
  higgsfield brand kit need it there.
- **Three Playwright versions** coexist: Node 1.61 (package-lock), Python 1.59 (uv.lock), and the MCP server's
  own. Each needs its own Chromium build; the bootstrap installs both library builds.

## Register

<!-- deps:start (generated by scripts/deps.py docs) -->

### Runtimes

| Dependency | Needed for | Required | Version | Pinned in |
|---|---|---|---|---|
| **Python** (`python`) | Runs every agent package, script and test. | yes | >= 3.12 | - |
| **uv** (`uv`) | Installs the locked Python environment (uv sync) and runs uvx MCP servers and uv tools. | yes | OS package manager | - |
| **Node.js (for MCP servers)** (`node`) | Runs npm MCP servers through scripts/mcp-npx.mjs, the HTML-to-PPTX tool and the ig-research scraper. | yes | >= 22.12 | - |
| **Git** (`git`) | Repo sync between the two machines; the cross-platform checker lists files with it. | yes | OS package manager | - |

### Libraries

| Dependency | Needed for | Required | Version | Pinned in |
|---|---|---|---|---|
| **Python packages (root project)** (`python-packages`) | All Python libraries for the four agency packages and the root tooling, locked exactly in uv.lock. | yes | lockfile | `uv.lock` |
| **Python packages (OpenSwarm sub-project)** (`openswarm-python`) | Agency Swarm and the OpenSwarm agents' libraries (slides, video, docs, data agents). | no | lockfile | `agents/openedswarm_core/uv.lock` |
| **Node packages (root)** (`node-packages`) | playwright (HTML-to-PPTX screenshots), pptxgenjs, animate.css. | no | lockfile | `package-lock.json` |
| **Node packages (ig-research scraper)** (`ig-research-packages`) | puppeteer-core for the CDP Instagram scraper. | no | lockfile | `agents/automata_core/ig-research/package-lock.json` |
| **Playwright Chromium builds** (`playwright-browsers`) | Headless Chromium for the Node playwright (1.61) and the Python playwright (1.59); each version needs its own browser build. | no | per playwrig | - |

### MCP servers

| Dependency | Needed for | Required | Version | Pinned in |
|---|---|---|---|---|
| **@playwright/mcp** (`playwright-mcp`) | Browser automation MCP for research; reuses the ~/.agency/chrome-instagram-cdp profile. | no | 0.0.73 | `.mcp.json`, `mcp/agents/research.json`, `dependencies.toml` |
| **chrome-devtools-mcp** (`chrome-devtools-mcp`) | Console, network and screenshot inspection for research. | no | 0.23.0 | `mcp/agents/research.json`, `dependencies.toml` |
| **@roomi-fields/notebooklm-mcp** (`notebooklm-mcp`) | Grounded Q&A against NotebookLM sources. | no | 1.5.9 | `mcp/agents/research.json`, `dependencies.toml` |
| **@apify/actors-mcp-server** (`apify-mcp`) | Apify actors (Instagram, LinkedIn extraction). | no | 0.9.20 | `mcp/agents/research.json`, `dependencies.toml` |
| **blender-mcp** (`blender-mcp`) | Drive Blender from the storyboard agent (asset prep, Blender-only shots). | no | 2.0.0 | `.mcp.json`, `mcp/agents/storyboard.json`, `dependencies.toml` |
| **gimp-mcp (server + GIMP plugin)** (`gimp-mcp`) | Local non-generative image editing through GIMP 3.2. | no | 732586538554 | `.mcp.json`, `mcp/agents/storyboard.json`, `dependencies.toml` |
| **Higgsfield MCP (remote)** (`higgsfield-mcp`) | Image and video generation. | no | hosted by vendor | `.mcp.json` |
| **Magnific MCP (remote)** (`magnific-mcp`) | Upscaling, restyling, generation history. | no | hosted by vendor | `.mcp.json` |
| **Figma desktop MCP** (`figma-mcp`) | Read/write Figma frames for editable final assets. | no | hosted by vendor | `.mcp.json` |

### Tools

| Dependency | Needed for | Required | Version | Pinned in |
|---|---|---|---|---|
| **raea (Render Anything Engine)** (`raea`) | Local GPU renderer for 3D previz (greybox keyframes and camera-move clips). | no | 0.1.0-canary.2 | `dependencies.toml` |
| **browser-act CLI** (`browser-act`) | Stealth browser extraction for research (--scraper browser-act). | no | 0.1.23 | `dependencies.toml` |

### System tools

| Dependency | Needed for | Required | Version | Pinned in |
|---|---|---|---|---|
| **ffmpeg / ffprobe** (`ffmpeg`) | Upscale and crop-to-motion b-roll, video agent edits, raea media. | no | OS package manager | - |
| **Poppler (pdftoppm)** (`poppler`) | PDF page rendering for slide checks and pdf2image. | no | OS package manager | - |
| **ImageMagick (magick)** (`imagemagick`) | Raster conversion for slides and the Higgsfield brand kit. | no | OS package manager | - |
| **LibreOffice (soffice)** (`libreoffice`) | PPTX to PDF/thumbnail rendering in the slides agent. | no | OS package manager | - |
| **Cairo / Pango libraries** (`cairo-pango`) | Native libraries behind weasyprint and cairosvg (PDF and SVG rendering). | no | OS package manager | - |
| **Android platform-tools (adb)** (`adb`) | Mobile-only Instagram search through redroid/BlueStacks. | no | OS package manager | - |

### Apps

| Dependency | Needed for | Required | Version | Pinned in |
|---|---|---|---|---|
| **Google Chrome or Microsoft Edge** (`chrome`) | Persistent logged-in Instagram profile for CDP research. | no | OS package manager | - |
| **GIMP 3.2** (`gimp`) | Host app for the GIMP MCP. | no | OS package manager | - |
| **Blender** (`blender`) | Host app for the Blender MCP. | no | OS package manager | - |
| **Obsidian vault (Brainiac2)** (`obsidian-vault`) | Brand notes, drafts and research; source for the vault search index. | yes | OS package manager | - |

### Skills and CI

| Dependency | Needed for | Required | Version | Pinned in |
|---|---|---|---|---|
| **Third-party agent skills** (`external-skills`) | browser-act, superdesign and eight higgsfield-* skills installed from GitHub, hashes recorded in skills-lock.json. | no | hashes in lock | `skills-lock.json` |
| **GitHub Actions** (`github-actions`) | actions/checkout, setup-python and setup-node in the Security and Cross-platform workflows. | no | tag in workflow | `.github/workflows/security.yml`, `.github/workflows/cross-platform.yml` |

### Install, update, and what to do when it breaks

#### Python (`python`)
- **Install:** linux: `sudo apt-get install -y python3 python3-venv`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id Python.Python.3.12`; macos: `brew install python@3.12`
- **Update:** Install the newer Python, delete .venv, re-run bootstrap. Keep requires-python in pyproject.toml in step.
- **If it breaks:** Recreate the venv: delete .venv and run the bootstrap. On Windows, check the 'python' on PATH is not the Microsoft Store stub.

#### uv (`uv`)
- **Install:** linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id astral-sh.uv`; macos: `brew install uv`
- **Update:** uv self update
- **If it breaks:** uv self update; if uv sync fails, run `uv lock --check` to see whether uv.lock is stale.

#### Node.js (for MCP servers) (`node`)
- **Install:** linux: `fnm install 22`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id OpenJS.NodeJS.LTS`; macos: `brew install node@22`
  Linux: or your distro's nodejs 22 package.
- **Update:** Install a newer LTS (fnm install 24 / winget upgrade OpenJS.NodeJS.LTS). mcp-npx.mjs picks the newest compatible one automatically.
- **If it breaks:** `node scripts/mcp-npx.mjs --which` shows which Node the MCP servers will use. 'none' = install Node 22+. An older default Node is fine as long as a newer one exists (fnm, nvm, PATH).

#### Git (`git`)
- **Install:** linux: `sudo apt-get install -y git`; windows: `winget install -e --accept-source-agreements --accept-package-agreements --id Git.Git`; macos: `xcode-select --install`
- **Update:** Package manager upgrade.
- **If it breaks:** Line-ending trouble: .gitattributes pins *.sh/*.py to LF and *.cmd to CRLF; run `git add --renormalize .` once if a script shows CRLF.

#### Python packages (root project) (`python-packages`)
- **Install:** all: `uv sync --locked`
- **Update:** One package: `uv lock --upgrade-package NAME` then `uv sync`. Everything: `uv lock --upgrade`. Run tests, commit uv.lock. Ranges live in pyproject.toml files; requirements.txt mirrors the root pyproject for CI and must be edited with it.
- **If it breaks:** `uv sync --locked` reinstalls exactly what uv.lock says. If a just-upgraded package broke something, `git checkout HEAD~1 -- uv.lock && uv sync --locked` rolls it back.

#### Python packages (OpenSwarm sub-project) (`openswarm-python`)
- **Install:** all: `uv sync --locked --directory agents/openedswarm_core`
- **Update:** uv lock --upgrade-package NAME --directory agents/openedswarm_core
- **If it breaks:** Same as the root lock: re-sync, or roll back agents/openedswarm_core/uv.lock from git.

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
- **If it breaks:** Usually an expired Google session: log in again through the MCP's auth flow.

#### @apify/actors-mcp-server (`apify-mcp`)
- **Update:** python scripts/deps.py set-pin apify-mcp NEW
- **If it breaks:** Check APIFY_API_TOKEN is set and the account has credit.

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
- **Update:** `python scripts/deps.py outdated` shows the newest engine release; `python scripts/deps.py set-pin raea NEW`, `python scripts/deps.py install raea`, then re-render skills/previz-3d/templates/greybox-shot.tsx and run `raea scene lint` on it.
- **If it breaks:** Canary software. Roll back: `python scripts/deps.py set-pin raea OLD && python scripts/deps.py install raea`. Upstream's own installer can pick a web-* release and 404; use deps.py instead.

#### browser-act CLI (`browser-act`)
- **Install:** all: `uv tool install browser-act-cli==0.1.23`
- **Update:** python scripts/deps.py set-pin browser-act NEW && python scripts/deps.py install browser-act
- **If it breaks:** uv tool install --force browser-act-cli=={version}

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
- **If it breaks:** Windows: add C:\Program Files\LibreOffice\program to PATH.

#### Cairo / Pango libraries (`cairo-pango`)
- **Install:** linux: `sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libcairo2`; windows: `manual: install the GTK3 runtime (MSYS2: pacman -S mingw-w64-x86_64-pango) and add its bin to PATH`; macos: `brew install pango cairo`
- **Update:** Package manager upgrade.
- **If it breaks:** 'cannot load library libgobject' / 'no library called cairo' = the native runtime is missing or not on PATH.

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

#### Obsidian vault (Brainiac2) (`obsidian-vault`)
- **Install:** all: `manual: set OBSIDIAN_VAULT_PATH in .env (Linux: the vault drive's fstab mount point; Windows: D:\Brainiac2)`
- **Update:** Synced between machines outside git.
- **If it breaks:** Linux I/O errors on the NTFS drive: run chkdsk on Windows. Index stale: make vault-index.

#### Third-party agent skills (`external-skills`)
- **Update:** Re-install through the `skills` CLI that wrote skills-lock.json (`npx skills --help`), review the diff, commit.
- **If it breaks:** Restore a skill folder from git; skills-lock.json holds the hash of the version that worked.

#### GitHub Actions (`github-actions`)
- **Update:** Bump the @vN tag in both workflow files together.
- **If it breaks:** Read the failing job log on GitHub; the Cross-platform job names the OS that broke.

<!-- deps:end -->
