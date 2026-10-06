"""The `zeus cleanup` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus cleanup`)
Does not own: dispatch and composition
Entry points: add_parser
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    cleanup = commands.add_parser("cleanup")
    cleanup.add_argument("--apply", action="store_true")
