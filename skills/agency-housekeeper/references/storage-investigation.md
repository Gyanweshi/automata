# Investigate storage without losing working material

Read this for large-folder diagnosis, disk pressure, recurring growth or a broader
Automata cleanup audit. A named file operation needs only the checks relevant to
that selection. The parent skill's protected paths and safe-delete rules take
precedence over these discovery leads. Do not scan unrelated projects, uninstall
software or clean system stores merely because they share the volume.

## Measure and explain

Record timestamp, repo/vault roots, their volumes, free bytes and exclusions before
making changes. Resolve the vault through `agency_common.get_vault_path()`. Use
`shutil.disk_usage(path).free` on each distinct volume; do not add the repo and vault
free space together when they live on the same volume.

Start with bounded directory summaries and large files in the requested scope.
Deepen only the branches that need explanation. Include hidden directories; do not
follow symlinks, Windows junctions/reparse points, or child mounts into other scopes.
Label timeouts and permission failures as uninspected, not empty. Any new inventory
helper must be Python with `pathlib`, OS differences handled inside it, and no
deletion functionality mixed into discovery.

Break large trees into source/configuration, environments/dependencies, Git history,
generated working output, unique source media, and preserved knowledge. Explain what
the bytes contain and why they exist. Report apparent file bytes separately from
allocated bytes when available; on platforms without an allocation probe, say that
allocation is unknown. Deduplicate hardlinks and overlapping parent/child totals.
Quarantine on the same volume does not recover space.

## Coverage within the authorized roots

| Family | Inspect | Preserve / establish before any removal |
| --- | --- | --- |
| Research and browser output | Dumps, screenshots, downloads, extracted assets | Unique evidence, provenance, active browser profiles and credentials |
| Visual production | Frames, previews, proxies, transcodes, render variants | Raw footage, selected masters, source projects, asset manifests, current render inputs |
| Builds and dependencies | Generated output versus installed environments | Source, lockfiles, local patches and installed tools; dependency removal is outside the parent skill |
| Repo caches | Only cache types recognized by the housekeeping CLI | Age eligibility plus no active reader/writer; a cache-like name is insufficient |
| Git/worktrees | Read-only size and status inspection | All history, dirty files and active writers; never manually remove packs or run blanket cleaning |
| Vault and local fallback | Exact preserved copies and note metadata | Every vault file stays protected; missing metadata is a repair, not disposal evidence |
| Quarantine | Batch receipts, expiry and modifications | Honor retention; a modified batch needs renewed review before purge |

For each family record measured, absent, excluded or incomplete. A protected large
dependency tree can explain disk use without becoming a cleanup opportunity. Do not
inflate a list to reach an arbitrary number of suggested removals.

## Establish eligibility and inactivity separately

Use the existing CLI audit/triage for classifications and fingerprints. For every
proposed removable subset record exact path, size, contents, preservation or cache
evidence, applicable age threshold, current-use evidence and method. Re-downloadable
does not override the parent skill's protections.

Check relevant processes, job inputs, working directories and open files where the
OS exposes them. Do not stop a running task to make its inputs disposable. If a
probe fails, activity is unknown. Old mtime, ignored Git status and no observed open
handle alone are insufficient. Skip uncertain entries and continue other authorized
work. If the CLI cannot exclude a live entry from a batch, do not apply that batch;
prepare a fresh eligible selection using supported tooling.

## Verify recovery and recurrence

After an authorized batch, re-audit and measure free bytes on the same volumes.
Report removed paths, retained resources, logical bytes removed, net free-space
change, quarantine bytes, and gaps. Concurrent writes, hardlinks and snapshots can
make those figures differ; never label a sum of folder sizes as physical recovery.

Keep JSON inventories and receipts under `.housekeeper/` with the existing reports.
Compare against earlier receipts before suggesting the same paths again. If growth
returns, trace the writer or repeated render/download rather than repeatedly deleting
the output. Preserve user keep decisions across runs. Final reports follow the
parent skill's vault-finalization rules.

## Source

Adapted from Charles Liu's [charles-storage-cleanup](https://github.com/LemonFace0309/charles-skills/tree/main/skills/charles-storage-cleanup)
and its discovery checklist. This version limits discovery to authorized repo/vault
roots, retains Automata's stricter deletion policy, and replaces macOS-specific
paths and commands with OS-aware measurement requirements.
