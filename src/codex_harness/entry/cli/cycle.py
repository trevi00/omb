"""The `zeus cycle` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus cycle`)
Does not own: dispatch and composition
Entry points: add_parser
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    cycle = commands.add_parser("cycle", help="Bounded persistent execution loop over one correlation; no conductor")
    cycle_commands = cycle.add_subparsers(dest="cycle_command", required=True)
    for name in ("start", "status", "handoff", "step"):
        sub = cycle_commands.add_parser(name)
        sub.add_argument("cycle_id")
        if name == "start":
            sub.add_argument("--correlation", required=True)
            sub.add_argument("--max-executions", type=int, required=True,
                             help="Executor starts allowed through this cycle; not a billing count")
