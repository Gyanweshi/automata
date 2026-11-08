---
name: agency-housekeeper
description: Audit and clean the Automata repo and its Obsidian vault when the user asks to tidy files, decide what belongs in the vault, remove temporary outputs, or run a cleanup watchdog. Produces conservative keep, review, and safe-delete decisions; it does not organize unrelated repositories.
---

# Agency Housekeeper

Keep Automata lean without losing source material, durable knowledge, or brand history.

For disk pressure, unexplained growth, large-folder analysis or requests to find more
cleanup opportunities, read [storage-investigation.md](references/storage-investigation.md).
It adds measured inventory, active-use checks and recovery accounting adapted from
Charles's storage workflow. It does not expand this skill beyond Automata and its
vault or change the CLI's deletion classifications.

## Safety boundary

- Treat an audit as read-only. Do not mutate anything merely because this skill was invoked.
- Never automatically delete or move a vault file. Flag vault problems for review.
- Never remove tracked repo files, `.env`, virtual environments, dependencies, source code, or plausible user inputs.
- A workspace or loose root artifact is safe-delete only when an exact byte-for-byte copy exists in the vault.
- Disposable caches are safe-delete only after the configured age threshold.
- After explicit authorization, delete fingerprint-verified safe-delete items immediately. These are exact vault copies or expired disposable caches.
- Quarantine authorized ambiguous workspace material in `.housekeeper/quarantine/<timestamp>/` for seven days, then purge it automatically.
- Before touching outputs for a specific brand, read `Brands/<slug>.md`, especially `## Memory`.

## Decisions

| Decision | Meaning |
| --- | --- |
| `keep-repo` | Code, configuration, runtime state, dependencies, or protected local material |
| `keep-vault` | Durable human-readable knowledge or protected brand/session/memory material |
| `review` | Ambiguous ownership, missing vault metadata, unverified output, or duplicate needing a canonical choice |
| `safe-delete` | Eligible for immediate deletion because it is disposable or exactly preserved in the vault |

The CLI implements these decisions deterministically in `agency_common.housekeeping`.

## Workflow

1. Read the repo `AGENTS.md` and inspect `git status --short`. Preserve unrelated dirty worktree changes.
2. Resolve the vault with `agency_common.get_vault_path()`; the no-vault fallback is
   `workspace/vault/`, which remains protected knowledge, never disposable workspace.
3. Run an audit and save the machine plan and working Markdown report in `.housekeeper/`. Do not write the report to the vault during an active cleanup. Promote it only if the user explicitly asks to save/finalize the report.

   ```powershell
   $stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
   .\.venv\Scripts\python.exe -m agency_common.housekeeping audit `
     --repo . `
     --plan ".housekeeper\plans\$stamp.json" `
     --report ".housekeeper\reports\Automata Cleanup $stamp.md"
   ```

4. Summarize safe-delete and review findings for the user. Explain any uncertain classification.
5. Apply only within explicit authorization for the selected batch; do not ask again
   when that exact batch is already authorized. Refresh fingerprints and active-use
   checks immediately before applying. Permanently delete only unchanged, inactive
   safe-delete candidates. A CLI classification does not prove that no job is using a file:

   ```powershell
   .\.venv\Scripts\python.exe -m agency_common.housekeeping apply `
     --plan ".housekeeper\plans\<stamp>.json" `
     --confirm delete-safe
   ```

6. Re-audit after applying. Quarantine ambiguous workspace material for seven days
   only when that move is authorized; an audit never grants quarantine permission.
7. Purge only expired quarantine batches. The scheduled watchdog runs this daily:

   ```powershell
   .\.venv\Scripts\python.exe -m agency_common.housekeeping purge `
     --repo . `
     --older-than-days 7 `
     --confirm delete
   ```

8. Install or refresh the daily watchdog with the platform dispatcher. It invokes only the native adapter for the detected OS:

   ```text
   Windows: .\.venv\Scripts\python.exe scripts\install-housekeeper-watchdog.py
   Linux:   .venv/bin/python scripts/install-housekeeper-watchdog.py
   ```

   - Windows uses Task Scheduler and the PowerShell runner.
   - Linux prefers a user-level systemd timer and falls back to the user's crontab.
   - Do not install both adapters on one machine.

## Explicit workspace clearing

When the user explicitly wants `workspace/` visibly empty, do not leave every unverified
output in place as `review`. Read the relevant brand memories, identify what is already
durable in the vault, and use the recoverable workspace override:

```powershell
.\.venv\Scripts\python.exe -m agency_common.housekeeping clear-workspace `
  --repo . `
  --confirm quarantine-workspace
```

This preserves tracked workspace scaffolding such as `.gitkeep` and quarantines every
other workspace file or directory for seven days. The daily watchdog permanently
purges the batch after its `purge_after` timestamp.

Treat `clear-workspace` as a final-state operation. After it runs, verify the returned
`workspace_empty: true` and `workspace_remaining: []` fields, then inspect the actual
workspace with:

```bash
find workspace -type f ! -name .gitkeep -print
```

The command is not complete if that command prints any path. A cleanup report must
state the remaining workspace files, quarantined batch, purge date, and any skipped
paths. `apply --confirm delete-safe` is cache/duplicate cleanup only; it does not mean
the workspace is empty. When the user says “clean the workspace,” use
`clear-workspace`, not only `apply --confirm delete-safe`.

## Judgment rules

- Missing required final-note frontmatter is a repair task, not evidence that a note is disposable.
- Exact duplicates inside the vault require a canonical-note decision; do not infer that the other copy can be deleted.
- Raw browser dumps, screenshots, and extraction logs may be provenance. Flag them for review unless they meet an explicit deterministic safe-delete rule.
- If a working artifact has no exact vault copy, recommend promoting or archiving it before cleanup.
- If a candidate changes after the audit, discard that decision and re-audit it.
