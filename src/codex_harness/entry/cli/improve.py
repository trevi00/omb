"""The `zeus improve` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus improve`)
Does not own: dispatch and composition
Entry points: add_parser
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    improve = commands.add_parser("improve")
    improve.add_argument("objective")
    improve.add_argument("--acceptance", action="append", required=True)
    improve.add_argument("--importance", choices=["simple", "important"])
