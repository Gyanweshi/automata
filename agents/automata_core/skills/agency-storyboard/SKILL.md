# Agency Storyboard Agent

You are the storyboard agent. When the user runs `/agency storyboard`, create visual storyboards and AI generation prompts for brand content.

## Trigger

`/agency storyboard <brand-slug> <type> "<topic>" [--slides N] [--duration N] [--tool freepik_image|freepik_video|blender]`

Types: `carousel` | `reel` | `post` | `mood_board`

## Steps

1. **Verify install**: `python3 -c "import agency_storyboard; print('OK')"`

2. **Load context** - before generating:
   - Read `$OBSIDIAN_VAULT_PATH/Brands/<brand-slug>.md`. This is the single source of truth for brand-specific visual direction, mood, photography style, and prior decisions.
   - Read the `## Memory` section carefully and build on what has already worked or been rejected.
   - Do not call `search_second_brain` for brand-specific context. Use vault search only for broad topic or reference research that is not already covered in the brand note.
   - If prior research or content exists in `workspace/research/<brand-slug>/` or `workspace/content/<brand-slug>/`, skim the latest relevant output before storyboarding.

3. **Generate the storyboard**:
   ```bash
   agency-storyboard --brand <brand-slug> --type <type> --topic "<topic>" [--slides 7] [--duration 30] [--tool freepik_image] --format markdown
   ```

4. **Read and enrich**: The output contains scene breakdowns and raw AI prompts. Your job:
   - Read each scene description and enrich the visual details based on the brand's photography style and mood.
   - Refine the generation prompts so they are more specific, vivid, and brand-appropriate.
   - Add creative direction notes for each scene.

5. **Freepik MCP integration**: After generating prompts, you can immediately generate images using the Freepik MCP tools already configured in this workspace:
   - For images: use `mcp__freepik__create_image_mystic` or `mcp__freepik__text_to_image_mystic_sync`.
   - For videos: use `mcp__freepik__create_video_kling_2_1_std` or `mcp__freepik__create_video_kling_2_1_pro`.
   - Use the `positive_prompt` from the storyboard output as the prompt parameter.
   - Check status with `mcp__freepik__get_mystic_task_status` or `mcp__freepik__get_kling_2_1_task_status`.

6. **Output**: Present the storyboard to the user as:
   - Scene-by-scene visual direction
   - Refined generation prompts ready to paste into any AI tool
   - Option to generate with Freepik immediately

## Aspect Ratios by Format

| Format | Recommended | Use |
|--------|-------------|-----|
| Instagram carousel | 4:5 (1080x1350) | Freepik image |
| Instagram reel | 9:16 (1080x1920) | Freepik video |
| Instagram post | 1:1 (1080x1080) | Freepik image |
| LinkedIn carousel | 1:1 or 4:5 | Freepik image |
| LinkedIn post | 1.91:1 (1200x628) | Freepik image |

## Tool Selection

- `freepik_image` - best for carousels and static posts (uses Mystic model)
- `freepik_video` - best for reels (uses Kling 2.1)
- `blender` - for 3D visualization (uses Blender MCP, already configured)
- `generic` - tool-agnostic prompts for any AI generator

## MCP Integrations

Agent-scoped MCP configuration is stored in `mcp/agents/storyboard.json`.

- **Freepik FastMCP** (`FREEPIK_API_KEY`) - search Freepik assets and generate Mystic/Kling visual assets.
- **Blender** - create and inspect 3D storyboard scenes when Blender and its MCP addon are running.

## Standalone Use

This agent can run without research data. If research exists in the workspace, it auto-loads it to inform scene themes.
