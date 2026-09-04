# Recipe guidance

This package intentionally contains no project-specific Python recipes. Build a
task-specific adapter under `workspace/<project>/` and measure every source,
repair plate, coordinate, mask, and output path for the current images.

Prefer polygon or ellipse masks for localized repairs. Use GrabCut only when the
generated subject and source framing are already closely aligned. Match
luminance and color locally inside the mask, and preserve the source image as an
immutable input.
