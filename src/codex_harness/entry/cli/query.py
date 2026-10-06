"""The `zeus query` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus query`), run (its knowledge-backed body)
Does not own: dispatch (entry.cli main) and composition (composition.cli_knowledge)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    q = commands.add_parser("query")
    q.add_argument("text")
    q.add_argument("--semantic", action="store_true")


def run(args) -> None:
    from codex_harness.composition import cli_knowledge
    from codex_harness.entry.cli.output import emit
    knowledge = cli_knowledge.knowledge()
    if args.semantic:
        emit(knowledge.hybrid_query(args.text, cli_knowledge.embeddings()))
    else:
        emit(knowledge.query(args.text))
