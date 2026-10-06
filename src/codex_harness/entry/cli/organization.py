"""The `zeus organization` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus organization`), run (its store-free body)
Does not own: dispatch (entry.cli main) and composition (composition.cli, composition.configuration)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    commands.add_parser("organization")


def run(args) -> None:
    from dataclasses import asdict

    from codex_harness.composition.cli import organization
    from codex_harness.entry.cli.output import emit
    emit({"agents": [asdict(a) for a in organization().agents.values()]})
