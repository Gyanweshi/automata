#!/bin/bash
# Sets up MCP dependencies for this project on a fresh system.
# Run once after cloning: bash setup-mcp.sh

set -e

echo "==> Installing fnm (Node version manager)..."
if ! command -v fnm &>/dev/null; then
  curl -fsSL https://fnm.vercel.app/install | bash -s -- --skip-shell
fi
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env --shell bash)"

echo "==> Installing Node 22..."
fnm install 22
fnm use 22

echo "==> Installing mcp-remote..."
mkdir -p "$HOME/.local/share/mcp-remote"
"$HOME/.local/share/fnm/node-versions/v22.22.2/installation/bin/npm" \
  install mcp-remote --prefix "$HOME/.local/share/mcp-remote"

echo "==> Creating mcp-remote-n22 wrapper..."
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/mcp-remote-n22" << 'EOF'
#!/bin/bash
exec "$HOME/.local/share/fnm/node-versions/v22.22.2/installation/bin/node" \
  "$HOME/.local/share/mcp-remote/node_modules/.bin/mcp-remote" "$@"
EOF
chmod +x "$HOME/.local/bin/mcp-remote-n22"

echo ""
echo "==> Done. Make sure ~/.local/bin is in your PATH, then set your API key:"
echo "    export FREEPIK_API_KEY=your_key_here"
echo ""
echo "    uv is required for the blender MCP:"
echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"
