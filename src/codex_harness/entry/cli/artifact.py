"""The `zeus artifact` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus artifact`)
Does not own: dispatch and composition
Entry points: add_parser
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    artifact = commands.add_parser("artifact")
    artifact.add_argument("reference")
    artifact.add_argument("--start", type=int, default=0)
    artifact.add_argument("--length", type=int, default=8000)
    artifact.add_argument("--search")
