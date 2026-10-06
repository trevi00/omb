"""The `zeus project-graph` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus project-graph`), run (its knowledge-backed body)
Does not own: dispatch (entry.cli main) and composition (composition.cli_knowledge)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    commands.add_parser("project-graph")


def run(args) -> None:
    from codex_harness.composition import build
    from codex_harness.composition.cli_knowledge import knowledge
    from codex_harness.entry.cli.output import emit
    service = build()
    emit(knowledge().project_runtime(service.store, service.org))
