---
name: image-gen
description: Generate and edit raster images with OpenAI GPT Image and assemble animated GIFs from ordered frames using portable Python CLIs. Use for image generation, reference-based variations, image edits, batch assets, and looping GIFs in Claude Code or other agents with shell access. Not for deterministic SVG or native vector edits.
---

# Portable Image Generation

This folder is self-contained. Resolve all scripts and references relative to this
SKILL.md, never relative to a Codex installation. Read [setup and CLI usage](references/cli.md)
before executing. No Automata, MCP server, or second skill is required.

For animated GIF requests, follow [the GIF workflow](references/gif.md). Generate
or reuse ordered still frames, then assemble them locally with `scripts/make_gif.py`.
GIF assembly requires Pillow but no API key; image generation still uses the route below.

## Execution route

- If the host exposes a native image-generation tool and the user has not selected
  the API, use that tool according to its actual schema. Inspect local edit targets
  with the host's image viewer first. This package does not install or export that tool.
- In Claude Code or another shell-enabled host without that tool, use the bundled
  `scripts/image_gen.py`. Explain that it calls the OpenAI API using
  `IMAGE_GEN_API_KEY` (or legacy `OPENAI_API_KEY`) and API billing. If the user has already chosen this API workflow,
  proceed; otherwise confirm that route before making a paid call. Dry runs need no key.
- Never claim a Claude or ChatGPT subscription supplies API credentials. Never ask
  for a key in chat, print it, or store it in the skill. Respect host network permissions.
- Live API generation needs Python, network access, and secure API credentials.
  Local GIF assembly only needs Python and Pillow. State any missing capability.

## Workflow

1. Read existing project/brand requirements and inspect supplied images. Preserve
   approved copy, identity, palette, composition, and selected assets.
2. Decide whether the request creates a new image or changes an existing image.
   Label every input by index and role: edit target, style reference, or inserted subject.
3. Prepare a concise prompt in scene, subject, details, constraints order. Include
   intended use, framing, medium and lighting when useful. Quote required text
   verbatim. For edits, explicitly state what changes and what stays unchanged.
   Normalize detailed prompts without inventing props, slogans, or creative direction.
4. For API execution, run the bundled CLI with an explicit output path and inspect
   its dry-run payload before the first live call. Use a prompt file for long copy.
   Reference-image requests use the CLI's `edit` command even when the desired
   result is a new composition; `generate` does not accept image inputs.
5. Keep generation within the requested number of images and any stated budget.
   Use one job per distinct asset; `--n` means variants of the same prompt.
   Do not silently switch models or start additional paid correction rounds.
6. Inspect each output for subject, composition, text accuracy, identity, artifacts,
   and requested transparency. If inspection is unavailable, report that limitation.
   A successful API response alone is not visual validation.
7. Save deliverables inside the user's project or specified destination. Use new
   versioned filenames; do not use `--force` without replacement authorization.
   Report saved paths, execution route/model, prompt or prompt-file path, and any
   remaining defects. Never claim a dry run generated an image.

## Prompt examples

Generation: "Product photograph of a matte ceramic mug on a pale stone surface.
Soft window light, natural material texture, wide framing for a website hero.
No added text or logos."

Edit: "Image 1 is the edit target. Replace only the background with a warm sunset
gradient. Preserve the product, label text, proportions, camera angle, and edges."

Multiple inputs: "Image 1 is the base scene; Image 2 supplies the subject. Place
the subject in the scene with matching perspective, lighting, and scale. Preserve
the subject's identity and the base image's framing."
