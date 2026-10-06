"""The `zeus embed` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus embed`), run (its knowledge-backed body)
Does not own: dispatch (entry.cli main) and composition (composition.cli_knowledge)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    embedding = commands.add_parser("embed")
    embedding.add_argument("--limit", type=int, default=200)


def run(args) -> None:
    from codex_harness.composition import cli_knowledge
    from codex_harness.entry.cli.output import emit
    emit(cli_knowledge.knowledge().embed_missing(cli_knowledge.embeddings(), args.limit))
