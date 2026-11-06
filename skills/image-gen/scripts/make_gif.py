#!/usr/bin/env python3
"""Assemble ordered still images into an opaque animated GIF without API calls."""
from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageColor, ImageOps


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames', nargs='+', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    timing = parser.add_mutually_exclusive_group()
    timing.add_argument('--fps', type=float)
    timing.add_argument('--duration-ms', nargs='+', type=int)
    parser.add_argument('--width', type=int)
    parser.add_argument('--loop', type=int, default=0)
    parser.add_argument('--ping-pong', action='store_true')
    parser.add_argument('--matte', help='Opaque background color for alpha inputs')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args(argv)
    try:
        if len(args.frames) < 2:
            raise ValueError('Provide at least two ordered still frames.')
        if args.out.suffix.lower() != '.gif':
            raise ValueError('Output must have a .gif extension.')
        if args.out.resolve() in [p.resolve() for p in args.frames]:
            raise ValueError('Output must not replace an input frame.')
        if args.out.exists() and not args.force:
            raise ValueError('Output exists; choose a new name or authorize --force.')
        if not -1 <= args.loop <= 65535:
            raise ValueError('Loop must be -1 through 65535.')
        if args.width is not None and not 1 <= args.width <= 65535:
            raise ValueError('Width must be 1 through 65535.')
        fps = args.fps if args.fps is not None else 10
        if not 1 <= fps <= 50:
            raise ValueError('FPS must be between 1 and 50.')
        durations = args.duration_ms or [round(100 / fps) * 10] * len(args.frames)
        if len(durations) != len(args.frames) or any(
            d < 20 or d > 655350 or d % 10 for d in durations
        ):
            raise ValueError('Provide one duration per frame, 20–655350 ms in steps of 10.')
        matte = ImageColor.getcolor(args.matte, 'RGB') if args.matte else None
        frames = []
        source_size = None
        for path in args.frames:
            with Image.open(path) as source:
                if getattr(source, 'n_frames', 1) != 1:
                    raise ValueError(f'Use still inputs, not an animation: {path}')
                frame = ImageOps.exif_transpose(source).convert('RGBA')
            if source_size is None:
                source_size = frame.size
            if frame.size != source_size:
                raise ValueError(f'Frame dimensions differ: {path}')
            if frame.getchannel('A').getextrema()[0] < 255 and matte is None:
                raise ValueError('Transparent input requires an explicit --matte color.')
            canvas = Image.new('RGBA', frame.size, (* (matte or (255, 255, 255)), 255))
            canvas.alpha_composite(frame)
            frame = canvas.convert('RGB')
            if args.width:
                height = max(1, round(frame.height * args.width / frame.width))
                if height > 65535:
                    raise ValueError('Resized height exceeds GIF limit.')
                frame = frame.resize((args.width, height), Image.Resampling.LANCZOS)
            if max(frame.size) > 65535:
                raise ValueError('Frame dimensions exceed GIF limit.')
            frames.append(frame)
        # Small equal-size samples ensure every frame contributes to one palette.
        sheet = Image.new('RGB', (64 * len(frames), 64))
        for i, frame in enumerate(frames):
            sheet.paste(frame.resize((64, 64)), (i * 64, 0))
        palette = sheet.quantize(colors=256)
        frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
        if args.ping_pong:
            frames += frames[-2:0:-1]
            durations += durations[-2:0:-1]
        options = {} if args.loop == -1 else {'loop': args.loop}
        encoded = BytesIO()
        frames[0].save(encoded, format='GIF', save_all=True, append_images=frames[1:],
                       duration=durations, disposal=2, optimize=False, **options)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open('wb' if args.force else 'xb') as target:
            target.write(encoded.getvalue())
        with Image.open(args.out) as result:
            print(f'{args.out.resolve()} | {result.n_frames} frames | {result.size} | '
                  f'{sum(durations)} ms | {args.out.stat().st_size} bytes')
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
