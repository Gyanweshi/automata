#!/usr/bin/env bash
# Symlink agency skills from the repo into ~/.claude/skills/
# Run from the repo root: bash scripts/install-skills.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_SRC="$REPO_DIR/skills"
SKILLS_DST="$HOME/.claude/skills"

if [[ ! -d "$SKILLS_SRC" ]]; then
    echo "Error: skills/ directory not found at $SKILLS_SRC"
    exit 1
fi

mkdir -p "$SKILLS_DST"

installed=0
for skill_dir in "$SKILLS_SRC"/agency-*/; do
    name=$(basename "$skill_dir")
    target="$SKILLS_DST/$name"
    if [[ -L "$target" ]]; then
        rm "$target"
        echo "Updated symlink: $name"
    elif [[ -d "$target" ]]; then
        echo "Warning: $target exists and is not a symlink — skipping (remove manually)"
        continue
    else
        echo "Installing: $name"
    fi
    ln -s "$skill_dir" "$target"
    installed=$((installed + 1))
done

echo ""
echo "$installed skill(s) installed to $SKILLS_DST"
echo "Available agency skills:"
for skill_dir in "$SKILLS_SRC"/agency-*/; do
    echo "  /$(basename "$skill_dir")"
done
