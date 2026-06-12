#!/usr/bin/env bash
# Symlink all skills from the repo into ~/.claude/skills/
# Run from the repo root: bash scripts/install-skills.sh
#
# Handles any subdirectory under skills/ that contains a SKILL.md file.
# Safe to re-run — existing symlinks are updated, non-symlink directories are skipped.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_SRC="$REPO_DIR/skills"
SKILLS_DST="$HOME/.claude/skills"

if [[ ! -d "$SKILLS_SRC" ]]; then
    echo "Error: skills/ directory not found at $SKILLS_SRC"
    exit 1
fi

mkdir -p "$SKILLS_DST"

installed=0
skipped=0

for skill_dir in "$SKILLS_SRC"/*/; do
    [[ -d "$skill_dir" ]] || continue
    [[ -f "$skill_dir/SKILL.md" ]] || continue   # only directories with a SKILL.md

    name=$(basename "$skill_dir")
    target="$SKILLS_DST/$name"

    if [[ -L "$target" ]]; then
        rm "$target"
        echo "  updated: $name"
    elif [[ -e "$target" ]]; then
        echo "  SKIP: $target exists and is not a symlink (remove manually to reinstall)"
        skipped=$((skipped + 1))
        continue
    else
        echo "  installed: $name"
    fi

    ln -s "$skill_dir" "$target"
    installed=$((installed + 1))
done

echo ""
echo "$installed skill(s) installed to $SKILLS_DST"
if [[ $skipped -gt 0 ]]; then
    echo "$skipped skill(s) skipped (non-symlink directories — remove manually to reinstall)"
fi
echo ""
echo "Active skills:"
for skill_dir in "$SKILLS_SRC"/*/; do
    [[ -f "$skill_dir/SKILL.md" ]] && echo "  /$(basename "$skill_dir")"
done
