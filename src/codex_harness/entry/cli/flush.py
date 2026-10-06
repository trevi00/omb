"""The `zeus flush` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus flush`), run (its store-backed body)
Does not own: dispatch (entry.cli main) and composition (composition, composition.cli_bus, composition.observation)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    commands.add_parser("flush")


def run(args) -> None:
    from codex_harness.composition import build
    from codex_harness.composition import cli_bus as composition
    from codex_harness.composition.observation import build_observer
    from codex_harness.entry.cli.output import emit
    service = build()
    observer = build_observer(service.store, "cli.flush")
    emit(composition.flusher(service).flush(composition.bus(), audit=observer.audit_system))
    observer.close()
