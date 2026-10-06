"""The `zeus execute-one` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus execute-one`)
Does not own: dispatch and composition
Entry points: add_parser
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    execute = commands.add_parser("execute-one")
    execute.add_argument("--agent", required=True)
