.PHONY: install install-skills check-skills list-workflows install-housekeeper-watchdog uninstall test pipeline clean help

BRAND ?= example-brand
TOPIC ?= "5 tips for entrepreneurs"
TYPE  ?= carousel
WORKSPACE ?= ./workspace
BRANDS_DIR ?= ./brands
PARALLEL ?= 0
MAX_WORKERS ?= 4
SCRAPER ?= apify
INSTAGRAM_LOGIN_MODE ?= auto
BROWSER_ACT_MODE ?= stealth
BROWSER_ACT_SESSION_NAME ?=
PLATFORMS ?=
VENV ?= .venv
RETENTION_DAYS ?= 7
DAILY_AT ?= 03:00
COMMIT_VAULT ?= 0
COMMIT_REASON ?=

ifeq ($(OS),Windows_NT)
PYTHON ?= $(VENV)/Scripts/python.exe
PIP ?= $(VENV)/Scripts/pip.exe
AGENCY_RESEARCH ?= $(VENV)/Scripts/agency-research.exe
AGENCY_STORYBOARD ?= $(VENV)/Scripts/agency-storyboard.exe
AGENCY_CONTENT ?= $(VENV)/Scripts/agency-content.exe
PYTHON_CMD ?= python
else
PYTHON ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip
AGENCY_RESEARCH ?= $(VENV)/bin/agency-research
AGENCY_STORYBOARD ?= $(VENV)/bin/agency-storyboard
AGENCY_CONTENT ?= $(VENV)/bin/agency-content
PYTHON_CMD ?= python3
endif

ifeq ($(PARALLEL),1)
RESEARCH_PARALLEL_FLAGS := --parallel --max-workers $(MAX_WORKERS)
endif
ifneq ($(strip $(PLATFORMS)),)
RESEARCH_PLATFORM_FLAGS := --platforms $(PLATFORMS)
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
	@echo "  make list-workflows List local skills and specialist instructions"
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
	@echo "  make clean          Remove workspace outputs"
	@echo "  make status         Show installed packages"

install:
	$(PYTHON_CMD) -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade "pip>=26.2" "setuptools>=83.0.0"
	$(PIP) install -e ./packages/agency-common[test]
	$(PIP) install -e ./packages/agency-research[test]
	$(PIP) install -e ./packages/agency-storyboard
	$(PIP) install -e ./packages/agency-content
	@echo ""
	@echo "All packages installed. Run 'make install-skills' to register repo skills."

install-skills:
	$(PYTHON) scripts/sync-skills.py --sync

check-skills:
	$(PYTHON) scripts/sync-skills.py --check

list-workflows:
	$(PYTHON) -c "from agency_common.workflow_discovery import discover_workflows; print(discover_workflows())"

install-housekeeper-watchdog:
	$(PYTHON) scripts/install-housekeeper-watchdog.py --daily-at $(DAILY_AT) --retention-days $(RETENTION_DAYS)

uninstall:
	$(PIP) uninstall -y agency-common agency-research agency-storyboard agency-content

research:
	$(AGENCY_RESEARCH) --brand $(BRAND) --workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) --scraper $(SCRAPER) --instagram-login-mode $(INSTAGRAM_LOGIN_MODE) --browser-act-mode $(BROWSER_ACT_MODE) --browser-act-session-name $(BROWSER_ACT_SESSION_NAME) $(RESEARCH_PLATFORM_FLAGS) $(RESEARCH_PARALLEL_FLAGS) $(VAULT_FLAGS)

storyboard:
	$(AGENCY_STORYBOARD) --brand $(BRAND) --type $(TYPE) --topic $(TOPIC) \
		--workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) $(VAULT_FLAGS)

content:
	$(AGENCY_CONTENT) --brand $(BRAND) --platform instagram --type $(TYPE) --topic $(TOPIC) \
		--workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) $(VAULT_FLAGS)

pipeline:
	@echo "==> Research"
	$(AGENCY_RESEARCH) --brand $(BRAND) --workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) --scraper $(SCRAPER) --instagram-login-mode $(INSTAGRAM_LOGIN_MODE) --browser-act-mode $(BROWSER_ACT_MODE) --browser-act-session-name $(BROWSER_ACT_SESSION_NAME) $(RESEARCH_PLATFORM_FLAGS) $(RESEARCH_PARALLEL_FLAGS) $(VAULT_FLAGS)
	@echo ""
	@echo "==> Storyboard"
	$(AGENCY_STORYBOARD) --brand $(BRAND) --type $(TYPE) --topic $(TOPIC) \
		--workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) $(VAULT_FLAGS)
	@echo ""
	@echo "==> Content"
	$(AGENCY_CONTENT) --brand $(BRAND) --platform instagram --type $(TYPE) --topic $(TOPIC) \
		--workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) $(VAULT_FLAGS)

week:
	$(AGENCY_CONTENT) --brand $(BRAND) --week --workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) --format markdown $(VAULT_FLAGS)

dry-run:
	$(AGENCY_RESEARCH) --brand $(BRAND) --workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) --dry-run
	$(AGENCY_CONTENT) --brand $(BRAND) --platform instagram --type caption --topic "test" \
		--workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) --format summary --dry-run

status:
	$(PIP) show agency-common agency-research agency-storyboard agency-content 2>/dev/null | grep -E "^(Name|Version|Location)"

test:
	$(PYTHON) -m pytest packages/*/tests -v

clean:
	$(PYTHON) -m agency_common.housekeeping clear-workspace --repo . --confirm quarantine-workspace --retention-days $(RETENTION_DAYS)
