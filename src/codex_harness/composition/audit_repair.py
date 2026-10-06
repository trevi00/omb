"""The `zeus audit-repair` composition: the repair owner over this host's store and artifact root.

Layer: composition
Owns: build_repair
Does not own: the argument shape and the command body (entry.cli.audit_repair) and the replay itself (research.adapters.audit_repair.replay_decode)
Entry points: build_repair
Contracts: INV-AUDIT-REPAIR-001

Provenance: carried over from the previous implementation.
"""


def build_repair(service, artifacts=None, *, replay=None):
    """The repair owner over this host's existing store, organization and artifact root."""
    from codex_harness.composition.configuration import runtime_dir
    from codex_harness.coordination.application import execution_notices
    from codex_harness.coordination.application.events import EventJournal
    from codex_harness.coordination.application.outbox import Outbox
    from codex_harness.research.adapters.audit_repair import replay_decode
    from codex_harness.research.application.audit_repair import AuditRepair
    from codex_harness.storage.adapters.file_artifacts import FileArtifacts

    if artifacts is None:
        artifacts = FileArtifacts(str(runtime_dir() / "artifacts"))
    return AuditRepair(service.store, service.org, artifacts, replay=replay_decode if replay is None else replay,
                       outbox=Outbox(), events=EventJournal(), notices=execution_notices)
