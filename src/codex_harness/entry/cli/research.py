"""The `zeus research` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus research`)
Does not own: dispatch and composition
Entry points: add_parser
Contracts: INV-DISCOVERY-PRESSURE-001

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    research = commands.add_parser("research")
    research.add_argument("source", choices=["github", "geeknews"])
    # INV-DISCOVERY-PRESSURE-001: why this fetch happens; carried in the task and checked before any fetch.
    research.add_argument("--intent", required=True,
                          choices=["proactive", "user_request", "incident", "existing_work_result", "task_required"])
