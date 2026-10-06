"""The `zeus rlm` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus rlm`)
Does not own: dispatch and composition
Entry points: add_parser
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    rlm = commands.add_parser("rlm")
    rlm.add_argument("reference")
    rlm.add_argument("question")
    rlm.add_argument("--max-calls", type=int, default=8)
