"""Read pinned Git bytes with git argv, never a shell (INV-OPERATION-001).

Layer: adapters
Context: host_os
Owns: GitSource, the commit-exists and blob reads at a pinned revision (the previous implementation, moved ahead of; implements host_os.ports.GitBlobSource structurally)
Does not own: the operation CLI and bind_goal, backlog policy (intake)
Entry points: GitSource
Contracts: INV-OPERATION-001, INV-FLEET-BACKLOG-001

Provenance: carried over from the previous implementation.
"""
from __future__ import annotations

import subprocess

from codex_harness.host_os.adapters import process_groups


class GitSource:
    """Read pinned bytes with git argv, never a shell."""

    def __init__(self, repository):
        self.repository = str(repository)

    def _run(self, *args) -> subprocess.CompletedProcess:
        return process_groups.run(["git", "-C", self.repository, *args], capture_output=True, timeout=60,
                                 **process_groups.no_console_kwargs())

    def commit_exists(self, revision: str) -> bool:
        return self._run("cat-file", "-e", revision + "^{commit}").returncode == 0

    def blob(self, revision: str, path: str) -> tuple[str | None, bytes]:
        listing = self._run("ls-tree", "-z", revision, "--", path)
        entries = [e for e in listing.stdout.split(b"\0") if e]
        if listing.returncode or len(entries) != 1:
            return None, b""
        mode = entries[0].split(b" ", 1)[0].decode("ascii")
        shown = self._run("show", revision + ":" + path)
        return (mode if shown.returncode == 0 else None), shown.stdout
