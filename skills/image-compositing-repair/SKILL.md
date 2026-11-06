---
name: image-compositing-repair
description: Edit, retouch, composite, mask, alpha-key, color-match, crop, enhance, or repair images locally (GIMP MCP for interactive edits, Python/OpenCV/Pillow for scripted ones) while preserving untouched source pixels. Use for any image editing task, GIMP work, layered XCF handoff, OpenCV/Pillow post-processing, face-repair composites, subject replacement from an existing generated plate, chroma-key extraction, and architectural frame construction; do not use for creative generative image editing itself.
---

# Image Compositing Repair

Use deterministic local pixel operations to integrate an existing edit or repair into a source image without regenerating the rest of the frame.

## Workflow

1. Read the repo `AGENTS.md`. For brand work, read the brand note and `## Memory` before touching its outputs.
2. Inspect the source, repair/generated plate, dimensions, color space, and intended unchanged regions. Keep the source immutable.
3. Read [references/script-catalog.md](references/script-catalog.md) and choose the closest recipe. Load only the selected legacy script and its direct imports.
4. Copy the recipe into a task-specific `workspace/<project>/` directory. Never run a legacy recipe from the skill directory: many contain obsolete absolute paths, measured coordinates, and output names.
5. Parameterize inputs, outputs, coordinates, masks, and preview paths for the current files. Use the repo `.venv`; verify required packages before changing the environment.
6. Write new outputs rather than overwriting the source. Save a mask or compositing preview when edge quality or protected regions need review.
7. Verify at full resolution: dimensions, subject alignment, mask seams, halos, color continuity, geometry, text, identity, and unchanged-region fidelity.
8. Keep source images, masks, previews, repair plates, and visual variants in `workspace/`. A human-readable work note may live in the vault with `status: draft`; promote only the approved asset and provenance after the user approves or asks to finalize.

## Routing

- Use this skill when the edit can be expressed as deterministic pixel operations over supplied images.
- **GIMP MCP is the default editor for local, non-generative edits** (`gimp` server in `.mcp.json`): retouch/clone/heal, selections and masks, layer compositing, color/tone/curves, transforms and perspective, text and logo placement, filters, and layered XCF handoff. See [GIMP MCP](#gimp-mcp) below. Use the Python recipes instead for batch runs, measured-coordinate scripts, or pixel-exact compositing that must be reproducible from a script.
- For creative generation or semantic changes that require inventing pixels, use an available image-generation/editing workflow first, then use this skill only for deterministic integration or cleanup.
- Use `render-upscale-crop` for pure resize, crop, or still-to-motion work that does not require masks or compositing.

## GIMP MCP

1. Preflight: call a cheap GIMP tool (e.g. list images). If it can't connect, ask the user to open GIMP and run **Tools > MCP > Start MCP Server**. Don't silently fall back to Python for an edit that was meant for GIMP. If the plugin is missing, run `scripts/install-gimp-mcp.ps1`.
2. Copy the source into `workspace/<project>/` and open the copy, never the original.
3. Do non-destructive work: a new layer per edit, masks rather than erasing, adjustments on duplicates.
4. Call `get_state_snapshot` after every edit step. Use `region` to zoom in on faces, text, edges and seams before moving on.
5. Save a layered `.xcf` next to the flattened export whenever the asset may be edited again. Export finals to `workspace/` and promote approved assets per the vault policy.
6. Brand rules still apply. GIMP is local pixel editing, not generation. Anything that invents pixels goes to the brand's generator (Purva: Magnific only), and the result comes back to GIMP for finishing.
7. The plugin runs Python that the server sends inside GIMP, and it listens on localhost only. Stop the MCP server in GIMP when you're done.

## Invariants

- Never silently replace or modify the only source image.
- Treat every legacy coordinate, filename, download path, identity, and project name as an example that must be re-measured.
- Do not claim architecture, text, or identity is preserved unless unchanged regions were compared against the source at full resolution.
- Do not install packages outside `.venv`.
- Do not commit generated images, masks, previews, caches, or workspace outputs.
