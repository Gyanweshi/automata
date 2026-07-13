const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const IMAGE_EXT_RE = /\.(png|jpe?g|webp|gif)$/i;

function isDirectlyInRepoRoot(candidatePath) {
  if (!candidatePath) return false;
  const resolved = path.resolve(REPO_ROOT, candidatePath);
  return path.dirname(resolved) === REPO_ROOT && IMAGE_EXT_RE.test(resolved);
}

function extractShellTargets(command) {
  const targets = [];
  const patterns = [
    /--screenshot=["']?([^"'\s]+)["']?/gi,
    />>?\s*["']?([^"'\s>]+)["']?/g,
    /\b(?:cp|copy|mv|move)\s+\S+\s+["']?([^"'\s]+)["']?\s*(?:;|&&|$)/gim,
  ];
  for (const re of patterns) {
    let m;
    while ((m = re.exec(command)) !== null) {
      targets.push(m[1]);
    }
  }
  return targets.filter((t) => IMAGE_EXT_RE.test(t));
}

let raw = '';
process.stdin.on('data', (d) => {
  raw += d;
});
process.stdin.on('end', () => {
  let input;
  try {
    input = JSON.parse(raw);
  } catch {
    process.exit(0);
  }

  const toolName = input.tool_name;
  const toolInput = input.tool_input || {};
  let offender = null;

  if (toolName === 'Write') {
    if (isDirectlyInRepoRoot(toolInput.file_path)) offender = toolInput.file_path;
  } else if (toolName === 'Bash' || toolName === 'PowerShell') {
    const cmd = toolInput.command || '';
    for (const t of extractShellTargets(cmd)) {
      if (isDirectlyInRepoRoot(t)) {
        offender = t;
        break;
      }
    }
  } else if (toolName === 'mcp__playwright__browser_take_screenshot') {
    const fn = toolInput.filename;
    if (fn && path.isAbsolute(fn) && isDirectlyInRepoRoot(fn)) offender = fn;
  }

  if (offender) {
    const out = {
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason:
          `Blocked: "${offender}" would write an image directly into the automata repo root (${REPO_ROOT}). ` +
          'Per CLAUDE.md, screenshots/images never go there. Save to the session scratchpad directory instead, ' +
          'or D:\\Brainiac2\\Research\\<topic>\\ (or Brands\\<slug>\\) if it is a keeper deliverable.',
      },
    };
    console.log(JSON.stringify(out));
  }
  process.exit(0);
});
