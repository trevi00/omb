"""The `zeus rebase` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus rebase`)
Does not own: dispatch and composition
Entry points: add_parser
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    rebase = commands.add_parser("rebase")
    rebase.add_argument("task_id")
    rebase.add_argument("--onto", default="HEAD")
