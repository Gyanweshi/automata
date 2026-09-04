from __future__ import annotations

import argparse
import shutil
import sqlite3
import uuid
from pathlib import Path


PROFILE_FILES = (
    "containers.json",
    "prefs.js",
)

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = (REPO_ROOT / "workspace").resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a lean Zen profile copy for Magnific automation."
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--cookie-domain", default="magnific")
    parser.add_argument(
        "--source-origin-attributes",
        default="^userContextId=2",
        help="Container originAttributes to normalize into the default context.",
    )
    return parser.parse_args()


def create_lean_profile(
    source: Path,
    target: Path,
    *,
    cookie_domain: str,
    source_origin_attributes: str,
) -> tuple[int, int]:
    source = source.resolve()
    target = target.resolve()
    cookie_db = source / "cookies.sqlite"

    if not source.is_dir():
        raise FileNotFoundError(f"Source profile does not exist: {source}")
    if not cookie_db.is_file():
        raise FileNotFoundError(f"Source cookie database does not exist: {cookie_db}")
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite existing target: {target}")
    if source == target or source in target.parents:
        raise ValueError("Target must not be the source or a child of the source")
    try:
        relative_target = target.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise ValueError(
            f"Target must be inside the git-ignored workspace directory: {WORKSPACE_ROOT}"
        ) from exc
    if not relative_target.parts:
        raise ValueError("Target must be a profile directory below workspace")
    if not cookie_domain.strip():
        raise ValueError("Cookie domain must not be empty")

    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.with_name(f".{target.name}.building-{uuid.uuid4().hex}")
    copied = 0
    try:
        staging.mkdir()
        for name in PROFILE_FILES:
            source_file = source / name
            if source_file.is_file():
                shutil.copy2(source_file, staging / name)
                copied += 1

        source_db = sqlite3.connect(f"file:{cookie_db}?mode=ro", uri=True)
        target_db = sqlite3.connect(staging / "cookies.sqlite")
        try:
            source_db.backup(target_db)
            pattern = f"%{cookie_domain.strip()}%"
            target_db.execute(
                "DELETE FROM moz_cookies WHERE host LIKE ? AND originAttributes = ''",
                (pattern,),
            )
            target_db.execute(
                "UPDATE moz_cookies SET originAttributes = '' "
                "WHERE host LIKE ? AND originAttributes = ?",
                (pattern, source_origin_attributes),
            )
            target_db.execute(
                "DELETE FROM moz_cookies WHERE host NOT LIKE ?",
                (pattern,),
            )
            target_db.commit()
        finally:
            target_db.close()
            source_db.close()

        staging.rename(target)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    total_bytes = sum(item.stat().st_size for item in target.rglob("*") if item.is_file())
    return copied, total_bytes


def main() -> None:
    args = parse_args()
    copied, total_bytes = create_lean_profile(
        args.source,
        args.target,
        cookie_domain=args.cookie_domain,
        source_origin_attributes=args.source_origin_attributes,
    )
    print(f"PROFILE={args.target.resolve()}")
    print(f"COPIED_PROFILE_FILES={copied}")
    print(f"SIZE_MB={total_bytes / 1024 / 1024:.2f}")


if __name__ == "__main__":
    main()
