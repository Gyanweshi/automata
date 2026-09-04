# Script catalog

The reusable portion of this skill is intentionally small. It contains one
parameterized helper and no client- or board-specific Selenium recipes.

## Profile preparation

- `scripts/prepare_lean_zen_profile.py` — create a fresh, gitignored lean
  profile under `workspace/`, copying only safe profile metadata and a filtered
  SQLite cookie backup. It refuses to overwrite an existing target and never
  prints cookie values.

## Workflow guidance

Use the current Zen/Selenium session to rediscover the live Space URL, board
nodes, selectors, model availability, resolution controls, and cost state.
Adapt any one-off diagnostic code into a task-specific copy under
`workspace/<project>/`; do not add client-specific URLs, node IDs, coordinates,
profiles, cookies, screenshots, or logs to this skill package.

Generation-capable clicks still require explicit user authorization immediately
before the run. Stop on a login wall, changed selector, missing node, unexpected
dialog, or ambiguous cost state.
