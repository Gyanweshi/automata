.PHONY: install install-skills bootstrap doctor deps deps-install deps-outdated deps-update check-skills check-cross-platform list-workflows install-housekeeper-watchdog uninstall test vault-index install-vault-index vault-search rag-eval research storyboard content pipeline week dry-run clean help

BRAND ?= example-brand
TOPIC ?= "5 tips for entrepreneurs"
TYPE  ?= carousel
WORKSPACE ?= ./workspace
BRANDS_DIR ?= ./brands
PARALLEL ?= 0
MAX_WORKERS ?= 4
SCRAPER ?= cdp
INSTAGRAM_LOGIN_MODE ?= auto
BROWSER_ACT_MODE ?= stealth
BROWSER_ACT_SESSION_NAME ?=
BROWSER_ACT_BROWSER ?=
PLATFORMS ?=
VENV ?= .venv
RETENTION_DAYS ?= 7
DAILY_AT ?= 03:00
VAULT_INDEX_AT ?= 02:30
COMMIT_VAULT ?= 0
COMMIT_REASON ?=

ifeq ($(OS),Windows_NT)
PYTHON ?= $(VENV)/Scripts/python.exe
PIP ?= $(VENV)/Scripts/pip.exe
PYTHON_CMD ?= python
else
PYTHON ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip
PYTHON_CMD ?= python3
endif

ifeq ($(PARALLEL),1)
RUN_AGENT_PARALLEL := --parallel --max-workers $(MAX_WORKERS)
endif
ifeq ($(COMMIT_VAULT),1)
ifeq ($(strip $(COMMIT_REASON)),)
$(error COMMIT_REASON is required when COMMIT_VAULT=1)
endif
VAULT_FLAGS := --commit-vault --commit-reason "$(COMMIT_REASON)"
endif

help:
	@echo "Agency Multi-Agent System"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install all packages in editable mode"
	@echo "  make install-skills Register repo skills for Codex and Claude"
	@echo "  make check-skills   Check skill discovery coverage"
	@echo "  make bootstrap      Set up this machine (Linux or Windows): venv, packages, browsers, checks"
	@echo "  make doctor         Check that everything on this machine works, step by step"
	@echo "  make deps           Check every external dependency (dependencies.toml)"
	@echo "  make deps-install ID=raea  Install one dependency the right way for this OS"
	@echo "  make deps-outdated  Show newer upstream versions of pinned dependencies"
	@echo "  make deps-update    Run the dependency update routine (cool-down, no majors, MCP smoke tests)"
	@echo "  make check-cross-platform  Flag code that would only work on Linux or only on Windows"
	@echo "  make list-workflows List local skills and the routing policy"
	@echo "  make install-housekeeper-watchdog  Install the native cleanup scheduler"
	@echo "  make uninstall      Uninstall all packages"
	@echo ""
	@echo "Run agents (set BRAND=my-client TOPIC='...' TYPE=carousel):"
	@echo "  make research       Run research agent"
	@echo "  make research PARALLEL=1 MAX_WORKERS=4  Run research with bounded concurrency"
	@echo "  make research SCRAPER=browser-act PARALLEL=1  Run research with browser-act stealth extraction"
	@echo "  make research SCRAPER=cdp PLATFORMS=ig  Run research against an open Chrome CDP Instagram session"
	@echo "  make research SCRAPER=playwright INSTAGRAM_LOGIN_MODE=manual  Run research with a manual Instagram login session"
	@echo "  make storyboard     Run storyboard agent"
	@echo "  make content        Run content agent"
	@echo "  make pipeline       Run all three agents in sequence"
	@echo "  make week           Generate a weekly content calendar"
	@echo ""
	@echo "Other:"
	@echo "  make dry-run        Validate all agent configs without API calls"
	@echo "  make test           Run the automated test suite"
	@echo "  make vault-index    Rebuild the chunked vault search index now"
	@echo "  make install-vault-index  Schedule the nightly index rebuild"
	@echo "  make vault-search Q=\"...\"  Search the vault index"
	@echo "  make rag-eval       Score vault retrieval: legacy index vs v2"
	@echo "  make clean         Remove workspace outputs"
	@echo "  make status         Show installed packages"

install:
	$(PYTHON_CMD) -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade "pip>=26.2" "setuptools>=83.0.0"
	$(PIP) install -e ./packages/agency-common[test,vector]
	$(PIP) install -e ./packages/agency-research[test]
	$(PIP) install -e ./packages/agency-storyboard
	$(PIP) install -e ./packages/agency-content
	@echo ""
	@echo "All packages installed. Run 'make install-skills' to register repo skills."

install-skills:
	$(PYTHON) scripts/sync-skills.py --sync

deps:
	$(PYTHON_CMD) scripts/deps.py check

deps-install:
	$(PYTHON_CMD) scripts/deps.py install $(ID)

deps-outdated:
	$(PYTHON_CMD) scripts/deps.py outdated

deps-update:
	$(PYTHON_CMD) scripts/deps.py update --report workspace/dependency-update.md

bootstrap:
	uv run --no-project --python 3.12 scripts/bootstrap.py

doctor:
	$(PYTHON_CMD) scripts/doctor.py

check-cross-platform:
	$(PYTHON_CMD) scripts/check-cross-platform.py

check-skills:
	$(PYTHON) scripts/sync-skills.py --check

list-workflows:
	$(PYTHON) -c "from agency_common.workflow_discovery import discover_workflows; print(discover_workflows())"

install-housekeeper-watchdog:
	$(PYTHON) scripts/install-housekeeper-watchdog.py --daily-at $(DAILY_AT) --retention-days $(RETENTION_DAYS)

uninstall:
	$(PIP) uninstall -y agency-common agency-research agency-storyboard agency-content

RUN_AGENT = $(PYTHON) scripts/run-agent.py
AGENT_FLAGS = --brand $(BRAND) --type $(TYPE) --topic $(TOPIC) --workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) \
	--scraper $(SCRAPER) --instagram-login-mode $(INSTAGRAM_LOGIN_MODE) --browser-act-mode $(BROWSER_ACT_MODE) \
	--browser-act-session-name "$(BROWSER_ACT_SESSION_NAME)" --browser-act-browser "$(BROWSER_ACT_BROWSER)" --platforms "$(PLATFORMS)" $(RUN_AGENT_PARALLEL) $(VAULT_FLAGS)

research storyboard content pipeline week dry-run:
	$(RUN_AGENT) $@ $(AGENT_FLAGS)

status:
	$(PIP) show agency-common agency-research agency-storyboard agency-content 2>/dev/null | grep -E "^(Name|Version|Location)"

test:
	$(PYTHON) -m pytest packages/*/tests -v

vault-index:
	$(PYTHON) scripts/schedule.py run vault-index

install-vault-index:
	$(PYTHON) scripts/schedule.py install vault-index --daily-at $(VAULT_INDEX_AT)

vault-search:
	$(PYTHON) -m agency_common.vault_search $(Q)

rag-eval:
	$(PYTHON) -m agency_common.rag_eval --collection second_brain --collection second_brain_v2 --verbose

clean:
	$(PYTHON) -m agency_common.housekeeping clear-workspace --repo . --confirm quarantine-workspace --retention-days $(RETENTION_DAYS)
