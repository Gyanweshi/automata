"""Default-deny authorization for writes to the Obsidian vault."""
from __future__ import annotations

from pathlib import Path


class VaultWriteBlockedError(PermissionError):
    """Raised when a vault mutation lacks one-shot finalization approval."""


def require_vault_write(
    *,
    commit_vault: bool,
    commit_reason: str | None,
    operation: str,
    target: Path | None = None,
) -> str:
    """Validate a one-shot vault write authorization and return its reason."""
    reason = (commit_reason or "").strip()
    target_text = f" Target: {target}." if target is not None else ""
    if not commit_vault:
        raise VaultWriteBlockedError(
            f"Vault write blocked for {operation}.{target_text} "
            "Finish in workspace, then retry with explicit commit_vault=True and a commit reason."
        )
    if not reason:
        raise VaultWriteBlockedError(
            f"Vault write blocked for {operation}.{target_text} "
            "A non-empty commit reason is required."
        )
    return reason
