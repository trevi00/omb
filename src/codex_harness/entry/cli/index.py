"""The `zeus index` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus index`), run (its knowledge-backed body)
Does not own: dispatch (entry.cli main) and composition (composition.cli_knowledge)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    index = commands.add_parser("index")
    index.add_argument("root", nargs="?", default=".")


def run(args) -> None:
    from codex_harness.composition.cli_knowledge import knowledge
    from codex_harness.entry.cli.output import emit
    emit(knowledge().index_python(args.root))
