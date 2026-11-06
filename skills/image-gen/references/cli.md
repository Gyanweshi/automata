# Installation and portable CLI

## Install the skill

Extract the complete `image-gen` folder from the ZIP, including `scripts` and
`references`. Do not install only SKILL.md or an Automata discovery shim.

- Claude Code, project: `.claude/skills/image-gen/`
- Claude Code, personal: `~/.claude/skills/image-gen/`
- Other skill-compatible agents: their supported skill directory, or instruct
  the agent to read the extracted SKILL.md directly.

In Claude Code invoke `/image-gen` with your image request. This package targets
shell-enabled agents; importing instructions into a chat UI does not confer
Python execution, network access, or a native image generator.

Create/activate a Python 3.10+ virtual environment, then install `openai` with
`python -m pip install openai`. Downscaling and animated GIF assembly require `pillow`.
For GIF requests read [the GIF workflow](gif.md); local assembly needs no API key.
Use the project's existing environment when available. Set `IMAGE_GEN_API_KEY`
locally in the execution environment without putting it in a prompt or command log.
Live calls require API access and incur API charges.

Keep `OPENAI_API_KEY=lm-studio` intact if other tools use it. The image runner
prefers `IMAGE_GEN_API_KEY` and falls back to `OPENAI_API_KEY` only when the
dedicated variable is unset/empty. Known placeholders fail before a network call;
other keys still require server authentication. Both sync and batch calls use
`https://api.openai.com/v1` explicitly, ignoring `OPENAI_BASE_URL` so local LM
Studio routing cannot accidentally receive the image credential.

For persistent configuration, add `IMAGE_GEN_API_KEY` with your real key to your
local untracked `.env` file. Install `python-dotenv` in the virtual environment and
pass `--env-file .env`. Only the dedicated image key is read; existing nonempty
process `IMAGE_GEN_API_KEY` takes precedence. No dotenv file is loaded implicitly.
Never paste keys into chat or include them in exported skill files.

Reproduce the mug test without a paid call:

```text
python "PATH_TO_SKILL/scripts/image_gen.py" generate --env-file .env --prompt "A ceramic mug product shot in soft studio light" --size 1536x1024 --quality low --out workspace/imagegen/test/mug-v1.png --dry-run
```

After configuring a real key locally, remove `--dry-run` to generate the image.

## Commands

Replace `PATH_TO_SKILL` with the extracted skill folder. `python` below means
the selected virtual environment's interpreter. Commands work in PowerShell and
POSIX shells; paths with spaces must remain quoted.

```text
python "PATH_TO_SKILL/scripts/image_gen.py" generate --prompt "A ceramic mug in soft studio light" --size 1024x1024 --out output/imagegen/mug.png --dry-run
python "PATH_TO_SKILL/scripts/image_gen.py" generate --prompt-file prompt.txt --size 1536x1024 --out output/imagegen/hero.png
python "PATH_TO_SKILL/scripts/image_gen.py" edit --image input.png --prompt "Change only the background to blue; preserve the subject" --out output/imagegen/edit-v1.png
python "PATH_TO_SKILL/scripts/image_gen.py" generate-batch --input jobs.jsonl --out-dir output/imagegen/batch --concurrency 2 --dry-run
```

Remove `--dry-run` only for an authorized live call. It validates arguments and
prints the payload without generating images. Use `--help` on each subcommand
for the complete supported interface. The CLI derives from the local Codex
imagegen skill; its historical help text calls it a fallback.

One JSON object per batch line, for example:

```json
{"prompt":"A ceramic mug in studio light","out":"mug.png","size":"1024x1024"}
{"prompt":"A mountain cabin at dawn","out":"cabin.png","size":"1536x1024"}
```

## Bundled runner defaults and constraints

- Defaults: `gpt-image-2`, quality `medium`, size `auto`, PNG, one image.
  These are retained compatibility defaults, not a claim about the newest model.
- Quality: `low`, `medium`, `high`, `auto`. Use low for requested drafts;
  medium/high for fine text or detailed final assets.
- Common sizes: `1024x1024`, `1536x1024`, `1024x1536`, `2048x1152`.
  For this runner's gpt-image-2 validation, both dimensions must be multiples of
  16, max edge 3840, aspect ratio at most 3:1, and total pixels 655360–8294400.
- Do not pass `--input-fidelity` with `gpt-image-2`.
- This runner rejects `--background transparent` with `gpt-image-2`.
  Explain the limitation; if the user selects `gpt-image-1.5`, use
  `--model gpt-image-1.5 --background transparent --output-format png`.
  Do not silently change models or deliver a checkerboard as transparency.
- Repeat `--image` for multiple inputs; describe each role in the prompt.
  `--mask` applies to the first input. Check matching image/mask dimensions,
  alpha channel and file size before sending; a generative edit does not guarantee
  exact preservation of untouched pixels.
- Existing outputs are protected unless `--force` is supplied. Use versioned names.
- On authentication/access errors, stop and report the issue without revealing
  credentials. On uncertain completion, inspect outputs before retrying to avoid
  duplicate charges. Do not change models automatically to evade an error.

## Provenance and documentation

Runner source: installed Codex `.system/imagegen/scripts/image_gen.py`, copied
on 2026-11-06 and adapted for a dedicated credential and fixed OpenAI endpoint.
Portable instructions were authored for this export.
No credentials or host authentication are included.

- [Claude Code skill locations and format](https://code.claude.com/docs/en/skills)
- [OpenAI image generation](https://developers.openai.com/api/docs/guides/image-generation)
- [GPT Image 2](https://developers.openai.com/api/docs/models/gpt-image-2)

Check current official API documentation before adding models or changing the
runner's compatibility constraints; do not assume its validation covers newer models.
