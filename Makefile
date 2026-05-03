.PHONY: install install-skills uninstall test pipeline clean help

BRAND ?= example-brand
TOPIC ?= "5 tips for entrepreneurs"
TYPE  ?= carousel
WORKSPACE ?= ./workspace
BRANDS_DIR ?= ./brands

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
	@echo "  make storyboard     Run storyboard agent"
	@echo "  make content        Run content agent"
	@echo "  make pipeline       Run all three agents in sequence"
	@echo "  make week           Generate a weekly content calendar"
	@echo ""
	@echo "Other:"
	@echo "  make dry-run        Validate all agent configs without API calls"
	@echo "  make clean          Remove workspace outputs"
	@echo "  make status         Show installed packages"

install:
	pip3 install --break-system-packages -e ./packages/agency-common
	pip3 install --break-system-packages -e ./packages/agency-research
	pip3 install --break-system-packages -e ./packages/agency-storyboard
	pip3 install --break-system-packages -e ./packages/agency-content
	@echo ""
	@echo "All packages installed. Run 'make install-skills' to set up Claude Code skills."

install-skills:
	bash scripts/install-skills.sh

uninstall:
	pip3 uninstall --break-system-packages -y agency-common agency-research agency-storyboard agency-content

research:
	agency-research --brand $(BRAND) --workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR)

storyboard:
	agency-storyboard --brand $(BRAND) --type $(TYPE) --topic $(TOPIC) \
		--workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR)

content:
	agency-content --brand $(BRAND) --platform instagram --type $(TYPE) --topic $(TOPIC) \
		--workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR)

pipeline:
	@echo "==> Research"
	agency-research --brand $(BRAND) --workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR)
	@echo ""
	@echo "==> Storyboard"
	agency-storyboard --brand $(BRAND) --type $(TYPE) --topic $(TOPIC) \
		--workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR)
	@echo ""
	@echo "==> Content"
	agency-content --brand $(BRAND) --platform instagram --type $(TYPE) --topic $(TOPIC) \
		--workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR)

week:
	agency-content --brand $(BRAND) --week --workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) --format markdown

dry-run:
	agency-research --brand $(BRAND) --workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) --dry-run
	agency-content --brand $(BRAND) --platform instagram --type caption --topic "test" \
		--workspace $(WORKSPACE) --brands-dir $(BRANDS_DIR) --format summary

status:
	pip3 show agency-common agency-research agency-storyboard agency-content 2>/dev/null | grep -E "^(Name|Version|Location)"

clean:
	rm -rf $(WORKSPACE)/research/ $(WORKSPACE)/storyboards/ $(WORKSPACE)/content/
	mkdir -p $(WORKSPACE)/research $(WORKSPACE)/storyboards $(WORKSPACE)/content
	touch $(WORKSPACE)/research/.gitkeep $(WORKSPACE)/storyboards/.gitkeep $(WORKSPACE)/content/.gitkeep
	@echo "Workspace cleaned."
