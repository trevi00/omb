"""The one mapping from a routing result to a fixed role-container profile.

Layer: domain
Context: routing
Owns: the four profile names and `select_profile` (pure); re-exports IsolationError (defined in kernel.errors)
Does not own: the container argv, mounts or credentials of a profile (execution/credentials)
Entry points: select_profile, IsolationError, CLAUDE_IMPL_RW, CLAUDE_ROLE_RO, CODEX_ROLE_RO, CODEX_IMPL_RW
Contracts: INV-ROLE-CONTAINER-001

Provenance: carried over from the previous implementation.
"""

from __future__ import annotations

from codex_harness.kernel.errors import IsolationError

CLAUDE_IMPL_RW, CLAUDE_ROLE_RO = "claude-impl-rw", "claude-role-ro"
CODEX_ROLE_RO, CODEX_IMPL_RW = "codex-role-ro", "codex-impl-rw"


def select_profile(provider, transport, action, read_only, *, codex_enabled: bool) -> str:
    """The one mapping from the routing result to a profile; everything else refuses before spawn.
    There is never a host fallback: a disabled Codex store refuses rather than using the host."""
    if type(read_only) is bool:
        if provider == "claude" and transport == "claude_cli":
            if read_only:
                return CLAUDE_ROLE_RO
            if action == "implement":
                return CLAUDE_IMPL_RW
        elif provider == "codex" and transport == "app_server":
            if not codex_enabled:
                raise IsolationError("codex_profile_disabled",
                                     "isolation is selected and no Codex credential store is configured; "
                                     "the host App Server is never the fallback")
            if read_only:
                return CODEX_ROLE_RO
            if action == "implement":
                return CODEX_IMPL_RW
    raise IsolationError("role_profile_refused", f"{provider}/{transport}/{action}/{'ro' if read_only else 'rw'}")
