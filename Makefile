.PHONY: install install-skills uninstall test pipeline clean help

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
PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
AGENCY_RESEARCH ?= .venv/bin/agency-research
AGENCY_STORYBOARD ?= .venv/bin/agency-storyboard
AGENCY_CONTENT ?= .venv/bin/agency-content

ifeq ($(PARALLEL),1)
RESEARCH_PARALLEL_FLAGS := --parallel --max-workers $(MAX_WORKERS)
endif
ifneq ($(strip $(PLATFORMS)),)
RESEARCH_PLATFORM_FLAGS := --platforms $(PLATFORMS)
endif

help:
	@echo "Agency Multi-Agent System"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install all packages in editable mode"
	@echo "  make install-skills Symlink skills to ~/.claude/skills/"
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
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -e ./packages/agency-common[test]
	$(PIP) install -e ./packages/agency-research[test]
	$(PIP) install -e ./packages/agency-storyboard
	$(PIP) install -e ./packages/agency-content
	@echo ""
	@echo "All packages installed. Run 'make install-skills' to set up repo skills for Claude Code."

install-skills:
	bash scripts/install-skills.sh

uninstall:
	$(PIP) uninstall -y agency-common agency-research agency-storyboard agency-content

research:
	$(AGENCY_RESEARCH) --brand $(BRAND) --workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) --scraper $(SCRAPER) --instagram-login-mode $(INSTAGRAM_LOGIN_MODE) --browser-act-mode $(BROWSER_ACT_MODE) --browser-act-session-name $(BROWSER_ACT_SESSION_NAME) $(RESEARCH_PLATFORM_FLAGS) $(RESEARCH_PARALLEL_FLAGS)

storyboard:
	$(AGENCY_STORYBOARD) --brand $(BRAND) --type $(TYPE) --topic $(TOPIC) \
		--workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR)

content:
	$(AGENCY_CONTENT) --brand $(BRAND) --platform instagram --type $(TYPE) --topic $(TOPIC) \
		--workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR)

pipeline:
	@echo "==> Research"
	$(AGENCY_RESEARCH) --brand $(BRAND) --workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) --scraper $(SCRAPER) --instagram-login-mode $(INSTAGRAM_LOGIN_MODE) --browser-act-mode $(BROWSER_ACT_MODE) --browser-act-session-name $(BROWSER_ACT_SESSION_NAME) $(RESEARCH_PLATFORM_FLAGS) $(RESEARCH_PARALLEL_FLAGS)
	@echo ""
	@echo "==> Storyboard"
	$(AGENCY_STORYBOARD) --brand $(BRAND) --type $(TYPE) --topic $(TOPIC) \
		--workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR)
	@echo ""
	@echo "==> Content"
	$(AGENCY_CONTENT) --brand $(BRAND) --platform instagram --type $(TYPE) --topic $(TOPIC) \
		--workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR)

week:
	$(AGENCY_CONTENT) --brand $(BRAND) --week --workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) --format markdown

dry-run:
	$(AGENCY_RESEARCH) --brand $(BRAND) --workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) --dry-run
	$(AGENCY_CONTENT) --brand $(BRAND) --platform instagram --type caption --topic "test" \
		--workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) --format summary

status:
	$(PIP) show agency-common agency-research agency-storyboard agency-content 2>/dev/null | grep -E "^(Name|Version|Location)"

test:
	$(PYTHON) -m pytest packages/*/tests -v

clean:
	rm -rf $(WORKSPACE)/research/ $(WORKSPACE)/storyboards/ $(WORKSPACE)/content/
	mkdir -p $(WORKSPACE)/research $(WORKSPACE)/storyboards $(WORKSPACE)/content
	touch $(WORKSPACE)/research/.gitkeep $(WORKSPACE)/storyboards/.gitkeep $(WORKSPACE)/content/.gitkeep
	@echo "Workspace cleaned."
