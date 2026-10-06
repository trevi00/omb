"""Read the exact committed bytes of a backlog document at a pin (INV-FLEET-BACKLOG-001).

Layer: adapters
Context: intake
Owns: read_blob and REGULAR_BLOB: the pinned-bytes read with its fixed refusal codes (the previous implementation, moved ahead of)
Does not own: the plan/manifest loaders and the backlog tick wiring, the Git reads themselves (host_os.GitSource)
Entry points: read_blob, REGULAR_BLOB
Contracts: INV-FLEET-BACKLOG-001

Provenance: carried over from the previous implementation.
"""
from __future__ import annotations

from codex_harness.host_os.ports import GitBlobSource
from codex_harness.intake.domain.backlog import BacklogRefused

REGULAR_BLOB = "100644"


def read_blob(source: GitBlobSource, revision: str, path: str, limit: int, role: str) -> bytes:
    """The exact committed bytes at a pin, or a fixed refusal code naming the role only."""
    if not source.commit_exists(revision):
        raise BacklogRefused(role + "_revision_missing")
    mode, data = source.blob(revision, path)
    if mode is None:
        raise BacklogRefused(role + "_missing_at_revision")
    if mode != REGULAR_BLOB:
        # A directory, symlink or submodule entry is not an owner document.
        raise BacklogRefused(role + "_not_regular")
    if len(data) > limit:
        raise BacklogRefused(role + "_too_large")
    return data
