"""The `zeus rollback-hook` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus rollback-hook`), run (its store-backed body)
Does not own: dispatch (entry.cli main) and composition (composition.cli, composition.configuration)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    rollback = commands.add_parser("rollback-hook")
    rollback.add_argument("hook_id")
    rollback.add_argument("--reason", required=True)


def run(args) -> None:
    from codex_harness.composition import build
    from codex_harness.composition import cli as composition
    from codex_harness.entry.cli.output import emit
    service = build()
    composition.hook_units(service).rollback(args.hook_id, args.reason)
    emit({"rolled_back": args.hook_id})
