---
name: zen-magnific-automation
description: Restore, inspect, debug, or automate Magnific Space workflows through Zen Browser and Selenium using a reusable authenticated Firefox-style profile. Use when the user explicitly mentions Zen, the archived Magnific headless workflow, Magnific canvas/node automation, Unlimited coverage probes, or resuming this browser profile; do not use for unrelated browser automation.
---

# Zen–Magnific Automation

Reuse the repo's Zen/Selenium workflow for Magnific Spaces while protecting login state and preventing accidental credit spend.

## Workflow

1. Read the repo `AGENTS.md`. For brand work, read the brand note and `## Memory` before touching its outputs.
2. Determine whether the request is profile recovery, read-only diagnosis, board configuration, cost/coverage probing, a single smoke run, or a batch generation.
3. Read [references/profile-and-preflight.md](references/profile-and-preflight.md). For a script choice, read [references/script-catalog.md](references/script-catalog.md).
4. Work from a task-specific copy under `workspace/<project>/`. Do not run a legacy script unchanged: its profile path, Space URL, node IDs, coordinates, output paths, model, and resolution may be obsolete.
5. Use the repo `.venv`. Verify Zen, geckodriver, Selenium, profile availability, and current authentication without printing cookie values.
6. Start with the least-mutating probe that answers the question. Save screenshots, DOM dumps, progress files, and logs only under `workspace/`.
7. Re-read the current UI state before relying on Unlimited badges, model availability, resolution behavior, or credit amounts.
8. Stop on a login wall, missing node, changed selector, unexpected dialog, or ambiguous cost state. Report the evidence instead of guessing.

## Authorization boundary

- Read-only DOM, layout, selection, and coverage inspection may proceed when requested.
- Configuration changes are allowed only when they are part of the requested workflow and their target is verified.
- Any click that can submit a generation—free, Unlimited, or paid—requires explicit user authorization for that run immediately beforehand.
- If a credit dialog appears, cancel it and stop unless the user has explicitly approved that exact spend.
- Never expose, commit, upload, or copy browser cookies/profile data outside the requested local recovery path.

## Routing

- Use this skill only for Zen/Magnific-specific browser work. Use the configured general browser-automation workflow for other sites.
- Use `scripts/prepare_lean_zen_profile.py` for a fresh parameterized lean-profile copy. Keep any board-specific diagnostics as task-local code under `workspace/<project>/`.
- Do not assume board-specific node IDs, coordinates, models, or selectors. Rediscover the current board state before any automation.
