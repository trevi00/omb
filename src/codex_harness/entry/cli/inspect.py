"""The `zeus inspect` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus inspect`), run (its store-backed body)
Does not own: dispatch (entry.cli main) and composition (composition, composition.cli)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    inspect = commands.add_parser("inspect")
    inspect.add_argument("bucket", choices=["incidents", "hooks", "sessions", "events", "deliveries", "outbox",
                                           "outbox_quarantine", "outbox_delivery", "outbox_attempts",
                                           "execution_failures", "execution_recoveries", "execution_notices", "execution_notice_errors",
                                           "execution_rejections",
                                           "execution_time_events",
                                           "invocation_reservations",
                                           "observations", "observation_audit", "observation_quarantine",
                                           "observation_alerts", "observation_collections", "observation_terminations",
                                           "tasks", "decisions_pending", "releases", "deployment", "release_queue",
                                           "audit_service"])


def run(args) -> None:
    from codex_harness.composition import build
    from codex_harness.entry.cli.output import emit
    service = build()
    with service.store.transaction() as tx:
        emit(tx.scan(args.bucket))
