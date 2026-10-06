"""The `zeus setup` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus setup`), run (its store-free body)
Does not own: dispatch (entry.cli main) and composition (composition.cli, composition.configuration)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    commands.add_parser("setup", help="Create local configuration without overwriting credentials")


def run(args) -> None:
    from codex_harness.composition.configuration import initialize, runtime_dir
    from codex_harness.entry.cli.output import emit
    result = initialize()
    runtime_dir().mkdir(parents=True, exist_ok=True)
    emit(result)
