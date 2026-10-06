"""The `zeus init-db` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus init-db`), run (its store-backed body)
Does not own: dispatch (entry.cli main) and composition (composition, composition.cli)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    commands.add_parser("init-db")


def run(args) -> None:
    from codex_harness.composition import build
    from codex_harness.entry.cli.output import emit
    service = build()
    receipt = service.store.migrate()
    emit({"migrated": True, "applied": receipt["applied"], "already_applied": receipt["already_applied"], "tool": receipt["tool"]})
