---
name: image-compositing-repair
description: Deterministically composite, mask, alpha-key, color-match, crop, enhance, or repair generated image regions with local Python tooling while preserving untouched source pixels. Use for OpenCV/Pillow post-processing, face-repair composites, subject replacement from an existing generated plate, chroma-key extraction, and architectural frame construction; do not use for creative generative image editing itself.
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
- For creative generation or semantic changes that require inventing pixels, use an available image-generation/editing workflow first, then use this skill only for deterministic integration or cleanup.
- Use `render-upscale-crop` for pure resize, crop, or still-to-motion work that does not require masks or compositing.

## Invariants

- Never silently replace or modify the only source image.
- Treat every legacy coordinate, filename, download path, identity, and project name as an example that must be re-measured.
- Do not claim architecture, text, or identity is preserved unless unchanged regions were compared against the source at full resolution.
- Do not install packages outside `.venv`.
- Do not commit generated images, masks, previews, caches, or workspace outputs.
