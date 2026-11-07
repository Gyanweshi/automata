#!/usr/bin/env node
// Cross-platform MCP launcher: runs `npx <args>` with a Node.js version the pinned MCP packages accept.
//
// MCP configs call it as {"command": "node", "args": ["scripts/mcp-npx.mjs", "-y", "<pkg>@<version>", ...]}.
// `node` is a real executable on Linux, macOS and Windows, so no bash or `cmd /c` is needed. The launcher
// itself runs on any Node; it then picks the newest compatible Node it can find (the one running it, others on
// PATH, fnm, nvm, nvm-windows) and runs that Node's own npx-cli.js directly, which avoids spawning npx.cmd.
//
// Arguments starting with "~/" or "~\" are expanded to the user's home directory, so configs can name
// per-user folders (a browser profile, an output dir) without a machine-specific path.
//
// Compatible = Node ^20.19, ^22.12 or >= 23 (chrome-devtools-mcp's floor; keep in sync with dependencies.toml).
import { spawn, spawnSync } from "node:child_process";
import { existsSync, readdirSync } from "node:fs";
import { homedir, platform } from "node:os";
import { delimiter, dirname, join, resolve } from "node:path";

const isWindows = platform() === "win32";
const nodeExe = isWindows ? "node.exe" : "node";

export function compatible(version) {
  const [major, minor] = version.replace(/^v/, "").split(".").map(Number);
  return (major === 20 && minor >= 19) || (major === 22 && minor >= 12) || major >= 23;
}

export function expandHome(arg, home = homedir()) {
  if (arg === "~") return home;
  if (arg.startsWith("~/") || arg.startsWith("~\\")) return join(home, arg.slice(2));
  return arg;
}

function versionOf(bin) {
  const out = spawnSync(bin, ["--version"], { encoding: "utf8", timeout: 10000 });
  return out.status === 0 ? out.stdout.trim() : null;
}

function subdirs(dir) {
  try {
    return readdirSync(dir, { withFileTypes: true }).filter((d) => d.isDirectory()).map((d) => join(dir, d.name));
  } catch {
    return [];
  }
}

function candidateNodes() {
  const home = homedir();
  const found = [process.execPath];
  for (const dir of (process.env.PATH || "").split(delimiter)) {
    if (dir) found.push(join(dir, nodeExe));
  }
  const fnmRoots = [
    process.env.FNM_DIR,
    join(home, ".local", "share", "fnm"),
    join(home, ".fnm"),
    process.env.APPDATA && join(process.env.APPDATA, "fnm"),
  ].filter(Boolean);
  for (const root of fnmRoots) {
    for (const v of subdirs(join(root, "node-versions"))) {
      found.push(isWindows ? join(v, "installation", nodeExe) : join(v, "installation", "bin", nodeExe));
    }
  }
  for (const v of subdirs(join(process.env.NVM_DIR || join(home, ".nvm"), "versions", "node"))) {
    found.push(join(v, "bin", nodeExe));
  }
  if (process.env.NVM_HOME) {
    for (const v of subdirs(process.env.NVM_HOME)) found.push(join(v, nodeExe));
  }
  return [...new Set(found.map((p) => resolve(p)))].filter((p) => existsSync(p));
}

function npxCliFor(node) {
  const dir = dirname(node);
  const options = [
    join(dir, "node_modules", "npm", "bin", "npx-cli.js"), // Windows layout
    join(dir, "..", "lib", "node_modules", "npm", "bin", "npx-cli.js"), // Linux/macOS layout
  ];
  return options.find((p) => existsSync(p)) || null;
}

function pickRuntime() {
  const ranked = candidateNodes()
    .map((node) => ({ node, version: versionOf(node) }))
    .filter((c) => c.version && compatible(c.version))
    .sort((a, b) => b.version.localeCompare(a.version, undefined, { numeric: true }));
  for (const c of ranked) {
    const cli = npxCliFor(c.node);
    if (cli) return { ...c, cli };
  }
  return null;
}

function main() {
  const args = process.argv.slice(2).map((a) => expandHome(a));
  if (args[0] === "--which") {
    const r = pickRuntime();
    console.log(r ? `${r.version} ${r.node}` : "none");
    process.exit(r ? 0 : 1);
  }
  const runtime = pickRuntime();
  if (!runtime) {
    console.error(
      "mcp-npx: no compatible Node.js found (need ^20.19, ^22.12 or >= 23).\n" +
        "Install one (e.g. `fnm install 22`, or nodejs.org on Windows), then restart the MCP client.",
    );
    process.exit(1);
  }
  const env = { ...process.env, PATH: dirname(runtime.node) + delimiter + (process.env.PATH || "") };
  const child = spawn(runtime.node, [runtime.cli, ...args], { stdio: "inherit", env });
  for (const sig of ["SIGINT", "SIGTERM"]) process.on(sig, () => child.kill(sig));
  child.on("exit", (code, signal) => process.exit(signal ? 1 : code ?? 1));
}

if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith("mcp-npx.mjs")) main();
