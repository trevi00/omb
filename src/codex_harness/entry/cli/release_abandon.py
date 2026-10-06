"""The `zeus release-abandon` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus release-abandon`)
Does not own: dispatch and composition
Entry points: add_parser
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    release = commands.add_parser("release-abandon")
    release.add_argument("release_id")
    release.add_argument("--reason", required=True)
