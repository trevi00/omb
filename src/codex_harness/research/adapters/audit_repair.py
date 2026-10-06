"""Wire the EXISTING pure content decoder and the existing artifact store into the bounded repair
owner (INV-AUDIT-REPAIR-001).

There is no second decoder, schema, validator or diagnosis engine here. `replay_decode` runs
`AuditExecution.proposed_checkpoint`, the same pure half of the rejection boundary that refused the
draft in the first place, against the trusted stored partition and the retained answer: it touches
no store, lease, runner, artifact, transport or provider, it repairs, decodes, normalizes and
deduplicates nothing, and it returns only the refusal's TYPE and the digest of its message. The
message itself never leaves this function, so a diagnosis is bound to a validator's identity rather
than to a substring an operator could read in a log.

Layer: adapters
Context: research
Owns: replay_decode, the pure replay of the content decode of one retained draft against its trusted assigned scope (the diagnosis the bounded repair owner binds to a validator's identity)
Does not own: the repair owner (research.application.audit_repair, which receives this function as its injected `replay`), the pure decoder itself (`AuditExecution.proposed_checkpoint`, research.adapters.audit_execution), the `build_repair` composition over this host's store and artifact root (an entry)
Entry points: replay_decode
Contracts: INV-AUDIT-REPAIR-001

Provenance: carried over from the previous implementation.
"""
from __future__ import annotations

from codex_harness.kernel.errors import ContractError
from codex_harness.kernel.ids import digest
from codex_harness.research.domain.research import PartitionCheckpoint

__all__ = ["replay_decode"]


def replay_decode(partition: dict, answer: dict) -> dict:
    """Replay the pure content decode of ONE retained draft against its trusted assigned scope.

    A refusal returns its type and the digest of its message; a draft that now decodes cleanly
    returns `refused` false, which makes the diagnosis a mismatch rather than an eligibility. Only
    the pure decoder's own refusal can ever be reproduced here: `AuditDraftRejected` from
    `ResearchAudits.checkpoint` is raised inside that method's transaction against trusted records
    and is deliberately not replayable, so its family is never admitted by this owner.
    """
    from codex_harness.research.adapters.audit_execution import AuditExecution

    trusted = PartitionCheckpoint(**partition)
    trusted.validate()
    try:
        AuditExecution.proposed_checkpoint(trusted, answer)
    except ContractError as rejection:
        return {"refused": True, "error_type": type(rejection).__name__,
                "error_digest": digest(str(rejection))}
    return {"refused": False, "error_type": None, "error_digest": None}
