"""The `zeus autonomous` argument parser (the previous implementation).

Layer: entry
Owns: add_parser (the argument shape of `zeus autonomous`)
Does not own: dispatch and composition
Entry points: add_parser
Contracts: none

Provenance: carried over from the previous implementation.
"""

from pathlib import Path


def add_parser(commands) -> None:
    auto = commands.add_parser("autonomous", help="Research, immutable packet, independent debate, Operation v2, atomic promotion")
    sub = auto.add_subparsers(dest="autonomous_command", required=True)
    run_parser = sub.add_parser("run", help="Claim the manifest id and run the full cycle to a terminal receipt "
                                            "(urn:zeus:autonomous:1, or urn:zeus:autonomous:2 for the DBA/two-lead council)")
    run_parser.add_argument("--file", type=Path, required=True)
    show = sub.add_parser("status", help="Safe read-only receipt; store read only")
    show.add_argument("run_id")
