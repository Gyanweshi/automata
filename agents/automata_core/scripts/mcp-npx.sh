#!/usr/bin/env bash
# Runs npx with a Node.js version compatible with the pinned MCP packages.

set -euo pipefail

version_ok() {
  local node_bin="$1"
  "$node_bin" -e '
const [major, minor] = process.versions.node.split(".").map(Number);
const ok = (major === 20 && minor >= 19) || (major === 22 && minor >= 12) || major >= 23;
process.exit(ok ? 0 : 1);
' >/dev/null 2>&1
}

try_npx() {
  local npx_bin="$1"
  local bin_dir
  local node_bin
  shift

  [[ -x "$npx_bin" ]] || return 1
  bin_dir="$(cd "$(dirname "$npx_bin")" && pwd)"
  node_bin="$bin_dir/node"
  [[ -x "$node_bin" ]] || node_bin="$(command -v node 2>/dev/null || true)"
  [[ -n "$node_bin" ]] || return 1

  if version_ok "$node_bin"; then
    PATH="$bin_dir:$PATH" exec "$npx_bin" "$@"
  fi

  return 1
}

declare -a candidates=()

if command -v npx >/dev/null 2>&1; then
  candidates+=("$(command -v npx)")
fi

for root in "${FNM_DIR:-$HOME/.local/share/fnm}/node-versions" "${NVM_DIR:-$HOME/.nvm}/versions/node"; do
  if [[ -d "$root" ]]; then
    while IFS= read -r candidate; do
      candidates+=("$candidate")
    done < <(find "$root" -path "*/bin/npx" 2>/dev/null | sort -Vr)
  fi
done

for candidate in "${candidates[@]}"; do
  try_npx "$candidate" "$@" || true
done

cat >&2 <<'EOF'
No compatible Node.js runtime was found for the pinned MCP packages.

chrome-devtools-mcp@0.23.0 requires Node.js ^20.19.0, ^22.12.0, or >=23.
Install or activate a compatible Node.js version, then rerun the MCP client.
EOF
exit 1
